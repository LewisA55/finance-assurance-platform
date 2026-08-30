export type PublicScenarioRef =
  | "DEMO-C001-RESTATEMENT@v1"
  | "DEMO-CT1-CORRECTION@v1";

export const PUBLIC_CONTEXT = {
  viewContractVersion: "1",
  scenarioRef: "DEMO-C001-RESTATEMENT@v1" as PublicScenarioRef,
  semanticAsOfTime: "2026-07-14T12:00:00Z",
} as const;

export const CT1_CONTEXT = {
  ...PUBLIC_CONTEXT,
  scenarioRef: "DEMO-CT1-CORRECTION@v1" as PublicScenarioRef,
} as const;

const CT1_SUBJECT_REFS = new Set([
  "RECON-CT1@v1",
  "EXC-CT1@v1",
  "ISSUE-CT1@v1",
  "ISSUE-CT1@v2",
  "VERIFY-CT1@v1",
]);

export function scenarioForSubject(subjectRef: string): PublicScenarioRef {
  return CT1_SUBJECT_REFS.has(subjectRef)
    ? CT1_CONTEXT.scenarioRef
    : PUBLIC_CONTEXT.scenarioRef;
}

export function getGovernedDecision(decisionRef: string): Promise<GovernedDecision> {
  return get<GovernedDecision>(
    `/api/v1/pythia/decisions/${encodeURIComponent(decisionRef)}`,
    "O-V09",
  );
}

export function getCorrectionIntegrity(
  verificationRef: string,
): Promise<CorrectionIntegrity> {
  return get<CorrectionIntegrity>(
    `/api/v1/corrections/${encodeURIComponent(verificationRef)}`,
    "O-V11",
    { scenarioRef: scenarioForSubject(verificationRef) },
  );
}

export type VerificationStatus =
  | "CONTENT_BYTES_VERIFIED"
  | "DECLARED_HASH_ONLY"
  | "MISSING"
  | "UNAVAILABLE";

export type HeadlineValue = {
  field: string;
  label: string;
  amount_minor: number;
  currency: "GBP";
  reporting_version_ref: string;
  content_verification_status: VerificationStatus;
  trace_available: boolean;
};

export type SuccessEnvelope<T, V extends string> = {
  view_contract: V;
  view_contract_version: 1;
  scenario_ref: PublicScenarioRef;
  semantic_as_of_time: string;
  query_revision: number;
  compatibility_read_mode: "EXACT_ORIGINAL";
  data: T;
  source_refs: string[];
};

type FailureEnvelope = {
  error_code: string;
  message: string;
  scenario_ref: string;
  subject_ref: string;
  query_revision?: number;
};

export type DemoManifest = SuccessEnvelope<
  {
    workspace_ref: string;
    runtime_release: string;
    synthetic_data_notice: string;
    scenario_summaries: Array<{
      scenario_ref: PublicScenarioRef;
      canonical_family: string;
      status: string;
      public_role: string;
      entry_point_count: number;
    }>;
    scenario_entry_points: Array<{
      journey_id: "O-J01" | "O-J02" | "O-J03" | "O-SJ01";
      semantic_role: string;
      exact_ref: string;
      source_kind: "AUTHORITATIVE_RECORD";
      availability: "AVAILABLE" | "UNAVAILABLE";
    }>;
    authoritative_inventory_digest: string;
    projection_generation_ref: string;
    verification_status: "VERIFIED" | "FAILED";
  },
  "O-V01"
>;

export type GovernedDecision = SuccessEnvelope<
  {
    planning_input_ref: string;
    reporting_version_ref: string;
    readiness_ref: string;
    purpose_ref: string;
    scope_ref: string;
    frozen_input_refs: string[];
    decision_ref: string;
    decision_type: string;
    position_ref: string;
    original_start_date: string;
    recommended_start_date: string;
    monthly_cost_minor: number;
    currency: "GBP";
    reason_code: string;
    approval_ref: string;
    approval_outcome: "APPROVED" | "REJECTED";
    candidate_ref: string;
    candidate_admission_outcome: "ACCEPTED" | "REJECTED" | "UNSUPPORTED";
  },
  "O-V09"
>;

export type CorrectionIntegrity = SuccessEnvelope<
  {
    source_projection_ref: string;
    source_projection_hash: string;
    reversal_proposal_ref: string;
    reversal_journal_ref: string;
    replacement_proposal_ref: string;
    replacement_journal_ref: string;
    identity_before: string;
    identity_after: string;
    reversal_binding_status: "BOUND_BEFORE_COMPARE";
    journal_balance_results: Array<{
      journal_ref: string;
      debits_minor: number;
      credits_minor: number;
      currency: "GBP";
      balanced: boolean;
    }>;
    control_account_net_movement_minor: number;
    currency: "GBP";
    verification_ref: string;
    issue_update_ref: string;
  },
  "O-V11"
>;

