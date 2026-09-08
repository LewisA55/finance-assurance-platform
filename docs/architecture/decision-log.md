# Architecture Decision Log

This log is append-only. Supersede decisions with later entries rather than rewriting history.

## ADR-001: Use One Platform With Product Lenses

Accepted.

The project is one Finance & Assurance Platform, not separate applications for Atlas, Argus, Aegis, Hermes, and Pythia.

## ADR-002: Preserve Five Platform Invariants

Accepted.

The five invariants in `AGENTS.md` govern the design across implementation choices.

## ADR-003: Use Hybrid Accounting Ontology

Accepted.

Business events are the causal substrate. Proposed journals are derived records. Posting, reversal, restatement, and publication actions are first-class accounting events because they carry governance significance.

## ADR-004: Enforce Event Stream Firewall

Accepted.

`business_event` is the only object class permitted to drive posting-rule evaluation. `accounting_event` can never recursively trigger the posting engine.

## ADR-005: Route C-001 Through Restatement

Accepted.

C-001 is not changed to demonstrate reversal. It proves submitted-but-unposted proposal preservation and hard-close restatement. CT-1 proves reversal and replacement.

## ADR-006: Use Finance & Assurance Platform as Public Project Name

Accepted.

The public-facing project name is Finance & Assurance Platform. "Synthetic finance and assurance digital twin" remains the product thesis and architecture descriptor.

## ADR-007: Ratify `restatement_case` as the Ninth Accounting Object

Accepted.

Restatement requires durable identity, affected-period scope, linked adjustment journals, approval evidence, a frozen presentation-adjustment manifest, and publication state. Manifest entries remain owned value records rather than an independently stateful tenth object.

## ADR-008: Make Close Deferral an Explicit Proposal Disposition

Accepted.

A submitted proposal cannot remain implicitly orphaned at hard close. An authorised close exception emits `proposal.deferred` and moves that proposal version to `DEFERRED`. The proposal remains historically submitted and unposted for completeness testing.

## ADR-009: Separate Ledger Correction From Prior-Period Presentation

Accepted.

A restatement-adjustment journal is posted in an eligible ledger period. A frozen manifest within the restatement case maps exact journal-line effects to the prior period re-presented in a successor reporting version. The original hard-closed ledger period and original reporting version remain unchanged.

## ADR-010: Route Reversals and Replacements Through Journal Proposals

Accepted.

Reversal and replacement constructors are separate from the business-event posting engine but still create frozen proposals that pass through submission, approval, and posting. Reversal lines are mechanically derived as equal and opposite to the referenced immutable journal.

## ADR-011: Use Event-Family-Specific Authority and Evidence

Accepted.

Every accounting event requires explicit authority and reproducible basis, but not every event requires human approval or a posting-rule version. Required evidence depends on the event family.

## ADR-012: Freeze the Artifact F Payload Boundary

Accepted.

Artifact F covers the nine accounting objects and ten distinct accounting-event types instantiated across seventeen canonical event instances. Contracts use integer minor units with ISO 4217 currency, reject undeclared fields by contract version, and use `debit_minor` and `credit_minor` consistently. Every event carries `event_id` and `command_id`; explicit idempotency keys are required only for journal posting and reporting publication.

`AUTOMATED_POSTING` remains in scope as a proposal origin but is excluded as an unexercised posted-journal class. Reporting versions reference immutable hashed content without defining financial-statement structure. Aegis-owned objects remain opaque typed references. C-001 fixes `2026-07` as its correction ledger period and `2026-06` as its presented period for scenario reproducibility.

## ADR-013: Strengthen Artifact F Without Expanding Its Authoring Boundary

Accepted.

Artifact F includes a read-only J-010 line projection solely to prove that J-011 is mechanically equal and opposite. The projection is not a tenth accounting object, is marked non-authored, and cannot be emitted by the domain serializer. Statement bodies remain external; June v1-to-v2 arithmetic is explicitly deferred to runtime content resolution.

Publication events use the transitioning restatement case as their subject and carry the created reporting-version reference in their payload. Proposal-submission derivation authority uses one discriminated shape. Logical command identity remains stable across delivery retries, while posting and publication idempotency keys separately protect effects across distinct command attempts.

## ADR-014: Ratify Artifact F v0.2

Accepted.

Artifact F v0.2 satisfies the closed-serializer criterion for C-001 and CT-1. The authored object boundary remains nine accounting objects and ten accounting-event types across seventeen canonical event instances. J-010 is available only through a non-authored proof projection, and statement-body arithmetic remains a runtime-resolved assurance test.

