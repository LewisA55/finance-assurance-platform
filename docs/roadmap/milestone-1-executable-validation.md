# Milestone 1: Executable Validation Harness

Status: Complete 2026-08-02 - H0 through H7 passing

## 1. Objective

Milestone 1 turns the ratified Artifact H v0.3 specification, clarified as the
current v0.3.1 baseline, into a deterministic in-process validation harness.

The harness must:

- load the six canonical fixture files without modifying them;
- enforce Artifact F payload boundaries;
- prove the H0-H7 test layers in dependency order;
- replay C-001 and CT-1 exactly;
- produce a machine-readable and human-readable assertion report;
- return a non-zero exit code for any failure or blocked assertion; and
- reproduce the same semantic result from two fresh runs.

This milestone implements the ratified design. It does not reopen the object
model, add event types, introduce a database, or build module applications.

## 2. Binding design sources

Implementation is governed by:

- Artifact C - Accounting Object Model;
- Artifact E - Accounting State Machines and Command/Event Matrix;
- Artifact F v0.2.1 - Minimum Payload Contracts;
- Artifact G v0.2 - Module Ownership and Contract Map;
- Artifact H v0.3.1 - Executable Validation Harness Specification;
- canonical transactions C-001 and CT-1;
- ADR-017, which ratified Artifact H and closed Milestone 0; and
- executable backlog items F-EXE-001 and F-EXE-002.

Where this roadmap conflicts with a ratified artifact, the artifact wins.
Implementation must stop and surface the conflict rather than compensate with
special-case code.

## 3. Locked implementation approach

These are reversible implementation choices, not platform architecture
decisions:

- Python 3.13;
- `uv` for project management and a locked dependency graph;
- Pydantic v2 at the external payload boundary only;
- pytest with importlib import mode for component and acceptance tests;
- a `src` package layout;
- standard-library JSON and hashing primitives for canonical serialization;
- Ruff for static checks and formatting; and
- one clean-checkout entry command:

```text
uv run --locked python -m finance_assurance.validation
```

Installing the runtime tooling and creating the executable scaffold belong to
the first implementation commit, not this documentation change.

## 4. Implementation invariants

### 4.1 One canonical serializer

Canonical serialization is explicit platform code. It must not delegate byte
ordering to Pydantic, model declaration order, or a test helper.

It must:

- encode UTF-8;
- sort object keys lexically and recursively;
- preserve array order;
- use compact JSON separators;
- reject non-JSON numeric values;
- never coerce floats into integer money;
- produce the exact byte form used by hashing and byte-equivalence tests; and
- keep JSONL record boundaries outside the canonical payload bytes.

### 4.2 Two immutable corpus indices

Corpus state has two named forms:

```text
RawCorpusIndex
    -> strict contract validation
ValidatedCorpusIndex
```

`RawCorpusIndex` contains parsed JSON values and supports H0 inventory,
uniqueness, and corpus-integrity checks.

`ValidatedCorpusIndex` is a new immutable value constructed only after all
relevant H1 contract checks pass. It contains validated discriminants,
references, money fields, and frozen payload models. H2 and every later layer
consume this index.

The raw index is never upgraded or mutated in place.

### 4.3 One guard implementation

All transition guards live in a pure planner:

```text
plan(command, immutable_state) -> TransitionPlan | Rejection
```

The planner performs precondition checks and prepares an explicit transition.
It does not mutate stores, append events, or register effects.

Stateful execution later commits the exact `TransitionPlan` returned by this
planner. There must not be a second implementation of the guard rules in the
dispatcher or stores.

### 4.4 H3 closes in two parts

H3 contains two distinct claims:

1. **Guard correctness** - the planner returns the required rejection and
   stable reason for every prohibited transition. This closes in Phase 4.
2. **No-mutation proof** - rejected commands leave object versions, lifecycle
   projections, the event log, journal store, reporting-version store, and
   effect registry unchanged. This closes in Phase 5 after those stores exist.

H3 must not be reported as fully passing after Phase 4.

### 4.5 Strict wire contracts, independent internal types

Pydantic models must be strict, frozen, discriminated, and configured to
forbid unknown fields. They validate Artifact F wire payloads only.

