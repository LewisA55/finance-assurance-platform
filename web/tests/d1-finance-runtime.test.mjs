import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

const webRoot = resolve(import.meta.dirname, "..");
const publicData = resolve(webRoot, "public", "finance-data");
const manifest = JSON.parse(
  readFileSync(resolve(publicData, "runtime-manifest.json"), "utf8"),
);
const snapshot = JSON.parse(
  readFileSync(resolve(publicData, "latest-command-centre.json"), "utf8"),
);

test("D1 runtime is pinned to the published C2 authority", () => {
  assert.equal(manifest.deliveryRef, "Q-FINANCE-C2@v1");
  assert.equal(manifest.financeModelRef, "Q-FINANCE-C1@v1");
  assert.equal(manifest.sourceDataRef, "ATLAS-FINANCE-STATUTORY-A24@v1");
  assert.equal(manifest.deliveredTableCount, 29);
  assert.equal(manifest.packageControlCount, 36);
});

test("every browser-local runtime file is authenticated before query registration", () => {
  for (const table of manifest.runtimeTables) {
    assert.equal(table.fileIntegrity.length, table.files.length, table.tableName);
    for (const item of table.fileIntegrity) {
      const path = resolve(webRoot, "public", item.url.slice(1));
      const bytes = readFileSync(path);
      assert.equal(bytes.length, item.bytes, item.url);
      assert.equal(`sha256:${createHash("sha256").update(bytes).digest("hex")}`, item.digest, item.url);
    }
  }
  const runtime = readFileSync(resolve(webRoot, "app", "lib", "finance-runtime", "client.ts"), "utf8");
  assert.match(runtime, /crypto\.subtle\.digest\("SHA-256"/);
  assert.match(runtime, /assertIntegrity\([\s\S]*`\$\{table\.tableName\} partition`/);
  assert.match(runtime, /assertIntegrity\(bytes, part\.bytes, part\.digest, "DuckDB-Wasm chunk"\)/);
});

test("DuckDB-Wasm is host-safe, complete and locally chunked", () => {
  assert.equal(manifest.duckdbWasm.variant, "eh");
  assert.equal(manifest.parquetExtension.version, "v1.5.4");
  assert.equal(manifest.parquetExtension.platform, "wasm_eh");
  assert.match(manifest.parquetExtension.digest, /^sha256:[0-9a-f]{64}$/);
  assert.equal(
    manifest.duckdbWasm.parts.reduce((sum, part) => sum + part.bytes, 0),
    manifest.duckdbWasm.sourceBytes,
  );
  for (const part of manifest.duckdbWasm.parts) {
    assert.ok(part.bytes < 25 * 1024 * 1024, part.url);
    assert.equal(existsSync(resolve(webRoot, "public", part.url.slice(1))), true, part.url);
  }
  assert.equal(
    existsSync(resolve(webRoot, "public", "duckdb", "duckdb-browser-eh.worker.js")),
    true,
  );
});

test("D1 loads only the three authorised first-slice tables", () => {
  const d1TableNames = [
    "mart_executive_cfo_command_center",
    "mart_cfo_metric_readiness",
    "mart_model_readiness_controls",
  ];
  const populations = Object.fromEntries(
    manifest.runtimeTables
      .filter((table) => d1TableNames.includes(table.tableName))
      .map((table) => [table.tableName, table.expectedRows]),
  );
  assert.deepEqual(populations, {
    mart_executive_cfo_command_center: 66,
    mart_cfo_metric_readiness: 11,
    mart_model_readiness_controls: 15,
  });
  assert.equal(
    manifest.runtimeTables
      .filter((table) => d1TableNames.includes(table.tableName))
      .flatMap((table) => table.files).length,
    8,
  );
  for (const table of manifest.runtimeTables.filter((row) => d1TableNames.includes(row.tableName))) {
    for (const url of table.files) {
      assert.equal(existsSync(resolve(webRoot, "public", url.slice(1))), true, url);
    }
  }
});

test("warm command-centre snapshot is the latest governed group version", () => {
  assert.equal(snapshot.period_id, "2026-06");
  assert.equal(snapshot.scope_id, "NEXUS-GROUP");
  assert.equal(snapshot.reporting_version_ref, "RV-NEXUS-GROUP-2026-06@v1");
  assert.equal(snapshot.presentation_status, "READY");
  assert.equal(snapshot.reliability_status, "RELIABLE_FOR_EXECUTIVE_PRESENTATION");
  assert.equal(snapshot.source_package_digest, manifest.sourceDataDigest);
});

test("DuckDB is client-only and the finance route owns the intelligence experience", () => {
  const component = readFileSync(
    resolve(webRoot, "app", "components", "finance", "FinanceIntelligenceExperience.tsx"),
    "utf8",
  );
  const runtime = readFileSync(
    resolve(webRoot, "app", "lib", "finance-runtime", "client.ts"),
    "utf8",
  );
  const page = readFileSync(
    resolve(webRoot, "app", "financial-performance", "page.tsx"),
    "utf8",
  );
  assert.match(component, /import\("\.\.\/\.\.\/lib\/finance-runtime\/queries"\)/);
  assert.match(runtime, /new duckdb\.AsyncDuckDB/);
  assert.match(runtime, /registerFileBuffer/);
  assert.match(runtime, /new Worker\("\/duckdb\/duckdb-browser-eh\.worker\.js"\)/);
  assert.match(runtime, /set custom_extension_repository/);
  assert.match(runtime, /load parquet/);
  assert.match(runtime, /set autoinstall_known_extensions = false/);
  assert.match(page, /FinanceIntelligenceExperience/);
  assert.doesNotMatch(component, /payroll plus AP|opening balance sheet proxy/i);
});