The remaining retry and executable projection-binding checks are implementation backlog items and do not block design ratification.

## ADR-015: Ratify Artifact G v0.2

Accepted.

Artifact G v0.2 fixes one authoritative writer for every in-scope lifecycle and
defines fourteen version-pinned, read-only publish/consume contracts across the
shared enterprise substrate and the five module lenses. The substrate remains
infrastructure rather than a sixth product module.

Source domains own business-event meaning; Hermes owns admission and lineage;
Atlas owns all accounting lifecycles; Argus owns machine observations and
exceptions; Aegis owns governance conclusions, directives, and purpose-specific
readiness; and Pythia owns planning and decision products. Artifact F actor
roles execute within Atlas when acting on Artifact F state.

G-13 exposes J-010 only as a non-authoring referenced-state projection, without
expanding Artifact F's object boundary. G-14 makes a pre-construction command
rejection observable without inventing an accounting-event subject. Neither
contract may enter the posting engine.

C-001 proves G-01 through G-12 and returns an approved operational decision
through normal business-event admission. CT-1 proves G-13 while Atlas remains
the only writer of the corrective journals. G-10 through G-12 are not required
where CT-1 has no controlled planning use.

The C-001 proof language in Artifact C is aligned with this ownership ruling:
Aegis publishes the issue and remediation directive; Atlas validates that
authority and opens RC-001 through `restatement.proposed`.

## ADR-016: Bound Cryptographic Verification to Reporting Proof Bodies

Accepted.

Milestone 1 cryptographically verifies only the two canonical June reporting
proof bodies used to establish the GBP 10,000 v1-to-v2 bridge. Their compact,
lexically key-sorted UTF-8 body bytes are committed with reproducible SHA-256
values.

All other `evidence_ref.content_hash` values remain declared fixture values.
The harness checks their format, stable reference-to-hash consistency,
immutability, and any exact equality required by a ratified test. It does not
claim that their absent content bytes were cryptographically verified.

This bounded treatment preserves invariant 5 for the numerical reporting claim
that the first harness actually proves while avoiding a premature evidence
storage design. Artifact F advances to v0.2.1 only as a reporting-proof fixture
revision; its nine-object, ten-event-type, seventeen-instance, and closed
serializer boundaries do not change.

## ADR-017: Ratify Artifact H v0.3 and Close Milestone 0

Accepted.

Artifact H v0.3 defines a finite first executable validation boundary with
separate conformance and execution modes, eight ordered test layers H0 through
H7, eighteen design-ratification checks, and complete mappings to the in-scope
Artifact E, F, and G obligations.

Ratification confirms that the Milestone 1 suite is internally consistent and
implementable. It does not claim that the unbuilt harness already passes its
runtime acceptance tests. Milestone 1 must reproduce all seventeen canonical
accounting-event instances, execute C-001 and CT-1 from declared bootstrap
state, and run through one documented clean-checkout command.

Rejected commands leave accounting-domain and financial-effect state
unchanged, while the first delivery records one immutable command result and,
where applicable, one G-14 disposition. A retry returns that result without
duplicating either record.

Only the two June reporting bodies are cryptographically verified. Evidence
references without committed bodies remain declared-consistency-only and may
not be reported as content-byte verified. Successful Artifact E transitions
outside Artifact F's closed event set remain explicitly deferred.

Database, API, UI, deployment, distributed-systems, and broader product-module
decisions remain outside this milestone. With Artifacts C, E, F, G, and H
aligned against C-001 and CT-1, Milestone 0 is complete.

## ADR-018: Ratify Artifact I v0.2

Accepted.

Artifact I v0.2 fixes one finite in-process application boundary for the
parameterised C-001 runtime slice. Its eleven rulings, twenty-three commands,
twenty queries, twenty-six ordered execution steps, and twenty-two acceptance
criteria are contiguous, uniquely defined, and internally cross-referenced.
Every catalogued command is exercised by the canonical sequence.

The twenty-six steps reuse exactly three command types: candidate assessment,
proposal submission, and reporting-readiness assessment. This reuse reflects
their parameterised semantics and does not create hidden command variants.
Each command still has one authoritative target owner and one local atomic
transaction.

Only an admitted `accounting.recognition.due` business event may enter Atlas's
posting-rule evaluator. Correction construction remains a separate typed path.
Pythia owns its recommendation but cannot approve it; the affected source
business domain independently approves operational action and may author a new
candidate that returns through ordinary Hermes admission.

