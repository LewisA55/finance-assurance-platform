"use client";

import { type ComponentProps, useEffect, useMemo, useState } from "react";
import {
  type AssuranceException,
  type DemoManifest,
  type CorrectionIntegrity,
  type GovernanceCase,
  type GovernedDecision,
  type PlatformOverview,
  type ReadinessMatrix,
  type ReportingHistory,
  type ReportingTrace,
  type ReportingVersion,
  type SourceReconciliation,
  formatMinorUnits,
  getAssuranceException,
  getDemoManifest,
  getCorrectionIntegrity,
  getGovernedDecision,
  getGovernanceCase,
  getPlatformOverview,
  getReadinessMatrix,
  getReportingHistory,
  getReportingTrace,
  getReportingVersion,
  getSourceReconciliation,
  humanizeCode,
  PublicApiError,
} from "../lib/public-api";
import {
  AssuranceExceptionScreen,
  BrokenQuarterRail,
  GovernanceCaseScreen,
  ReadinessScreen,
  ReconciliationScreen,
  ReportingHistoryScreen,
} from "./BrokenQuarterViews";
import {
  CorrectionExceptionScreen,
  CorrectionGovernanceScreen,
  CorrectionIntegrityScreen,
  CorrectionReconciliationScreen,
  GovernedDecisionScreen,
} from "./DecisionCorrectionViews";

function Link({ children, ...props }: ComponentProps<"a">) {
  return <a {...props}>{children}</a>;
}

type Screen =
  | { kind: "overview" }
  | { kind: "reconciliation"; productRef: string }
  | { kind: "history"; periodId: string }
  | { kind: "reporting"; periodId: string; versionRef: string }
  | { kind: "exception"; exceptionRef: string }
  | { kind: "governance"; issueRef: string }
  | { kind: "readiness"; reportingVersionRef: string }
  | { kind: "decision"; decisionRef: string }
  | { kind: "correction"; correctionRef: string }
  | {
      kind: "trace";
      reportingVersionRef: string;
      statementField: string;
    };

type ProductExperienceProps = {
  screen: Screen;
};

type ScreenData =
  | { kind: "overview"; value: PlatformOverview }
  | { kind: "reconciliation"; value: SourceReconciliation }
  | { kind: "history"; value: ReportingHistory }
  | { kind: "reporting"; value: ReportingVersion }
  | { kind: "exception"; value: AssuranceException }
  | { kind: "governance"; value: GovernanceCase }
  | { kind: "readiness"; value: ReadinessMatrix }
  | { kind: "decision"; value: GovernedDecision }
  | { kind: "correction"; value: CorrectionIntegrity }
  | { kind: "trace"; value: ReportingTrace };

type LoadState =
  | { status: "loading" }
  | { status: "ready"; manifest: DemoManifest; screen: ScreenData }
  | { status: "error"; message: string; code: string };

const moduleMarks = {
  Hermes: "HE",
  Atlas: "AT",
  Argus: "AR",
  Aegis: "AE",
  Pythia: "PY",
} as const;

function reportingHref(periodId: string, versionRef: string): string {
  return `/atlas/reporting/${encodeURIComponent(periodId)}/${encodeURIComponent(versionRef)}`;
}

function loadScreen(screen: Screen): Promise<ScreenData> {
  switch (screen.kind) {
    case "overview":
      return getPlatformOverview().then((value) => ({ kind: "overview", value }));
    case "reconciliation":
      return getSourceReconciliation(screen.productRef).then((value) => ({ kind: "reconciliation", value }));
    case "history":
      return getReportingHistory(screen.periodId).then((value) => ({ kind: "history", value }));
    case "reporting":
      return getReportingVersion(screen.versionRef).then((value) => ({ kind: "reporting", value }));
    case "exception":
      return getAssuranceException(screen.exceptionRef).then((value) => ({ kind: "exception", value }));
    case "governance":
      return getGovernanceCase(screen.issueRef).then((value) => ({ kind: "governance", value }));
    case "readiness":
      return getReadinessMatrix(screen.reportingVersionRef).then((value) => ({ kind: "readiness", value }));
    case "decision":
      return getGovernedDecision(screen.decisionRef).then((value) => ({ kind: "decision", value }));
    case "correction":
      return getCorrectionIntegrity(screen.correctionRef).then((value) => ({ kind: "correction", value }));
    case "trace":
      return getReportingTrace(screen.reportingVersionRef, screen.statementField).then(
        (value) => ({ kind: "trace", value }),
      );
  }
}

