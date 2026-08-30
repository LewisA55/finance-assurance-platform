# Public v0.1 architecture

## Product thesis

The platform models a single finance process, not five disconnected applications.
Independent source events pass through ingestion, accounting, assurance and
planning boundaries before they become consumer-facing analysis.

## Module ownership

| Lens | Owns | Does not own |
|---|---|---|
| Hermes | immutable source identity, admission, quarantine, duplicate and late-arrival state, lineage | financial interpretation |
| Atlas | posting rules, journals, subledgers, trial balances, reporting versions and financial statements | source mutation or scenario overlays |
| Argus | executed controls, exceptions, materiality and reproducible evidence | reviewed findings or remediation authority |
| Aegis | findings, issues, owners, evidence, approvals, remediation and readiness | silent source correction |
| Pythia | scenario assumptions, integrated forecasts, liquidity and valuation gates | rewriting approved actuals |

## Finance data path

```text
source event
  -> Hermes admission
  -> accounting rule
  -> proposed journal
  -> immutable posted journal
  -> subledger and trial balance
  -> reporting version
  -> reconciled statements and management marts
  -> Argus/Aegis assurance state
  -> governed analytical handoff
  -> React, Excel and Power BI products
```

`business_event` is the only object class that can drive posting-rule evaluation.
Posting, reversal, restatement and publication are accounting lifecycle events
with their own governance significance. A hard-closed period is corrected through
reversal or restatement rather than silent mutation.

## Analytical layers

- Bronze retains independent physical source-system records and admission evidence.
- Silver provides typed, source-oriented views without creating management conclusions.
- Gold publishes conformed dimensions, facts, statements, rollforwards,
  reconciliations and governed consumer marts.
- C2 materialises the same governed facts into consumer-appropriate physical formats.
- Pythia consumes the approved C2/Atlas snapshot and publishes a separate model authority.

## React runtime boundary

The browser receives a small versioned runtime package containing JSON warm
snapshots, Parquet partitions, relationship/query metadata and exact digests. It
assembles the pinned DuckDB-Wasm module locally, verifies the SHA-256 digest of
every module chunk and Parquet file, then registers only the tables required for
the current query.

The browser has no application database and does not recreate accounting,
assurance, forecasting or valuation authority.

## Consumer boundary

- React explains governed actuals, controls and Pythia consequences through local analytical queries.
- Excel v0.2 will own authored three-statement and DCF mechanics over the same governed handoff.
- Power BI v0.3 will own the semantic model, calculation groups, security and distributed report experiences.

This separation demonstrates both governed data-product engineering and
purpose-built analytical product construction.
