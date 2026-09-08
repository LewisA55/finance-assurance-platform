import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

import { readRuntimeTable } from "./finance-parquet.mjs";

const webRoot = resolve(import.meta.dirname, "..");
const publicData = resolve(webRoot, "public", "finance-data");
const manifest = JSON.parse(readFileSync(resolve(publicData, "runtime-manifest.json"), "utf8"));
const latest = JSON.parse(
  readFileSync(resolve(publicData, "latest-financial-performance.json"), "utf8"),
);
const d2Populations = {
  mart_financial_performance_monthly: 198,
  mart_cfo_presented_financials: 8514,
  mart_planning_performance_monthly: 10416,
  dim_reporting_scope: 3,
  dim_reporting_version: 198,
};

test("D2 runtime extends the exact published C2 authority", () => {
  assert.equal(manifest.contractVersion, "q-finance-d6-runtime-manifest@v1");
  assert.equal(manifest.deliveryRef, "Q-FINANCE-C2@v1");
  assert.equal(manifest.runtimeTables.length, 24);
  const actual = Object.fromEntries(
    manifest.runtimeTables
      .filter((table) => Object.hasOwn(d2Populations, table.tableName))
      .map((table) => [table.tableName, table.expectedRows]),
  );
  assert.deepEqual(actual, d2Populations);
});

test("independent D2 YTD and LTM sums reconcile to the 66-month runtime", async () => {
  const rows = (await readRuntimeTable("mart_financial_performance_monthly")).filter(
    (row) => row.scope_id === "NEXUS-GROUP",
  );
  const totals = (startPeriod) => {
    const included = rows.filter(
      (row) => row.period_id >= startPeriod && row.period_id <= "2026-06",
    );
    return {
      rows: included.length,
      revenue: included.reduce((sum, row) => sum + Number(row.revenue_minor), 0),
      grossProfit: included.reduce((sum, row) => sum + Number(row.gross_profit_minor), 0),
      ebitda: included.reduce((sum, row) => sum + Number(row.ebitda_minor), 0),
      operatingProfit: included.reduce((sum, row) => sum + Number(row.operating_profit_minor), 0),
      netIncome: included.reduce((sum, row) => sum + Number(row.net_income_minor), 0),
    };
  };
  assert.deepEqual(totals("2026-01"), {
    rows: 6,
    revenue: 1376998385,
    grossProfit: 1274053356,
    ebitda: -1064273954,
    operatingProfit: -1227698121,
    netIncome: -1155894614,
  });
  assert.deepEqual(totals("2025-07"), {
    rows: 12,
    revenue: 2764959569,
    grossProfit: 2564026894,
    ebitda: -2141655984,
    operatingProfit: -2527612841,
    netIncome: -2384404783,
  });
});

test("all D2 Parquet partitions are present and host-safe", () => {
  const tables = manifest.runtimeTables.filter((table) =>
    Object.hasOwn(d2Populations, table.tableName),
  );
  assert.equal(tables.flatMap((table) => table.files).length, 35);
  for (const table of tables) {
    for (const url of table.files) {
      assert.equal(existsSync(resolve(webRoot, "public", url.slice(1))), true, url);
    }
  }
});

test("warm D2 snapshot contains the three exact June 2026 reporting scopes", () => {
  assert.deepEqual(latest.map((row) => row.scope_id), ["NEXUS-GROUP", "NEXUS-UK", "NEXUS-US"]);
  for (const row of latest) {
    assert.equal(row.period_id, "2026-06");
    assert.equal(row.reliability_status, "RELIABLE_FOR_STATUTORY_ACTUALS");
    assert.equal(row.source_package_digest, manifest.sourceDataDigest);
  }
  const byScope = Object.fromEntries(latest.map((row) => [row.scope_id, row]));
  assert.equal(byScope["NEXUS-GROUP"].reporting_version_ref, "RV-NEXUS-GROUP-2026-06@v1");
  assert.equal(
    byScope["NEXUS-GROUP"].revenue_minor -
      byScope["NEXUS-UK"].revenue_minor -
      byScope["NEXUS-US"].revenue_minor,
    -22150000,
  );
});

test("D2 route retains statutory and management-source authority separation", () => {
  const route = readFileSync(resolve(webRoot, "app", "financial-performance", "page.tsx"), "utf8");
  const component = readFileSync(
    resolve(webRoot, "app", "components", "finance", "FinancialPerformanceView.tsx"),
    "utf8",
  );
  const queries = readFileSync(resolve(webRoot, "app", "lib", "finance-runtime", "queries.ts"), "utf8");
  assert.match(route, /initialView="financial-performance"/);
  assert.match(component, /Separate management authority/);
  assert.match(component, /not substituted for the statutory statement/i);
  assert.match(component, /Group less UK less US/);
  assert.match(queries, /mart_financial_performance_monthly/);
  assert.match(queries, /mart_planning_performance_monthly/);
  assert.match(queries, /dim_reporting_version/);
});

test("runtime registers only explicitly required tables for each query", () => {
  const runtime = readFileSync(resolve(webRoot, "app", "lib", "finance-runtime", "client.ts"), "utf8");
  assert.match(runtime, /Runtime table is not authorised/);
  assert.match(runtime, /ensureRuntimeTables\(tableNames\)/);
  assert.match(runtime, /registeredTableFiles/);
});