function evidenceLabel(status: string): string {
  const labels: Record<string, string> = {
    CONTENT_BYTES_VERIFIED: "Content bytes verified",
    DECLARED_HASH_ONLY: "Declared hash only",
    MISSING: "Evidence missing",
    UNAVAILABLE: "Evidence unavailable",
  };
  return labels[status] ?? humanizeCode(status);
}

function traceHref(versionRef: string, statementField: string): string {
  return `/trace/reporting/${encodeURIComponent(versionRef)}/${encodeURIComponent(statementField)}`;
}

export function ProductExperience({ screen }: ProductExperienceProps) {
  const [loadState, setLoadState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    const screenRequest = loadScreen(screen);

    Promise.all([getDemoManifest(), screenRequest])
      .then(([manifest, resolvedScreen]) => {
        if (active) {
          setLoadState({
            status: "ready",
            manifest,
            screen: resolvedScreen,
          });
        }
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (error instanceof PublicApiError) {
          setLoadState({ status: "error", message: error.message, code: error.code });
          return;
        }
        setLoadState({
          status: "error",
          message: "The governed public view could not be loaded.",
          code: "CLIENT_BOUNDARY_FAILURE",
        });
      });

    return () => {
      active = false;
    };
  }, [screen]);

  return (
    <div className="product-frame">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <Sidebar screen={screen} />
      <div className="product-stage">
        <SyntheticBanner />
        <Topbar loadState={loadState} />
        <main
          id="main-content"
          className="content-canvas"
          tabIndex={-1}
          aria-busy={loadState.status === "loading"}
        >
          {loadState.status === "loading" ? <LoadingState /> : null}
          {loadState.status === "error" ? (
            <ErrorState code={loadState.code} message={loadState.message} />
          ) : null}
          {loadState.status === "ready" ? (
            <ScreenContent data={loadState.screen} />
          ) : null}
        </main>
        <footer className="product-footer">
          <span>Finance &amp; Assurance Platform</span>
          <span>Deterministic synthetic environment / no paid API required</span>
        </footer>
      </div>
    </div>
  );
}

