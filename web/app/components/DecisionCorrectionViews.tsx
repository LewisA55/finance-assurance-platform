import type { ComponentProps } from "react";
import {
  type AssuranceException,
  type CorrectionIntegrity,
  type GovernanceCase,
  type GovernedDecision,
  type SourceReconciliation,
  formatMinorUnits,
  humanizeCode,
} from "../lib/public-api";

function Link({ children, ...props }: ComponentProps<"a">) {
  return <a {...props}>{children}</a>;
}

type DecisionStep = "input" | "decision" | "approval" | "candidate";

const decisionSteps: Array<{
  id: DecisionStep;
  owner: string;
  label: string;
}> = [
  { id: "input", owner: "Aegis", label: "Approved input" },
  { id: "decision", owner: "Pythia", label: "Governed decision" },
  { id: "approval", owner: "Business", label: "Independent approval" },
  { id: "candidate", owner: "Shared boundary", label: "Candidate outcome" },
];

export function DecisionRail({ current }: { current: DecisionStep }) {
  const currentIndex = decisionSteps.findIndex((step) => step.id === current);
  return (
    <nav className="journey-rail" aria-label="Governed-decision journey progress">
      <div className="journey-rail-heading">
        <span>O-J03</span>
        <strong>Make a governed decision</strong>
      </div>
      <ol>
        {decisionSteps.map((step, index) => {
          const state = index === currentIndex ? "current" : index < currentIndex ? "passed" : "next";
          return (
            <li className={state} key={step.id}>
              <span className="journey-static-step" aria-current={state === "current" ? "step" : undefined}>
                <span className="journey-step-number">{String(index + 1).padStart(2, "0")}</span>
                <span><small>{step.owner}</small><strong>{step.label}</strong></span>
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export function GovernedDecisionScreen({ decision }: { decision: GovernedDecision }) {
  const data = decision.data;
  return (
    <div className="screen-stack">
      <DecisionRail current="decision" />
      <section className="page-heading compact">
        <div>
          <p className="section-kicker">Pythia / Governed decision</p>
          <h2>Reliable planning starts by freezing the exact input.</h2>
          <p>
            Pythia consumed the approved June v2 pairing. It did not substitute the
            predecessor report, approve its own recommendation, or post back into accounting.
          </p>
        </div>
        <span className="exact-badge">Exact-original input</span>
      </section>

      <section className="decision-binding-grid" aria-label="Governed planning input">
        <article className="panel decision-input-card">
          <p className="section-kicker">Frozen planning basis</p>
          <h3>{data.planning_input_ref}</h3>
          <dl className="compact-definition-list">
            <div><dt>Reporting version</dt><dd>{data.reporting_version_ref}</dd></div>
            <div><dt>Readiness</dt><dd>{data.readiness_ref}</dd></div>
            <div><dt>Purpose</dt><dd>{humanizeCode(data.purpose_ref)}</dd></div>
            <div><dt>Scope</dt><dd>{humanizeCode(data.scope_ref)}</dd></div>
          </dl>
          <ReferenceStrip label="Immutable input set" refs={data.frozen_input_refs} />
        </article>

        <article className="panel decision-effect-card">
          <p className="section-kicker">Operational effect</p>
          <h3>{humanizeCode(data.decision_type)}</h3>
          <code>{data.decision_ref}</code>
          <strong className="decision-amount">
            {formatMinorUnits(data.monthly_cost_minor, data.currency)} <small>per month</small>
          </strong>
          <div className="date-shift" aria-label="Recommended start-date movement">
            <span><small>Original</small><strong>{data.original_start_date}</strong></span>
            <span aria-hidden="true">&rarr;</span>
            <span><small>Recommended</small><strong>{data.recommended_start_date}</strong></span>
          </div>
          <code>{data.position_ref}</code>
          <p>{humanizeCode(data.reason_code)}</p>
        </article>
      </section>

      <section className="boundary-comparison" aria-label="Approval and candidate boundaries">
        <article>
          <span className="boundary-owner">Source business domain</span>
          <p className="section-kicker">Approval boundary</p>
          <h3>{data.approval_outcome}</h3>
          <code>{data.approval_ref}</code>
          <p>The business owner approved the decision; Pythia did not self-certify it.</p>
        </article>
        <span className="boundary-arrow" aria-hidden="true">&rarr;</span>
        <article>
          <span className="boundary-owner">Shared admission boundary</span>
          <p className="section-kicker">Returned candidate</p>
          <h3>{data.candidate_admission_outcome}</h3>
          <code>{data.candidate_ref}</code>
          <p>Approval and admission remain separate. Unsupported is not reported as rejected.</p>
        </article>
      </section>

      <section className="integrity-callout">
        <span className="integrity-mark" aria-hidden="true">G12</span>
        <div>
          <p className="section-kicker">Finite-loop firewall</p>
          <h3>The planning output does not re-enter the accounting event stream.</h3>
          <p>Only admitted business events may drive posting-rule evaluation; this returned candidate remains outside that boundary.</p>
        </div>
      </section>

      <ExactReadFooter envelope={decision} />
    </div>
  );
}

type CorrectionStep = "reconciliation" | "exception" | "governance" | "integrity";

const correctionSteps: Array<{ id: CorrectionStep; owner: string; label: string; href: string }> = [
  { id: "reconciliation", owner: "Hermes", label: "Identity mismatch", href: "/hermes/reconciliation/RECON-CT1@v1" },
  { id: "exception", owner: "Argus", label: "Accuracy exception", href: "/argus/exceptions/EXC-CT1@v1" },
  { id: "governance", owner: "Aegis", label: "Verified remediation", href: "/aegis/cases/ISSUE-CT1@v2" },
  { id: "integrity", owner: "Atlas + Argus", label: "Correction integrity", href: "/corrections/VERIFY-CT1@v1" },
];

export function CorrectionRail({ current }: { current: CorrectionStep }) {
  const currentIndex = correctionSteps.findIndex((step) => step.id === current);
  return (
    <nav className="journey-rail supporting-rail" aria-label="Correction-integrity journey progress">
      <div className="journey-rail-heading"><span>O-SJ01</span><strong>Prove correction integrity</strong></div>
      <ol>
        {correctionSteps.map((step, index) => {
          const state = index === currentIndex ? "current" : index < currentIndex ? "passed" : "next";
          return (
            <li className={state} key={step.id}>
              <Link href={step.href} aria-current={state === "current" ? "step" : undefined}>
                <span className="journey-step-number">{String(index + 1).padStart(2, "0")}</span>
                <span><small>{step.owner}</small><strong>{step.label}</strong></span>
              </Link>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export function CorrectionReconciliationScreen({ reconciliation }: { reconciliation: SourceReconciliation }) {
  if (reconciliation.data.reconciliation_type !== "CASH_APPLICATION_IDENTITY") return null;
  const data = reconciliation.data;
  return (
    <div className="screen-stack">
      <CorrectionRail current="reconciliation" />
      <section className="page-heading compact">
        <div><p className="section-kicker">Hermes / Source reconciliation</p><h2>The cash arrived. Its customer identity did not.</h2><p>Hermes exposes the source disagreement without prescribing the accounting correction.</p></div>
        <span className="blocked-badge">{data.reconciliation_status}</span>
      </section>
      <section className="identity-comparison" aria-label="Cash application identity mismatch">
        <article><small>Receipt party</small><strong>{data.receipt_party_ref}</strong><code>{data.cash_application_ref}</code></article>
        <span aria-hidden="true">&ne;</span>
        <article><small>Application party</small><strong>{data.application_party_ref}</strong><code>{data.party_mapping_ref}</code></article>
      </section>
      <section className="integrity-callout warning-callout">
        <span className="integrity-mark" aria-hidden="true">G13</span>
        <div><p className="section-kicker">Referenced-only predecessor</p><h3>The prior journal is observed, not re-authored.</h3><p>The correction begins from immutable pre-scope state exposed through G-13.</p></div>
        <Link className="primary-action" href={`/argus/exceptions/${encodeURIComponent(data.downstream_exception_ref)}`}>Inspect exception <span aria-hidden="true">&rarr;</span></Link>
      </section>
      <ExactReadFooter envelope={reconciliation} />
    </div>
  );
}

export function CorrectionExceptionScreen({ exception }: { exception: AssuranceException }) {
  if (exception.data.exception_type !== "CASH_APPLICATION_IDENTITY") return null;
  const data = exception.data;
  return (
    <div className="screen-stack">
      <CorrectionRail current="exception" />
      <section className="page-heading compact">
        <div><p className="section-kicker">Argus / Machine observation</p><h2>A high-severity accuracy exception, not yet a governance conclusion.</h2><p>Argus links the mismatched parties to the referenced journal and preserves review ownership in Aegis.</p></div>
        <span className="blocked-badge">{data.severity}</span>
      </section>
      <section className="exception-fact-grid">
        <article><small>Amount exposed</small><strong>{formatMinorUnits(data.amount_minor, data.currency)}</strong></article>
        <article><small>Assertion</small><strong>{humanizeCode(data.assertion)}</strong></article>
        <article><small>Referenced journal</small><strong>{data.journal_id}</strong></article>
        <article><small>Test run</small><strong>{data.test_run_ref}</strong></article>
      </section>
      <ReferenceStrip label="Evidence retained by Argus" refs={data.evidence_refs} />
      <section className="journey-handoff-card">
        <div><p className="section-kicker">Human review boundary</p><h3>Take the observation into governance.</h3><p>Confirmation, remediation authority, and issue state remain outside Argus.</p></div>
        <Link className="primary-action" href={`/aegis/cases/${encodeURIComponent(data.related_governance_case_ref)}`}>Open case <span aria-hidden="true">&rarr;</span></Link>
      </section>
      <ExactReadFooter envelope={exception} />
    </div>
  );
}

export function CorrectionGovernanceScreen({ governance }: { governance: GovernanceCase }) {
  const data = governance.data;
  return (
    <div className="screen-stack">
      <CorrectionRail current="governance" />
      <section className="page-heading compact">
        <div><p className="section-kicker">Aegis / Governed remediation</p><h2>Remediation verified is not closed.</h2><p>Aegis records the reviewed finding, correction authority, and exact Argus verification while preserving the issue lifecycle.</p></div>
        <span className="approved-badge">{humanizeCode(data.final_issue_status)}</span>
      </section>
      <section className="governance-chain compact-chain" aria-label="Correction governance chain">
        <article><small>Review</small><strong>{humanizeCode(data.review_disposition)}</strong><code>{data.review_ref}</code></article>
        <article><small>Directive</small><strong>Correction authorised</strong><code>{data.remediation_directive_ref}</code></article>
        <article><small>Verification</small><strong>Argus evidence</strong><code>{data.verification_ref}</code></article>
        <article><small>Issue update</small><strong>{humanizeCode(data.final_issue_status)}</strong><code>{data.final_issue_ref}</code></article>
      </section>
      <ReferenceStrip label="Separate immutable correction records" refs={data.correction_refs} />
      <section className="journey-handoff-card">
        <div><p className="section-kicker">Server-owned proof</p><h3>Inspect binding, balance, identity, and net movement.</h3><p>The public view presents the exact verification; it does not rerun or self-certify the correction.</p></div>
        <Link className="primary-action" href={`/corrections/${encodeURIComponent(data.verification_ref)}`}>Prove integrity <span aria-hidden="true">&rarr;</span></Link>
      </section>
      <ExactReadFooter envelope={governance} />
    </div>
  );
}

export function CorrectionIntegrityScreen({ correction }: { correction: CorrectionIntegrity }) {
  const data = correction.data;
  return (
    <div className="screen-stack">
      <CorrectionRail current="integrity" />
      <section className="page-heading compact">
        <div><p className="section-kicker">Atlas + Argus / Correction integrity</p><h2>Bound first. Reverse exactly. Replace correctly.</h2><p>The values below are the server-owned read model of the exact verification—not client-side recomputation.</p></div>
        <span className="approved-badge">{humanizeCode(data.reversal_binding_status)}</span>
      </section>
      <section className="source-binding-card">
        <div><p className="section-kicker">G-13 source projection</p><h3>{data.source_projection_ref}</h3><p>Referenced-only state, consumed by exact semantic hash before any line comparison.</p></div>
        <code>{data.source_projection_hash}</code>
      </section>
      <section className="journal-proof-grid" aria-label="Correction journal balance results">
        {data.journal_balance_results.map((journal) => {
          const proposal = journal.journal_ref === data.reversal_journal_ref ? data.reversal_proposal_ref : data.replacement_proposal_ref;
          const role = journal.journal_ref === data.reversal_journal_ref ? "Equal-and-opposite reversal" : "Correct identity replacement";
          return (
            <article className="panel journal-proof-card" key={journal.journal_ref}>
              <div><p className="section-kicker">{role}</p><h3>{journal.journal_ref}</h3><code>{proposal}</code></div>
              <dl><div><dt>Debits</dt><dd>{formatMinorUnits(journal.debits_minor, journal.currency)}</dd></div><div><dt>Credits</dt><dd>{formatMinorUnits(journal.credits_minor, journal.currency)}</dd></div></dl>
              <span className={journal.balanced ? "approved-badge" : "blocked-badge"}>{journal.balanced ? "Server verified balanced" : "Unbalanced"}</span>
            </article>
          );
        })}
      </section>
      <section className="correction-result-grid">
        <article><small>Identity before</small><strong>{data.identity_before}</strong></article>
        <span aria-hidden="true">&rarr;</span>
        <article><small>Identity after</small><strong>{data.identity_after}</strong></article>
        <article className="net-result"><small>Control-account net movement</small><strong>{formatMinorUnits(data.control_account_net_movement_minor, data.currency)}</strong><span>Server read-model result</span></article>
      </section>
      <section className="journey-complete-card">
        <span className="completion-mark" aria-hidden="true">OK</span>
        <div><p className="section-kicker">O-SJ01 complete</p><h3>Source bound. Journals balanced. Identity corrected. Net movement zero.</h3><p>Verification {data.verification_ref} supports issue update {data.issue_update_ref}; it does not silently close the issue.</p></div>
        <Link className="secondary-action" href="/">Return to overview <span aria-hidden="true">&rarr;</span></Link>
      </section>
      <ExactReadFooter envelope={correction} />
    </div>
  );
}

function ReferenceStrip({ label, refs }: { label: string; refs: string[] }) {
  return <div className="reference-strip"><span>{label}</span><div>{refs.map((ref) => <code key={ref}>{ref}</code>)}</div></div>;
}

function ExactReadFooter({ envelope }: { envelope: { view_contract: string; query_revision: number; compatibility_read_mode: string; scenario_ref: string } }) {
  return (
    <footer className="exact-read-footer">
      <span><strong>{envelope.view_contract}</strong> / r{envelope.query_revision}</span>
      <span>{envelope.compatibility_read_mode}</span>
      <span>{envelope.scenario_ref}</span>
    </footer>
  );
}
