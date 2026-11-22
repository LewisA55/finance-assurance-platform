import {
  CT1_CONTEXT,
  PUBLIC_CONTEXT,
  formatMinorUnits,
  getAssuranceException,
  getCorrectionIntegrity,
  getGovernanceCase,
  getGovernedDecision,
  getReadinessMatrix,
  getReportingHistory,
  getReportingTrace,
  getSourceReconciliation,
  humanizeCode,
  type GovernanceCase,
  type PublicScenarioRef,
  type ReportingTrace,
} from "./public-api";

export type ExplorerStage = {
  title: string;
  owner: string;
  facts: Array<[string, string]>;
  link: { href: string; label: string };
  trace?: ReportingTrace["data"];
};

type ExplorerContext = {
  scenario_ref: PublicScenarioRef;
  semantic_as_of_time: string;
  compatibility_read_mode: "EXACT_ORIGINAL";
  query_revision: number;
};

type ExplorerCase = {
  context: ExplorerContext;
  stages: ExplorerStage[];
};

function requireBinding(condition: unknown): asserts condition {
  if (!condition) throw new Error("The case records could not be joined by their exact references.");
}

function checkContext(expected: PublicScenarioRef, reads: ExplorerContext[]) {
  const first = reads[0];
  requireBinding(reads.every((read) =>
    read.scenario_ref === expected &&
    read.semantic_as_of_time === PUBLIC_CONTEXT.semanticAsOfTime &&
    read.compatibility_read_mode === "EXACT_ORIGINAL" &&
    read.query_revision === first.query_revision,
  ));
  return first;
}

function subjectLink(path: string, ref: string, label: string) {
  return { href: `${path}/${encodeURIComponent(ref)}`, label };
}

function governanceStages({ data }: GovernanceCase): ExplorerStage[] {
  const link = subjectLink("/aegis/cases", data.final_issue_ref, "Open governance case");
  return [
    {
      title: "Review, finding and issue",
      owner: "Aegis",
      facts: [
        ["Review", data.review_ref],
        ["Disposition", humanizeCode(data.review_disposition)],
        ["Finding", data.finding_ref],
        ["Initial issue", data.initial_issue_ref],
      ],
      link,
    },
    {
      title: "Remediation and verification",
      owner: "Aegis / Argus",
      facts: [
        ["Directive", data.remediation_directive_ref],
        ["Correction records", data.correction_refs.join(", ")],
        ["Verification", data.verification_ref],
        ["Updated issue", data.final_issue_ref],
        ["Issue status", humanizeCode(data.final_issue_status)],
      ],
      link,
    },
  ];
}

