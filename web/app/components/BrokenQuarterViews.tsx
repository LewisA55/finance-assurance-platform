import type { ComponentProps } from "react";
import {
  type AssuranceException,
  type GovernanceCase,
  type ReadinessMatrix,
  type ReportingHistory,
  type SourceReconciliation,
  formatMinorUnits,
  humanizeCode,
} from "../lib/public-api";

function Link({ children, ...props }: ComponentProps<"a">) {
  return <a {...props}>{children}</a>;
}

export type BrokenQuarterStep =
  | "history"
  | "reconciliation"
  | "exception"
  | "governance"
  | "restatement"
  | "readiness";

const journeySteps: Array<{
  id: BrokenQuarterStep;
  label: string;
  owner: string;
  href: string;
}> = [
  {
    id: "history",
    label: "As-was history",
    owner: "Atlas",
    href: "/atlas/reporting/2026-06",
  },
  {
    id: "reconciliation",
    label: "Population gap",
    owner: "Hermes",
    href: "/hermes/reconciliation/RECON-C001@v1",
  },
  {
    id: "exception",
    label: "Exception",
    owner: "Argus",
    href: "/argus/exceptions/EXC-C001@v1",
  },
  {
    id: "governance",
    label: "Governance",
    owner: "Aegis",
    href: "/aegis/cases/ISSUE-C001@v1",
  },
  {
    id: "restatement",
    label: "Restated v2",
    owner: "Atlas",
    href: "/atlas/reporting/2026-06/RV-2026-06@v2",
  },
  {
    id: "readiness",
    label: "Approved use",
    owner: "Aegis",
    href: "/aegis/readiness/RV-2026-06@v2",
  },
];