function Sidebar({ screen }: { screen: Screen }) {
  const active =
    screen.kind === "overview"
      ? "Overview"
      : screen.kind === "trace"
        ? "Trace"
        : screen.kind === "decision"
          ? "Pythia"
          : screen.kind === "correction"
            ? "Trace"
        : screen.kind === "reconciliation"
          ? "Hermes"
          : screen.kind === "exception"
            ? "Argus"
            : screen.kind === "governance" || screen.kind === "readiness"
              ? "Aegis"
              : "Atlas";
  const items: Array<
    | { label: string; mark: string; href: string; available: true }
    | { label: string; mark: string; available: false }
  > = [
    { label: "Overview", mark: "OV", href: "/", available: true },
    {
      label: "Hermes",
      mark: "HE",
      href: "/hermes/reconciliation/RECON-C001@v1",
      available: true,
    },
    {
      label: "Atlas",
      mark: "AT",
      href: "/atlas/reporting/2026-06",
      available: true,
    },
    {
      label: "Argus",
      mark: "AR",
      href: "/argus/exceptions/EXC-C001@v1",
      available: true,
    },
    {
      label: "Aegis",
      mark: "AE",
      href: "/aegis/cases/ISSUE-C001@v1",
      available: true,
    },
    {
      label: "Pythia",
      mark: "PY",
      href: "/pythia/decisions/DECISION-C001@v1",
      available: true,
    },
  ];

  return (
    <aside className="sidebar" aria-label="Product modules">
      <Link className="brand" href="/" aria-label="Finance and Assurance home">
        <span className="brand-mark" aria-hidden="true">
          F
        </span>
        <span>
          <strong>Finance &amp; Assurance</strong>
          <small>Operating environment</small>
        </span>
      </Link>
      <nav className="module-nav" aria-label="Primary navigation">
        <p className="nav-label">Platform</p>
        {items.map((item) =>
          item.available ? (
            <Link
              className={active === item.label ? "module-link active" : "module-link"}
              href={item.href}
              aria-current={active === item.label ? "page" : undefined}
              key={item.label}
            >
              <span className="module-mark" aria-hidden="true">
                {item.mark}
              </span>
              <span>{item.label}</span>
            </Link>
          ) : (
            <span className="module-link pending" key={item.label}>
              <span className="module-mark" aria-hidden="true">
                {item.mark}
              </span>
              <span>{item.label}</span>
              <small>Next</small>
            </span>
          ),
        )}
      </nav>
      <div className="sidebar-lower">
        <Link
          className={active === "Trace" ? "module-link active" : "module-link"}
          href={traceHref("RV-2026-06@v2", "subscription_revenue_minor")}
          aria-current={active === "Trace" ? "page" : undefined}
        >
          <span className="module-mark" aria-hidden="true">
            TR
          </span>
          <span>Trace explorer</span>
        </Link>
        <div className="runtime-card">
          <span className="status-dot" aria-hidden="true" />
          <div>
            <strong>Local runtime</strong>
            <span>Exact-original reads</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

function SyntheticBanner() {
  return (
    <div className="synthetic-banner" role="note">
      <span className="synthetic-icon" aria-hidden="true">
        S
      </span>
      <strong>Synthetic environment</strong>
      <span>All entities, transactions, evidence, and decisions are fictional.</span>
    </div>
  );
}

function Topbar({ loadState }: { loadState: LoadState }) {
  const context =
    loadState.status === "ready"
      ? {
          revision: loadState.screen.value.query_revision,
          verified: loadState.manifest.data.verification_status,
          scenario:
            loadState.screen.value.scenario_ref === "DEMO-CT1-CORRECTION@v1"
              ? "CT-1"
              : "C-001",
        }
      : null;
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Nexus Group / June 2026</p>
        <h1>Assurance Casework</h1>
      </div>
      <div className="context-strip" aria-label="Current data context">
        <ContextChip label="Scenario" value={context?.scenario ?? "Loading"} />
        <ContextChip label="As of" value="14 Jul 2026 12:00 UTC" />
        <ContextChip
          label="Revision"
          value={context ? `r${context.revision}` : "Loading"}
        />
        <span className="verification-chip" role="status" aria-live="polite">
          <span className="status-dot" aria-hidden="true" />
          {context?.verified === "VERIFIED"
            ? "Runtime verified"
            : context
              ? "Runtime failed"
              : "Checking runtime"}
        </span>
      </div>
    </header>
  );
}

function ContextChip({ label, value }: { label: string; value: string }) {
  return (
    <span className="context-chip">
      <small>{label}</small>
      <strong>{value}</strong>
    </span>
  );
}

function ScreenContent({ data }: { data: ScreenData }) {
  switch (data.kind) {
    case "overview":
      return <OverviewScreen overview={data.value} />;
    case "reconciliation":
      return data.value.data.reconciliation_type === "CASH_APPLICATION_IDENTITY" ? (
        <CorrectionReconciliationScreen reconciliation={data.value} />
      ) : (
        <ReconciliationScreen reconciliation={data.value} />
      );
    case "history":
      return <ReportingHistoryScreen history={data.value} />;
    case "reporting":
      return <ReportingScreen report={data.value} />;
    case "exception":
      return data.value.data.exception_type === "CASH_APPLICATION_IDENTITY" ? (
        <CorrectionExceptionScreen exception={data.value} />
      ) : (
        <AssuranceExceptionScreen exception={data.value} />
      );
    case "governance":
      return data.value.scenario_ref === "DEMO-CT1-CORRECTION@v1" ? (
        <CorrectionGovernanceScreen governance={data.value} />
      ) : (
        <GovernanceCaseScreen governance={data.value} />
      );
    case "readiness":
      return <ReadinessScreen readiness={data.value} />;
    case "trace":
      return <TraceScreen trace={data.value} />;
    case "decision":
      return <GovernedDecisionScreen decision={data.value} />;
    case "correction":
      return <CorrectionIntegrityScreen correction={data.value} />;
  }
}

function OverviewScreen({ overview }: { overview: PlatformOverview }) {
  const readiness = overview.data.readiness_summary[0];
  const primaryJourney = overview.data.journey_links.find(
    (journey) => journey.journey_id === "O-J01",
  );
  const brokenQuarterJourney = overview.data.journey_links.find(
    (journey) => journey.journey_id === "O-J02",
  );
  const governedDecisionJourney = overview.data.journey_links.find(
    (journey) => journey.journey_id === "O-J03",
  );
  const correctionJourney = overview.data.journey_links.find(
    (journey) => journey.journey_id === "O-SJ01",
  );
  return (
    <div className="screen-stack">
      <section className="page-heading">
        <div>
          <p className="section-kicker">Governed operating view</p>
          <h2>{overview.data.company_label}</h2>
          <p>
            One shared view of source integrity, accounting truth, assurance,
            governance, and the decisions permitted to consume it.
          </p>
        </div>
        <Link
          className="primary-action"
          href={reportingHref(
            overview.data.reporting_period,
            overview.data.headline_reporting_version_ref,
          )}
        >
          Inspect June v2 <span aria-hidden="true">&rarr;</span>
        </Link>
      </section>
      <section className="journey-card decision-entry">
        <div className="journey-number">O-J03</div>
        <div>
          <p className="section-kicker">Flagship journey</p>
          <h3>{governedDecisionJourney?.label ?? "Make a governed decision"}</h3>
          <p>
            Inspect the exact reporting and readiness pairing behind a deferred-hire
            recommendation, then keep approval distinct from event admission.
          </p>
        </div>
        <Link
          className="secondary-action"
          href={governedDecisionJourney?.route ?? "/pythia/decisions/DECISION-C001@v1"}
        >
          Open decision <span aria-hidden="true">&rarr;</span>
        </Link>
      </section>
      <section className="journey-card correction-entry">
        <div className="journey-number">O-SJ01</div>
        <div>
          <p className="section-kicker">Supporting journey</p>
          <h3>{correctionJourney?.label ?? "Prove correction integrity"}</h3>
          <p>
            Follow a wrong-customer cash application through reconciliation,
            governance, exact reversal, replacement, and zero net movement.
          </p>
        </div>
        <Link
          className="secondary-action"
          href={correctionJourney?.route ?? "/corrections/VERIFY-CT1@v1"}
        >
          Inspect correction <span aria-hidden="true">&rarr;</span>
        </Link>
      </section>
      <section className="journey-card broken-quarter-entry">
        <div className="journey-number">O-J02</div>
        <div>
          <p className="section-kicker">Flagship journey</p>
          <h3>{brokenQuarterJourney?.label ?? "Explain a broken quarter"}</h3>
          <p>
            Follow the immutable June v1 report through reconciliation, assurance,
            governance, restatement, and exact purpose-specific readiness.
          </p>
        </div>
        <Link
          className="secondary-action"
          href={brokenQuarterJourney?.route ?? "/atlas/reporting/2026-06"}
        >
          Start the journey <span aria-hidden="true">&rarr;</span>
        </Link>
      </section>

      <section className="journey-card broken-quarter-entry">
        <div className="journey-number">O-J02</div>
        <div>
          <p className="section-kicker">Flagship journey</p>
          <h3>{brokenQuarterJourney?.label ?? "Explain a broken quarter"}</h3>
          <p>
            Follow the immutable June v1 report through reconciliation, assurance,
            governance, restatement, and exact purpose-specific readiness.
          </p>
        </div>
        <Link
          className="secondary-action"
          href={brokenQuarterJourney?.route ?? "/atlas/reporting/2026-06"}
        >
          Start the journey <span aria-hidden="true">&rarr;</span>
        </Link>
      </section>

      <section className="metric-grid" aria-label="Headline financial values">
        {overview.data.headline_values.map((value, index) => (
          <article className="metric-card" key={value.field}>
            <div className="metric-topline">
              <span>{value.label}</span>
              <span className="metric-index">0{index + 1}</span>
            </div>
            <strong>{formatMinorUnits(value.amount_minor, value.currency)}</strong>
            <div className="metric-meta">
              <span
                className={
                  value.content_verification_status === "CONTENT_BYTES_VERIFIED"
                    ? "verified-label"
                    : "limited-label"
                }
              >
                {evidenceLabel(value.content_verification_status)}
              </span>
              <Link href={traceHref(value.reporting_version_ref, value.field)}>
                Trace value
              </Link>
            </div>
          </article>
        ))}
        <article className="metric-card signal-card">
          <div className="metric-topline">
            <span>Assurance signal</span>
            <span className="metric-index">03</span>
          </div>
          <strong>{overview.data.machine_exception_count}</strong>
          <div className="metric-meta">
            <span>Machine exception</span>
            <span>Governance distinct</span>
          </div>
        </article>
      </section>

      <section className="overview-grid">
        <article className="panel process-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Complete platform loop</p>
              <h3>From source record to governed decision</h3>
            </div>
            <span className="exact-badge">Exact original</span>
          </div>
          <div className="module-flow">
            {overview.data.module_summaries.map((module, index) => (
              <div className="flow-item" key={module.module}>
                <span className={`flow-mark ${module.module.toLowerCase()}`}>
                  {moduleMarks[module.module]}
                </span>
                <div>
                  <strong>{module.module}</strong>
                  <span>{humanizeCode(module.summary_code)}</span>
                  <code>{module.primary_product_ref}</code>
                </div>
                {index < overview.data.module_summaries.length - 1 ? (
                  <span className="flow-line" aria-hidden="true" />
                ) : null}
              </div>
            ))}
          </div>
        </article>

        <article className="panel readiness-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Purpose-specific reliance</p>
              <h3>Decision readiness</h3>
            </div>
            <span className="approved-badge">{readiness?.status ?? "Unavailable"}</span>
          </div>
          {readiness ? (
            <div className="readiness-body">
              <div className="readiness-ring" aria-hidden="true">
                <span aria-hidden="true">OK</span>
              </div>
              <dl>
                <div>
                  <dt>Purpose</dt>
                  <dd>{humanizeCode(readiness.purpose_ref)}</dd>
                </div>
                <div>
                  <dt>Scope</dt>
                  <dd>{humanizeCode(readiness.scope_ref)}</dd>
                </div>
                <div>
                  <dt>Assessment</dt>
                  <dd>{readiness.assessed_by_ref}</dd>
                </div>
                <div>
                  <dt>Decision</dt>
                  <dd>{overview.data.governed_decision_ref}</dd>
                </div>
              </dl>
            </div>
          ) : (
            <p className="empty-copy">No readiness assessment is available.</p>
          )}
        </article>
      </section>

      <section className="journey-card">
        <div className="journey-number">O-J01</div>
        <div>
          <p className="section-kicker">Flagship journey</p>
          <h3>{primaryJourney?.label ?? "Trace a verified reporting value"}</h3>
          <p>
            Follow June subscription revenue from its immutable reporting version
            through the directed authority graph to rule, event, source, and evidence.
          </p>
        </div>
        <Link
          className="secondary-action"
          href={
            primaryJourney?.route ??
            traceHref(
              overview.data.headline_reporting_version_ref,
              "subscription_revenue_minor",
            )
          }
        >
          Open trace <span aria-hidden="true">&rarr;</span>
        </Link>
      </section>
    </div>
  );
}

function ReportingScreen({ report }: { report: ReportingVersion }) {
  const isRestated = report.data.publication_origin === "RESTATEMENT_PUBLICATION";
  const isCanonicalRestatement = report.data.reporting_version_ref === "RV-2026-06@v2";
  const valueForTrace = report.data.statement_values.find((value) =>
    report.data.traceable_fields.includes(value.field),
  );
  return (
    <div className="screen-stack">
      {isCanonicalRestatement ? <BrokenQuarterRail current="restatement" /> : null}
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link href="/">Overview</Link><span>/</span><span>Atlas</span><span>/</span>
        <span aria-current="page">{report.data.reporting_version_ref}</span>
      </nav>
      <section className="page-heading compact">
        <div>
          <p className="section-kicker">Atlas / Accounting truth</p>
          <h2>June reporting version v{report.data.version}</h2>
          <p>
            {isRestated
              ? "Immutable restated financials, published without reopening the hard-closed June period."
              : "Immutable predecessor financials preserved exactly as originally imported."}
          </p>
        </div>
        {valueForTrace ? (
          <Link
            className="primary-action"
            href={traceHref(report.data.reporting_version_ref, valueForTrace.field)}
          >
            Trace verified value <span aria-hidden="true">&rarr;</span>
          </Link>
        ) : null}
      </section>

      <section className="version-context" aria-label="Reporting version context">
        <ContextBlock label="Exact version" value={report.data.reporting_version_ref} />
        <ContextBlock label="Publication" value={humanizeCode(report.data.publication_origin)} />
        <ContextBlock label="Published" value={formatTimestamp(report.data.published_at)} />
        <ContextBlock
          label="Evidence"
          value={evidenceLabel(report.data.content_verification_status)}
          tone={
            report.data.content_verification_status === "CONTENT_BYTES_VERIFIED"
              ? "verified"
              : undefined
          }
        />
      </section>

      <section className="panel statement-panel">
        <div className="panel-heading">
          <div>
            <p className="section-kicker">Statement values</p>
            <h3>Controlled reporting content</h3>
          </div>
          <span className="exact-badge">{report.data.currency}</span>
        </div>
        <div className="statement-table" role="table" aria-label="June statement values">
          <div className="statement-row statement-header" role="row">
            <span role="columnheader">Statement field</span>
            <span role="columnheader">Exact value</span>
            <span role="columnheader">Evidence status</span>
            <span role="columnheader">Action</span>
          </div>
          {report.data.statement_values.map((value) => (
            <div className="statement-row" role="row" key={value.field}>
              <span role="cell">
                <strong>{value.label}</strong>
                <code>{value.field}</code>
              </span>
              <span role="cell" className="statement-amount">
                {formatMinorUnits(value.amount_minor, value.currency)}
              </span>
              <span role="cell">
                <span
                  className={
                    value.content_verification_status === "CONTENT_BYTES_VERIFIED"
                      ? "verified-label"
                      : "limited-label"
                  }
                >
                  {evidenceLabel(value.content_verification_status)}
                </span>
              </span>
              <span role="cell">
                {value.trace_available ? (
                  <Link href={traceHref(value.reporting_version_ref, value.field)}>
                    Trace <span aria-hidden="true">&rarr;</span>
                  </Link>
                ) : (
                  <span>Unavailable</span>
                )}
              </span>
            </div>
          ))}
        </div>
      </section>

      {isRestated ? (
        <section className="reporting-detail-grid">
          <article className="panel detail-panel">
            <p className="section-kicker">Restatement lineage</p>
            <h3>History remains visible</h3>
            <dl className="detail-list">
              <div><dt>Predecessor</dt><dd>{report.data.predecessor_version_ref}</dd></div>
              <div><dt>Restatement case</dt><dd>{report.data.restatement_case_ref}</dd></div>
              <div><dt>Published by event</dt><dd>{report.data.published_by_event_id}</dd></div>
            </dl>
          </article>
          <article className="panel detail-panel hash-panel">
            <p className="section-kicker">Reproducible content</p>
            <h3>Verified manifest</h3>
            <code className="hash-value">{report.data.manifest_hash}</code>
            <p>
              The content hash binds this displayed version to the exact reporting
              body resolved by the runtime.
            </p>
          </article>
        </section>
      ) : (
        <section className="panel detail-panel">
          <p className="section-kicker">Pre-scope authority</p>
          <h3>Original reporting state preserved</h3>
          <dl className="detail-list">
            <div><dt>Import attestation</dt><dd>{report.data.import_attestation_ref}</dd></div>
            <div><dt>Original authority</dt><dd>{report.data.original_authority_ref}</dd></div>
            <div><dt>Source</dt><dd>{report.data.source_ref}</dd></div>
          </dl>
        </section>
      )}
      {isCanonicalRestatement ? (
        <section className="handoff-card">
          <div>
            <p className="section-kicker">Reliance is a separate decision</p>
            <h3>Corrected does not automatically mean approved for use.</h3>
            <p>
              Continue to the exact readiness assessment for June v2, its named
              purpose, and its governed scope.
            </p>
          </div>
          <Link className="primary-action" href="/aegis/readiness/RV-2026-06@v2">
            Inspect readiness <span aria-hidden="true">&rarr;</span>
          </Link>
        </section>
      ) : null}
    </div>
  );
}

function TraceScreen({ trace }: { trace: ReportingTrace }) {
  const isCanonicalRestatement = trace.data.reporting_version_ref === "RV-2026-06@v2";
  const orderedRelationships = useMemo(
    () =>
      trace.data.nodes.slice(0, -1).map((node, index) => {
        const nextNode = trace.data.nodes[index + 1];
        return trace.data.edges.find(
          (edge) =>
            edge.source_ref === node.node_ref &&
            edge.target_ref === nextNode.node_ref,
        )?.relationship;
      }),
    [trace.data.edges, trace.data.nodes],
  );
  return (
    <div className="screen-stack">
      {isCanonicalRestatement ? <BrokenQuarterRail current="restatement" /> : null}
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link href="/">Overview</Link><span>/</span><span>Trace</span><span>/</span>
        <span aria-current="page">{humanizeCode(trace.data.statement_field)}</span>
      </nav>
      <section className="page-heading compact trace-heading">
        <div>
          <p className="section-kicker">O-J01 / Directed authority path</p>
          <h2>Trace a verified reporting value</h2>
          <p>
            Every step below is supplied by the runtime&apos;s directed J-P11 traversal.
            The interface adds no inferred edge or accounting conclusion.
          </p>
        </div>
        <div className="trace-value-card">
          <span>{humanizeCode(trace.data.statement_field)}</span>
          <strong>
            {formatMinorUnits(trace.data.statement_value_minor, trace.data.currency)}
          </strong>
          <small>{trace.data.reporting_version_ref}</small>
        </div>
      </section>

      <section className="trace-layout">
        <article className="panel trace-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Bounded provenance</p>
              <h3>{trace.data.nodes.length} exact authority nodes</h3>
            </div>
            <span className="verified-label">Content bytes verified</span>
          </div>
          <ol className="trace-list">
            {trace.data.nodes.map((node, index) => (
              <li className="trace-node" key={node.node_ref}>
                <span className="trace-order">{String(index + 1).padStart(2, "0")}</span>
                <span className="trace-node-mark" aria-hidden="true">
                  {node.record_family.replace("J-AR", "A")}
                </span>
                <div className="trace-node-copy">
                  <span className="trace-role">{humanizeCode(node.role)}</span>
                  <strong>{node.record_identity}</strong>
                  <code>{node.semantic_hash ?? "No semantic hash supplied"}</code>
                </div>
                {index < trace.data.nodes.length - 1 ? (
                  <span className="trace-relationship">
                    {humanizeCode(orderedRelationships[index] ?? "directed link")}
                  </span>
                ) : (
                  <span className="trace-terminal">Evidence terminus</span>
                )}
              </li>
            ))}
          </ol>
        </article>
        <aside className="trace-aside">
          <article className="panel assurance-card">
            <span className="assurance-seal" aria-hidden="true">OK</span>
            <p className="section-kicker">Claim boundary</p>
            <h3>Verified, not merely declared</h3>
            <p>
              The reporting body&apos;s committed bytes reproduce the stored SHA-256
              value. Declaration-only evidence is never promoted to this status.
            </p>
          </article>
          <article className="panel detail-panel">
            <p className="section-kicker">Read context</p>
            <dl className="detail-list">
              <div><dt>Mode</dt><dd>{trace.compatibility_read_mode}</dd></div>
              <div><dt>Revision</dt><dd>r{trace.query_revision}</dd></div>
              <div><dt>Scenario</dt><dd>C-001</dd></div>
              <div><dt>As of</dt><dd>{formatTimestamp(trace.semantic_as_of_time)}</dd></div>
            </dl>
          </article>
          <Link
            className="secondary-action full-width"
            href={reportingHref("2026-06", trace.data.reporting_version_ref)}
          >
            Return to reporting version <span aria-hidden="true">&rarr;</span>
          </Link>
        </aside>
      </section>
    </div>
  );
}

function ContextBlock({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "verified";
}) {
  return (
    <div className="context-block">
      <span>{label}</span>
      <strong className={tone === "verified" ? "text-verified" : undefined}>{value}</strong>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="loading-layout" role="status" aria-live="polite">
      <span className="sr-only">Loading governed finance view</span>
      <div className="loading-heading" />
      <div className="loading-grid">
        <div /><div /><div />
      </div>
      <div className="loading-panel" />
    </div>
  );
}

function ErrorState({ code, message }: { code: string; message: string }) {
  return (
    <section className="error-state" role="alert">
      <span className="error-mark" aria-hidden="true">!</span>
      <p className="section-kicker">Public view unavailable</p>
      <h2>{humanizeCode(code)}</h2>
      <p>{message}</p>
      <Link className="primary-action" href="/">Return to overview</Link>
    </section>
  );
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));
}