CT-1 reuses the same application boundary. Its reversal constructor must bind
the exact G-13 projection source hash to the declared reversal input hash before
deriving or comparing equal-and-opposite lines.

Ratification does not select a database or persistence representation. Proposal
treatment identity versus lifecycle state and predecessor reporting-version
bootstrap provenance remain explicit blockers for the authoritative-record and
projection artifact. No physical persistence schema may be ratified before both
are resolved.

## ADR-019: Ratify Artifact J v0.2

Accepted.

Artifact J v0.2 defines seventeen immutable authoritative-record families and
thirteen rebuildable projections for all twenty-six Artifact I execution steps.
It separates one proposal's immutable treatment version from its event-derived
lifecycle state, using the construction command result for `DRAFT` and the last
accepted accounting-event identity for later exact-state tokens. Artifact F
payloads remain exact derived views and its closed external boundary is
unchanged.

Candidate receipts and durable G publications retain or resolve exact canonical
bytes, their contract and canonicalization versions, and matching hashes so
restart does not depend on external redelivery. Initial accounting-period state
uses the immutable base-record identity and canonical hash for optimistic
concurrency; later lifecycle writes use the last accepted event identity.

The predecessor reporting version enters through one typed, bounded pre-scope
admission operation after the exact affected-period hard close. Before admission
it remains sealed external input and is invisible to application, planner,
query, projection, trace, and contract-read paths. Admission atomically commits
the reporting core, import attestation, verified proof content, and imported
G-06 publication. It emits no accounting event, consumes no ordinary
publication effect key, and cannot become a general import framework.

Every accepted multi-record write validates explicit cross-record bindings
before commit and again during rebuild. Command results, effect claims, G-14
dispositions, import attestations, and contract publications are authoritative
coordination records rather than disposable projections. The approved-decision
return binds exact source-domain approval and candidate versions without
inventing another Artifact G contract.

Ratification fixes semantic persistence ownership, rebuild sources, concurrency
tokens, availability, and atomic binding requirements. It does not select a
database, define physical tables, introduce a public API, expand Artifact F, or
ratify repository interfaces. Those interfaces must be defined next through a
database-independent persistence-port and transactional unit-of-work contract.

## ADR-020: Ratify Artifact K v0.2

Accepted.

Artifact K v0.2 fixes one database-independent persistence boundary with six
closed modes: command unit of work, runtime-baseline admission, pre-scope
reporting import, referenced-journal admission, query session, and rebuild
session. Authoritative records, immutable events, coordination records,
contract publications, and rebuildable projections retain distinct typed
facets. No repository or store may commit independently of its enclosing unit
of work.

Command deduplication and effect idempotency remain separate mechanisms. Exact
state tokens and availability rules govern planning and commit, and successful
command closure may reference only outputs staged and committed by that command.
For authoritative-token conflicts, the adapter reports an exact conflict
snapshot, the target command owner constructs the J-AR14 rejection, and the
adapter validates and atomically commits the rejection-only result. The adapter
does not author semantic rejections.

The three administrative write modes have explicit typed interfaces, distinct
conflict and receipt outcomes, and cannot emit J-AR14 command rejections. The
core conformance suite K-T01 through K-T42 applies to every adapter; durable
adapters additionally prove K-D01 through K-D06 across a real process restart.
The CT-1 mapping exercises the ordinary persistence boundary row by row,
including the required bind-before-derive reversal ordering.

The module-product discriminator registry is fixed as an interface only.
Artifact L must populate its finite entries and define the minimum internal
runtime-message bodies for G-01 through G-14 and the approved-decision return.
Rebuilds use isolated generations and atomic promotion; verified proof content
remains distinct from declared-format-only evidence hashes.

Ratification does not select a database, define a physical schema, introduce a
public API, or require distributed transactions. Those choices remain deferred
until the remaining Milestone 2 Phase 0 contracts are ratified.

## ADR-021: Ratify the CT-1 Producer Repair in Artifacts I v0.2.1 and K v0.2.1

Accepted.

Artifact I v0.2.1 adds two missing owner-specific CT-1 commands without changing
its general application boundary. Hermes owns
`ReconcileCashApplicationIdentity` and publishes the exact G-03
customer-identity reconciliation before Argus testing. Aegis owns
`UpdateCashApplicationIssue`, consumes the exact Argus G-07 verification, and
publishes the successor issue through G-08. Neither command invokes the
business-event posting engine or creates an Artifact F object or event.

