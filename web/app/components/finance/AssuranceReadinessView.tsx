import Link from "next/link";
import type {
  AssuranceWarmSnapshot,
  AssuranceWorkspace,
  PackageReconciliationRow,
  ReadinessControlRow,
  ReportingVersionRow,
} from "../../lib/finance-runtime/contracts";

interface AssuranceReadinessViewProps {
  workspace: AssuranceWorkspace | null;
  warmSnapshot: AssuranceWarmSnapshot | null;
  selectedPeriod: string;
  selectedScope: string;
  runtimeReady: boolean;
}

function formatPeriod(periodId: string): string {
  const [year, month] = periodId.split("-").map(Number);
  return new Intl.DateTimeFormat("en-GB", { month: "long", year: "numeric" }).format(
    new Date(Date.UTC(year, month - 1, 1)),
  );
}

function label(value: string): string {
  return value.replaceAll("_", " ");
}

function isPassingState(value: string): boolean {
  return ["PASS", "READY", "RECONCILED", "CONSOLIDATED", "CONFIRMED", "BALANCED", "PUBLISHED", "HARD_CLOSED", "NOT_APPLICABLE"].includes(value);
}

function Status({ value }: { value: string }) {
  return <span className={`fi-control-status ${isPassingState(value) ? "pass" : "review"}`}>{label(value)}</span>;
}

