# Milestone 2: Persistent Runtime Vertical Slice

Status: Approved v0.2 - Phase 6 gate passed 2026-08-09

## 1. Objective

Milestone 2 turns the proven Milestone 1 architecture into a reusable,
persistent, in-process runtime for the two canonical transaction families.

The milestone must answer:

> Can the platform accept parameterised business and correction inputs,
> execute the ratified lifecycles through real application boundaries, persist
> the authoritative result atomically, rebuild every derived projection, and
> reproduce the same governed outcome after restart?

Milestone 2 is not the public application. It is the runtime spine that a later
API, simulator, and user interface can safely use.

The vertical slice deliberately retains the complete C-001 loop through
Pythia. Cohesion is the scope control: every capability must participate in one
traceable transaction, while each runtime message and workflow step remains the
minimum needed to prove that transaction. The milestone must not reduce scope
by breaking the platform loop, or expand scope by inventing a reusable workflow
framework.

## 2. Why This Milestone Exists

Milestone 1 proves that the design is internally coherent:

- Artifact F payloads are strictly validated;
- the pure planner owns transition guards;
- the dispatcher commits immutable in-memory state atomically;
- C-001 and CT-1 reproduce their canonical event sequences;
- Artifact G ownership and consumption rules are executable; and
- H0 through H7 produce one deterministic conformance report.

However, the canonical scenario drivers still construct known inputs around
ratified fixtures, all mutable lifetime ends with one process, and the Artifact
G trace is an observational proof assembled after scenario execution.

Milestone 2 closes that gap. It moves the platform from:

```text
load canonical fixtures
-> replay known scenario
-> compare expected terminal state
```

to:

```text
accept parameterised input
-> validate and admit
-> execute application command
-> persist authoritative records atomically
-> publish real module handoffs
-> rebuild projections
-> query traceable governed output
```

## 3. Binding Baseline

Milestone 2 remains governed by:

- the five platform invariants in `AGENTS.md`;
- Artifact C - Accounting Object Model;
- Artifact E v0.2.1 - Accounting State Machines and Command/Event Matrix;
- Artifact F v0.2.1 - Minimum Payload Contracts;
- Artifact G v0.2 - Module Ownership and Contract Map;
- Artifact H v0.3.1 - Executable Validation Harness Specification;
- canonical transactions C-001 and CT-1;
- ADR-012 through ADR-017; and
- the passing Milestone 1 baseline at commit `943df3a`.

Milestone 2 may define new runtime boundaries that Artifact G deliberately left
semantic. It must not silently change an Artifact F field, accounting-event
variant, lifecycle, owner, correction treatment, or canonical proof.

Where runtime implementation reveals a contradiction with the ratified
baseline, work stops for design review. An adapter must not conceal the
contradiction.

## 4. Hard Constraints

### 4.1 One modular monolith

Milestone 2 runs as one process over one authoritative persistence boundary.
Hermes, Atlas, Argus, Aegis, and Pythia remain ownership and capability lenses,
not independently deployed services.

The milestone must not introduce:

- one database per module;
- network calls between modules;
- a message broker or universal event bus;
- distributed transactions;
- eventual-consistency claims; or
- service-local copies that compete with an authoritative publisher.

### 4.2 Business and accounting event streams remain structurally separate

`business_event` is the only class accepted by posting-rule evaluation.

Accounting lifecycle actions remain in the accounting-event stream. Posting,
reversal, restatement, and publication events may drive projections and
assurance consumers, but can never re-enter business-event admission or the
posting-rule engine.

The persistence model must make this distinction explicit rather than relying
on a runtime `if` statement or caller discipline.

### 4.3 Authoritative records and projections remain distinct

The runtime must distinguish:

- immutable admitted business events;
- immutable object versions;
- immutable accounting events;
- immutable posted journal records;
- immutable reporting versions;
- immutable command results and G-14 dispositions;
- immutable evidence identities and resolved proof content; and
- rebuildable current-state and query projections.

A projection may be deleted and rebuilt. Deleting a projection must never
delete or rewrite the authoritative record from which it was derived.

### 4.4 One planner and one commit path

Milestone 2 must reuse the semantics of:

```text
plan(command, immutable_state) -> TransitionPlan | Rejection
```