export type SourceReconciliation = SuccessEnvelope<
  | {
      reconciliation_ref: string;
      reconciliation_type: "RECOGNITION_POPULATION";
      scope_ref: string;
      performed_at: string;
      source_refs: string[];
      reconciliation_status: "PASSED" | "FAILED" | "REVIEW";
      downstream_exception_ref: string;
      period_id: string;
      expected_item_count: number;
      posted_item_count: number;
      submitted_unposted_count: number;
      deferred_count: number;
      expected_amount_minor: number;
      posted_amount_minor: number;
      difference_minor: number;
      currency: "GBP";
    }
  | {
      reconciliation_ref: string;
      reconciliation_type: "CASH_APPLICATION_IDENTITY";
      scope_ref: string;
      performed_at: string;
      source_refs: string[];
      reconciliation_status: "PASSED" | "FAILED" | "REVIEW";
      downstream_exception_ref: string;
      cash_application_ref: string;
      receipt_party_ref: string;
      application_party_ref: string;
      party_mapping_ref: string;
      identity_match: boolean;
    },
  "O-V03"
>;

export type ReportingHistory = SuccessEnvelope<
  {
    period_id: string;
    versions: Array<{
      reporting_version_ref: string;
      version: number;
      publication_origin: "PRE_SCOPE_IMPORT" | "RESTATEMENT_PUBLICATION";
      published_at: string;
      content_verification_status: VerificationStatus;
      statement_values: HeadlineValue[];
    }>;
    restatement_bridge: Array<{
      predecessor_version_ref: string;
      successor_version_ref: string;
      statement_field: string;
      adjustment_minor: number;
      currency: "GBP";
      restatement_case_ref: string;
    }>;
  },
  "O-V04"
>;

export type AssuranceException = SuccessEnvelope<
  | {
      test_run_ref: string;
      test_definition_ref: string;
      exception_ref: string;
      exception_type: "RECOGNITION_COMPLETENESS";
      assertion: string;
      severity: string;
      evidence_refs: string[];
      related_governance_case_ref: string;
      subject_refs: string[];
      period_id: string;
      expected_amount_minor: number;
      actual_amount_minor: number;
      difference_minor: number;
      currency: "GBP";
    }
  | {
      test_run_ref: string;
      test_definition_ref: string;
      exception_ref: string;
      exception_type: "CASH_APPLICATION_IDENTITY";
      assertion: string;
      severity: string;
      evidence_refs: string[];
      related_governance_case_ref: string;
      receipt_party_ref: string;
      application_party_ref: string;
      journal_id: string;
      amount_minor: number;
      currency: "GBP";
    },
  "O-V06"
>;

export type GovernanceCase = SuccessEnvelope<
  {
    exception_ref: string;
    review_ref: string;
    review_disposition: string;
    finding_ref: string;
    initial_issue_ref: string;
    initial_issue_status: string;
    owner_ref: string;
    remediation_directive_ref: string;
    correction_refs: string[];
    verification_ref: string;
    prior_issue_refs: string[];
    final_issue_ref: string;
    final_issue_status: string;
    readiness_refs: string[];
  },
  "O-V07"
>;

export type ReadinessMatrix = SuccessEnvelope<
  {
    reporting_version_ref: string;
    period_id: string;
    rows: Array<{
      readiness_ref: string;
      purpose_ref: string;
      scope_ref: string;
      status: "BLOCKED" | "USABLE_WITH_REVIEW" | "APPROVED";
      basis_refs: string[];
      limitation_codes: string[];
      assessed_by_ref: string;
    }>;
  },
  "O-V08"
>;

export type PlatformOverview = SuccessEnvelope<
  {
    company_label: string;
    reporting_period: string;
    headline_reporting_version_ref: string;
    headline_values: HeadlineValue[];
    module_summaries: Array<{
      module: "Hermes" | "Atlas" | "Argus" | "Aegis" | "Pythia";
      summary_code: string;
      primary_product_ref: string;
      route: string;
    }>;
    machine_exception_count: number;
    governance_issue_states: Array<{
      issue_ref: string;
      status: string;
      owner_ref: string;
    }>;
    readiness_summary: Array<{
      readiness_ref: string;
      reporting_version_ref: string;
      period_id: string;
      purpose_ref: string;
      scope_ref: string;
      status: "BLOCKED" | "USABLE_WITH_REVIEW" | "APPROVED";
      basis_refs: string[];
      limitation_codes: string[];
      assessed_by_ref: string;
    }>;
    governed_decision_ref: string;
    journey_links: Array<{
      journey_id: string;
      label: string;
      route: string;
      availability: "AVAILABLE" | "UNAVAILABLE";
    }>;
  },
  "O-V02"
>;

export type ReportingVersion = SuccessEnvelope<
  {
    reporting_version_ref: string;
    period_id: string;
    version: number;
    published_at: string;
    statement_values: HeadlineValue[];
    currency: "GBP";
    content_ref: string;
    content_verification_status: VerificationStatus;
    traceable_fields: string[];
    publication_origin: "PRE_SCOPE_IMPORT" | "RESTATEMENT_PUBLICATION";
    predecessor_version_ref?: string;
    restatement_case_ref?: string;
    manifest_hash?: string;
    published_by_event_id?: string;
    import_attestation_ref?: string;
    original_authority_ref?: string;
    source_ref?: string;
  },
  "O-V05"
>;

