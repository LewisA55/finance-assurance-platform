import { copyFile, mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(scriptDirectory, "..");
const repositoryRoot = resolve(webRoot, "..");
const deliveryRoot = join(
  repositoryRoot,
  "build",
  "finance-delivery",
  "Q-FINANCE-C2-V1",
);
const pythiaRoot = join(repositoryRoot, "build", "pythia", "PYTHIA-D6-V1");
const publicRoot = join(webRoot, "public", "finance-data");
const duckdbPublicRoot = join(webRoot, "public", "duckdb");
const duckdbWasmSource = join(
  webRoot,
  "node_modules",
  "@duckdb",
  "duckdb-wasm",
  "dist",
  "duckdb-eh.wasm",
);
const duckdbWorkerSource = join(
  webRoot,
  "node_modules",
  "@duckdb",
  "duckdb-wasm",
  "dist",
  "duckdb-browser-eh.worker.js",
);
const DUCKDB_CHUNK_BYTES = 12 * 1024 * 1024;
const PARQUET_EXTENSION = {
  version: "v1.5.4",
  platform: "wasm_eh",
  sourceUrl: "https://extensions.duckdb.org/v1.5.4/wasm_eh/parquet.duckdb_extension.wasm",
  url: "/duckdb/extensions/v1.5.4/wasm_eh/parquet.duckdb_extension.wasm",
  bytes: 3218307,
  digest: "sha256:4845705bbd69fc9ad52878d96a505c73cae4a6c509822079cc2413e5eb437f95",
};

const D1_TABLES = [
  "mart_executive_cfo_command_center",
  "mart_cfo_metric_readiness",
  "mart_model_readiness_controls",
];

const D6_TABLES = [
  "dim_pythia_scenario",
  "fct_pythia_forecast_monthly",
  "mart_pythia_valuation",
  "mart_pythia_dcf_sensitivity",
  "mart_pythia_execution_controls",
];

const D2_TABLES = [
  "mart_financial_performance_monthly",
  "mart_cfo_presented_financials",
  "mart_planning_performance_monthly",
  "dim_reporting_scope",
  "dim_reporting_version",
];

const D3_TABLES = [
  "mart_balance_sheet_monthly",
  "mart_cash_flow_liquidity_monthly",
  "mart_ap_working_capital_monthly",
  "mart_model_working_capital_drivers",
  "mart_o2c_customer_collections_monthly",
  "mart_capital_structure_monthly",
  "mart_fixed_asset_capex_monthly",
  "mart_tax_equity_monthly",
];

const D4_TABLES = [
  "mart_revenue_waterfall_monthly",
  "mart_saas_performance_monthly",
  "mart_cfo_presented_operating_metrics",
];

const RUNTIME_TABLES = [...D1_TABLES, ...D2_TABLES, ...D3_TABLES, ...D4_TABLES];

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

function annualisePythiaForecasts(rows) {
  const groups = new Map();
  for (const row of rows) {
    const year = row.period_id.slice(0, 4);
    const key = `${row.scenario_code}:${year}`;
    groups.set(key, [...(groups.get(key) ?? []), row]);
  }

  return [...groups.values()].map((values) => {
    const ordered = values.sort((left, right) => left.period_id.localeCompare(right.period_id));
    const closing = ordered.at(-1);
    const sum = (column) => ordered.reduce((total, row) => total + row[column], 0);
    return {
      scenario_code: closing.scenario_code,
      year: closing.period_id.slice(0, 4),
      currency: closing.currency,
      revenue_minor: sum("revenue_minor"),
      ebitda_minor: sum("ebitda_minor"),
      unlevered_free_cash_flow_minor: sum("unlevered_free_cash_flow_minor"),
      capex_minor: sum("capex_minor"),
      operating_cash_flow_minor: sum("operating_cash_flow_minor"),
      closing_cash_minor: closing.closing_cash_minor,
      net_debt_minor: closing.net_debt_minor,
      total_assets_minor: closing.total_assets_minor,
      total_liabilities_minor: closing.total_liabilities_minor,
      total_equity_minor: closing.total_equity_minor,
      cumulative_funding_requirement_minor: closing.cumulative_funding_requirement_minor,
      balance_sheet_difference_minor: closing.balance_sheet_difference_minor,
      cash_rollforward_difference_minor: closing.cash_rollforward_difference_minor,
      actuals_reporting_version_ref: closing.actuals_reporting_version_ref,
      value_authority: closing.value_authority,
      reliability_status: closing.reliability_status,
      reliability_purpose: closing.reliability_purpose,
      finance_delivery_digest: closing.finance_delivery_digest,
      source_data_digest: closing.source_data_digest,
    };
  }).sort((left, right) =>
    left.scenario_code.localeCompare(right.scenario_code) || left.year.localeCompare(right.year),
  );
}

function coercePythiaRows(csvText, numericColumns, booleanColumns = new Set()) {
  return parseCsvRows(csvText).map((row) =>
    Object.fromEntries(
      Object.entries(row).map(([key, value]) => [
        key,
        value === "\\N"
          ? null
          : numericColumns.has(key)
            ? Number(value)
            : booleanColumns.has(key)
              ? value === "True" || value === "true"
              : value,
      ]),
    ),
  );
}

async function listFiles(root) {
  const entries = await readdir(root, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) files.push(...(await listFiles(path)));
    else if (entry.isFile()) files.push(path);
  }

  return files.sort();
}