Persistence must not introduce a second guard implementation. Execution remains:

```text
load exact state
-> plan
-> prepare complete write set
-> validate invariants
-> commit atomically
```

The persistent adapter owns storage mechanics, not accounting decisions.

### 4.5 The validation harness remains independent

H0 through H7 remain the conformance authority for the ratified baseline. The
runtime must not absorb those test layers into its production execution path.

The desired dependency direction is:

```text
runtime contracts and kernel
        ^
        |
validation harness and acceptance tests
```

The runtime must never depend on H-layer runners, canonical fixture loaders,
scenario assertions, or the manually declared Artifact G proof traces.

### 4.6 No speculative generalisation

Milestone 2 supports only the behaviours already required by C-001 and CT-1.

It may parameterise:

- identifiers;
- timestamps and effective dates;
- legal entity;
- customer identity;
- accounts and dimensions within the existing rule shape;
- integer minor-unit amounts and currency where the current contract permits;
- period identity and state; and
- exact evidence and policy references.

It must not invent a new event type, accounting origin, business process,
control family, forecasting model, or generic workflow engine merely to appear
extensible.

### 4.7 Complete loop, minimum machinery

Milestone 2 must execute the complete canonical responsibility chain:

```text
Hermes admission and reconciliation
-> Atlas accounting and reporting
-> Argus exception and verification
-> Aegis issue, remediation, and readiness
-> Pythia governed input and decision
-> approved decision returned as a G-01 candidate
```

This is one thin platform transaction, not five feature sets. Each lens receives
only the command, query, and message shape required by C-001. There is no generic
case-management engine, workflow definition language, plugin system, arbitrary
approval graph, or module-local orchestration framework.

CT-1 exercises the correction arm only as far as its actual governed use
requires. It must not acquire Pythia messages or readiness merely for symmetry.

## 5. Target Runtime Boundary

The runtime should expose a small in-process application surface. Exact type
names remain a design deliverable, but the capability boundary is:

### Commands

- submit a candidate business event for Hermes admission;
- execute an admitted business event through Atlas posting-rule evaluation;
- submit, approve, defer, post, reverse, replace, or restate through the
  existing typed accounting commands;
- publish a reporting version;
- apply a validated Aegis remediation directive; and
- record a pre-construction command disposition when no domain object exists.

### Queries

- retrieve an exact object version;
- retrieve an exact event by identity;
- retrieve a journal with immutable lines;
- retrieve an accounting period and its current projection;
- retrieve an exact reporting version and proof-content reference;
- retrieve a command result or G-14 disposition;
- trace a reporting value back through journal, proposal, rule, business event,
  source reference, and evidence; and
- retrieve current state only as an explicitly labelled rebuildable projection.

Commands and queries are application ports, not HTTP routes. A later milestone
may place an API over them without changing their domain meaning.

## 6. Persistence Model Requirements

Milestone 2 requires one transactional persistence adapter behind an explicit
port. Database product selection remains unresolved until the requirements in
this section are tested against candidate engines.

The adapter must provide:

- atomic commit across the complete transition write set;
- append-only accounting-event and command-result identity;
- exact object-version retrieval;
- immutable journal header and line retrieval;
- uniqueness for event, command, version, and effect identities;
- optimistic or equivalent conflict detection for stale input state;
- independent command deduplication and effect idempotency;
- durable G-14 dispositions outside the accounting-event stream;
- transactional projection checkpoints;
- complete rollback under injected pre-commit failure;
- deterministic export for semantic digest comparison; and
- schema migration under version control.

### 6.1 Source of truth

Milestone 2 must decide and document which immutable records are sufficient to
rebuild each projection. It must not claim full event sourcing unless every
required projection can actually be reconstructed from the declared event
history and immutable object records.

The expected position is hybrid:

- business events preserve operational causality;
- object versions preserve submitted and governed domain state;
- accounting events preserve lifecycle transitions;
- posted journals and reporting versions remain immutable authoritative
  accounting records; and
- current projections are derived conveniences.

### 6.2 Restart and rebuild proof

For each canonical case, the milestone must compare:

```text
terminal state before shutdown
=
terminal state loaded after restart
=
terminal state after projection rebuild
```

Equality is semantic and content-addressed. Storage row order, database page
layout, generated timestamps, and local paths are not part of the comparison.

