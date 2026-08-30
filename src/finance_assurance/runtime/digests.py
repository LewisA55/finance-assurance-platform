"""Deterministic normalization and hashing for immutable runtime values."""

from __future__ import annotations

from dataclasses import fields
from typing import Any

from pydantic import BaseModel

from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256


def stable_value(value: object) -> Any:
    """Convert frozen runtime values to deterministic JSON-native data."""

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if hasattr(value, "__dataclass_fields__"):
        return {
            field.name: stable_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): stable_value(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        normalized = [stable_value(item) for item in value]
        return sorted(normalized, key=canonical_bytes)
    if isinstance(value, (tuple, list)):
        return [stable_value(item) for item in value]
    return value


def value_digest(value: object) -> str:
    """Hash one runtime value with the canonical serializer."""

    return canonical_sha256(stable_value(value))
