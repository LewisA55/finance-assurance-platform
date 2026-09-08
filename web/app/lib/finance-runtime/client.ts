import * as duckdb from "@duckdb/duckdb-wasm";
import type { FinanceRuntimeManifest } from "./contracts";

let manifestPromise: Promise<FinanceRuntimeManifest> | null = null;
let runtimePromise: Promise<{
  database: duckdb.AsyncDuckDB;
  connection: duckdb.AsyncDuckDBConnection;
}> | null = null;
const registeredTableFiles = new Map<string, Map<string, string>>();
let queryQueue: Promise<void> = Promise.resolve();
let runtimeWorker: Worker | null = null;
let runtimeModuleUrl: string | null = null;

export type RuntimePhase =
  | "manifest"
  | "wasm"
  | "authenticating"
  | "registering"
  | "querying"
  | "ready"
  | "error";

export interface RuntimeProgress {
  phase: RuntimePhase;
  label: string;
  loadedFiles: number;
  totalFiles: number;
  loadedBytes: number;
  totalBytes: number;
}

export interface RuntimeTableRequest {
  tableName: string;
  fromYear?: number;
  throughYear?: number;
  years?: number[];
}

type RuntimeTableInput = string | RuntimeTableRequest;
type RuntimeProgressListener = (progress: RuntimeProgress) => void;

const progressListeners = new Set<RuntimeProgressListener>();
let latestProgress: RuntimeProgress = {
  phase: "manifest",
  label: "Reading governed runtime authority",
  loadedFiles: 0,
  totalFiles: 0,
  loadedBytes: 0,
  totalBytes: 0,
};

function publishProgress(progress: RuntimeProgress): void {
  latestProgress = progress;
  for (const listener of progressListeners) listener(progress);
}

export function subscribeRuntimeProgress(listener: RuntimeProgressListener): () => void {
  progressListeners.add(listener);
  listener(latestProgress);
  return () => progressListeners.delete(listener);
}

async function sha256Digest(bytes: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return `sha256:${[...new Uint8Array(digest)]
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("")}`;
}

async function assertIntegrity(
  bytes: ArrayBuffer,
  expectedBytes: number,
  expectedDigest: string,
  label: string,
): Promise<void> {
  if (bytes.byteLength !== expectedBytes) throw new Error(`${label} size mismatch`);
  if ((await sha256Digest(bytes)) !== expectedDigest) throw new Error(`${label} digest mismatch`);
}

export function getRuntimeManifest(): Promise<FinanceRuntimeManifest> {
  if (!manifestPromise) {
    publishProgress({
      phase: "manifest",
      label: "Reading governed runtime authority",
      loadedFiles: 0,
      totalFiles: 1,
      loadedBytes: 0,
      totalBytes: 0,
    });
    manifestPromise = fetch("/finance-data/runtime-manifest.json").then(
      async (response) => {
        if (!response.ok) {
          throw new Error(`Finance runtime manifest unavailable (${response.status})`);
        }
        const manifest = (await response.json()) as FinanceRuntimeManifest;
        publishProgress({
          phase: "wasm",
          label: "Preparing local DuckDB-Wasm",
          loadedFiles: 1,
          totalFiles: 1,
          loadedBytes: 0,
          totalBytes: manifest.duckdbWasm.sourceBytes,
        });
        return manifest;
      },
    );
  }
  return manifestPromise;
}

async function assembleWasmModule(manifest: FinanceRuntimeManifest): Promise<string> {
  let loadedBytes = 0;
  let loadedParts = 0;
  const parts = await Promise.all(
    manifest.duckdbWasm.parts.map(async (part) => {
      const response = await fetch(part.url);
      if (!response.ok) throw new Error(`DuckDB-Wasm chunk unavailable (${response.status})`);
      const bytes = await response.arrayBuffer();
      await assertIntegrity(bytes, part.bytes, part.digest, "DuckDB-Wasm chunk");
      loadedBytes += bytes.byteLength;
      loadedParts += 1;
      publishProgress({
        phase: "wasm",
        label: "Authenticating local query engine",
        loadedFiles: loadedParts,
        totalFiles: manifest.duckdbWasm.parts.length,
        loadedBytes,
        totalBytes: manifest.duckdbWasm.sourceBytes,
      });
      return bytes;
    }),
  );
  return URL.createObjectURL(new Blob(parts, { type: "application/wasm" }));
}

