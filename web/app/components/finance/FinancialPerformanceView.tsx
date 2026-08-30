"use client";

import { useMemo, useState } from "react";
import type {
  FinancialPerformanceRow,
  PlanningPerformanceRow,
  PresentedFinancialRow,
  ReportingVersionRow,
} from "../../lib/finance-runtime/contracts";

type PerformanceBasis = "MONTH" | "YTD" | "LTM";

type MonetaryField =
  | "subscription_revenue_minor"
  | "services_revenue_minor"
  | "revenue_minor"
  | "cost_of_revenue_minor"
  | "gross_profit_minor"
  | "research_and_development_minor"
  | "sales_and_marketing_minor"
  | "general_and_administrative_minor"
  | "depreciation_and_amortisation_minor"
  | "operating_expense_minor"
  | "operating_profit_minor"
  | "ebitda_minor"
  | "interest_expense_minor"
  | "profit_before_tax_minor"
  | "income_tax_expense_minor"
  | "net_income_minor";

const monetaryFields: MonetaryField[] = [
  "subscription_revenue_minor",
  "services_revenue_minor",
  "revenue_minor",
  "cost_of_revenue_minor",
  "gross_profit_minor",
  "research_and_development_minor",
  "sales_and_marketing_minor",
  "general_and_administrative_minor",
  "depreciation_and_amortisation_minor",
  "operating_expense_minor",
  "operating_profit_minor",
  "ebitda_minor",
  "interest_expense_minor",
  "profit_before_tax_minor",
  "income_tax_expense_minor",
  "net_income_minor",
];

const statementLines: Array<{
  field: MonetaryField;
  label: string;
  className?: string;
  indent?: boolean;
}> = [
  { field: "subscription_revenue_minor", label: "Subscription revenue", indent: true },
  { field: "services_revenue_minor", label: "Services revenue", indent: true },
  { field: "revenue_minor", label: "Revenue", className: "subtotal" },
  { field: "cost_of_revenue_minor", label: "Cost of revenue", indent: true },
  { field: "gross_profit_minor", label: "Gross profit", className: "total" },
  { field: "research_and_development_minor", label: "Research & development", indent: true },
  { field: "sales_and_marketing_minor", label: "Sales & marketing", indent: true },
  { field: "general_and_administrative_minor", label: "General & administrative", indent: true },
  { field: "depreciation_and_amortisation_minor", label: "Depreciation & amortisation", indent: true },
  { field: "operating_expense_minor", label: "Operating expense", className: "subtotal" },
  { field: "operating_profit_minor", label: "Operating profit", className: "total" },
  { field: "ebitda_minor", label: "EBITDA", className: "emphasis" },
  { field: "interest_expense_minor", label: "Interest expense", indent: true },
  { field: "profit_before_tax_minor", label: "Profit before tax", className: "subtotal" },
  { field: "income_tax_expense_minor", label: "Income tax expense / (benefit)", indent: true },
  { field: "net_income_minor", label: "Net income", className: "total" },
];

const moneyDetailed = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 0,
});

function formatMoney(value: number | null | undefined, compact = true): string {
  if (value == null) return "-";
  const pounds = value / 100;
  if (!compact) return moneyDetailed.format(pounds);
  const absolute = Math.abs(pounds);
  const [scaled, suffix] = absolute >= 1_000_000_000
    ? [pounds / 1_000_000_000, "bn"]
    : absolute >= 1_000_000
      ? [pounds / 1_000_000, "m"]
      : absolute >= 1_000
        ? [pounds / 1_000, "k"]
        : [pounds, ""];
  const formatted = Math.abs(scaled).toFixed(1).replace(/\.0$/, "");
  return `${scaled < 0 ? "-" : ""}£${formatted}${suffix}`;
}

function formatPercent(value: number | null | undefined): string {
  return value == null || !Number.isFinite(value) ? "-" : `${(value / 100).toFixed(1)}%`;
}

function formatPeriod(periodId: string): string {
  const [year, month] = periodId.split("-").map(Number);
  return new Intl.DateTimeFormat("en-GB", { month: "long", year: "numeric" }).format(
    new Date(Date.UTC(year, month - 1, 1)),
  );
}

function shiftPeriod(periodId: string, months: number): string {
  const [year, month] = periodId.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1 + months, 1));
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
}

