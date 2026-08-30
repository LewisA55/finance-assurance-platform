"""Deterministic technical relationship keys for Artifact R."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

from finance_assurance.exports.serialization import canonical_json_bytes, sha256_bytes


def _validate_component(source_type: str, value: object) -> object:
    if value is None:
        raise ValueError("relationship-key components cannot be null")
    if source_type == "integer":
        if type(value) is not int:
            raise TypeError("integer relationship-key component must be an int")
    elif source_type == "boolean":
        if type(value) is not bool:
            raise TypeError("boolean relationship-key component must be a bool")
    elif source_type in {"text", "enum", "hash", "date", "timestamp"}:
        if not isinstance(value, str) or not value:
            raise TypeError("textual relationship-key component must be non-empty text")
        if source_type == "date":
            date.fromisoformat(value)
        elif source_type == "timestamp":
            datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError(f"unsupported source type {source_type}")
    return value


def relationship_key(
    relationship_id: str,
    source_types: Sequence[str],
    values: Sequence[object],
) -> str:
    """Hash one exact typed tuple using Artifact P canonical JSON plus LF."""

    if not relationship_id or not relationship_id.isascii():
        raise ValueError("relationship_id must be non-empty ASCII")
    if len(source_types) != len(values) or len(values) < 2:
        raise ValueError("relationship-key type/value tuples must have equal width")
    payload = {
        "relationship_id": relationship_id,
        "values": [
            {"type": source_type, "value": _validate_component(source_type, value)}
            for source_type, value in zip(source_types, values, strict=True)
        ],
    }
    return sha256_bytes(canonical_json_bytes(payload))


def assert_no_key_collisions(
    projected: Sequence[tuple[str, tuple[object, ...]]],
) -> None:
    """Reject one technical hash resolving to multiple source tuples."""

    seen: dict[str, tuple[object, ...]] = {}
    for key, preimage in projected:
        prior = seen.setdefault(key, preimage)
        if prior != preimage:
            raise ValueError("relationship-key collision detected")
