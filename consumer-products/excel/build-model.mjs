import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";
import JSZip from "jszip";

const [deliveryDir, output, previewDir] = process.argv.slice(2);
assert.ok(deliveryDir && output?.endsWith(".xlsx") && previewDir, "Pass C2 directory, new workbook path, and preview directory.");
assert.equal(await fs.stat(output).then(() => true, (error) => {
  if (error.code !== "ENOENT") throw error;
  return false;
}), false, "Output already exists");

const deliveryRef = "Q-FINANCE-C2@v1";
const deliveryDigest = "sha256:7538132e08ea2b7e8c20f339db10e6c138cd2a08c71c4708c47c378d7c1b0141";
const scope = "NEXUS-GROUP";
const cutover = "2026-06";
const version = "RV-NEXUS-GROUP-2026-06@v1";
const cases = ["BASE", "BULL", "BEAR"];
const hash = (bytes) => `sha256:${createHash("sha256").update(bytes).digest("hex")}`;
const read = (name) => fs.readFile(path.join(deliveryDir, name));
const seal = await read("checksums.json");
assert.equal(hash(seal), deliveryDigest);
assert.equal((await read("finance-delivery.digest")).toString().trim(), deliveryDigest);
const inventory = JSON.parse(seal).files;
assert.equal(new Set(inventory.map(({ path }) => path)).size, inventory.length);
const authenticated = new Map();
for (const item of inventory) {
  const bytes = await read(item.path);
  assert.equal(bytes.length, item.byte_count, item.path);
  assert.equal(hash(bytes), item.sha256, item.path);
  if (item.path.startsWith("csv/") || item.path.endsWith(".json")) authenticated.set(item.path, bytes);
}
const manifest = JSON.parse(authenticated.get("delivery-manifest.json"));
assert.equal(manifest.delivery_ref, deliveryRef);
assert.equal(manifest.status, "PUBLISHED");
const controls = JSON.parse(authenticated.get("metadata/reconciliation.json")).rows;
assert.equal(controls.length, manifest.validation_control_count);
assert.ok(controls.every((row) => row.status === "PASS" && row.difference === 0));

function csv(table) {
  const spec = manifest.tables.find((item) => item.table_name === table);
  assert.ok(spec, table);
  const data = authenticated.get(spec.csv_path).toString("utf8");
  const records = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < data.length; i++) {
    const ch = data[i];
    if (ch === '"') {
      if (quoted && data[i + 1] === '"') {
        field += '"';
        i++;
      } else quoted = !quoted;
    } else if (!quoted && (ch === "," || ch === "\n")) {
      row.push(field === "\\N" ? null : field);
      field = "";
      if (ch === "\n") {
        records.push(row);
        row = [];
      }
    } else field += ch;
  }
  assert.ok(!quoted && row.length === 0 && field === "", `${table} CSV termination`);
  const keys = records.shift();
  assert.equal(records.length, spec.row_count, table);
  return records.map((values) => {
    assert.equal(values.length, keys.length, table);
    return Object.fromEntries(keys.map((key, index) => [key, values[index]]));
  });
}

function integer(row, key) {
  const value = row[key];
  assert.ok(/^-?\d+$/.test(value ?? "") && Number.isSafeInteger(Number(value)), `${key} at ${row.period_id}`);
  return Number(value);
}

function groupIndex(table) {
  const rows = csv(table).filter((row) => row.scope_id === scope);
  const indexed = new Map(rows.map((row) => [row.period_id, row]));
  assert.equal(indexed.size, 66, table);
  assert.equal(indexed.size, rows.length, table);
  return indexed;
}

const versions = groupIndex("dim_reporting_version");
const income = groupIndex("mart_financial_performance_monthly");
const balance = groupIndex("mart_balance_sheet_monthly");
const cash = groupIndex("mart_cash_flow_liquidity_monthly");
const equity = groupIndex("mart_tax_equity_monthly");
const actualPeriods = [...versions.keys()].sort();
assert.equal(actualPeriods[0], "2021-01");
assert.equal(actualPeriods.at(-1), cutover);
assert.equal(versions.get(cutover).reporting_version_ref, version);
const calendar = csv("dim_period").sort((a, b) => a.period_id.localeCompare(b.period_id));
const forecastPeriods = calendar.filter((row) => row.period_id > cutover).slice(0, 60).map((row) => row.period_id);
assert.equal(forecastPeriods.at(-1), "2031-06");
const dateByPeriod = new Map(calendar.map((row) => [row.period_id, row.month_end]));
const periods = [...actualPeriods, ...forecastPeriods];
for (let i = 0; i < periods.length; i++) {
  const date = new Date(Date.UTC(2021, i, 1));
  assert.equal(periods[i], date.toISOString().slice(0, 7));
}

for (const period of actualPeriods) {
  const authority = versions.get(period);
  const p = income.get(period);
  const b = balance.get(period);
  const c = cash.get(period);
  const e = equity.get(period);
  assert.equal(authority.close_status, "HARD_CLOSED");
  assert.ok([authority, p, b, c, e].every((row) => row.reporting_version_ref === authority.reporting_version_ref && row.reliability_status === "RELIABLE_FOR_STATUTORY_ACTUALS"));
  assert.ok([p, b, c, e].every((row) => row.currency === "GBP"));
  assert.equal(integer(b, "total_assets_minor"), integer(b, "total_liabilities_and_equity_minor"));
  assert.equal(integer(c, "closing_cash_minor"), integer(b, "cash_minor"));
  assert.equal(integer(c, "opening_cash_minor") + integer(c, "net_change_in_cash_minor"), integer(c, "closing_cash_minor"));
  assert.equal(integer(e, "net_income_minor"), integer(p, "net_income_minor"));
  assert.equal(integer(e, "closing_retained_earnings_minor"), integer(b, "retained_earnings_minor"));
}

const planLines = [
  ["Subscription revenue", "subscription_revenue"], ["Services revenue", "services_revenue"],
  ["Cost of revenue", "cost_of_revenue"], ["Research and development", "research_and_development"],
  ["Sales and marketing", "sales_and_marketing"], ["General and administrative", "general_and_administrative"],
];
const scenarios = new Map(csv("dim_planning_scenario").map((row) => [row.scenario_code, row]));
assert.equal(scenarios.size, cases.length);
const plan = new Map();
for (const row of csv("mart_model_planning_inputs")) {
  assert.ok(cases.includes(row.scenario_code));
  assert.equal(row.actuals_reporting_version_ref, version);
  assert.equal(row.actuals_scope_id, scope);
  assert.equal(row.currency, "GBP");
  assert.equal(row.is_governed_pythia_snapshot, "false");
  assert.equal(row.planning_scenario_ref, scenarios.get(row.scenario_code).planning_scenario_ref);
  const key = `${row.scenario_code}/${row.period_id}/${row.statement_line}`;
  plan.set(key, (plan.get(key) ?? 0) + integer(row, "forecast_amount_minor"));
}