Artifact K v0.2.1 maps both commands through the existing
`CommandUnitOfWork`. Each command atomically commits its owner-authored J-AR02
version, exact J-AR13 publication, J-AR14 command result, and permitted
projections. CT-1 therefore proves G-03 before assurance and G-08 after
verification without a scenario-private repository, commit path, or workflow
framework.

The correction is limited to command coverage and persistence mapping. It does
not change the twenty-two Artifact K rulings, six persistence modes, forty-one
acceptance criteria, forty-two core tests, six durable tests, or Artifact F's
closed payload boundary.

## ADR-022: Ratify Artifact L v0.2

Accepted.

Artifact L v0.2 fixes one strict J-AR13 semantic publication envelope, exact
version-1 bodies for G-01 through G-14, a finite twenty-entry J-AR02
module-product discriminator registry, and the bounded source-domain
approved-decision return. It defines semantic contracts rather than HTTP,
broker, database-row, or public API schemas.

The registry gives every in-scope product one owner, validator, persistence
mode, baseline eligibility treatment, and command-output treatment. G-04 and
G-05 reuse Artifact F bodies exactly; G-13 remains non-authoring referenced
state; G-14 remains a subject-free pre-construction rejection; readiness remains
purpose-specific; and operational approval remains outside Artifact G.

The C-001 proof uses all required G-01 through G-12 bodies and G-14. The CT-1
proof uses the ratified Hermes G-03 producer before Argus testing and the Aegis
G-08 producer after verification while preserving bind-before-derive reversal
ordering and excluding G-10 through G-12. The artifact introduces no generic
workflow, message broker, physical persistence design, or new Artifact F field,
object, or event.

The next design artifact must define deterministic clock, identity-allocation,
and sequence-allocation ports. Database selection remains deferred.

## ADR-023: Ratify Artifact M v0.2

Accepted.

Artifact M v0.2 fixes three explicit deterministic authority ports for time,
identity, and sequence. Twenty-five rulings separate economic and source facts
from governed action, recording, and semantic-as-of time; require stable
application-supplied command identity; use bulk named identity slots; derive
initial and successor versions from exact predecessor state; and preserve
Artifact K's independent command, state-token, and effect arbitration.

The ratification review resolves the draft's circular output-shape dependency.
Each command invokes its pure planner or typed owner operation exactly once,
derives the closed output-slot shape from that typed result, obtains identity and
sequence grants, and materializes records without re-running guards or domain
rules. The initial restatement case receives one family identity but advances
only through accounting-event state tokens. J-AR15 claim identity remains a
derivation of its exact effect class and key, required J-AR12 evidence
declarations receive explicit slots, and pre-scope import preserves its supplied
J-AR11 `import_id`.

One sealed authority-profile candidate is permitted only for runtime-baseline
bootstrap; every ordinary mode requires exact committed and semantically
available J-AR04 configuration. The authority seed exists before grants, the
deterministic time grant completes Artifact K's command input digest, and
identity/sequence grants remain construction inputs rather than caller input.

Ratification closes twenty-five rulings, forty-five conformance tests, forty-one
acceptance criteria, all six Artifact K modes, all twenty-six C-001 steps, and
the CT-1 producer repairs. The seventeen canonical accounting-event identities
and timestamp pairs match the committed fixtures exactly. No Artifact F object
or event, G contract, J-AR family, Artifact L discriminator, workflow class,
database, physical schema, or provider implementation is added.

The next design artifact must define migration compatibility and persisted
contract-version semantics. Database selection remains deferred.

## ADR-024: Ratify Artifact N v0.2

Accepted.

Artifact N v0.2 fixes semantic compatibility for authoritative records across
runtime and contract evolution without selecting a physical migration tool.
Original bytes, typed contract coordinates, canonicalization treatment,
identity, and semantic hashes remain immutable. A runtime must pass one global
compatibility preflight over the complete persisted inventory before serving
semantic commands, queries, publications, or rebuilds; Milestone 2 defines no
partial read-only degradation mode.

Exact historical reads remain primary. Any forward adaptation is an explicit,
labelled, non-authoritative view produced by one governed direct adapter. The
application resolves exact semantically available J-AR04 configuration into an
immutable configuration set before invoking the pure adapter. Compatibility
cannot cross event streams, truth layers, semantic ownership, evidence status,
or the business-event posting firewall.

