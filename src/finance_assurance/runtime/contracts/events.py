"""Runtime-owned accounting-event variants from Artifact F sections 4-5."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, TypeAdapter

from .primitives import (
    ActorRef,
    AsciiString,
    Authorization,
    ChecklistRef,
    Currency,
    DateString,
    DerivationAuthority,
    DisclosureBasisRef,
    EvidenceRef,
    FrozenContractModel,
    HashValue,
    IssueRef,
    MaterialityRef,
    PeriodId,
    PolicyRef,
    PositiveInt,
    ReconciliationRef,
    RemediationDirectiveRef,
    Timestamp,
    VersionRef,
)


class ProposalSubjectRef(FrozenContractModel):
    object_type: Literal["journal_proposal"]
    object_ref: VersionRef


class PeriodSubjectRef(FrozenContractModel):
    object_type: Literal["accounting_period"]
    object_ref: PeriodId


class RestatementSubjectRef(FrozenContractModel):
    object_type: Literal["restatement_case"]
    object_ref: AsciiString


class AccountingEventBase(FrozenContractModel):
    contract_version: Literal[1]
    event_id: AsciiString
    command_id: AsciiString
    correlation_id: AsciiString
    causation_event_id: AsciiString | None
    occurred_at: Timestamp
    recorded_at: Timestamp
    actor: ActorRef
    authorization: Authorization
    evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)


class ProposalSubmissionBasis(FrozenContractModel):
    basis_type: Literal["PROPOSAL_SUBMISSION"]
    derivation_authority: DerivationAuthority
    input_hashes: tuple[HashValue, ...] = Field(min_length=1)
    total_debit_minor: PositiveInt
    total_credit_minor: PositiveInt
    currency: Currency
    dimensions_resolved: Literal[True]


class ProposalSubmittedPayload(FrozenContractModel):
    proposal_ref: VersionRef
    from_status: Literal["DRAFT"]
    to_status: Literal["SUBMITTED"]


class ProposalSubmitted(AccountingEventBase):
    event_type: Literal["proposal.submitted"]
    subject_ref: ProposalSubjectRef
    basis: ProposalSubmissionBasis
    payload: ProposalSubmittedPayload


class ProposalDeferredBasis(FrozenContractModel):
    basis_type: Literal["CLOSE_EXCEPTION"]
    close_policy_ref: PolicyRef
    reason_code: Literal["RECOGNITION_NOT_POSTED_BEFORE_CLOSE"]
    owner_ref: ActorRef
    target_treatment: Literal["RESTATEMENT_REVIEW"]
    expires_on: DateString


class ProposalDeferredPayload(FrozenContractModel):
    proposal_ref: VersionRef
    from_status: Literal["SUBMITTED"]
    to_status: Literal["DEFERRED"]


class ProposalDeferred(AccountingEventBase):
    event_type: Literal["proposal.deferred"]
    subject_ref: ProposalSubjectRef
    basis: ProposalDeferredBasis
    payload: ProposalDeferredPayload


class PeriodCloseBasis(FrozenContractModel):
    basis_type: Literal["PERIOD_CLOSE"]
    close_policy_ref: PolicyRef
    checklist_ref: ChecklistRef
    trial_balance_hash: HashValue
    reconciliation_refs: tuple[ReconciliationRef, ...]
    unresolved_submitted_count: Literal[0]
    unresolved_approved_count: Literal[0]
    deferred_proposal_refs: tuple[VersionRef, ...]


class PeriodHardClosedPayload(FrozenContractModel):
    period_id: PeriodId
    from_status: Literal["SOFT_CLOSED"]
    to_status: Literal["HARD_CLOSED"]


class PeriodHardClosed(AccountingEventBase):
    event_type: Literal["period.hard_closed"]
    subject_ref: PeriodSubjectRef
    basis: PeriodCloseBasis
    payload: PeriodHardClosedPayload


class RestatementInitiationBasis(FrozenContractModel):
    basis_type: Literal["RESTATEMENT_INITIATION"]
    trigger_ref: IssueRef
    directive_ref: RemediationDirectiveRef
    materiality_ref: MaterialityRef
    scope_period_ids: tuple[PeriodId, ...] = Field(min_length=1)


class RestatementProposedPayload(FrozenContractModel):
    restatement_case_id: AsciiString
    to_status: Literal["PROPOSED"]


class RestatementProposed(AccountingEventBase):
    event_type: Literal["restatement.proposed"]
    subject_ref: RestatementSubjectRef
    basis: RestatementInitiationBasis
    payload: RestatementProposedPayload


class ProposalApprovalBasis(FrozenContractModel):
    basis_type: Literal["PROPOSAL_APPROVAL"]
    decision_maker: ActorRef
    sod_check_passed: Literal[True]
    period_guard_state: Literal["OPEN"]
    period_guard_passed: Literal[True]


class ProposalApprovedPayload(FrozenContractModel):
    proposal_ref: VersionRef
    from_status: Literal["SUBMITTED"]
    to_status: Literal["APPROVED"]


class ProposalApproved(AccountingEventBase):
    event_type: Literal["proposal.approved"]
    subject_ref: ProposalSubjectRef
    basis: ProposalApprovalBasis
    payload: ProposalApprovedPayload


class JournalPostingBasis(FrozenContractModel):
    basis_type: Literal["JOURNAL_POSTING"]
    proposal_ref: VersionRef
    balance_debit_minor: PositiveInt
    balance_credit_minor: PositiveInt
    currency: Currency
    period_id: PeriodId
    period_state: Literal["OPEN"]
    period_guard_passed: Literal[True]


class JournalPostedPayload(FrozenContractModel):
    proposal_ref: VersionRef
    journal_id: AsciiString
    entry_class: Literal["REVERSAL", "REPLACEMENT", "RESTATEMENT_ADJUSTMENT"]
    from_status: Literal["APPROVED"]
    to_status: Literal["POSTED"]


class JournalPosted(AccountingEventBase):
    event_type: Literal["journal.posted"]
    subject_ref: ProposalSubjectRef
    basis: JournalPostingBasis
    payload: JournalPostedPayload
    idempotency_key: AsciiString


class RestatementLinkBasis(FrozenContractModel):
    basis_type: Literal["RESTATEMENT_LINK"]
    restatement_case_id: AsciiString
    journal_id: AsciiString
    entry_class: Literal["RESTATEMENT_ADJUSTMENT"]
    class_check_passed: Literal[True]


class RestatementAdjustmentLinkedPayload(FrozenContractModel):
    restatement_case_id: AsciiString
    journal_id: AsciiString
    status: Literal["PROPOSED"]


class RestatementAdjustmentLinked(AccountingEventBase):
    event_type: Literal["restatement.adjustment_linked"]
    subject_ref: RestatementSubjectRef
    basis: RestatementLinkBasis
    payload: RestatementAdjustmentLinkedPayload


class RestatementManifestBasis(FrozenContractModel):
    basis_type: Literal["RESTATEMENT_MANIFEST"]
    restatement_case_id: AsciiString
    linked_journal_ids: tuple[AsciiString, ...] = Field(min_length=1)
    manifest_hash: HashValue
    manifest_debit_minor: PositiveInt
    manifest_credit_minor: PositiveInt
    currency: Currency
    reconciles_to_journal_lines: Literal[True]


class RestatementAdjustmentsReadyPayload(FrozenContractModel):
    restatement_case_id: AsciiString
    from_status: Literal["PROPOSED"]
    to_status: Literal["ADJUSTMENTS_READY"]


class RestatementAdjustmentsReady(AccountingEventBase):
    event_type: Literal["restatement.adjustments_ready"]
    subject_ref: RestatementSubjectRef
    basis: RestatementManifestBasis
    payload: RestatementAdjustmentsReadyPayload


class RestatementApprovalBasis(FrozenContractModel):
    basis_type: Literal["RESTATEMENT_APPROVAL"]
    restatement_case_id: AsciiString
    manifest_hash: HashValue
    materiality_ref: MaterialityRef
    disclosure_basis_ref: DisclosureBasisRef


class RestatementApprovedPayload(FrozenContractModel):
    restatement_case_id: AsciiString
    from_status: Literal["ADJUSTMENTS_READY"]
    to_status: Literal["APPROVED"]


class RestatementApproved(AccountingEventBase):
    event_type: Literal["restatement.approved"]
    subject_ref: RestatementSubjectRef
    basis: RestatementApprovalBasis
    payload: RestatementApprovedPayload


class ReportingPublicationBasis(FrozenContractModel):
    basis_type: Literal["REPORTING_PUBLICATION"]
    restatement_case_id: AsciiString
    predecessor_version_ref: VersionRef
    manifest_hash: HashValue
    content_ref: AsciiString
    content_hash: HashValue
    content_schema_version: PositiveInt
    publication_policy_ref: PolicyRef


class ReportingVersionPublishedPayload(FrozenContractModel):
    reporting_version_ref: VersionRef
    restatement_case_id: AsciiString
    restatement_from_status: Literal["APPROVED"]
    restatement_to_status: Literal["PUBLISHED"]


class ReportingVersionPublished(AccountingEventBase):
    event_type: Literal["reporting_version.published"]
    subject_ref: RestatementSubjectRef
    basis: ReportingPublicationBasis
    payload: ReportingVersionPublishedPayload
    idempotency_key: AsciiString


AccountingEvent = Annotated[
    ProposalSubmitted
    | ProposalDeferred
    | PeriodHardClosed
    | RestatementProposed
    | ProposalApproved
    | JournalPosted
    | RestatementAdjustmentLinked
    | RestatementAdjustmentsReady
    | RestatementApproved
    | ReportingVersionPublished,
    Field(discriminator="event_type"),
]

ACCOUNTING_EVENT_ADAPTER = TypeAdapter(AccountingEvent)