const workbook = Workbook.create();
const overview = workbook.worksheets.add("Overview");
const control = workbook.worksheets.add("Control");
const assumptions = workbook.worksheets.add("Assumptions");
const statements = workbook.worksheets.add("Statements");
const checks = workbook.worksheets.add("Checks");
const actuals = workbook.worksheets.add("Actuals");
const planInputs = workbook.worksheets.add("Plan inputs");

const colors = { dark: "#163932", pale: "#E7F1EB", tan: "#FAF4E7", muted: "#56665F", green: "#087442", blue: "#174FB2", input: "#FFF2CF" };
const amount = '#,##0;(#,##0);"-"';
const currency = '"£"#,##0;("£"#,##0);"-"';
const pct = '0.0%;(0.0%);"-"';
const gap = '0.00;(0.00);0.00';
const values = (sheet, cell, value) => { sheet.getRange(cell).values = [[value]]; };
const formula = (sheet, cell, expression) => { sheet.getRange(cell).formulas = [[expression]]; };
function column(index) {
  let name = "";
  for (let n = index; n > 0; n = Math.floor((n - 1) / 26)) name = String.fromCharCode(65 + (n - 1) % 26) + name;
  return name;
}
const start = 4;
const col = (index) => column(start + index);
const endActual = col(actualPeriods.length - 1);
const firstForecast = col(actualPeriods.length);
const endForecast = col(periods.length - 1);
const planEnd = col(forecastPeriods.length - 1);
const excelDate = (period) => Date.parse(`${dateByPeriod.get(period)}T00:00:00Z`) / 86_400_000 + 25_569;
const caseSelector = "'Control'!$D$5";

function setup(sheet, title, lastColumn, lastRow, labelWidth = 290, firstColumn = "C") {
  sheet.showGridLines = false;
  sheet.getRange(`${firstColumn}2:${lastColumn}${lastRow}`).format.font = { name: "Arial", size: 10, color: "#162822" };
  sheet.getRange(`${firstColumn}2:${lastColumn}${lastRow}`).format.verticalAlignment = "center";
  if (firstColumn === "C") sheet.getRange("A1:B2").format.columnWidthPx = 13;
  sheet.getRange(`${firstColumn}2`).format.columnWidthPx = labelWidth;
  sheet.getRange(`D2:${lastColumn}2`).format.columnWidthPx = 108;
  values(sheet, `${firstColumn}2`, title);
  sheet.getRange(`${firstColumn}2`).format.font = { name: "Arial", size: 15, bold: true, color: colors.dark };
  sheet.getRange(`${firstColumn}2`).format.rowHeightPx = 27;
  sheet.getRange(`${firstColumn}2:${lastColumn}2`).format.borders = { bottom: { color: "#ABC6B8", style: "thin" } };
}

function band(sheet, row, label, last = endForecast, first = "C") {
  values(sheet, `${first}${row}`, label);
  sheet.getRange(`${first}${row}:${last}${row}`).format = {
    fill: colors.dark,
    font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
    rowHeightPx: 20,
  };
}

function dates(sheet, row, keys, last, index = 0) {
  sheet.getRange(`${col(index)}${row}:${last}${row}`).values = [keys.map(excelDate)];
  sheet.getRange(`${col(index)}${row}:${last}${row}`).setNumberFormat("mmm-yy");
  sheet.getRange(`${col(index)}${row}:${last}${row}`).format.horizontalAlignment = "center";
}

function caseLink(sheet, row) {
  values(sheet, `C${row}`, "Case selected");
  formula(sheet, `D${row}`, "='Control'!$E$5");
  sheet.getRange(`D${row}`).format.font.color = colors.green;
  sheet.getRange(`D${row}`).format.horizontalAlignment = "center";
  sheet.getRange(`D${row}`).format.borders = { preset: "outside", style: "dotted", color: colors.green };
}

const jumps = new Map();
function jump(sheet, cell, targetSheet, targetCell, label) {
  values(sheet, cell, label);
  sheet.getRange(cell).format.font = { name: "Arial", size: 10, color: colors.green, underline: "single" };
  if (!jumps.has(sheet.name)) jumps.set(sheet.name, []);
  jumps.get(sheet.name).push({ cell, targetSheet, targetCell, label });
}

setup(control, "Model control", "E", 32, 230);
control.tabColor = "#3F7866";
control.getRange("D2").format.columnWidthPx = 335;
control.getRange("E2").format.columnWidthPx = 305;
band(control, 4, "Scenario and valuation", "E");
values(control, "C5", "Case (1 Base, 2 Bull, 3 Bear)");
values(control, "D5", 1);
formula(control, "E5", '=CHOOSE(D5,"BASE","BULL","BEAR")');
control.getRange("D5").dataValidation = { rule: { type: "list", values: ["1", "2", "3"] } };
control.getRange("D5").format.fill = colors.input;
control.getRange("D5").format.horizontalAlignment = "left";
control.getRange("D5").format.font.color = colors.blue;
control.getRange("E5").format.font.bold = true;
values(control, "C6", "C2 planning input approval");
const approvalLabels = { APPROVED_AND_LOCKED_PLANNING_INPUT: "Approved and locked C2 input", DRAFT_PLANNING_INPUT: "Draft C2 input" };
const approvalStates = cases.map((code) => approvalLabels[scenarios.get(code).planning_input_status]);
assert.ok(approvalStates.every(Boolean));
formula(control, "D6", `=CHOOSE(D5,${approvalStates.map((label) => `"${label}"`).join(",")})`);
values(control, "C7", "Workbook valuation status");
formula(control, "D7", "='Overview'!D21");
jump(control, "E7", "Overview", "C20", "Open the DCF");
control.getRange("D7").conditionalFormats.addCustom('=$D$7<>"Indicative value"', {
  fill: "#FBE9E7", font: { color: "#9E2B21", bold: true },
});

band(control, 9, "Reporting basis", "E");
control.getRange("C10:D14").values = [
  ["Workbook review version", "0.2.1"], ["C2 package", deliveryRef], ["C2 detached SHA-256", deliveryDigest],
  ["Actuals at cutover", version], ["Scope and currency", `${scope} (GBP)`],
];
control.getRange("D12:E12").format.font.size = 9;
values(control, "C15", "Forecast month-ends");
control.getRange("D15:E15").values = [[excelDate(forecastPeriods[0]), excelDate(forecastPeriods.at(-1))]];
control.getRange("D15:E15").setNumberFormat("dd mmm yyyy");
control.getRange("D15:E15").format.horizontalAlignment = "left";

