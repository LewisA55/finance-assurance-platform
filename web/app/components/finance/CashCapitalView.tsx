"use client";

import type {
  CashCapitalWarmSnapshot,
  CashCapitalWorkspace,
  CashFlowLiquidityRow,
  CustomerCollectionsRow,
  FixedAssetRow,
} from "../../lib/finance-runtime/contracts";

const moneyDetailed = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 0,
});

const number = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });

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

function label(value: string): string {
  return value
    .toLowerCase()
    .split("_")
    .map((word) => `${word.slice(0, 1).toUpperCase()}${word.slice(1)}`)
    .join(" ");
}

function CashKpi({
  label: itemLabel,
  value,
  context,
  tone = "neutral",
}: {
  label: string;
  value: string;
  context: string;
  tone?: "neutral" | "positive" | "negative";
}) {
  return (
    <article className="fi-kpi-card">
      <p>{itemLabel}</p>
      <strong>{value}</strong>
      <div className="fi-kpi-meta">
        <span className={tone}>{context}</span>
        <small>Selected close</small>
      </div>
    </article>
  );
}

function CashHistory({ rows, selectedPeriod }: { rows: CashFlowLiquidityRow[]; selectedPeriod: string }) {
  const maximum = Math.max(...rows.flatMap((row) => [row.closing_cash_minor, row.closing_debt_minor]), 1);
  return (
    <div className="fi-history-bars" role="img" aria-label="Monthly closing cash and debt history">
      {rows.map((row) => (
        <div key={row.period_id} className={`fi-history-month${row.period_id === selectedPeriod ? " selected" : ""}`} title={`${row.period_id}: cash ${formatMoney(row.closing_cash_minor)}, debt ${formatMoney(row.closing_debt_minor)}`}>
          <i className="cash" style={{ height: `${Math.max((row.closing_cash_minor / maximum) * 100, 1)}%` }} />
          <i className="debt" style={{ height: `${Math.max((row.closing_debt_minor / maximum) * 100, 1)}%` }} />
        </div>
      ))}
    </div>
  );
}