function parseCsvLine(line) {
  const values = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (character === '"') {
      if (quoted && line[index + 1] === '"') {
        value += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (character === "," && !quoted) {
      values.push(value);
      value = "";
    } else {
      value += character;
    }
  }
  values.push(value);
  return values;
}

function parseCsvRows(csvText) {
  const lines = csvText.trim().split(/\r?\n/);
  const headers = parseCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, values[index]]));
  });
}

function coerceRow(row, numericColumns) {
  return Object.fromEntries(
    Object.entries(row).map(([key, value]) => [
      key,
      value === "\\N" ? null : numericColumns.has(key) ? Number(value) : value,
    ]),
  );
}

function latestSnapshot(csvText) {
  const rows = parseCsvRows(csvText);
  const latest = rows.sort((left, right) =>
    left.period_id.localeCompare(right.period_id),
  ).at(-1);
  if (!latest) throw new Error("C2 command-centre CSV has no rows");

  const numericColumns = new Set([
    "fiscal_year",
    "revenue_minor",
    "gross_profit_minor",
    "ebitda_minor",
    "net_income_minor",
    "gross_margin_bps",
    "ebitda_margin_bps",
    "total_assets_minor",
    "total_liabilities_minor",
    "total_equity_minor",
    "operating_cash_flow_minor",
    "investing_cash_flow_minor",
    "financing_cash_flow_minor",
    "closing_cash_minor",
    "gross_debt_minor",
    "net_debt_minor",
    "available_liquidity_minor",
    "billings_minor",
    "collections_minor",
    "closing_ar_minor",
    "overdue_ar_minor",
    "closing_ap_minor",
    "closing_deferred_revenue_minor",
    "operating_working_capital_minor",
    "dso_days",
    "dpo_days",
    "ending_arr_minor",
    "active_customer_count",
    "net_revenue_retention_bps",
    "payroll_cost_minor",
    "active_headcount_count",
    "capex_additions_minor",
    "closing_net_book_value_minor",
    "not_ready_metric_count",
  ]);
  return coerceRow(latest, numericColumns);
}

function latestFinancialPerformance(csvText) {
  const rows = parseCsvRows(csvText);
  const latestPeriod = rows.reduce(
    (latest, row) => (row.period_id > latest ? row.period_id : latest),
    "",
  );
  if (!latestPeriod) throw new Error("C2 financial-performance CSV has no rows");
  const numericColumns = new Set([
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
    "gross_margin_bps",
    "operating_margin_bps",
    "ebitda_margin_bps",
  ]);
  return rows
    .filter((row) => row.period_id === latestPeriod)
    .sort((left, right) => left.scope_id.localeCompare(right.scope_id))
    .map((row) => coerceRow(row, numericColumns));
}