band(control, 17, "Jump to", "E");
jump(control, "C18", "Assumptions", "C6", "Scenario drivers");
jump(control, "D18", "Assumptions", "D78", "Monthly revenue adjustments");
jump(control, "E18", "Checks", "C6", "Reconciliation summary");
jump(control, "E19", "Overview", "C20", "Discounted cash flow");

band(control, 21, "Model map", "E");
control.getRange("C22:E22").values = [["Tab", "What it owns", "Feeds"]];
control.getRange("C22:E22").format.fill = colors.pale;
control.getRange("C22:E22").format.font.bold = true;
const modelMap = [
  ["Overview", "Annual results, DCF and valuation eligibility", "Reader review"],
  ["Control", "Case selection, reporting basis and navigation", "Assumptions. Displays valuation status."],
  ["Assumptions", "Editable drivers and the selected C2 plan", "Statements and DCF"],
  ["Statements", "Monthly statements, schedules and cash-flow discounting", "Overview and Checks"],
  ["Checks", "Independent monthly reconciliations", "Reviewer diagnostics"],
  ["Actuals", "Published group statements in GBP minor units", "Statements and Checks"],
  ["Plan inputs", "C2 plan totals by case, month and statement line", "Assumptions"],
];
for (const [i, [tab, owner, feeds]] of modelMap.entries()) {
  const row = 23 + i;
  jump(control, `C${row}`, tab, "C2", tab);
  control.getRange(`D${row}:E${row}`).values = [[owner, feeds]];
}
control.getRange("D23:E29").format.wrapText = true;
control.getRange("C23:E29").format.rowHeightPx = 32;

const actualFields = {
  subscription: [income, "subscription_revenue_minor"], services: [income, "services_revenue_minor"],
  revenue: [income, "revenue_minor"], cogs: [income, "cost_of_revenue_minor"], gross: [income, "gross_profit_minor"],
  rd: [income, "research_and_development_minor"], sales: [income, "sales_and_marketing_minor"],
  admin: [income, "general_and_administrative_minor"], da: [income, "depreciation_and_amortisation_minor"],
  ebitda: [income, "ebitda_minor"], ebit: [income, "operating_profit_minor"], interest: [income, "interest_expense_minor"],
  pbt: [income, "profit_before_tax_minor"], tax: [income, "income_tax_expense_minor"], netIncome: [income, "net_income_minor"],
  cash: [balance, "cash_minor"], ar: [balance, "accounts_receivable_minor"], prepay: [balance, "prepayments_minor"],
  ppe: [balance, "net_property_plant_equipment_minor"], inventory: [balance, "inventory_minor"],
  intercoAR: [balance, "intercompany_receivables_minor"], dta: [balance, "deferred_tax_asset_minor"], goodwill: [balance, "goodwill_minor"],
  intangibles: [balance, "net_intangible_assets_minor"], rou: [balance, "net_right_of_use_assets_minor"],
  assets: [balance, "total_assets_minor"], ap: [balance, "accounts_payable_minor"],
  defRev: [balance, "deferred_revenue_minor"], accruals: [balance, "accrued_expenses_minor"],
  debt: [balance, "long_term_debt_minor"], leases: [balance, "lease_liabilities_minor"],
  intercoAP: [balance, "intercompany_payables_minor"], unapplied: [balance, "unapplied_cash_minor"],
  taxPayable: [balance, "tax_payable_minor"], liabilities: [balance, "total_liabilities_minor"],
  shareCapital: [balance, "share_capital_minor"], retained: [balance, "retained_earnings_minor"],
  equity: [balance, "total_equity_minor"], le: [balance, "total_liabilities_and_equity_minor"],
  openingCash: [cash, "opening_cash_minor"], ocf: [cash, "operating_cash_flow_minor"],
  icf: [cash, "investing_cash_flow_minor"], fcf: [cash, "financing_cash_flow_minor"],
  fx: [cash, "fx_and_other_movement_minor"], netCash: [cash, "net_change_in_cash_minor"], closingCash: [cash, "closing_cash_minor"],
  facility: [cash, "undrawn_facility_minor"], openingRetained: [equity, "opening_retained_earnings_minor"],
  dividends: [equity, "dividends_minor"], otherEquity: [equity, "other_equity_movements_minor"],
};
const actualRow = Object.fromEntries(Object.keys(actualFields).map((key, i) => [key, i + 9]));
const dataEndRow = 8 + Object.keys(actualFields).length;
setup(actuals, "Published group actuals", endActual, dataEndRow, 310);
actuals.tabColor = colors.tan;
values(actuals, "C3", "GBP minor units. Source values are unscaled and formula-free.");
values(actuals, "C4", `${deliveryRef} ${deliveryDigest}`);
values(actuals, "C5", "C2 datasets QF-D05, QF-D79, QF-D80, QF-D81 and QF-D89");
band(actuals, 6, "Group reporting periods", endActual);
dates(actuals, 6, actualPeriods, endActual);
values(actuals, "C7", "Reporting version");
actuals.getRange(`D7:${endActual}7`).values = [actualPeriods.map((period) => versions.get(period).reporting_version_ref)];
actuals.getRange(`D7:${endActual}7`).format.columnWidthPx = 204;
for (const [key, [rows, field]] of Object.entries(actualFields)) {
  const row = actualRow[key];
  values(actuals, `C${row}`, field);
  actuals.getRange(`D${row}:${endActual}${row}`).values = [actualPeriods.map((period) => integer(rows.get(period), field))];
}
actuals.getRange(`D9:${endActual}${dataEndRow}`).setNumberFormat(amount);
actuals.freezePanes.freezeRows(7);

setup(planInputs, "C2 planning inputs", planEnd, 27);
values(planInputs, "C3", "GBP minor units. Source plan lines summed by case, month and statement line.");
values(planInputs, "C4", "C2 datasets QF-D98 and QF-D74. Forecast version RF-2026-06@v1.");
band(planInputs, 6, "Forecast period", planEnd);
dates(planInputs, 6, forecastPeriods, planEnd);
const planRow = new Map();
for (const [caseIndex, code] of cases.entries()) {
  const firstRow = 8 + caseIndex * 7;
  values(planInputs, `C${firstRow - 1}`, `${code}: ${scenarios.get(code).planning_input_status}`);
  for (const [index, [label, field]] of planLines.entries()) {
    const row = firstRow + index;
    planRow.set(`${code}/${field}`, row);
    values(planInputs, `C${row}`, label);
    planInputs.getRange(`D${row}:${planEnd}${row}`).values = [forecastPeriods.map((period) => {
      const key = `${code}/${period}/${field}`;
      assert.ok(plan.has(key), key);
      return plan.get(key);
    })];
  }
}
planInputs.getRange(`D8:${planEnd}27`).setNumberFormat(amount);
planInputs.freezePanes.freezeRows(6);