function aggregatePerformance(
  rows: FinancialPerformanceRow[],
  scopeId: string,
  endPeriod: string,
  basis: PerformanceBasis,
): FinancialPerformanceRow | null {
  const startPeriod =
    basis === "MONTH"
      ? endPeriod
      : basis === "YTD"
        ? `${endPeriod.slice(0, 4)}-01`
        : shiftPeriod(endPeriod, -11);
  const included = rows.filter(
    (row) => row.scope_id === scopeId && row.period_id >= startPeriod && row.period_id <= endPeriod,
  );
  const anchor = included.find((row) => row.period_id === endPeriod) ?? included.at(-1);
  if (!anchor) return null;
  const aggregate = { ...anchor };
  for (const field of monetaryFields) {
    aggregate[field] = included.reduce((sum, row) => sum + row[field], 0);
  }
  aggregate.gross_margin_bps = aggregate.revenue_minor
    ? (aggregate.gross_profit_minor / aggregate.revenue_minor) * 10_000
    : 0;
  aggregate.operating_margin_bps = aggregate.revenue_minor
    ? (aggregate.operating_profit_minor / aggregate.revenue_minor) * 10_000
    : 0;
  aggregate.ebitda_margin_bps = aggregate.revenue_minor
    ? (aggregate.ebitda_minor / aggregate.revenue_minor) * 10_000
    : 0;
  return aggregate;
}

function basisLabel(basis: PerformanceBasis, periodId: string): string {
  if (basis === "MONTH") return formatPeriod(periodId);
  if (basis === "YTD") return `FY${periodId.slice(0, 4)} year to date`;
  return `12 months to ${formatPeriod(periodId)}`;
}

function valueChange(current: number, comparison: number | undefined): number | null {
  if (comparison == null || comparison === 0) return null;
  return (current - comparison) / Math.abs(comparison);
}

function changeLabel(change: number | null): string {
  if (change == null) return "Prior-year comparison unavailable";
  return `${change >= 0 ? "+" : ""}${(change * 100).toFixed(1)}% vs prior year`;
}

function changeTone(change: number | null): string {
  if (change == null || Math.abs(change) < 0.0005) return "neutral";
  return change > 0 ? "positive" : "negative";
}

function PerformanceKpi({
  label,
  value,
  change,
  context,
}: {
  label: string;
  value: string;
  change: number | null;
  context: string;
}) {
  return (
    <article className="fi-kpi-card">
      <p>{label}</p>
      <strong>{value}</strong>
      <div className="fi-kpi-meta">
        <span className={changeTone(change)}>{changeLabel(change)}</span>
        <small>{context}</small>
      </div>
    </article>
  );
}

function PerformanceTrendChart({
  rows,
  selectedPeriod,
}: {
  rows: FinancialPerformanceRow[];
  selectedPeriod: string;
}) {
  const width = 720;
  const height = 270;
  const padding = { left: 54, right: 18, top: 24, bottom: 34 };
  const values = rows.flatMap((row) => [row.revenue_minor, row.gross_profit_minor, row.ebitda_minor]);
  const minimum = Math.min(...values, 0);
  const maximum = Math.max(...values, 1);
  const range = maximum - minimum || 1;
  const x = (index: number) =>
    padding.left + (index / Math.max(rows.length - 1, 1)) * (width - padding.left - padding.right);
  const y = (value: number) =>
    padding.top + ((maximum - value) / range) * (height - padding.top - padding.bottom);
  const path = (field: "revenue_minor" | "gross_profit_minor" | "ebitda_minor") =>
    rows.map((row, index) => `${index === 0 ? "M" : "L"}${x(index)},${y(row[field])}`).join(" ");
  const selectedIndex = rows.findIndex((row) => row.period_id === selectedPeriod);

  return (
    <div className="fi-chart-wrap" aria-label="Revenue, gross profit and EBITDA trend">
      <svg className="fi-chart" viewBox={`0 0 ${width} ${height}`} role="img">
        <title>Monthly revenue, gross profit and EBITDA</title>
        {[0, 0.25, 0.5, 0.75, 1].map((step) => {
          const lineY = padding.top + step * (height - padding.top - padding.bottom);
          return <line key={step} x1={padding.left} x2={width - padding.right} y1={lineY} y2={lineY} className="fi-chart-grid" />;
        })}
        <line x1={padding.left} x2={width - padding.right} y1={y(0)} y2={y(0)} className="fi-chart-zero" />
        {selectedIndex >= 0 && (
          <line x1={x(selectedIndex)} x2={x(selectedIndex)} y1={padding.top} y2={height - padding.bottom} className="fi-chart-selected" />
        )}
        <path d={path("revenue_minor")} className="fi-chart-line fi-revenue-line" />
        <path d={path("gross_profit_minor")} className="fi-chart-line fi-gross-profit-line" />
        <path d={path("ebitda_minor")} className="fi-chart-line fi-ebitda-line" />
        <text x={padding.left} y={height - 10} className="fi-chart-label">{rows.at(0)?.period_id}</text>
        <text x={width - padding.right} y={height - 10} textAnchor="end" className="fi-chart-label">{rows.at(-1)?.period_id}</text>
        <text x={padding.left - 8} y={padding.top + 4} textAnchor="end" className="fi-chart-label">{formatMoney(maximum)}</text>
        <text x={padding.left - 8} y={height - padding.bottom} textAnchor="end" className="fi-chart-label">{formatMoney(minimum)}</text>
      </svg>
      <div className="fi-chart-legend" aria-hidden="true">
        <span><i className="fi-legend-line revenue" /> Revenue</span>
        <span><i className="fi-legend-line gross-profit" /> Gross profit</span>
        <span><i className="fi-legend-line ebitda" /> EBITDA</span>
      </div>
    </div>
  );
}

