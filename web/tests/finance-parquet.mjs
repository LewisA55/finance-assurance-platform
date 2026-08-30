import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { asyncBufferFromFile, parquetReadObjects } from "hyparquet";
import { compressors } from "hyparquet-compressors";

const webRoot = resolve(import.meta.dirname, "..");
const manifest = JSON.parse(
  readFileSync(resolve(webRoot, "public", "finance-data", "runtime-manifest.json"), "utf8"),
);
const tableCache = new Map();

export function readRuntimeTable(tableName) {
  if (!tableCache.has(tableName)) {
    tableCache.set(
      tableName,
      (async () => {
        const table = manifest.runtimeTables.find((item) => item.tableName === tableName);
        if (!table) throw new Error(`Runtime table is not authorised: ${tableName}`);
        const partitions = await Promise.all(
          table.files.map(async (url) => {
            const file = await asyncBufferFromFile(resolve(webRoot, "public", url.slice(1)));
            return parquetReadObjects({ file, compressors });
          }),
        );
        const rows = partitions.flat();
        if (rows.length !== table.expectedRows) {
          throw new Error(
            `${tableName} expected ${table.expectedRows} rows but decoded ${rows.length}`,
          );
        }
        return rows;
      })(),
    );
  }
  return tableCache.get(tableName);
}