## 7. Runtime Module Handoffs

Artifact G defines semantic contracts rather than wire schemas. Milestone 2
must define only the minimum internal runtime messages needed to execute the
canonical handoffs.

The design must preserve:

- exact contract and object versions;
- one authoritative publisher;
- read-only consumption;
- upstream and evidence references;
- accepted, rejected, blocked, and deferred outcomes;
- purpose-specific readiness pairing; and
- G-13/G-14 non-authoring boundaries.

### 7.1 Observation must follow execution

The runtime boundary recorder must observe application-port calls that actually
occurred. It must not construct the expected C-001 or CT-1 G trace from a known
terminal state.

The same execution should independently produce:

```text
authoritative state changes
+ module handoff observations
+ traceable evidence references
```

Removing or replacing the observer must not change the state transition.

### 7.2 Minimum message rule

A runtime message field is permitted only when it is required to:

- identify the exact semantic contract;
- identify publisher and intended consumer;
- pin an exact subject or product version;
- express command or outcome identity;
- preserve causation, upstream lineage, purpose, scope, or evidence; or
- prove one Milestone 2 acceptance criterion.

The milestone must not turn Artifact G into fourteen speculative public API
schemas.

## 8. Evidence Boundary

Milestone 2 needs a runtime evidence port but not a production document
management system.

The minimum port must distinguish:

- a declared evidence identity and hash;
- committed content bytes that can be cryptographically verified;
- an unavailable body whose hash is declaration-only; and
- a verification result tied to exact input and rule versions.

The two June reporting proof bodies remain content-byte verified. Additional
content may be committed only where a Milestone 2 acceptance proof genuinely
requires it. The runtime must not claim that every declared `EVD-*` hash has a
resolved preimage.

## 9. Parameterised Canonical Cases

### 9.1 C-001 family

The runtime must accept a recognition-due business event and configuration that
are semantically equivalent to C-001 without requiring the literal canonical
identifiers.

It must still prove:

- one and only one business event reaches posting-rule evaluation;
- the automated proposal remains identifiable when submitted but unposted;
- the hard-closed period is not reopened;
- the correction posts in an eligible open correction period;
- the original reporting version remains retrievable;
- the restated version presents the quantified prior-period adjustment;
- readiness attaches to the exact reporting product and purpose; and
- an approved decision returns only as a new business-event candidate.

### 9.2 CT-1 family

The runtime must accept an eligible immutable wrong-customer journal projection
and opaque validated directive without requiring J-010, Vega, Orion, J-011, or
J-012 as literal identifiers.

It must still prove:

- the G-13 projection hash binds the reversal input before line comparison;
- the reversal is equal and opposite by account, dimensions, currency, side,
  and amount;
- the replacement uses the corrected customer identity;
- both correction journals are balanced and immutable;
- the combined control-account movement is zero; and
- no correction constructor invokes the business-event posting-rule evaluator.

### 9.3 Canonical compatibility

When supplied with the canonical C-001 and CT-1 inputs, the runtime must still
reproduce the ratified Artifact F bytes and terminal semantic digests. Generic
execution must not weaken exact canonical replay.

## 10. Existing Asset Disposition

Milestone 2 begins with a deliberate disposition review. Existing code is not
promoted into the runtime merely because it already works in the harness.

| Asset | Initial disposition | Constraint |
|---|---|---|
| Canonical JSON and hashing | Reuse candidate | Must remain independent of Pydantic field order and storage serialization. |
| Artifact F strict contracts | Reuse candidate | External payload boundary only; no silent defaults or coercion. |
| Pure planner semantics | Extract/adapt candidate | One guard implementation must remain demonstrably equivalent to H3. |
| Dispatcher transaction semantics | Extract/adapt candidate | Persistent commit must preserve H4 atomicity and idempotency. |
| Immutable harness state | Reference model | Do not treat an in-memory test aggregate as the persistence schema. |
| Scenario-local constructors | Replace with application services | Preserve typed derivation; remove fixture and literal-ID dependence. |
| H0-H7 runners | Validation only | Runtime must not import or call them. |
| Canonical fixtures | Acceptance evidence | Never become seed data required for normal runtime startup. |
| Manual G trace tables | Validation oracle | Replace runtime use with observations emitted by actual application handoffs. |
| Assertion report | Conformance output | Do not turn it into an operational monitoring or audit-workpaper product. |

