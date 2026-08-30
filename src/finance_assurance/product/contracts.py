"""Strict Artifact O version-1 public view and envelope contracts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from finance_assurance.runtime.contracts.primitives import (
    AsciiString,
    Currency,
    DateString,
    HashValue,
    NonNegativeInt,
    PeriodId,
    PositiveInt,
    Timestamp,
)


class PublicContractModel(BaseModel):
    """Closed immutable model used only at the public read boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ScenarioSummary(PublicContractModel):
    scenario_ref: AsciiString
    canonical_family: Literal["C-001", "CT-1"]
    status: Literal["AVAILABLE", "UNAVAILABLE", "FAILED"]
    public_role: AsciiString
    entry_point_count: NonNegativeInt


class ScenarioEntryPoint(PublicContractModel):
    journey_id: Literal["O-J01", "O-J02", "O-J03", "O-SJ01"]
    semantic_role: AsciiString
    exact_ref: AsciiString
    source_kind: Literal[
        "AUTHORITATIVE_RECORD",
        "CONTRACT_PUBLICATION",
        "LABELLED_PROJECTION",
    ]
    availability: Literal["AVAILABLE", "UNAVAILABLE"]


class HeadlineValue(PublicContractModel):
    field: AsciiString
    label: AsciiString
    amount_minor: int
    currency: Currency
    reporting_version_ref: AsciiString
    content_verification_status: Literal[
        "CONTENT_BYTES_VERIFIED",
        "DECLARED_HASH_ONLY",
        "MISSING",
        "UNAVAILABLE",
    ]
    trace_available: bool


StatementValue = HeadlineValue


class ModuleSummary(PublicContractModel):
    module: Literal["Hermes", "Atlas", "Argus", "Aegis", "Pythia"]
    summary_code: AsciiString
    primary_product_ref: AsciiString
    route: AsciiString


class GovernanceIssueState(PublicContractModel):
    issue_ref: AsciiString
    status: AsciiString
    owner_ref: AsciiString


class ReadinessSummary(PublicContractModel):
    readiness_ref: AsciiString
    reporting_version_ref: AsciiString
    period_id: PeriodId
    purpose_ref: AsciiString
    scope_ref: AsciiString
    status: Literal["BLOCKED", "USABLE_WITH_REVIEW", "APPROVED"]
    basis_refs: tuple[AsciiString, ...]
    limitation_codes: tuple[AsciiString, ...]
    assessed_by_ref: AsciiString


class JourneyLink(PublicContractModel):
    journey_id: Literal["O-J01", "O-J02", "O-J03", "O-SJ01"]
    label: AsciiString
    route: AsciiString
    availability: Literal["AVAILABLE", "UNAVAILABLE"]


class ReportingVersionSummary(PublicContractModel):
    reporting_version_ref: AsciiString
    version: PositiveInt
    publication_origin: Literal["PRE_SCOPE_IMPORT", "RESTATEMENT_PUBLICATION"]
    published_at: Timestamp
    content_verification_status: Literal[
        "CONTENT_BYTES_VERIFIED",
        "DECLARED_HASH_ONLY",
        "MISSING",
        "UNAVAILABLE",
    ]
    statement_values: tuple[StatementValue, ...]


class RestatementBridgeItem(PublicContractModel):
    predecessor_version_ref: AsciiString
    successor_version_ref: AsciiString
    statement_field: AsciiString
    adjustment_minor: int
    currency: Currency
    restatement_case_ref: AsciiString


class JournalBalanceResult(PublicContractModel):
    journal_ref: AsciiString
    debits_minor: NonNegativeInt
    credits_minor: NonNegativeInt
    currency: Currency
    balanced: bool


class TraceNodeView(PublicContractModel):
    node_ref: AsciiString
    role: AsciiString
    record_family: AsciiString
    record_identity: AsciiString
    semantic_hash: HashValue | None


class TraceEdgeView(PublicContractModel):
    source_ref: AsciiString
    target_ref: AsciiString
    relationship: AsciiString


