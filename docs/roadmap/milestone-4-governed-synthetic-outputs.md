# Milestone 4 - Governed Synthetic Outputs

Status: Artifact R Phase R2 complete - Artifact S v0.2 reframed for critique

## 1. Purpose

Milestone 4 creates the governed package and evidence boundary that later
analytical datasets, Excel, and Power BI will share. It does not start by
building either consumer. It first proves that exact export discovery and
Artifact O views can become one deterministic, typed, readiness-aware,
traceable, and reproducible evidence package without adding a second finance or
assurance engine.

Artifact P v0.2 is the ratified package and evidence contract:

`docs/product/governed-synthetic-outputs.md`

## 2. Product Sequence

```text
Milestone 3 runtime and public views
-> Artifact P package and evidence contract
-> verified canonical evidence package
-> evidence-package cohesion audit
-> finite governed analytical-read artifact and registry
-> analytical registry implementation and audit
-> local analytical handoff contract and implementation
-> independently authored React, Excel, and Power BI consumers
-> expanded synthetic operating populations
```

This order is deliberate. Wider synthetic volume, workbooks, and dashboards
must inherit the same version, readiness, evidence, lineage, and module
semantics rather than defining their own extracts.

## 3. Phase 0 - Contract Critique and Ratification

Current.

Phase 0 must:

- verify every proposed P-D field against P-Q00 or the implemented O-V
  contracts;
- prove that P-Q00 is finite structural discovery rather than generic product
  enumeration or a second semantic engine;
- define one package-wide query session with a fresh public reader per O-Q
  invocation;
- close canonical JSON, CSV, checksum, schema, key, and relationship semantics;
- preserve exact-original compatibility, reporting history, purpose-specific
  readiness, evidence status, and directed traceability;
- retain the deferral of journal lines, source populations, account dimensions,
  and other analytical grains to a separately ratified governed analytical
  registry;
- prove C-001 and CT-1 without filling scope-correct absences; and
- record the ratified boundary through an append-only ADR.

No export implementation starts while a proposed dataset requires an
unpublished source field or consumer-side semantic inference.

## 4. Phase 1 - Canonical Package Contracts

Planned after ratification.

- strict request, result, manifest, dataset-schema, relationship, and
  verification values;
- finite `P-EVIDENCE@v1` registry, exact column order, column provenance, export
  stewardship, and semantic ownership;
- deterministic row identity and ordering;
- explicit canonical JSON and CSV serializers;
- checksum-ledger and detached package-digest rules;
- positive fixtures and boundary-negative tests; and
- no query execution, HTTP route, workbook, or BI model yet.

## 5. Phase 2 - Revision-Pinned Export Assembly

Planned after Phase 1.

- one read-only runtime query session shared by P-Q00 and all O-Q invocations;
- a fresh invocation-local reader for every O-Q result;
- lossless P-Q00/O-Q/O-V to P-D tabularisation;
- exact-original and snapshot-coordinate enforcement;
- exact full-scenario-set enforcement and deterministic row construction;
- P-C01 atomic build through a verified staging directory;
- canonical C-001 and CT-1 output packages; and
- no SQLite, fixture, HTTP-scraping, or web-component dependency.

## 6. Mandatory Post-Phase-2 Evidence Cohesion Audit

Before any governed analytical registry or consumer, perform a hard audit of:

- field-by-field source authority;
- absence of new domain calculations or inferred statuses;
- immutable reporting versions and copied restatement bridges;
- purpose-specific readiness and exact decision-input binding;
- declaration-only versus content-verified evidence wording;
- unchanged J-P11 edge direction and node identity;
- module ownership and cross-module references;
- schema, relationship, digest, and package-snapshot closure;
- byte reproducibility and offline operation;
- C-001/CT-1 parity with Artifact O; and
- P-Q00 parameterisation across non-canonical C-001/CT-1 identities; and
- unchanged Milestone 1 through 3 acceptance results.

An audit failure returns Milestone 4 to the contract or assembler phase that
owns the defect. It does not author a workbook workaround.

## 7. Phase 3 - Verification and Milestone Closure

Planned after the audit.

- P-C02 full offline verification;
- P-C03 exact-query-revision reproduction;
- tamper, missing-file, unknown-file, collision, relationship, and atomicity
  tests;
- clean-checkout package reproduction;
- one machine-readable Milestone 4 acceptance report; and
- one documented package walkthrough suitable for portfolio review.

## 8. Governed Analytical Registry

The evidence-package boundary does not by itself authorise Excel or Power BI.
After Artifact P is implemented and audited, the next bounded architecture
artifact must define a finite governed analytical-read registry over the same
runtime query session.

Its first use cases should determine the minimum exact grains, expected to
include:

- journal headers and immutable journal lines;
- reporting facts and reporting-version identity;
- account attributes required for statement and control-account analysis;
- source business objects needed for reconciliation and audit drill-through;
- purpose-specific readiness and evidence bindings; and
- stable dimensions required by both Excel and Power BI.

The artifact may not expose generic J-AR records, SQLite tables, or a warehouse
merely because downstream tools prefer tabular data. It must define explicit
governed products with ownership, versions, lineage, keys, and intended uses.

## 9. Consumer Handoff

Only after the analytical registry and model-digestion layer are ratified,
implemented, and audited should Artifact S define a local analytical handoff.
That handoff provides complete LINEAGE CSV and Parquet, a rebuildable DuckDB
query layer, a data-only XLSX pack, tool-neutral modelling metadata, and
reconciliation SQL.

