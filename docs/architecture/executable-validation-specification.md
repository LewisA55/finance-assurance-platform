# Artifact H: First Executable Validation Specification

Design sequence artifact H. This document defines the smallest executable
harness that can prove the ratified accounting contracts, state machines,
module boundaries, and canonical transactions without beginning product
implementation.

Status: Design v0.3.1 - v0.3 ratified 2026-07-24; corpus-role clarification 2026-08-02

Binds:

- the five platform invariants;
- Artifact C: Accounting Object Model;
- Artifact E v0.2.1: Accounting State Machines and Command/Event Matrix;
- Artifact F v0.2.1: Minimum Payload Contracts;
- Artifact G v0.2: Module Ownership and Publish/Consume Contract Map;
- canonical transactions C-001 and CT-1;
- F-EXE-001 and F-EXE-002; and
- ADR-015: Ratify Artifact G v0.2.
- ADR-016: Bound Cryptographic Verification to Reporting Proof Bodies.

## 0. Purpose and Hard Constraint

The first executable milestone must answer one question:

> Can the platform reproduce C-001 and CT-1, reject their prohibited
> alternatives, and prove every resulting claim from versioned fixtures?

Artifact H defines a test harness, not the product architecture.

The harness must be:

- in-process;
- deterministic;
- stateful where command behaviour requires state;
- independent of database, API, UI, deployment, and authentication choices;
- driven by canonical fixtures and explicit scenario scripts;
- strict about contract versions and unknown fields; and
- capable of producing one machine-readable assertion report.

The harness must not:

- add a business process beyond C-001 or CT-1;
- expand Artifact F's nine-object or ten-event-type authoring boundary;
- define production payloads for G-01 through G-14;
- introduce a production database or message broker;
- claim distributed concurrency behaviour;
- build a module dashboard, API, or application shell; or
- turn a test-only proof projection into a domain object.

## 1. Milestone Boundary

### 1.1 Milestone 0

Milestone 0 is design complete when Artifact H is ratified. Ratification means
the repository has an unambiguous, finite specification for the first
executable proof.

### 1.2 Milestone 1

Milestone 1 implements only the harness defined here. It is complete when the
ratified acceptance suite passes from a clean checkout through one documented
command.

Milestone 1 is not a thin version of the public application. It is executable
architecture proof that the application can later trust.

## 2. Harness Modes

One harness exposes two modes. They may share code, but their claims remain
distinct.

### 2.1 Conformance mode

Conformance mode treats the existing JSONL corpus as fixed input and proves:

- every fixture parses;
- every Artifact F payload satisfies its exact contract and variant;
- canonical serialization is stable;
- domain and reporting-content references resolve within the permitted
  authored, bootstrap, opaque-owner, or referenced-state boundary;
- declared-only evidence references remain internally consistent without being
  misreported as content-byte resolved;
- money, totals, hashes, state guards, and discriminators are valid; and
- negative mutations are rejected with the expected reason.

Conformance mode does not claim that the platform can execute a lifecycle.

### 2.2 Execution mode

Execution mode bootstraps declared preconditions, invokes the commands in
Artifact E order, and proves:

- only valid transitions occur;
- emitted accounting events reproduce the Artifact F event fixtures;
- immutable objects and terminal projections reproduce the expected fixtures;
- duplicate delivery and effect idempotency are enforced;
- prohibited commands leave state unchanged; and
- cross-module publications follow Artifact G.

Execution mode does not deserialize a terminal fixture and then claim it
executed the transition that created it.

## 3. Logical Harness Components

These are logical responsibilities, not prescribed services, classes, or
deployment units.

