# Milestone 2 Post-Phase 6 Cohesion Audit

Status: Passed - F1 through F6 resolved and re-audited 2026-08-09

## 1. Audit Question

Do the persisted read models and end-to-end traceability implementation preserve
Artifacts C through N, the five platform invariants, the complete Artifact I
command/query boundary, and the atomic Artifact G handoffs required by C-001
and CT-1?

Original verdict: no. At audited revision `8abbd48`, the implementation remained
structurally disciplined and all 112 existing tests passed, but six ratified
obligations were bypassable or absent. The findings below preserve that
historical audit result.

Follow-up verdict 2026-08-09: yes. F1 through F6 now execute through the ordinary
runtime boundary, Ruff passes, all 126 tests pass, and H0-H7 plus H3 guard
validation pass. Phase 7 is unblocked.

This audit changes no ratified architecture and makes no runtime correction. It
records the difference between a green implemented test suite and complete
conformance to the ratified contracts.

Remediation progress: F1 and F2 were resolved by the bounded pass documented in
`docs/roadmap/milestone-2-phase6-remediation-f1-f2.md`; F6 was resolved by
`docs/roadmap/milestone-2-phase6-remediation-f6.md`; F3 and F4 were resolved by
`docs/roadmap/milestone-2-phase6-remediation-f3-f4.md`; F5 was resolved by
`docs/roadmap/milestone-2-phase6-remediation-f5.md`. Their findings below remain
as the historical audit record. The follow-up audit found no remaining blocker.

Remediation progress: F1 and F2 were resolved by the bounded pass documented in
`docs/roadmap/milestone-2-phase6-remediation-f1-f2.md`. Their findings below
remain as the historical audit record. F3 through F6 still block Phase 7.

## 2. Blocking Findings

### F1 - Semantic availability is recorded but not enforced on reads

Artifacts J and K require every normal query, load, projection, trace, and
planner read to hide a record until `available_from <= semantic_as_of_time`.

`RuntimeQueryService` opens a query with a semantic time, but the query session
does not retain or apply that time when returning exact records or deriving
read models. An exact record can therefore be observed before its semantic
availability. The required K-T05 before/after-availability proof is absent.

Required resolution:

- carry the immutable semantic query context into both adapters;
- filter exact authority before any count, lookup, projection, trace, or
  controlled downstream read can observe it;
- prove identical before/at/after-boundary behavior in memory and SQLite; and
- prove a pinned session does not change its semantic horizon after opening.

### F2 - Pre-scope import does not validate its hard-close and time boundary

Artifacts J and K require the predecessor reporting import to resolve the exact
hard-close state and close-event/view binding, verify content and ordering, and
respect its declared availability.

The SQLite import path currently checks only that prerequisite references are
non-empty and that the admitted family set and identities are permitted. It
does not resolve the exact hard-close authority, compare the declared view
hash, or validate the import/availability ordering. The Phase 6 C-001 test
imports the predecessor while the initial June period is still `SOFT_CLOSED`
and before the workflow executes its hard-close transition. The test passing is
direct evidence that K-T28 and K-A24 are not implemented.

Required resolution:

- resolve and verify the prerequisite J-AR06 hard-close event and J-P04 view;
- reject an import before the exact hard-close state exists;
- enforce import time, publication time, and `available_from` ordering;
- verify the predecessor content/hash binding required by the import contract;
  and
- reorder the persisted C-001 proof so import occurs only after the ratified
  prerequisite state exists.

### F3 - J-P11 guesses through ambiguous references and traverses both ways

Artifacts I and J define a source-directed statement trace rebuilt from exact
immutable upstream references. Broken or ambiguous authoritative bindings must
fail rather than be guessed.

The current graph builder resolves a reference only when exactly one alias
matches. Both zero matches and multiple matches become an `EXTERNAL` node, so
an ambiguity is silently downgraded to an unresolved external reference. It
also inserts every edge in both directions and returns the entire connected
component. A statement-to-source trace can therefore include downstream
consumers or sibling records rather than one directed authority chain.

The Phase 6 proof checks only that expected role labels appear; it does not
prove a directed path or exclude unrelated descendants.

Required resolution:

- distinguish a permitted unresolved external reference from an ambiguous
  authoritative match;
- fail graph construction on ambiguous or broken internal bindings;
- retain edge direction and expose the bounded upstream traversal required by
  I-Q20;
- prove the ordered reporting-to-source path and absence of downstream/sibling
  contamination; and
- retain rebuild/restart digest parity after the semantic correction.

Resolution 2026-08-09: complete. J-P11 now follows only typed upstream
authority edges. Broken internal bindings fail, ambiguous typed aliases fail,
and only declared evidence, authority, and source references may terminate as
external leaves. The canonical trace proves the ordered reporting-to-source
reachability, excludes an unrelated downstream consumer, and preserves its
digest across rebuild and restart. See
`docs/roadmap/milestone-2-phase6-remediation-f3-f4.md`.

### F4 - The finite Artifact I query boundary is incomplete

Phase 6 claims the finite Artifact I query boundary, but three ratified query
semantics are not available:

- I-Q05 requires an exact immutable accounting-period version or an explicitly
  labelled current projection; only current is exposed;
- I-Q06 requires exact proposal treatment plus lifecycle evidence without
  implicit latest resolution; the current query returns treatment plus current
  status only; and
- I-Q11 requires a restatement-case view at a named state token with scope,
  linked journals, manifest, and publication state; only the current projection
  is exposed.

Required resolution:

- implement the missing exact/as-of result shapes through the shared query
  port;
- make exact and labelled-current operations unambiguous at the method
  boundary;
- add in-memory/SQLite parity tests for each form; and
- narrow the Phase 6 completion claim if any ratified query is deliberately
  deferred rather than silently omitted.

Resolution 2026-08-09: complete. I-Q05, I-Q06, and I-Q11 now expose separately
named exact and labelled-current operations. Exact reads require accounting
event tokens and return exact G-04 bodies plus ordered lifecycle evidence;
current reads expose state labels separately from authority tokens. In-memory
and SQLite semantics match. See
`docs/roadmap/milestone-2-phase6-remediation-f3-f4.md`.

### F5 - J-AR01 candidate receipt has no producer path

Artifact I makes the source-substrate candidate receipt part of I-S01 and
exposes it through I-Q01. The runtime currently has a candidate-receipt query
but no command or admission path that creates J-AR01. The finite query is
therefore dead and the first canonical execution step is incomplete.

Required resolution:

- add the ratified source-substrate producer through an existing Artifact K
  mode and ordinary ownership boundary;
- preserve the business-event/accounting-event firewall;
- prove accepted and rejected candidate handling without a direct repository
  mutation; and
- prove I-Q01 after restart and rebuild where applicable.

Resolution 2026-08-09: complete. Ordinary I-C01 now atomically commits replayable
J-AR01 custody, the Hermes admission product, exact G-02, and J-AR14. Outcome is
derived from the finite supported-event registry; rejected and unsupported
candidates retain custody but cannot cross into J-AR03/G-01. I-Q01 returns the
exact receipt, admission result, publication, disposition, and eligibility and
survives retry, restart, and rebuild. Shared adapter invariants reject partial or
inconsistent candidate/admission sets. See
`docs/roadmap/milestone-2-phase6-remediation-f5.md`.

### F6 - Required Artifact G publication closure is caller-optional

Artifact I includes Atlas G-04/G-05/G-06 publications in the atomic write sets
for the accounting lifecycle, including I-S20. The application service only
validates and observes publications when a `ModuleContractService` was supplied
and the caller happened to include publication objects in the event bundle.
The accounting command otherwise commits normally.

The ordinary persisted Phase 6 C-001 test uses no module-contract service and
publishes the v2 reporting version without its required atomic G-06
publication. A separate test proves that selected publications can share a
commit, but it does not make the closure mandatory for every ordinary path.

Required resolution:

- make the exact required G publication set a command-owned closure invariant,
  not optional constructor wiring;
- reject missing, extra, or mismatched required publications before commit;
- ensure the post-commit observation sink remains non-authoritative and cannot
  determine success;
- replay every C-001 and CT-1 accounting transition with its required G-04,
  G-05, and G-06 publications where applicable; and
- prove the same closure after restart and projection rebuild.

