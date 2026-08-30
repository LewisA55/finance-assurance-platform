"""Semantic-availability helpers for pinned runtime reads and admissions."""

from __future__ import annotations

from datetime import datetime

BASELINE_AVAILABLE_FROM = "0001-01-01T00:00:00Z"


def instant(value: str) -> datetime:
    """Parse the runtime's RFC 3339 UTC timestamp form into an aware instant."""

    if not value or not value.endswith("Z"):
        raise ValueError("semantic time must be an RFC 3339 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise ValueError("semantic time must be an RFC 3339 UTC timestamp") from error
    return parsed


def is_available(available_from: str, semantic_as_of_time: str) -> bool:
    """Return whether one record is semantically available at a pinned time."""

    return instant(available_from) <= instant(semantic_as_of_time)


def latest(*values: str) -> str:
    """Return the latest timestamp by instant while preserving wire text."""

    if not values:
        raise ValueError("at least one semantic timestamp is required")
    return max(values, key=instant)
