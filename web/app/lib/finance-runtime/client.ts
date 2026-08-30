import * as duckdb from "@duckdb/duckdb-wasm";
import type { FinanceRuntimeManifest } from "./contracts";

let manifestPromise: Promise<FinanceRuntimeManifest> | null = null;
let runtimePromise: Promise<{
  database: duckdb.AsyncDuckDB;
  connection: duckdb.AsyncDuckDBConnection;
}> | null = null;
const registeredTables = new Set<string>();
let queryQueue: Promise<void> = Promise.resolve();

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
    manifestPromise = fetch("/finance-data/runtime-manifest.json").then(
      async (response) => {
        if (!response.ok) {
          throw new Error(`Finance runtime manifest unavailable (${response.status})`);
        }
        return (await response.json()) as FinanceRuntimeManifest;
      },
    );
  }
  return manifestPromise;
}

async function assembleWasmModule(manifest: FinanceRuntimeManifest): Promise<string> {
  const parts = await Promise.all(
    manifest.duckdbWasm.parts.map(async (part) => {
      const response = await fetch(part.url);
      if (!response.ok) throw new Error(`DuckDB-Wasm chunk unavailable (${response.status})`);
      const bytes = await response.arrayBuffer();
      await assertIntegrity(bytes, part.bytes, part.digest, "DuckDB-Wasm chunk");
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
  await database.instantiate(mainModule);
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
  tableName: string,
): Promise<void> {
  assertTableName(tableName);
  if (registeredTables.has(tableName)) return;
  const table = manifest.runtimeTables.find((row) => row.tableName === tableName);
  if (!table) throw new Error(`Runtime table is not authorised: ${tableName}`);
  const buffers = await Promise.all(
    table.files.map(async (url, index) => {
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
      return {
        name: `${table.tableName}__${index}.parquet`,
        bytes: new Uint8Array(bytes),
      };
    }),
  );

  for (const file of buffers) {
    await database.registerFileBuffer(file.name, file.bytes);
  }
  const fileList = buffers.map((file) => `'${file.name}'`).join(", ");
  await connection.query(
    `create or replace view "${table.tableName}" as select * from read_parquet([${fileList}])`,
  );
  registeredTables.add(tableName);
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
      return { database, connection };
    })().catch((error) => {
      runtimePromise = null;
      registeredTables.clear();
      throw error;
    });
  }
  return runtimePromise;
}

export async function getConnection(): Promise<duckdb.AsyncDuckDBConnection> {
  return (await getRuntime()).connection;
}

async function ensureRuntimeTables(tableNames: string[]): Promise<void> {
  const manifest = await getRuntimeManifest();
  const { database, connection } = await getRuntime();
  for (const tableName of [...new Set(tableNames)]) {
    await registerRuntimeTable(database, connection, manifest, tableName);
  }
}

export async function runQuery<T>(sql: string, tableNames: string[] = []): Promise<T[]> {
  let release: () => void = () => {};
  const previous = queryQueue;
  queryQueue = new Promise<void>((resolve) => {
    release = resolve;
  });
  await previous;
  try {
    await ensureRuntimeTables(tableNames);
    const connection = await getConnection();
    const result = await connection.query(sql);
    return result.toArray().map((row) => {
      const record = row.toJSON() as Record<string, unknown>;
      for (const key of Object.keys(record)) {
        if (typeof record[key] === "bigint") record[key] = Number(record[key]);
      }
      return record as T;
    });
  } finally {
    release();
  }
}