function latestRows(csvText, numericColumns) {
  const rows = parseCsvRows(csvText);
  const latestPeriod = rows.reduce(
    (latest, row) => (row.period_id > latest ? row.period_id : latest),
    "",
  );
  if (!latestPeriod) throw new Error("C2 D3 source CSV has no rows");
  return rows
    .filter((row) => row.period_id === latestPeriod)
    .map((row) => coerceRow(row, numericColumns));
}

async function appendPythiaRuntime(pythiaManifest, deliveryDigest, runtimeTables) {
  if (
    pythiaManifest.pythia_ref !== "PYTHIA-D6@v1" ||
    pythiaManifest.status !== "PUBLISHED" ||
    pythiaManifest.finance_delivery_digest !== deliveryDigest
  ) {
    throw new Error("Expected published PYTHIA-D6@v1 authority bound to C2");
  }

  const pythiaGrains = {
    dim_pythia_scenario: "ONE_ROW_PER_EXECUTED_PLANNING_SCENARIO",
    fct_pythia_forecast_monthly: "ONE_ROW_PER_SCENARIO_FORECAST_MONTH",
    mart_pythia_valuation: "ONE_ROW_PER_SCENARIO_VALUATION",
    mart_pythia_dcf_sensitivity: "ONE_ROW_PER_SCENARIO_WACC_GROWTH_PAIR",
    mart_pythia_execution_controls: "ONE_ROW_PER_EXECUTED_PYTHIA_CONTROL",
  };
  const pythiaScenarios = coercePythiaRows(
    await readFile(join(pythiaRoot, "csv", "dim_pythia_scenario.csv"), "utf8"),
    new Set(),
    new Set(["scenario_locked_flag", "is_governed_pythia_snapshot"]),
  );
  const pythiaForecasts = coercePythiaRows(
    await readFile(join(pythiaRoot, "csv", "fct_pythia_forecast_monthly.csv"), "utf8"),
    new Set([
      "forecast_month_number", "subscription_revenue_minor", "services_revenue_minor",
      "revenue_minor", "cost_of_revenue_minor", "gross_profit_minor",
      "research_and_development_minor", "sales_and_marketing_minor",
      "general_and_administrative_minor", "ebitda_minor",
      "depreciation_and_amortisation_minor", "ebit_minor", "interest_expense_minor",
      "profit_before_tax_minor", "income_tax_expense_minor", "net_income_minor",
      "capex_minor", "change_in_operating_working_capital_minor",
      "unlevered_free_cash_flow_minor", "operating_cash_flow_minor",
      "investing_cash_flow_minor", "financing_cash_flow_minor", "opening_cash_minor",
      "closing_cash_minor", "accounts_receivable_minor", "prepayments_minor",
      "net_property_plant_equipment_minor", "accounts_payable_minor",
      "deferred_revenue_minor", "accrued_expenses_minor", "term_debt_minor",
      "revolver_debt_minor", "lease_liabilities_minor", "net_debt_minor",
      "available_liquidity_minor", "monthly_funding_gap_minor",
      "cumulative_funding_requirement_minor", "total_assets_minor",
      "total_liabilities_minor", "total_equity_minor", "balance_sheet_difference_minor",
      "cash_rollforward_difference_minor", "gross_margin_bps", "ebitda_margin_bps",
    ]),
  );
  const pythiaValuations = coercePythiaRows(
    await readFile(join(pythiaRoot, "csv", "mart_pythia_valuation.csv"), "utf8"),
    new Set([
      "explicit_forecast_months", "wacc_bps", "terminal_growth_bps",
      "explicit_period_pv_minor", "terminal_year_fcf_minor", "terminal_value_minor",
      "present_value_terminal_minor", "enterprise_value_minor", "opening_net_debt_minor",
      "equity_value_minor", "diluted_shares", "implied_value_per_share_minor",
      "five_year_revenue_minor", "five_year_ebitda_minor",
      "five_year_unlevered_fcf_minor", "peak_funding_requirement_minor",
    ]),
  );
  const pythiaSensitivities = coercePythiaRows(
    await readFile(join(pythiaRoot, "csv", "mart_pythia_dcf_sensitivity.csv"), "utf8"),
    new Set([
      "wacc_bps", "terminal_growth_bps", "enterprise_value_minor",
      "equity_value_minor", "implied_value_per_share_minor",
    ]),
  );
  const pythiaExecutionControls = coercePythiaRows(
    await readFile(join(pythiaRoot, "csv", "mart_pythia_execution_controls.csv"), "utf8"),
    new Set(["control_order", "actual_value", "expected_value"]),
  );

  for (const tableName of D6_TABLES) {
    const table = pythiaManifest.tables.find((row) => row.table_name === tableName);
    if (!table) throw new Error(`Missing Pythia metadata for ${tableName}`);
    const sourceFile = join(pythiaRoot, table.parquet_path);
    const targetFile = join(publicRoot, "parquet", "pythia", `${tableName}.parquet`);
    await mkdir(dirname(targetFile), { recursive: true });
    await copyFile(sourceFile, targetFile);
    const sourceBytes = await readFile(sourceFile);
    const url = `/finance-data/parquet/pythia/${tableName}.parquet`;
    runtimeTables.push({
      tableName,
      expectedRows: table.row_count,
      logicalDigest: table.logical_digest,
      grain: pythiaGrains[tableName],
      reliabilityPurpose: tableName === "mart_pythia_valuation"
        ? "GOVERNED_VALUATION_READINESS"
        : "GOVERNED_PYTHIA_MODEL_RESULTS",
      partitionStrategy: "UNPARTITIONED",
      files: [url],
      fileIntegrity: [{
        url,
        bytes: sourceBytes.length,
        digest: `sha256:${createHash("sha256").update(sourceBytes).digest("hex")}`,
      }],
    });
  }

  return {
    scenarios: pythiaScenarios,
    annualForecasts: annualisePythiaForecasts(pythiaForecasts),
    valuations: pythiaValuations,
    sensitivities: pythiaSensitivities,
    executionControls: pythiaExecutionControls,
  };
}