class DemoManifestView(PublicContractModel):
    workspace_ref: AsciiString
    runtime_release: AsciiString
    synthetic_data_notice: AsciiString
    scenario_summaries: tuple[ScenarioSummary, ...]
    scenario_entry_points: tuple[ScenarioEntryPoint, ...]
    authoritative_inventory_digest: HashValue
    projection_generation_ref: AsciiString
    verification_status: Literal["VERIFIED", "FAILED"]


class PlatformOverviewView(PublicContractModel):
    company_label: AsciiString
    reporting_period: PeriodId
    headline_reporting_version_ref: AsciiString
    headline_values: tuple[HeadlineValue, ...]
    module_summaries: tuple[ModuleSummary, ...]
    machine_exception_count: NonNegativeInt
    governance_issue_states: tuple[GovernanceIssueState, ...]
    readiness_summary: tuple[ReadinessSummary, ...]
    governed_decision_ref: AsciiString
    journey_links: tuple[JourneyLink, ...]


class RecognitionPopulationReconciliationView(PublicContractModel):
    reconciliation_ref: AsciiString
    reconciliation_type: Literal["RECOGNITION_POPULATION"]
    scope_ref: AsciiString
    performed_at: Timestamp
    source_refs: tuple[AsciiString, ...]
    reconciliation_status: Literal["PASSED", "FAILED", "REVIEW"]
    downstream_exception_ref: AsciiString
    period_id: PeriodId
    expected_item_count: NonNegativeInt
    posted_item_count: NonNegativeInt
    submitted_unposted_count: NonNegativeInt
    deferred_count: NonNegativeInt
    expected_amount_minor: NonNegativeInt
    posted_amount_minor: NonNegativeInt
    difference_minor: int
    currency: Currency


class CashApplicationIdentityReconciliationView(PublicContractModel):
    reconciliation_ref: AsciiString
    reconciliation_type: Literal["CASH_APPLICATION_IDENTITY"]
    scope_ref: AsciiString
    performed_at: Timestamp
    source_refs: tuple[AsciiString, ...]
    reconciliation_status: Literal["PASSED", "FAILED", "REVIEW"]
    downstream_exception_ref: AsciiString
    cash_application_ref: AsciiString
    receipt_party_ref: AsciiString
    application_party_ref: AsciiString
    party_mapping_ref: AsciiString
    identity_match: bool


type SourceReconciliationView = Annotated[
    RecognitionPopulationReconciliationView
    | CashApplicationIdentityReconciliationView,
    Field(discriminator="reconciliation_type"),
]


class ReportingHistoryView(PublicContractModel):
    period_id: PeriodId
    versions: tuple[ReportingVersionSummary, ...]
    restatement_bridge: tuple[RestatementBridgeItem, ...]


class ReportingVersionBase(PublicContractModel):
    reporting_version_ref: AsciiString
    period_id: PeriodId
    version: PositiveInt
    published_at: Timestamp
    statement_values: tuple[StatementValue, ...]
    currency: Currency
    content_ref: AsciiString
    content_verification_status: Literal[
        "CONTENT_BYTES_VERIFIED",
        "DECLARED_HASH_ONLY",
        "MISSING",
        "UNAVAILABLE",
    ]
    traceable_fields: tuple[AsciiString, ...]


class PreScopeReportingVersionView(ReportingVersionBase):
    publication_origin: Literal["PRE_SCOPE_IMPORT"]
    import_attestation_ref: AsciiString
    original_authority_ref: AsciiString
    source_ref: AsciiString


class RestatedReportingVersionView(ReportingVersionBase):
    publication_origin: Literal["RESTATEMENT_PUBLICATION"]
    predecessor_version_ref: AsciiString
    restatement_case_ref: AsciiString
    manifest_hash: HashValue
    published_by_event_id: AsciiString


type ReportingVersionView = Annotated[
    PreScopeReportingVersionView | RestatedReportingVersionView,
    Field(discriminator="publication_origin"),
]


