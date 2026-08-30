"""Observer protocol and proof metadata for Artifact G boundary traces."""

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class BoundaryObservation:
    """One immutable, ordered observation of a cross-module handoff."""

    sequence: int
    publisher: str
    consumer: str
    contract_id: str
    purpose: str
    object_version: str | None = None
    event_id: str | None = None
    command_id: str | None = None
    contract_version: str | None = None
    subject_ref: str | None = None
    outcome: Literal["ACCEPTED", "REJECTED", "BLOCKED"] = "ACCEPTED"
    upstream_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        for field_name in (
            "publisher",
            "consumer",
            "contract_id",
            "purpose",
        ):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} must not be empty")
        if (
            self.subject_ref is None
            and self.object_version is None
            and self.event_id is None
            and self.command_id is None
        ):
            raise ValueError(
                "an object_version, event_id, or command_id is required "
                "when subject_ref is absent"
            )
        if not self.evidence_refs and (
            self.contract_version is not None or self.subject_ref is not None
        ):
            raise ValueError("Phase 7 observations require immutable evidence")


@runtime_checkable
class BoundaryRecorder(Protocol):
    """Receives observations without participating in domain transitions."""

    def record(self, observation: BoundaryObservation) -> None:
        """Record one observation in deterministic execution order."""