async function buildWarmSnapshots(reconciliation) {
  const financialPerformance = latestFinancialPerformance(
    await readFile(
      join(deliveryRoot, "csv", "mart_financial_performance_monthly.csv"),
      "utf8",
    ),
  );
  const balanceSheets = latestRows(
    await readFile(join(deliveryRoot, "csv", "mart_balance_sheet_monthly.csv"), "utf8"),
    new Set([
      "cash_minor", "accounts_receivable_minor", "prepayments_minor",
      "deferred_tax_asset_minor", "net_property_plant_equipment_minor",
      "goodwill_minor", "net_intangible_assets_minor", "net_right_of_use_assets_minor",
      "accounts_payable_minor", "deferred_revenue_minor", "accrued_expenses_minor",
      "tax_payable_minor", "long_term_debt_minor", "lease_liabilities_minor",
      "share_capital_minor", "retained_earnings_minor", "total_assets_minor",
      "total_liabilities_minor", "total_equity_minor", "operating_working_capital_minor",
      "net_debt_minor", "balance_sheet_difference_minor",
    ]),
  ).sort((left, right) => left.scope_id.localeCompare(right.scope_id));
  const cashFlows = latestRows(
    await readFile(join(deliveryRoot, "csv", "mart_cash_flow_liquidity_monthly.csv"), "utf8"),
    new Set([
      "opening_cash_minor", "operating_cash_flow_minor", "investing_cash_flow_minor",
      "financing_cash_flow_minor", "fx_and_other_movement_minor", "net_change_in_cash_minor",
      "closing_cash_minor", "closing_debt_minor", "closing_lease_liability_minor",
      "undrawn_facility_minor", "cash_interest_minor", "lease_cash_payment_minor",
      "net_debt_minor", "available_liquidity_minor", "unreconciled_difference_minor",
    ]),
  ).sort((left, right) => left.scope_id.localeCompare(right.scope_id));
  const workingCapital = latestRows(
    await readFile(join(deliveryRoot, "csv", "mart_ap_working_capital_monthly.csv"), "utf8"),
    new Set([
      "closing_ar_minor", "overdue_ar_minor", "closing_trade_ap_minor",
      "closing_capital_ap_minor", "closing_ap_minor", "overdue_ap_minor",
      "billings_minor", "collections_minor", "purchases_minor",
      "supplier_payments_minor", "closing_deferred_revenue_minor",
      "trade_working_capital_minor", "operating_working_capital_minor",
      "dso_days", "dpo_days", "overdue_ap_bps",
    ]),
  );
  const capitalStructure = latestRows(
    await readFile(join(deliveryRoot, "csv", "mart_capital_structure_monthly.csv"), "utf8"),
    new Set([
      "opening_debt_minor", "debt_drawdown_minor", "debt_repayment_minor",
      "debt_cash_interest_minor", "debt_accrued_interest_minor", "closing_debt_minor",
      "undrawn_facility_minor", "debt_instrument_count", "opening_lease_liability_minor",
      "lease_addition_minor", "lease_cash_payment_minor", "lease_interest_minor",
      "lease_principal_reduction_minor", "closing_lease_liability_minor",
      "lease_contract_count", "cash_minor", "gross_debt_minor", "net_debt_minor",
      "available_liquidity_minor",
    ]),
  ).sort((left, right) => left.scope_id.localeCompare(right.scope_id));
  const cashCapitalSnapshot = { balanceSheets, cashFlows, workingCapital, capitalStructure };

  const revenueWaterfalls = latestRows(
    await readFile(join(deliveryRoot, "csv", "mart_revenue_waterfall_monthly.csv"), "utf8"),
    new Set([
      "opening_deferred_revenue_minor", "new_billings_minor",
      "recognised_revenue_minor", "closing_deferred_revenue_minor",
      "scheduled_revenue_minor", "schedule_line_count",
      "rollforward_difference_minor", "schedule_difference_minor",
    ]),
  );
  const saasPerformance = latestRows(
    await readFile(join(deliveryRoot, "csv", "mart_saas_performance_monthly.csv"), "utf8"),
    new Set([
      "beginning_mrr_minor", "new_mrr_minor", "expansion_mrr_minor",
      "contraction_mrr_minor", "churn_mrr_minor", "fx_remeasurement_mrr_minor",
      "ending_mrr_minor", "ending_arr_minor", "active_subscription_count",
      "active_customer_count", "new_subscription_count", "churned_subscription_count",
      "gross_revenue_retention_bps", "net_revenue_retention_bps",
    ]),
  ).sort((left, right) =>
    `${left.product_name}|${left.region_name}|${left.customer_segment}`.localeCompare(
      `${right.product_name}|${right.region_name}|${right.customer_segment}`,
    ),
  );
  const operatingMetrics = latestRows(
    await readFile(join(deliveryRoot, "csv", "mart_cfo_presented_operating_metrics.csv"), "utf8"),
    new Set(["metric_value_minor", "metric_value_count", "metric_value_bps"]),
  ).sort((left, right) => left.metric_id.localeCompare(right.metric_id));
  const revenueSaasSnapshot = { revenueWaterfalls, saasPerformance, operatingMetrics };

  const assuranceReportingVersions = latestRows(
    await readFile(join(deliveryRoot, "csv", "dim_reporting_version.csv"), "utf8"),
    new Set(),
  ).sort((left, right) => left.scope_id.localeCompare(right.scope_id));
  const assuranceMetricReadiness = parseCsvRows(
    await readFile(join(deliveryRoot, "csv", "mart_cfo_metric_readiness.csv"), "utf8"),
  ).map((row) => coerceRow(row, new Set([
    "period_count", "minimum_period_count", "null_value_count",
    "acceptable_null_value_count",
  ]))).sort((left, right) => left.metric_label.localeCompare(right.metric_label));
  const assuranceReadinessControls = parseCsvRows(
    await readFile(join(deliveryRoot, "csv", "mart_model_readiness_controls.csv"), "utf8"),
  ).map((row) => coerceRow(row, new Set([
    "control_order", "actual_value", "expected_value",
  ]))).sort((left, right) => left.control_order - right.control_order);
  const assuranceSnapshot = {
    reportingVersions: assuranceReportingVersions,
    metricReadiness: assuranceMetricReadiness,
    readinessControls: assuranceReadinessControls,
    packageReconciliations: reconciliation.rows,
  };

  return { financialPerformance, cashCapitalSnapshot, revenueSaasSnapshot, assuranceSnapshot };
}