No source file should move packages until equivalence tests establish whether
it is a reusable kernel asset or a harness-specific reference implementation.

## 11. Proposed Build Sequence

### Phase 0 - Design closure

Produce and ratify:

- the runtime application command/query map;
- authoritative-record and projection ownership map;
- persistence port and transactional unit-of-work contract;
- minimum Artifact G runtime-message contracts;
- restart, rebuild, and migration semantics;
- runtime evidence port;
- parameterised C-001 and CT-1 specifications; and
- the Milestone 2 executable acceptance catalog.

No runtime implementation begins until these artefacts pass a contradiction
review against C-001, CT-1, and Artifacts C through H.

### Phase 1 - Characterise and separate the kernel

Status: Complete 2026-08-05. See
`docs/roadmap/milestone-2-phase1-kernel-separation.md`.

- add black-box equivalence tests around reusable Milestone 1 semantics;
- define the runtime package boundary;
- separate reusable contracts and pure domain behaviour from H-layer code;
- keep all canonical fixture and report behaviour unchanged; and
- prove H0 through H7 still pass.

This phase changes dependency direction, not domain behaviour.

### Phase 2 - Persistence port and in-memory parity

Status: Complete 2026-08-05. See
`docs/roadmap/milestone-2-phase2-persistence-parity.md`.

- define repository and unit-of-work ports;
- implement an in-memory adapter through those ports;
- run the existing command paths without direct `HarnessState` mutation;
- prove atomicity, deduplication, effect idempotency, and G-14 parity; and
- preserve exact terminal digests.

The port is proven before a database product shapes it.

### Phase 3 - Transactional persistent adapter

Status: Complete 2026-08-05. See
`docs/roadmap/milestone-2-phase3-transactional-persistence.md` and
`docs/roadmap/milestone-2-post-phase3-cohesion-audit.md`.

- select one storage engine through a recorded decision;
- implement schema migrations and exact uniqueness constraints;
- persist authoritative records and projection checkpoints;
- inject transaction failure before commit;
- restart the process and reload exact state; and
- delete and rebuild projections from declared authoritative inputs.

This phase ends with persistence and rebuild proofs, not module workflows.

### Phase 4 - Parameterised application services

Status: Complete 2026-08-05. See
`docs/roadmap/milestone-2-phase4-parameterised-application-services.md`.

- replace scenario-local orchestration with runtime commands and queries;
- inject clock and identity generation through deterministic ports;
- execute non-canonical instances of the C-001 and CT-1 families;
- preserve exact canonical compatibility; and
- reject inputs that would require an undeclared event type or lifecycle.

### Phase 5 - Executed module contracts

Status: Complete 2026-08-05. See
`docs/roadmap/milestone-2-phase5-executed-module-contracts.md` and
`docs/roadmap/milestone-2-post-phase5-cohesion-audit.md`.

- route canonical workflows through the in-process G contract ports;
- generate boundary observations from real handoffs;
- enforce publisher, consumer, version, evidence, and readiness rules at the
  boundary;
- prove G-13 and G-14 remain outside Artifact F authorship; and
- reproduce the C-001 and CT-1 contract traces without manual trace assembly.

### Phase 6 - Read models and end-to-end traceability

Status: Complete 2026-08-05. See
`docs/roadmap/milestone-2-phase6-read-models-traceability.md`.

- build exact-version queries;
- build labelled current-state projections;
- trace statement value to reporting version, journal, proposal, posting rule,
  business event, source reference, and evidence;
- prove as-published and as-restated retrieval after restart; and
- prove purpose-specific readiness is never inferred from a predecessor.

These are programmatic query models, not public dashboards.

### Phase 7 - Acceptance, audit, and closure

Status: Complete 2026-08-10; M2-A01 through M2-A19 pass from a clean checkout.
See
`docs/roadmap/milestone-2-phase7-acceptance-closure.md`.

- run the original H0-H7 conformance suite unchanged;
- run the Milestone 2 acceptance catalog;
- compare clean-start, restart, and rebuilt semantic results;
- run a hard cross-artifact and implementation audit;
- update current-status documentation; and
- emit one deterministic machine-readable Milestone 2 report.

