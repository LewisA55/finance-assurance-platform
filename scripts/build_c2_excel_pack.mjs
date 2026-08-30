import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const argv = process.argv.slice(2);
const options = {};
for (let index = 0; index < argv.length; index += 2) {
  const key = argv[index];
  const value = argv[index + 1];
  if (!key?.startsWith("--") || value === undefined) {
    throw new Error("arguments must be supplied as --name value pairs");
  }
  options[key.slice(2)] = value;
}

for (const required of ["mode", "input", "workbook"]) {
  if (!options[required]) throw new Error(`missing --${required}`);
}
if (!new Set(["build", "verify"]).has(options.mode)) {
  throw new Error("--mode must be build or verify");
}

const input = JSON.parse(await fs.readFile(options.input, "utf8"));
if (input.contract_version !== "q-finance-c2-workbook-input@v1") {
  throw new Error("unsupported workbook input contract");
}

const NAVY = "#17365D";
const BLUE = "#1F4E78";
const PALE_BLUE = "#D9EAF7";
const PALE_GREEN = "#E2F0D9";
const PALE_RED = "#FCE4D6";
const GREY = "#E7E6E6";
const TEXT = "#1F2937";
const WHITE = "#FFFFFF";
const LIGHT_BORDER = "#D9E2F3";

function excelColumn(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    value -= 1;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
}

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, stable(value[key])]),
    );
  }
  return value;
}

function sha256(value) {
  return `sha256:${crypto.createHash("sha256").update(value).digest("hex")}`;
}

function workbookLogicalDigest() {
  const preimage = {
    contract_version: "q-finance-c2-workbook-logical@v1",
    delivery_ref: input.delivery_ref,
    finance_model_digest: input.finance_model_digest,
    source_data_digest: input.source_data_digest,
    documentation: {
      catalogue: input.catalogue,
      controls: input.controls,
      dictionary: input.dictionary,
      relationships: input.relationships,
      measures: input.measures,
    },
    data_sheets: input.data_sheets.map((sheet) => ({
      table_name: sheet.table_name,
      sheet_name: sheet.sheet_name,
      row_count: sheet.rows.length,
      logical_digest: sheet.logical_digest,
    })),
  };
  return sha256(JSON.stringify(stable(preimage)));
}

function toCellValue(value, sourceType) {
  if (value === null) return null;
  const upper = sourceType.toUpperCase();
  if (/^(BIGINT|INTEGER|SMALLINT|TINYINT|HUGEINT|UBIGINT)/.test(upper)) {
    const numeric = Number(value);
    if (!Number.isSafeInteger(numeric)) {
      throw new Error(`integer exceeds safe Excel precision: ${value}`);
    }
    return numeric;
  }
  if (/^(DOUBLE|FLOAT|REAL|DECIMAL|NUMERIC)/.test(upper)) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) throw new Error(`invalid numeric value: ${value}`);
    return numeric;
  }
  if (upper === "BOOLEAN") return Boolean(value);
  if (upper === "DATE") return new Date(`${value}T00:00:00.000Z`);
  // Excel serials have no timezone. Preserve governed timestamp instants as ISO text.
  if (upper.startsWith("TIMESTAMP")) return `'${String(value)}`;
  return String(value);
}

function expectedComparable(value, sourceType) {
  if (sourceType.toUpperCase().startsWith("TIMESTAMP")) return String(value);
  const converted = toCellValue(value, sourceType);
  if (converted instanceof Date) return converted.toISOString();
  return converted;
}

function actualComparable(value, sourceType) {
  if (value === undefined || value === "") return value === "" ? "" : null;
  if (value === null) return null;
  const upper = sourceType.toUpperCase();
  if (upper.startsWith("TIMESTAMP")) {
    const text = String(value);
    return text.startsWith("'") ? text.slice(1) : text;
  }
  if (upper === "DATE") {
    if (value instanceof Date) return value.toISOString();
    if (typeof value === "number") {
      const excelEpoch = Date.UTC(1899, 11, 30);
      return new Date(excelEpoch + value * 86400000).toISOString();
    }
    return new Date(value).toISOString();
  }
  if (/^(BIGINT|INTEGER|SMALLINT|TINYINT|HUGEINT|UBIGINT|DOUBLE|FLOAT|REAL|DECIMAL|NUMERIC)/.test(upper)) {
    return Number(value);
  }
  if (upper === "BOOLEAN") return Boolean(value);
  return String(value);
}

