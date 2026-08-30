import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Product Guide | Nexus Technologies",
  description:
    "The governed architecture, trust boundaries and decision experiences behind the Nexus finance and assurance product.",
};

const reportPages = [
  ["01", "CFO command centre", "/", "Executive state, material signals and readiness."],
  ["02", "Financial performance", "/financial-performance", "Statutory and management performance with variance authority."],
  ["03", "Cash & capital", "/cash-capital", "Cash conversion, working capital and capital structure."],
  ["04", "Revenue & SaaS", "/revenue-saas", "Recognised revenue, recurring value and portfolio quality."],
  ["05", "Assurance", "/assurance", "Close controls, reliability and evidence journeys."],
  ["06", "Planning & valuation", "/planning-valuation", "Governed scenarios, liquidity consequences and valuation gates."],
];

const modules = [
  ["Hermes", "Observe", "Preserves source identity, ingestion state and event lineage."],
  ["Atlas", "Account", "Derives journals, ledgers, reporting versions and financial state."],
  ["Argus", "Assure", "Executes controls and publishes exceptions with reproducible evidence."],
  ["Aegis", "Govern", "Owns findings, remediation, approvals and readiness decisions."],
  ["Pythia", "Simulate", "Overlays governed assumptions without rewriting approved actuals."],
];

export default function ProductGuidePage() {
  return (
    <div className="fi-guide-page">
      <a className="fi-skip-link" href="#finance-main">Skip to product guide</a>
      <div className="fi-synthetic-strip">
        <strong>Synthetic data environment</strong>
        <span>Demonstrative finance and assurance product. No real company data.</span>
      </div>

      <header className="fi-guide-header">
        <Link className="fi-guide-brand" href="/" aria-label="Nexus Technologies finance home">
          <span className="fi-guide-mark">N</span>
          <span><strong>Nexus</strong><small>Technologies</small></span>
        </Link>
        <Link className="fi-guide-return" href="/">Enter management reporting <span aria-hidden="true">→</span></Link>
      </header>

      <main id="finance-main" className="fi-guide-main" tabIndex={-1}>
        <section className="fi-guide-hero">
          <div>
            <p className="fi-eyebrow">Product objective / governed finance intelligence</p>
            <h1>One financial state.<br />Multiple decision lenses.</h1>
          </div>
          <div className="fi-guide-thesis">
            <strong>This is not a dashboard sitting on convenient outputs.</strong>
            <p>Independent business events become balanced accounting, controlled reporting, traceable assurance and governed scenarios before they become management information.</p>
            <dl>
              <div><dt>Actuals authority</dt><dd>Atlas reporting versions</dd></div>
              <div><dt>Scenario authority</dt><dd>Pythia model runs</dd></div>
              <div><dt>Query boundary</dt><dd>Browser-local DuckDB</dd></div>
            </dl>
          </div>
        </section>

        <section className="fi-guide-thread" aria-labelledby="digital-thread-title">
          <div className="fi-guide-section-head">
            <p className="fi-eyebrow">The governed digital thread</p>
            <h2 id="digital-thread-title">Trust travels with the number.</h2>
            <p>Each layer preserves a distinct truth rather than collapsing ingestion, accounting, assurance and planning into one opaque result.</p>
          </div>
          <ol className="fi-guide-flow">
            <li><span>01</span><strong>Source events</strong><small>Independent systems, timing and identifiers</small></li>
            <li><span>02</span><strong>Accounting state</strong><small>Rules, journals, subledgers and trial balance</small></li>
            <li><span>03</span><strong>Governed actuals</strong><small>Reporting versions and reconciled statements</small></li>
            <li><span>04</span><strong>Assurance state</strong><small>Controls, evidence, findings and readiness</small></li>
            <li><span>05</span><strong>Decision state</strong><small>Scenarios, liquidity and valuation gates</small></li>
          </ol>
        </section>

        <section className="fi-guide-modules" aria-labelledby="module-title">
          <div className="fi-guide-section-head compact">
            <p className="fi-eyebrow">Five lenses / one substrate</p>
            <h2 id="module-title">Clear ownership prevents false authority.</h2>
          </div>
          <div className="fi-guide-module-grid">
            {modules.map(([name, verb, description]) => (
              <article key={name}>
                <span>{verb}</span><h3>{name}</h3><p>{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="fi-guide-report" aria-labelledby="report-title">
          <div className="fi-guide-section-head">
            <p className="fi-eyebrow">React management product</p>
            <h2 id="report-title">Six finite experiences, each with a decision purpose.</h2>
            <p>The report body fuses institutional finance presentation with provenance, reliability and control state. It does not recreate accounting or forecast mechanics in the interface.</p>
          </div>
          <nav className="fi-guide-report-grid" aria-label="Management report pages">
            {reportPages.map(([code, label, href, description]) => (
              <Link key={code} href={href}>
                <span>{code}</span><strong>{label}</strong><small>{description}</small><i aria-hidden="true">→</i>
              </Link>
            ))}
          </nav>
        </section>

        <section className="fi-guide-consumers" aria-label="Cross-product delivery boundary">
          <div><p className="fi-eyebrow">Shared analytical handoff</p><h2>Same governed facts. Purpose-built products.</h2></div>
          <article><span>React</span><strong>Explore and explain</strong><p>Local DuckDB-Wasm queries over governed Parquet.</p></article>
          <article><span>Excel</span><strong>Model and challenge</strong><p>High-volume integrated statements and DCF mechanics.</p></article>
          <article><span>Power BI</span><strong>Standardise and distribute</strong><p>Semantic modelling, calculation groups and enterprise reporting.</p></article>
        </section>
      </main>

      <footer className="fi-guide-footer">
        <span>Nexus Technologies / Synthetic data environment</span>
        <span>Business events → accounting → assurance → decisions</span>
      </footer>
    </div>
  );
}