async function createDatabase(manifest: FinanceRuntimeManifest): Promise<duckdb.AsyncDuckDB> {
  if (typeof WebAssembly === "undefined") {
    throw new Error("This browser does not support WebAssembly");
  }
  const mainModule = await assembleWasmModule(manifest);
  const worker = new Worker("/duckdb/duckdb-browser-eh.worker.js");
  const logger = new duckdb.ConsoleLogger(duckdb.LogLevel.WARNING);
  const database = new duckdb.AsyncDuckDB(logger, worker);
  try {
    await database.instantiate(mainModule);
  } catch (error) {
    worker.terminate();
    URL.revokeObjectURL(mainModule);
    throw error;
  }
  runtimeWorker = worker;
  runtimeModuleUrl = mainModule;
  return database;
}

function assertTableName(tableName: string): void {
  if (!/^[a-z][a-z0-9_]*$/.test(tableName)) {
    throw new Error(`Rejected runtime table name: ${tableName}`);
  }
}

async function registerRuntimeTable(
  database: duckdb.AsyncDuckDB,
  connection: duckdb.AsyncDuckDBConnection,
  manifest: FinanceRuntimeManifest,
  request: RuntimeTableRequest,
): Promise<void> {
  const { tableName } = request;
  assertTableName(tableName);
  const table = manifest.runtimeTables.find((row) => row.tableName === tableName);
  if (!table) throw new Error(`Runtime table is not authorised: ${tableName}`);
  const requestedYears = request.years ? new Set(request.years) : null;
  const selectedFiles = table.files.filter((url) => {
    const match = url.match(/period_year=(\d{4})/);
    if (!match) return true;
    const year = Number(match[1]);
    if (requestedYears && !requestedYears.has(year)) return false;
    if (request.fromYear != null && year < request.fromYear) return false;
    if (request.throughYear != null && year > request.throughYear) return false;
    return true;
  });
  if (selectedFiles.length === 0) {
    throw new Error(`${tableName} has no authorised partitions for the requested horizon`);
  }
  const registeredFiles = registeredTableFiles.get(tableName) ?? new Map<string, string>();
  const pendingFiles = selectedFiles.filter((url) => !registeredFiles.has(url));
  if (pendingFiles.length === 0) return;
  const totalBytes = pendingFiles.reduce((sum, url) => {
    return sum + (table.fileIntegrity.find((item) => item.url === url)?.bytes ?? 0);
  }, 0);
  let loadedBytes = 0;
  let loadedFiles = 0;
  publishProgress({
    phase: "authenticating",
    label: `Authenticating ${tableName.replaceAll("_", " ")}`,
    loadedFiles,
    totalFiles: pendingFiles.length,
    loadedBytes,
    totalBytes,
  });
  const buffers = await Promise.all(
    pendingFiles.map(async (url) => {
      const integrity = table.fileIntegrity.find((item) => item.url === url);
      if (!integrity) throw new Error(`${table.tableName} partition integrity unavailable`);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`${table.tableName} partition unavailable (${response.status})`);
      }
      const bytes = await response.arrayBuffer();
      await assertIntegrity(
        bytes,
        integrity.bytes,
        integrity.digest,
        `${table.tableName} partition`,
      );
      loadedFiles += 1;
      loadedBytes += bytes.byteLength;
      publishProgress({
        phase: "authenticating",
        label: `Authenticating ${tableName.replaceAll("_", " ")}`,
        loadedFiles,
        totalFiles: pendingFiles.length,
        loadedBytes,
        totalBytes,
      });
      const sourceIndex = table.files.indexOf(url);
      return {
        url,
        name: `${table.tableName}__${sourceIndex}.parquet`,
        bytes: new Uint8Array(bytes),
      };
    }),
  );

  for (const file of buffers) {
    await database.registerFileBuffer(file.name, file.bytes);
    registeredFiles.set(file.url, file.name);
  }
  registeredTableFiles.set(tableName, registeredFiles);
  const partitionQuery = [...registeredFiles.values()]
    .map((name) => `select * from read_parquet('${name}')`)
    .join(" union all ");
  publishProgress({
    phase: "registering",
    label: `Registering ${tableName.replaceAll("_", " ")}`,
    loadedFiles: pendingFiles.length,
    totalFiles: pendingFiles.length,
    loadedBytes: totalBytes,
    totalBytes,
  });
  try {
    await connection.query(
      `create or replace view "${table.tableName}" as ${partitionQuery}`,
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : "unknown DuckDB error";
    throw new Error(`${tableName} registration failed: ${message}`);
  }
}

