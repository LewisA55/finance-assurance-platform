"""Canonical Artifact P JSON and CSV serialization independent of model order."""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Mapping, Sequence
from hashlib import sha256

from pydantic import BaseModel

from finance_assurance.exports.registry import ColumnDefinition, DatasetDefinition

_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")


def _json_value(value: object) -> object:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise TypeError("Artifact P canonical JSON prohibits floating-point values")
    if isinstance(value, BaseModel):
        return _json_value(value.model_dump(mode="json"))
    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical JSON keys must be strings")
            normalized[key] = _json_value(item)
        return normalized
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_value(item) for item in value]
    raise TypeError(f"unsupported Artifact P JSON value: {type(value).__name__}")


def canonical_json_bytes(value: object) -> bytes:
    normalized = _json_value(value)
    return (
        json.dumps(
            normalized,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{sha256(value).hexdigest()}"


def _reject_forbidden_text(value: str) -> None:
    if not value:
        raise ValueError("Artifact P CSV prohibits empty strings")
    if any(character in value for character in ("\t", "\r", "\n")):
        raise ValueError("Artifact P CSV prohibits tabs and line breaks")


def _encode_scalar(value: object, column: ColumnDefinition) -> str:
    if value is None:
        if not column.nullable:
            raise ValueError(f"{column.name} is not nullable")
        return ""
    if column.type == "boolean":
        if type(value) is not bool:
            raise TypeError(f"{column.name} requires a strict boolean")
        text = "true" if value else "false"
    elif column.type == "integer":
        if type(value) is not int:
            raise TypeError(f"{column.name} requires a strict integer")
        text = str(value)
    else:
        if not isinstance(value, str):
            raise TypeError(f"{column.name} requires text")
        _reject_forbidden_text(value)
        text = value
        if column.type == "hash" and _HASH.fullmatch(text) is None:
            raise ValueError(f"{column.name} requires a canonical SHA-256 value")
        if column.type == "date" and _DATE.fullmatch(text) is None:
            raise ValueError(f"{column.name} requires an ISO date")
        if column.type == "timestamp" and _TIMESTAMP.fullmatch(text) is None:
            raise ValueError(f"{column.name} requires a UTC RFC 3339 timestamp")
        if column.type == "enum" and text not in column.enum_values:
            raise ValueError(f"{column.name} contains an unregistered enum value")
    return f'"{text.replace(chr(34), chr(34) * 2)}"'


def canonical_csv_bytes(
    definition: DatasetDefinition,
    rows: Sequence[Mapping[str, object]],
) -> bytes:
    header = definition.header
    expected = set(header)
    lines = [",".join(f'"{item}"' for item in header)]
    ordered = sorted(rows, key=lambda row: str(row["row_key"]))
    for row in ordered:
        if set(row) != expected:
            missing = sorted(expected - set(row))
            extra = sorted(set(row) - expected)
            message = (
                f"{definition.dataset_id} row shape mismatch: "
                f"missing={missing}, extra={extra}"
            )
            raise ValueError(message)
        lines.append(
            ",".join(
                _encode_scalar(row[column.name], column)
                for column in definition.columns
            )
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def parse_canonical_csv(
    definition: DatasetDefinition,
    payload: bytes,
) -> tuple[dict[str, object], ...]:
    if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload:
        raise ValueError("CSV must be UTF-8 without BOM and use LF line endings")
    text = payload.decode("utf-8")
    parsed = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    if not parsed or tuple(parsed[0]) != definition.header:
        raise ValueError("CSV header does not match the registered dataset")
    rows: list[dict[str, object]] = []
    for raw in parsed[1:]:
        if len(raw) != len(definition.columns):
            raise ValueError("CSV row width does not match the registered header")
        row: dict[str, object] = {}
        for column, value in zip(definition.columns, raw, strict=True):
            if value == "":
                if not column.nullable:
                    raise ValueError(f"{column.name} is not nullable")
                row[column.name] = None
            elif column.type == "integer":
                if re.fullmatch(r"-?\d+", value) is None:
                    raise ValueError(f"{column.name} is not a canonical integer")
                row[column.name] = int(value)
            elif column.type == "boolean":
                if value not in {"true", "false"}:
                    raise ValueError(f"{column.name} is not a canonical boolean")
                row[column.name] = value == "true"
            else:
                row[column.name] = value
        rows.append(row)
    if canonical_csv_bytes(definition, rows) != payload:
        raise ValueError("CSV bytes are not canonical")
    return tuple(rows)
