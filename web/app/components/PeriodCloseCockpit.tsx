import { useState } from "react";
import { closeOutcomes, type CloseOutcome, type PeriodCloseBasis } from "../lib/period-close";
import { formatMinorUnits } from "../lib/public-api";

type Treatment = "unresolved" | "resolved" | "deferred";

const treatmentLabels: Record<Treatment, string> = {
  unresolved: "Submitted and unresolved",
  resolved: "Posted in June",
  deferred: "Authorised deferral",
};

export function PeriodCloseCockpit({ basis }: { basis: PeriodCloseBasis }) {
  const [treatment, setTreatment] = useState<Treatment>("unresolved");
  const [signedOff, setSignedOff] = useState(false);
  const [outcome, setOutcome] = useState<CloseOutcome>();
  const { recon, control } = basis;
  const hardClosed = outcome === "resolved" || outcome === "deferred";
  const posted = treatment === "resolved";
  const hasTreatment = treatment !== "unresolved";
  const adjustment = posted ? recon.difference_minor : 0;
  const postedCount = recon.posted_item_count + Number(posted);
  const remainingGap = recon.expected_amount_minor - recon.posted_amount_minor - adjustment;
  const money = (minor: number) => formatMinorUnits(minor, recon.currency);

  function recordTreatment(value: Exclude<Treatment, "unresolved">) {
    setTreatment(value);
    setOutcome(undefined);
  }

  function startNewSimulation() {
    setTreatment("unresolved");
    setSignedOff(false);
    setOutcome(undefined);
  }

  return (
    <div className="screen-stack period-close">
      <section className="page-heading compact">
        <div>
          <p className="section-kicker">C-001 / June 2026 / Simulation</p>
          <h2>Period-close cockpit</h2>
          <p>Decide how to handle the {money(recon.difference_minor)} recognition gap before hard close. Your actions apply only to this browser simulation.</p>
        </div>
        <span className="exact-badge">{hardClosed ? "Hard-closed" : "Soft-closed"}</span>
      </section>

      <div className="close-workbench">
        <section className="panel close-panel" aria-labelledby="close-checklist">
          <p className="section-kicker">01 / Evidence review</p>
          <h3 id="close-checklist">Close checklist</h3>
          <dl className="close-checklist">
            <div><dt>Trial balance</dt><dd>Balanced in scenario setup</dd></div>
            <div><dt>Close reconciliations</dt><dd>Ready in scenario setup</dd></div>
            <div><dt>Recognition completeness</dt><dd>{postedCount}/{recon.expected_item_count} posted · {money(remainingGap)} gap · {posted ? "Pass" : "Gap open"}</dd></div>
            <div><dt>Proposal disposition</dt><dd>{treatmentLabels[treatment]}</dd></div>
            <div><dt>Reviewer sign-off</dt><dd>{signedOff ? "Recorded for this treatment" : "Pending"}</dd></div>
          </dl>
          <details>
            <summary>Recorded evidence used for the simulation</summary>
            <ul className="close-source-list">
              <li><a href={`/hermes/reconciliation/${encodeURIComponent(recon.reconciliation_ref)}`}>Recognition reconciliation</a> <code>{recon.reconciliation_ref}</code></li>
              <li><a href={`/argus/exceptions/${encodeURIComponent(control.exception_ref)}`}>Completeness exception</a> <code>{control.exception_ref}</code></li>
              <li><a href={`/atlas/reporting/${basis.period}/${encodeURIComponent(basis.originalRef)}`}>Original June report</a> <code>{basis.originalRef}</code></li>
            </ul>
          </details>
        </section>

        <section className="panel close-panel" aria-labelledby="close-treatment">
          <p className="section-kicker">02 / Controller treatment</p>
          <h3 id="close-treatment">Resolve the proposal</h3>
          <p>Choose a treatment for the submitted recognition proposal, then have the reviewer sign off.</p>
          <div className="close-actions">
            <button className="secondary-action" type="button" disabled={hasTreatment} onClick={() => recordTreatment("resolved")}>
              Approve, post and rerun control
            </button>
            <button className="secondary-action" type="button" disabled={hasTreatment} onClick={() => recordTreatment("deferred")}>
              Authorise deferral
            </button>
          </div>
          {treatment === "resolved" && (
            <p className="close-treatment-note">Simulated June journal: debit deferred revenue and credit subscription revenue, {money(adjustment)} each.</p>
          )}
          {treatment === "deferred" && (
            <p className="close-treatment-note">Simulated authorisation under <code>POL-CLOSE-v1</code>. The controller owns the unposted recognition, targets restatement review and sets expiry to 31 July 2026.</p>
          )}
          <button className="secondary-action" type="button" disabled={!hasTreatment || signedOff} onClick={() => {
            setSignedOff(true);
            setOutcome(undefined);
          }}>
            Record reviewer sign-off
          </button>
        </section>
      </div>

      <section className="panel close-panel close-decision" aria-labelledby="close-decision">
        <p className="section-kicker">03 / Close decision</p>
        <h3 id="close-decision">Attempt hard close</h3>
        <div className="close-actions">
          <button className="primary-action" type="button" disabled={hardClosed} onClick={() => {
            setOutcome(!hasTreatment ? "unresolved" : !signedOff ? "unsigned" : treatment);
          }}>
            Attempt hard close
          </button>
          <button className="secondary-action" type="button" onClick={startNewSimulation}>Start new simulation</button>
        </div>
        <div role="status" aria-live="polite">
          {outcome && (
            <div className="close-result">
              <h4>{closeOutcomes[outcome].title}</h4>
              <p>{closeOutcomes[outcome].explanation}</p>
              {hardClosed && (
                <dl className="close-checklist">
                  <div><dt>Simulated June subscription revenue at close</dt><dd>{money(basis.revenueMinor + adjustment)}</dd></div>
                  <div><dt>Simulated June deferred revenue at close</dt><dd>{money(basis.deferredRevenueMinor - adjustment)}</dd></div>
                </dl>
              )}
            </div>
          )}
        </div>
        {outcome && <a className="secondary-action" href={`/explorer?close=${outcome}`}>Follow consequences in explorer</a>}
      </section>
    </div>
  );
}