| Component | Required responsibility |
|---|---|
| Fixture loader | Reads the canonical JSONL corpus and test-only scenario assets without changing them. |
| Contract validator | Selects the declared contract version and rejects undeclared or inapplicable fields. |
| Canonical serializer | Produces stable UTF-8 JSON with canonical key ordering for equality tests. |
| Posting-rule evaluator | Accepts only an admitted `business_event` and derives an `AUTOMATED_POSTING` proposal. |
| Correction constructors | Derive `REVERSAL`, `REPLACEMENT`, and `RESTATEMENT_ADJUSTMENT` proposals without invoking the posting-rule evaluator. |
| Command dispatcher | Applies Artifact E preconditions and routes an accepted command to one transition handler. |
| Object store | Holds immutable versions and current lifecycle projections for the duration of one isolated run. |
| Accounting-event log | Appends accepted accounting events in order and never updates an appended event. |
| Command-result registry | Returns the original result for a repeated logical `command_id` and prevents a second event. |
| Effect registry | Prevents duplicate posting and publication under a consumed `idempotency_key`. |
| Evidence resolver | Resolves exact evidence references and verifies the content made available to the test. |
| Reporting-content resolver | Resolves exact reporting content versions for runtime v1-to-v2 arithmetic. |
| Contract-boundary recorder | Records publisher, consumer, contract ID, object version, and purpose for G handoff assertions. |
| Assertion reporter | Emits the complete ordered test result and sufficient failure evidence. |

The logical components may be implemented in one process and one package. A
network boundary between them is explicitly out of scope.

## 4. Stores and Mutation Rules

### 4.1 Object store

The object store separates:

- immutable version records;
- current lifecycle projections derived from accepted events; and
- non-authored referenced-state projections.

An accepted transition may append a new immutable version or replace a
rebuildable current projection. It must not modify:

- a posted journal or journal line;
- a published reporting version;
- a frozen restatement manifest;
- an appended accounting event; or
- the J-010 referenced-state projection.

### 4.2 Accounting-event log

The event log enforces:

- globally unique `event_id`;
- one produced event per consumed `command_id`;
- causal order inside each `correlation_id`;
- immutable recorded payloads; and
- no registration of an accounting-event type as a business-event trigger.

### 4.3 Command and effect indexes

Command identity and financial-effect identity remain separate.

```text
command_id
-> one logical command result

idempotency_key
-> one posting or publication effect
```

A retry using the same `command_id` returns the first accepted or rejected
result and appends nothing. A new command using a consumed posting or publication
`idempotency_key` is rejected as a duplicate financial effect.

### 4.4 Transactional mutation

A command is atomic at harness scope:

```text
validate preconditions
-> prepare object and event changes
-> validate resulting invariants
-> commit all changes
```

Any rejected command leaves the accounting object store, accounting-event log,
effect index, journal store, and publication store unchanged. Its first
delivery records exactly one immutable rejection in the command-result
registry. A cross-module rejection also records exactly one separate G-14
command disposition where that test requires one. Redelivery returns the
original rejection and appends neither record again.

## 5. Inputs

### 5.1 Ratified fixture corpus

The harness consumes these existing files:

| File | Role |
|---|---|
| `fixtures/canonical-object-payloads.jsonl` | Artifact F object payloads and terminal canonical state. |
| `fixtures/c001-accounting-events.jsonl` | Eleven expected C-001 accounting-event instances. |
| `fixtures/ct1-accounting-events.jsonl` | Six expected CT-1 accounting-event instances. |
| `fixtures/restatement-case-snapshots.jsonl` | Four exercised non-terminal RC-001 projections; terminal `PUBLISHED` remains in `canonical-object-payloads.jsonl`, completing the five-form proof. |
| `fixtures/referenced-state-projections.jsonl` | Non-authored J-010 proof projection for G-13 and reversal validation. |
| `fixtures/reporting-content-proof-bodies.jsonl` | Non-domain June v1 and v2 canonical bytes used for runtime reporting arithmetic and SHA-256 verification. |

The harness may not rewrite these inputs during a run.

### 5.2 Required Milestone 1 test assets

Implementation may add the following test-only assets:

- ordered C-001 command script;
- ordered CT-1 command script;
- bootstrap-state manifest for each scenario;
- table-driven negative mutations;
- expected Artifact G contract-boundary trace; and
- expected command dispositions for pre-construction rejection.

These assets are harness inputs, not production contracts. Their fields must
not be accepted by an Artifact F serializer or emitted as G domain payloads.

### 5.3 Bootstrap boundary

Each scenario declares all state that predates its first executed command.
Bootstrap state is not silently created by the harness.

C-001 bootstrap includes:

- admitted recognition-due business event;
- active `PR-O2C-RECOG@v1`;
- June in the required opening period state;
- July open as the eligible correction ledger period;
- original `RV-2026-06@v1` reporting content; and
- opaque Aegis trigger and directive references at the step where they become
  available.

CT-1 bootstrap includes:

- J-010 only through the G-13 referenced-state projection;
- July 2026 open;
- opaque Aegis directive `DIR-CT1-001`; and
- applicable reversal, correction, approval, and posting policies.

Bootstrap does not make J-010 an Artifact F-authored journal.

## 6. Determinism

Every run must control:

- clock values;
- command order;
- event identifiers;
- correlation and causation identifiers;
- canonical JSON serialization;
- iteration order;
- hash input bytes;
- money representation;
- fixture and contract versions; and
- reporting-content resolution.

There is no random generation in Milestone 1. Tests execute against isolated,
fresh stores. A full suite run twice from the same commit must produce the same
ordered assertion results and final-state digest.

## 7. Reporting-Content Proof Boundary

Artifact F deliberately stores a `content_ref`, `content_hash`, and
`content_schema_version` rather than a statement body. The harness must now
prove runtime resolution without defining the platform's future financial
statement schema.

A test-only reporting-content resolver supplies immutable June v1 and v2 proof
bodies. The minimum proof body contains only:

- reporting-version reference;
- presented period;
- currency;
- the deferred-revenue balance needed by C-001;
- the subscription-revenue amount needed by C-001; and
- canonical bytes whose hash is checked against the reporting-version
  reference used by the test.

Canonical bytes are the UTF-8 encoding, with no BOM or trailing newline, of
the `canonical_body` object serialized with keys in ascending lexical order and
no insignificant whitespace. The fixture declares
`SORTED_KEYS_COMPACT_UTF8_V1`. The wrapper, fixture ID, declared hash, and
canonicalization label are not part of the hashed bytes.

The resolver must prove:

```text
June v2 subscription revenue
= June v1 subscription revenue + GBP 10,000

June v2 deferred revenue
= June v1 deferred revenue - GBP 10,000
```

It must also prove that:

- the v1 content remains retrievable and unchanged;
- the v2 bridge is supported by RC-001's frozen manifest;
- J-560 remains a July ledger journal;
- June remains `HARD_CLOSED`; and
- the reporting successor does not overwrite v1.

The proof body is a test projection, not a production reporting contract.

## 8. Test Layers

Tests run in the following order. A layer may rely only on passed lower layers.

| Layer | Name | Claim |
|---|---|---|
| H0 | Corpus integrity | The fixture files and inventory are complete, parseable, and internally identifiable. |
| H1 | Contract conformance | Artifact F serializers accept exactly the ratified payload boundary. |
| H2 | Referential and accounting integrity | References, causality, money, balance, manifests, and reversal proofs reconcile. |
| H3 | Pure transition guards | Artifact E accepts legal transitions and rejects illegal transitions without mutation. |
| H4 | Stateful command and effect control | Retry, command deduplication, and posting/publication idempotency work over time. |
| H5 | Canonical scenario replay | C-001 and CT-1 reproduce their exact event sequences and terminal states. |
| H6 | Module boundary trace | The scenario handoffs comply with Artifact G and prohibit cross-module writes. |
| H7 | Reproducibility and report | The run is repeatable and emits a complete assertion report. |

If H0 fails, no higher-layer result may be reported as passed. A failed lower
layer may cause dependent tests to be reported as blocked, not silently
skipped.

## 9. H0: Corpus Integrity Suite

| Test | Required assertion |
|---|---|
| H0-01 | Every non-empty JSONL line parses as one JSON object. |
| H0-02 | The inventory contains nine Artifact F object types, ten distinct accounting-event types, eleven C-001 events, six CT-1 events, and seventeen event instances. |
| H0-03 | Event IDs, fixture IDs, fully versioned object references, and command IDs are unique where the contract requires uniqueness. |
| H0-04 | The five RC-001 snapshots cover empty `PROPOSED`, linked `PROPOSED`, `ADJUSTMENTS_READY`, `APPROVED`, and `PUBLISHED`. |
| H0-05 | The J-010 projection is marked `authored_by_f = false` and is excluded from the nine-object authored inventory. |
| H0-06 | Every domain object, event, projection, and reporting-content reference required for the canonical proof resolves through its permitted authored, bootstrap, opaque-owner, G-13, or reporting-content boundary. |
| H0-07 | Every declared-only evidence reference retains one stable `ref_id` to declared-hash relationship; absence of an evidence body is permitted and is not reported as content-byte resolution. |

## 10. H1: Contract Conformance Suite