Internal transition plans, state snapshots, store records, assertion results,
and rejection values should use purpose-built immutable Python types. Pydantic
serialization must not become the canonical serializer.

Library error text is not a platform contract. Validation failures must map to
stable harness-owned rejection codes.

### 4.6 Fixtures remain authoritative

The six fixture files under `docs/architecture/fixtures/` remain the sole
canonical corpus. Tests must not copy or silently regenerate them under
`tests/`.

Fixture changes require the same design review and decision-log treatment as
any other change to ratified evidence.

## 5. Proposed package layout

The implementation should begin with the following shape and add files only
when a phase requires them:

```text
pyproject.toml
.python-version
uv.lock
src/
  finance_assurance/
    __init__.py
    validation/
      __init__.py
      __main__.py
      canonical.py
      corpus.py
      results.py
      contracts/
      integrity/
      transitions/
      state/
      scenarios/
      boundaries.py
      report.py
tests/
  h0_corpus/
  h1_contracts/
  h2_integrity/
  h3_transitions/
  h4_stateful/
  h5_replay/
  h6_boundaries/
  h7_reporting/
```

This is a validation package, not an early decomposition into Atlas, Hermes,
Argus, Aegis, and Pythia services. The mythology names remain capability and
ownership lenses over one platform substrate.

## 6. Build phases and gates

Each phase depends only on passed lower phases. A phase is committed only after
its own gate passes.

### Cohesion-audit checkpoints

The implementation pauses for a hard cross-artifact audit at three points:

1. **After Phase 1, before Phase 2** - reconcile the first executable corpus
   interpretation with Artifacts C, E, F, G, and H before schemas freeze those
   meanings in code.
2. **After Phase 3, before Phase 4** - reconcile the complete conformance and
   integrity baseline before introducing commands, state, and mutation.
3. **After Phase 7, before Milestone 1 closure** - verify documentation,
   decisions, fixtures, implementation, reports, and public claims from a clean
   checkout.

Each audit must distinguish historical wording from a stale current claim,
correct non-architectural drift, and stop implementation when a material
contract contradiction requires a new decision.

The first checkpoint passed in
`docs/roadmap/milestone-1-cohesion-audit.md`. The second checkpoint passed in
`docs/roadmap/milestone-1-post-phase3-cohesion-audit.md` after closing three
non-architectural assurance gaps. The final checkpoint passed in
`docs/roadmap/milestone-1-post-phase7-cohesion-audit.md` after closing four
implementation-proof gaps and synchronising current-status documentation. No
new ADR was required at either later checkpoint.

### Phase 0 - Runtime and harness protocols

Build:

- Python and `uv` project scaffold;
- locked dependencies;
- package and test discovery;
- stable `AssertionResult`, `Rejection`, and rejection-code types;
- the boundary-recorder interface;
- the report-sink interface; and
- the clean-checkout command shell.

The recorder and reporter interfaces are defined now because later components
must emit observations through stable ports. Their H6/H7 implementations are
completed only in Phase 7.

Gate:

- the package imports from a clean environment;
- an empty harness run is deterministic;
- tests and static checks execute through the locked toolchain; and
- no domain fixture is yet interpreted.

### Phase 1 - Raw corpus and H0

Build:

- the six-file fixture loader;
- the explicit canonical serializer;
- `RawCorpusIndex`;
- raw inventory and uniqueness checks; and
- reporting proof-body byte loading and SHA-256 verification.

Gate:

- every JSONL line parses;
- fixture inventory matches Artifact H;
- identifiers are unique within their required scopes;
- every required authored, bootstrap, opaque-owner, G-13, and
  reporting-content reference resolves through its permitted boundary;
- each declared-only evidence reference preserves one stable
  `ref_id`-to-declared-hash relationship without claiming byte verification;
- the two committed reporting proof bodies resolve and hash correctly;
- canonicalization is byte-stable; and
- H0 passes.

### Phase 2 - Contract boundary and H1

Status: Complete 2026-08-02. The strict frozen Pydantic boundary, discriminated
registry, immutable `ValidatedCorpusIndex`, stable harness rejection mapping,
three positive conformance proofs, and eleven isolated negative mutations are
implemented. H1 passes 14/14 without altering `RawCorpusIndex` or the fixtures.

