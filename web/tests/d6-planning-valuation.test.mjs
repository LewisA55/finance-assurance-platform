import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

const webRoot = resolve(import.meta.dirname, "..");
const publicData = resolve(webRoot, "public", "finance-data");
const manifest = JSON.parse(readFileSync(resolve(publicData, "runtime-manifest.json"), "utf8"));
const snapshot = JSON.parse(readFileSync(resolve(publicData, "latest-planning-valuation.json"), "utf8"));

const d6Populations = {
  dim_pythia_scenario: 3,
  fct_pythia_forecast_monthly: 360,
  mart_pythia_valuation: 3,
  mart_pythia_dcf_sensitivity: 75,
  mart_pythia_execution_controls: 10,
};

test("D6 admits the sealed Pythia authority without changing C2 actuals", () => {
  assert.equal(manifest.contractVersion, "q-finance-d6-runtime-manifest@v1");
  assert.equal(manifest.deliveryRef, "Q-FINANCE-C2@v1");
  assert.equal(manifest.pythiaRef, "PYTHIA-D6@v1");
  assert.equal(manifest.actualsReportingVersionRef, "RV-NEXUS-GROUP-2026-06@v1");
  assert.equal(manifest.pythiaControlCount, 10);
  assert.equal(manifest.runtimeTables.length, 24);
  const actual = Object.fromEntries(
    manifest.runtimeTables
      .filter((table) => Object.hasOwn(d6Populations, table.tableName))
      .map((table) => [table.tableName, table.expectedRows]),
  );
  assert.deepEqual(actual, d6Populations);
});

test("all D6 Parquet results are present as browser-local query inputs", () => {
  for (const tableName of Object.keys(d6Populations)) {
    const table = manifest.runtimeTables.find((row) => row.tableName === tableName);
    assert.equal(table.files.length, 1);
    assert.equal(existsSync(resolve(webRoot, "public", table.files[0].slice(1))), true);
  }
});

test("warm D6 snapshot preserves scenario approval boundaries", () => {
  assert.equal(snapshot.scenarios.length, 3);
  assert.equal(snapshot.annualForecasts.length, 33);
  assert.equal(Object.hasOwn(snapshot, "forecasts"), false);
  assert.ok(readFileSync(resolve(publicData, "latest-planning-valuation.json")).length < 100_000);
  assert.equal(snapshot.valuations.length, 3);
  assert.equal(snapshot.sensitivities.length, 75);
  assert.equal(snapshot.executionControls.length, 10);
  const base = snapshot.scenarios.find((row) => row.scenario_code === "BASE");
  assert.equal(base.scenario_approval_status, "APPROVED");
  assert.equal(base.scenario_locked_flag, true);
  assert.equal(base.pythia_result_status, "APPROVED_FORECAST_RESULT");
  assert.equal(base.finance_delivery_digest, manifest.deliveryDigest);
  assert.equal(
    snapshot.scenarios
      .filter((row) => row.scenario_code !== "BASE")
      .every((row) => row.pythia_result_status === "DRAFT_SCENARIO_RESULT"),
    true,
  );
});

test("every warm annual close balances while monthly authority remains queryable", () => {
  assert.equal(snapshot.annualForecasts.every((row) => row.balance_sheet_difference_minor === 0), true);
  assert.equal(snapshot.annualForecasts.every((row) => row.cash_rollforward_difference_minor === 0), true);
  assert.equal(snapshot.annualForecasts.every((row) => row.value_authority === "PYTHIA_GOVERNED_MODEL_RESULT"), true);
  assert.equal(d6Populations.fct_pythia_forecast_monthly, 360);
  assert.equal(snapshot.executionControls.every((row) => row.result_status === "PASS"), true);
});

test("Pythia exposes funding failure and withholds unsupported terminal values", () => {
  for (const row of snapshot.valuations) {
    assert.equal(row.valuation_status, "BLOCKED_NEGATIVE_TERMINAL_FCF");
    assert.equal(row.terminal_value_minor, null);
    assert.equal(row.present_value_terminal_minor, null);
    assert.equal(row.decision_status, "FUNDING_ACTION_REQUIRED");
    assert.ok(row.first_funding_gap_period);
    assert.ok(row.peak_funding_requirement_minor > 0);
  }
  assert.equal(snapshot.sensitivities.every((row) => row.valuation_status === "BLOCKED_NEGATIVE_TERMINAL_FCF"), true);
  assert.equal(snapshot.sensitivities.every((row) => row.enterprise_value_minor === null), true);
});

test("D6 route queries Pythia results and does not recreate model mechanics", () => {
  const route = readFileSync(resolve(webRoot, "app", "planning-valuation", "page.tsx"), "utf8");
  const queries = readFileSync(resolve(webRoot, "app", "lib", "finance-runtime", "queries.ts"), "utf8");
  const component = readFileSync(resolve(webRoot, "app", "components", "finance", "PlanningValuationView.tsx"), "utf8");
  assert.match(route, /initialView="planning-valuation"/);
  assert.match(queries, /loadPlanningValuationWorkspace/);
  assert.match(queries, /arg_max\(closing_cash_minor, period_id\)/);
  for (const tableName of Object.keys(d6Populations)) assert.match(queries, new RegExp(tableName));
  assert.match(component, /Terminal value withheld/);
  assert.match(component, /does not manufacture financing or a valuation/i);
  assert.doesNotMatch(component, /terminalValue\s*=|wacc\s*=|revolverDraw\s*=/i);
});