### 10.1 Positive conformance

| Test | Source obligation | Required assertion |
|---|---|---|
| H1-01 | F-P01 | Every nested canonical object payload deserializes under its selected contract. |
| H1-02 | F-P02 | All eleven C-001 events deserialize and canonically reserialize byte-equivalently. |
| H1-03 | F-P03 | All six CT-1 events deserialize and canonically reserialize byte-equivalently. |

### 10.2 Negative conformance

Each Artifact F negative mutation remains an independently reported test.

| Test range | Source obligations | Rejection class |
|---|---|---|
| H1-04 to H1-10 | F-N01 to F-N07 | Unknown field, money type, reference version, conditional field, or discriminator. |
| H1-11 | F-N09 | Cross-variant reversal field leakage. |
| H1-12 | F-N10 | Cross-variant restatement field leakage. |
| H1-13 | F-N12 | Incomplete reporting-version reference. |
| H1-14 | F-N16 | Ownership-boundary violation from an embedded Aegis body. |

The mutation driver changes one condition at a time. A test does not pass
merely because malformed JSON failed before reaching the intended validator.

## 11. H2: Referential and Accounting Integrity Suite

| Test | Source obligation | Required assertion |
|---|---|---|
| H2-01 | F-P04 | Every non-null causal event resolves to the immediately preceding causal event in the same correlation. |
| H2-02 | F-P05 | Every proposal, journal, and posted event balances in integer minor units and one currency. |
| H2-03 | F-P06 and F-N08 | Only the original admitted C-001 business event is eligible for the posting-rule evaluator. |
| H2-04 | F-P07 and F-N11 | RC-001's manifest hash, totals, and line references reconcile to J-560; a changed amount under the frozen hash fails. |
| H2-05 | F-P08, F-N20, F-EXE-001 | J-010 `source_hash` first equals the reversal proposal input hash; only then is J-011 proved equal and opposite by account, dimensions, currency, and amount. |
| H2-06 | F-P09 | Every exercised RC-001 snapshot satisfies its state guard. |
| H2-07 | F-N13 | J-560 cannot use hard-closed June as its ledger period. |
| H2-08 | F-N14 | A manifest entry cannot present into a period outside RC-001 scope. |
| H2-09 | F-N17 and F-N18 | Hard close rejects non-zero unresolved submitted or approved proposal counts. |
| H2-10 | F-N19 | Approval rejects a failed segregation-of-duties result. |
| H2-11 | Artifact F section 9.1 and ADR-016 | Runtime content resolution proves June v1-to-v2 arithmetic and preserves both versions. |

H2-05 is ordered deliberately. Equal-and-opposite comparison against an
unbound projection is not a valid proof.

## 12. H3: Pure Transition Guard Suite

The harness executes every preventive invariant PI-01 through PI-18 from
Artifact E as a distinct test.

| Test range | Source obligations | Required result |
|---|---|---|
| H3-01 to H3-18 | PI-01 to PI-18 | Reject before prohibited state, ledger, manifest, or publication mutation. |

For every rejected command, the harness captures before and after digests for:

- object versions;
- lifecycle projections;
- event log;
- journal store;
- reporting-version store;
- effect registry.

Those accounting-domain and effect digests must remain equal. The first
delivery must add exactly one immutable command-result rejection. Where G-14
applies, it must also add exactly one disposition outside accounting domain
state. A retry must leave both control records unchanged.

At least one legal in-scope control case must accompany each transition family
so the suite cannot pass through an implementation that rejects every command.
The accepted transitions are limited to those exercised by C-001 and CT-1.

## 13. H4: Stateful Command and Effect Suite

| Test | Source obligation | Required assertion |
|---|---|---|
| H4-01 | F-P10 and F-EXE-002 | Redeliver the same logical command under the same `command_id`; return the original result and append no event. |
| H4-02 | F-N21 and F-EXE-002 | Attempt to append a different event under a consumed `command_id`; reject it and preserve state. |
| H4-03 | F-N15, PI-18, F-EXE-002 | Submit a new command using a consumed posting idempotency key; reject the second financial effect. |
| H4-04 | F-N15, PI-18, F-EXE-002 | Submit a new command using a consumed publication idempotency key; reject the second publication. |
| H4-05 | G-A13 and G-14 | Reject an invalid remediation directive before constructing a target object and publish one G-14 disposition without an accounting-event subject. |
| H4-06 | Atomicity rule | Inject a failure after validation but before commit; no partial object, event, command, effect, journal, or publication state remains. |
| H4-07 | Rejected-command replay | Redeliver the H4-05 command under the same `command_id`; return the original rejection without adding a second command result or G-14 disposition. |