export type ReportingTrace = SuccessEnvelope<
  {
    reporting_version_ref: string;
    statement_field: string;
    statement_value_minor: number;
    currency: "GBP";
    content_verification_status: "CONTENT_BYTES_VERIFIED";
    nodes: Array<{
      node_ref: string;
      role: string;
      record_family: string;
      record_identity: string;
      semantic_hash: string | null;
    }>;
    edges: Array<{
      source_ref: string;
      target_ref: string;
      relationship: string;
    }>;
  },
  "O-V10"
>;

export class PublicApiError extends Error {
  readonly code: string;
  readonly subjectRef: string;
  readonly queryRevision?: number;

  constructor(failure: FailureEnvelope) {
    super(failure.message);
    this.name = "PublicApiError";
    this.code = failure.error_code;
    this.subjectRef = failure.subject_ref;
    this.queryRevision = failure.query_revision;
  }
}

export function getSourceReconciliation(
  reconciliationRef: string,
): Promise<SourceReconciliation> {
  return get<SourceReconciliation>(
    `/api/v1/hermes/reconciliations/${encodeURIComponent(reconciliationRef)}`,
    "O-V03",
    { scenarioRef: scenarioForSubject(reconciliationRef) },
  );
}

export function getReportingHistory(periodId: string): Promise<ReportingHistory> {
  return get<ReportingHistory>(
    `/api/v1/atlas/reporting-periods/${encodeURIComponent(periodId)}`,
    "O-V04",
  );
}

export function getAssuranceException(
  exceptionRef: string,
): Promise<AssuranceException> {
  return get<AssuranceException>(
    `/api/v1/argus/exceptions/${encodeURIComponent(exceptionRef)}`,
    "O-V06",
    { scenarioRef: scenarioForSubject(exceptionRef) },
  );
}

export function getGovernanceCase(issueRef: string): Promise<GovernanceCase> {
  return get<GovernanceCase>(
    `/api/v1/aegis/cases/${encodeURIComponent(issueRef)}`,
    "O-V07",
    { scenarioRef: scenarioForSubject(issueRef) },
  );
}

export function getReadinessMatrix(
  reportingVersionRef: string,
): Promise<ReadinessMatrix> {
  return get<ReadinessMatrix>(
    `/api/v1/aegis/readiness/${encodeURIComponent(reportingVersionRef)}`,
    "O-V08",
    {
      query: {
        period_id: "2026-06",
        purpose_ref: "HIRING-FORECAST",
        scope_ref: "NEXUS-GROUP",
      },
    },
  );
}

function queryString(
  scenarioRef: PublicScenarioRef,
  additional: Record<string, string> = {},
): string {
  return new URLSearchParams({
    view_contract_version: PUBLIC_CONTEXT.viewContractVersion,
    scenario_ref: scenarioRef,
    semantic_as_of_time: PUBLIC_CONTEXT.semanticAsOfTime,
    ...additional,
  }).toString();
}

async function get<T>(
  path: string,
  expectedView: string,
  options: {
    scenarioRef?: PublicScenarioRef;
    query?: Record<string, string>;
  } = {},
): Promise<T> {
  const response = await fetch(
    `${path}?${queryString(options.scenarioRef ?? PUBLIC_CONTEXT.scenarioRef, options.query)}`,
    {
    cache: "no-store",
    headers: { Accept: "application/json" },
    },
  );
  const payload = (await response.json()) as T | FailureEnvelope;
  if (!response.ok) {
    throw new PublicApiError(payload as FailureEnvelope);
  }
  const envelope = payload as { view_contract?: string };
  if (envelope.view_contract !== expectedView) {
    throw new Error("The public API returned an unexpected view contract.");
  }
  return payload as T;
}

export function getDemoManifest(): Promise<DemoManifest> {
  return get<DemoManifest>("/api/v1/demo", "O-V01");
}

export function getPlatformOverview(): Promise<PlatformOverview> {
  return get<PlatformOverview>("/api/v1/overview", "O-V02");
}

export function getReportingVersion(
  reportingVersionRef: string,
): Promise<ReportingVersion> {
  return get<ReportingVersion>(
    `/api/v1/atlas/reporting-versions/${encodeURIComponent(reportingVersionRef)}`,
    "O-V05",
  );
}

export function getReportingTrace(
  reportingVersionRef: string,
  statementField: string,
): Promise<ReportingTrace> {
  return get<ReportingTrace>(
    `/api/v1/traces/reporting-values/${encodeURIComponent(reportingVersionRef)}/${encodeURIComponent(statementField)}`,
    "O-V10",
  );
}

export function formatMinorUnits(amountMinor: number, currency: "GBP"): string {
  const sign = amountMinor < 0 ? "-" : "";
  const absolute = Math.abs(amountMinor);
  const major = Math.floor(absolute / 100);
  const minor = absolute % 100;
  const symbol = currency === "GBP" ? "GBP " : `${currency} `;
  return `${sign}${symbol}${new Intl.NumberFormat("en-GB").format(major)}.${String(minor).padStart(2, "0")}`;
}

export function humanizeCode(value: string): string {
  return value
    .toLowerCase()
    .split("_")
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}