async function loadRevenueCase(): Promise<ExplorerCase> {
  const version = "RV-2026-06@v2";
  const field = "subscription_revenue_minor";
  const [recon, history, trace, exception, governance, readiness, decision] = await Promise.all([
    getSourceReconciliation("RECON-C001@v1"),
    getReportingHistory("2026-06"),
    getReportingTrace(version, field),
    getAssuranceException("EXC-C001@v1"),
    getGovernanceCase("ISSUE-C001@v1"),
    getReadinessMatrix(version),
    getGovernedDecision("DECISION-C001@v1"),
  ]);
  const context = checkContext(PUBLIC_CONTEXT.scenarioRef, [recon, history, trace, exception, governance, readiness, decision]);
  const basis = readiness.data.rows.find((row) => row.readiness_ref === decision.data.readiness_ref);
  const published = history.data.versions.find((item) => item.reporting_version_ref === version);
  const predecessor = history.data.restatement_bridge.find((item) =>
    item.successor_version_ref === version && item.statement_field === field,
  );
  const original = history.data.versions.find((item) => item.reporting_version_ref === predecessor?.predecessor_version_ref);
  const originalValue = original?.statement_values.find((item) => item.field === field);
  const publishedValue = published?.statement_values.find((item) => item.field === field);
  requireBinding(
    recon.data.reconciliation_type === "RECOGNITION_POPULATION" &&
    exception.data.exception_type === "RECOGNITION_COMPLETENESS" &&
    recon.data.downstream_exception_ref === exception.data.exception_ref &&
    exception.data.related_governance_case_ref === governance.data.final_issue_ref &&
    governance.data.exception_ref === exception.data.exception_ref &&
    original && originalValue && predecessor && publishedValue &&
    trace.data.reporting_version_ref === version && trace.data.statement_field === field &&
    trace.data.content_verification_status === "CONTENT_BYTES_VERIFIED" &&
    trace.data.statement_value_minor === publishedValue.amount_minor && trace.data.currency === publishedValue.currency &&
    readiness.data.reporting_version_ref === version && decision.data.reporting_version_ref === version &&
    basis?.status === "APPROVED" && basis.purpose_ref === decision.data.purpose_ref &&
    basis.scope_ref === decision.data.scope_ref &&
    governance.data.readiness_refs.includes(basis.readiness_ref),
  );

  const traceLink = subjectLink(`/trace/reporting/${encodeURIComponent(version)}`, field, "Open verified statement trace");
  const traceFacts: ExplorerStage["facts"] = [];
  for (const [role, label] of [
    ["source_reference", "Source reference"],
    ["business_event", "Business event"],
    ["posting_rule", "Posting rule version"],
    ["proposal", "Journal proposal"],
    ["journal", "Posted journal"],
  ]) {
    for (const node of trace.data.nodes.filter((item) => item.role === role)) {
      traceFacts.push([label, node.record_identity]);
    }
  }

  return {
    context,
    stages: [
      {
        title: "Source reconciliation",
        owner: "Hermes",
        facts: [
          ["Recognition schedule", recon.data.source_refs.join(", ")],
          ["Reconciliation", recon.data.reconciliation_ref],
          ["Expected versus posted", `${recon.data.expected_item_count} expected / ${recon.data.posted_item_count} posted`],
          ["Recognition gap", formatMinorUnits(recon.data.difference_minor, recon.data.currency)],
        ],
        link: subjectLink("/hermes/reconciliation", recon.data.reconciliation_ref, "Open recognition reconciliation"),
      },
      {
        title: "Completeness control and exception",
        owner: "Argus",
        facts: [
          ["Control definition", exception.data.test_definition_ref],
          ["Control run", exception.data.test_run_ref],
          ["Exception", exception.data.exception_ref],
          ["Evidence", exception.data.evidence_refs.join(", ")],
        ],
        link: subjectLink("/argus/exceptions", exception.data.exception_ref, "Open completeness exception"),
      },
      ...governanceStages(governance),
      {
        title: "Records in the restatement trace",
        owner: "Atlas",
        facts: traceFacts,
        link: traceLink,
        trace: trace.data,
      },
      {
        title: "Original and restated subscription revenue",
        owner: "Atlas",
        facts: [
          ["Original reporting version", original.reporting_version_ref],
          ["Original value", formatMinorUnits(originalValue.amount_minor, originalValue.currency)],
          ["Restatement case", predecessor.restatement_case_ref],
          ["Restated reporting version", version],
          ["Restated value", formatMinorUnits(trace.data.statement_value_minor, trace.data.currency)],
          ["Statement field", trace.data.statement_field],
        ],
        link: subjectLink("/atlas/reporting", history.data.period_id, "Compare reporting versions"),
      },
      {
        title: "Readiness for the hiring forecast",
        owner: "Aegis",
        facts: [["Assessment", basis.readiness_ref], ["Purpose", basis.purpose_ref], ["Scope", basis.scope_ref], ["Status", humanizeCode(basis.status)]],
        link: subjectLink("/aegis/readiness", version, "Open purpose-specific readiness"),
      },
      {
        title: "Hiring decision",
        owner: "Pythia",
        facts: [
          ["Frozen planning input", decision.data.planning_input_ref],
          ["Reporting version", decision.data.reporting_version_ref],
          ["Readiness consumed", decision.data.readiness_ref],
          ["Decision", decision.data.decision_ref],
          ["Recommendation", humanizeCode(decision.data.decision_type)],
          ["Start date change", `${decision.data.original_start_date} to ${decision.data.recommended_start_date}`],
          ["Monthly cost", formatMinorUnits(decision.data.monthly_cost_minor, decision.data.currency)],
          ["Business approval", humanizeCode(decision.data.approval_outcome)],
          ["Returned candidate admission", humanizeCode(decision.data.candidate_admission_outcome)],
        ],
        link: subjectLink("/pythia/decisions", decision.data.decision_ref, "Open governed decision"),
      },
    ],
  };
}