## 12. Proposed Acceptance Criteria

Milestone 2 is complete only when all of the following are independently
observable:

- M2-A01: the runtime has one in-process application boundary and one
  authoritative transactional persistence boundary;
- M2-A02: only an admitted `business_event` can invoke posting-rule evaluation;
- M2-A03: accounting events, G-14 dispositions, governance outputs, and Pythia
  outputs are structurally rejected from that input;
- M2-A04: the pure planner remains the only transition-guard implementation;
- M2-A05: persistent command retry and independent effect idempotency survive
  process restart;
- M2-A06: injected failure commits neither authoritative records nor projection
  updates;
- M2-A07: every current projection can be deleted and rebuilt from its declared
  authoritative records;
- M2-A08: clean-start, restart, and rebuilt canonical states have identical
  semantic digests;
- M2-A09: parameterised C-001 completes without literal canonical identities
  and without reopening the hard-closed period;
- M2-A10: parameterised CT-1 completes without literal canonical identities and
  binds the G-13 source hash before reversal comparison;
- M2-A11: canonical inputs remain byte-compatible with the ratified Artifact F
  fixtures and preserve their terminal digests;
- M2-A12: C-001 and CT-1 G traces arise from executed application handoffs, not
  post-hoc expected trace construction;
- M2-A13: every controlled use binds an exact data-product version to an exact,
  purpose-specific readiness version;
- M2-A14: evidence reporting distinguishes content-byte verification from
  declared-hash consistency;
- M2-A15: the runtime imports no H-layer runner, fixture loader, scenario driver,
  or manually declared trace table;
- M2-A16: H0 through H7 still pass without weakening an assertion;
- M2-A17: no database, module, adapter, or query path creates a second owner for
  an Artifact G lifecycle;
- M2-A18: no public API, UI, authentication system, event broker, or new business
  process is introduced; and
- M2-A19: one locked clean-checkout command reproduces the complete Milestone 1
  and Milestone 2 reports with a non-zero exit for any failure or block.

## 13. Cohesion-Audit Checkpoints

Milestone 2 pauses for hard review at three points:

1. **After Phase 0, before kernel extraction** - prove that the runtime contract
   does not reinterpret Artifacts C through H or smuggle in a new taxonomy.
2. **After Phase 3, before parameterised workflows** - prove that persistence,
   migrations, projections, transaction boundaries, and restart behaviour do
   not alter domain semantics.
3. **After Phase 6, before milestone closure** - reconcile design, code,
   database schema, executed G traces, evidence claims, tests, generated reports,
   and public documentation.

Each checkpoint distinguishes historical wording from stale current claims.
Material decisions enter the append-only decision log. Reversible library and
folder-layout choices do not become architecture decisions merely because the
first runtime uses them.

## 14. Explicit Non-Goals

Milestone 2 does not introduce:

- an HTTP or GraphQL API;
- a React or other public user interface;
- authentication, authorisation, tenancy, or user administration;
- background workers or orchestration;
- a message broker or distributed event bus;
- concurrent or exactly-once distributed-delivery claims;
- a second database or database-per-module architecture;
- production evidence/document storage;
- operational monitoring, alerting, or workpaper generation;
- an expanded business-event or accounting-event taxonomy;
- a new O2C variation beyond parameterising C-001;
- P2P, payroll, treasury, consolidation, tax, or intercompany processes;
- migration of the legacy standalone Atlas repository; or
- a public deployment.

Those remain candidate later milestones only after the persistent runtime spine
is proven.

## 15. Design Decisions Resolved

Artifacts J through N and ADR-028 resolve the storage engine, internal G
messages, finite J-AR02 registry, authority ports, migration compatibility,
evidence treatment, readiness shape, persistence semantics, and rebuild map.
The complete C-001 loop through Pythia remains binding while its implementation
must use only the minimum ratified message bodies.

Remaining work is implementation sequencing, not an unresolved design fork.
The post-Phase-6 cohesion audit found six implementation-conformance blockers.
The bounded F1/F2 pass resolved semantic availability and exact pre-scope
import prerequisites; the F6 pass made Artifact G publication closure mandatory
and atomic; the F3/F4 pass completed exact lifecycle reads and directed J-P11
traversal; and the F5 pass completed candidate custody, admission, and I-Q01.
The follow-up audit passes, leaving Phase 7 acceptance and closure work.

