import type {
  PresentedOperatingMetricRow,
  RevenueSaasWarmSnapshot,
  RevenueSaasWorkspace,
  RevenueWaterfallRow,
  SaasPerformanceRow,
} from "../../lib/finance-runtime/contracts";

interface RevenueSaasViewProps {
  workspace: RevenueSaasWorkspace | null;
  warmSnapshot: RevenueSaasWarmSnapshot | null;
  selectedPeriod: string;
  runtimeReady: boolean;
}

interface PortfolioRow {
  key: string;
  arr: number;
  customers: number;
  share: number;
}

const sum = (rows: SaasPerformanceRow[], key: keyof SaasPerformanceRow) =>
  rows.reduce((total, row) => total + Number(row[key]), 0);

function formatMoney(minor: number | null | undefined, compact = true): string {
  if (minor == null) return "-";
  const pounds = minor / 100;
  const absolute = Math.abs(pounds);
  const [scaled, suffix] = compact && absolute >= 1_000_000_000
    ? [pounds / 1_000_000_000, "bn"]
    : compact && absolute >= 1_000_000
      ? [pounds / 1_000_000, "m"]
      : compact && absolute >= 1_000
        ? [pounds / 1_000, "k"]
        : [pounds, ""];
  const decimals = compact && suffix ? 1 : 0;
  const formatted = Math.abs(scaled).toFixed(decimals).replace(/\.0$/, "");
  return `${scaled < 0 ? "-" : ""}£${formatted}${suffix}`;
}

function formatPercent(basisPoints: number | null | undefined): string {
  return basisPoints == null ? "-" : `${(basisPoints / 100).toFixed(1)}%`;
}

function formatPeriod(periodId: string): string {
  const [year, month] = periodId.split("-").map(Number);
  return new Intl.DateTimeFormat("en-GB", { month: "long", year: "numeric" }).format(
    new Date(Date.UTC(year, month - 1, 1)),
  );
}

function aggregatePortfolio(
  rows: SaasPerformanceRow[],
  key: "product_name" | "region_name" | "customer_segment",
): PortfolioRow[] {
  const totalArr = Math.max(sum(rows, "ending_arr_minor"), 1);
  const groups = new Map<string, { arr: number; customers: number }>();
  for (const row of rows) {
    const current = groups.get(row[key]) ?? { arr: 0, customers: 0 };
    current.arr += row.ending_arr_minor;
    current.customers += row.active_customer_count;
    groups.set(row[key], current);
  }
  return [...groups.entries()]
    .map(([groupKey, value]) => ({
      key: groupKey,
      ...value,
      share: value.arr / totalArr,
    }))
    .sort((left, right) => right.arr - left.arr);
}

function weightedRetention(
  rows: SaasPerformanceRow[],
  key: "gross_revenue_retention_bps" | "net_revenue_retention_bps",
): number | null {
  const beginningMrr = sum(rows, "beginning_mrr_minor");
  if (!beginningMrr) return null;
  return rows.reduce(
    (total, row) => total + row[key] * row.beginning_mrr_minor,
    0,
  ) / beginningMrr;
}

