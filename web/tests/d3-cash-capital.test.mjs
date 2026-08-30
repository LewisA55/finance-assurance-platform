import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

import { readRuntimeTable } from "./finance-parquet.mjs";

const webRoot = resolve(import.meta.dirname, "..");
const publicData = resolve(webRoot, "public", "finance-data");
const manifest = JSON.parse(readFileSync(resolve(publicData, "runtime-manifest.json"), "utf8"));
const snapshot = JSON.parse(readFileSync(resolve(publicData, "latest-cash-capital.json"), "utf8"));

const d3Populations = {
  mart_balance_sheet_monthly: 198,
  mart_cash_flow_liquidity_monthly: 198,
  mart_ap_working_capital_monthly: 66,
  mart_model_working_capital_drivers: 66,
  mart_o2c_customer_collections_monthly: 784,
  mart_capital_structure_monthly: 132,
  mart_fixed_asset_capex_monthly: 330,
  mart_tax_equity_monthly: 198,
};

test("D3 admits eight exact C2 marts without changing delivery authority", () => {
  assert.equal(manifest.contractVersion, "q-finance-d6-runtime-manifest@v1");
  assert.equal(manifest.deliveryRef, "Q-FINANCE-C2@v1");
  assert.equal(manifest.runtimeTables.length, 24);
  const actual = Object.fromEntries(
    manifest.runtimeTables
      .filter((table) => Object.hasOwn(d3Populations, table.tableName))
      .map((table) => [table.tableName, table.expectedRows]),
  );
  assert.deepEqual(actual, d3Populations);
});

test("all D3 Parquet partitions are present and host-safe", () => {
  const tables = manifest.runtimeTables.filter((table) => Object.hasOwn(d3Populations, table.tableName));
  assert.equal(tables.flatMap((table) => table.files).length, 48);
  for (const table of tables) {
    for (const url of table.files) assert.equal(existsSync(resolve(webRoot, "public", url.slice(1))), true, url);
  }
});

test("warm D3 snapshot binds the exact June 2026 hard-close state", () => {
  assert.deepEqual(snapshot.cashFlows.map((row) => row.scope_id), ["NEXUS-GROUP", "NEXUS-UK", "NEXUS-US"]);
  const groupCash = snapshot.cashFlows.find((row) => row.scope_id === "NEXUS-GROUP");
  const groupBalance = snapshot.balanceSheets.find((row) => row.scope_id === "NEXUS-GROUP");
  assert.equal(groupCash.period_id, "2026-06");
  assert.equal(groupCash.reporting_version_ref, "RV-NEXUS-GROUP-2026-06@v1");
  assert.equal(groupCash.opening_cash_minor, 535948052);
  assert.equal(groupCash.net_change_in_cash_minor, -227717867);
  assert.equal(groupCash.closing_cash_minor, 308230185);
  assert.equal(groupCash.available_liquidity_minor, 3358230185);
  assert.equal(groupBalance.balance_sheet_difference_minor, 0);
  assert.equal(groupCash.source_package_digest, manifest.sourceDataDigest);
});

test("independent cash and balance-sheet equations reconcile across all published scopes", async () => {
  const cashRows = await readRuntimeTable("mart_cash_flow_liquidity_monthly");
  const balanceRows = await readRuntimeTable("mart_balance_sheet_monthly");
  for (const row of cashRows) {
    assert.equal(Number(row.opening_cash_minor) + Number(row.net_change_in_cash_minor), Number(row.closing_cash_minor), `${row.scope_id}/${row.period_id}`);
    assert.equal(Number(row.unreconciled_difference_minor), 0, `${row.scope_id}/${row.period_id}`);
    assert.equal(row.reconciliation_status, "RECONCILED");
  }
  for (const row of balanceRows) {
    assert.equal(Number(row.total_assets_minor), Number(row.total_liabilities_and_equity_minor), `${row.scope_id}/${row.period_id}`);
    assert.equal(Number(row.balance_sheet_difference_minor), 0, `${row.scope_id}/${row.period_id}`);
  }
});

test("latest operational collections reconcile internally while retaining a visible statutory basis difference", async () => {
  const collections = (await readRuntimeTable("mart_o2c_customer_collections_monthly")).filter(
    (row) => row.period_id === "2026-06",
  );
  const driver = (await readRuntimeTable("mart_model_working_capital_drivers")).find(
    (row) => row.period_id === "2026-06",
  );
  const groupBalance = (await readRuntimeTable("mart_balance_sheet_monthly")).find(
    (row) => row.period_id === "2026-06" && row.scope_id === "NEXUS-GROUP",
  );
  assert.equal(collections.reduce((sum, row) => sum + Number(row.closing_ar_minor), 0), 807019959);
  assert.equal(collections.reduce((sum, row) => sum + Number(row.overdue_ar_minor), 0), 623943843);
  assert.equal(Number(driver.operating_working_capital_minor), 427555213);
  assert.equal(Number(groupBalance.operating_working_capital_minor), 432781215);
  assert.equal(Number(driver.operating_working_capital_minor) - Number(groupBalance.operating_working_capital_minor), -5226002);
});

test("latest fixed-asset classes aggregate without being labelled as cash capex", async () => {
  const rows = (await readRuntimeTable("mart_fixed_asset_capex_monthly")).filter(
    (row) => row.period_id === "2026-06",
  );
  assert.equal(rows.reduce((sum, row) => sum + Number(row.closing_net_book_value_minor), 0), 1166591476);
  assert.equal(rows.reduce((sum, row) => sum + Number(row.asset_count), 0), 25);
  const component = readFileSync(resolve(webRoot, "app", "components", "finance", "CashCapitalView.tsx"), "utf8");
  assert.match(component, /Additions are subledger movements/);
  assert.match(component, /not presented as cash expenditure/i);
  assert.match(component, /Distinct operational authority/);
  assert.doesNotMatch(component, /notation:\s*"compact"/);
});

test("D3 route uses lazy authorised browser-local tables", () => {
  const route = readFileSync(resolve(webRoot, "app", "cash-capital", "page.tsx"), "utf8");
  const queries = readFileSync(resolve(webRoot, "app", "lib", "finance-runtime", "queries.ts"), "utf8");
  assert.match(route, /initialView="cash-capital"/);
  assert.match(queries, /loadCashCapitalWorkspace/);
  for (const tableName of Object.keys(d3Populations)) assert.match(queries, new RegExp(tableName));
  assert.doesNotMatch(route, /forecast|scenario|valuation/i);
});