const drivers = [
  ["wacc", "Annual WACC", [.095, .09, .105], pct],
  ["growth", "Terminal growth", [.025, .03, .015], pct],
  ["tax", "Cash tax rate", [.25, .25, .25], pct],
  ["interest", "Annual cost of debt", [.07, .0675, .075], pct],
  ["capex", "Cash capex / revenue", [.06, .075, .045], pct],
  ["dso", "Receivable days", [85, 78, 105], amount],
  ["dpo", "Payable days on cash costs", [120, 105, 145], amount],
  ["defRev", "Deferred revenue / monthly revenue", [.7757, .82, .70], pct],
  ["prepay", "Prepayments / cash costs", [.05, .05, .045], pct],
  ["accruals", "Accruals / cash costs", [.03, .03, .025], pct],
  ["rd", "R&D ceiling / revenue", [2, .18, 2], pct],
  ["sales", "Sales and marketing ceiling / revenue", [2, .25, 2], pct],
  ["admin", "G&A ceiling / revenue", [2, .12, 2], pct],
];
const driverRows = Object.fromEntries(drivers.map(([key], i) => [key, 8 + i * 4]));
const planDriverStart = 71;
setup(assumptions, "Scenario assumptions", planEnd, 96, 310);
caseLink(assumptions, 4);
jump(assumptions, "E4", "Control", "D5", "Change case");
values(assumptions, "C5", "Blue cells are editable. Forecast outputs are local workbook analysis.");
band(assumptions, 6, "Case drivers", "D");
values(assumptions, "E6", "Defaults follow Pythia D6 case conventions.");
for (const [key, label, options, format] of drivers) {
  const row = driverRows[key];
  values(assumptions, `C${row}`, label);
  assumptions.getRange(`C${row + 1}:D${row + 3}`).values = cases.map((name, i) => [name, options[i]]);
  const optionsRefs = [1, 2, 3].map((i) => `D${row + i}`);
  formula(assumptions, `D${row}`, `=IF(CHOOSE(${caseSelector},${optionsRefs.map((ref) => `ISNUMBER(${ref})`).join(",")}),CHOOSE(${caseSelector},${optionsRefs.join(",")}),NA())`);
  assumptions.getRange(`C${row}:D${row}`).format.fill = colors.pale;
  assumptions.getRange(`C${row}:D${row}`).format.font.bold = true;
  assumptions.getRange(`D${row + 1}:D${row + 3}`).format.font.color = colors.blue;
  assumptions.getRange(`D${row}:D${row + 3}`).setNumberFormat(format);
}
band(assumptions, 61, "Financing and forecast conventions", "D");
assumptions.getRange("C62:D67").values = [
  ["Minimum cash (GBP)", 1_000_000], ["Monthly term debt repayment (GBP)", 750_000],
  ["Opening PPE depreciation months", 36], ["New capex depreciation months", 60],
  ["Operating cost transition months", 36], ["Working capital month (days)", 30],
];
assumptions.getRange("D62:D67").format.font.color = colors.blue;
assumptions.getRange("D62:D67").setNumberFormat(amount);
assumptions.getRange("D62:D63").dataValidation = { rule: { type: "whole", operator: "between", formula1: 0, formula2: 1000000000 } };
assumptions.getRange("D64:D67").dataValidation = { rule: { type: "whole", operator: "between", formula1: 1, formula2: 120 } };
band(assumptions, 69, "Active monthly C2 plan (GBP)", planEnd);
dates(assumptions, 69, forecastPeriods, planEnd);
for (const [i, [label, field]] of planLines.entries()) {
  const row = planDriverStart + i;
  values(assumptions, `C${row}`, label);
  assumptions.getRange(`D${row}:${planEnd}${row}`).formulas = [forecastPeriods.map((_, period) =>
    `=CHOOSE(${caseSelector},${cases.map((code) => `'Plan inputs'!${col(period)}${planRow.get(`${code}/${field}`)}`).join(",")})/100`)];
}
assumptions.getRange(`D${planDriverStart}:${planEnd}${planDriverStart + 5}`).setNumberFormat(amount);
assumptions.getRange(`D${planDriverStart}:${planEnd}${planDriverStart + 5}`).format.font.color = colors.green;
values(assumptions, "C78", "Monthly revenue adjustment vs C2 plan");
assumptions.getRange(`D78:${planEnd}78`).values = [forecastPeriods.map(() => 0)];
assumptions.getRange(`D78:${planEnd}78`).setNumberFormat(pct);
assumptions.getRange(`D78:${planEnd}78`).format.font.color = colors.blue;
assumptions.getRange(`D78:${planEnd}78`).dataValidation = { rule: { type: "decimal", operator: "between", formula1: -1, formula2: 10 } };
values(assumptions, "C80", "The monthly adjustment applies to subscription and services revenue in the selected case.");