## 16. Ratification Questions

Before this roadmap becomes binding, review should challenge:

- whether any phase bundles work that can be deferred without breaking the
  complete C-001 platform loop;
- whether any proposed C-001 runtime message contains fields beyond the exact
  G-01 through G-12 proof need;
- whether Pythia's approved-decision feedback is implemented as one bounded
  handoff rather than the start of a speculative planning workflow framework;
- whether the source of truth is stated precisely enough to avoid false
  event-sourcing claims;
- whether the persistence adapter can remain domain-neutral without weakening
  invariant enforcement;
- whether canonical byte compatibility and non-canonical parameterisation can
  coexist without scenario-specific branches; and
- whether any proposed query is actually an early dashboard requirement in
  disguise.

## 17. Implementation Progress and Next Move

Phases 0 through 6 are complete, and the Phase 6 follow-up cohesion gate passes.
The runtime kernel, Artifact K persistence
port, SQLite adapter, deterministic authority-backed rebuild, and parameterised
C-001/CT-1 accounting services and the ratified in-process Artifact G contract
ports are executable. Real publish/consume handoffs now generate removable
post-commit observations, while J-AR13 remains authoritative. Exact and
labelled-current reads now operate over revision-pinned authority, June v1/v2
remain independently retrievable, verified statement values trace through the
accounting chain to source and evidence, and planning cannot infer readiness
from a predecessor. The post-Phase-6 cohesion audit found six blocking gaps.
Semantic availability and pre-scope import were resolved by the bounded F1/F2
correction, mandatory G-publication closure was resolved by the F6 pass, and
directed trace plus exact/as-of query semantics were resolved by the F3/F4
pass. The F5 pass completes ordinary candidate custody, derived admission,
G-01 firewall enforcement, and I-Q01 restart/rebuild coverage. The Phase 7
acceptance candidate now consolidates the unchanged H0-H7 report, all nineteen
M2 criteria, full-suite and Ruff gates, and two-run C-001/CT-1 durable semantic
proofs. The committed candidate passes M2-A01 through M2-A19 through the locked
clean-checkout command. Milestone 2 is complete; the public product layer is the
next separately bounded milestone.

### Historical Phase 0 design trail

The remainder of this section records the order in which Artifacts J through N
closed the former design questions. Statements such as "next artifact" and
"selection remains deferred" are historical decisions at that point in the
sequence, not current implementation instructions. The current instruction is
the Phase 5 entry above.

Its proposal-identity/lifecycle question and predecessor-reporting-version
bootstrap question are resolved in the ratified Artifact J v0.2:

`docs/architecture/authoritative-record-projection-map.md`

Artifact J separates immutable proposal treatment from event-derived lifecycle
state and admits predecessor v1 through an evidenced, time-gated pre-scope
import. The next design artifact must define the database-independent
persistence port and transactional unit-of-work contract before any physical
schema is designed.

Artifact K v0.2.2 ratifies that contract:

`docs/architecture/persistence-port-unit-of-work-contract.md`

It defines one shared persistence boundary, six closed persistence modes, typed
record facets, command-scoped atomic commit, retry and effect semantics, bounded
administrative admission, and isolated projection rebuild with atomic promotion.

The next design artifact must define the minimum internal runtime-message bodies
for G-01 through G-14 and the approved-decision return, and populate the finite
J-AR02 module-product discriminator registry. No database, physical schema, or
runtime package may be selected until the remaining Milestone 2 Phase 0
artifacts pass review.

Artifact L v0.2 ratifies those contracts:

`docs/architecture/internal-runtime-message-contracts.md`

It defines the strict J-AR13 envelope, exact G-01 through G-14 bodies, a finite
twenty-entry J-AR02 registry, and the non-G approved-decision return. Its v0.1
review identified two inherited CT-1 producer gaps. Corrective Artifact I
v0.2.1 and Artifact K v0.2.1 drafts now add the Hermes G-03
customer-identity reconciliation before Argus testing and the Aegis G-08 issue
update after verification through their ordinary command and unit-of-work
boundaries. The three drafts require one joint contradiction review before
ratification.