class RecognitionCompletenessExceptionView(PublicContractModel):
    test_run_ref: AsciiString
    test_definition_ref: AsciiString
    exception_ref: AsciiString
    exception_type: Literal["RECOGNITION_COMPLETENESS"]
    assertion: AsciiString
    severity: AsciiString
    evidence_refs: tuple[AsciiString, ...]
    related_governance_case_ref: AsciiString
    subject_refs: tuple[AsciiString, ...]
    period_id: PeriodId
    expected_amount_minor: NonNegativeInt
    actual_amount_minor: NonNegativeInt
    difference_minor: int
    currency: Currency


class CashApplicationIdentityExceptionView(PublicContractModel):
    test_run_ref: AsciiString
    test_definition_ref: AsciiString
    exception_ref: AsciiString
    exception_type: Literal["CASH_APPLICATION_IDENTITY"]
    assertion: AsciiString
    severity: AsciiString
    evidence_refs: tuple[AsciiString, ...]
    related_governance_case_ref: AsciiString
    receipt_party_ref: AsciiString
    application_party_ref: AsciiString
    journal_id: AsciiString
    amount_minor: NonNegativeInt
    currency: Currency


type AssuranceExceptionView = Annotated[
    RecognitionCompletenessExceptionView | CashApplicationIdentityExceptionView,
    Field(discriminator="exception_type"),
]


class GovernanceCaseView(PublicContractModel):
    exception_ref: AsciiString
    review_ref: AsciiString
    review_disposition: AsciiString
    finding_ref: AsciiString
    initial_issue_ref: AsciiString
    initial_issue_status: AsciiString
    owner_ref: AsciiString
    remediation_directive_ref: AsciiString
    correction_refs: tuple[AsciiString, ...]
    verification_ref: AsciiString
    prior_issue_refs: tuple[AsciiString, ...]
    final_issue_ref: AsciiString
    final_issue_status: AsciiString
    readiness_refs: tuple[AsciiString, ...]


class ReadinessRow(PublicContractModel):
    readiness_ref: AsciiString
    purpose_ref: AsciiString
    scope_ref: AsciiString
    status: Literal["BLOCKED", "USABLE_WITH_REVIEW", "APPROVED"]
    basis_refs: tuple[AsciiString, ...]
    limitation_codes: tuple[AsciiString, ...]
    assessed_by_ref: AsciiString


class ReadinessMatrixView(PublicContractModel):
    reporting_version_ref: AsciiString
    period_id: PeriodId
    rows: tuple[ReadinessRow, ...]


class GovernedDecisionView(PublicContractModel):
    planning_input_ref: AsciiString
    reporting_version_ref: AsciiString
    readiness_ref: AsciiString
    purpose_ref: AsciiString
    scope_ref: AsciiString
    frozen_input_refs: tuple[AsciiString, ...]
    decision_ref: AsciiString
    decision_type: AsciiString
    position_ref: AsciiString
    original_start_date: DateString
    recommended_start_date: DateString
    monthly_cost_minor: NonNegativeInt
    currency: Currency
    reason_code: AsciiString
    approval_ref: AsciiString
    approval_outcome: Literal["APPROVED", "REJECTED"]
    candidate_ref: AsciiString
    candidate_admission_outcome: Literal["ACCEPTED", "REJECTED", "UNSUPPORTED"]


class ReportingValueTraceView(PublicContractModel):
    reporting_version_ref: AsciiString
    statement_field: AsciiString
    statement_value_minor: int
    currency: Currency
    content_verification_status: Literal["CONTENT_BYTES_VERIFIED"]
    nodes: tuple[TraceNodeView, ...]
    edges: tuple[TraceEdgeView, ...]


class CorrectionIntegrityView(PublicContractModel):
    source_projection_ref: AsciiString
    source_projection_hash: HashValue
    reversal_proposal_ref: AsciiString
    reversal_journal_ref: AsciiString
    replacement_proposal_ref: AsciiString
    replacement_journal_ref: AsciiString
    identity_before: AsciiString
    identity_after: AsciiString
    reversal_binding_status: Literal["BOUND_BEFORE_COMPARE"]
    journal_balance_results: tuple[JournalBalanceResult, ...]
    control_account_net_movement_minor: int
    currency: Currency
    verification_ref: AsciiString
    issue_update_ref: AsciiString