const lines = {
  subscription: [9, "Subscription revenue"], services: [10, "Services revenue"], revenue: [11, "Revenue"],
  cogs: [12, "Cost of revenue"], gross: [13, "Gross profit"], rd: [14, "Research and development"],
  sales: [15, "Sales and marketing"], admin: [16, "General and administrative"], ebitda: [17, "EBITDA"],
  da: [18, "Depreciation and amortisation"], ebit: [19, "Operating profit"], interest: [20, "Interest expense"],
  pbt: [21, "Profit before tax"], tax: [22, "Income tax expense or credit"], netIncome: [23, "Net income"],
  cash: [27, "Cash"], ar: [28, "Accounts receivable"], prepay: [29, "Prepayments"], ppe: [30, "Net property, plant and equipment"],
  otherAssets: [31, "Other assets held at cutover"], assets: [32, "Total assets"], ap: [33, "Accounts payable"],
  defRev: [34, "Deferred revenue"], accruals: [35, "Accrued expenses"], debt: [36, "Term debt"],
  revolver: [37, "Revolver drawn"], leases: [38, "Lease liabilities"], otherLiabilities: [39, "Other liabilities held at cutover"],
  liabilities: [40, "Total liabilities"], shareCapital: [41, "Share capital"], retained: [42, "Retained earnings"],
  equity: [43, "Total equity"], le: [44, "Total liabilities and equity"], openingCash: [48, "Opening cash"],
  ocf: [49, "Operating cash flow"], icf: [50, "Investing cash flow"], fcf: [51, "Financing cash flow"],
  fx: [52, "FX and other cash effects"], netCash: [53, "Net change in cash"], closingCash: [54, "Closing cash"],
  wc: [58, "Operating working capital"], wcChange: [59, "Increase in operating working capital"],
  capex: [60, "Cash capex"], openingPpeDa: [61, "Depreciation on opening PPE"], newPpeDa: [62, "Depreciation on forecast capex"],
  principal: [63, "Term debt repaid"], draw: [64, "Revolver draw"], undrawn: [65, "Undrawn revolver"],
  fundingGap: [66, "Funding gap to cash floor"], nopat: [70, "Operating profit after cash tax"],
  uf: [71, "Unlevered free cash flow"], discount: [72, "Month-end discount factor"], pv: [73, "PV of unlevered free cash flow"],
};
const s = (c, key) => `${c}${lines[key][0]}`;
const a = (c, key) => `'Actuals'!${c}${actualRow[key]}/100`;
const d = (key) => `'Assumptions'!$D$${driverRows[key]}`;
const fixed = (row) => `'Assumptions'!$D$${row}`;
setup(statements, "Integrated financial statements", endForecast, 73);
caseLink(statements, 4);
jump(control, "C19", "Statements", s(endActual, "revenue"), "June 2026 actuals");
jump(control, "D19", "Statements", s(firstForecast, "revenue"), "July 2026 forecast");
jump(statements, "E4", "Control", "D5", "Control");
jump(statements, "F4", "Statements", s(endActual, "revenue"), "Jun-26 actuals");
jump(statements, "G4", "Statements", s(firstForecast, "revenue"), "Jul-26 forecast");
values(statements, "C3", "Nexus Group. GBP. Actuals through June 2026, followed by 60 forecast months.");
band(statements, 6, "Monthly reporting periods");
dates(statements, 6, periods, endForecast);
statements.getRange(`${firstForecast}6:${endForecast}6`).format.fill = "#357861";
values(statements, "D7", "Actuals");
values(statements, `${firstForecast}7`, "Forecast");
for (const [row, label] of [[8, "Income statement"], [26, "Balance sheet"], [47, "Cash flow statement"], [57, "Operating and funding schedules"], [69, "Discounted cash flow"]]) band(statements, row, label);
statements.freezePanes.freezeRows(7);
statements.freezePanes.freezeColumns(3);
const statementFormulas = new Map(Object.entries(lines).map(([key]) => [key, []]));
for (const [i] of periods.entries()) {
  const c = col(i);
  const p = col(i - 1);
  const current = (key) => s(c, key);
  const prior = (key) => s(p, key);
  let f;
  if (i < actualPeriods.length) {
    f = Object.fromEntries(Object.keys(lines).filter((key) => actualFields[key]).map((key) => [key, a(c, key)]));
    f.otherAssets = ["inventory", "intercoAR", "dta", "goodwill", "intangibles", "rou"].map((key) => a(c, key)).join("+");
    f.otherLiabilities = ["intercoAP", "unapplied", "taxPayable"].map((key) => a(c, key)).join("+");
    f.undrawn = a(c, "facility");
    f.wc = `${current("ar")}+${current("prepay")}-${current("ap")}-${current("defRev")}-${current("accruals")}`;
    if (i > 0) f.wcChange = `${current("wc")}-${prior("wc")}`;
  } else {
    const month = i - actualPeriods.length + 1;
    const planCol = col(month - 1);
    const input = (line) => `'Assumptions'!${planCol}${planDriverStart + line}`;
    const opCost = (line, key) => `-${input(line)}+(MAX(${input(line)}-${current("revenue")}*${d(key)},0)*MIN(${month}/${fixed(66)},1))`;
    f = {
      subscription: `${input(0)}*(1+'Assumptions'!${planCol}78)`,
      services: `${input(1)}*(1+'Assumptions'!${planCol}78)`, revenue: `SUM(${current("subscription")}:${current("services")})`,
      cogs: `-${input(2)}`, gross: `${current("revenue")}+${current("cogs")}`,
      rd: opCost(3, "rd"), sales: opCost(4, "sales"), admin: opCost(5, "admin"),
      ebitda: `SUM(${current("gross")}:${current("admin")})`,
      da: `-MIN(${prior("ppe")}+${current("capex")},${current("openingPpeDa")}+${current("newPpeDa")})`,
      ebit: `${current("ebitda")}+${current("da")}`,
      interest: `-SUM(${prior("debt")},${month === 1 ? "0" : prior("revolver")},${prior("leases")})*${d("interest")}/12`,
      pbt: `${current("ebit")}+${current("interest")}`, tax: `-MAX(${current("pbt")},0)*${d("tax")}`,
      netIncome: `${current("pbt")}+${current("tax")}`, cash: current("closingCash"),
      ar: `${current("revenue")}*${d("dso")}/${fixed(67)}`,
      prepay: `(${current("revenue")}-${current("ebitda")})*${d("prepay")}`,
      ppe: `${prior("ppe")}+${current("capex")}+${current("da")}`, otherAssets: prior("otherAssets"),
      assets: `SUM(${current("cash")}:${current("otherAssets")})`,
      ap: `(${current("revenue")}-${current("ebitda")})*${d("dpo")}/${fixed(67)}`,
      defRev: `${current("revenue")}*${d("defRev")}`, accruals: `(${current("revenue")}-${current("ebitda")})*${d("accruals")}`,
      debt: `${prior("debt")}-${current("principal")}`, revolver: `${month === 1 ? "0" : prior("revolver")}+${current("draw")}`,
      leases: prior("leases"), otherLiabilities: prior("otherLiabilities"),
      liabilities: `SUM(${current("ap")}:${current("otherLiabilities")})`, shareCapital: prior("shareCapital"),
      retained: `${prior("retained")}+${current("netIncome")}`, equity: `SUM(${current("shareCapital")}:${current("retained")})`,
      le: `${current("liabilities")}+${current("equity")}`, openingCash: prior("closingCash"),
      ocf: `${current("netIncome")}-${current("da")}-${current("wcChange")}`, icf: `-${current("capex")}`,
      fcf: `${current("draw")}-${current("principal")}`, fx: "0",
      netCash: `SUM(${current("ocf")}:${current("fx")})`, closingCash: `${current("openingCash")}+${current("netCash")}`,
      wc: `${current("ar")}+${current("prepay")}-${current("ap")}-${current("defRev")}-${current("accruals")}`,
      wcChange: `${current("wc")}-${prior("wc")}`, capex: `${current("revenue")}*${d("capex")}`,
      openingPpeDa: `IF(${month}<=${fixed(64)},$${endActual}$${lines.ppe[0]}/${fixed(64)},0)`,
      newPpeDa: month === 1 ? "0" : `SUM(INDEX($${firstForecast}$60:${p}60,1,MAX(1,${month}-${fixed(65)})):${p}60)/${fixed(65)}`,
      principal: `MIN(${prior("debt")},${fixed(63)})`,
      draw: `MIN(MAX(${fixed(62)}-(${current("openingCash")}+${current("ocf")}+${current("icf")}-${current("principal")}),0),${prior("undrawn")})`,
      undrawn: `${prior("undrawn")}-${current("draw")}`, fundingGap: `MAX(ROUND(${fixed(62)}-${current("cash")},2),0)`,
      nopat: `${current("ebit")}-MAX(${current("ebit")},0)*${d("tax")}`,
      uf: `${current("nopat")}-${current("da")}-${current("capex")}-${current("wcChange")}`,
      discount: `1/(1+${d("wacc")})^(${month}/12)`, pv: `${current("uf")}*${current("discount")}`,
    };
  }
  for (const [key, expressions] of statementFormulas) expressions.push(f[key] === undefined ? null : `=${f[key]}`);
}
statements.getRange(`D9:${endForecast}73`).setNumberFormat(amount);
for (const [key, [row, label]] of Object.entries(lines)) {
  values(statements, `C${row}`, label);
  statements.getRange(`D${row}:${endForecast}${row}`).formulas = [statementFormulas.get(key)];
  if (actualFields[key] || ["undrawn", "otherAssets", "otherLiabilities"].includes(key)) statements.getRange(`D${row}:${endActual}${row}`).format.font.color = colors.green;
  if (["subscription", "services", "cogs"].includes(key)) statements.getRange(`${firstForecast}${row}:${endForecast}${row}`).format.font.color = colors.green;
}
for (const key of ["revenue", "gross", "ebitda", "ebit", "netIncome", "assets", "liabilities", "equity", "le", "closingCash", "fundingGap", "uf", "pv"]) {
  const row = lines[key][0];
  statements.getRange(`C${row}:${endForecast}${row}`).format.fill = colors.pale;
  statements.getRange(`C${row}:${endForecast}${row}`).format.font.bold = true;
  statements.getRange(`D${row}:${endForecast}${row}`).setNumberFormat(currency);
}
statements.getRange(`${firstForecast}72:${endForecast}72`).setNumberFormat("0.0000");