Milestone 1 tests sequential delivery and deterministic retry. Parallel race
testing and distributed exactly-once claims remain out of scope.

## 14. H5: Canonical Scenario Replay

### 14.1 C-001

Execution mode must reproduce, in order:

1. the admitted recognition-due business event entering the posting-rule
   evaluator exactly once and deriving draft P-551@v1;
2. `AE-C001-001` through `AE-C001-011`;
3. P-551@v1 ending `DEFERRED`;
4. June ending and remaining `HARD_CLOSED`;
5. Atlas's restatement constructor deriving P-551@v2 without invoking the
   posting-rule evaluator;
6. RC-001 traversing all five exercised projections;
7. P-551@v2 ending `POSTED`;
8. J-560 and its balanced immutable lines in July;
9. the frozen June presentation-adjustment manifest;
10. immutable `RV-2026-06@v1`;
11. published `RV-2026-06@v2`;
12. the runtime-resolved GBP 10,000 statement bridge; and
13. no accounting event entering the posting-rule evaluator.

The emitted accounting events must canonically equal the eleven ratified event
fixtures. The final authored object states must equal their expected fixtures.

### 14.2 CT-1

Execution mode must reproduce, in order:

1. the reversal constructor resolving hash-bound G-13 state and deriving draft
   P-REV-010@v1 without invoking the posting-rule evaluator;
2. the replacement constructor deriving draft P-REP-010@v1 from J-010 and the
   opaque directive without invoking the posting-rule evaluator;
3. `AE-CT1-001` through `AE-CT1-006`;
4. P-REV-010@v1 and P-REP-010@v1 ending `POSTED`;
5. immutable J-010 referenced state;
6. balanced immutable J-011 and J-012;
7. J-011 equal and opposite to the hash-bound J-010 projection;
8. J-012 applying cash to Orion rather than Vega; and
9. zero net change to the GL control-account total across J-011 and J-012.

The emitted accounting events must canonically equal the six ratified event
fixtures. CT-1 does not create a G-10 readiness assessment or Pythia output.

## 15. H6: Module Boundary Trace

The contract-boundary recorder is a test instrument. It records semantic
handoffs without defining G payload bodies.

Each record contains only the proof metadata needed by the harness:

- sequence number;
- publisher module or substrate boundary;
- consumer module or substrate boundary;
- G contract ID;
- exact subject or product reference;
- exact contract version where defined;
- declared purpose where required; and
- outcome: accepted, rejected, or blocked.

This is a harness trace and cannot be published as a G domain contract.

### 15.1 Artifact G acceptance mapping

Each ratified G acceptance test remains separately observable.

| Test | Source obligation | Required assertion |
|---|---|---|
| H6-01 | G-A01 | Every in-scope lifecycle write resolves to exactly one authoritative module. |
| H6-02 | G-A02 | The trace contains five module lenses and a non-module substrate boundary; it contains no sixth product module. |
| H6-03 | G-A03 | Hermes admits and traces an event without changing its source meaning or adding accounting treatment. |
| H6-04 | G-A04 | Only Atlas writes the eight Atlas-owned Artifact F object types. |
| H6-05 | G-A05 | Aegis publishes the directive, while only Atlas creates and transitions RC-001. |
| H6-06 | G-A06 | Argus publishes an exception and Aegis separately publishes the finding or issue. |
| H6-07 | G-A07 | A controlled Pythia use is accepted only with exact product-version and purpose-specific readiness references. |
| H6-08 | G-A08 | An unversioned or implicit-latest cross-module reference is rejected. |
| H6-09 | G-A09 | C-001 records every permitted contract G-01 through G-12 without a direct cross-module write. |
| H6-10 | G-A10 | CT-1 leaves Atlas as the only writer of J-011 and J-012. |
| H6-11 | G-A11 | Accounting, governance, and forecast events are rejected from the G-01 posting input boundary. |
| H6-12 | G-A12 | Every handoff retains immutable evidence and exact upstream references. |
| H6-13 | G-A13 | Retry, rejection, deferral, and stale-version outcomes remain observable. |
| H6-14 | G-A14 | The harness adds no domain payload schema beyond the ratified canonical need. |
| H6-15 | G-A15 | J-010 is read only through G-13 and never appears as an Artifact F-authored G-04 or G-05 record. |
| H6-16 | G-A16 | Every Artifact F actor role acts inside Atlas when operating on Artifact F state. |
| H6-17 | G-A17 | Pre-construction rejection produces G-14 without an accounting-event subject. |

