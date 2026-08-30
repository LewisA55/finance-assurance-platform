"""Immutable semantic stores used by the in-memory persistence adapter."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from pydantic import BaseModel

from finance_assurance.runtime.contracts.objects import (
    JournalEntryBase,
    JournalLine,
    ReportingVersion,
)
from finance_assurance.runtime.digests import stable_value as stable_value
from finance_assurance.runtime.digests import value_digest as value_digest
from finance_assurance.runtime.persistence.models import (
    CommandDisposition,
    CommandResult,
    EffectRecord,
)
from finance_assurance.runtime.planner import StateSnapshot
from finance_assurance.runtime.referenced import ReferencedJournalProjection


@dataclass(frozen=True, slots=True)
class ProtectedDigests:
    object_versions: str
    lifecycle_projections: str
    event_log: str
    journal_store: str
    reporting_version_store: str
    effect_registry: str

    @property
    def combined(self) -> str:
        return value_digest(self)


@dataclass(frozen=True, slots=True)
class InMemoryState:
    """Immutable semantic state held by the in-memory persistence adapter."""

    snapshot: StateSnapshot = field(default_factory=StateSnapshot)
    object_versions: tuple[BaseModel, ...] = ()
    event_log: tuple[BaseModel, ...] = ()
    journal_store: tuple[BaseModel, ...] = ()
    reporting_version_store: tuple[ReportingVersion, ...] = ()
    reporting_content_proofs: tuple[BaseModel, ...] = ()
    effect_registry: tuple[EffectRecord, ...] = ()
    command_results: tuple[CommandResult, ...] = ()
    dispositions: tuple[CommandDisposition, ...] = ()
    referenced_state: tuple[ReferencedJournalProjection, ...] = ()
    known_predecessor_event_ids: frozenset[str] = frozenset()

    @classmethod
    def from_snapshot(
        cls,
        snapshot: StateSnapshot,
        *,
        known_predecessor_event_ids: frozenset[str] = frozenset(),
    ) -> InMemoryState:
        effects = tuple(
            EffectRecord(
                idempotency_key=key,
                effect_type="PUBLICATION" if key.startswith("publish:") else "POSTING",
                command_id=f"BOOTSTRAP:{key}",
                event_id=f"BOOTSTRAP:{key}",
                subject_ref=key.partition(":")[2],
            )
            for key in sorted(snapshot.consumed_effect_keys)
        )
        return cls(
            snapshot=snapshot,
            effect_registry=effects,
            referenced_state=snapshot.referenced_journals,
            known_predecessor_event_ids=(
                known_predecessor_event_ids | snapshot.accounting_event_ids
            ),
        )

    def command_result(self, command_id: str) -> CommandResult | None:
        return next(
            (item for item in self.command_results if item.command_id == command_id),
            None,
        )

    def effect(self, idempotency_key: str) -> EffectRecord | None:
        return next(
            (
                item
                for item in self.effect_registry
                if item.idempotency_key == idempotency_key
            ),
            None,
        )

    def protected_digests(self) -> ProtectedDigests:
        return ProtectedDigests(
            object_versions=value_digest(self.object_versions),
            lifecycle_projections=value_digest(self.snapshot),
            event_log=value_digest(self.event_log),
            journal_store=value_digest(self.journal_store),
            reporting_version_store=value_digest(self.reporting_version_store),
            effect_registry=value_digest(self.effect_registry),
        )

    @property
    def full_digest(self) -> str:
        return value_digest(self)


def split_creations(
    creations: tuple[BaseModel, ...],
) -> tuple[tuple[BaseModel, ...], tuple[BaseModel, ...], tuple[ReportingVersion, ...]]:
    """Route immutable creations to their non-overlapping stores."""

    objects: list[BaseModel] = []
    journals: list[BaseModel] = []
    reporting: list[ReportingVersion] = []
    for item in creations:
        if isinstance(item, (JournalEntryBase, JournalLine)):
            journals.append(item)
        elif isinstance(item, ReportingVersion):
            reporting.append(item)
        else:
            objects.append(item)
    return tuple(objects), tuple(journals), tuple(reporting)


HarnessState = InMemoryState


def with_snapshot(state: InMemoryState, snapshot: StateSnapshot) -> InMemoryState:
    return replace(state, snapshot=snapshot)
