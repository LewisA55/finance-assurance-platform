# Finance intelligence web product

The `web/` directory contains the React/vinext product for the public v0.1
Finance & Assurance Platform release.

Its primary routes are:

- `/` - CFO command centre
- `/financial-performance`
- `/cash-capital`
- `/revenue-saas`
- `/assurance`
- `/planning-valuation`
- `/product-guide`

The repository also retains finite evidence journeys for reporting lineage,
reconciliation, exceptions, remediation, readiness and governed decisions.

## Runtime contract

The finance routes use DuckDB-Wasm to query governed Parquet in the browser.
There is no application database. The client authenticates each Parquet file
and DuckDB-Wasm chunk against the versioned runtime manifest before query
registration.

`public/finance-data/` is the compact v0.1 release fixture. It binds the exact
C2 actuals delivery and Pythia model-run authority. `public/duckdb/` is generated
from the pinned npm dependency and is not tracked.

## Local development

```bash
npm ci
npm run dev
```

For the complete product, including the read-only assurance API, run from the
repository root:

```bash
uv run --locked python public_product.py serve
```

## Regenerating the browser package

Only run this after reconstructing or verifying the exact C2 and Pythia
packages under the root `build/` directory:

```bash
npm run sync:finance-data
```

Ordinary development and CI use `npm run prepare:duckdb`; they do not require
the untracked full warehouse.

## Validation

```bash
npm run lint
npm run typecheck
npm run prepare:duckdb
npm run test:finance
npm test
```

All data is synthetic. The interface is demonstrative and does not publish an
audit opinion or investment recommendation.
