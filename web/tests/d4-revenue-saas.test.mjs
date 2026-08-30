import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

import { readRuntimeTable } from "./finance-parquet.mjs";

const webRoot = resolve(import.meta.dirname, "..");
const publicData = resolve(webRoot, "public", "finance-data");
const manifest = JSON.parse(readFileSync(resolve(publicData, "runtime-manifest.json"), "utf8"));
const snapshot = JSON.parse(readFileSync(resolve(publicData, "latest-revenue-saas.json"), "utf8"));

const d4Populations = {
  mart_revenue_waterfall_monthly: 66,
  mart_saas_performance_monthly: 3720,
  mart_cfo_presented_operating_metrics: 726,
};

test("D4 admits three exact C2 marts without changing delivery authority", () => {
  assert.equal(manifest.contractVersion, "q-finance-d6-runtime-manifest@v1");
  assert.equal(manifest.deliveryRef, "Q-FINANCE-C2@v1");
  assert.equal(manifest.runtimeTables.length, 24);
  const actual = Object.fromEntries(
    manifest.runtimeTables
      .filter((table) => Object.hasOwn(d4Populations, table.tableName))
      .map((table) => [table.tableName, table.expectedRows]),
  );
  assert.deepEqual(actual, d4Populations);
});

test("all D4 Parquet partitions are present and host-safe", () => {
  const tables = manifest.runtimeTables.filter((table) => Object.hasOwn(d4Populations, table.tableName));
  assert.equal(tables.flatMap((table) => table.files).length, 18);
  for (const table of tables) {
    for (const url of table.files) assert.equal(existsSync(resolve(webRoot, "public", url.slice(1))), true, url);
  }
});

test("warm D4 snapshot binds the exact June 2026 group state", () => {
  assert.equal(snapshot.revenueWaterfalls.length, 1);
  assert.equal(snapshot.saasPerformance.length, 60);
  assert.equal(snapshot.operatingMetrics.length, 11);
  const revenue = snapshot.revenueWaterfalls[0];
  assert.equal(revenue.period_id, "2026-06");
  assert.equal(revenue.reporting_version_ref, "RV-NEXUS-GROUP-2026-06@v1");
  assert.equal(revenue.recognised_revenue_minor, 228800965);
  assert.equal(revenue.closing_deferred_revenue_minor, 170875496);
  assert.equal(revenue.source_package_digest, manifest.sourceDataDigest);
  assert.equal(snapshot.saasPerformance.reduce((sum, row) => sum + row.ending_arr_minor, 0), 2680056468);
  assert.equal(snapshot.saasPerformance.reduce((sum, row) => sum + row.active_customer_count, 0), 957);
});

test("every deferred-revenue waterfall independently reconciles", async () => {
  for (const row of await readRuntimeTable("mart_revenue_waterfall_monthly")) {
    assert.equal(
      Number(row.opening_deferred_revenue_minor) + Number(row.new_billings_minor) - Number(row.recognised_revenue_minor),
      Number(row.closing_deferred_revenue_minor),
      row.period_id,
    );
    assert.equal(Number(row.rollforward_difference_minor), 0, row.period_id);
    assert.equal(Number(row.schedule_difference_minor), 0, row.period_id);
    assert.equal(Number(row.scheduled_revenue_minor), Number(row.recognised_revenue_minor), row.period_id);
  }
});

test("every period MRR movement and ARR annualisation independently reconcile", async () => {
  const periods = Map.groupBy(
    await readRuntimeTable("mart_saas_performance_monthly"),
    (row) => row.period_id,
  );
  for (const [periodId, rows] of periods) {
    const total = (column) => rows.reduce((sum, row) => sum + Number(row[column]), 0);
    assert.equal(
      total("beginning_mrr_minor") + total("new_mrr_minor") + total("expansion_mrr_minor") +
        total("contraction_mrr_minor") + total("churn_mrr_minor") + total("fx_remeasurement_mrr_minor"),
      total("ending_mrr_minor"),
      periodId,
    );
    assert.equal(total("ending_arr_minor"), total("ending_mrr_minor") * 12, periodId);
  }
});

test("D4 keeps revenue, subscription and collections authorities distinct", () => {
  const component = readFileSync(resolve(webRoot, "app", "components", "finance", "RevenueSaasView.tsx"), "utf8");
  assert.match(component, /Distinct operational authority/);
  assert.match(component, /neither statutory revenue nor billings/i);
  assert.match(component, /Beginning-MRR weighted/);
  assert.match(component, /no movement is inferred/i);
  assert.doesNotMatch(component, /notation:\s*"compact"/);
  assert.doesNotMatch(component, /CAC|lifetime value|pipeline/i);
});

test("D4 route uses lazy authorised browser-local tables", () => {
  const route = readFileSync(resolve(webRoot, "app", "revenue-saas", "page.tsx"), "utf8");
  const queries = readFileSync(resolve(webRoot, "app", "lib", "finance-runtime", "queries.ts"), "utf8");
  assert.match(route, /initialView="revenue-saas"/);
  assert.match(queries, /loadRevenueSaasWorkspace/);
  for (const tableName of Object.keys(d4Populations)) assert.match(queries, new RegExp(tableName));
  assert.doesNotMatch(route, /forecast|scenario|valuation/i);
});