function titleFormat(range) {
  range.format = {
    fill: NAVY,
    font: { bold: true, color: WHITE, size: 16 },
    verticalAlignment: "center",
    horizontalAlignment: "left",
  };
  range.format.rowHeight = 28;
}

function headerFormat(range) {
  range.format = {
    fill: BLUE,
    font: { bold: true, color: WHITE },
    verticalAlignment: "center",
    horizontalAlignment: "left",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: LIGHT_BORDER },
  };
  range.format.rowHeight = 30;
}

function addDocumentTable(workbook, name, title, headers, rows, widths = {}) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  const lastColumn = excelColumn(Math.max(headers.length - 1, 7));
  sheet.getRange(`A1:${lastColumn}2`).merge();
  sheet.getRange("A1").values = [[title]];
  titleFormat(sheet.getRange(`A1:${lastColumn}2`));
  sheet.getRangeByIndexes(3, 0, 1, headers.length).values = [headers];
  headerFormat(sheet.getRangeByIndexes(3, 0, 1, headers.length));
  if (rows.length > 0) {
    sheet.getRangeByIndexes(4, 0, rows.length, headers.length).values = rows;
    const range = `A4:${excelColumn(headers.length - 1)}${rows.length + 4}`;
    const table = sheet.tables.add(range, true, `C2_${name.replace(/[^A-Za-z0-9]/g, "")}`);
    table.style = "TableStyleMedium2";
    table.showBandedRows = true;
    table.showFilterButton = true;
  }
  headers.forEach((header, index) => {
    const width = widths[header] ?? Math.min(Math.max(header.length + 3, 12), 28);
    sheet.getRangeByIndexes(0, index, rows.length + 4, 1).format.columnWidth = width;
  });
  sheet.freezePanes.freezeRows(4);
  return sheet;
}