J-AR14 retains executed compatibility bindings as input-derivation provenance,
separate from `committed_outputs[]`; Artifact K output closure therefore still
enumerates only records created by the command. Native output coordinates and
complete compatibility intents bind command identity before planning, while
retry resolves the original J-AR14 before loading or adapting content. State
tokens, J-AR15 effect keys, and upstream authoritative references do not
migrate.

The sealed runtime-baseline port admits only the initial compatibility policy.
Milestone 2 defines no live successor-policy admission or activation path; any
future maintenance capability requires an explicit typed contract and separate
ADR. Current C-001 and CT-1 remain exact version-1 paths, while a
validation-only value proves adapter mechanics without creating a speculative
domain contract or persistence permission.

Ratification closes twenty-eight rulings, fifty-four conformance tests, and
forty-five acceptance criteria. It does not define a database, physical schema,
deployment topology, public API, retention policy, or production migration
workflow. The next gate is the full Milestone 2 Phase 0 cohesion audit across
Artifacts I through N before runtime-package or persistence implementation
selection.

## ADR-025: Close the Milestone 2 Phase 0 Cohesion Audit

Accepted.

The Phase 0 semantic audit across Artifacts I through N found two blocking
contradictions and two required cohesion corrections. All four are resolved by
one bounded documentation patch without adding a command, query, event, record
family, projection, G body, J-AR02 discriminator, persistence mode, authority
slot, compatibility coordinate, or physical implementation decision.

Artifact I v0.2.2 removes G-04 from Hermes I-C07 consumption so the recognition
reconciliation uses only the source schedule, Hermes admission/lineage state,
and Atlas G-05 lifecycle events. Argus remains the G-04 consumer that freezes
and tests the exact accounting-object population. The same amendment aligns the
current C-001 sequence with Artifact J's immutable treatment plus event-derived
lifecycle model and restores the required G-04/G-05 publications at I-S18 and
I-S19.

Artifact K v0.2.2 adds the exact Hermes G-03/L-MP05 reconciliation to the CT-1
Argus test row. Artifact M v0.2.1 corrects its C-001 proof to place J-560 and
journal-line identity grants after the typed posting outcome fixes output shape
and before materialization. Artifact N v0.2.1 changes no compatibility ruling;
it aligns its binding-source references to the corrected I, K, and M patch
levels.

All numbered inventories remain unchanged: I retains eleven rulings,
twenty-three commands, twenty queries, twenty-six execution steps, and
twenty-four acceptance criteria; K retains twenty-two rulings, six modes,
forty-two core tests, six durable tests, and forty-one acceptance criteria; M
retains twenty-five rulings, forty-five tests, and forty-one acceptance criteria;
and N retains twenty-eight rulings, fifty-four tests, and forty-five acceptance
criteria.

The audit confirms the event firewall, ownership boundaries, authoritative
closure, deterministic authority ordering, compatibility semantics, evidence
treatment, purpose-specific readiness, C-001, CT-1, and M2-A01 through M2-A19.
Milestone 2 Phase 0 is complete. Phase 1 may characterize and separate the
reusable kernel, but database selection remains deferred until the in-memory
persistence-port parity gate is complete.

## ADR-026: Separate the Reusable Runtime Kernel from the Validation Harness

Accepted.

`finance_assurance.runtime` is the dependency root for reusable Milestone 1
semantics. It owns canonical serialization, deterministic value hashing, the
strict Artifact F contracts, stable semantic rejection values, the admitted
non-authored referenced-journal projection model, and the single pure Artifact E
transition planner.

`finance_assurance.validation` remains the independent conformance harness. It
owns fixture ingestion, validation-library error translation, H0 through H7,
scenario replay, harness state, dispatch, boundary observation, and assertion
reporting. Compatibility facades preserve the ratified validation import paths,
but those facades resolve to the runtime-owned types and planner; they do not
duplicate behavior.

The dependency direction is mechanically enforced: no Python module under
`finance_assurance.runtime` may import `finance_assurance.validation`. A locked
black-box characterization covers twenty rejected guard executions and thirteen
accepted transitions. Their pre-extraction combined digest remains
`sha256:a8cb0dc06380a815febd301d1edba461803330607e016af73ae7ab7a686d4168`.

All seventy tests, Ruff, and the unchanged H0 through H7 command pass. This
decision changes package ownership and dependency direction only. It introduces
no repository, unit of work, persistent adapter, database, schema, migration,
public transport, workflow, or product surface. Phase 2 may now implement the
Artifact K persistence port and in-memory parity; database selection remains
deferred.

