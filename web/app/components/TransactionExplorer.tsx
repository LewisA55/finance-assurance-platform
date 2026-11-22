import { useState } from "react";
import { closeOutcomes, type CloseOutcome } from "../lib/period-close";
import type { ExplorerData } from "../lib/transaction-explorer";

function matches(terms: string[], ...values: string[]): boolean {
  const searchable = values.join(" ").toLowerCase();
  return terms.every((term) => searchable.includes(term));
}

export function TransactionExplorer({ cases, closeOutcome }: { cases: ExplorerData; closeOutcome?: CloseOutcome }) {
  const [query, setQuery] = useState("");
  const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const visible = cases.flatMap((item) => {
    const caseText = [item.id, item.title, item.summary];
    const stageMatches = (item.evidence?.stages ?? []).flatMap((stage, index) => {
      const traceRefs = stage.trace?.nodes.flatMap((node) => [node.node_ref, node.record_identity]) ?? [];
      return matches(terms, ...caseText, stage.title, stage.owner, ...stage.facts.flat(), ...traceRefs)
        ? [{ title: stage.title, anchor: `${item.id}-stage-${index + 1}` }]
        : [];
    });
    return matches(terms, ...caseText) || stageMatches.length > 0
      ? [{ ...item, stageMatches }]
      : [];
  });
  const unavailable = cases.filter((item) => !item.evidence);

  return (
    <div className="screen-stack transaction-explorer">
      <section className="page-heading compact">
        <div>
          <p className="section-kicker">Assurance Casework</p>
          <h2>Transaction-to-decision explorer</h2>
          <p>Follow the evidence across two canonical cases. Open a source view to inspect its records, verification or directed trace.</p>
        </div>
      </section>
      <section className="panel close-panel" aria-label="Period-close simulation">
        <p className="section-kicker">C-001 / Close simulation</p>
        {closeOutcome ? (
          <>
            <h3>{closeOutcomes[closeOutcome].title}</h3>
            <p>{closeOutcomes[closeOutcome].comparison}</p>
          </>
        ) : (
          <p>Try making the June close decision, then compare your simulated outcome with the recorded C-001 evidence.</p>
        )}
        <a className="secondary-action" href="/period-close">{closeOutcome ? "Start a new close simulation" : "Simulate the June close"}</a>
      </section>
      <section className="panel explorer-search" aria-label="Search case evidence">
        <label htmlFor="explorer-query">Search cases and evidence</label>
        <div>
          <input
            id="explorer-query"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="e.g. PR-O2C-RECOG, J-010 or hiring"
          />
          <button className="secondary-action" type="button" onClick={() => setQuery("")} disabled={!query}>Clear search</button>
        </div>
        <p role="status" aria-live="polite">
          {visible.length === 0 ? "No matching cases." : `${visible.length} ${visible.length === 1 ? "case" : "cases"}`}
          {unavailable.length > 0 && ` Evidence unavailable for ${unavailable.map((item) => item.id).join(", ")}.`}
        </p>
        {visible.length > 0 && (
          <nav aria-label="Matching cases" className="explorer-jumps">
            <ul>
              {visible.map((item) => (
                <li key={item.id}>
                  <a href={`#${item.id}`}>{item.id} / {item.title}</a>
                  {terms.length > 0 && !matches(terms, item.id, item.title, item.summary) && (
                    <ul>
                      {item.stageMatches.map((stage) => (
                        <li key={stage.anchor}><a href={`#${stage.anchor}`}>{stage.title}</a></li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
          </nav>
        )}
      </section>
      {visible.map(({ id, title, summary, evidence }) => (
        <section id={id} aria-labelledby={`${id}-heading`} className="panel explorer-case" key={id}>
          <p className="section-kicker">{id}</p>
          <h3 id={`${id}-heading`}>{title}</h3>
          <p>{summary}</p>
          {evidence ? (
            <>
              <ol className="explorer-stages" aria-label={`${id} evidence stages`}>
                {evidence.stages.map((stage, index) => (
                  <li id={`${id}-stage-${index + 1}`} key={stage.title}>
                    <p className="section-kicker">{stage.owner}</p>
                    <h4>{stage.title}</h4>
                    <dl>
                      {stage.facts.map(([label, value]) => (
                        <div key={`${label}/${value}`}><dt>{label}</dt><dd>{value}</dd></div>
                      ))}
                    </dl>
                    {stage.trace && (
                      <details>
                        <summary>Directed trace relationships ({stage.trace.edges.length})</summary>
                        <ul className="explorer-edges">
                          {stage.trace.edges.map((edge) => (
                            <li key={JSON.stringify(edge)}>
                              <code>{edge.source_ref}</code>
                              <span>{edge.relationship} <span aria-hidden="true">&rarr;</span></span>
                              <code>{edge.target_ref}</code>
                            </li>
                          ))}
                        </ul>
                      </details>
                    )}
                    <a className="secondary-action" href={stage.link.href}>{stage.link.label}</a>
                  </li>
                ))}
              </ol>
              <footer className="exact-read-footer">
                <span>{evidence.context.scenario_ref}</span>
                <span>{evidence.context.compatibility_read_mode} / r{evidence.context.query_revision}</span>
                <span>{evidence.context.semantic_as_of_time}</span>
              </footer>
            </>
          ) : <p>The required case records could not be loaded and joined. Reload using the complete local product launcher to retry.</p>}
        </section>
      ))}
    </div>
  );
}