### 15.2 C-001 trace

The trace must reproduce Artifact G section 8:

- every contract G-01 through G-12 appears in a permitted direction;
- Pythia receives exact G-06 and G-10 versions before publishing G-11 and G-12;
- Argus and Aegis consume the Pythia proof outputs;
- the approved operational decision returns only as a G-01 candidate; and
- no module directly writes another module's owned lifecycle.

### 15.3 CT-1 trace

The trace must reproduce Artifact G section 9:

- Hermes publishes G-03;
- Atlas's read boundary publishes J-010 only through G-13;
- Argus publishes G-07;
- Aegis publishes G-08 and G-09;
- Atlas alone writes the correction proposals, events, J-011, and J-012; and
- G-10 through G-12 remain absent because there is no controlled planning use.

### 15.4 Boundary rejection cases

The recorder or ownership guard must reject:

- an accounting event offered as G-01;
- Argus attempting to mutate a journal;
- Aegis attempting to open RC-001 directly;
- Pythia attempting to append an accounting event;
- J-010 represented as an Artifact F-authored G-04 or G-05 object;
- a controlled Pythia use without exact G-10 readiness;
- readiness attached to a different reporting-product version; and
- a consumer attempting an unversioned or implicit-latest reference.

## 16. H7: Assertion Report and Reproducibility

The harness emits one machine-readable report containing, for every test:

- test ID;
- layer;
- source obligation;
- status: `PASS`, `FAIL`, or `BLOCKED`;
- expected outcome;
- actual outcome;
- fixture, command, object, event, or contract references;
- before and after digests where mutation is relevant; and
- deterministic failure details.

The report also contains:

- repository revision when available;
- fixture inventory digest;
- contract inventory digest;
- ordered test count by status;
- final C-001 state digest;
- final CT-1 state digest; and
- overall result.

The overall result is `PASS` only when every required test passes. A blocked
test prevents an overall pass.

Run A and Run B from fresh stores and identical inputs must produce identical
semantic report content. Environment-specific elapsed time and filesystem
paths are excluded from the reproducibility comparison.

## 17. Coverage Matrix

| Ratified source | Executable coverage |
|---|---|
| Artifact E legal lifecycles | In-scope accepted transitions use H3 legal control cases and H5 replay; unexercised accepted transitions are explicitly deferred in section 18. |
| PI-01 through PI-18 | H3-01 through H3-18. |
| F-P01 through F-P03 | H1-01 through H1-03. |
| F-P04 through F-P09 | H2-01 through H2-06. |
| F-P10 | H4-01. |
| F-N01 through F-N07 | H1-04 through H1-10. |
| F-N08 | H2-03. |
| F-N09, F-N10, F-N12, F-N16 | H1-11 through H1-14. |
| F-N11, F-N13, F-N14, F-N17 through F-N20 | H2-04 and H2-07 through H2-10. |
| F-N15 and F-N21 | H4-02 through H4-04. |
| F-EXE-001 | H2-05. |
| F-EXE-002 | H4-01 through H4-04. |
| G-A01 through G-A17 | H6-01 through H6-17 plus supporting assertions in H3, H4, and H5. |
| C-001 | H5.1 and H6.1. |
| CT-1 | H5.2 and H6.2. |
| Runtime reporting arithmetic deferred by F | H2-11 and section 7. |

## 18. Explicitly Deferred

The following are not required for Milestone 1:

- production JSON Schema, Pydantic, Avro, or Protobuf selection;
- database engine or physical schema;
- API framework;
- message broker or event-stream platform;
- user authentication or authorisation UI;
- multi-tenant isolation;
- parallel command execution;
- distributed transaction semantics;
- performance or volume testing;
- synthetic enterprise data generation;
- broader chart of accounts or statement schema;
- payload schemas for Hermes, Argus, Aegis, or Pythia;
- production evidence storage;
- production cryptographic key management; and
- modules or transactions beyond C-001 and CT-1.