## ADR-027: Implement Artifact K Command Persistence Through One Unit of Work

Accepted.

Ordinary planner commands now execute through one database-independent
`CommandUnitOfWork`. The application supplies an immutable, version-bound
command context; the unit resolves prior results, exposes one stable read view,
accepts exactly one typed staged set, validates command closure, arbitrates
state tokens and effect keys, and commits or rolls back atomically.

The in-memory adapter holds its transaction lock from final arbitration through
commit or rollback. It returns factual stale/effect snapshots only; the runtime
application layer constructs the semantic rejection and the same unit validates
and commits that rejection-only set. This preserves Artifact K's separation
between storage facts and command-owner judgment.

`finance_assurance.runtime` now owns command execution and `InMemoryState`.
`finance_assurance.validation` retains compatibility facades for the unchanged
H0 through H7 suite, including the historical `HarnessState` name. No validation
module is imported by the runtime.

Phase 2 closes with seventy-eight passing tests, Ruff, and the full H0 through H7
report green. It proves atomic accepted and rejected commits, same-command retry,
version-bound identity conflict, effect idempotency including a two-unit race,
G-14 parity, rollback, clean receipts, and exact canonical replay.

This decision implements only Artifact K's ordinary command mode. The five
administrative, query, and rebuild modes remain ratified but not yet executable;
full Artifact K adapter conformance is required before Phase 3 closure. No
database, ORM, physical schema, migration, public API, authentication, broker,
outbox, external effect, or UI is introduced.

## ADR-024: Ratify Artifact N v0.2

Accepted.

Artifact N v0.2 fixes semantic compatibility for authoritative records across
runtime and contract evolution without selecting a physical migration tool.
Original bytes, typed contract coordinates, canonicalization treatment,
identity, and semantic hashes remain immutable. A runtime must pass one global
compatibility preflight over the complete persisted inventory before serving
semantic commands, queries, publications, or rebuilds; Milestone 2 defines no
partial read-only degradation mode.

Exact historical reads remain primary. Any forward adaptation is an explicit,
labelled, non-authoritative view produced by one governed direct adapter. The
application resolves exact semantically available J-AR04 configuration into an
immutable configuration set before invoking the pure adapter. Compatibility
cannot cross event streams, truth layers, semantic ownership, evidence status,
or the business-event posting firewall.

J-AR14 retains executed compatibility bindings as input-derivation provenance,
separate from `committed_outputs[]`; Artifact K output closure therefore still
enumerates only records created by the command. Native output coordinates and
complete compatibility intents bind command identity before planning, while
retry resolves the original J-AR14 before loading or adapting content. State
tokens, J-AR15 effect keys, and upstream authoritative references do not
migrate.

The sealed runtime-baseline port admits only the initial compatibility policy.
Milestone 2 defines no live successor-policy admission or activation path; any
future maintenance capability requires an explicit typed contract and separate
ADR. Current C-001 and CT-1 remain exact version-1 paths, while a
validation-only value proves adapter mechanics without creating a speculative
domain contract or persistence permission.

Ratification closes twenty-eight rulings, fifty-four conformance tests, and
forty-five acceptance criteria. It does not define a database, physical schema,
deployment topology, public API, retention policy, or production migration
workflow. The next gate is the full Milestone 2 Phase 0 cohesion audit across
Artifacts I through N before runtime-package or persistence implementation
selection.

## ADR-023: Ratify Artifact M v0.2

Accepted.

Artifact M v0.2 fixes three explicit deterministic authority ports for time,
identity, and sequence. Twenty-five rulings separate economic and source facts
from governed action, recording, and semantic-as-of time; require stable
application-supplied command identity; use bulk named identity slots; derive
initial and successor versions from exact predecessor state; and preserve
Artifact K's independent command, state-token, and effect arbitration.

The ratification review resolves the draft's circular output-shape dependency.
Each command invokes its pure planner or typed owner operation exactly once,
derives the closed output-slot shape from that typed result, obtains identity and
sequence grants, and materializes records without re-running guards or domain
rules. The initial restatement case receives one family identity but advances
only through accounting-event state tokens. J-AR15 claim identity remains a
derivation of its exact effect class and key, required J-AR12 evidence
declarations receive explicit slots, and pre-scope import preserves its supplied
J-AR11 `import_id`.

One sealed authority-profile candidate is permitted only for runtime-baseline
bootstrap; every ordinary mode requires exact committed and semantically
available J-AR04 configuration. The authority seed exists before grants, the
deterministic time grant completes Artifact K's command input digest, and
identity/sequence grants remain construction inputs rather than caller input.

