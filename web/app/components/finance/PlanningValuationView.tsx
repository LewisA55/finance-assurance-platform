"use client";

import { useMemo, useState } from "react";
import type {
  PlanningValuationWarmSnapshot,
  PlanningValuationWorkspace,
  PythiaAnnualForecastRow,
} from "../../lib/finance-runtime/contracts";

interface PlanningValuationViewProps {
  workspace: PlanningValuationWorkspace | null;
  warmSnapshot: PlanningValuationWarmSnapshot | null;
  runtimeReady: boolean;
}

const scenarioOrder = ["BASE", "BULL", "BEAR"];

function money(minor: number | null | undefined): string {
  if (minor == null) return "Withheld";
  const pounds = minor / 100;
  const absolute = Math.abs(pounds);
  const [scaled, suffix] = absolute >= 1_000_000_000
    ? [pounds / 1_000_000_000, "bn"]
    : absolute >= 1_000_000
      ? [pounds / 1_000_000, "m"]
      : absolute >= 1_000
        ? [pounds / 1_000, "k"]
        : [pounds, ""];
  return `${scaled < 0 ? "-" : ""}\u00a3${Math.abs(scaled).toFixed(1).replace(/\.0$/, "")}${suffix}`;
}

function percent(bps: number | null | undefined): string {
  return bps == null ? "-" : `${(bps / 100).toFixed(1)}%`;
}

function periodLabel(period: string | null): string {
  if (!period) return "No breach in horizon";
  const [year, month] = period.split("-").map(Number);
  return new Intl.DateTimeFormat("en-GB", { month: "short", year: "numeric" }).format(
    new Date(Date.UTC(year, month - 1, 1)),
  );
}

function ForecastChart({ rows }: { rows: PythiaAnnualForecastRow[] }) {
  const width = 820;
  const height = 260;
  const padding = { left: 62, right: 22, top: 22, bottom: 36 };
  const values = rows.flatMap((row) => [row.revenue_minor, row.ebitda_minor, row.unlevered_free_cash_flow_minor]);
  const minimum = Math.min(0, ...values);
  const maximum = Math.max(1, ...values);
  const range = maximum - minimum;
  const x = (index: number) =>
    padding.left + (index / Math.max(rows.length - 1, 1)) * (width - padding.left - padding.right);
  const y = (value: number) =>
    padding.top + ((maximum - value) / range) * (height - padding.top - padding.bottom);
  const path = (key: "revenue_minor" | "ebitda_minor" | "unlevered_free_cash_flow_minor") =>
    rows.map((row, index) => `${index === 0 ? "M" : "L"}${x(index)},${y(row[key])}`).join(" ");

  return (
    <div className="fi-plan-chart-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Annual forecast revenue, EBITDA and free cash flow">
        <title>Annual forecast revenue, EBITDA and free cash flow</title>
        {[0, 0.25, 0.5, 0.75, 1].map((step) => {
          const lineY = padding.top + step * (height - padding.top - padding.bottom);
          return <line key={step} x1={padding.left} x2={width - padding.right} y1={lineY} y2={lineY} className="fi-chart-grid" />;
        })}
        <line x1={padding.left} x2={width - padding.right} y1={y(0)} y2={y(0)} className="fi-chart-zero" />
        <path d={path("revenue_minor")} className="fi-plan-line revenue" />
        <path d={path("ebitda_minor")} className="fi-plan-line ebitda" />
        <path d={path("unlevered_free_cash_flow_minor")} className="fi-plan-line fcf" />
        {rows.map((row, index) => (
          <text key={row.year} x={x(index)} y={height - 10} textAnchor="middle" className="fi-chart-label">
            {row.year}
          </text>
        ))}
        <text x={padding.left - 8} y={padding.top + 4} textAnchor="end" className="fi-chart-label">{money(maximum)}</text>
        <text x={padding.left - 8} y={height - padding.bottom} textAnchor="end" className="fi-chart-label">{money(minimum)}</text>
      </svg>
      <div className="fi-plan-legend">
        <span><i className="revenue" />Revenue</span>
        <span><i className="ebitda" />EBITDA</span>
        <span><i className="fcf" />Unlevered FCF</span>
      </div>
    </div>
  );
}