const sh = (c, key) => `'Statements'!${s(c, key)}`;
const sumStatement = (first, last, key) => `SUM(${sh(first, key)}:${s(last, key)})`;
setup(overview, "Nexus Technologies financial model", "I", 39, 315);
overview.tabColor = colors.dark;
values(overview, "C3", "Group reporting in GBP. Actuals through June 2026. Forecast years end in June.");
caseLink(overview, 4);
jump(overview, "E4", "Control", "D5", "Model control");
jump(overview, "F4", "Overview", "C20", "DCF");
band(overview, 6, "Financial summary (GBP)", "I");
overview.getRange("D6:I6").values = [["LTM Jun 2026", "Jun 2027", "Jun 2028", "Jun 2029", "Jun 2030", "Jun 2031"]];
overview.getRange("D6:I6").format.horizontalAlignment = "center";
const outputRows = [
  ["Revenue", "revenue", true], ["EBITDA", "ebitda", true], ["Operating profit", "ebit", true],
  ["Net income", "netIncome", true], ["Total assets", "assets", false], ["Total liabilities and equity", "le", false],
  ["Operating cash flow", "ocf", true], ["Investing cash flow", "icf", true], ["Financing cash flow", "fcf", true],
  ["Closing cash", "closingCash", false], ["Unlevered free cash flow", "uf", true], ["Peak funding gap to cash floor", "fundingGap", false],
];
const yearColumns = Array.from({ length: 6 }, (_, i) => {
  const end = actualPeriods.length - 1 + 12 * i;
  return [col(end - 11), col(end)];
});
for (const [i, [label, key, flow]] of outputRows.entries()) {
  const row = 7 + i;
  values(overview, `C${row}`, label);
  overview.getRange(`D${row}:I${row}`).formulas = [yearColumns.map(([first, last], j) => {
    if (j === 0 && ["uf", "fundingGap"].includes(key)) return null;
    if (key === "fundingGap") return `=MAX(${sh(first, key)}:${s(last, key)})`;
    return `=${flow ? sumStatement(first, last, key) : sh(last, key)}`;
  })];
}
values(overview, "D17", "n.a.");
values(overview, "D18", "n.a.");
overview.getRange("D7:I18").setNumberFormat(amount);
for (const row of [7, 8, 16, 17, 18]) {
  overview.getRange(`C${row}:I${row}`).format.fill = colors.pale;
  overview.getRange(`C${row}:I${row}`).format.font.bold = true;
  overview.getRange(`D${row}:I${row}`).setNumberFormat(currency);
}

band(overview, 20, "Discounted cash flow (GBP)", "I");
const dcf = [
  ["Valuation status", '=IF(D22<=D23,"WACC must exceed growth",IF(D24<=0,"Non-positive terminal cash flow",IF(D25>0.01,"Unfunded cash floor","Indicative value")))'],
  ["Annual WACC", `=${d("wacc")}`],
  ["Terminal growth", `=${d("growth")}`],
  ["Final 12 months unlevered cash flow", `=${sumStatement(yearColumns.at(-1)[0], endForecast, "uf")}`],
  ["Peak funding gap", `=MAX(${sh(firstForecast, "fundingGap")}:${s(endForecast, "fundingGap")})`],
  ["PV of 60 monthly cash flows", `=${sumStatement(firstForecast, endForecast, "pv")}`],
  ["Terminal value at month 60", '=IF(D21="Indicative value",D24*(1+D23)/(D22-D23),"")'],
  ["PV of terminal value", `=IF(D21="Indicative value",D27*${sh(endForecast, "discount")},"")`],
  ["Enterprise value", '=IF(D21="Indicative value",D26+D28,"")'],
  ["Cutover cash", `=${sh(endActual, "cash")}`],
  ["Cutover term debt", `=-${sh(endActual, "debt")}`],
  ["Cutover lease liabilities", `=-${sh(endActual, "leases")}`],
  ["Equity value", '=IF(D21="Indicative value",SUM(D29:D32),"")'],
];
for (const [i, [label, expression]] of dcf.entries()) {
  values(overview, `C${21 + i}`, label);
  formula(overview, `D${21 + i}`, expression);
}
overview.getRange("D21:F21").merge();
overview.getRange("D21:F21").format.font.bold = true;
overview.getRange("D22:D23").setNumberFormat(pct);
overview.getRange("D24:D33").setNumberFormat(currency);
for (const row of [29, 33]) {
  overview.getRange(`C${row}:D${row}`).format.fill = colors.pale;
  overview.getRange(`C${row}:D${row}`).format.font.bold = true;
}
overview.getRange("D21:F21").conditionalFormats.addCustom('=$D$21<>"Indicative value"', {
  fill: "#FBE9E7", font: { color: "#9E2B21", bold: true },
});
values(overview, "C35", "Valuation date 30 June 2026. Month-end discounting and perpetual growth terminal value.");
values(overview, "C36", "Select the case on Control. Statements shows the forecast by month and Checks shows reconciliations.");
values(overview, "C37", "Forecast assumes no new equity or dividends. Existing leases and other non-operating balances carry forward.");
values(overview, "C38", "Negative forecast cash after the facility is exhausted represents unmet financing needs.");