Ratification closes twenty-five rulings, forty-five conformance tests, forty-one
acceptance criteria, all six Artifact K modes, all twenty-six C-001 steps, and
the CT-1 producer repairs. The seventeen canonical accounting-event identities
and timestamp pairs match the committed fixtures exactly. No Artifact F object
or event, G contract, J-AR family, Artifact L discriminator, workflow class,
database, physical schema, or provider implementation is added.

The next design artifact must define migration compatibility and persisted
contract-version semantics. Database selection remains deferred.

## ADR-021: Ratify the CT-1 Producer Repair in Artifacts I v0.2.1 and K v0.2.1

Accepted.

Artifact I v0.2.1 adds two missing owner-specific CT-1 commands without changing
its general application boundary. Hermes owns
`ReconcileCashApplicationIdentity` and publishes the exact G-03
customer-identity reconciliation before Argus testing. Aegis owns
`UpdateCashApplicationIssue`, consumes the exact Argus G-07 verification, and
publishes the successor issue through G-08. Neither command invokes the
business-event posting engine or creates an Artifact F object or event.

Artifact K v0.2.1 maps both commands through the existing
`CommandUnitOfWork`. Each command atomically commits its owner-authored J-AR02
version, exact J-AR13 publication, J-AR14 command result, and permitted
projections. CT-1 therefore proves G-03 before assurance and G-08 after
verification without a scenario-private repository, commit path, or workflow
framework.

The correction is limited to command coverage and persistence mapping. It does
not change the twenty-two Artifact K rulings, six persistence modes, forty-one
acceptance criteria, forty-two core tests, six durable tests, or Artifact F's
closed payload boundary.

## ADR-022: Ratify Artifact L v0.2

Accepted.

Artifact L v0.2 fixes one strict J-AR13 semantic publication envelope, exact
version-1 bodies for G-01 through G-14, a finite twenty-entry J-AR02
module-product discriminator registry, and the bounded source-domain
approved-decision return. It defines semantic contracts rather than HTTP,
broker, database-row, or public API schemas.

The registry gives every in-scope product one owner, validator, persistence
mode, baseline eligibility treatment, and command-output treatment. G-04 and
G-05 reuse Artifact F bodies exactly; G-13 remains non-authoring referenced
state; G-14 remains a subject-free pre-construction rejection; readiness remains
purpose-specific; and operational approval remains outside Artifact G.

The C-001 proof uses all required G-01 through G-12 bodies and G-14. The CT-1
proof uses the ratified Hermes G-03 producer before Argus testing and the Aegis
G-08 producer after verification while preserving bind-before-derive reversal
ordering and excluding G-10 through G-12. The artifact introduces no generic
workflow, message broker, physical persistence design, or new Artifact F field,
object, or event.

The next design artifact must define deterministic clock, identity-allocation,
and sequence-allocation ports. Database selection remains deferred.

## ADR-020: Ratify Artifact K v0.2

Accepted.

Artifact K v0.2 fixes one database-independent persistence boundary with six
closed modes: command unit of work, runtime-baseline admission, pre-scope
reporting import, referenced-journal admission, query session, and rebuild
session. Authoritative records, immutable events, coordination records,
contract publications, and rebuildable projections retain distinct typed
facets. No repository or store may commit independently of its enclosing unit
of work.

Command deduplication and effect idempotency remain separate mechanisms. Exact
state tokens and availability rules govern planning and commit, and successful
command closure may reference only outputs staged and committed by that command.
For authoritative-token conflicts, the adapter reports an exact conflict
snapshot, the target command owner constructs the J-AR14 rejection, and the
adapter validates and atomically commits the rejection-only result. The adapter
does not author semantic rejections.

The three administrative write modes have explicit typed interfaces, distinct
conflict and receipt outcomes, and cannot emit J-AR14 command rejections. The
core conformance suite K-T01 through K-T42 applies to every adapter; durable
adapters additionally prove K-D01 through K-D06 across a real process restart.
The CT-1 mapping exercises the ordinary persistence boundary row by row,
including the required bind-before-derive reversal ordering.

The module-product discriminator registry is fixed as an interface only.
Artifact L must populate its finite entries and define the minimum internal
runtime-message bodies for G-01 through G-14 and the approved-decision return.
Rebuilds use isolated generations and atomic promotion; verified proof content
remains distinct from declared-format-only evidence hashes.

