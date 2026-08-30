# Milestone 5 Slice D1 - React Runtime and CFO Product Shell

Status: Implementation authorised on 2026-08-25

## 0. Objective

Slice D1 turns the verified `Q-FINANCE-C2@v1` React handoff into the first
consumer-owned finance intelligence experience. It restores the strongest
part of the original Atlas product - browser-local analytical execution - over
the deeper statutory and operational finance authority now present in the
Finance & Assurance Platform.

D1 is a consumer implementation. It must not alter, repair, reinterpret or
reseal C2 data.

## 1. Product boundary

D1 provides:

- a React and TypeScript enterprise finance shell;
- DuckDB-Wasm running in a browser worker with no application database;
- same-origin C2 partitioned Parquet and governed metadata;
- a typed query service with explicit minor-unit conversion at presentation;
- a global period, scope, currency and reporting-version context;
- a CFO Command Centre over `mart_executive_cfo_command_center`;
- visible reliability, authority and drill-through metadata;
- a data-status drawer binding the page to the exact C2 and A2.4 digests;
- explicit loading, empty, unavailable and query-failure states; and
- retained links to the existing Hermes, Atlas, Argus, Aegis and Pythia
  evidence journeys.

D1 does not yet provide the full Financial Performance, Cash and Capital,
Revenue and SaaS, or Assurance analytical experiences. Those remain D2-D5.

## 2. Reuse boundary

The original Atlas dashboard is a design and implementation reference, not a
source authority. D1 may reuse its browser-local DuckDB pattern, query-hook
shape, formatting conventions and high-value management-report layout.

It must not reuse:

- old Parquet or CSV extracts;
- proxy operating-profit definitions;
- the generated opening balance sheet;
- the former short GL-close assumption;
- old source names or reporting-scope semantics; or
- any client-side fixture presented as governed truth.

The existing Milestone 3 assurance routes remain available as focused evidence
journeys. The root route becomes the finance intelligence product shell.

## 3. Runtime contract

1. The browser loads `delivery-manifest.json`, `query-catalogue.json` and only
   the Parquet partitions required by the D1 query catalogue.
2. DuckDB-Wasm is instantiated lazily in a dedicated browser worker.
3. Every D1 view is created from same-origin registered C2 Parquet bytes.
4. SQL is selected from a closed query catalogue; UI values never become SQL
   identifiers or unvalidated literals.
5. Money remains integer minor units in Parquet and SQL. Conversion to pounds
   occurs only in the presentation boundary.
6. The default context is the latest delivered group reporting version.
7. Scope and reporting-version selections travel together and are never
   inferred from labels alone.
8. Reliability status, reliability purpose, value authority and source digest
   travel with the visible command-centre result.
9. A runtime row-count replay must equal the C2 control total for every loaded
   D1 table.
10. Consumer failures are visible and must not fall back to invented values.

## 4. D1 data surface

D1 loads three governed tables:

1. `mart_executive_cfo_command_center` - 66 group-period rows;
2. `mart_cfo_metric_readiness` - 11 executive metric controls; and
3. `mart_model_readiness_controls` - 15 model-readiness controls.

The complete 29-table C2 catalogue remains visible as the authorised expansion
surface. Later D slices add tables deliberately rather than downloading the
entire handoff at first render.

## 5. Acceptance

- the root experience is recognisably a Nexus CFO product, not the earlier
  public-product overview;
- DuckDB-Wasm queries the copied C2 Parquet rather than bundled JSON values;
- the period selector exposes all 66 governed monthly actual periods;
- headline metrics reconcile to the selected command-centre row;
- 11/11 executive metrics and 15/15 model controls are shown from validator-
  produced rows;
- the page displays the exact reporting version, purpose-specific reliability,
  value authority and source digest;
- the runtime table populations replay to 66, 11 and 15 rows;
- existing assurance journey routes remain buildable and reachable;
- loading, error and unavailable states are testable; and
- typecheck, lint, build and focused D1 tests pass.