function lineLabel(value: string): string {
  return value
    .split("_")
    .map((word) => (word === "and" ? "&" : `${word.slice(0, 1).toUpperCase()}${word.slice(1)}`))
    .join(" ");
}

interface FinancialPerformanceViewProps {
  rows: FinancialPerformanceRow[];
  presentedRows: PresentedFinancialRow[];
  planningRows: PlanningPerformanceRow[];
  reportingVersion: ReportingVersionRow | null;
  selectedPeriod: string;
  selectedScope: string;
  runtimeReady: boolean;
  populationsMatch: boolean | undefined;
  packageControlCount: number;
  onInspectData: () => void;
}

export function FinancialPerformanceView({
  rows,
  presentedRows,
  planningRows,
  reportingVersion,
  selectedPeriod,
  selectedScope,
  runtimeReady,
  populationsMatch,
  packageControlCount,
  onInspectData,
}: FinancialPerformanceViewProps) {
  const [basis, setBasis] = useState<PerformanceBasis>("MONTH");
  const current = useMemo(
    () => aggregatePerformance(rows, selectedScope, selectedPeriod, basis),
    [basis, rows, selectedPeriod, selectedScope],
  );
  const comparison = useMemo(
    () => aggregatePerformance(rows, selectedScope, shiftPeriod(selectedPeriod, -12), basis),
    [basis, rows, selectedPeriod, selectedScope],
  );
  const trendRows = useMemo(
    () => rows.filter((row) => row.scope_id === selectedScope).sort((left, right) => left.period_id.localeCompare(right.period_id)),
    [rows, selectedScope],
  );
  const presentedLineCount = presentedRows.filter(
    (row) => row.period_id === selectedPeriod && row.scope_id === selectedScope && row.statement_class === "INCOME_STATEMENT",
  ).length;
  const entityAggregates = useMemo(
    () => Object.fromEntries(
      ["NEXUS-GROUP", "NEXUS-UK", "NEXUS-US"].map((scopeId) => [
        scopeId,
        aggregatePerformance(rows, scopeId, selectedPeriod, basis),
      ]),
    ) as Record<string, FinancialPerformanceRow | null>,
    [basis, rows, selectedPeriod],
  );
  const budgetLines = useMemo(() => {
    const selectedRows = planningRows.filter(
      (row) => row.period_id === selectedPeriod && row.period_status === "ACTUAL" && !row.is_statutory_actual,
    );
    const grouped = new Map<string, { actual: number; budget: number; variance: number; budgetRef: string | null }>();
    for (const row of selectedRows) {
      const item = grouped.get(row.statement_line) ?? { actual: 0, budget: 0, variance: 0, budgetRef: row.budget_version_ref };
      item.actual += row.actual_amount_minor;
      item.budget += row.budget_amount_minor;
      item.variance += row.actual_vs_budget_variance_minor;
      item.budgetRef ??= row.budget_version_ref;
      grouped.set(row.statement_line, item);
    }
    return [...grouped.entries()]
      .map(([statementLine, value]) => ({ statementLine, ...value }))
      .sort((left, right) => Math.abs(right.variance) - Math.abs(left.variance));
  }, [planningRows, selectedPeriod]);

  if (!current) {
    return (
      <section className="fi-view-unavailable">
        <p className="fi-eyebrow">Financial performance</p>
        <h2>The selected statutory performance view is unavailable.</h2>
        <p>No governed row exists for this period, scope and reporting-version context.</p>
      </section>
    );
  }

  const group = entityAggregates["NEXUS-GROUP"];
  const uk = entityAggregates["NEXUS-UK"];
  const us = entityAggregates["NEXUS-US"];
  const entityMetrics: Array<{ label: string; field: MonetaryField }> = [
    { label: "Revenue", field: "revenue_minor" },
    { label: "Gross profit", field: "gross_profit_minor" },
    { label: "EBITDA", field: "ebitda_minor" },
    { label: "Net income", field: "net_income_minor" },
  ];

  return (
    <>
      <section className="fi-heading-row fi-performance-heading">
        <div>
          <p className="fi-eyebrow">Statutory performance / {basisLabel(basis, selectedPeriod)}</p>
          <h2>Understand what moved, where it moved and what authority supports it.</h2>
        </div>
        <div className="fi-basis-control" aria-label="Performance time basis">
          {(["MONTH", "YTD", "LTM"] as PerformanceBasis[]).map((option) => (
            <button
              key={option}
              type="button"
              className={basis === option ? "active" : ""}
              onClick={() => setBasis(option)}
              disabled={!runtimeReady && option !== "MONTH"}
            >
              {option === "MONTH" ? "Monthly" : option}
            </button>
          ))}
        </div>
      </section>

      <section className="fi-publication-strip" aria-label="Publication and close status">
        <div><span>Close state</span><strong>{reportingVersion?.close_status.replaceAll("_", " ") ?? "Hard closed"}</strong></div>
        <div><span>Statement state</span><strong>{reportingVersion?.statement_status ?? "Published"}</strong></div>
        <div><span>Presented IS lines</span><strong>{runtimeReady ? `${presentedLineCount} governed lines` : "Preparing replay"}</strong></div>
        <div><span>Runtime population</span><strong>{populationsMatch == null ? "Preparing" : populationsMatch ? "Reconciled" : "Mismatch"}</strong></div>
        <button type="button" onClick={onInspectData}><span>Delivery controls</span><strong>{packageControlCount}/{packageControlCount} pass</strong></button>
      </section>

      <section className="fi-kpi-grid" aria-label="Financial performance indicators">
        <PerformanceKpi label="Revenue" value={formatMoney(current.revenue_minor)} change={valueChange(current.revenue_minor, comparison?.revenue_minor)} context="Published statutory statement" />
        <PerformanceKpi label="Gross profit" value={formatMoney(current.gross_profit_minor)} change={valueChange(current.gross_profit_minor, comparison?.gross_profit_minor)} context={`${formatPercent(current.gross_margin_bps)} gross margin`} />
        <PerformanceKpi label="EBITDA" value={formatMoney(current.ebitda_minor)} change={valueChange(current.ebitda_minor, comparison?.ebitda_minor)} context={`${formatPercent(current.ebitda_margin_bps)} EBITDA margin`} />
        <PerformanceKpi label="Operating profit" value={formatMoney(current.operating_profit_minor)} change={valueChange(current.operating_profit_minor, comparison?.operating_profit_minor)} context={`${formatPercent(current.operating_margin_bps)} operating margin`} />
        <PerformanceKpi label="Net income" value={formatMoney(current.net_income_minor)} change={valueChange(current.net_income_minor, comparison?.net_income_minor)} context="After interest and tax" />
        <PerformanceKpi label="Operating expense" value={formatMoney(current.operating_expense_minor)} change={valueChange(Math.abs(current.operating_expense_minor), comparison ? Math.abs(comparison.operating_expense_minor) : undefined)} context="R&D, S&M, G&A and D&A" />
      </section>

      <section className="fi-performance-grid">
        <article className="fi-panel fi-statement-panel">
          <div className="fi-panel-head">
            <div><p className="fi-eyebrow">Management income statement</p><h3>{basisLabel(basis, selectedPeriod)}</h3></div>
            <span>GBP / prior-year basis</span>
          </div>
          <div className="fi-table-scroll">
            <table className="fi-statement-table">
              <thead><tr><th>Statement line</th><th>Current</th><th>Prior year</th><th>Variance</th><th>% revenue</th></tr></thead>
              <tbody>
                {statementLines.map((line) => {
                  const currentValue = current[line.field];
                  const comparisonValue = comparison?.[line.field];
                  return (
                    <tr key={line.field} className={line.className ?? ""}>
                      <th className={line.indent ? "indent" : ""}>{line.label}</th>
                      <td>{formatMoney(currentValue, false)}</td>
                      <td>{formatMoney(comparisonValue, false)}</td>
                      <td>{formatMoney(comparisonValue == null ? null : currentValue - comparisonValue, false)}</td>
                      <td>{formatPercent(current.revenue_minor ? (currentValue / current.revenue_minor) * 10_000 : null)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </article>

        <article className="fi-panel fi-performance-trend-panel">
          <div className="fi-panel-head">
            <div><p className="fi-eyebrow">66-month statutory history</p><h3>Scale, gross profit and operating conversion</h3></div>
            <span>{selectedScope}</span>
          </div>
          {runtimeReady && trendRows.length > 1 ? (
            <PerformanceTrendChart rows={trendRows} selectedPeriod={selectedPeriod} />
          ) : (
            <div className="fi-chart-loading"><strong>Preparing statutory history</strong><span>The latest governed monthly statement remains visible while DuckDB loads the five-year series.</span></div>
          )}
          <dl className="fi-performance-ratios">
            <div><dt>Gross margin</dt><dd>{formatPercent(current.gross_margin_bps)}</dd></div>
            <div><dt>Operating margin</dt><dd>{formatPercent(current.operating_margin_bps)}</dd></div>
            <div><dt>EBITDA margin</dt><dd>{formatPercent(current.ebitda_margin_bps)}</dd></div>
          </dl>
        </article>
      </section>

      <section className="fi-panel fi-entity-panel">
        <div className="fi-panel-head">
          <div><p className="fi-eyebrow">Legal entity to group</p><h3>Published positions and consolidation effect</h3></div>
          <span>Group less UK less US</span>
        </div>
        <div className="fi-table-scroll">
          <table className="fi-entity-table">
            <thead><tr><th>Metric</th><th>Nexus Group</th><th>Nexus UK</th><th>Nexus US</th><th>Consolidation effect</th></tr></thead>
            <tbody>
              {entityMetrics.map((metric) => {
                const effect = group && uk && us ? group[metric.field] - uk[metric.field] - us[metric.field] : null;
                return <tr key={metric.field}><th>{metric.label}</th><td>{formatMoney(group?.[metric.field], false)}</td><td>{formatMoney(uk?.[metric.field], false)}</td><td>{formatMoney(us?.[metric.field], false)}</td><td className={effect && effect < 0 ? "negative" : ""}>{formatMoney(effect, false)}</td></tr>;
              })}
            </tbody>
          </table>
        </div>
        <p className="fi-panel-note">The consolidation effect is a transparent consumer calculation over three separately published statutory scopes. It is not a generated balancing plug.</p>
      </section>

      <section className="fi-panel fi-budget-panel">
        <div className="fi-panel-head">
          <div><p className="fi-eyebrow">Management-source variance / Group view</p><h3>Actual versus approved budget by statement line</h3></div>
          <span>{budgetLines.at(0)?.budgetRef ?? "Budget unavailable"}</span>
        </div>
        <div className="fi-budget-boundary">
          <strong>Separate management authority</strong>
          <span>These actual and budget values come from the management-source variance feed. They are not substituted for the statutory statement above.</span>
        </div>
        {budgetLines.length > 0 ? (
          <div className="fi-table-scroll">
            <table className="fi-budget-table">
              <thead><tr><th>Statement line</th><th>Source actual</th><th>Budget</th><th>Variance</th><th>Variance %</th><th>Assessment</th></tr></thead>
              <tbody>
                {budgetLines.map((line) => {
                  const revenueLine = line.statementLine.endsWith("revenue");
                  const favourable = revenueLine ? line.variance >= 0 : line.variance <= 0;
                  const varianceRate = line.budget ? line.variance / Math.abs(line.budget) : null;
                  return (
                    <tr key={line.statementLine}>
                      <th>{lineLabel(line.statementLine)}</th>
                      <td>{formatMoney(line.actual, false)}</td>
                      <td>{formatMoney(line.budget, false)}</td>
                      <td>{formatMoney(line.variance, false)}</td>
                      <td>{varianceRate == null ? "-" : `${(varianceRate * 100).toFixed(1)}%`}</td>
                      <td><span className={favourable ? "favourable" : "unfavourable"}>{favourable ? "Favourable" : "Unfavourable"}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="fi-chart-loading"><strong>Management budget comparison unavailable</strong><span>No source-report actual and budget rows exist for the selected period.</span></div>
        )}
      </section>
    </>
  );
}