function RevenueHistory({ rows, selectedPeriod }: { rows: RevenueWaterfallRow[]; selectedPeriod: string }) {
  const width = 760;
  const height = 230;
  const padding = { left: 48, right: 18, top: 18, bottom: 32 };
  const maximum = Math.max(...rows.flatMap((row) => [row.recognised_revenue_minor, row.new_billings_minor]), 1);
  const x = (index: number) => padding.left + (index / Math.max(rows.length - 1, 1)) * (width - padding.left - padding.right);
  const y = (value: number) => padding.top + ((maximum - value) / maximum) * (height - padding.top - padding.bottom);
  const path = (key: "recognised_revenue_minor" | "new_billings_minor") => rows
    .map((row, index) => `${index ? "L" : "M"}${x(index)},${y(row[key])}`)
    .join(" ");
  const selectedIndex = rows.findIndex((row) => row.period_id === selectedPeriod);

  return (
    <div className="fi-revenue-history" aria-label="Recognised revenue and billings history">
      <svg viewBox={`0 0 ${width} ${height}`} role="img">
        <title>Recognised revenue and billings, January 2021 to June 2026</title>
        {[0, 0.25, 0.5, 0.75, 1].map((step) => {
          const lineY = padding.top + step * (height - padding.top - padding.bottom);
          return <line key={step} x1={padding.left} x2={width - padding.right} y1={lineY} y2={lineY} className="fi-chart-grid" />;
        })}
        {selectedIndex >= 0 && <line x1={x(selectedIndex)} x2={x(selectedIndex)} y1={padding.top} y2={height - padding.bottom} className="fi-revenue-selected" />}
        <path d={path("recognised_revenue_minor")} className="fi-chart-line fi-revenue-line" />
        <path d={path("new_billings_minor")} className="fi-chart-line fi-billings-line" />
        <text x={padding.left} y={height - 9} className="fi-chart-label">Jan 2021</text>
        <text x={width - padding.right} y={height - 9} textAnchor="end" className="fi-chart-label">Jun 2026</text>
        <text x={padding.left - 7} y={padding.top + 4} textAnchor="end" className="fi-chart-label">{formatMoney(maximum)}</text>
      </svg>
      <div className="fi-history-legend"><span><i className="revenue" /> Recognised revenue</span><span><i className="billings" /> Billings</span></div>
    </div>
  );
}

function PortfolioList({ title, rows }: { title: string; rows: PortfolioRow[] }) {
  return (
    <article className="fi-portfolio-list">
      <h4>{title}</h4>
      {rows.map((row) => (
        <div key={row.key}>
          <span>{row.key.replaceAll("_", " ")}</span>
          <i><b style={{ width: `${row.share * 100}%` }} /></i>
          <strong>{formatMoney(row.arr)}</strong>
          <small>{(row.share * 100).toFixed(1)}%</small>
        </div>
      ))}
    </article>
  );
}

function metric(rows: PresentedOperatingMetricRow[], metricId: string) {
  return rows.find((row) => row.metric_id === metricId);
}