class _SuccessEnvelope(PublicContractModel):
    view_contract_version: Literal[1]
    scenario_ref: AsciiString
    semantic_as_of_time: Timestamp
    query_revision: NonNegativeInt
    compatibility_read_mode: Literal["EXACT_ORIGINAL"]
    source_refs: tuple[AsciiString, ...]

    @model_validator(mode="after")
    def source_refs_are_sorted_unique(self) -> _SuccessEnvelope:
        if self.source_refs != tuple(sorted(set(self.source_refs))):
            raise ValueError("source_refs must be sorted and unique")
        return self


class DemoManifestEnvelope(_SuccessEnvelope):
    view_contract: Literal["O-V01"]
    data: DemoManifestView


class PlatformOverviewEnvelope(_SuccessEnvelope):
    view_contract: Literal["O-V02"]
    data: PlatformOverviewView


class SourceReconciliationEnvelope(_SuccessEnvelope):
    view_contract: Literal["O-V03"]
    data: SourceReconciliationView


class ReportingHistoryEnvelope(_SuccessEnvelope):
    view_contract: Literal["O-V04"]
    data: ReportingHistoryView


class ReportingVersionEnvelope(_SuccessEnvelope):
    view_contract: Literal["O-V05"]
    data: ReportingVersionView


class AssuranceExceptionEnvelope(_SuccessEnvelope):
    view_contract: Literal["O-V06"]
    data: AssuranceExceptionView


class GovernanceCaseEnvelope(_SuccessEnvelope):
    view_contract: Literal["O-V07"]
    data: GovernanceCaseView


class ReadinessMatrixEnvelope(_SuccessEnvelope):
    view_contract: Literal["O-V08"]
    data: ReadinessMatrixView


class GovernedDecisionEnvelope(_SuccessEnvelope):
    view_contract: Literal["O-V09"]
    data: GovernedDecisionView


class ReportingValueTraceEnvelope(_SuccessEnvelope):
    view_contract: Literal["O-V10"]
    data: ReportingValueTraceView


class CorrectionIntegrityEnvelope(_SuccessEnvelope):
    view_contract: Literal["O-V11"]
    data: CorrectionIntegrityView


type PublicSuccessEnvelope = Annotated[
    DemoManifestEnvelope
    | PlatformOverviewEnvelope
    | SourceReconciliationEnvelope
    | ReportingHistoryEnvelope
    | ReportingVersionEnvelope
    | AssuranceExceptionEnvelope
    | GovernanceCaseEnvelope
    | ReadinessMatrixEnvelope
    | GovernedDecisionEnvelope
    | ReportingValueTraceEnvelope
    | CorrectionIntegrityEnvelope,
    Field(discriminator="view_contract"),
]


class StartupFailureEnvelope(PublicContractModel):
    error_code: Literal["DEMO_NOT_INITIALISED", "UNSUPPORTED_CONTRACT"]
    message: AsciiString
    scenario_ref: AsciiString
    subject_ref: AsciiString


class RuntimeFailureEnvelope(PublicContractModel):
    error_code: Literal[
        "NOT_FOUND",
        "UNAVAILABLE",
        "UNVERIFIED_CONTENT",
        "REVISION_CONFLICT",
        "TRACE_INTEGRITY_FAILURE",
        "INTERNAL_FAILURE",
    ]
    message: AsciiString
    scenario_ref: AsciiString
    subject_ref: AsciiString
    query_revision: NonNegativeInt


type PublicFailureEnvelope = Annotated[
    StartupFailureEnvelope | RuntimeFailureEnvelope,
    Field(discriminator="error_code"),
]


PUBLIC_SUCCESS_ADAPTER = TypeAdapter(PublicSuccessEnvelope)
PUBLIC_FAILURE_ADAPTER = TypeAdapter(PublicFailureEnvelope)