Artifact E legal transitions not exercised by the closed Artifact F event set
are also deferred as successful paths. These include:

- proposal rejection, cancellation, and expiry;
- period soft close, exceptional reopen, and reclose; and
- restatement withdrawal.

Their preventive guards may still be tested when the expected result is
rejection before event emission. A successful deferred transition requires a
later payload-contract revision because Artifact F deliberately excludes its
event type. Milestone 1 must not invent that event merely to increase state
machine coverage.

An implementation may choose a lightweight validation library internally, but
that choice does not become a platform architecture decision merely because
the first harness uses it.

### 18.1 Resolved: bounded hash verification

ADR-016 adopts a scoped hybrid.

The two June reporting-content proof bodies have committed canonical bytes and
reproducible SHA-256 values. They are cryptographically verified because H2-11
and the C-001 replay make a numerical claim from their contents.

All other `evidence_ref.content_hash` values remain declared fixture values.
The harness validates:

- SHA-256 string format;
- stable `ref_id` to declared-hash consistency;
- exact cross-reference equality where a ratified test requires it;
- immutability across the run; and
- preservation through module handoffs.

The harness does not report those evidence artifacts as content-byte verified.
Canonical evidence bodies and production evidence storage remain deferred.
This limitation is explicit in the assertion report.

`EVD-C001-011` carries the same declared hash as the verified v2 reporting
content because it identifies that published snapshot. The reporting body is
verified through `reporting://2026-06/v2`; the equality does not create a
separate evidence-artifact body or a separate evidence-byte verification
claim.

This resolution changes fixture values for the reporting proof only. It does
not change Artifact F's payload boundary or define an evidence-storage model.

## 19. Design Ratification Checks

Artifact H ratification confirms that the Milestone 1 acceptance suite is
finite, internally consistent, and implementable. It does not claim that the
unbuilt harness already passes its runtime tests.

Artifact H may be ratified only when:

- H-A01: every ratified E, F, and G executable obligation is mapped to a named
  Milestone 1 test or an explicit deferral.
- H-A02: the specification keeps conformance and execution claims distinct.
- H-A03: the specification requires execution to start from declared bootstrap
  state rather than terminal fixtures.
- H-A04: H5 defines deterministic reproduction of all seventeen
  accounting-event instances.
- H-A05: H2-05 requires F-EXE-001 to bind J-010's source hash before reversal
  comparison.
- H-A06: H4 distinguishes F-EXE-002 command retry from effect idempotency.
- H-A07: H3 requires every rejected command to prove no accounting-domain
  mutation.
- H-A08: H4-05 defines G-14 pre-construction rejection without an Artifact F
  subject.
- H-A09: H2-11 defines June v1-to-v2 runtime resolution without a production
  statement schema.
- H-A10: H5.1 requires C-001 restatement without reopening June.
- H-A11: H5.2 requires CT-1 reversal and replacement while J-010 remains
  non-authored referenced state.
- H-A12: H6 tests Artifact G boundaries without defining G payload schemas.
- H-A13: H2-03, H3, and H6-11 test the accounting-event posting firewall
  preventively and independently.
- H-A14: every monetary test requirement uses integer minor units with ISO 4217
  currency.
- H-A15: H7 defines deterministic execution and one complete machine-readable
  report.
- H-A16: the Milestone 1 exit gate requires one documented clean-checkout
  command for the full suite.
- H-A17: database, API, UI, deployment, and distributed-system choices remain
  outside the artifact.
- H-A18: the two June reporting-content fixtures have committed canonical bytes
  and reproducible SHA-256 values; evidence references without bodies are
  explicitly declared-consistency-only and cannot be reported as content-byte
  verified.

## 20. Implementation Entry Gate

No Milestone 1 harness implementation should begin until Artifact H is
ratified.

After ratification, the first implementation plan should contain only:

1. repository runtime and test-runner bootstrap;
2. fixture loader and canonical serializer;
3. Artifact F contract validators;
4. in-memory stores and transition handlers;
5. C-001 and CT-1 scenario drivers;
6. negative mutation and stateful retry suites;
7. G contract-boundary recorder;
8. assertion report; and
9. one clean-checkout validation command.

Anything else requires a separately justified scope decision.
