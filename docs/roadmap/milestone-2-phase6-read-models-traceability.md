# Milestone 2 Phase 6: Read Models and End-to-End Traceability

Status: Complete - follow-up cohesion audit passed 2026-08-09

## 1. Outcome

The runtime now exposes the finite Artifact I query boundary as programmatic
read models over one revision-pinned Artifact K query session. Exact immutable
versions, rebuildable current projections, reporting content, controlled
planning inputs, and reporting-value lineage all read through the shared
persistence port. No query imports SQLite, reads a physical table directly,
or treats J-P13 observations as authority.

Phase 6 adds no HTTP or GraphQL API, dashboard, UI, authentication, generic
search service, or module-owned repository.

## 2. Exact and Current Semantics

`ExactVersionRead` returns one J-AR family, permanent identity, semantic hash,
canonical payload, and pinned revision. The query port exposes the same exact
record stream in memory and through SQLite, including independently durable
J-AR15 effect claims and sealed administrative records.

`LabelledCurrentProjection` is deliberately separate. It always carries:

- `label = CURRENT_REBUILDABLE`;
- the J-P02, J-P04, or J-P06 projection family;
- subject type and identity;
- exactness token; and
- projection hash.

No `Get*` method silently resolves a family to its latest version. Reporting
predecessor and successor versions remain independent J-AR10 reads.

## 3. Revision Pinning

SQLite materializes the exact semantic record set while the query session is
opened under the boundary lock. Later commits do not leak into a session whose
revision has already been advertised. The in-memory adapter provides the same
pinned behavior over its immutable state value.

The query service holds one session for its lifetime, so a controlled planning
read cannot resolve its planning input at one revision and readiness at a later
revision.

## 4. Reporting Content and Evidence Claims

`ReportingContentRecord` is the runtime J-AR12 representation of the already
ratified June reporting proof body. It does not add an event or business-object
type. It permits the runtime to prove the same bounded content bytes and
SHA-256 claim that Artifact H already verifies.

Content resolution reports one of two explicit statuses:

- `CONTENT_BYTES_VERIFIED` when committed canonical bytes reproduce the
  reporting version's declared content hash; or
- `DECLARED_HASH_ONLY` when only the reference and declared hash exist.

It never upgrades the second case to content verification. A statement-value
trace requires verified bytes and an integer-minor statement field.

## 5. End-to-End Trace Graph

J-P11 is rebuilt from immutable semantic references in the pinned exact-record
stream. For the corrected June subscription-revenue value, the graph traverses
the connected authority chain through:

```text
verified reporting content
-> exact reporting version
-> publication accounting event
-> restatement and journal references
-> immutable journal and ordered lines
-> exact proposal treatment
-> predecessor automated proposal
-> exact posting-rule version
-> admitted business event
-> source record/system references
-> evidence references
```

Edges retain their declaring field path. Unresolved source and evidence
references are labelled external nodes rather than fabricated authoritative
records. Removing J-P13 observations cannot change the graph or its semantic
digest.

## 6. Purpose-Specific Readiness

The controlled planning query resolves one exact G-11 J-AR02 product, then
requires the exact readiness identity named by it to match:

- reporting-version identity;
- purpose;
- accounting period;
- scope; and
- `APPROVED` status.

An approved readiness record for the predecessor reporting version is
insufficient. The query fails rather than inferring readiness from G-06, from
version order, or from another purpose.

## 7. Implementation Findings Corrected

Phase 6 found and corrected three read-boundary defects before closure:

1. the in-memory identity resolver checked `journal_id` before
   `journal_line_id`, collapsing a header and its lines for exact reads;
2. business-event and posting-rule permanent identities were absent from both
   adapter identity precedence lists; and
3. a SQLite query session originally read the live exact-record table after
   opening, which could expose records newer than its pinned revision.

The adapters now share the same permanent-identity precedence, reporting
content has a distinct content identity, and SQLite snapshots exact records at
query-session creation.

## 8. Executable Proofs

The Phase 6 tests prove:

- a query session cannot observe a later committed business event;
- C-001 June v1 and v2 remain independently retrievable after restart;
- both committed content bodies verify, and the v2 subscription-revenue value
  resolves to GBP 1,000,000 minor units;
- the C-001 statement trace contains reporting version, journal, proposal,
  posting rule, business event, source, and evidence roles;
- the trace semantic digest is identical before rebuild, after rebuild, and
  after process restart;
- C-001 and CT-1 exact proposal/journal reads remain distinct from their
  labelled current projections; and
- controlled planning refuses predecessor readiness and succeeds only with
  the exact v2 readiness version.

Ruff passes. All 112 tests pass, including the unchanged H0 through H7 suite.

## 9. Scope Guard and Next Gate

Phase 6 remains a bounded read layer. Generic reporting marts, dashboard
queries, access control, tenancy, public endpoints, and expanded business
processes remain deferred.

The roadmap-required post-Phase-6 cohesion audit is the next gate. It must
reconcile Artifacts C through N, schema and migration behavior, exact-query
semantics, J-P11 reconstruction, evidence wording, executed G traces, tests,
roadmap status, and public documentation before Phase 7 closes Milestone 2.

That audit is recorded in
`docs/roadmap/milestone-2-post-phase6-cohesion-audit.md`. It found six blocking
conformance gaps. Phase 7 must not begin until they are corrected and the
follow-up gate passes.

The bounded F1/F2 correction is recorded in
`docs/roadmap/milestone-2-phase6-remediation-f1-f2.md`; mandatory Artifact G
publication closure is recorded in
`docs/roadmap/milestone-2-phase6-remediation-f6.md`. Semantic availability,
pre-scope import prerequisites, atomic G-04/G-05/G-06 closure, exact/as-of
lifecycle reads, and directed strict J-P11 traversal now have executable
coverage. The F3/F4 pass is recorded in
`docs/roadmap/milestone-2-phase6-remediation-f3-f4.md`; ordinary candidate
custody and I-Q01 closure are recorded in
`docs/roadmap/milestone-2-phase6-remediation-f5.md`. The follow-up audit passes
and Phase 7 is unblocked.

The bounded F1/F2 correction is recorded in
`docs/roadmap/milestone-2-phase6-remediation-f1-f2.md`. Semantic availability
and pre-scope import prerequisites now have executable coverage; F3 through F6
remain blocking.

That audit is recorded in
`docs/roadmap/milestone-2-post-phase6-cohesion-audit.md`. It found six blocking
conformance gaps. Phase 7 must not begin until they are corrected and the
follow-up gate passes.
