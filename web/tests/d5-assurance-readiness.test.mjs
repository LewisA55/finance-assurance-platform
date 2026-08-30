import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

import { readRuntimeTable } from "./finance-parquet.mjs";

const webRoot = resolve(import.meta.dirname, "..");
const publicData = resolve(webRoot, "public", "finance-data");
const manifest = JSON.parse(readFileSync(resolve(publicData, "runtime-manifest.json"), "utf8"));
const snapshot = JSON.parse(readFileSync(resolve(publicData, "latest-assurance.json"), "utf8"));

test("D5 remains bound to the C2 tables within the D6 runtime", () => {
  assert.equal(manifest.contractVersion, "q-finance-d6-runtime-manifest@v1");
  assert.equal(manifest.deliveryRef, "Q-FINANCE-C2@v1");
  assert.equal(manifest.runtimeTables.length, 24);
  for (const [tableName, rows] of Object.entries({
    dim_reporting_version: 198,
    mart_cfo_metric_readiness: 11,
    mart_model_readiness_controls: 15,
  })) {
    assert.equal(manifest.runtimeTables.find((table) => table.tableName === tableName)?.expectedRows, rows);
  }
});

test("warm D5 snapshot binds the complete June 2026 readiness state", () => {
  assert.deepEqual(snapshot.reportingVersions.map((row) => row.scope_id), ["NEXUS-GROUP", "NEXUS-UK", "NEXUS-US"]);
  assert.equal(snapshot.metricReadiness.length, 11);
  assert.equal(snapshot.readinessControls.length, 15);
  assert.equal(snapshot.packageReconciliations.length, 36);
  assert.equal(snapshot.reportingVersions.every((row) => row.period_id === "2026-06"), true);
  assert.equal(snapshot.reportingVersions.every((row) => row.source_package_digest === manifest.sourceDataDigest), true);
});

test("all 198 reporting versions retain hard-close and reconciliation source states", async () => {
  const rows = await readRuntimeTable("dim_reporting_version");
  assert.equal(rows.length, 198);
  for (const row of rows) {
    assert.equal(row.subledger_reconciliation_status, "RECONCILED", row.reporting_version_ref);
    assert.ok(["RECONCILED", "CONSOLIDATED", "NOT_APPLICABLE"].includes(row.bank_reconciliation_status), row.reporting_version_ref);
    assert.ok(["CONFIRMED", "NOT_APPLICABLE"].includes(row.intercompany_reconciliation_status), row.reporting_version_ref);
    assert.equal(row.trial_balance_status, "BALANCED", row.reporting_version_ref);
    assert.equal(row.statement_status, "PUBLISHED", row.reporting_version_ref);
    assert.equal(row.close_status, "HARD_CLOSED", row.reporting_version_ref);
  }
});

test("all model-serving readiness controls replay their declared comparisons", async () => {
  const rows = await readRuntimeTable("mart_model_readiness_controls");
  assert.equal(rows.length, 15);
  for (const row of rows) {
    const actual = Number(row.actual_value);
    const expected = Number(row.expected_value);
    const passes = row.comparison_operator === "GREATER_THAN_OR_EQUAL" ? actual >= expected : actual === expected;
    assert.equal(passes, true, row.control_id);
    assert.equal(row.result_status, "PASS", row.control_id);
    assert.equal(row.first_failure_ref, null, row.control_id);
    assert.equal(row.value_authority, "VALIDATOR_PRODUCED", row.control_id);
  }
});

test("all executive metrics satisfy coverage and acceptable-null thresholds", async () => {
  const rows = await readRuntimeTable("mart_cfo_metric_readiness");
  assert.equal(rows.length, 11);
  for (const row of rows) {
    assert.ok(Number(row.period_count) >= Number(row.minimum_period_count), row.metric_id);
    assert.ok(Number(row.null_value_count) <= Number(row.acceptable_null_value_count), row.metric_id);
    assert.equal(row.readiness_status, "READY", row.metric_id);
    assert.equal(row.readiness_authority, "VALIDATOR_PRODUCED", row.metric_id);
  }
});

test("all package controls pass while remaining distinct from case-study findings", () => {
  assert.equal(snapshot.packageReconciliations.filter((row) => row.control_id.startsWith("C2-TABLE-")).length, 29);
  assert.equal(snapshot.packageReconciliations.every((row) => row.status === "PASS"), true);
  assert.equal(snapshot.packageReconciliations.every((row) => row.difference === 0), true);
  const component = readFileSync(resolve(webRoot, "app", "components", "finance", "AssuranceReadinessView.tsx"), "utf8");
  assert.match(component, /not an external-audit opinion/i);
  assert.match(component, /Separate from current C2 package readiness/);
  assert.match(component, /not counted as failures/i);
  assert.match(component, /Exception.*Finding.*Issue.*Remediation.*Readiness/s);
  assert.doesNotMatch(component, /audit opinion issued|controls effective in all material respects/i);
});

test("D5 route uses lazy read-only assurance queries and governed evidence links", () => {
  const route = readFileSync(resolve(webRoot, "app", "assurance", "page.tsx"), "utf8");
  const queries = readFileSync(resolve(webRoot, "app", "lib", "finance-runtime", "queries.ts"), "utf8");
  assert.match(route, /initialView="assurance"/);
  assert.match(queries, /loadAssuranceWorkspace/);
  for (const tableName of ["dim_reporting_version", "mart_cfo_metric_readiness", "mart_model_readiness_controls"]) {
    assert.match(queries, new RegExp(tableName));
  }
  assert.doesNotMatch(route, /create|approve|remediate|sign.?off/i);
});