setup(checks, "Financial reconciliations", endForecast, 28, 315);
caseLink(checks, 4);
jump(checks, "E4", "Control", "D5", "Control");
values(checks, "C3", "GBP differences. Review differences greater than £0.01 in absolute value.");
band(checks, 6, "Reconciliation summary", "D");
checks.getRange("C7:C10").values = [["Failed reconciliation cells"], ["Largest absolute difference (GBP)"], ["First failed month"], ["Missing numeric results"]];
band(checks, 12, "Monthly reporting periods");
dates(checks, 12, periods, endForecast);
checks.getRange(`${firstForecast}12:${endForecast}12`).format.fill = "#357861";
const checkLines = [
  ["Assets less liabilities and equity", (c) => `${sh(c, "assets")}-${sh(c, "liabilities")}-${sh(c, "equity")}`],
  ["Balance sheet cash less cash-flow closing cash", (c) => `${sh(c, "cash")}-${sh(c, "closingCash")}`],
  ["Closing cash less opening cash and net flows", (c) => `${sh(c, "closingCash")}-${sh(c, "openingCash")}-${sh(c, "ocf")}-${sh(c, "icf")}-${sh(c, "fcf")}-${sh(c, "fx")}`],
  ["Retained earnings roll-forward difference", (c, p, forecast) => forecast
    ? `${sh(c, "retained")}-${sh(p, "retained")}-${sh(c, "netIncome")}`
    : `${sh(c, "retained")}-${a(c, "openingRetained")}-${sh(c, "netIncome")}+${a(c, "dividends")}-${a(c, "otherEquity")}`],
  ["Net PPE roll-forward difference", (c, p, forecast) => forecast ? `${sh(c, "ppe")}-${sh(p, "ppe")}-${sh(c, "capex")}-${sh(c, "da")}` : null],
  ["Term debt roll-forward difference", (c, p, forecast) => forecast ? `${sh(c, "debt")}-${sh(p, "debt")}+${sh(c, "principal")}` : null],
  ["Revolver capacity difference", (c, p, forecast) => forecast ? `${sh(c, "revolver")}+${sh(c, "undrawn")}-${a(endActual, "facility")}` : null],
  ["Revenue less C2 statement value", (c, p, forecast) => forecast ? null : `${sh(c, "subscription")}+${sh(c, "services")}-${a(c, "revenue")}`],
  ["Net income less C2 statement value", (c, p, forecast) => forecast ? null : `${sh(c, "ebit")}+${sh(c, "interest")}+${sh(c, "tax")}-${a(c, "netIncome")}`],
  ["Total assets less component balances", (c) => `${sh(c, "assets")}-SUM(${sh(c, "cash")}:${s(c, "otherAssets")})`],
  ["Total liabilities less component balances", (c) => `${sh(c, "liabilities")}-SUM(${sh(c, "ap")}:${s(c, "otherLiabilities")})`],
];
const firstCheckRow = 14;
const lastCheckRow = firstCheckRow + checkLines.length - 1;
for (const [i, [label, expression]] of checkLines.entries()) {
  const row = firstCheckRow + i;
  values(checks, `C${row}`, label);
  checks.getRange(`D${row}:${endForecast}${row}`).formulas = [periods.map((_, j) => {
    const result = expression(col(j), col(j - 1), j >= actualPeriods.length);
    return result === null ? null : `=ROUND(${result},2)`;
  })];
}
const checkRange = checks.getRange(`D${firstCheckRow}:${endForecast}${lastCheckRow}`);
checkRange.setNumberFormat(gap);
const errorFormat = { fill: "#FBE9E7", font: { color: "#9E2B21", bold: true } };
checkRange.conditionalFormats.addCustom(`=ABS(D${firstCheckRow})>0.01`, errorFormat);
const detail = `D${firstCheckRow}:${endForecast}${lastCheckRow}`;
const perPeriod = periods.map((_, i) => {
  const c = col(i);
  const range = `${c}${firstCheckRow}:${c}${lastCheckRow}`;
  const expected = checkLines.filter(([, f]) => f(c, col(i - 1), i >= actualPeriods.length) !== null).length;
  return [
    `=COUNTIF(${range},">0.01")+COUNTIF(${range},"<-0.01")`,
    `=IF(${c}26>0,${c}12,"")`,
    `=${expected}-COUNT(${range})`,
  ];
});
checks.getRange("C26:C28").values = [["Failed checks by month"], ["Failed month-end"], ["Missing results by month"]];
checks.getRange(`D26:${endForecast}28`).formulas = [0, 1, 2].map((i) => perPeriod.map((expressions) => expressions[i]));
checks.getRange(`D27:${endForecast}27`).setNumberFormat("mmm-yy");
formula(checks, "D7", `=SUM(D26:${endForecast}26)`);
formula(checks, "D8", `=IF(COUNT(${detail})=0,"Unavailable",MAX(ABS(MIN(${detail})),ABS(MAX(${detail}))))`);
formula(checks, "D9", `=IF(D7>0,MIN(D27:${endForecast}27),"None")`);
formula(checks, "D10", `=SUM(D28:${endForecast}28)`);
checks.getRange("D8").setNumberFormat(gap);
checks.getRange("D9").setNumberFormat("mmm-yy");
checks.getRange("D7").conditionalFormats.addCustom("=$D$7>0", errorFormat);
checks.getRange("D10").conditionalFormats.addCustom("=$D$10>0", errorFormat);
checks.freezePanes.freezeRows(12);
checks.freezePanes.freezeColumns(3);

