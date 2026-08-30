"""Canonical JSON serialization for deterministic runtime digests."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from hashlib import sha256

from pydantic import BaseModel

JsonScalar = bool | int | float | str | None
JsonValue = JsonScalar | Mapping[str, "JsonValue"] | Sequence["JsonValue"]


def _json_value(value: object) -> JsonScalar | dict[str, object] | list[object]:
    """Convert immutable container types to JSON-native containers."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON rejects non-finite numbers")
        return value
    if isinstance(value, BaseModel):
        return _json_value(value.model_dump(mode="json"))
    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical JSON object keys must be strings")
            normalized[key] = _json_value(item)
        return normalized
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_value(item) for item in value]
    raise TypeError(f"unsupported canonical JSON value: {type(value).__name__}")


def canonical_bytes(value: JsonValue) -> bytes:
    """Serialize one value as sorted-key, compact UTF-8 JSON bytes."""
    normalized = _json_value(value)
    text = json.dumps(normalized, allow_nan=False, ensure_ascii=False,
                      separators=(",", ":"), sort_keys=True)
    return text.encode("utf-8")


def canonical_sha256(value: JsonValue) -> str:
    """Return the contract-form SHA-256 digest of canonical JSON bytes."""
    return f"sha256:{sha256(canonical_bytes(value)).hexdigest()}"