function CollectionsTable({ rows }: { rows: CustomerCollectionsRow[] }) {
  const sorted = [...rows].sort((left, right) => right.overdue_ar_minor - left.overdue_ar_minor);
  return (
    <div className="fi-table-scroll">
      <table className="fi-collections-table">
        <thead>
          <tr><th>Region / segment</th><th>Closing AR</th><th>Overdue</th><th>DSO</th><th>Collections</th><th>Efficiency</th></tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr key={`${row.region_id}-${row.customer_segment}`}>
              <th><strong>{row.region_name}</strong><span>{label(row.customer_segment)}</span></th>
              <td>{formatMoney(row.closing_ar_minor, false)}</td>
              <td>{formatMoney(row.overdue_ar_minor, false)}</td>
              <td>{row.dso_days.toFixed(1)} days</td>
              <td>{formatMoney(row.collections_minor, false)}</td>
              <td><span className={row.collection_efficiency_bps >= 10_000 ? "favourable" : "unfavourable"}>{formatPercent(row.collection_efficiency_bps)}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FixedAssetTable({ rows }: { rows: FixedAssetRow[] }) {
  return (
    <div className="fi-table-scroll">
      <table className="fi-capital-table">
        <thead><tr><th>Asset class</th><th>Assets</th><th>Additions</th><th>D&A</th><th>Closing NBV</th></tr></thead>
        <tbody>
          {[...rows].sort((left, right) => right.closing_net_book_value_minor - left.closing_net_book_value_minor).map((row) => (
            <tr key={`${row.legal_entity_id}-${row.asset_class}`}>
              <th>{label(row.asset_class)}</th>
              <td>{number.format(row.asset_count)}</td>
              <td>{formatMoney(row.capex_additions_minor, false)}</td>
              <td>{formatMoney(row.depreciation_minor + row.amortisation_minor, false)}</td>
              <td>{formatMoney(row.closing_net_book_value_minor, false)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface CashCapitalViewProps {
  workspace: CashCapitalWorkspace | null;
  warmSnapshot: CashCapitalWarmSnapshot | null;
  selectedPeriod: string;
  selectedScope: string;
  runtimeReady: boolean;
  populationsMatch: boolean | undefined;
  packageControlCount: number;
  onInspectData: () => void;
}

export function CashCapitalView({
  workspace,
  warmSnapshot,
  selectedPeriod,
  selectedScope,
  runtimeReady,
  populationsMatch,
  packageControlCount,
  onInspectData,
}: CashCapitalViewProps) {
  const balanceSheets = workspace?.balanceSheets ?? warmSnapshot?.balanceSheets ?? [];
  const cashFlows = workspace?.cashFlows ?? warmSnapshot?.cashFlows ?? [];
  const workingCapitalRows = workspace?.workingCapital ?? warmSnapshot?.workingCapital ?? [];
  const capitalRows = workspace?.capitalStructure ?? warmSnapshot?.capitalStructure ?? [];

  const cashFlow = cashFlows.find((row) => row.period_id === selectedPeriod && row.scope_id === selectedScope) ?? null;
  const balanceSheet = balanceSheets.find((row) => row.period_id === selectedPeriod && row.scope_id === selectedScope) ?? null;
  const workingCapital = workingCapitalRows.find((row) => row.period_id === selectedPeriod) ?? null;
  const capital = capitalRows.find((row) => row.period_id === selectedPeriod && row.scope_id === selectedScope) ?? null;
  const history = cashFlows
    .filter((row) => row.scope_id === selectedScope)
    .sort((left, right) => left.period_id.localeCompare(right.period_id));
  const collections = workspace?.customerCollections.filter((row) => row.period_id === selectedPeriod) ?? [];
  const fixedAssets = workspace?.fixedAssets.filter(
    (row) => row.period_id === selectedPeriod && (selectedScope === "NEXUS-GROUP" || row.legal_entity_id === selectedScope),
  ) ?? [];
  const taxEquity = workspace?.taxEquity.find((row) => row.period_id === selectedPeriod && row.scope_id === selectedScope) ?? null;
  const wcDriver = workspace?.workingCapitalDrivers.find((row) => row.period_id === selectedPeriod) ?? null;

  if (!cashFlow || !balanceSheet) {
    return (
      <section className="fi-view-unavailable">
        <p className="fi-eyebrow">Cash & capital</p>
        <h2>The selected statutory cash position is unavailable.</h2>
        <p>No governed cash-flow and balance-sheet pair exists for this period and scope.</p>
      </section>
    );
  }

  const bridge = [
    { label: "Opening cash", value: cashFlow.opening_cash_minor, anchor: true },
    { label: "Operating", value: cashFlow.operating_cash_flow_minor },
    { label: "Investing", value: cashFlow.investing_cash_flow_minor },
    { label: "Financing", value: cashFlow.financing_cash_flow_minor },
    { label: "FX & other", value: cashFlow.fx_and_other_movement_minor },
    { label: "Closing cash", value: cashFlow.closing_cash_minor, anchor: true },
  ];
  const bridgeScale = Math.max(...bridge.map((item) => Math.abs(item.value)), 1);
  const overdueRate = workingCapital?.closing_ar_minor
    ? (workingCapital.overdue_ar_minor / workingCapital.closing_ar_minor) * 10_000
    : null;
  const cashReconciles = cashFlow.opening_cash_minor + cashFlow.net_change_in_cash_minor === cashFlow.closing_cash_minor;
  const latestDriverDifference = wcDriver && balanceSheet
    ? wcDriver.operating_working_capital_minor - balanceSheet.operating_working_capital_minor
    : null;

  return (
    <>
      <section className="fi-heading-row fi-performance-heading">
        <div>
          <p className="fi-eyebrow">Liquidity and funding / {formatPeriod(selectedPeriod)}</p>
          <h2>Follow cash conversion from operating drivers into the statutory close.</h2>
        </div>
        <div className={`fi-capital-signal ${cashFlow.operating_cash_flow_minor < 0 ? "watch" : "stable"}`}>
          <span>Management signal</span>
          <strong>{cashFlow.operating_cash_flow_minor < 0 ? "Operating cash burn" : "Operating cash generation"}</strong>
          <small>{formatMoney(Math.abs(cashFlow.operating_cash_flow_minor))} in the selected month</small>
        </div>
      </section>

      <section className="fi-publication-strip" aria-label="Cash and balance-sheet publication state">
        <div><span>Cash reconciliation</span><strong>{cashFlow.reconciliation_status}</strong></div>
        <div><span>Cash equation</span><strong>{cashReconciles ? "Reconciled" : "Mismatch"}</strong></div>
        <div><span>Balance sheet</span><strong>{balanceSheet.balance_sheet_difference_minor === 0 ? "Balanced" : "Difference"}</strong></div>
        <div><span>Runtime population</span><strong>{populationsMatch == null ? "Preparing" : populationsMatch ? "Reconciled" : "Mismatch"}</strong></div>
        <button type="button" onClick={onInspectData}><span>Delivery controls</span><strong>{packageControlCount}/{packageControlCount} pass</strong></button>
      </section>

      <section className="fi-kpi-grid" aria-label="Cash and capital indicators">
        <CashKpi label="Closing cash" value={formatMoney(cashFlow.closing_cash_minor)} context="Statutory cash flow" />
        <CashKpi label="Available liquidity" value={formatMoney(cashFlow.available_liquidity_minor)} context="Cash plus undrawn facility" tone="positive" />
        <CashKpi label="Net debt" value={formatMoney(cashFlow.net_debt_minor)} context="Debt and leases less cash" tone={cashFlow.net_debt_minor > 0 ? "negative" : "positive"} />
        <CashKpi label="Operating cash flow" value={formatMoney(cashFlow.operating_cash_flow_minor)} context="Selected month" tone={cashFlow.operating_cash_flow_minor < 0 ? "negative" : "positive"} />
        <CashKpi label="Operating working capital" value={formatMoney(workingCapital?.operating_working_capital_minor)} context="Operational driver state" />
        <CashKpi label="Overdue receivables" value={formatMoney(workingCapital?.overdue_ar_minor)} context={`${formatPercent(overdueRate)} of closing AR`} tone={overdueRate != null && overdueRate > 5_000 ? "negative" : "neutral"} />
      </section>

      <section className="fi-cash-grid">
        <article className="fi-panel fi-cash-bridge-panel">
          <div className="fi-panel-head">
            <div><p className="fi-eyebrow">Monthly cash bridge</p><h3>Opening cash to reconciled close</h3></div>
            <span>GBP / statutory cash flow</span>
          </div>
          <div className="fi-cash-bridge">
            {bridge.map((item) => (
              <div key={item.label} className={item.anchor ? "anchor" : item.value < 0 ? "outflow" : "inflow"}>
                <span>{item.label}</span>
                <i style={{ width: `${Math.max((Math.abs(item.value) / bridgeScale) * 100, item.value === 0 ? 0 : 2)}%` }} />
                <strong>{formatMoney(item.value, false)}</strong>
              </div>
            ))}
          </div>
          <p className="fi-panel-note">Bridge components are copied from the reconciled statutory cash-flow mart. Fixed-asset additions are not relabelled as cash capex.</p>
        </article>

        <article className="fi-panel fi-liquidity-history-panel">
          <div className="fi-panel-head">
            <div><p className="fi-eyebrow">66-month close history</p><h3>Cash against drawn debt</h3></div>
            <span>{selectedScope}</span>
          </div>
          {runtimeReady && history.length > 1 ? (
            <CashHistory rows={history} selectedPeriod={selectedPeriod} />
          ) : (
            <div className="fi-chart-loading"><strong>Preparing liquidity history</strong><span>The latest governed close remains visible while the local query starts.</span></div>
          )}
          <div className="fi-history-legend"><span><i className="cash" /> Closing cash</span><span><i className="debt" /> Drawn debt</span></div>
          <dl className="fi-performance-ratios">
            <div><dt>Undrawn facility</dt><dd>{formatMoney(cashFlow.undrawn_facility_minor)}</dd></div>
            <div><dt>Cash interest</dt><dd>{formatMoney(cashFlow.cash_interest_minor)}</dd></div>
            <div><dt>Lease cash</dt><dd>{formatMoney(cashFlow.lease_cash_payment_minor)}</dd></div>
          </dl>
        </article>
      </section>

      <section className="fi-panel fi-working-capital-panel">
        <div className="fi-panel-head">
          <div><p className="fi-eyebrow">Working-capital conversion / Group operational view</p><h3>Receivables, payables and deferred revenue</h3></div>
          <span>{workingCapital?.value_authority.replaceAll("_", " ") ?? "Operational rows unavailable"}</span>
        </div>
        <div className="fi-authority-boundary">
          <strong>Distinct operational authority</strong>
          <span>This view explains cash conversion but does not replace the statutory balance-sheet position. The difference is visible, never plugged.</span>
        </div>
        {workingCapital ? (
          <div className="fi-working-capital-layout">
            <dl className="fi-wc-driver-list">
              <div><dt>Closing AR</dt><dd>{formatMoney(workingCapital.closing_ar_minor)}</dd><small>{workingCapital.dso_days.toFixed(1)} DSO</small></div>
              <div><dt>Closing AP</dt><dd>{formatMoney(workingCapital.closing_ap_minor)}</dd><small>{workingCapital.dpo_days.toFixed(1)} DPO</small></div>
              <div><dt>Deferred revenue</dt><dd>{formatMoney(workingCapital.closing_deferred_revenue_minor)}</dd><small>Contract funding</small></div>
              <div><dt>Monthly WC movement</dt><dd>{formatMoney(wcDriver?.change_in_operating_working_capital_minor)}</dd><small>{wcDriver?.change_in_operating_working_capital_minor && wcDriver.change_in_operating_working_capital_minor > 0 ? "Cash absorbed" : "Cash released"}</small></div>
            </dl>
            <div className="fi-wc-reconciliation">
              <p><span>Operational driver state</span><strong>{formatMoney(wcDriver?.operating_working_capital_minor, false)}</strong></p>
              <p><span>Statutory presentation</span><strong>{formatMoney(balanceSheet.operating_working_capital_minor, false)}</strong></p>
              <p className="difference"><span>Visible basis difference</span><strong>{formatMoney(latestDriverDifference, false)}</strong></p>
              <small>Different governed purposes can produce different presentations without weakening either source.</small>
            </div>
          </div>
        ) : <div className="fi-chart-loading"><strong>Working-capital view unavailable</strong><span>No governed group operational row exists for this period.</span></div>}
      </section>

      <section className="fi-panel fi-collections-panel">
        <div className="fi-panel-head">
          <div><p className="fi-eyebrow">Customer collections / Group operational view</p><h3>Overdue exposure by region and segment</h3></div>
          <span>{collections.length ? `${collections.length} governed cohorts` : "Awaiting local query"}</span>
        </div>
        {selectedScope !== "NEXUS-GROUP" ? (
          <div className="fi-chart-loading"><strong>Group operational view held separate</strong><span>Collections are published at region and segment grain, not fabricated into legal-entity scope.</span></div>
        ) : collections.length ? <CollectionsTable rows={collections} /> : <div className="fi-chart-loading"><strong>Preparing collections exposure</strong><span>Region and segment detail loads from the O2C analytical mart.</span></div>}
      </section>

      <section className="fi-capital-grid">
        <article className="fi-panel fi-capital-structure-panel">
          <div className="fi-panel-head">
            <div><p className="fi-eyebrow">Capital structure</p><h3>Debt, leases and capacity</h3></div>
            <span>{capital?.value_authority.replaceAll("_", " ") ?? "Unsupported scope"}</span>
          </div>
          {capital ? (
            <>
              <dl className="fi-capital-metrics">
                <div><dt>Closing debt</dt><dd>{formatMoney(capital.closing_debt_minor)}</dd><small>{capital.debt_instrument_count} instruments</small></div>
                <div><dt>Lease liability</dt><dd>{formatMoney(capital.closing_lease_liability_minor)}</dd><small>{capital.lease_contract_count} contracts</small></div>
                <div><dt>Gross debt</dt><dd>{formatMoney(capital.gross_debt_minor)}</dd><small>Debt plus leases</small></div>
                <div><dt>Debt repayment</dt><dd>{formatMoney(capital.debt_repayment_minor)}</dd><small>Selected month</small></div>
              </dl>
              <div className="fi-funding-capacity"><span>Available liquidity</span><i><b style={{ width: `${Math.min((capital.cash_minor / Math.max(capital.available_liquidity_minor, 1)) * 100, 100)}%` }} /></i><strong>{formatMoney(capital.available_liquidity_minor)}</strong><small>Cash component shown in dark blue; remaining capacity is undrawn facility.</small></div>
            </>
          ) : <div className="fi-chart-loading"><strong>No capital subledger row for this scope</strong><span>D3 does not copy the UK or Group treasury position into an unsupported entity.</span></div>}
        </article>

        <article className="fi-panel fi-balance-integrity-panel">
          <div className="fi-panel-head">
            <div><p className="fi-eyebrow">Balance-sheet integrity</p><h3>Published financial position</h3></div>
            <span>{balanceSheet.reliability_status.replaceAll("_", " ")}</span>
          </div>
          <dl className="fi-balance-equation">
            <div><dt>Total assets</dt><dd>{formatMoney(balanceSheet.total_assets_minor, false)}</dd></div>
            <div><dt>Total liabilities</dt><dd>{formatMoney(balanceSheet.total_liabilities_minor, false)}</dd></div>
            <div><dt>Total equity</dt><dd>{formatMoney(balanceSheet.total_equity_minor, false)}</dd></div>
            <div className="total"><dt>Balance-sheet difference</dt><dd>{formatMoney(balanceSheet.balance_sheet_difference_minor, false)}</dd></div>
          </dl>
          <div className="fi-tax-equity-note">
            <span>Tax and equity rollforward</span>
            <strong>{taxEquity?.reconciliation_status ?? (runtimeReady ? "Unavailable" : "Preparing")}</strong>
            <small>{taxEquity ? `${formatMoney(taxEquity.closing_deferred_tax_asset_minor)} deferred-tax asset; ${formatMoney(taxEquity.closing_retained_earnings_minor)} retained earnings.` : "Loaded from a distinct reconciled statutory rollforward."}</small>
          </div>
        </article>
      </section>

      <section className="fi-panel fi-fixed-assets-panel">
        <div className="fi-panel-head">
          <div><p className="fi-eyebrow">Fixed-asset subledger</p><h3>Capital employed by asset class</h3></div>
          <span>{fixedAssets.length ? `${fixedAssets.reduce((sum, row) => sum + row.asset_count, 0)} registered assets` : "Awaiting supported scope"}</span>
        </div>
        {fixedAssets.length ? <FixedAssetTable rows={fixedAssets} /> : <div className="fi-chart-loading"><strong>No fixed-asset rows for this scope</strong><span>Unsupported entity positions remain unavailable rather than inherited from Group.</span></div>}
        <p className="fi-panel-note">Additions are subledger movements. They are not presented as cash expenditure without matching cash-flow authority.</p>
      </section>
    </>
  );
}