It does not build a React dashboard, Excel financial model, Power BI semantic
model, DAX, report, forecast, or valuation. Those are independently authored
portfolio workstreams. Their shared governed values reconcile to the same
handoff snapshot; their presentation and consumer-owned analysis need not be
identical.

## 10. Current Gate

Phases 0 through 4 are complete under ADR-035 through ADR-037. The implemented
`P-EVIDENCE@v1` boundary passes all forty-five Artifact P criteria, offline
verification, exact reproduction, dependency review, C-001/CT-1 parity, and the
mandatory cohesion audit documented in
`docs/roadmap/milestone-4-post-evidence-package-cohesion-audit.md`.

Phase 4 is complete. Artifact Q v0.2 closes the finite
`Q-ANALYTICS@v1` governed analytical-read registry, its exact ledger-semantics
and period prerequisites, sixteen datasets, the closed P-plus-Q package
extension, and relationship contract v2 for the first Excel and Power BI use
cases. The v0.2 assessment closes all nine bounded v0.1 blockers and judges the
artifact ratifiable. ADR-037 ratifies that boundary. The bounded implementation
and multi-registry cohesion audit now pass, as recorded in
`docs/roadmap/milestone-4-post-analytical-registry-cohesion-audit.md`.

The Phase 4 sequence is:

1. preserve the exact configuration, query, dataset, manifest, and relationship
   boundaries during implementation;
2. implement Q through the ordinary runtime and the existing Artifact P package
   service;
3. execute a multi-registry cohesion audit; and
4. begin the local analytical handoff artifact only after that audit passes.

All four steps are complete. Artifact R defines the proposed shared model-
digestion boundary between the verified P-plus-Q package and every local
consumer. Its independent v0.1 field-by-field critique records eight bounded
blockers in `docs/roadmap/milestone-4-artifact-r-v01-critique.md`. Artifact R
v0.2 incorporates all eight blockers and seven tightening items. The repeated
structural and semantic audit passes and is recorded in
`docs/roadmap/milestone-4-artifact-r-v02-assessment.md`. Artifact R v0.2 is
ratified through ADR-038. Phase R1 now
passes its cohesion audit in
`docs/roadmap/milestone-4-post-r1-cohesion-audit.md`; ADR-039 records that
implementation result. Bounded Phase R2 materialization and its cohesion audit
are complete; ADR-041 records the result. Phase R3 DuckDB acceleration and its
cohesion audit are also complete; ADR-042 records the result.

The current sequence is:

1. critique Artifact R against all thirty-seven implemented P/Q datasets and
   relationship v2: complete;
2. resolve its profile, physical-type, relationship, and measure questions:
   complete in v0.2;
3. repeat the structural and semantic assessment: complete and passed;
4. ratify R through append-only ADR-038: complete;
5. implement strict Phase R1 contracts, registries, writer binding, fixtures,
   and the post-R1 cohesion audit: complete;
6. implement bounded Phase R2 Parquet and semantic materialization: complete;
7. execute the mandatory post-R2 cohesion audit: complete;
8. draft the first local analytical handoff contract over that verified
   boundary: complete as Artifact S v0.2;
9. execute the Artifact S v0.2 hard critique: complete with eight bounded
   blockers;
10. revise Artifact S as v0.3 following the bounded correction sequence:
    complete;
11. repeat the Artifact S structural and semantic assessment: complete with
    five bounded blockers; and
12. implement and audit Artifact R Phase R3: complete;
13. revise Artifact S as v0.4 after closing the R3 boundary: complete;
14. reassess Artifact S v0.4 before ratification: complete with four bounded
    blockers;
15. revise Artifact S as v0.5 following the bounded correction sequence:
    complete;
16. independently reassess Artifact S v0.5 before ratification: complete with
    three bounded blockers; and
17. revise Artifact S as v0.6 following the bounded correction sequence:
    complete; and
18. independently reassess Artifact S v0.6 before ratification: complete with
    one bounded blocker; and
19. revise Artifact S as v0.7 following the bounded correction sequence:
    complete; and
20. independently reassess Artifact S v0.7 before ratification: complete; and
21. ratify Artifact S v0.7 through append-only ADR-043: complete; and
22. implement bounded Phase S1 contracts, profiles, authorities, failure
    admissions, and negative-fixture machinery: in progress; and
23. execute the private-copy mutation and metadata-construction authority
    audit: complete with two bounded blockers requiring v0.8; and
24. complete the bounded v0.8 executable-authority correction: complete;
    and
25. independently reassess Artifact S v0.8: complete with three bounded
    blockers requiring v0.9.

Until the handoff implementation passes its later phase gates:

- no `.xlsx`, `.pbix`, or `.pbip` is authored;
- no synthetic population is widened merely to fill a chart;
- no export reads SQLite or runtime repositories directly; and
- no package or consumer is described as governed merely because it has a
  checksum.

Artifact S v0.12 is the current correction candidate; v0.11 is the current
assessed design boundary and v0.7 remains the latest ratified handoff boundary
until a later correction passes reassessment:

`docs/product/local-analytical-handoff.md`

It defines one complete LINEAGE-backed local handoff containing canonical CSV,
typed Parquet, a rebuildable DuckDB warehouse, a data-only XLSX pack,
tool-neutral modelling metadata, and validation SQL. It explicitly withholds
React dashboards, Excel financial models, Power BI semantic models, DAX, and
visuals so those remain independently authored portfolio work. It is a design
draft, not implementation authority. The next action is its hard
field-by-field and format-by-format critique.
