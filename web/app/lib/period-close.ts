import {
  PUBLIC_CONTEXT,
  getAssuranceException,
  getReportingHistory,
  getSourceReconciliation,
} from "./public-api";

export const closeOutcomes = {
  unresolved: {
    title: "Close blocked by an unresolved proposal",
    explanation: "June remains soft-closed. The completeness gap remains open until the proposal is posted or explicitly deferred.",
    comparison: "In the recorded case, the controller deferred the proposal under the close policy before hard close.",
  },
  unsigned: {
    title: "Close blocked pending reviewer sign-off",
    explanation: "June remains soft-closed until the reviewer signs off on the selected treatment and evidence.",
    comparison: "The recorded case proceeds through an authorised close. Inspect the original and restated reporting versions below.",
  },
  resolved: {
    title: "June hard-closed after simulated posting",
    explanation: "The simulated journal recognises the missing revenue in June. The simulated completeness check passes before close.",
    comparison: "The simulation starts June reporting with the recognition included. In the recorded case, the gap was carried into June v1 and corrected through restatement.",
  },
  deferred: {
    title: "June hard-closed with authorised deferral",
    explanation: "The recognition gap carries into the original June report. A July adjustment and a separately approved restatement are needed to publish June v2.",
    comparison: "This matches the recorded C-001 path. Follow the completeness exception, reviewed finding, July adjustment and restated June report below.",
  },
} as const;

export type CloseOutcome = keyof typeof closeOutcomes;

export function readCloseOutcome(value: string | string[] | undefined): CloseOutcome | undefined {
  return typeof value === "string" && Object.hasOwn(closeOutcomes, value)
    ? value as CloseOutcome
    : undefined;
}

export async function loadPeriodCloseBasis() {
  const period = "2026-06";
  const [reconciliation, exception, history] = await Promise.all([
    getSourceReconciliation("RECON-C001@v1"),
    getAssuranceException("EXC-C001@v1"),
    getReportingHistory(period),
  ]);
  const recon = reconciliation.data;
  const control = exception.data;
  const original = history.data.versions.find((item) => item.reporting_version_ref === "RV-2026-06@v1");
  const revenue = original?.statement_values.find((item) => item.field === "subscription_revenue_minor");
  const deferredRevenue = original?.statement_values.find((item) => item.field === "deferred_revenue_minor");
  const sameContext = [reconciliation, exception, history].every((read) =>
    read.scenario_ref === PUBLIC_CONTEXT.scenarioRef &&
    read.semantic_as_of_time === PUBLIC_CONTEXT.semanticAsOfTime &&
    read.compatibility_read_mode === "EXACT_ORIGINAL" &&
    read.query_revision === history.query_revision,
  );
  if (
    !sameContext ||
    recon.reconciliation_type !== "RECOGNITION_POPULATION" ||
    control.exception_type !== "RECOGNITION_COMPLETENESS" ||
    recon.period_id !== period || control.period_id !== period || history.data.period_id !== period ||
    recon.downstream_exception_ref !== control.exception_ref ||
    recon.expected_item_count !== recon.posted_item_count + 1 ||
    recon.submitted_unposted_count !== 1 || recon.deferred_count !== 1 ||
    recon.difference_minor <= 0 || recon.difference_minor !== control.difference_minor ||
    recon.expected_amount_minor - recon.posted_amount_minor !== recon.difference_minor ||
    original?.content_verification_status !== "CONTENT_BYTES_VERIFIED" ||
    !revenue || !deferredRevenue || deferredRevenue.amount_minor < recon.difference_minor ||
    [control.currency, revenue.currency, deferredRevenue.currency].some((currency) => currency !== recon.currency)
  ) {
    throw new Error("The June close simulation requires a consistent C-001 evidence baseline.");
  }

  return {
    scenario_ref: history.scenario_ref,
    query_revision: history.query_revision,
    period,
    recon,
    control,
    originalRef: original.reporting_version_ref,
    revenueMinor: revenue.amount_minor,
    deferredRevenueMinor: deferredRevenue.amount_minor,
  };
}

export type PeriodCloseBasis = Awaited<ReturnType<typeof loadPeriodCloseBasis>>;
