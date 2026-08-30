"""Typed database-independent ports for Artifact K command persistence."""

from __future__ import annotations

from typing import Protocol

from finance_assurance.runtime.persistence.models import (
    AcceptedCommitPlan,
    AdmissionBundle,
    AdmissionReceipt,
    BaselineContext,
    CommandContext,
    CommandIdentityConflict,
    CommandResult,
    CommitReceipt,
    ExactCommandResult,
    ExactConflictSnapshot,
    ExactStoredRecord,
    ImportContext,
    ProjectionGenerationRef,
    QueryContext,
    RebuildContext,
    RebuildReceipt,
    RebuiltProjectionSet,
    ReferencedJournalContext,
    StagedRejectionSet,
    StagedWriteSet,
    ValidatedAcceptedPlan,
    ValidatedProjectionGeneration,
    ValidatedRejectionPlan,
)
from finance_assurance.runtime.persistence.state import InMemoryState
from finance_assurance.runtime.planner import StateSnapshot


class TypedReadFacets(Protocol):
    """Stable semantic read view held by one command unit of work."""

    def snapshot(self) -> StateSnapshot: ...


class CommandUnitOfWork(Protocol):
    """One Artifact K command-attempt transaction boundary."""

    def context(self) -> CommandContext: ...

    def prior_result(self) -> ExactCommandResult | None: ...

    def records(self) -> TypedReadFacets: ...

    def stage_accepted(self, write_set: StagedWriteSet) -> None: ...

    def stage_rejection(self, write_set: StagedRejectionSet) -> None: ...

    def validate(self) -> ValidatedAcceptedPlan | ValidatedRejectionPlan: ...

    def arbitrate(
        self, plan: ValidatedAcceptedPlan
    ) -> AcceptedCommitPlan | ExactConflictSnapshot | ExactCommandResult | CommandIdentityConflict: ...

    def replace_with_conflict_rejection(
        self,
        snapshot: ExactConflictSnapshot,
        write_set: StagedRejectionSet,
    ) -> None: ...

    def commit(
        self, plan: AcceptedCommitPlan | ValidatedRejectionPlan
    ) -> CommitReceipt: ...

    def rollback(self) -> None: ...


class CommandPersistenceBoundary(Protocol):
    """Root port for ordinary application-command attempts."""

    @property
    def state(self) -> InMemoryState: ...

    def command_result(self, command_id: str) -> CommandResult | None: ...

    def authoritative_record(
        self, record_family: str, record_identity: str
    ) -> ExactStoredRecord | None: ...

    def authoritative_records(
        self, record_family: str | None = None
    ) -> tuple[ExactStoredRecord, ...]: ...

    @property
    def revision(self) -> int: ...

    def begin_command(self, context: CommandContext) -> CommandUnitOfWork: ...


class AdmissionUnitOfWork(Protocol):
    """Sealed baseline, import, or referenced-state admission mode."""

    def context(self) -> object: ...

    def prior_receipt(self) -> AdmissionReceipt | None: ...

    def stage_bundle(self, bundle: AdmissionBundle) -> None: ...

    def validate(self) -> str: ...

    def commit(self, validated_digest: str) -> AdmissionReceipt: ...

    def rollback(self) -> None: ...


class QuerySession(Protocol):
    @property
    def revision(self) -> int: ...

    def state(self) -> InMemoryState: ...


class RebuildSession(Protocol):
    def context(self) -> RebuildContext: ...

    def begin_generation(self) -> ProjectionGenerationRef: ...

    def rebuild(self, generation: ProjectionGenerationRef) -> RebuiltProjectionSet: ...

    def validate(
        self, rebuilt: RebuiltProjectionSet
    ) -> ValidatedProjectionGeneration: ...

    def promote(
        self, validated: ValidatedProjectionGeneration
    ) -> RebuildReceipt: ...

    def abort(self, generation: ProjectionGenerationRef) -> None: ...

    def rollback(self) -> None: ...


class PersistenceBoundary(CommandPersistenceBoundary, Protocol):
    """Complete six-mode Artifact K root persistence boundary."""

    def begin_runtime_baseline_admission(
        self, context: BaselineContext
    ) -> AdmissionUnitOfWork: ...

    def begin_pre_scope_reporting_import(
        self, context: ImportContext
    ) -> AdmissionUnitOfWork: ...

    def begin_referenced_journal_admission(
        self, context: ReferencedJournalContext
    ) -> AdmissionUnitOfWork: ...

    def open_query(self, context: QueryContext) -> QuerySession: ...

    def open_rebuild(self, context: RebuildContext) -> RebuildSession: ...