function buildWorkbook() {
  const workbook = Workbook.create();
  const cover = workbook.worksheets.add("Cover");
  cover.showGridLines = false;
  cover.getRange("A1:D2").format = { fill: NAVY };
  cover.getRange("A1").values = [["Finance Assurance C1 - Governed Data Pack"]];
  titleFormat(cover.getRange("A1:D2"));
  cover.getRange("A4:B12").values = [
    ["Delivery reference", input.delivery_ref],
    ["Built at", `'${input.built_at}`],
    ["Finance-model reference", input.finance_model_ref],
    ["Finance-model digest", input.finance_model_digest],
    ["Model semantic digest", input.model_semantic_digest],
    ["Source-data reference", input.source_data_ref],
    ["Source-data digest", input.source_data_digest],
    ["Delivered tables", input.catalogue.length],
    ["Workbook data sheets", input.data_sheets.length],
  ];
  cover.getRange("A4:A12").format = { fill: PALE_BLUE, font: { bold: true, color: TEXT } };
  cover.getRange("B4:B12").format = { font: { color: TEXT }, wrapText: true };
  cover.getRange("D4").values = [["MODEL-READY DATA - VERIFIED"]];
  cover.getRange("D4").format = {
    fill: PALE_GREEN,
    font: { bold: true, color: "#006100", size: 14 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "medium", color: "#70AD47" },
  };
  cover.getRange("A15").values = [["Purpose and boundary"]];
  headerFormat(cover.getRange("A15:D15"));
  cover.getRange("A16:A21").values = [
    ["Data-only handoff for Excel model construction and review."],
    ["All monetary fields ending _minor remain integer minor units."],
    ["Blue workbook headers identify governed imports, not editable assumptions."],
    ["No DCF, forecast formula, dashboard, chart, macro or external connection is included."],
    ["Use CSV for refreshable ingestion and these sheets for inspection and model linking."],
    ["Full source paths, grains, controls and semantic specifications are listed in the documentation sheets."],
  ];
  cover.getRange("A16:D21").format = { wrapText: true, verticalAlignment: "top", font: { color: TEXT } };
  cover.getRange("A1:A30").format.columnWidth = 28;
  cover.getRange("B1:B30").format.columnWidth = 42;
  cover.getRange("C1:C30").format.columnWidth = 4;
  cover.getRange("D1:D30").format.columnWidth = 36;
  cover.freezePanes.freezeRows(2);

  addDocumentTable(
    workbook,
    "Table_Catalogue",
    "Delivered Table Catalogue",
    ["Dataset ID", "Table", "Class", "Grain", "Rows", "Excel Sheet", "React Partition", "Power BI File", "Reliability Purpose"],
    input.catalogue.map((row) => [row.dataset_id, row.table_name, row.delivery_class, row.grain, row.row_count, row.excel_sheet ?? "CSV only", row.react_partition_strategy, row.powerbi_path, row.reliability_purpose]),
    { "Table": 34, "Grain": 42, "Excel Sheet": 22, "Power BI File": 44, "Reliability Purpose": 40 },
  );

  const controlSheet = addDocumentTable(
    workbook,
    "Control_Totals",
    "Cross-Format Reconciliation and Readiness Controls",
    ["Control", "Table", "Expected", "Actual", "Difference", "Status", "Evidence"],
    input.controls.map((row) => [row.control_id, row.table_name ?? "PACKAGE", row.expected_value, row.actual_value, row.difference, row.status, row.evidence]),
    { "Control": 30, "Table": 34, "Evidence": 52 },
  );
  const statusRange = controlSheet.getRange(`F5:F${input.controls.length + 4}`);
  statusRange.conditionalFormats.add("containsText", { text: "PASS", format: { fill: PALE_GREEN, font: { color: "#006100", bold: true } } });
  statusRange.conditionalFormats.add("containsText", { text: "FAIL", format: { fill: PALE_RED, font: { color: "#9C0006", bold: true } } });

  addDocumentTable(
    workbook,
    "Data_Dictionary",
    "C1 Data Dictionary",
    ["Dataset ID", "Table", "Ordinal", "Column", "DuckDB Type", "Nullable", "Field Role", "Suggested Summarisation", "Suggested Visibility"],
    input.dictionary.map((row) => [row.dataset_id, row.table_name, row.ordinal, row.column_name, row.data_type, row.nullable, row.field_role, row.suggested_summarisation, row.suggested_visibility]),
    { "Table": 34, "Column": 38, "DuckDB Type": 22, "Field Role": 24, "Suggested Summarisation": 24, "Suggested Visibility": 20 },
  );

  addDocumentTable(
    workbook,
    "Relationships",
    "Q-FINANCE v5 Relationship Guidance",
    ["Relationship ID", "From Table", "From Columns", "To Table", "To Columns", "Cardinality", "Load Disposition", "Endpoint Status"],
    input.relationships.map((row) => [row.relationship_id, row.from_table, row.from_columns, row.to_table, row.to_columns, row.cardinality, row.load_disposition, row.endpoint_status]),
    { "From Table": 34, "From Columns": 28, "To Table": 34, "To Columns": 28, "Load Disposition": 24, "Endpoint Status": 26 },
  );

  addDocumentTable(
    workbook,
    "Measures",
    "Q-FINANCE v5 Measure Specifications",
    ["Measure ID", "Dataset ID", "Table", "Measure", "Source Field", "Aggregation", "Measure Class", "Required Grain", "Reporting-Version Policy"],
    input.measures.map((row) => [row.measure_id, row.dataset_id, row.table_name, row.measure_name, row.source_field, row.aggregation, row.measure_class, row.required_grain, row.reporting_version_policy]),
    { "Table": 34, "Measure": 38, "Source Field": 32, "Measure Class": 30, "Required Grain": 55, "Reporting-Version Policy": 32 },
  );

  for (const dataSheet of input.data_sheets) {
    const sheet = workbook.worksheets.add(dataSheet.sheet_name);
    sheet.showGridLines = true;
    const columnCount = dataSheet.columns.length;
    const rowCount = dataSheet.rows.length;
    const lastColumn = excelColumn(columnCount - 1);
    sheet.getRange(`A1:${lastColumn}1`).merge();
    sheet.getRange("A1").values = [[dataSheet.table_name]];
    titleFormat(sheet.getRange(`A1:${lastColumn}1`));
    sheet.getRange(`A2:${lastColumn}2`).merge();
    sheet.getRange("A2").values = [[`Grain: ${dataSheet.grain} | Rows: ${rowCount} | Logical digest: ${dataSheet.logical_digest}`]];
    sheet.getRange(`A2:${lastColumn}2`).format = { fill: GREY, font: { italic: true, color: TEXT }, wrapText: true };
    sheet.getRangeByIndexes(3, 0, 1, columnCount).values = [dataSheet.columns.map((column) => column.name)];
    headerFormat(sheet.getRangeByIndexes(3, 0, 1, columnCount));
    dataSheet.columns.forEach((column, index) => {
      if (column.data_type.toUpperCase().startsWith("TIMESTAMP")) {
        sheet.getRangeByIndexes(4, index, Math.max(rowCount, 1), 1).format.numberFormat = "@";
      }
    });
    const values = dataSheet.rows.map((row) => row.map((value, index) => toCellValue(value, dataSheet.columns[index].data_type)));
    if (rowCount > 0) {
      sheet.getRangeByIndexes(4, 0, rowCount, columnCount).values = values;
      const table = sheet.tables.add(`A4:${lastColumn}${rowCount + 4}`, true, `C2Data_${dataSheet.sheet_name.replace(/[^A-Za-z0-9]/g, "")}`);
      table.style = "TableStyleMedium2";
      table.showBandedRows = true;
      table.showFilterButton = true;
    }
    dataSheet.columns.forEach((column, index) => {
      const name = column.name;
      const upper = column.data_type.toUpperCase();
      const range = sheet.getRangeByIndexes(4, index, Math.max(rowCount, 1), 1);
      if (name.endsWith("_minor")) range.format.numberFormat = "#,##0;[Red](#,##0);-";
      else if (name.endsWith("_bps")) range.format.numberFormat = "#,##0 \"bps\";[Red](#,##0 \"bps\");-";
      else if (/^(BIGINT|INTEGER|SMALLINT|TINYINT|HUGEINT|UBIGINT)/.test(upper)) range.format.numberFormat = "#,##0;[Red](#,##0);-";
      else if (/^(DOUBLE|FLOAT|REAL|DECIMAL|NUMERIC)/.test(upper)) range.format.numberFormat = "0.0;[Red](0.0);-";
      else if (upper === "DATE") range.format.numberFormat = "yyyy-mm-dd";
      // Governed timestamps stay ISO text because Excel has no timezone-aware type.
      const wideText = /(_digest|_relation|_purpose|_authority|_name|_label)$/.test(name);
      const width = wideText ? 28 : /(_id|_ref|_hk)$/.test(name) ? 22 : name.length > 20 ? 20 : 15;
      sheet.getRangeByIndexes(0, index, rowCount + 4, 1).format.columnWidth = width;
    });
    sheet.freezePanes.freezeRows(4);
    sheet.freezePanes.freezeColumns(Math.min(2, columnCount));
  }
  return workbook;
}