Resolution 2026-08-09: complete. The Atlas accounting application service now
owns and validates the finite publication matrix before every accounting-event
commit. C-001 atomically commits twenty-four required G records and CT-1
commits fourteen. Missing, extra, and mismatched closure inputs leave the target
command's digest and revision unchanged; restart and rebuild preserve the exact
publication identities. Post-commit observations remain optional and
non-authoritative. The executable proof and scope guard are recorded in
`docs/roadmap/milestone-2-phase6-remediation-f6.md`.

## 3. Non-Blocking Hardening Items

### H1 - Controlled-planning reads should resolve publication authority

The controlled-planning query correctly requires exact matching G-11,
readiness, reporting-version, purpose, period, scope, and approved status. Its
positive test constructs module products directly without the named G-06 and
G-10 J-AR13 publications. Write-time contract validation protects ordinary
commands, but resolving those exact publication references at read time would
make the reliance proof self-contained and resistant to malformed admitted
state.

### H2 - Trace tests should assert paths, not only role membership

Even after F3 is corrected, the canonical proof should assert the ordered node
and field-edge sequence for the GBP 10,000 June revenue value. A set of expected
roles can pass when the graph contains the right types for the wrong reason.

### H3 - Phase 6 status wording should distinguish implementation from gate

The Phase 6 implementation record may remain historically complete, but it
must link to this audit and state that post-phase conformance is blocked. The
README and master roadmap must not imply that green tests are equivalent to
Phase 7 readiness.

## 4. Cohesion Checks That Passed

| Boundary | Audit result |
|---|---|
| Event firewall | Runtime code still permits only G-01 business events to reach posting-rule evaluation; accounting events and G publications do not recurse. |
| Accounting integrity | Balanced journal construction, immutable posted records, reversal/restatement separation, and independent ledger checks remain intact. |
| Persistence topology | One SQLite database and one Artifact K boundary remain; no module-owned repository or hidden write path was found. |
| Transaction/idempotency | Command results and effect claims remain distinct, durable, and restart-safe on the tested paths. |
| Projection disposition | J-P02/J-P04/J-P06 remain rebuildable conveniences rather than authority. |
| G-13 non-authorship | J-010 remains referenced J-AR17/G-13 state and is not rewritten as an Artifact F journal. |
| Evidence wording | Verified reporting bytes remain distinct from declared-hash-only evidence. |
| Runtime independence | `finance_assurance.runtime` imports no Milestone 1 validation module. |
| Scope | No API, UI, authentication, tenancy, broker, distributed worker, or expanded process taxonomy entered Phase 6. |
| Existing regression suite | Ruff was clean and all 112 tests passed at the audited revision `8abbd48`; those tests are insufficient to discharge F1 through F6. |

## 5. Remediation Sequence

The blockers should be corrected in dependency order:

1. enforce semantic time and pre-scope import prerequisites (F1, F2);
2. make Artifact G publication closure mandatory in the ordinary unit of work
   (F6);
3. complete exact/as-of query semantics and directed J-P11 traversal (F4, F3);
4. complete the source-substrate candidate-receipt path (F5);
5. replay parameterised C-001 and CT-1 through only those ordinary paths; and
6. rerun Ruff, the complete test suite, restart/rebuild comparison, H0-H7, and
   this cohesion audit.

Fixes must not add a second dispatcher, repository, workflow framework, or
scenario-literal branch.

## 6. Phase 7 Entry Gate

Phase 7 may begin only when:

- F1 through F6 have executable regression tests and pass in both adapters
  where the contract applies;
- the ordinary persisted C-001 and CT-1 proofs no longer use a bypass that the
  ratified application boundary forbids;
- the Phase 6 status record lists the corrected proof set;
- the full suite remains green after clean start, restart, and rebuild; and
- a follow-up audit records no remaining blocking contradiction across
  Artifacts C through N, code, tests, migrations, and current-status prose.

No ADR is required for this audit because it resolves no architecture choice.
Any remediation that changes a ratified contract rather than implementing it
must stop and enter the append-only decision process first.

Follow-up result 2026-08-09: every entry condition above passes. No second
dispatcher, repository, workflow framework, event taxonomy, or architecture
decision was introduced. Phase 7 may begin.
