"""Database-independent semantic types for Artifact K persistence ports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from finance_assurance.runtime.contracts.primitives import AuthoritativeRef
from finance_assurance.runtime.planner import StateSnapshot, TransitionPlan
from finance_assurance.runtime.rejections import Rejection

CommandStatus = Literal["ACCEPTED", "REJECTED"]
EffectType = Literal["POSTING", "PUBLICATION"]
DispositionStatus = Literal["REJECTED"]
ConflictClass = Literal["STALE_STATE", "EFFECT_CONSUMED"]
AdmissionMode = Literal[
    "RUNTIME_BASELINE",
    "PRE_SCOPE_REPORTING",
    "REFERENCED_JOURNAL",
]


@dataclass(frozen=True, slots=True)
class CommandContext:
    command_owner: str
    command_id: str
    command_type: str
    input_contract_version: str
    input_canonicalization_version: str
    input_digest: str
    actor_ref: str
    authority_refs: tuple[str, ...]
    semantic_as_of_time: str
    correlation_id: str

    def __post_init__(self) -> None:
        required = (
            self.command_owner,
            self.command_id,
            self.command_type,
            self.input_contract_version,
            self.input_canonicalization_version,
            self.input_digest,
            self.actor_ref,
            self.semantic_as_of_time,
            self.correlation_id,
        )
        if not all(required):
            raise ValueError("command context fields must not be empty")

    @property
    def retry_identity(self) -> tuple[str, ...]:
        """Fields that bind command deduplication before domain execution."""

        return (
            self.command_owner,
            self.command_id,
            self.command_type,
            self.input_contract_version,
            self.input_canonicalization_version,
            self.input_digest,
        )

@dataclass(frozen=True, slots=True)
class StateExpectation:
    subject_type: str
    subject_ref: str
    expected_state_token: str


@dataclass(frozen=True, slots=True)
class EffectRecord:
    idempotency_key: str
    effect_type: EffectType
    command_id: str
    event_id: str
    subject_ref: str


@dataclass(frozen=True, slots=True)
class CommandResult:
    command_id: str
    command_fingerprint: str
    status: CommandStatus
    outcome: TransitionPlan | ModuleCommandOutcome | Rejection


@dataclass(frozen=True, slots=True)
class ModuleCommandOutcome:
    """Accepted non-lifecycle closure for one Artifact G publisher command."""

    command_id: str
    command_owner: str
    consumed_publication_refs: tuple[str, ...]
    immutable_creations: tuple[BaseModel, ...]


@dataclass(frozen=True, slots=True)
class ExactCommandResult:
    context: CommandContext
    result: CommandResult


@dataclass(frozen=True, slots=True)
class CommandDisposition:
    contract_id: Literal["G-14"]
    command_id: str
    request_ref: str
    status: DispositionStatus
    rejection_code: str
    reason: str


@dataclass(frozen=True, slots=True)
class StagedWriteSet:
    projection_replacement: StateSnapshot
    object_appends: tuple[BaseModel, ...]
    accounting_event_appends: tuple[BaseModel, ...]
    journal_appends: tuple[BaseModel, ...]
    reporting_version_appends: tuple[BaseModel, ...]
    effect_claims: tuple[EffectRecord, ...]
    expected_state_tokens: tuple[StateExpectation, ...]
    resulting_state_tokens: tuple[StateExpectation, ...]
    command_result: CommandResult
    dispositions: tuple[CommandDisposition, ...] = ()


@dataclass(frozen=True, slots=True)
class BaselineContext:
    baseline_manifest_ref: str
    baseline_manifest_contract_version: str
    baseline_manifest_canonicalization_version: str
    baseline_manifest_hash: str
    semantic_as_of_time: str
    admitting_actor_ref: str

    @property
    def admission_id(self) -> str:
        return self.baseline_manifest_ref


@dataclass(frozen=True, slots=True)
class ImportContext:
    import_id: str
    imported_reporting_version_ref: str
    sealed_candidate_contract_version: str
    sealed_candidate_canonicalization_version: str
    sealed_candidate_hash: str
    semantic_as_of_time: str
    importer_ref: str


@dataclass(frozen=True, slots=True)
class ReferencedJournalContext:
    source_journal_ref: str
    source_canonicalization_version: str
    source_hash: str
    source_contract_version: str
    semantic_as_of_time: str
    admitting_actor_ref: str

    @property
    def admission_id(self) -> str:
        return self.source_journal_ref


@dataclass(frozen=True, slots=True)
class SealedAdmissionRecord:
    record_family: str
    record_identity: str
    semantic_owner: str
    contract_version: str
    canonicalization_version: str
    semantic_hash: str
    canonical_payload: bytes


@dataclass(frozen=True, slots=True)
class ProjectionReplacement:
    projection_family: str
    projection_token: str
    source_hash: str
    canonical_payload: bytes


@dataclass(frozen=True, slots=True)
class AdmissionBundle:
    declared_records: tuple[SealedAdmissionRecord, ...]
    projection_replacements: tuple[ProjectionReplacement, ...] = ()


@dataclass(frozen=True, slots=True)
class PreScopeReportingImportBundle(AdmissionBundle):
    sealed_candidate_body: bytes = b""
    prerequisite_period_ref: str = ""
    prerequisite_close_event_ref: str = ""
    prerequisite_close_view_hash: str = ""


@dataclass(frozen=True, slots=True)
class ReferencedJournalAdmissionBundle(AdmissionBundle):
    canonical_source_body: bytes = b""
    provenance_body: bytes = b""


@dataclass(frozen=True, slots=True)
class AdmissionReceipt:
    admission_mode: AdmissionMode
    admission_id: str
    input_digest: str
    revision: int
    replayed: bool = False


@dataclass(frozen=True, slots=True)
class QueryContext:
    semantic_as_of_time: str


@dataclass(frozen=True, slots=True)
class RebuildContext:
    semantic_as_of_time: str
    requested_projection_families: tuple[str, ...]
    verification_mode: Literal["FULL"] = "FULL"


@dataclass(frozen=True, slots=True)
class ProjectionGenerationRef:
    generation_id: str
    source_revision: int


@dataclass(frozen=True, slots=True)
class RebuiltProjectionSet:
    generation_ref: ProjectionGenerationRef
    projection: StateSnapshot
    prior_projection_hash: str
    authoritative_state_hash: str
    command_count: int


@dataclass(frozen=True, slots=True)
class ValidatedProjectionGeneration:
    generation_ref: ProjectionGenerationRef
    projection_set: RebuiltProjectionSet


@dataclass(frozen=True, slots=True)
class RebuildReceipt:
    prior_projection_hash: str
    rebuilt_projection_hash: str
    authoritative_state_hash: str
    command_count: int


@dataclass(frozen=True, slots=True)
class ExactStoredRecord:
    record_family: str
    record_identity: str
    semantic_hash: str
    canonical_payload: bytes
    available_from: str

    def semantic_body(self) -> object:
        """Return the semantic body without exposing adapter type envelopes."""

        parsed = json.loads(self.canonical_payload)
        if (
            isinstance(parsed, dict)
            and "$runtime_type" in parsed
            and "value" in parsed
        ):
            return parsed["value"]
        return parsed


@dataclass(frozen=True, slots=True)
class StagedRejectionSet:
    command_result: CommandResult
    dispositions: tuple[CommandDisposition, ...] = ()
    object_appends: tuple[BaseModel, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidatedAcceptedPlan:
    unit_token: object
    write_set: StagedWriteSet


@dataclass(frozen=True, slots=True)
class ValidatedRejectionPlan:
    unit_token: object
    write_set: StagedRejectionSet


@dataclass(frozen=True, slots=True)
class AcceptedCommitPlan:
    unit_token: object
    write_set: StagedWriteSet
    revision: int


@dataclass(frozen=True, slots=True)
class ExactConflictSnapshot:
    conflict_class: ConflictClass
    subject_or_effect_key: str
    expected_authoritative_ref: str | None
    observed_authoritative_ref: str | None
    observed_semantic_hash: str


@dataclass(frozen=True, slots=True)
class CommandIdentityConflict:
    command_id: str
    expected_input_digest: str
    supplied_input_digest: str


@dataclass(frozen=True, slots=True)
class CommitReceipt:
    outcome: Literal["ACCEPTED", "REJECTED"]
    command_result_ref: str
    command_result_hash: str
    committed_authoritative_refs: tuple[AuthoritativeRef, ...]
    committed_publication_refs: tuple[AuthoritativeRef, ...]
    claimed_effect_refs: tuple[str, ...]
    resulting_state_tokens: tuple[StateExpectation, ...]