async function verifyWorkbook(workbook) {
  const expectedNames = ["Cover", "Table_Catalogue", "Control_Totals", "Data_Dictionary", "Relationships", "Measures", ...input.data_sheets.map((sheet) => sheet.sheet_name)];
  const actualNames = [];
  for (let index = 0; index < expectedNames.length; index += 1) {
    actualNames.push(workbook.worksheets.getItemAt(index).name);
  }
  if (JSON.stringify(actualNames) !== JSON.stringify(expectedNames)) {
    throw new Error(`workbook sheet inventory differs: ${JSON.stringify(actualNames)}`);
  }
  let checkedCells = 0;
  for (const dataSheet of input.data_sheets) {
    const sheet = workbook.worksheets.getItem(dataSheet.sheet_name);
    const columnCount = dataSheet.columns.length;
    const rowCount = dataSheet.rows.length;
    const headers = sheet.getRangeByIndexes(3, 0, 1, columnCount).values[0];
    if (JSON.stringify(headers) !== JSON.stringify(dataSheet.columns.map((column) => column.name))) {
      throw new Error(`workbook headers differ for ${dataSheet.table_name}`);
    }
    const values = rowCount > 0 ? sheet.getRangeByIndexes(4, 0, rowCount, columnCount).values : [];
    for (let rowIndex = 0; rowIndex < rowCount; rowIndex += 1) {
      for (let columnIndex = 0; columnIndex < columnCount; columnIndex += 1) {
        const sourceType = dataSheet.columns[columnIndex].data_type;
        const expected = expectedComparable(dataSheet.rows[rowIndex][columnIndex], sourceType);
        const actual = actualComparable(values[rowIndex][columnIndex], sourceType);
        if (expected !== actual) {
          throw new Error(`workbook value differs at ${dataSheet.sheet_name}!${excelColumn(columnIndex)}${rowIndex + 5}: expected=${expected} actual=${actual}`);
        }
        checkedCells += 1;
      }
    }
  }
  const errors = new Set(["#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"]);
  for (const sheetName of expectedNames) {
    const used = workbook.worksheets.getItem(sheetName).getUsedRange(true);
    for (const row of used.formulas ?? []) {
      for (const formula of row) {
        if (typeof formula === "string" && formula.startsWith("=")) {
          throw new Error(`data pack must be formula-free: ${sheetName}`);
        }
      }
    }
    for (const row of used.values ?? []) {
      for (const value of row) {
        if (typeof value === "string" && errors.has(value)) {
          throw new Error(`workbook error scan returned ${value} in ${sheetName}`);
        }
      }
    }
  }
  return { sheet_count: expectedNames.length, data_sheet_count: input.data_sheets.length, checked_cell_count: checkedCells };
}