Build:

- one strict payload model per in-scope Artifact F contract;
- a registry keyed by object or accounting-event discriminant;
- positive validation for every canonical payload;
- all eleven H1 negative cases;
- stable mapping from validator failures to harness rejection codes; and
- construction of `ValidatedCorpusIndex` from `RawCorpusIndex`.

Gate:

- unknown fields, wrong money types, incomplete version references, invalid
  discriminants, and cross-variant fields are rejected;
- valid payloads survive canonical round trips byte-equivalently;
- no contract model supplies a missing value by default;
- the raw index is unchanged; and
- H1 passes.

If this phase reveals an under-specified contract or fixture, implementation
stops for a documentation correction. The validator must not infer a new
field, default, or variant.

### Phase 3 - Pure integrity and H2

Status: Complete 2026-08-02. Eleven pure H2 assertions now reconcile causal
order, proposal/journal/posting balance, the event-stream firewall, restatement
manifest and scope, the ordered J-010 reversal binding, close and approval
guards, and the hash-resolved GBP 10,000 June reporting bridge. H2 passes 11/11
without mutable stores. The mandatory cohesion audit now runs before Phase 4.

Build pure checks over `ValidatedCorpusIndex` for:

- causal and correlation references;
- object-version and accounting-event references;
- journal and manifest balance;
- manifest-to-projection reconciliation;
- lifecycle and reporting-content arithmetic;
- restatement-case state guards; and
- the F-EXE-001 reversal binding in the required order.

For F-EXE-001, first prove that the referenced projection's `source_hash`
equals the reversal event's declared `input_hashes[0]`. Only then compare the
projection lines with the opposite reversal lines.

Gate:

- all H2 assertions run without mutable stores;
- referenced J-010 remains non-authored state;
- the GBP 10,000 June reporting bridge is resolved from committed bytes;
- F-EXE-001 is executable and passing; and
- H2 passes.

### Phase 4 - Pure planner and H3 guard correctness

Status: Complete 2026-08-02. One pure `plan(command, immutable_state)` function
now owns every preventive guard. PI-01 through PI-18 pass with stable rejection
codes, including both unresolved-close and both duplicate-effect variants.
Thirteen accepted controls cover all in-scope transition families, exact event
subjects, and complete immutable posting/publication packages. Reversal
integrity is recomputed from the bound G-13 projection rather than trusted from
the caller. The runner reports `H3-GUARD PASS` and explicitly keeps full H3
pending until Phase 5 store-digest proofs exist.

Build:

- immutable `StateSnapshot` inputs;
- command types required only by C-001, CT-1, PI-01 through PI-18, and the H4
  retry, idempotency, and pre-construction rejection cases;
- `TransitionPlan` variants for the permitted transitions;
- the pure `plan()` function; and
- exact rejection-code tests for every prohibited transition.

Gate:

- every PI case is rejected for the required reason;
- every permitted transition produces a complete plan;
- planning performs no I/O or mutation;
- there is one guard implementation; and
- the H3 guard-correctness sub-claim passes.

H3 is not yet fully green at this gate.

### Phase 5 - Transactional state, H3 no-mutation, and H4

Status: Complete 2026-08-02. Immutable harness state now separates object
versions, lifecycle projections, the append-only accounting-event log, journal
and reporting-version stores, command results, financial effects, and G-14
dispositions. The dispatcher invokes the single Phase 4 planner, prepares the
complete write set, validates commit invariants, and returns a new state only
after the atomic boundary. A fault injected immediately before commit leaves
the original state byte-identical. All eighteen H3 cases prove equality across
the six protected digests, one immutable rejection on first delivery, and no
new control record on retry. H4 passes 7/7, including independent posting and
publication effect idempotency and subject-free pre-construction G-14 rejection.

Build:

- immutable object-version storage;
- rebuildable lifecycle projections;
- non-authored referenced-state storage;
- append-only accounting-event log;
- journal and reporting-version stores;
- command-result registry;
- effect registry;
- the non-accounting command-disposition log required by G-14;
- a harness-scoped unit of work; and
- a dispatcher that commits an already validated `TransitionPlan`.