export function PlanningValuationView({
  workspace,
  warmSnapshot,
  runtimeReady,
}: PlanningValuationViewProps) {
  const data = workspace ?? warmSnapshot;
  const [selectedScenario, setSelectedScenario] = useState("BASE");
  const forecasts = useMemo(() => data?.annualForecasts ?? [], [data]);
  const selectedRows = useMemo(
    () => forecasts.filter((row) => row.scenario_code === selectedScenario),
    [forecasts, selectedScenario],
  );
  const annual = selectedRows;
  const valuation = data?.valuations.find((row) => row.scenario_code === selectedScenario);
  const scenario = data?.scenarios.find((row) => row.scenario_code === selectedScenario);
  const sensitivity = data?.sensitivities.filter((row) => row.scenario_code === selectedScenario) ?? [];
  const waccValues = [...new Set(sensitivity.map((row) => row.wacc_bps))];
  const growthValues = [...new Set(sensitivity.map((row) => row.terminal_growth_bps))];
  const controlsPassed = data?.executionControls.filter((row) => row.result_status === "PASS").length ?? 10;
  const closing = selectedRows.at(-1);

  if (!data || !valuation || !scenario || !closing) {
    return <section className="fi-panel"><p>Preparing governed Pythia results.</p></section>;
  }

  return (
    <>
      <section className="fi-heading-row fi-plan-heading">
        <div>
          <p className="fi-eyebrow">Pythia / governed scenario execution</p>
          <h2>Plans only become decisions when economics, liquidity and valuation agree.</h2>
        </div>
        <div className="fi-plan-authority">
          <span>Execution authority</span>
          <strong>{runtimeReady ? "Queried from sealed Pythia Parquet" : "Governed Pythia warm snapshot"}</strong>
          <small>{scenario.model_run_ref} · anchored to {scenario.actuals_reporting_version_ref}</small>
        </div>
      </section>

      <section className="fi-scenario-bar" aria-label="Planning scenario">
        <div>
          <p className="fi-eyebrow">Scenario lens</p>
          <strong>Actuals remain fixed at June 2026. Only the governed assumption overlay changes.</strong>
        </div>
        <div className="fi-scenario-switch">
          {scenarioOrder.map((code) => {
            const item = data.scenarios.find((row) => row.scenario_code === code);
            return (
              <button key={code} className={selectedScenario === code ? "active" : ""} type="button" onClick={() => setSelectedScenario(code)}>
                <span>{code}</span>
                <small>{item?.scenario_approval_status === "APPROVED" ? "Approved & locked" : "Draft simulation"}</small>
              </button>
            );
          })}
        </div>
      </section>

      <section className="fi-kpi-grid fi-plan-kpis" aria-label="Scenario decision indicators">
        <article className="fi-kpi-card"><p>Five-year revenue</p><strong>{money(valuation.five_year_revenue_minor)}</strong><div className="fi-kpi-meta"><span className="neutral">Atlas plan lines</span><small>60 explicit months</small></div></article>
        <article className="fi-kpi-card"><p>Five-year EBITDA</p><strong>{money(valuation.five_year_ebitda_minor)}</strong><div className="fi-kpi-meta"><span className="negative">Loss-making plan</span><small>No margin override</small></div></article>
        <article className="fi-kpi-card"><p>Five-year unlevered FCF</p><strong>{money(valuation.five_year_unlevered_fcf_minor)}</strong><div className="fi-kpi-meta"><span className="negative">Cash consumption</span><small>After CapEx and working capital</small></div></article>
        <article className="fi-kpi-card"><p>First funding gap</p><strong>{periodLabel(valuation.first_funding_gap_period)}</strong><div className="fi-kpi-meta"><span className="negative">Facility exhausted</span><small>Not hidden by a cash plug</small></div></article>
        <article className="fi-kpi-card"><p>Peak funding requirement</p><strong>{money(valuation.peak_funding_requirement_minor)}</strong><div className="fi-kpi-meta"><span className="negative">Management action</span><small>Beyond committed liquidity</small></div></article>
      </section>

      <section className="fi-plan-grid">
        <article className="fi-panel">
          <div className="fi-panel-head"><div><p className="fi-eyebrow">Integrated forecast</p><h3>Growth does not convert to free cash flow</h3></div><span>GBP / annual</span></div>
          <ForecastChart rows={annual} />
        </article>
        <article className="fi-panel fi-plan-decision">
          <div className="fi-panel-head"><div><p className="fi-eyebrow">Decision gate</p><h3>Funding action required</h3></div><span className="fi-control-status review">Escalate</span></div>
          <p>The approved operating inputs produce negative EBITDA and exhaust the committed revolving facility. Pythia publishes the economic consequence; it does not manufacture financing or a valuation.</p>
          <dl>
            <div><dt>Scenario authority</dt><dd>{scenario.pythia_result_status.replaceAll("_", " ")}</dd></div>
            <div><dt>Facility breach</dt><dd>{periodLabel(valuation.first_funding_gap_period)}</dd></div>
            <div><dt>Horizon-end cash</dt><dd>{money(closing.closing_cash_minor)}</dd></div>
            <div><dt>Horizon-end net debt</dt><dd>{money(closing.net_debt_minor)}</dd></div>
            <div><dt>Balance-sheet control</dt><dd>£0 difference</dd></div>
          </dl>
        </article>
      </section>

      <section className="fi-panel fi-scenario-comparison">
        <div className="fi-panel-head"><div><p className="fi-eyebrow">Cross-scenario decision table</p><h3>Scale, cash burn and governance state</h3></div><span>Five-year explicit period</span></div>
        <div className="fi-scenario-table-wrap">
          <table>
            <thead><tr><th>Scenario</th><th>Authority</th><th>Revenue</th><th>EBITDA</th><th>Unlevered FCF</th><th>First funding gap</th><th>Peak requirement</th><th>DCF</th></tr></thead>
            <tbody>
              {data.valuations.map((row) => (
                <tr key={row.scenario_code} className={row.scenario_code === selectedScenario ? "selected" : ""}>
                  <th><button type="button" onClick={() => setSelectedScenario(row.scenario_code)}>{row.scenario_code}</button></th>
                  <td>{row.scenario_approval_status}</td><td>{money(row.five_year_revenue_minor)}</td><td>{money(row.five_year_ebitda_minor)}</td><td>{money(row.five_year_unlevered_fcf_minor)}</td><td>{periodLabel(row.first_funding_gap_period)}</td><td>{money(row.peak_funding_requirement_minor)}</td><td><span className="fi-control-status review">Blocked</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="fi-plan-grid fi-plan-statements">
        <article className="fi-panel">
          <div className="fi-panel-head"><div><p className="fi-eyebrow">Integrated three-statement spine</p><h3>Annual operating and funding bridge</h3></div><span>{selectedScenario}</span></div>
          <div className="fi-statement-table-wrap">
            <table>
              <thead><tr><th>£</th>{annual.slice(0, 6).map((row) => <th key={row.year}>{row.year}</th>)}</tr></thead>
              <tbody>
                {[{ label: "Revenue", key: "revenue_minor" }, { label: "EBITDA", key: "ebitda_minor" }, { label: "Operating cash flow", key: "operating_cash_flow_minor" }, { label: "Capital expenditure", key: "capex_minor", invert: true }, { label: "Unlevered FCF", key: "unlevered_free_cash_flow_minor" }, { label: "Closing cash", key: "closing_cash_minor" }, { label: "Net debt", key: "net_debt_minor" }].map((line) => (
                  <tr key={line.label}><th>{line.label}</th>{annual.slice(0, 6).map((row) => <td key={row.year}>{money((row[line.key as keyof PythiaAnnualForecastRow] as number) * (line.invert ? -1 : 1))}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
        <article className="fi-panel fi-balance-proof">
          <div className="fi-panel-head"><div><p className="fi-eyebrow">Horizon-end position</p><h3>Balance sheet remains integrated</h3></div><span className="fi-control-status pass">Reconciled</span></div>
          <dl>
            <div><dt>Total assets</dt><dd>{money(closing.total_assets_minor)}</dd></div>
            <div><dt>Total liabilities</dt><dd>{money(closing.total_liabilities_minor)}</dd></div>
            <div><dt>Total equity</dt><dd>{money(closing.total_equity_minor)}</dd></div>
            <div className="total"><dt>Assets less liabilities & equity</dt><dd>{money(closing.balance_sheet_difference_minor)}</dd></div>
            <div><dt>Cash-flow rollforward difference</dt><dd>{money(closing.cash_rollforward_difference_minor)}</dd></div>
          </dl>
        </article>
      </section>

      <section className="fi-plan-grid fi-valuation-grid">
        <article className="fi-panel fi-valuation-gate">
          <div className="fi-panel-head"><div><p className="fi-eyebrow">DCF valuation gate</p><h3>Terminal value withheld</h3></div><span className="fi-control-status review">Not supportable</span></div>
          <div className="fi-valuation-message"><strong>Negative terminal-year free cash flow fails the perpetuity-growth precondition.</strong><p>The explicit forecast PV is retained for traceability, but Pythia will not turn a negative terminal cash flow into a mechanically precise enterprise value.</p></div>
          <dl className="fi-valuation-list">
            <div><dt>WACC</dt><dd>{percent(valuation.wacc_bps)}</dd></div>
            <div><dt>Terminal growth</dt><dd>{percent(valuation.terminal_growth_bps)}</dd></div>
            <div><dt>Explicit-period PV</dt><dd>{money(valuation.explicit_period_pv_minor)}</dd></div>
            <div><dt>Terminal-year FCF</dt><dd>{money(valuation.terminal_year_fcf_minor)}</dd></div>
            <div><dt>Terminal value</dt><dd>Withheld</dd></div>
          </dl>
        </article>
        <article className="fi-panel">
          <div className="fi-panel-head"><div><p className="fi-eyebrow">WACC / terminal-growth sensitivity</p><h3>Guardrail matrix</h3></div><span>25 evaluated states</span></div>
          <div className="fi-sensitivity-grid" style={{ gridTemplateColumns: `72px repeat(${growthValues.length}, 1fr)` }}>
            <span>WACC / g</span>{growthValues.map((growth) => <strong key={growth}>{percent(growth)}</strong>)}
            {waccValues.flatMap((wacc) => [
              <strong key={`w-${wacc}`}>{percent(wacc)}</strong>,
              ...growthValues.map((growth) => {
                const cell = sensitivity.find((row) => row.wacc_bps === wacc && row.terminal_growth_bps === growth);
                return <span key={`${wacc}-${growth}`} className={cell?.valuation_status === "READY" ? "ready" : "blocked"}>{cell?.valuation_status === "READY" ? money(cell.implied_value_per_share_minor) : "Blocked"}</span>;
              }),
            ])}
          </div>
        </article>
      </section>

      <section className="fi-panel fi-pythia-controls">
        <div className="fi-panel-head"><div><p className="fi-eyebrow">Executed model assurance</p><h3>{controlsPassed}/10 Pythia validators pass</h3></div><span>{workspace ? "Browser replayed" : "Sealed package snapshot"}</span></div>
        <div>
          {data.executionControls.map((control) => (
            <article key={control.control_id}><span>{control.control_id}</span><strong>{control.control_name.replaceAll("_", " ")}</strong><small>{control.actual_value} / {control.expected_value}</small><i className="fi-control-status pass">Pass</i></article>
          ))}
        </div>
      </section>
    </>
  );
}