async function renderPreviews(workbook, previewDir) {
  if (!previewDir) return 0;
  await fs.mkdir(previewDir, { recursive: true });
  const names = ["Cover", "Table_Catalogue", "Control_Totals", "Data_Dictionary", "Relationships", "Measures", ...input.data_sheets.map((sheet) => sheet.sheet_name)];
  for (const name of names) {
    const sheet = workbook.worksheets.getItem(name);
    const used = sheet.getUsedRange(true);
    const rowCount = Math.min(used.rowCount ?? 22, name === "Cover" ? 26 : 22);
    const columnCount = Math.min(used.columnCount ?? 12, 12);
    const range = `A1:${excelColumn(Math.max(columnCount - 1, 0))}${Math.max(rowCount, 1)}`;
    const blob = await workbook.render({ sheetName: name, range, scale: 1, format: "png" });
    await fs.writeFile(path.join(previewDir, `${name}.png`), new Uint8Array(await blob.arrayBuffer()));
  }
  return names.length;
}

let workbook;
let verification;
let previewCount = 0;
if (options.mode === "build") {
  workbook = buildWorkbook();
  await fs.mkdir(path.dirname(options.workbook), { recursive: true });
  verification = await verifyWorkbook(workbook);
  previewCount = await renderPreviews(workbook, options.previews);
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(options.workbook);
  const imported = await SpreadsheetFile.importXlsx(await FileBlob.load(options.workbook));
  verification = await verifyWorkbook(imported);
} else {
  workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(options.workbook));
  verification = await verifyWorkbook(workbook);
}

const workbookBytes = await fs.readFile(options.workbook);
process.stdout.write(`${JSON.stringify({
  status: "VERIFIED",
  workbook_sha256: sha256(workbookBytes),
  workbook_byte_count: workbookBytes.length,
  workbook_logical_digest: workbookLogicalDigest(),
  preview_count: previewCount,
  ...verification,
})}\n`);