async function getRuntime(): Promise<{
  database: duckdb.AsyncDuckDB;
  connection: duckdb.AsyncDuckDBConnection;
}> {
  if (!runtimePromise) {
    runtimePromise = (async () => {
      const manifest = await getRuntimeManifest();
      const database = await createDatabase(manifest);
      const connection = await database.connect();
      const extensionResponse = await fetch(manifest.parquetExtension.url);
      if (!extensionResponse.ok) {
        throw new Error(`Local Parquet extension unavailable (${extensionResponse.status})`);
      }
      const extensionBytes = await extensionResponse.arrayBuffer();
      await assertIntegrity(
        extensionBytes,
        manifest.parquetExtension.bytes,
        manifest.parquetExtension.digest,
        "Local Parquet extension",
      );
      const extensionRepository = `${window.location.origin}/duckdb/extensions`;
      await connection.query(`set custom_extension_repository = '${extensionRepository}'`);
      await connection.query("load parquet");
      await connection.query("set autoinstall_known_extensions = false");
      await connection.query("set allow_community_extensions = false");
      return { database, connection };
    })().catch((error) => {
      runtimePromise = null;
      runtimeWorker?.terminate();
      if (runtimeModuleUrl) URL.revokeObjectURL(runtimeModuleUrl);
      runtimeWorker = null;
      runtimeModuleUrl = null;
      registeredTableFiles.clear();
      publishProgress({ ...latestProgress, phase: "error", label: "Local runtime unavailable" });
      throw error;
    });
  }
  return runtimePromise;
}

export async function getConnection(): Promise<duckdb.AsyncDuckDBConnection> {
  return (await getRuntime()).connection;
}

function normaliseTableRequest(input: RuntimeTableInput): RuntimeTableRequest {
  return typeof input === "string" ? { tableName: input } : input;
}

async function ensureRuntimeTables(tableInputs: RuntimeTableInput[]): Promise<void> {
  const manifest = await getRuntimeManifest();
  const { database, connection } = await getRuntime();
  const requests = new Map<string, RuntimeTableRequest>();
  for (const input of tableInputs) {
    const request = normaliseTableRequest(input);
    requests.set(JSON.stringify(request), request);
  }
  for (const request of requests.values()) {
    await registerRuntimeTable(database, connection, manifest, request);
  }
}

function toSafeJsonRecord(row: { toJSON(): unknown }): Record<string, unknown> {
  const record = row.toJSON() as Record<string, unknown>;
  for (const key of Object.keys(record)) {
    const value = record[key];
    if (typeof value !== "bigint") continue;
    if (value > BigInt(Number.MAX_SAFE_INTEGER) || value < BigInt(Number.MIN_SAFE_INTEGER)) {
      throw new Error(`Unsafe integer conversion rejected for ${key}; cast explicitly in governed SQL`);
    }
    record[key] = Number(value);
  }
  return record;
}

export async function runQuery<T>(sql: string, tableNames: RuntimeTableInput[] = []): Promise<T[]> {
  let release: () => void = () => {};
  const previous = queryQueue;
  queryQueue = new Promise<void>((resolve) => {
    release = resolve;
  });
  await previous;
  try {
    await ensureRuntimeTables(tableNames);
    const connection = await getConnection();
    publishProgress({ ...latestProgress, phase: "querying", label: "Querying authenticated Parquet" });
    let result;
    try {
      result = await connection.query(sql);
    } catch (error) {
      const message = error instanceof Error ? error.message : "unknown DuckDB error";
      const authorities = tableNames.map((input) => normaliseTableRequest(input).tableName).join(", ");
      throw new Error(`Governed query failed for ${authorities || "runtime metadata"}: ${message}`);
    }
    const rows = result.toArray().map((row) => toSafeJsonRecord(row) as T);
    publishProgress({ ...latestProgress, phase: "ready", label: "Governed local query ready" });
    return rows;
  } finally {
    release();
  }
}

export async function disposeRuntime(): Promise<void> {
  const runtime = await runtimePromise?.catch(() => null);
  try {
    if (runtime) {
      try {
        await runtime.connection.close();
      } finally {
        await runtime.database.terminate();
      }
    }
  } finally {
    runtimeWorker?.terminate();
    if (runtimeModuleUrl) URL.revokeObjectURL(runtimeModuleUrl);
    runtimePromise = null;
    runtimeWorker = null;
    runtimeModuleUrl = null;
    registeredTableFiles.clear();
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("pagehide", () => {
    void disposeRuntime();
  }, { once: true });
}