function CloseMatrix({ rows, selectedScope }: { rows: ReportingVersionRow[]; selectedScope: string }) {
  return (
    <div className="fi-close-matrix-wrap">
      <table className="fi-close-matrix">
        <thead><tr><th>Reporting scope</th><th>Subledger</th><th>Bank</th><th>Intercompany</th><th>Trial balance</th><th>Statements</th><th>Close</th></tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.reporting_version_ref} className={row.scope_id === selectedScope ? "selected" : undefined}>
              <th><strong>{row.scope_id}</strong><span>{row.scope_type.replaceAll("_", " ")}</span></th>
              <td><Status value={row.subledger_reconciliation_status} /></td>
              <td><Status value={row.bank_reconciliation_status} /></td>
              <td><Status value={row.intercompany_reconciliation_status} /></td>
              <td><Status value={row.trial_balance_status} /></td>
              <td><Status value={row.statement_status} /></td>
              <td><Status value={row.close_status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function controlContext(control: ReadinessControlRow): string {
  if (control.comparison_operator === "GREATER_THAN_OR_EQUAL") return `Minimum ${control.expected_value}`;
  if (control.control_name.toLowerCase().includes("failure")) return "Expected no failures";
  return `Expected ${control.expected_value}`;
}

function ReadinessControls({ rows }: { rows: ReadinessControlRow[] }) {
  return (
    <div className="fi-readiness-control-grid">
      {rows.map((control) => (
        <article key={control.control_id}>
          <div><span>{control.control_id}</span><Status value={control.result_status} /></div>
          <h4>{control.control_name}</h4>
          <strong>{control.actual_value.toLocaleString("en-GB")}</strong>
          <small>{controlContext(control)} · {label(control.comparison_operator)}</small>
          <p>{control.evidence_relation}</p>
        </article>
      ))}
    </div>
  );
}

function criticalPackageControls(rows: PackageReconciliationRow[]) {
  const ids = [
    "C2-READINESS",
    "C2-BALANCE-SHEET",
    "C2-CASH-FLOW",
    "C2-REVENUE",
    "C2-CFO-READINESS",
    "C2-SOURCE-BINDING",
  ];
  return ids.map((id) => rows.find((row) => row.control_id === id)).filter((row): row is PackageReconciliationRow => Boolean(row));
}

export function AssuranceReadinessView({
  workspace,
  warmSnapshot,
  selectedPeriod,
  selectedScope,
  runtimeReady,
}: AssuranceReadinessViewProps) {
  const reportingVersions = workspace?.reportingVersions ?? warmSnapshot?.reportingVersions ?? [];
  const metricReadiness = workspace?.metricReadiness ?? warmSnapshot?.metricReadiness ?? [];
  const readinessControls = workspace?.readinessControls ?? warmSnapshot?.readinessControls ?? [];
  const packageControls = workspace?.packageReconciliations ?? warmSnapshot?.packageReconciliations ?? [];
  const periodVersions = reportingVersions.filter((row) => row.period_id === selectedPeriod);
  const selectedVersion = periodVersions.find((row) => row.scope_id === selectedScope) ?? periodVersions[0];
  const readinessPassed = readinessControls.filter((row) => row.result_status === "PASS").length;
  const metricsReady = metricReadiness.filter((row) => row.readiness_status === "READY").length;
  const packagePassed = packageControls.filter((row) => row.status === "PASS").length;
  const closeStatesPassing = selectedVersion
    ? [
        selectedVersion.subledger_reconciliation_status,
        selectedVersion.bank_reconciliation_status,
        selectedVersion.intercompany_reconciliation_status,
        selectedVersion.trial_balance_status,
        selectedVersion.statement_status,
        selectedVersion.close_status,
      ].filter(isPassingState).length
    : 0;

  if (!selectedVersion) {
    return <div className="fi-chart-loading"><strong>Reporting-version control state unavailable</strong><span>No governed close row exists for the selected period and scope.</span></div>;
  }

  return (
    <>
      <section className="fi-heading-row fi-performance-heading">
        <div>
          <p className="fi-eyebrow">Close assurance / Governed readiness</p>
          <h2>Assurance &amp; Control Readiness</h2>
          <p>Trace the {formatPeriod(selectedPeriod)} reporting state from reconciled close through serving controls and package evidence.</p>
        </div>
        <div className="fi-assurance-opinion-boundary">
          <span>Purpose boundary</span>
          <strong>Ready for declared analytical use</strong>
          <small>These controls support governed publication and model serving. They are not an external-audit opinion or management sign-off.</small>
        </div>
      </section>

      <section className="fi-kpi-grid fi-assurance-kpis">
        <article className="fi-kpi-card"><p>Close state</p><strong>{label(selectedVersion.close_status)}</strong><div className="fi-kpi-meta"><span className="positive">{closeStatesPassing}/6 states accepted</span><small>{selectedScope}</small></div></article>
        <article className="fi-kpi-card"><p>Readiness controls</p><strong>{readinessPassed}/{readinessControls.length}</strong><div className="fi-kpi-meta"><span className="positive">Validator produced</span><small>Model-serving purpose</small></div></article>
        <article className="fi-kpi-card"><p>Executive metrics</p><strong>{metricsReady}/{metricReadiness.length}</strong><div className="fi-kpi-meta"><span className="positive">Ready</span><small>66-month maximum coverage</small></div></article>
        <article className="fi-kpi-card"><p>Package controls</p><strong>{packagePassed}/{packageControls.length}</strong><div className="fi-kpi-meta"><span className="positive">Reproduced</span><small>Population, digest and replay</small></div></article>
        <article className="fi-kpi-card"><p>Runtime state</p><strong>{runtimeReady ? "Replayed" : "Warm state"}</strong><div className="fi-kpi-meta"><span className="neutral">Browser local</span><small>DuckDB-Wasm / governed Parquet</small></div></article>
      </section>

      <section className="fi-panel fi-close-panel">
        <div className="fi-panel-head"><div><p className="fi-eyebrow">Exact reporting versions</p><h3>Close and reconciliation matrix</h3></div><span>{selectedVersion.reporting_version_ref}</span></div>
        <CloseMatrix rows={periodVersions} selectedScope={selectedScope} />
        <p className="fi-panel-note">Consolidated and not-applicable are preserved source states. D5 does not relabel them as reconciled.</p>
      </section>

      <section className="fi-panel fi-readiness-panel">
        <div className="fi-panel-head"><div><p className="fi-eyebrow">Validator-produced evidence</p><h3>Model-serving readiness controls</h3></div><span>{readinessPassed} of {readinessControls.length} passed</span></div>
        <ReadinessControls rows={readinessControls} />
        <div className="fi-authority-boundary"><strong>Control meaning</strong><span>A pass establishes the named comparison for its declared serving purpose. It does not assert that every underlying business process control is effective.</span></div>
      </section>

      <section className="fi-assurance-grid">
        <article className="fi-panel fi-metric-readiness-panel">
          <div className="fi-panel-head"><div><p className="fi-eyebrow">Executive presentation</p><h3>Metric reliability coverage</h3></div><span>{metricsReady} ready metrics</span></div>
          <div className="fi-metric-readiness-list">
            {metricReadiness.map((metric) => (
              <div key={metric.metric_id}>
                <span><strong>{metric.metric_label}</strong><small>{label(metric.value_authority)}</small></span>
                <i><b style={{ width: `${Math.min((metric.period_count / Math.max(metric.minimum_period_count ?? 60, 1)) * 100, 100)}%` }} /></i>
                <span className="coverage">{metric.period_count} months</span>
                <Status value={metric.readiness_status} />
              </div>
            ))}
          </div>
        </article>

        <article className="fi-panel fi-package-control-panel">
          <div className="fi-panel-head"><div><p className="fi-eyebrow">C2 delivery integrity</p><h3>Package replay controls</h3></div><span>{packagePassed} passed</span></div>
          <div className="fi-package-control-list">
            {criticalPackageControls(packageControls).map((control) => (
              <div key={control.control_id}>
                <span><strong>{control.control_id}</strong><small>{control.table_name}</small></span>
                <Status value={control.status} />
                <p>{control.evidence}</p>
              </div>
            ))}
          </div>
          <p className="fi-panel-note">The remaining controls bind all 29 delivered table populations and logical digests across C1, CSV, React and Power BI outputs.</p>
        </article>
      </section>

      <section className="fi-panel fi-assurance-journeys-panel">
        <div className="fi-panel-head"><div><p className="fi-eyebrow">Controlled evidence demonstrations</p><h3>Inspect the assurance lifecycle</h3></div><span>Separate from current C2 package readiness</span></div>
        <div className="fi-assurance-lifecycle" aria-label="Assurance lifecycle object sequence">
          {[
            ["Exception", "Machine observation requiring review"],
            ["Finding", "Reviewed control conclusion"],
            ["Issue", "Governed accountability object"],
            ["Remediation", "Approved corrective action"],
            ["Readiness", "Purpose-specific use decision"],
          ].map(([name, description], index) => <div key={name}><span>{String(index + 1).padStart(2, "0")}</span><strong>{name}</strong><small>{description}</small></div>)}
        </div>
        <div className="fi-assurance-journeys">
          <Link href="/hermes/reconciliation/RECON-C001%40v1"><span>Hermes</span><strong>Source reconciliation</strong><small>Inspect completeness, traceability and exact source binding.</small></Link>
          <Link href="/argus/exceptions/EXC-C001%40v1"><span>Argus</span><strong>Control exception</strong><small>Inspect the machine observation and reproducible evidence.</small></Link>
          <Link href="/aegis/cases/ISSUE-C001%40v1"><span>Aegis</span><strong>Issue governance</strong><small>Inspect ownership, review state and remediation boundary.</small></Link>
          <Link href="/aegis/readiness/RV-2026-06%40v2"><span>Aegis</span><strong>Reporting readiness</strong><small>Inspect a governed purpose-specific readiness decision.</small></Link>
        </div>
        <p className="fi-panel-note">C-001 and CT-1 are controlled case studies. Their exceptions and issues are not counted as failures in the current Q-FINANCE-C2 delivery.</p>
      </section>
    </>
  );
}