async function loadCashCase(): Promise<ExplorerCase> {
  const [recon, exception, governance, correction] = await Promise.all([
    getSourceReconciliation("RECON-CT1@v1"),
    getAssuranceException("EXC-CT1@v1"),
    getGovernanceCase("ISSUE-CT1@v1"),
    getCorrectionIntegrity("VERIFY-CT1@v1"),
  ]);
  const context = checkContext(CT1_CONTEXT.scenarioRef, [recon, exception, governance, correction]);
  requireBinding(
    recon.data.reconciliation_type === "CASH_APPLICATION_IDENTITY" &&
    exception.data.exception_type === "CASH_APPLICATION_IDENTITY" &&
    recon.data.downstream_exception_ref === exception.data.exception_ref &&
    exception.data.related_governance_case_ref === governance.data.final_issue_ref &&
    governance.data.exception_ref === exception.data.exception_ref &&
    governance.data.verification_ref === correction.data.verification_ref &&
    governance.data.final_issue_ref === correction.data.issue_update_ref,
  );
  return {
    context,
    stages: [
      {
        title: "Cash application and source identity",
        owner: "Hermes",
        facts: [
          ["Cash application", recon.data.cash_application_ref],
          ["Receipt party", recon.data.receipt_party_ref],
          ["Application party", recon.data.application_party_ref],
          ["Party mapping", recon.data.party_mapping_ref],
          ["Reconciliation", recon.data.reconciliation_ref],
          ["Source references", recon.data.source_refs.join(", ")],
        ],
        link: subjectLink("/hermes/reconciliation", recon.data.reconciliation_ref, "Open identity reconciliation"),
      },
      {
        title: "Accuracy control and exception",
        owner: "Argus",
        facts: [
          ["Referenced journal", exception.data.journal_id],
          ["Control definition", exception.data.test_definition_ref],
          ["Control run", exception.data.test_run_ref],
          ["Exception", exception.data.exception_ref],
          ["Evidence", exception.data.evidence_refs.join(", ")],
        ],
        link: subjectLink("/argus/exceptions", exception.data.exception_ref, "Open accuracy exception"),
      },
      ...governanceStages(governance),
      {
        title: "Reversal and replacement proof",
        owner: "Atlas / Argus",
        facts: [
          ["Source projection", correction.data.source_projection_ref],
          ["Reversal proposal", correction.data.reversal_proposal_ref],
          ["Reversal journal", correction.data.reversal_journal_ref],
          ["Replacement proposal", correction.data.replacement_proposal_ref],
          ["Replacement journal", correction.data.replacement_journal_ref],
          ["Net control-account movement", formatMinorUnits(correction.data.control_account_net_movement_minor, correction.data.currency)],
        ],
        link: subjectLink("/corrections", correction.data.verification_ref, "Open correction integrity proof"),
      },
    ],
  };
}

const explorerCases = [
  {
    id: "C-001",
    title: "Missing subscription revenue",
    summary: "June hard-closes with recognition missing. The restated report becomes part of the approved input for a hiring decision.",
    load: loadRevenueCase,
  },
  {
    id: "CT-1",
    title: "Cash applied to the wrong customer",
    summary: "The public record ends with a verified reversal and replacement in the open correction path.",
    load: loadCashCase,
  },
] as const;

export function loadExplorer() {
  return Promise.all(explorerCases.map(async ({ id, title, summary, load }) => {
    try {
      return { id, title, summary, evidence: await load() };
    } catch {
      return { id, title, summary, evidence: null };
    }
  }));
}

export type ExplorerData = Awaited<ReturnType<typeof loadExplorer>>;
