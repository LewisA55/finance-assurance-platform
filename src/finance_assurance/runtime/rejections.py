"""Stable runtime rejection values independent of validation libraries."""

import re
from dataclasses import dataclass

_CODE_PATTERN = re.compile(r"[A-Z][A-Z0-9_]*")


@dataclass(frozen=True, slots=True, order=True)
class Detail:
    """One deterministic key/value detail."""

    key: str
    value: str

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("detail key must not be empty")


@dataclass(frozen=True, slots=True, order=True)
class RejectionCode:
    """Stable rejection identifier shared by runtime entry points."""

    value: str

    def __post_init__(self) -> None:
        if _CODE_PATTERN.fullmatch(self.value) is None:
            raise ValueError("rejection code must match [A-Z][A-Z0-9_]*")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Rejection:
    """A deterministic semantic rejection."""

    code: RejectionCode
    reason: str
    details: tuple[Detail, ...] = ()

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("rejection reason must not be empty")