export function RevenueSaasView({
  workspace,
  warmSnapshot,
  selectedPeriod,
  runtimeReady,
}: RevenueSaasViewProps) {
  const waterfalls = workspace?.revenueWaterfalls ?? warmSnapshot?.revenueWaterfalls ?? [];
  const allSaasRows = workspace?.saasPerformance ?? warmSnapshot?.saasPerformance ?? [];
  const allMetrics = workspace?.operatingMetrics ?? warmSnapshot?.operatingMetrics ?? [];
  const waterfall = waterfalls.find((row) => row.period_id === selectedPeriod) ?? waterfalls.at(-1);
  const saasRows = allSaasRows.filter((row) => row.period_id === selectedPeriod);
  const metrics = allMetrics.filter((row) => row.period_id === selectedPeriod);

  if (!waterfall) {
    return <div className="fi-chart-loading"><strong>Revenue state unavailable</strong><span>No governed revenue-waterfall row exists for the selected period.</span></div>;
  }

  const beginningMrr = sum(saasRows, "beginning_mrr_minor");
  const newMrr = sum(saasRows, "new_mrr_minor");
  const expansionMrr = sum(saasRows, "expansion_mrr_minor");
  const contractionMrr = sum(saasRows, "contraction_mrr_minor");
  const churnMrr = sum(saasRows, "churn_mrr_minor");
  const fxMrr = sum(saasRows, "fx_remeasurement_mrr_minor");
  const endingMrr = sum(saasRows, "ending_mrr_minor");
  const endingArr = sum(saasRows, "ending_arr_minor");
  const customers = sum(saasRows, "active_customer_count");
  const subscriptions = sum(saasRows, "active_subscription_count");
  const nrr = weightedRetention(saasRows, "net_revenue_retention_bps");
  const grr = weightedRetention(saasRows, "gross_revenue_retention_bps");
  const mrrDifference = beginningMrr + newMrr + expansionMrr + contractionMrr + churnMrr + fxMrr - endingMrr;
  const deferredDifference = waterfall.opening_deferred_revenue_minor + waterfall.new_billings_minor - waterfall.recognised_revenue_minor - waterfall.closing_deferred_revenue_minor;
  const presentedRevenue = metric(metrics, "REVENUE")?.metric_value_minor;
  const presentedArr = metric(metrics, "ENDING_ARR")?.metric_value_minor;
  const collections = metric(metrics, "COLLECTIONS")?.metric_value_minor;
  const acquisitionDormant = newMrr === 0 && expansionMrr === 0;

  return (
    <>
      <section className="fi-heading-row fi-performance-heading">
        <div>
          <p className="fi-eyebrow">Revenue subledger / Subscription state</p>
          <h2>Revenue &amp; SaaS Economics</h2>
          <p>Recognised revenue, recurring-value movements and portfolio quality for {formatPeriod(selectedPeriod)}.</p>
        </div>
        <div className={`fi-revenue-signal ${acquisitionDormant ? "watch" : "stable"}`}>
          <span>{acquisitionDormant ? "Growth watch" : "Growth active"}</span>
          <strong>{acquisitionDormant ? "No new or expansion MRR in period" : "Positive acquisition or expansion MRR"}</strong>
          <small>{formatMoney(Math.abs(churnMrr))} MRR churn recorded; no movement is inferred where the source reports zero.</small>
        </div>
      </section>

      <section className="fi-kpi-grid fi-revenue-kpis">
        <article className="fi-kpi-card"><p>Ending ARR</p><strong>{formatMoney(endingArr)}</strong><div className="fi-kpi-meta"><span className="neutral">Subscription state</span><small>{subscriptions.toLocaleString("en-GB")} active subscriptions</small></div></article>
        <article className="fi-kpi-card"><p>Recognised revenue</p><strong>{formatMoney(waterfall.recognised_revenue_minor)}</strong><div className="fi-kpi-meta"><span className="neutral">Revenue subledger</span><small>{waterfall.schedule_line_count.toLocaleString("en-GB")} schedule lines</small></div></article>
        <article className="fi-kpi-card"><p>Net revenue retention</p><strong>{formatPercent(nrr)}</strong><div className="fi-kpi-meta"><span className={nrr != null && nrr >= 10000 ? "positive" : "negative"}>Beginning-MRR weighted</span><small>Gross retention {formatPercent(grr)}</small></div></article>
        <article className="fi-kpi-card"><p>Active customers</p><strong>{customers.toLocaleString("en-GB")}</strong><div className="fi-kpi-meta"><span className="neutral">Published cohort total</span><small>{saasRows.length} product-region-segment cohorts</small></div></article>
        <article className="fi-kpi-card"><p>Billings</p><strong>{formatMoney(waterfall.new_billings_minor)}</strong><div className="fi-kpi-meta"><span className="neutral">Revenue waterfall input</span><small>{formatMoney(waterfall.closing_deferred_revenue_minor)} closing deferred revenue</small></div></article>
      </section>

      <section className="fi-revenue-grid">
        <article className="fi-panel">
          <div className="fi-panel-head"><div><p className="fi-eyebrow">66-month history</p><h3>Revenue and billing progression</h3></div><span>{waterfall.value_authority.replaceAll("_", " ")}</span></div>
          {runtimeReady && waterfalls.length > 1 ? <RevenueHistory rows={waterfalls} selectedPeriod={selectedPeriod} /> : <div className="fi-chart-loading"><strong>Preparing revenue history</strong><span>The latest governed close remains visible while DuckDB-Wasm loads the partitions.</span></div>}
          <div className="fi-revenue-conversion">
            <div><span>Recognised revenue</span><strong>{formatMoney(waterfall.recognised_revenue_minor, false)}</strong></div>
            <div><span>Billings</span><strong>{formatMoney(waterfall.new_billings_minor, false)}</strong></div>
            <div><span>Collections</span><strong>{formatMoney(collections, false)}</strong><small>Distinct operational authority</small></div>
          </div>
        </article>

        <article className="fi-panel">
          <div className="fi-panel-head"><div><p className="fi-eyebrow">Contract liability</p><h3>Deferred-revenue waterfall</h3></div><span>{deferredDifference === 0 ? "Reconciled" : "Difference visible"}</span></div>
          <dl className="fi-revenue-waterfall">
            <div><dt>Opening deferred revenue</dt><dd>{formatMoney(waterfall.opening_deferred_revenue_minor, false)}</dd></div>
            <div className="positive"><dt>New billings</dt><dd>+{formatMoney(waterfall.new_billings_minor, false)}</dd></div>
            <div className="negative"><dt>Recognised revenue</dt><dd>-{formatMoney(waterfall.recognised_revenue_minor, false)}</dd></div>
            <div className="total"><dt>Closing deferred revenue</dt><dd>{formatMoney(waterfall.closing_deferred_revenue_minor, false)}</dd></div>
            <div className="control"><dt>Rollforward difference</dt><dd>{formatMoney(deferredDifference, false)}</dd></div>
          </dl>
          <p className="fi-panel-note">Scheduled revenue equals {formatMoney(waterfall.scheduled_revenue_minor)}; the published schedule difference is {formatMoney(waterfall.schedule_difference_minor)}.</p>
        </article>
      </section>

      <section className="fi-panel fi-mrr-panel">
        <div className="fi-panel-head"><div><p className="fi-eyebrow">Monthly recurring revenue</p><h3>Subscription movement bridge</h3></div><span>{mrrDifference === 0 ? "Reconciled" : "Difference visible"}</span></div>
        <div className="fi-mrr-bridge">
          {[
            ["Opening MRR", beginningMrr, "anchor"],
            ["New", newMrr, "inflow"],
            ["Expansion", expansionMrr, "inflow"],
            ["Contraction", contractionMrr, "outflow"],
            ["Churn", churnMrr, "outflow"],
            ["FX", fxMrr, "other"],
            ["Ending MRR", endingMrr, "anchor"],
          ].map(([label, value, tone]) => (
            <div key={String(label)} className={String(tone)}><span>{label}</span><i /><strong>{formatMoney(Number(value))}</strong></div>
          ))}
        </div>
        <div className="fi-authority-boundary"><strong>Measurement boundary</strong><span>ARR and MRR are subscription-state measures. They are neither statutory revenue nor billings. The bridge preserves the signed source movements and reports a {formatMoney(mrrDifference)} difference.</span></div>
      </section>

      <section className="fi-panel fi-portfolio-panel">
        <div className="fi-panel-head"><div><p className="fi-eyebrow">Recurring-revenue portfolio</p><h3>ARR composition and concentration</h3></div><span>{formatMoney(endingArr)} governed ARR</span></div>
        {saasRows.length ? (
          <div className="fi-portfolio-grid">
            <PortfolioList title="Product" rows={aggregatePortfolio(saasRows, "product_name")} />
            <PortfolioList title="Region" rows={aggregatePortfolio(saasRows, "region_name")} />
            <PortfolioList title="Customer segment" rows={aggregatePortfolio(saasRows, "customer_segment")} />
          </div>
        ) : <div className="fi-chart-loading"><strong>Subscription detail unavailable</strong><span>No product-region-segment rows exist for the selected period.</span></div>}
      </section>

      <section className="fi-panel fi-revenue-control-panel">
        <div className="fi-panel-head"><div><p className="fi-eyebrow">Authority cross-check</p><h3>Source-to-presentation consistency</h3></div><span>{waterfall.reliability_status.replaceAll("_", " ")}</span></div>
        <div className="fi-revenue-controls">
          <div><span>Subledger revenue</span><strong>{formatMoney(waterfall.recognised_revenue_minor, false)}</strong><small>{waterfall.reporting_version_ref}</small></div>
          <div><span>Presented revenue</span><strong>{formatMoney(presentedRevenue, false)}</strong><small>{metric(metrics, "REVENUE")?.value_authority.replaceAll("_", " ") ?? "Preparing presentation metric"}</small></div>
          <div><span>Subscription ARR</span><strong>{formatMoney(endingArr, false)}</strong><small>{formatMoney(presentedArr, false)} executive presentation</small></div>
          <div><span>Control state</span><strong>{deferredDifference === 0 && mrrDifference === 0 ? "Reconciled" : "Review"}</strong><small>Revenue and subscription bridges tested independently</small></div>
        </div>
      </section>
    </>
  );
}
