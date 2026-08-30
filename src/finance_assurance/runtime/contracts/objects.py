"""Runtime-owned strict object variants from Artifact F section 3."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, TypeAdapter, model_validator

from .primitives import (
    ActorRef,
    AsciiString,
    ContractRef,
    Currency,
    DateString,
    Dimensions,
    EvidenceRef,
    FrozenContractModel,
    HashValue,
    IssueRef,
    NonNegativeInt,
    PeriodId,
    PolicyRef,
    PositiveInt,
    RecognitionScheduleRef,
    RemediationDirectiveRef,
    Timestamp,
    VersionRef,
    require_one_sided_line,
)


class RecognitionDuePayload(FrozenContractModel):
    contract_ref: ContractRef
    recognition_schedule_ref: RecognitionScheduleRef
    service_period_start: DateString
    service_period_end: DateString
    amount_minor: PositiveInt
    currency: Currency


class BusinessEvent(FrozenContractModel):
    contract_version: Literal[1]
    business_event_id: AsciiString
    event_type: Literal["accounting.recognition.due"]
    correlation_id: AsciiString
    occurred_at: Timestamp
    recorded_at: Timestamp
    effective_date: DateString
    source_system: Literal["REVENUE_SUBLEDGER"]
    legal_entity_id: AsciiString
    payload: RecognitionDuePayload
    evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)


class PostingRule(FrozenContractModel):
    contract_version: Literal[1]
    posting_rule_id: Literal["PR-O2C-RECOG"]
    rule_version: PositiveInt
    posting_rule_ref: VersionRef
    trigger_event_type: Literal["accounting.recognition.due"]
    effective_from: DateString
    effective_to: DateString | None
    status: Literal["ACTIVE"]
    content_ref: AsciiString
    content_hash: HashValue
    content_schema_version: PositiveInt
    evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def reference_matches_identity(self) -> PostingRule:
        if self.posting_rule_ref != f"{self.posting_rule_id}@v{self.rule_version}":
            raise ValueError("posting_rule_ref does not match identity and version")
        return self


class ProposalLine(FrozenContractModel):
    line_no: PositiveInt
    account_id: AsciiString
    debit_minor: NonNegativeInt
    credit_minor: NonNegativeInt
    currency: Currency
    dimensions: Dimensions

    @model_validator(mode="after")
    def is_one_sided(self) -> ProposalLine:
        require_one_sided_line(self.debit_minor, self.credit_minor)
        return self


class AutomatedPostingBasis(FrozenContractModel):
    business_event_ref: AsciiString
    posting_rule_ref: VersionRef
    input_hashes: tuple[HashValue, ...] = Field(min_length=1)


class ReversalOriginBasis(FrozenContractModel):
    reverses_journal_id: AsciiString
    correction_policy_ref: PolicyRef
    directive_ref: RemediationDirectiveRef
    input_hashes: tuple[HashValue, ...] = Field(min_length=1)


class ReplacementOriginBasis(FrozenContractModel):
    corrects_journal_id: AsciiString
    correction_policy_ref: PolicyRef
    directive_ref: RemediationDirectiveRef
    input_hashes: tuple[HashValue, ...] = Field(min_length=1)


class RestatementAdjustmentOriginBasis(FrozenContractModel):
    restatement_case_id: AsciiString
    restatement_policy_ref: PolicyRef
    directive_ref: RemediationDirectiveRef
    predecessor_proposal_ref: VersionRef
    input_hashes: tuple[HashValue, ...] = Field(min_length=1)


class JournalProposalBase(FrozenContractModel):
    contract_version: Literal[1]
    proposal_id: AsciiString
    proposal_version: PositiveInt
    proposal_ref: VersionRef
    status: Literal["SUBMITTED", "APPROVED", "POSTED", "DEFERRED"]
    target_period_id: PeriodId
    effective_date: DateString
    ledger_currency: Currency
    proposed_lines: tuple[ProposalLine, ...] = Field(min_length=2)
    total_debit_minor: PositiveInt
    total_credit_minor: PositiveInt
    prepared_by: ActorRef
    created_at: Timestamp
    submitted_at: Timestamp
    evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identity_and_totals(self) -> JournalProposalBase:
        if self.proposal_ref != f"{self.proposal_id}@v{self.proposal_version}":
            raise ValueError("proposal_ref does not match identity and version")
        line_numbers = [line.line_no for line in self.proposed_lines]
        if len(line_numbers) != len(set(line_numbers)):
            raise ValueError("proposal line numbers must be unique")
        debit = sum(line.debit_minor for line in self.proposed_lines)
        credit = sum(line.credit_minor for line in self.proposed_lines)
        if debit != credit or debit != self.total_debit_minor or credit != self.total_credit_minor:
            raise ValueError("proposal totals must balance and reconcile to lines")
        return self


class AutomatedPostingProposal(JournalProposalBase):
    origin_type: Literal["AUTOMATED_POSTING"]
    origin_basis: AutomatedPostingBasis


class ReversalProposal(JournalProposalBase):
    origin_type: Literal["REVERSAL"]
    origin_basis: ReversalOriginBasis


class ReplacementProposal(JournalProposalBase):
    origin_type: Literal["REPLACEMENT"]
    origin_basis: ReplacementOriginBasis


class RestatementAdjustmentProposal(JournalProposalBase):
    origin_type: Literal["RESTATEMENT_ADJUSTMENT"]
    origin_basis: RestatementAdjustmentOriginBasis


JournalProposal = Annotated[
    AutomatedPostingProposal | ReversalProposal | ReplacementProposal | RestatementAdjustmentProposal,
    Field(discriminator="origin_type"),
]


class ReversalCorrectionBasis(FrozenContractModel):
    reverses_journal_id: AsciiString


class ReplacementCorrectionBasis(FrozenContractModel):
    corrects_journal_id: AsciiString
    directive_ref: RemediationDirectiveRef


class RestatementCorrectionBasis(FrozenContractModel):
    restatement_case_id: AsciiString
    directive_ref: RemediationDirectiveRef


class JournalEntryBase(FrozenContractModel):
    contract_version: Literal[1]
    journal_id: AsciiString
    source_proposal_ref: VersionRef
    posted_by_event_id: AsciiString
    ledger_period_id: PeriodId
    effective_date: DateString
    posted_at: Timestamp
    currency: Currency
    total_debit_minor: PositiveInt
    total_credit_minor: PositiveInt
    line_refs: tuple[AsciiString, ...] = Field(min_length=2)
    evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_totals_and_lines(self) -> JournalEntryBase:
        if self.total_debit_minor != self.total_credit_minor:
            raise ValueError("journal totals must balance")
        if len(self.line_refs) != len(set(self.line_refs)):
            raise ValueError("journal line references must be unique")
        return self


class ReversalJournalEntry(JournalEntryBase):
    entry_class: Literal["REVERSAL"]
    correction_basis: ReversalCorrectionBasis


class ReplacementJournalEntry(JournalEntryBase):
    entry_class: Literal["REPLACEMENT"]
    correction_basis: ReplacementCorrectionBasis


class RestatementJournalEntry(JournalEntryBase):
    entry_class: Literal["RESTATEMENT_ADJUSTMENT"]
    correction_basis: RestatementCorrectionBasis


JournalEntry = Annotated[
    ReversalJournalEntry | ReplacementJournalEntry | RestatementJournalEntry,
    Field(discriminator="entry_class"),
]


class JournalLine(FrozenContractModel):
    contract_version: Literal[1]
    journal_line_id: AsciiString
    journal_id: AsciiString
    line_no: PositiveInt
    account_id: AsciiString
    debit_minor: NonNegativeInt
    credit_minor: NonNegativeInt
    currency: Currency
    dimensions: Dimensions

    @model_validator(mode="after")
    def is_one_sided(self) -> JournalLine:
        require_one_sided_line(self.debit_minor, self.credit_minor)
        return self


class AccountingPeriodBase(FrozenContractModel):
    contract_version: Literal[1]
    period_id: PeriodId
    start_date: DateString
    end_date: DateString
    ledger_currency: Currency
    evidence_refs: tuple[EvidenceRef, ...]


class OpenAccountingPeriod(AccountingPeriodBase):
    status: Literal["OPEN"]
    opened_at: Timestamp


class SoftClosedAccountingPeriod(AccountingPeriodBase):
    status: Literal["SOFT_CLOSED"]
    soft_closed_at: Timestamp
    soft_close_event_id: AsciiString


class HardClosedAccountingPeriod(AccountingPeriodBase):
    status: Literal["HARD_CLOSED"]
    hard_closed_at: Timestamp
    hard_close_event_id: AsciiString
    close_policy_ref: PolicyRef


AccountingPeriod = Annotated[
    OpenAccountingPeriod | SoftClosedAccountingPeriod | HardClosedAccountingPeriod,
    Field(discriminator="status"),
]


class ReportingVersion(FrozenContractModel):
    contract_version: Literal[1]
    reporting_version_id: AsciiString
    period_id: PeriodId
    version: PositiveInt
    reporting_version_ref: VersionRef
    predecessor_version_ref: VersionRef
    restatement_case_id: AsciiString
    content_ref: AsciiString
    content_hash: HashValue
    content_schema_version: PositiveInt
    adjustment_manifest_hash: HashValue
    published_at: Timestamp
    published_by_event_id: AsciiString
    evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def reference_matches_identity(self) -> ReportingVersion:
        if self.reporting_version_ref != f"{self.reporting_version_id}@v{self.version}":
            raise ValueError("reporting_version_ref does not match identity and version")
        return self


class ManifestEntry(FrozenContractModel):
    journal_line_ref: AsciiString
    ledger_period_id: PeriodId
    presented_period_id: PeriodId
    account_id: AsciiString
    debit_minor: NonNegativeInt
    credit_minor: NonNegativeInt
    currency: Currency
    basis_ref: PolicyRef

    @model_validator(mode="after")
    def is_one_sided(self) -> ManifestEntry:
        require_one_sided_line(self.debit_minor, self.credit_minor)
        return self


class RestatementCaseBase(FrozenContractModel):
    contract_version: Literal[1]
    restatement_case_id: AsciiString
    scope_period_ids: tuple[PeriodId, ...] = Field(min_length=1)
    trigger_ref: IssueRef
    directive_ref: RemediationDirectiveRef
    owner_ref: ActorRef
    linked_journal_ids: tuple[AsciiString, ...]
    adjustment_manifest: tuple[ManifestEntry, ...]
    manifest_hash: HashValue | None
    approver_ref: ActorRef | None
    approved_at: Timestamp | None
    published_version_refs: tuple[VersionRef, ...]
    evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)


class ProposedRestatementCase(RestatementCaseBase):
    status: Literal["PROPOSED"]

    @model_validator(mode="after")
    def state_guard(self) -> ProposedRestatementCase:
        if self.adjustment_manifest or self.manifest_hash is not None:
            raise ValueError("PROPOSED cannot have a frozen manifest")
        if self.approver_ref is not None or self.approved_at is not None or self.published_version_refs:
            raise ValueError("PROPOSED cannot be approved or published")
        return self


class AdjustmentsReadyRestatementCase(RestatementCaseBase):
    status: Literal["ADJUSTMENTS_READY"]

    @model_validator(mode="after")
    def state_guard(self) -> AdjustmentsReadyRestatementCase:
        if not self.linked_journal_ids or not self.adjustment_manifest or self.manifest_hash is None:
            raise ValueError("ADJUSTMENTS_READY requires linked journals and frozen manifest")
        if self.approver_ref is not None or self.approved_at is not None or self.published_version_refs:
            raise ValueError("ADJUSTMENTS_READY cannot be approved or published")
        return self


class ApprovedRestatementCase(RestatementCaseBase):
    status: Literal["APPROVED"]

    @model_validator(mode="after")
    def state_guard(self) -> ApprovedRestatementCase:
        if not self.adjustment_manifest or self.manifest_hash is None:
            raise ValueError("APPROVED requires a frozen manifest")
        if self.approver_ref is None or self.approved_at is None or self.published_version_refs:
            raise ValueError("APPROVED requires approval and cannot already be published")
        return self


class PublishedRestatementCase(RestatementCaseBase):
    status: Literal["PUBLISHED"]

    @model_validator(mode="after")
    def state_guard(self) -> PublishedRestatementCase:
        if not self.adjustment_manifest or self.manifest_hash is None:
            raise ValueError("PUBLISHED requires a frozen manifest")
        if self.approver_ref is None or self.approved_at is None or not self.published_version_refs:
            raise ValueError("PUBLISHED requires approval and published versions")
        return self


RestatementCase = Annotated[
    ProposedRestatementCase
    | AdjustmentsReadyRestatementCase
    | ApprovedRestatementCase
    | PublishedRestatementCase,
    Field(discriminator="status"),
]

ArtifactObject = (
    BusinessEvent | PostingRule | JournalProposal | JournalEntry | JournalLine | AccountingPeriod | ReportingVersion | RestatementCase
)

OBJECT_ADAPTERS: dict[str, TypeAdapter[object]] = {
    "business_event": TypeAdapter(BusinessEvent),
    "posting_rule": TypeAdapter(PostingRule),
    "journal_proposal": TypeAdapter(JournalProposal),
    "journal_entry": TypeAdapter(JournalEntry),
    "journal_line": TypeAdapter(JournalLine),
    "accounting_period": TypeAdapter(AccountingPeriod),
    "reporting_version": TypeAdapter(ReportingVersion),
    "restatement_case": TypeAdapter(RestatementCase),
}