Ratification does not select a database, define a physical schema, introduce a
public API, or require distributed transactions. Those choices remain deferred
until the remaining Milestone 2 Phase 0 contracts are ratified.

## ADR-019: Ratify Artifact J v0.2

Accepted.

Artifact J v0.2 defines seventeen immutable authoritative-record families and
thirteen rebuildable projections for all twenty-six Artifact I execution steps.
It separates one proposal's immutable treatment version from its event-derived
lifecycle state, using the construction command result for `DRAFT` and the last
accepted accounting-event identity for later exact-state tokens. Artifact F
payloads remain exact derived views and its closed external boundary is
unchanged.

Candidate receipts and durable G publications retain or resolve exact canonical
bytes, their contract and canonicalization versions, and matching hashes so
restart does not depend on external redelivery. Initial accounting-period state
uses the immutable base-record identity and canonical hash for optimistic
concurrency; later lifecycle writes use the last accepted event identity.

The predecessor reporting version enters through one typed, bounded pre-scope
admission operation after the exact affected-period hard close. Before admission
it remains sealed external input and is invisible to application, planner,
query, projection, trace, and contract-read paths. Admission atomically commits
the reporting core, import attestation, verified proof content, and imported
G-06 publication. It emits no accounting event, consumes no ordinary
publication effect key, and cannot become a general import framework.

Every accepted multi-record write validates explicit cross-record bindings
before commit and again during rebuild. Command results, effect claims, G-14
dispositions, import attestations, and contract publications are authoritative
coordination records rather than disposable projections. The approved-decision
return binds exact source-domain approval and candidate versions without
inventing another Artifact G contract.

Ratification fixes semantic persistence ownership, rebuild sources, concurrency
tokens, availability, and atomic binding requirements. It does not select a
database, define physical tables, introduce a public API, expand Artifact F, or
ratify repository interfaces. Those interfaces must be defined next through a
database-independent persistence-port and transactional unit-of-work contract.

## ADR-018: Ratify Artifact I v0.2

Accepted.

Artifact I v0.2 fixes one finite in-process application boundary for the
parameterised C-001 runtime slice. Its eleven rulings, twenty-three commands,
twenty queries, twenty-six ordered execution steps, and twenty-two acceptance
criteria are contiguous, uniquely defined, and internally cross-referenced.
Every catalogued command is exercised by the canonical sequence.

The twenty-six steps reuse exactly three command types: candidate assessment,
proposal submission, and reporting-readiness assessment. This reuse reflects
their parameterised semantics and does not create hidden command variants.
Each command still has one authoritative target owner and one local atomic
transaction.

Only an admitted `accounting.recognition.due` business event may enter Atlas's
posting-rule evaluator. Correction construction remains a separate typed path.
Pythia owns its recommendation but cannot approve it; the affected source
business domain independently approves operational action and may author a new
candidate that returns through ordinary Hermes admission.

CT-1 reuses the same application boundary. Its reversal constructor must bind
the exact G-13 projection source hash to the declared reversal input hash before
deriving or comparing equal-and-opposite lines.

Ratification does not select a database or persistence representation. Proposal
treatment identity versus lifecycle state and predecessor reporting-version
bootstrap provenance remain explicit blockers for the authoritative-record and
projection artifact. No physical persistence schema may be ratified before both
are resolved.

## ADR-014: Ratify Artifact F v0.2

Accepted.

Artifact F v0.2 satisfies the closed-serializer criterion for C-001 and CT-1. The authored object boundary remains nine accounting objects and ten accounting-event types across seventeen canonical event instances. J-010 is available only through a non-authored proof projection, and statement-body arithmetic remains a runtime-resolved assurance test.

The remaining retry and executable projection-binding checks are implementation backlog items and do not block design ratification.

## ADR-028: Mirror and Authenticate the Browser Parquet Extension

Accepted.

The public React product must not depend on a runtime download from DuckDB's
extension service. The build preparation step mirrors the exact signed Parquet
extension declared by the browser runtime manifest and verifies its byte length
and SHA-256 digest before use. The browser repeats that verification, points
DuckDB at the local extension repository, loads Parquet explicitly, and then
disables known-extension auto-install and community extension loading.

DuckDB-Wasm, the extension executable, and governed Parquet inputs therefore
remain separate authenticated authorities. The mirrored executable is a
generated, ignored build input; its version, platform, source URL, size, and
digest remain tracked in source and the published runtime manifest. A missing or
mismatched extension is a visible runtime failure rather than permission to
fall back to an external download.