export function BrokenQuarterRail({ current }: { current: BrokenQuarterStep }) {
  const currentIndex = journeySteps.findIndex((step) => step.id === current);
  return (
    <nav className="journey-rail" aria-label="Broken-quarter journey progress">
      <div className="journey-rail-heading">
        <span>O-J02</span>
        <strong>Explain a broken quarter</strong>
      </div>
      <ol>
        {journeySteps.map((step, index) => {
          const state = index === currentIndex ? "current" : index < currentIndex ? "passed" : "next";
          return (
            <li className={state} key={step.id}>
              <Link href={step.href} aria-current={state === "current" ? "step" : undefined}>
                <span className="journey-step-number">{String(index + 1).padStart(2, "0")}</span>
                <span>
                  <small>{step.owner}</small>
                  <strong>{step.label}</strong>
                </span>
              </Link>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export function ReportingHistoryScreen({ history }: { history: ReportingHistory }) {
  const bridge = history.data.restatement_bridge[0];
  return (
    <div className="screen-stack">
      <BrokenQuarterRail current="history" />
      <section className="page-heading compact">
        <div>
          <p className="section-kicker">Atlas / Immutable reporting history</p>
          <h2>A balanced ledger can still report an incomplete quarter.</h2>
          <p>
            June remains hard-closed. Atlas preserves the original publication and
            exposes the governed restatement as a separate version.
          </p>
        </div>
        <span className="period-lock-badge">June hard close preserved</span>
      </section>

      <section className="history-layout" aria-label="June reporting versions">
        {history.data.versions.map((version) => (
          <article
            className={
              version.publication_origin === "RESTATEMENT_PUBLICATION"
                ? "history-version-card restated"
                : "history-version-card"
            }
            key={version.reporting_version_ref}
          >
            <div className="history-version-heading">
              <div>
                <span className="version-number">v{version.version}</span>
                <p>{humanizeCode(version.publication_origin)}</p>
              </div>
              <span className="verified-label">{evidenceLabel(version.content_verification_status)}</span>
            </div>
            <dl className="history-values">
              {version.statement_values.map((value) => (
                <div key={value.field}>
                  <dt>{value.label}</dt>
                  <dd>{formatMinorUnits(value.amount_minor, value.currency)}</dd>
                </div>
              ))}
            </dl>
            <div className="history-version-footer">
              <span>{formatTimestamp(version.published_at)}</span>
              <Link href={`/atlas/reporting/${history.data.period_id}/${encodeURIComponent(version.reporting_version_ref)}`}>
                Open exact version <span aria-hidden="true">&rarr;</span>
              </Link>
            </div>
          </article>
        ))}
      </section>

      {bridge ? (
        <section className="restatement-bridge" aria-label="Restatement bridge">
          <div className="bridge-marker" aria-hidden="true">ADJ</div>
          <div>
            <p className="section-kicker">Server-published restatement bridge</p>
            <h3>{humanizeCode(bridge.statement_field)} corrected by {formatMinorUnits(bridge.adjustment_minor, bridge.currency)}</h3>
            <p>
              {bridge.predecessor_version_ref} remains retrievable. {bridge.successor_version_ref}
              records the correction under case {bridge.restatement_case_ref}; the client does not net these versions.
            </p>
          </div>
          <Link className="secondary-action" href="/hermes/reconciliation/RECON-C001@v1">
            Explain the gap <span aria-hidden="true">&rarr;</span>
          </Link>
        </section>
      ) : null}

      <ExactReadFooter envelope={history} />
    </div>
  );
}

export function ReconciliationScreen({ reconciliation }: { reconciliation: SourceReconciliation }) {
  if (reconciliation.data.reconciliation_type !== "RECOGNITION_POPULATION") {
    return <UnsupportedJourneyVariant label="cash-application identity reconciliation" />;
  }
  const item = reconciliation.data;
  return (
    <div className="screen-stack">
      <BrokenQuarterRail current="reconciliation" />
      <section className="page-heading compact">
        <div>
          <p className="section-kicker">Hermes / Source integrity</p>
          <h2>One expected recognition item never reached the posted population.</h2>
          <p>
            Hermes exposes the source disagreement and its lineage. It does not
            prescribe an accounting correction.
          </p>
        </div>
        <StatusBadge status={item.reconciliation_status} />
      </section>

      <section className="reconciliation-board">
        <article className="recon-population panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Recognition population</p>
              <h3>Expected versus posted</h3>
            </div>
            <code>{item.reconciliation_ref}</code>
          </div>
          <div className="population-bars">
            <PopulationBar label="Expected" value={item.expected_item_count} total={item.expected_item_count} tone="expected" />
            <PopulationBar label="Posted" value={item.posted_item_count} total={item.expected_item_count} tone="posted" />
          </div>
          <div className="recon-counts">
            <Metric label="Submitted, unposted" value={String(item.submitted_unposted_count)} />
            <Metric label="Deferred" value={String(item.deferred_count)} />
            <Metric label="Period" value={item.period_id} />
          </div>
        </article>

        <article className="gap-card">
          <p className="section-kicker">Unreconciled difference</p>
          <strong>{formatMinorUnits(item.difference_minor, item.currency)}</strong>
          <dl>
            <div><dt>Expected</dt><dd>{formatMinorUnits(item.expected_amount_minor, item.currency)}</dd></div>
            <div><dt>Posted</dt><dd>{formatMinorUnits(item.posted_amount_minor, item.currency)}</dd></div>
          </dl>
          <p className="boundary-note">Observation only. Accounting treatment remains with Atlas.</p>
        </article>
      </section>

      <section className="handoff-card">
        <div>
          <p className="section-kicker">Controlled handoff</p>
          <h3>Hermes publishes the failed reconciliation to Argus.</h3>
          <p>{item.scope_ref} / performed {formatTimestamp(item.performed_at)}</p>
        </div>
        <Link className="primary-action" href={`/argus/exceptions/${encodeURIComponent(item.downstream_exception_ref)}`}>
          Inspect exception <span aria-hidden="true">&rarr;</span>
        </Link>
      </section>

      <ReferenceStrip label="Source basis" refs={item.source_refs} />
      <ExactReadFooter envelope={reconciliation} />
    </div>
  );
}

export function AssuranceExceptionScreen({ exception }: { exception: AssuranceException }) {
  if (exception.data.exception_type !== "RECOGNITION_COMPLETENESS") {
    return <UnsupportedJourneyVariant label="cash-application identity exception" />;
  }
  const item = exception.data;
  return (
    <div className="screen-stack">
      <BrokenQuarterRail current="exception" />
      <section className="page-heading compact">
        <div>
          <p className="section-kicker">Argus / Machine observation</p>
          <h2>Recognition completeness failed by {formatMinorUnits(item.difference_minor, item.currency)}.</h2>
          <p>
            The ledger can remain mechanically balanced while the completeness
            assertion fails. This is an exception, not yet a finding or issue.
          </p>
        </div>
        <span className="blocking-badge">{item.severity}</span>
      </section>

      <section className="exception-layout">
        <article className="exception-measure panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">ARG-O2C-002</p>
              <h3>Contract-to-revenue completeness</h3>
            </div>
            <span className="exact-badge">{item.assertion}</span>
          </div>
          <div className="exception-comparison">
            <Metric label="Expected June revenue" value={formatMinorUnits(item.expected_amount_minor, item.currency)} />
            <span className="comparison-mark" aria-hidden="true">vs</span>
            <Metric label="Recorded June revenue" value={formatMinorUnits(item.actual_amount_minor, item.currency)} />
          </div>
          <div className="assertion-contrast">
            <span className="pass-signal">Trial-balance integrity: PASS</span>
            <span className="fail-signal">Revenue completeness: FAIL</span>
          </div>
        </article>

        <article className="classification-card">
          <span className="classification-mark" aria-hidden="true">EX</span>
          <p className="section-kicker">Classification boundary</p>
          <h3>Machine exception</h3>
          <p>
            Argus reports the observation and evidence basis. Aegis owns human
            review, the finding, and any governed issue.
          </p>
          <code>{item.exception_ref}</code>
        </article>
      </section>

      <section className="handoff-card">
        <div>
          <p className="section-kicker">Human review required</p>
          <h3>The exception now crosses into Aegis governance.</h3>
          <p>Test run {item.test_run_ref} / definition {item.test_definition_ref}</p>
        </div>
        <Link className="primary-action" href={`/aegis/cases/${encodeURIComponent(item.related_governance_case_ref)}`}>
          Follow governance chain <span aria-hidden="true">&rarr;</span>
        </Link>
      </section>

      <ReferenceStrip label="Evidence and subjects" refs={[...item.evidence_refs, ...item.subject_refs]} />
      <ExactReadFooter envelope={exception} />
    </div>
  );
}

export function GovernanceCaseScreen({ governance }: { governance: GovernanceCase }) {
  const item = governance.data;
  const stages = [
    { label: "Exception", ref: item.exception_ref, state: "Observed" },
    { label: "Review", ref: item.review_ref, state: item.review_disposition },
    { label: "Finding", ref: item.finding_ref, state: "Established" },
    { label: "Issue", ref: item.initial_issue_ref, state: item.initial_issue_status },
    { label: "Remediation", ref: item.remediation_directive_ref, state: "Directed" },
    { label: "Verification", ref: item.verification_ref, state: "Recorded" },
    { label: "Successor issue", ref: item.final_issue_ref, state: item.final_issue_status },
  ];
  return (
    <div className="screen-stack">
      <BrokenQuarterRail current="governance" />
      <section className="page-heading compact">
        <div>
          <p className="section-kicker">Aegis / Governed treatment</p>
          <h2>The exception becomes a reviewed issue with verified remediation.</h2>
          <p>
            Each governance object remains distinct. Verification advances the
            issue state but does not silently assert closure.
          </p>
        </div>
        <span className="review-badge">{item.final_issue_status}</span>
      </section>

      <section className="governance-timeline panel" aria-label="Governance object chain">
        {stages.map((stage, index) => (
          <article className="governance-stage" key={`${stage.label}-${stage.ref}`}>
            <span className="stage-index">{String(index + 1).padStart(2, "0")}</span>
            <div>
              <p>{stage.label}</p>
              <strong>{humanizeCode(stage.state)}</strong>
              <code>{stage.ref}</code>
            </div>
          </article>
        ))}
      </section>

      <section className="governance-summary-grid">
        <article className="panel governance-owner-card">
          <p className="section-kicker">Accountability</p>
          <h3>{humanizeCode(item.owner_ref)}</h3>
          <p>Owns the issue treatment; Atlas owns the correcting accounting record.</p>
          <ReferenceStrip label="Correction record" refs={item.correction_refs} compact />
        </article>
        <article className="not-closed-card">
          <span className="not-equal" aria-hidden="true">!=</span>
          <div>
            <p className="section-kicker">Claim boundary</p>
            <h3>Remediation verified is not closed.</h3>
            <p>The exact successor issue state is shown without promotion to a stronger governance claim.</p>
          </div>
        </article>
      </section>

      <section className="handoff-card">
        <div>
          <p className="section-kicker">Accounting correction</p>
          <h3>Inspect the separately published June v2.</h3>
          <p>The original June publication remains intact; the hard-closed period was not silently reopened.</p>
        </div>
        <Link className="primary-action" href="/atlas/reporting/2026-06/RV-2026-06@v2">
          Inspect restated v2 <span aria-hidden="true">&rarr;</span>
        </Link>
      </section>

      <ExactReadFooter envelope={governance} />
    </div>
  );
}

export function ReadinessScreen({ readiness }: { readiness: ReadinessMatrix }) {
  return (
    <div className="screen-stack">
      <BrokenQuarterRail current="readiness" />
      <section className="page-heading compact">
        <div>
          <p className="section-kicker">Aegis / Purpose-specific reliance</p>
          <h2>Corrected is not the same as approved for use.</h2>
          <p>
            Readiness attaches to the exact reporting version, period, purpose,
            and scope. No global reliability status is inferred.
          </p>
        </div>
        <span className="approved-badge">Exact pairing</span>
      </section>

      <section className="readiness-matrix" aria-label="Purpose-specific readiness matrix">
        <div className="readiness-matrix-head">
          <span>Reporting product</span>
          <span>Purpose and scope</span>
          <span>Reliance</span>
          <span>Authority</span>
        </div>
        {readiness.data.rows.map((row) => (
          <article className="readiness-matrix-row" key={row.readiness_ref}>
            <div>
              <small>{readiness.data.period_id}</small>
              <strong>{readiness.data.reporting_version_ref}</strong>
            </div>
            <div>
              <strong>{humanizeCode(row.purpose_ref)}</strong>
              <small>{humanizeCode(row.scope_ref)}</small>
            </div>
            <div>
              <span className="approved-badge">{row.status}</span>
              <small>{row.limitation_codes.length === 0 ? "No recorded limitations" : row.limitation_codes.join(", ")}</small>
            </div>
            <div>
              <strong>{row.assessed_by_ref}</strong>
              <small>{row.readiness_ref}</small>
            </div>
            <ReferenceStrip label="Exact readiness basis" refs={row.basis_refs} compact />
          </article>
        ))}
      </section>

      <section className="journey-complete-card">
        <span className="completion-mark" aria-hidden="true">OK</span>
        <div>
          <p className="section-kicker">O-J02 complete</p>
          <h3>History preserved. Gap explained. Remediation verified. Use explicitly approved.</h3>
          <p>
            The journey never reopened June, collapsed governance stages, or
            treated a corrected report as globally reliable.
          </p>
        </div>
        <Link className="secondary-action" href="/pythia/decisions/DECISION-C001@v1">
          Continue to O-J03 <span aria-hidden="true">&rarr;</span>
        </Link>
      </section>

      <ExactReadFooter envelope={readiness} />
    </div>
  );
}

function PopulationBar({
  label,
  value,
  total,
  tone,
}: {
  label: string;
  value: number;
  total: number;
  tone: "expected" | "posted";
}) {
  return (
    <div className={`population-count-row ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>of {total} expected items</small>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="phase4-metric"><span>{label}</span><strong>{value}</strong></div>;
}

function StatusBadge({ status }: { status: string }) {
  return <span className={status === "FAILED" ? "blocking-badge" : "review-badge"}>{status}</span>;
}

function ReferenceStrip({
  label,
  refs,
  compact = false,
}: {
  label: string;
  refs: string[];
  compact?: boolean;
}) {
  return (
    <div className={compact ? "reference-strip compact" : "reference-strip"}>
      <span>{label}</span>
      <div>{refs.map((ref) => <code key={ref}>{ref}</code>)}</div>
    </div>
  );
}

function ExactReadFooter({
  envelope,
}: {
  envelope: { view_contract: string; query_revision: number; compatibility_read_mode: string; semantic_as_of_time: string };
}) {
  return (
    <footer className="exact-read-footer">
      <span>{envelope.view_contract}</span>
      <span>Revision r{envelope.query_revision}</span>
      <span>{humanizeCode(envelope.compatibility_read_mode)}</span>
      <span>As of {formatTimestamp(envelope.semantic_as_of_time)}</span>
    </footer>
  );
}

function UnsupportedJourneyVariant({ label }: { label: string }) {
  return (
    <section className="error-state" role="alert">
      <span className="error-mark" aria-hidden="true">!</span>
      <p className="section-kicker">Journey variant mismatch</p>
      <h2>{humanizeCode(label)}</h2>
      <p>This exact record belongs to a different ratified journey variant.</p>
      <Link className="primary-action" href="/">Return to overview</Link>
    </section>
  );
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date(value));
}

function evidenceLabel(status: string): string {
  if (status === "CONTENT_BYTES_VERIFIED") return "Content bytes verified";
  if (status === "DECLARED_HASH_ONLY") return "Declared hash only";
  return humanizeCode(status);
}