async function main() {
  const deliveryManifest = await readJson(join(deliveryRoot, "delivery-manifest.json"));
  const pythiaManifest = await readJson(join(pythiaRoot, "pythia-manifest.json"));
  const queryCatalogue = await readJson(
    join(deliveryRoot, "react", "query-catalogue.json"),
  );
  const reconciliation = await readJson(
    join(deliveryRoot, "metadata", "reconciliation.json"),
  );
  const deliveryDigest = (
    await readFile(join(deliveryRoot, "finance-delivery.digest"), "utf8")
  ).trim();
  const pythiaDigest = (await readFile(join(pythiaRoot, "pythia.digest"), "utf8")).trim();

  if (
    deliveryManifest.delivery_ref !== "Q-FINANCE-C2@v1" ||
    deliveryManifest.status !== "PUBLISHED"
  ) {
    throw new Error("Expected published Q-FINANCE-C2@v1 delivery authority");
  }

  await mkdir(join(publicRoot, "parquet"), { recursive: true });
  await mkdir(join(publicRoot, "metadata"), { recursive: true });
  await mkdir(duckdbPublicRoot, { recursive: true });
  await copyFile(duckdbWorkerSource, join(duckdbPublicRoot, "duckdb-browser-eh.worker.js"));

  const duckdbWasm = await readFile(duckdbWasmSource);
  const duckdbParts = [];
  for (let offset = 0, index = 0; offset < duckdbWasm.length; offset += DUCKDB_CHUNK_BYTES, index += 1) {
    const bytes = duckdbWasm.subarray(offset, offset + DUCKDB_CHUNK_BYTES);
    const filename = `duckdb-eh.part-${String(index).padStart(2, "0")}.bin`;
    await writeFile(join(duckdbPublicRoot, filename), bytes);
    duckdbParts.push({
      url: `/duckdb/${filename}`,
      bytes: bytes.length,
      digest: `sha256:${createHash("sha256").update(bytes).digest("hex")}`,
    });
  }

  const runtimeTables = [];
  for (const tableName of RUNTIME_TABLES) {
    const table = deliveryManifest.tables.find((row) => row.table_name === tableName);
    const queryTable = queryCatalogue.tables.find((row) => row.table_name === tableName);
    if (!table || !queryTable) throw new Error(`Missing C2 metadata for ${tableName}`);

    const sourceDirectory = join(
      deliveryRoot,
      "react",
      "parquet",
      tableName,
    );
    const sourceFiles = (await listFiles(sourceDirectory)).filter((path) =>
      path.endsWith(".parquet"),
    );
    if (sourceFiles.length === 0) throw new Error(`No Parquet files for ${tableName}`);

    const files = [];
    const fileIntegrity = [];
    for (const sourceFile of sourceFiles) {
      const sourceRelative = relative(
        join(deliveryRoot, "react", "parquet"),
        sourceFile,
      );
      const targetFile = join(publicRoot, "parquet", sourceRelative);
      await mkdir(dirname(targetFile), { recursive: true });
      await copyFile(sourceFile, targetFile);
      const url = `/finance-data/parquet/${sourceRelative.split(sep).join("/")}`;
      const bytes = await readFile(sourceFile);
      files.push(url);
      fileIntegrity.push({
        url,
        bytes: bytes.length,
        digest: `sha256:${createHash("sha256").update(bytes).digest("hex")}`,
      });
    }

    runtimeTables.push({
      tableName,
      expectedRows: table.row_count,
      logicalDigest: table.logical_digest,
      grain: table.grain,
      reliabilityPurpose: table.reliability_purpose,
      partitionStrategy: queryTable.partition_strategy,
      files,
      fileIntegrity,
    });
  }

  const planningValuationSnapshot = await appendPythiaRuntime(
    pythiaManifest,
    deliveryDigest,
    runtimeTables,
  );

  const runtimeManifest = {
    contractVersion: "q-finance-d6-runtime-manifest@v1",
    deliveryRef: deliveryManifest.delivery_ref,
    deliveryDigest,
    builtAt: deliveryManifest.built_at,
    sourceDataRef: deliveryManifest.source_data_ref,
    sourceDataDigest: deliveryManifest.source_data_digest,
    financeModelRef: deliveryManifest.finance_model_ref,
    financeModelDigest: deliveryManifest.finance_model_digest,
    semanticDigest: deliveryManifest.model_semantic_digest,
    deliveredTableCount: deliveryManifest.delivered_table_count,
    deliveredRowCount: deliveryManifest.delivered_row_count,
    martCount: deliveryManifest.mart_count,
    conformedDimensionCount: deliveryManifest.conformed_dimension_count,
    packageControlCount: deliveryManifest.validation_control_count,
    pythiaRef: pythiaManifest.pythia_ref,
    pythiaDigest,
    pythiaModelRunRef: pythiaManifest.model_run_ref,
    actualsReportingVersionRef: pythiaManifest.actuals_reporting_version_ref,
    pythiaControlCount: pythiaManifest.control_count,
    duckdbWasm: {
      variant: "eh",
      sourceBytes: duckdbWasm.length,
      sourceDigest: `sha256:${createHash("sha256").update(duckdbWasm).digest("hex")}`,
      parts: duckdbParts,
    },
    parquetExtension: PARQUET_EXTENSION,
    runtimeTables,
  };

  const snapshot = latestSnapshot(
    await readFile(
      join(deliveryRoot, "csv", "mart_executive_cfo_command_center.csv"),
      "utf8",
    ),
  );
  const {
    financialPerformance,
    cashCapitalSnapshot,
    revenueSaasSnapshot,
    assuranceSnapshot,
  } = await buildWarmSnapshots(reconciliation);

  await Promise.all([
    writeFile(
      join(publicRoot, "runtime-manifest.json"),
      `${JSON.stringify(runtimeManifest)}\n`,
      "utf8",
    ),
    writeFile(
      join(publicRoot, "latest-command-centre.json"),
      `${JSON.stringify(snapshot)}\n`,
      "utf8",
    ),
    writeFile(
      join(publicRoot, "latest-financial-performance.json"),
      `${JSON.stringify(financialPerformance)}\n`,
      "utf8",
    ),
    writeFile(
      join(publicRoot, "latest-cash-capital.json"),
      `${JSON.stringify(cashCapitalSnapshot)}\n`,
      "utf8",
    ),
    writeFile(
      join(publicRoot, "latest-revenue-saas.json"),
      `${JSON.stringify(revenueSaasSnapshot)}\n`,
      "utf8",
    ),
    writeFile(
      join(publicRoot, "latest-assurance.json"),
      `${JSON.stringify(assuranceSnapshot)}\n`,
      "utf8",
    ),
    writeFile(
      join(publicRoot, "latest-planning-valuation.json"),
      `${JSON.stringify(planningValuationSnapshot)}\n`,
      "utf8",
    ),
    writeFile(
      join(publicRoot, "metadata", "query-catalogue.json"),
      `${JSON.stringify(queryCatalogue)}\n`,
      "utf8",
    ),
    writeFile(
      join(publicRoot, "metadata", "reconciliation.json"),
      `${JSON.stringify(reconciliation)}\n`,
      "utf8",
    ),
    writeFile(
      join(publicRoot, "metadata", "delivery-manifest.json"),
      `${JSON.stringify(deliveryManifest)}\n`,
      "utf8",
    ),
  ]);

  process.stdout.write(
    `Synced ${runtimeTables.reduce((sum, table) => sum + table.files.length, 0)} governed Parquet files and ${duckdbParts.length} DuckDB-Wasm chunks for Slices D1-D6.\n`,
  );
}

await main();
