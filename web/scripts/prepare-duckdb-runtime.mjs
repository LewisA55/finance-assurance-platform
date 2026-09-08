import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(scriptDirectory, "..");
const publicRoot = join(webRoot, "public");
const targetRoot = join(publicRoot, "duckdb");
const wasmSource = join(
  webRoot,
  "node_modules",
  "@duckdb",
  "duckdb-wasm",
  "dist",
  "duckdb-eh.wasm",
);
const workerSource = join(
  webRoot,
  "node_modules",
  "@duckdb",
  "duckdb-wasm",
  "dist",
  "duckdb-browser-eh.worker.js",
);

function digest(bytes) {
  return `sha256:${createHash("sha256").update(bytes).digest("hex")}`;
}

async function main() {
  const manifest = JSON.parse(
    await readFile(join(publicRoot, "finance-data", "runtime-manifest.json"), "utf8"),
  );
  const wasm = await readFile(wasmSource);
  if (wasm.length !== manifest.duckdbWasm.sourceBytes) {
    throw new Error("Pinned DuckDB-Wasm byte length does not match the runtime manifest");
  }
  if (digest(wasm) !== manifest.duckdbWasm.sourceDigest) {
    throw new Error("Pinned DuckDB-Wasm digest does not match the runtime manifest");
  }

  await mkdir(targetRoot, { recursive: true });
  await copyFile(workerSource, join(targetRoot, "duckdb-browser-eh.worker.js"));

  let offset = 0;
  for (const part of manifest.duckdbWasm.parts) {
    const bytes = wasm.subarray(offset, offset + part.bytes);
    if (bytes.length !== part.bytes || digest(bytes) !== part.digest) {
      throw new Error(`DuckDB-Wasm chunk contract failed for ${part.url}`);
    }
    const filename = part.url.split("/").at(-1);
    if (!filename || !/^duckdb-eh\.part-\d+\.bin$/.test(filename)) {
      throw new Error(`Unsafe DuckDB-Wasm chunk path: ${part.url}`);
    }
    await writeFile(join(targetRoot, filename), bytes);
    offset += part.bytes;
  }
  if (offset !== wasm.length) throw new Error("DuckDB-Wasm manifest does not cover the source module");

  const extension = manifest.parquetExtension;
  if (!extension || extension.version !== "v1.5.4" || extension.platform !== "wasm_eh") {
    throw new Error("Pinned Parquet extension contract is unavailable");
  }
  const extensionTarget = join(
    targetRoot,
    "extensions",
    extension.version,
    extension.platform,
    "parquet.duckdb_extension.wasm",
  );
  let extensionBytes;
  try {
    extensionBytes = await readFile(extensionTarget);
  } catch {
    const response = await fetch(extension.sourceUrl);
    if (!response.ok) {
      throw new Error(`Pinned Parquet extension unavailable (${response.status})`);
    }
    extensionBytes = Buffer.from(await response.arrayBuffer());
  }
  if (extensionBytes.length !== extension.bytes || digest(extensionBytes) !== extension.digest) {
    throw new Error("Pinned Parquet extension integrity differs");
  }
  await mkdir(dirname(extensionTarget), { recursive: true });
  await writeFile(extensionTarget, extensionBytes);
  process.stdout.write(
    `Prepared ${manifest.duckdbWasm.parts.length} verified DuckDB-Wasm chunks and one signed Parquet extension.\n`,
  );
}

await main();