Execution order is:

```text
plan
-> prepare domain, event, command-result, effect, and disposition writes
-> validate all commit invariants
-> commit the complete unit of work atomically
```

Fault injection must be possible immediately before commit so H4-06 can prove
atomicity.

Gate:

- all rejected commands produce equal before/after digests across every store
  named by Artifact H;
- command retries return the prior result without duplicate effects;
- an invalid remediation directive is rejected before target-object
  construction and produces exactly one G-14 disposition;
- retrying that rejected command produces neither a second command result nor
  a second G-14 disposition;
- effect idempotency is enforced independently of command deduplication;
- partial writes are impossible under injected failure;
- the H3 no-mutation sub-claim passes;
- H3 is now fully passing; and
- H4 passes.

All Phase 5 gate conditions are satisfied. F-EXE-002 is closed by H4-01 through
H4-04. Sequential deterministic delivery is proven; distributed concurrency
and exactly-once claims remain explicitly out of scope.

### Phase 6 - Canonical scenario replay and H5

Status: Complete 2026-08-02. Scenario-local constructors now derive the C-001
automated draft, C-001 restatement correction draft, and both CT-1 correction
drafts through the public planner. Every subsequent command executes through
the Phase 5 dispatcher. The drivers independently construct terminal proposal,
period, journal, restatement, and reporting objects from scenario inputs and
event basis, then compare them to the ratified fixtures only after execution.
C-001 reproduces eleven ordered events across thirteen committed commands;
CT-1 reproduces six ordered events across eight committed commands. H5 passes
2/2 with deterministic terminal digests.

Build:

- bootstrap of the ratified starting state;
- C-001 command sequence;
- CT-1 command sequence;
- scenario-local constructors that use the same public planner and dispatcher;
  and
- exact end-state and event-sequence assertions.

Scenario drivers are integration proofs, not reusable domain services. They
must not mutate stores directly or bypass the contract boundary.

Gate:

- C-001 reproduces its eleven accounting-event instances;
- CT-1 reproduces its six accounting-event instances;
- correction, reversal, replacement, restatement, publication, and readiness
  consequences match the ratified traces;
- no accounting event re-enters the business-event posting engine; and
- H5 passes.

All Phase 6 gate conditions are satisfied. C-001 preserves the immutable June
v1 reporting proof, publishes v2 through restatement, and never reopens June.
CT-1 keeps J-010 solely in G-13 referenced state, proves J-011 equal and
opposite, applies J-012 to Orion, and produces zero net control-account movement.
Only the C-001 business event enters the posting-rule evaluator; all correction
constructors remain on the separate eventless path.

### Phase 7 - Boundary trace, assertion report, and H6-H7

Status: Complete 2026-08-02. The observational recorder proves all fourteen
Artifact G contracts without participating in transition execution. C-001
records G-01 through G-12, including both Argus and Aegis consumption of the
Pythia proof products and the approved-decision return through G-01. CT-1 keeps
J-010 solely on G-13 and records its complete verification handoff without
inventing a planning use. G-14 remains command-scoped and subject-free.

H7 aggregates 80 H assertions into canonical JSON with schema-backed contract,
fixture, and terminal-state digests, ordered PASS/FAIL/BLOCKED counts, repository
revision, and non-zero failure/block exit semantics. Two fresh executions are
semantically identical. H6 passes 17/17 and H7 passes 4/4.

Status: Complete 2026-08-02. The observational recorder proves all fourteen
Artifact G contracts without participating in transition execution. C-001
records G-01 through G-12, including both Argus and Aegis consumption of the
Pythia proof products and the approved-decision return through G-01. CT-1 keeps
J-010 solely on G-13 and records its complete verification handoff without
inventing a planning use. G-14 remains command-scoped and subject-free.

H7 aggregates 80 H assertions into canonical JSON with schema-backed contract,
fixture, and terminal-state digests, ordered PASS/FAIL/BLOCKED counts, repository
revision, and non-zero failure/block exit semantics. Two fresh executions are
semantically identical. H6 passes 17/17 and H7 passes 4/4.

Complete:

- the Artifact G boundary recorder;
- publisher, consumer, contract, object, and event observations;
- aggregation of H0-H7 results;
- machine-readable report output;
- concise human-readable output;
- blocked-versus-failed status handling; and
- final process exit semantics.

The recorder is observational. It must not participate in state transitions or
change scenario outcomes.

Gate:

- all required G contracts are observed in the canonical proofs;
- no unregistered writer or consumer is observed;
- H6 passes;
- H7 accounts for every required assertion;
- failures and blocks return non-zero;
- two fresh runs produce semantically identical reports; and
- the single clean-checkout command passes.

## 7. H-layer closure map

| Claim | Closing phase | Completion rule |
|---|---:|---|
| H0 corpus integrity | 1 | Raw corpus, inventory, identity, and proof-body hashes pass |
| H1 contract boundary | 2 | Three positive and eleven negative contract tests pass |
| H2 referential/accounting integrity | 3 | Pure checks pass over `ValidatedCorpusIndex` |
| H3 guard correctness | 4 | The pure planner returns every required rejection |
| H3 no mutation | 5 | Equal store digests prove rejected commands have no effects |
| H3 complete | 5 | Both H3 sub-claims pass |
| H4 stateful and idempotent behavior | 5 | Deduplication, effects, and atomicity pass |
| H5 canonical replay | 6 | C-001 and CT-1 replay exactly |
| H6 module boundary conformance | 7 | Artifact G observations pass |
| H7 assertion reporting | 7 | Complete deterministic report and exit behavior pass |

No phase may report a higher layer green while a required lower layer is
failing or blocked.

## 8. Test architecture

The executable H catalog is the source of acceptance truth. Each H assertion
returns a structured `AssertionResult`; the command-line harness aggregates
those results into H7.

pytest verifies components and invokes the same H assertion functions. It must
not contain a second, divergent interpretation of the H catalog. In
particular:

- the CLI report is not reconstructed from pytest output;
- scenario fixtures are not copied into pytest fixtures;
- rejection codes are asserted instead of Pydantic message strings; and
- canonical bytes come only from `canonical.py`.

Conformance-mode H2 remains pure and store-free. Stateful behavior begins only
with Phase 5.

## 9. Commit sequence

Implementation should land as small, passing commits:

1. scaffold the locked runtime and harness protocols;
2. implement canonical loading and H0;
3. implement the Artifact F boundary and H1;
4. implement pure H2 integrity proofs;
5. implement the pure planner and H3 guard tests;
6. implement transactional state, complete H3, and prove H4;
7. replay C-001 and CT-1 for H5;
8. complete G-boundary recording and H6; and
9. complete H7 reporting and the clean-checkout gate.

No commit may combine a fixture-contract correction with code that depends on
that correction. The documentation change must be reviewed and ratified first.

## 10. Milestone 1 definition of done

Milestone 1 is complete only when:

- one locked command runs H0 through H7 from a clean checkout;
- all required assertions pass with none silently omitted;
- C-001 and CT-1 replay through ordinary planner and dispatcher paths;
- both H3 sub-claims are independently visible and passing;
- F-EXE-001 and F-EXE-002 have executable proof coverage;
- the two reporting-content hashes resolve from committed canonical bytes;
- two fresh runs are semantically reproducible;
- the repository contains no database, API, UI, authentication, orchestration,
  or speculative event taxonomy added for the harness; and
- the decision log records only material architecture or contract changes
  discovered during implementation, not reversible library choices.

All definition-of-done conditions are satisfied. The final cohesion audit found
no unresolved architecture, contract, fixture, ownership, or scope blocker.

All definition-of-done conditions are satisfied. The final cohesion audit found
no unresolved architecture, contract, fixture, ownership, or scope blocker.

## 11. Explicitly deferred

Milestone 1 does not introduce:

- persistent databases;
- network services or module APIs;
- authentication or authorization infrastructure;
- a universal event bus;
- production evidence storage;
- an expanded event taxonomy;
- business-process simulation beyond C-001 and CT-1;
- dashboards or public application pages; or
- independent Atlas, Hermes, Argus, Aegis, or Pythia deployments.

Those capabilities begin only after the executable contract baseline is
proven.