const near = (actual, expected, label) => assert.ok(Number.isFinite(actual) && Math.abs(actual - expected) <= 0.01, `${label}: ${actual} versus ${expected}`);
function verifyScenario(caseNumber) {
  values(control, "D5", caseNumber);
  workbook.recalculate();
  const code = cases[caseNumber - 1];
  assert.equal(overview.getRange("D4").values[0][0], code);
  const checkValues = checkRange.values;
  for (const [i, [label]] of checkLines.entries()) {
    for (const [j, period] of periods.entries()) {
      const expected = checkLines[i][1](col(j), col(j - 1), j >= actualPeriods.length);
      if (expected === null) assert.equal(checkValues[i][j], null, `${label} ${period}`);
      else near(checkValues[i][j], 0, `${code} ${label} ${period}`);
    }
  }
  near(overview.getRange("D7").values[0][0], actualPeriods.slice(-12).reduce((sum, period) => sum + integer(income.get(period), "revenue_minor"), 0) / 100, "C2 LTM revenue");
  const annualRevenue = forecastPeriods.slice(0, 12).reduce((sum, period) => sum + plan.get(`${code}/${period}/subscription_revenue`) + plan.get(`${code}/${period}/services_revenue`), 0) / 100;
  near(overview.getRange("E7").values[0][0], annualRevenue, `${code} first year plan revenue`);
  const monthly = statements.getRange(`${firstForecast}71:${endForecast}71`).values[0];
  const wacc = drivers[0][2][caseNumber - 1];
  const growth = drivers[1][2][caseNumber - 1];
  const pv = monthly.reduce((sum, value, i) => sum + value / (1 + wacc) ** ((i + 1) / 12), 0);
  const terminal = monthly.slice(-12).reduce((sum, value) => sum + value, 0);
  const funding = Math.max(...statements.getRange(`${firstForecast}66:${endForecast}66`).values[0]);
  const status = overview.getRange("D21").values[0][0];
  assert.equal(control.getRange("D6").values[0][0], approvalStates[caseNumber - 1]);
  assert.equal(control.getRange("D7").values[0][0], status);
  assert.deepEqual(checks.getRange("D7:D10").values, [[0], [0], ["None"], [0]]);
  near(overview.getRange("D26").values[0][0], pv, `${code} DCF present value`);
  const ev = overview.getRange("D29").values[0][0];
  if (terminal > 0 && funding <= 0.01) {
    assert.equal(status, "Indicative value");
    near(ev, pv + terminal * (1 + growth) / (wacc - growth) / (1 + wacc) ** 5, `${code} enterprise value`);
  } else {
    assert.equal(status, terminal <= 0 ? "Non-positive terminal cash flow" : "Unfunded cash floor");
    assert.ok(ev === "" || ev === null, "A blocked valuation must not show a number");
  }
  console.log(`${code}: ${status}. Funding gap ${funding.toFixed(2)}. EV ${ev ?? ""}`);
}
for (const caseNumber of [1, 2, 3]) verifyScenario(caseNumber);

values(control, "D5", 2);
workbook.recalculate();
const bullWacc = drivers[0][2][1];
const bullGrowth = drivers[1][2][1];
values(assumptions, "D10", bullGrowth);
workbook.recalculate();
assert.equal(overview.getRange("D21").values[0][0], "WACC must exceed growth");
values(assumptions, "D10", bullWacc);
workbook.recalculate();
const lastPlanCol = col(forecastPeriods.length - 1);
const terminalRevenue = statements.getRange(`${endForecast}11`).values[0][0];
const historicalRevenue = overview.getRange("D7").values[0][0];
values(assumptions, `${lastPlanCol}78`, .1);
workbook.recalculate();
near(statements.getRange(`${endForecast}11`).values[0][0], terminalRevenue * 1.1, "last month revenue adjustment");
near(overview.getRange("D7").values[0][0], historicalRevenue, "historical revenue after assumption edit");
values(assumptions, `${lastPlanCol}78`, 0);
values(control, "D5", 1);
const earlyCheck = checks.getRange(`D${firstCheckRow}`);
const lateCheck = checks.getRange(`${endForecast}${firstCheckRow}`);
const originalEarly = earlyCheck.formulas;
const originalLate = lateCheck.formulas;
earlyCheck.values = [[-0.05]];
lateCheck.values = [[0.2]];
workbook.recalculate();
assert.deepEqual(checks.getRange("D7:D10").values, [[2], [0.2], [excelDate(actualPeriods[0])], [0]]);
earlyCheck.values = [[null]];
workbook.recalculate();
assert.deepEqual(checks.getRange("D7:D10").values, [[1], [0.2], [excelDate(forecastPeriods.at(-1))], [1]]);
earlyCheck.formulas = originalEarly;
lateCheck.formulas = originalLate;
workbook.recalculate();
const summary = await workbook.inspect({ kind: "table", range: "Overview!C21:D33", include: "values,formulas", tableMaxRows: 13, tableMaxCols: 2, maxChars: 3500 });
console.log(summary.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 20 } });
assert.doesNotMatch(errors.ndjson, /"kind":"match"/);

await fs.mkdir(previewDir, { recursive: true });
for (const [sheetName, range] of [["Overview", "A1:I38"], ["Control", "A1:E30"], ["Assumptions", "A1:H27"], ["Statements", "C2:H25"], ["Checks", "C2:J28"]]) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
}
await fs.mkdir(path.dirname(output), { recursive: true });
// Artifact Tool renders the labels. Attach native workbook-local links at export
// because its HYPERLINK calculation does not return the display label.
const temp = path.join(previewDir, `export-${process.pid}.xlsx`);
try {
  await (await SpreadsheetFile.exportXlsx(workbook)).save(temp);
  const zip = await JSZip.loadAsync(await fs.readFile(temp));
  const readPart = async (name) => {
    const entry = zip.file(name);
    assert.ok(entry, name);
    return entry.async("string");
  };
  const workbookXml = await readPart("xl/workbook.xml");
  const relations = await readPart("xl/_rels/workbook.xml.rels");
  const attr = (tag, name) => tag.match(new RegExp(`(?:^|\\s)${name}="([^"]*)"`))?.[1];
  const sheetIds = new Map([...workbookXml.matchAll(/<x:sheet\b[^>]*>/g)].map(([tag]) => [attr(tag, "name"), attr(tag, "r:id")]));
  const targets = new Map([...relations.matchAll(/<Relationship\b[^>]*>/g)].map(([tag]) => [attr(tag, "Id"), attr(tag, "Target")]));
  const escape = (value) => value.replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
  for (const [sheetName, links] of jumps) {
    const target = targets.get(sheetIds.get(sheetName));
    assert.match(target ?? "", /^\/xl\/worksheets\/sheet\d+\.xml$/);
    const part = target.slice(1);
    const xml = await readPart(part);
    assert.ok(!xml.includes("<x:hyperlinks") && xml.includes("<x:pageMargins"));
    const entries = links.map(({ cell, targetSheet, targetCell, label }) => {
      assert.ok(sheetIds.has(targetSheet));
      return `<x:hyperlink ref="${escape(cell)}" location="${escape(`'${targetSheet}'!${targetCell}`)}" display="${escape(label)}" />`;
    });
    zip.file(part, xml.replace("<x:pageMargins", `<x:hyperlinks>${entries.join("")}</x:hyperlinks><x:pageMargins`));
  }
  await fs.writeFile(output, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }), { flag: "wx" });
} finally {
  await fs.unlink(temp).catch((error) => { if (error.code !== "ENOENT") throw error; });
}
console.log(`Saved ${output}`);
