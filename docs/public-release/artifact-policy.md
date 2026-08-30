# Public artifact policy

## Tracked source authority

The repository tracks Python source, dbt SQL, schemas, tests, architecture and
product contracts, React source and lockfile, the project-owned social preview,
and the compact v0.1 React runtime under `web/public/finance-data/`.

The React runtime is a deliberately versioned release fixture. It contains about
2.6 MB of compressed Parquet and JSON, binds the published C2 and Pythia digests,
and allows a fresh clone to build the flagship product without committing the
complete warehouse.

## Generated and local-only artifacts

The following are excluded from Git:

- `build/`, `outputs/`, dbt `target/` and local test caches;
- raw/Bronze populations, DuckDB warehouses and general Parquet exports;
- DuckDB-Wasm chunks under `web/public/duckdb/`, rebuilt from the pinned npm package;
- XLSX, PBIX and other consumer binaries;
- local consumer-product workspaces (`consumer-products/*/work/`), cover
  mock-ups and private review notes; and
- environment files, credentials and machine-specific paths.

Excel and Power BI binaries will be attached to their own tagged releases when
those products are complete. Their reproducible source, model metadata and
validation evidence should remain in Git where practical.

The tracked [consumer-products workspace](../../consumer-products/README.md)
separates future model documentation and text-based source from local desktop
authoring and release binaries.

## Size limits

No tracked file should exceed 25 MB without an explicit architecture decision.
Large governed packages belong in release assets or reproducible local build
directories, not ordinary Git history.

## Integrity

The public-release checker rejects forbidden paths, unexpected binary formats,
personal absolute paths, common credential signatures and oversized files. It
also replays the byte length and SHA-256 digest of every tracked browser Parquet
partition against `runtime-manifest.json`.
