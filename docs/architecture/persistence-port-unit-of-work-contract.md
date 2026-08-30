# Artifact K - Persistence Port and Transactional Unit-of-Work Contract

Status: Design v0.2.2 - ratified 2026-08-05

## 0. Purpose and Boundary

Artifact K defines the database-independent persistence boundary required to
implement the authoritative records and rebuildable projections ratified in
Artifact J.

It specifies:

- the one local transactional boundary used by an application command;
- the typed persistence facets exposed inside that boundary;
- exact read, stage, validation, commit, rollback, and retry semantics;
- optimistic-concurrency and independent effect-idempotency treatment;
- the distinction between persisted domain rejection and invariant failure;
- the bounded runtime-baseline, predecessor-import, and referenced-journal
  admission transactions;
- projection deletion and deterministic rebuild access; and
- the conformance obligations every in-memory or persistent adapter must pass.

Artifact K does not define:

- physical tables, columns, indexes, or migrations;
- a database engine or object-relational mapper;
- public HTTP, GraphQL, or user-interface APIs;
- asynchronous messaging, distributed transactions, or background workers;
- the minimum internal bodies of G-01 through G-14;
- the finite Artifact L J-AR02 discriminator entries and their body fields;
- a generic repository for arbitrary untyped module data;
- clock or identity-allocation algorithms;
- production evidence storage; or
- new commands, events, accounting objects, modules, or business processes.

The interfaces below are semantic contracts. Pseudocode names do not select a
programming language or package layout.

## 1. Binding Sources

Artifact K is subordinate to:

- the five invariants and architecture rules in `AGENTS.md`;
- Artifact C - Accounting Object Model;
- Artifact E v0.2.1 - Accounting State Machines and Command/Event Matrix;
- Artifact F v0.2.1 - Minimum Payload Contracts;
- Artifact G v0.2 - Module Ownership and Contract Map;
- Artifact H v0.3.1 - Executable Validation Harness Specification;
- Artifact I v0.2.2 - Runtime Application Boundary;
- Artifact J v0.2 - Authoritative Records and Rebuildable Projections;
- canonical transactions C-001 and CT-1;
- ADR-003 through ADR-019; and
- the approved Milestone 2 Persistent Runtime Vertical Slice roadmap.

Artifact J remains authoritative for record ownership, immutability, rebuild
sources, state tokens, availability, and cross-record bindings. Artifact K
defines how a storage adapter must preserve those semantics without turning the
record vocabulary into a physical schema prematurely.

## 2. Rulings

### K-R01 - One persistence boundary serves the platform

Milestone 2 has one in-process `PersistenceBoundary`. All module-owned records,
Atlas accounting records, shared coordination records, durable G publications,
and rebuildable projections commit through it.

Typed repository facets preserve semantic ownership. They do not imply separate
databases, separate transactions, or permission for one module to write another
module's records.

### K-R02 - One application command owns one local unit of work

An Artifact I application-command attempt opens at most one
`CommandUnitOfWork`. All authoritative appends, effect claims, contract
publications, command closure, dispositions, and projection updates for that
attempt either commit together or do not commit.

No repository facet can commit independently. Nested units of work and a second
commit phase are prohibited.

### K-R03 - Record families are closed and bodies enter through typed contracts

The unit of work exposes typed facets for the seventeen Artifact J record
families and thirteen projections. Those family, owner, and mode boundaries are
closed by Artifact K. A facet accepts only a body validated against its declared
contract discriminator and version.

Artifact K defines the `ModuleProductDiscriminatorRegistry` contract used for
J-AR02 but does not populate Artifact L's minimum runtime-message bodies. An
unregistered discriminator or validator version is rejected structurally; it
cannot fall through to a generic body.

A generic `put(kind, json)` operation that can bypass owner, contract,
canonicalization, state-token, or binding validation is outside the contract.
An adapter may use generic physical machinery internally, but that machinery is
not available to application services.

### K-R04 - Authoritative writes are append-only

The only authoritative write operation is semantic append under a permanent
identity and canonical semantic hash. Repeating the same identity and semantic
bytes is either a recognised retry where a ruling permits one or an existing
record read. Reusing the identity with different semantic bytes is an identity
conflict.

An existing same-content record cannot be claimed as a new output by a different
command unless a ratified idempotency rule explicitly allows that relationship.
Command closure must preserve the record's original creation basis.

No port exposes update or delete for J-AR01 through J-AR17.

### K-R05 - Reads occur against one stable transaction view

All reads used to plan and commit one command observe one stable local
transaction view. An adapter may implement this with locking, snapshots, or
optimistic validation, but commit must detect any authoritative state-token
change that invalidates the plan.

Cross-module controlled use always loads exact published versions. It never
resolves an implicit latest value.

### K-R06 - Semantic time and availability are explicit

Every unit of work carries one injected `semantic_as_of_time`. Where semantic
availability applies, normal application and query reads enforce
`available_from <= semantic_as_of_time`. Records without a distinct semantic
availability field become visible only after commit. No path can observe,
infer, count, trace, or project an unavailable or uncommitted record.

Wall-clock time read inside an adapter cannot silently replace the supplied
semantic time. Maintenance verification may inspect sealed or future-available
records only through its separate privileged mode and may not expose them as
application results.

### K-R07 - Planning remains pure and storage-independent

Application services load immutable inputs through the unit of work and call the
single pure planner implementation:

```text
plan(command, immutable_state) -> TransitionPlan | Rejection
```

The callable mode is:

```text
RebuildSession
  context() -> RebuildContext
  begin_generation() -> ProjectionGenerationRef
  rebuild(ProjectionGenerationRef) -> RebuiltProjectionSet
  validate(RebuiltProjectionSet) -> ValidatedProjectionGeneration
      | RebuildFailure
  promote(ValidatedProjectionGeneration) -> ProjectionPromotionReceipt
  abort(ProjectionGenerationRef) -> None
```

The generation and promotion receipts are rebuild diagnostics, not authoritative
records.

The planner cannot append, publish, claim an effect, update a projection, read a
database, allocate storage identities, or commit. The persistence adapter cannot
reimplement domain transition guards.

### K-R08 - A transition plan is not permission to commit

A successful plan is translated into a typed staged write set. Before commit,
the unit of work validates:

- ownership and closed record type;
- immutable identity and canonical hash;
- expected state tokens;
- semantic availability;
- command identity and input digest;
- effect-key uniqueness where applicable;
- every applicable Artifact J section 8.1 cross-record binding;
- command-result closure over all staged authoritative outputs; and
- projection source tokens.

Failure of any check prevents the accepted write set from committing.

### K-R09 - Commit is atomic at the semantic boundary

One successful commit makes all staged authoritative records, coordination
records, contract publications, effect claims, and projection replacements
visible together.

No observer can see an accounting event without its command result, a posted
journal without its effect claim, a G publication without its owner outcome, or
a projection checkpoint beyond its authoritative cause.

### K-R10 - Command deduplication precedes domain execution

The unit of work first resolves `command_owner + command_id`.

- If no result exists, execution may continue.
- If a result exists and the supplied input digest matches, the original result
  is returned without invoking the planner or staging writes.
- If a result exists and the input digest differs, the attempt is rejected as a
  command-identity conflict without changing the original result.

This guarantee survives adapter replacement and process restart.

Final commit arbitration resolves the command key again. If a concurrent
attempt has committed the same input digest, the unit returns that prior result
and discards its staged set. If the digest differs, the original result remains
authoritative and no staged record commits.

Final commit arbitration resolves the command key again. If a concurrent
attempt has committed the same input digest, the unit returns that prior result
and discards its staged set. If the digest differs, the original result remains
authoritative and no staged record commits.

### K-R11 - Effect idempotency is independent of command identity

Posting and reporting publication claim their declared effect key separately
from command deduplication.

A different command ID cannot repeat a consumed financial or publication
effect. The losing command records the required rejection result without
appending the effect, accounting event, journal, reporting version, or G
publication.

### K-R12 - Optimistic concurrency uses only Artifact J state tokens

A state-changing command stages every expected token it planned against.
During final commit arbitration, the adapter compares each token with
authoritative state:

- construction command-result identity for eventless proposal `DRAFT`;
- last accepted accounting-event identity for event-backed lifecycles;
- base-record identity plus canonical hash for eventless period state; and
- exact immutable product-version reference for module products.

Projection timestamps, adapter row versions, and implicit latest values are not
semantic concurrency tokens.

### K-R13 - Expected rejection commits only rejection records

A first domain rejection, stale-state result, consumed-effect result, or declared
pre-construction rejection commits the rejection-only write set required by its
ratified command contract.

That set contains the immutable J-AR14 command result and, where required, the
J-AR16 disposition, its evidence declaration, and G-14 J-AR13 publication. It
contains no target accounting object, accounting event, financial effect, or
successful domain publication.

For an accepted plan that loses a state-token or effect-key race, the adapter
returns an immutable `ExactConflictSnapshot` while the same local transaction
remains active. A pure coordination function owned by the target command owner
constructs J-AR14 from the command context, exact conflict, and versioned
rejection policy. The adapter validates and commits that rejection-only set; it
never authors the semantic command result.

For an accepted plan that can lose a state-token or effect-key race, the unit of
work also stages and validates a restricted conflict-rejection fallback. Final
commit arbitration selects the accepted set or that rejection-only set; it can
never combine them.

### K-R14 - Invariant failure is not converted into a business rejection

An ownership violation, malformed canonical body, impossible cross-record
binding, adapter corruption, or unrecognised record type is a persistence
invariant failure. The unit of work rolls back and reports an infrastructure or
integrity error. It must not create a plausible-looking domain rejection that
hides a programming or storage defect.

### K-R15 - Projections are transactionally aligned but disposable

Application commits stage projection replacements and checkpoints with their
authoritative causes, as required by Artifact I. A projection write cannot
commit ahead of or without its cause.

Projection loss after commit does not invalidate authoritative state. A
maintenance rebuild can delete and regenerate J-P01 through J-P12 from the
ratified sources. J-P13 observations remain outside the semantic transaction.

### K-R16 - Boundary observation happens after authoritative commit

The application may emit J-P13/H6 observations only after a successful commit
receipt or after retrieving an existing command result. Observation failure
cannot roll back, fabricate, or alter the authoritative outcome.

An observation sink is not a persistence repository and cannot be queried as a
source of domain truth.

### K-R17 - Pre-scope import has its own closed transaction type

The predecessor reporting-version admission uses
`PreScopeReportingImportUnitOfWork`, implemented by the same
`PersistenceBoundary` and local transaction capability as ordinary commands.

It accepts only the typed predecessor candidate ratified in Artifact J. It can
atomically append J-AR10, J-AR11, J-AR12, and imported G-06 J-AR13. It cannot
append a business event, accounting event, J-AR14 command result, J-AR15 effect
claim, or ordinary reporting publication.

### K-R18 - Runtime baseline admission is manifest-bound

Authoritative preconditions that no Artifact I command creates enter through
`RuntimeBaselineAdmissionUnitOfWork`. It accepts one exact versioned baseline
manifest and only the declared J-AR02 source/governed input versions, J-AR04
configuration versions, J-AR07 period base facts, and J-AR12 content or evidence
treatments referenced by that manifest.

Baseline J-AR02 is limited to registry descriptors populated by the later
minimum runtime-body artifact with `baseline_eligible = true` and
`command_output_eligible = false`. This contract shape prevents the baseline
mode from admitting a product that I-S01 through I-S26 creates as an
application-command outcome without requiring Artifact K to define its body.
Baseline J-AR12 excludes predecessor reporting proof content and any content
reserved for another bounded admission mode. The predecessor candidate, proof,
and provenance remain sealed external input until the post-I-S06 import seam.

It cannot admit a candidate receipt, business event, proposal, accounting event,
journal, manifest adjustment, reporting version, G publication, command result,
effect claim, disposition, or referenced prior journal. It is runtime
initialization, not a generic data-import framework.

### K-R19 - Referenced prior-journal admission is separately bounded

CT-1's non-authored prior journal enters through
`ReferencedJournalAdmissionUnitOfWork`, implemented by the same
`PersistenceBoundary`.

It accepts only the typed referenced prior-journal source required by the
ratified reversal family. It can atomically append J-AR17, its G-13 J-AR13
publication, and J-P09/J-P11/J-P12 projections. It cannot append J-AR08,
claim Atlas authored the source journal, emit an accounting event, or become a
generic legacy-data import facility.

J-AR17 is the immutable Atlas read-boundary custody/admission outcome for this
handoff. The G-13 J-AR13 publication binds that exact J-AR17 identity and source
hash as its publication basis rather than inventing a J-AR14 command result.

### K-R20 - Commit acknowledgement may be retried safely

If the caller cannot distinguish a pre-commit failure from a lost post-commit
acknowledgement, it retries the same command owner, command ID, and input digest.
The adapter resolves the immutable J-AR14 result before execution.

The caller must not manufacture a new command ID merely because acknowledgement
was lost. Import acknowledgement uses the same principle through J-AR11 import
identity and semantic content. Runtime-baseline acknowledgement resolves the
exact manifest and all bound records; referenced-journal acknowledgement resolves
the exact J-AR17 source identity/hash and G-13 publication.

### K-R21 - Rebuild uses a separate non-command mode

`RebuildSession` can enumerate and verify authoritative records, delete
projections, and regenerate J-P01 through J-P12 at an explicit semantic time.
It cannot append domain records, emit accounting events, claim effects, publish
G contracts, or create command results.

Historical corruption causes rebuild failure. Rebuild never repairs, fills, or
rewrites authoritative records.

### K-R22 - Adapter capability is selected after port conformance

The first in-memory adapter and any later persistent adapter implement the same
semantic contract and run the same core adapter conformance suite. An adapter
claiming durable persistence must additionally pass the durable restart and
crash-recovery extension. Database-specific features may enforce the contract
more strongly, but may not weaken or reinterpret it.

Artifact K does not select a database, distributed isolation level, ORM,
repository library, or serialization format for physical storage.

## 3. Shared Semantic Types

These are minimum semantic inputs to the port. They are not public payloads or
physical row definitions.

### 3.1 Command context

```text
CommandContext
  command_owner
  command_id
  command_type
  input_contract_version
  input_canonicalization_version
  input_digest
  actor_ref
  authority_refs
  semantic_as_of_time
  correlation_id
```

`input_digest` covers the complete canonical command input under the declared
contract and canonicalization versions, including exact upstream references,
expected state tokens, governed configuration references, and evidence
references. The same command identity cannot be reused for a different version
or digest.

### 3.2 Authoritative reference

```text
AuthoritativeRef
  record_family        # one of J-AR01 through J-AR17
  record_identity
  semantic_hash
```

Where a contract requires byte reproduction, the referenced record also retains
its canonicalization and contract versions plus canonical bytes or an immutable
resolving content reference.

### 3.3 State expectation

```text
StateExpectation
  subject_type
  subject_ref
  expected_state_token
```

The token uses only the forms ratified by Artifact J. The persistence adapter may
also use private storage concurrency mechanisms, but those do not replace or
appear as the semantic token.

### 3.4 Staged write set

```text
StagedWriteSet
  authoritative_appends[]
  effect_claims[]
  contract_publications[]
  projection_replacements[]
  expected_state_tokens[]
  command_result
  conflict_rejection_plan?      # permitted stale/effect fallback
  conflict_rejection_fallback?  # restricted J-AR14-led set
```

The set is immutable once submitted for pre-commit validation. A rejection-only
set has the restricted shape defined in K-R13.

```text
ExactConflictSnapshot
  conflict_class                # STALE_STATE or EFFECT_CONSUMED
  subject_or_effect_key
  expected_authoritative_ref
  observed_authoritative_ref
  observed_semantic_hash
```

The adapter constructs only this factual snapshot. It cannot choose the
rejection reason, invoke domain logic, author J-AR14, or add a G-14 disposition.
The application-owned pure function is:

```text
construct_conflict_rejection(
  CommandContext,
  ExactConflictSnapshot,
  rejection_policy_ref
) -> StagedRejectionSet
```

It is a coordination constructor, not an Artifact E transition guard. Its
output remains subject to owner, closure, canonicalization, and binding
validation before commit.

### 3.5 Commit receipt

```text
CommitReceipt
  transaction_ref
  outcome                    # ACCEPTED, REJECTED, BLOCKED, or PRIOR_RESULT
  command_result_ref
  command_result_hash
  committed_authoritative_refs[]
  committed_publication_refs[]
  claimed_effect_refs[]
  resulting_state_tokens[]
```

The receipt summarizes committed state. It is not a second authoritative record
and can always be reconstructed from J-AR14 and its bound outputs. Adapter-local
transaction IDs may appear in diagnostics but are excluded from this semantic
receipt and every authoritative or compatibility digest.

## 4. Persistence Boundary Modes

The root port exposes exactly six semantic modes.

| Mode | Purpose | May append authoritative records? | May replace projections? |
|---|---|---:|---:|
| `CommandUnitOfWork` | Execute one Artifact I command attempt. | Yes, through typed facets and command closure. | Yes. |
| `RuntimeBaselineAdmissionUnitOfWork` | Admit exact pre-existing runtime inputs under one versioned manifest. | Only declared J-AR02/J-AR04/J-AR07/J-AR12. | Permitted J-P04/J-P05/J-P10/J-P11 only. |
| `PreScopeReportingImportUnitOfWork` | Admit the one typed predecessor bundle. | Only J-AR10/J-AR11/J-AR12/imported J-AR13. | J-P08/J-P09/J-P11 only. |
| `ReferencedJournalAdmissionUnitOfWork` | Admit one non-authored prior-journal source for the ratified reversal family. | Only J-AR17 and its G-13 J-AR13. | J-P09/J-P11/J-P12 only. |
| `QuerySession` | Exact-version and labelled-current read access. | No. | No. |
| `RebuildSession` | Verify authoritative state and rebuild projections. | No. | Delete/recreate J-P01 through J-P12. |

The root semantic shape is:

```text
PersistenceBoundary
  begin_command(CommandContext) -> CommandUnitOfWork
  begin_runtime_baseline_admission(BaselineContext)
      -> RuntimeBaselineAdmissionUnitOfWork
  begin_pre_scope_reporting_import(ImportContext)
      -> PreScopeReportingImportUnitOfWork
  begin_referenced_journal_admission(ReferencedJournalContext)
      -> ReferencedJournalAdmissionUnitOfWork
  open_query(QueryContext) -> QuerySession
  open_rebuild(RebuildContext) -> RebuildSession
```

An implementation may require disposal or rollback mechanics. Leaving a unit of
work without commit must release its resources and expose none of its staged
writes.

`BoundaryObservationSink` is a separate optional non-authoritative port used for
J-P13/H6 observations after commit. It is not a seventh persistence mode, does not
participate in the local transaction, and cannot be used by a command or query
as authoritative input.

## 5. Typed Persistence Facets

The following facets are available only inside the modes that require them.
They are semantic groupings, not table or package prescriptions.

| Facet | Artifact J families | Minimum operations |
|---|---|---|
| Candidate custody | J-AR01 | Get exact receipt; resolve candidate bytes; stage immutable receipt. |
| Module product | J-AR02 | Get exact owned version; stage only `ValidatedModuleProduct`; enumerate declared upstream refs. |
| Business event | J-AR03 | Get exact admitted event; stage one admitted event derived from accepted candidate content. |
| Configuration | J-AR04 | Get exact governed version; no implicit latest for controlled execution. |
| Accounting lifecycle | J-AR05, J-AR06, J-AR07 | Get treatment/base facts/events; rebuild exact state at token; stage treatment or event. |
| Journal and restatement values | J-AR08, J-AR09 | Get immutable journal/lines or manifest; stage only with creating accounting transition. |
| Reporting history | J-AR10, J-AR11 | Get exact version/import; stage successor publication or bounded predecessor import. |
| Content and evidence | J-AR12 | Resolve verified bytes; get declared-only reference; stage only the treatment permitted by verification status. |
| Contract publication | J-AR13 | Get exact publication; list by pinned product and contract; stage publisher-owned handoff. |
| Command coordination | J-AR14, J-AR16 | Resolve command result; stage closure or permitted G-14 rejection package. |
| Effect registry | J-AR15 | Resolve effect key; stage one posting or publication claim. |
| Referenced state | J-AR17 | Get exact non-authored source; stage only through `ReferencedJournalAdmissionUnitOfWork`. |
| Projection | J-P01 through J-P13 | Get exact/current view; stage replace/checkpoint; delete/rebuild only in rebuild mode; append observation outside authoritative commit. |

### 5.1 Owner enforcement

Each staged body identifies its semantic owner. The facet checks that the active
command owner is permitted to author it under Artifact G and Artifact I.

Shared-substrate writes that support another owner's command are allowed only
where Artifact I explicitly defines that atomic write set, such as candidate
custody in I-S01. Infrastructure custody does not change semantic ownership.

### 5.2 Exact-read result

Every exact authoritative read returns:

```text
ExactRecord
  authoritative_ref
  owner
  canonical_body_or_content_ref
  canonicalization_version
  contract_or_body_discriminator
  upstream_refs[]
  evidence_refs[]
  available_from
```

Fields that do not apply to a record family remain absent, not silently
defaulted. Artifact K does not define each internal body; the later runtime
message artifact must do so without weakening this envelope.

### 5.3 Module-product discriminator registry

Artifact K fixes the registry interface, not Artifact L's body fields:

```text
ModuleProductDiscriminatorRegistry
  resolve(
    product_discriminator,
    contract_version
  ) -> ModuleProductContractDescriptor | UnsupportedDiscriminator

ModuleProductContractDescriptor
  product_discriminator
  contract_version
  semantic_owner
  permitted_persistence_modes[]
  baseline_eligible
  command_output_eligible
  validator_ref
  supported_canonicalization_versions[]

validate_module_product(
  descriptor,
  canonical_body,
  canonicalization_version
) -> ValidatedModuleProduct | BodyContractFailure
```

`ValidatedModuleProduct` retains the descriptor identity/version, canonical
bytes and hash, owner, exact version identity, upstream refs, evidence refs, and
creation basis. The J-AR02 facet accepts only this capability; application code
cannot construct one by assertion or submit raw JSON directly.

Artifact L must populate a finite registry for the C-001 and CT-1 runtime
messages. Adding a registry entry is a contract change, not adapter
configuration. K-T closure claims apply to the seventeen record families and to
the exact registry entries present in the tested contract version; they do not
pretend Artifact K already defines Artifact L's body fields.

## 6. Command Unit-of-Work Protocol

### 6.1 Ordered execution

Every ordinary command attempt follows this order:

1. open one unit of work with immutable `CommandContext`;
2. resolve prior J-AR14 by command owner and command ID;
3. return the prior result on matching input digest, or reject identity conflict;
4. load exact authoritative inputs and state tokens at `semantic_as_of_time`;
5. call the pure planner or typed non-lifecycle domain operation;
6. translate the result into either an accepted or rejection-only staged set;
7. validate ownership, identities, hashes, availability, tokens, effects,
   cross-record bindings, and command closure;
8. for an accepted plan, arbitrate command identity, state tokens, and effect
   keys against the final authoritative view;
9. commit the accepted plan, return a concurrent prior result, or return an
   `ExactConflictSnapshot` while retaining the same local transaction;
10. on conflict, let the target command owner construct, stage, and validate the
    required rejection-only set, then commit it; and
11. after commit, emit boundary observations from the receipt and actual reads.

No stage may be reordered so that domain planning occurs before duplicate
resolution, an effect is claimed before all bindings are prepared, or an
observation becomes proof of commit.

### 6.2 Unit-of-work semantic interface

```text
CommandUnitOfWork
  context() -> CommandContext
  prior_result() -> None | ExactCommandResult
  records() -> TypedReadFacets
  stage_accepted(StagedWriteSet) -> None
  stage_rejection(StagedRejectionSet) -> None
  validate() -> ValidatedAcceptedPlan | ValidatedRejectionPlan
      | PersistenceFailure
  arbitrate(ValidatedAcceptedPlan) -> AcceptedCommitPlan
      | ExactConflictSnapshot | ExactCommandResult
      | CommandIdentityConflict
  replace_with_conflict_rejection(
      ExactConflictSnapshot,
      StagedRejectionSet
  ) -> None
  commit(AcceptedCommitPlan | ValidatedRejectionPlan) -> CommitReceipt
  rollback() -> None
```

`stage_accepted` and `stage_rejection` are mutually exclusive at initial staging.
`replace_with_conflict_rejection` is the only permitted replacement: it discards
the accepted set after exact arbitration and binds the replacement to that
snapshot. The unit then validates the rejection set before commit. `commit`
accepts only a plan produced by the same open unit of work. A plan or conflict
snapshot cannot be serialized, moved to another unit, or modified after
validation.

### 6.3 Typed non-lifecycle operations

Commands such as reconciliation, test execution, readiness assessment, planning
snapshot creation, and decision production may not use Artifact E lifecycle
planners. They still produce typed immutable owner outputs, exact publications,
and J-AR14 closure through the same unit-of-work protocol.

This avoids inventing one generic workflow state machine while preserving the
same transaction, deduplication, availability, and binding guarantees.

## 7. Read and Query Contract

### 7.1 Exact authoritative reads

Command planning and cross-module consumption use exact identities and, where
stateful, exact state tokens. If the exact record is absent, unavailable, owned
by a different type, or has a different semantic hash, the read fails rather
than falling back to a current projection.

### 7.2 Labelled current reads

A query may request a labelled current projection for local operational use.
The result must include its authoritative source tokens and semantic
`as_of_time`. It cannot be passed to a controlled cross-module command unless
that command converts it to and validates exact pinned references.

### 7.3 Projection-assisted command loads

An adapter may use a projection to accelerate a command load only when:

- the projection declares every authoritative source token it includes;
- the requested exact token is present and matches;
- semantic availability is evaluated independently; and
- the returned immutable state is byte-equivalent to rebuilding from the named
  authoritative sources.

Otherwise the adapter must rebuild or reject. Projection freshness alone is not
authority.

### 7.4 Raw maintenance reads

Only `RebuildSession` and the bounded import verifier may inspect records without
normal application availability filtering. Their outputs are maintenance proof,
not G products or command inputs, until normal availability rules are met.

## 8. Staging and Pre-Commit Validation

### 8.1 Append validation

Every staged authoritative record proves:

- the record family is closed and known;
- the permanent identity is complete;
- the owner is permitted;
- canonical semantic bytes reproduce the declared hash;
- required contract and canonicalization versions are present;
- referenced authoritative inputs resolve exactly;
- content verification status matches actual byte availability; and
- its identity is absent or is a permitted same-content retry.

The semantic hash of a declaration-only J-AR12 record proves the declaration's
own bytes. It does not upgrade the referenced absent evidence body to
content-byte verified. The verified-versus-declared distinction from ADR-016
travels unchanged through staging, commit, query, digest, and rebuild.

### 8.2 Cross-record validation

The adapter must implement every applicable binding in Artifact J section 8.1
as a pre-commit invariant over the complete staged set plus its exact reads.

This includes candidate admission, business-event publication, proposal
lifecycle, journal posting, restatement manifest, reporting publication,
pre-scope predecessor, general G publication, command closure, and approved
decision return.

The adapter may not split these checks among repositories in a way that permits
one repository to commit before another check finishes.

### 8.3 Command closure

The staged J-AR14 result enumerates every authoritative output identity and hash,
every G publication, every claimed effect, and every resulting state token for
that command. The unit of work rejects:

- an output in the staged set missing from command closure;
- a closure output reference missing from the staged set;
- an output attributed to another command;
- a successful closure containing a failed effect claim; or
- a rejection closure containing a successful domain effect.

When arbitration returns an `ExactConflictSnapshot`, the target command owner's
pure coordination constructor must use the same command identity and input
digest. The adapter then validates the constructed J-AR14 body, exact conflict
reference, and final rejection closure before commit. The adapter does not
materialize or own that result. Accepted and rejection closures must be
disjoint.

Where an accepted plan includes a conflict-rejection fallback, the adapter
validates that fallback independently and proves it shares the same command
identity and input digest. Accepted and fallback closures must be disjoint.

Projection replacements and boundary observations are not authoritative outputs
inside J-AR14.

Pre-existing authoritative records may appear only as exact command inputs.
They can never satisfy an output-closure reference. A legitimate command retry
returns the prior J-AR14 before staging and therefore needs no output carve-out.

### 8.4 Projection validation

Each staged projection replacement identifies its projection family, semantic
key, source authoritative references, exactness token, and semantic
`as_of_time`. Its bytes must reproduce from the authoritative records visible in
the same commit plan.

A checkpoint cannot advance beyond an authoritative event or output committed
in that transaction.

## 9. Commit, Concurrency, and Isolation

### 9.1 Required local transaction capability

An adapter is conformant only if it can atomically enforce:

- immutable identity uniqueness;
- command identity and input-digest consistency;
- expected state-token comparison;
- effect-key uniqueness;
- cross-record binding validation;
- authoritative append;
- command closure; and
- projection replacement/checkpoint alignment.

The contract requires serializable semantic outcomes for conflicting commands.
It does not require a specific database isolation-level label; the adapter must
prove the observable result through conformance tests.

At final arbitration the adapter returns an accepted plan, concurrent prior
result, command-identity conflict, or exact stale/effect snapshot. The accepted
plan commits atomically. A conflict snapshot keeps the same local transaction
active while the target owner constructs and stages the rejection-only result;
that result is validated and committed atomically. A physical uniqueness error
may not escape after a partial accepted write or prevent the required rejection
result from being recorded.

The validated commit plan contains both the accepted write set and its permitted
conflict fallback. At the final token/effect check, the adapter atomically
commits exactly one. A physical uniqueness error may not escape after a partial
accepted write or prevent the required rejection result from being recorded.

### 9.2 Concurrency outcomes

For two attempts planned from the same state token:

- at most one accepted state-changing write set commits;
- the other observes an exact stale token and commits the immutable rejection
  result required by its Artifact I command contract;
- no partial records or projections from the losing accepted plan remain; and
- retrying either command returns its original persisted outcome.

### 9.3 Rollback

Rollback removes all staged but uncommitted writes and releases adapter
resources. It does not delete or alter records that predated the unit of work.
Calling rollback after an unsuccessful validation is safe and idempotent.

### 9.4 No external side effects inside commit

The unit of work may claim only persisted in-platform effects. It cannot send
email, invoke an external API, publish to a broker, write an external file, or
perform any other effect that the local transaction cannot roll back.

Milestone 2 does not need an outbox because it has no such runtime side effect.

## 10. Duplicate, Effect, and Failure Semantics

### 10.1 Command-attempt outcome classes

| Result class | Persists J-AR14? | Persists target domain records? | Meaning |
|---|---:|---:|---|
| `ACCEPTED` | Yes | Yes | Complete validated write set committed. |
| `REJECTED` | Yes | No | Expected domain, authority, stale-token, or effect conflict. |
| `BLOCKED` | Yes | No successful controlled-use output | Required governed input or readiness is absent or unusable. |
| `PRIOR_RESULT` | Reuses existing | No new writes | Same command identity and input digest retried. |
| `COMMAND_IDENTITY_CONFLICT` | Original remains | No | Occupied command identity supplied with a different input contract version, canonicalization version, or digest. |
| `INVARIANT_FAILURE` | No fabricated result | No | Programming, binding, canonicalization, or corruption defect. |
| `ADAPTER_FAILURE` | No claim unless later resolved by retry | No guaranteed new state | Storage unavailable or acknowledgement uncertain. |

`COMMAND_IDENTITY_CONFLICT` never creates another J-AR14 because the command key
is already occupied. A mismatched retry never overwrites or supplements the
original result.

An immutable output identity collision during a new command is not this outcome.
Unless an explicit ratified idempotency rule applies, it is an
`INVARIANT_FAILURE`: the accepted set rolls back and no plausible domain
rejection is fabricated.

### 10.2 Administrative-mode outcomes

Administrative modes never create J-AR14. Their outcomes are mode-specific:

| Mode | Identical retry | Conflicting semantic input | Successful receipt basis |
|---|---|---|---|
| Runtime baseline | Return `BaselineAdmissionReceipt`. | `BaselineAdmissionConflict`; write nothing. | Exact J-AR04 manifest plus all bound admitted records. |
| Pre-scope reporting import | Return `ExactImportReceipt`. | `PreScopeImportConflict`; write nothing. | J-AR11 plus bound J-AR10/J-AR12/imported J-AR13. |
| Referenced prior journal | Return `ReferencedJournalAdmissionReceipt`. | `ReferencedJournalAdmissionConflict`; write nothing. | J-AR17 plus bound G-13 J-AR13. |

A conflict response identifies the occupied semantic identity and the supplied
versus existing hashes/versions without exposing unavailable content. It is a
deterministic response, not an authoritative record or command result.
Malformed bodies, impossible bindings, or historical corruption remain
`INVARIANT_FAILURE`; adapter unavailability remains `ADAPTER_FAILURE`.

### 10.3 Lost acknowledgement

After an adapter failure with uncertain outcome, the only safe resolution is:

1. reopen with the same command owner, ID, and input digest;
2. resolve J-AR14;
3. return it if present; otherwise retry normal execution; and
4. allow J-AR15 to prevent a repeated effect under a different command attempt.

### 10.4 Rejection atomicity

The first expected rejection commits its result and applicable G-14 package in
one local transaction. A retry returns that package without duplicating a
disposition, evidence declaration, or G publication.

## 11. Runtime Baseline Admission Contract

### 11.1 Baseline context

```text
BaselineContext
  baseline_manifest_ref
  baseline_manifest_contract_version
  baseline_manifest_canonicalization_version
  baseline_manifest_hash
  semantic_as_of_time
  admitting_actor_ref
```

```text
ReferencedJournalAdmissionBundle
  canonical_source_body
  provenance_body
  g13_publication_body
  projection_replacements[]
```

```text
BaselineAdmissionBundle
  baseline_manifest_body
  declared_records[]
  projection_replacements[]
```

The baseline manifest is itself an exact J-AR04 governed configuration version.
It enumerates every other admitted record identity, family, owner, semantic
hash, contract/canonicalization treatment, availability, upstream relationship,
and evidence treatment. Its own identity and hash are supplied by the context,
avoiding a self-hash cycle. No record can enter by directory scanning, fixture
loading, or adapter-specific seed logic.

The callable mode is:

```text
RuntimeBaselineAdmissionUnitOfWork
  context() -> BaselineContext
  prior_receipt() -> None | BaselineAdmissionReceipt
  stage_bundle(BaselineAdmissionBundle) -> None
  validate() -> ValidatedBaselineAdmission | BaselineAdmissionConflict
      | PersistenceFailure
  commit(ValidatedBaselineAdmission) -> BaselineAdmissionReceipt
  rollback() -> None
```

`BaselineAdmissionReceipt` resolves the exact manifest identity/hash, all bound
record refs/hashes, permitted projection tokens, and admitted semantic time. It
is reconstructible from the manifest and bound records and is not J-AR14.

### 11.2 Ordered baseline protocol

1. resolve the baseline-manifest identity and hash;
2. return the prior admission outcome when the complete manifest and every
   admitted record are already present byte-identically;
3. reject reuse of the manifest or any declared record identity with different
   semantic content;
4. validate that every record belongs to J-AR02, J-AR04, J-AR07, or J-AR12 and
   has the owner permitted by Artifacts G, I, and J;
5. resolve every J-AR02 discriminator/version through the registry and require
   `baseline_eligible = true` and `command_output_eligible = false`;
6. reject J-AR12 content reserved for the predecessor or referenced-journal
   admission modes;
7. validate all canonical bytes, hashes, exact upstream refs, and evidence
   verification statuses;
8. validate period-base identities, declared initial states, and base hashes;
9. prepare only the permitted J-P04/J-P05/J-P10/J-P11 projections; and
10. commit the manifest, admitted records, and projections atomically.

### 13.3 Structural prohibition

The mode exposes no append method for J-AR01, J-AR03, J-AR05/J-AR06,
J-AR08 through J-AR11, or J-AR13 through J-AR17.
It cannot generate an Artifact I command result, publish a G contract, claim an
effect, or execute a planner.

Canonical fixtures may supply acceptance-test inputs to this port, but they may
not bypass it or become hidden adapter seed state required by normal runtime
startup.

## 12. Pre-Scope Reporting Import Contract

### 12.1 Import context

```text
ImportContext
  import_id
  imported_reporting_version_ref
  sealed_candidate_contract_version
  sealed_candidate_canonicalization_version
  sealed_candidate_hash
  semantic_as_of_time
  importer_ref
```

```text
PreScopeReportingImportBundle
  sealed_candidate_body
  prerequisite_period_ref
  prerequisite_close_event_ref
  prerequisite_close_view_hash
  reporting_core_body
  reporting_content_body
  import_attestation_body
  imported_g06_publication_body
  projection_replacements[]
```

The import unit can inspect the exact sealed candidate, prerequisite period base
facts, hard-close event and view hash, verified reporting content, and original
publication provenance.

The callable mode is:

```text
PreScopeReportingImportUnitOfWork
  context() -> ImportContext
  prior_receipt() -> None | ExactImportReceipt
  stage_bundle(PreScopeReportingImportBundle) -> None
  validate() -> ValidatedPreScopeImport | PreScopeImportConflict
      | PersistenceFailure
  commit(ValidatedPreScopeImport) -> ExactImportReceipt
  rollback() -> None
```

`ExactImportReceipt` is the exact J-AR11 attestation plus its bound J-AR10,
J-AR12, imported J-AR13, and permitted projection refs. It is not J-AR14.

### 12.2 Ordered import protocol

1. resolve J-AR11 by `import_id`;
2. return the prior receipt if all semantic content matches;
3. reject reuse of the identity, reporting-version ref, or content hash with
   conflicting semantic content;
4. resolve the exact prerequisite `HARD_CLOSED` state;
5. validate original publication, import, and availability ordering;
6. validate committed reporting bytes and content hash;
7. prepare J-AR10, J-AR11, J-AR12, imported G-06 J-AR13, and only the permitted
   J-P08/J-P09/J-P11 projection updates;
8. validate Artifact J's pre-scope predecessor binding; and
9. commit the complete import set atomically.

### 11.3 Structural prohibition

The import mode exposes no candidate, business-event, accounting-event,
command-result, effect-claim, ordinary-publication, or arbitrary module-product
append method. This makes its bounded scope structural rather than procedural.

## 13. Referenced Prior-Journal Admission Contract

### 13.1 Admission context

```text
ReferencedJournalContext
  source_journal_ref
  source_canonicalization_version
  source_hash
  source_contract_version
  semantic_as_of_time
  admitting_actor_ref
```

The source body includes the exact immutable journal header and ordered lines,
source identity, provenance, canonicalization treatment, and availability needed
to reproduce G-13 without acquiring Artifact F authorship.

The callable mode is:

```text
ReferencedJournalAdmissionUnitOfWork
  context() -> ReferencedJournalContext
  prior_receipt() -> None | ReferencedJournalAdmissionReceipt
  stage_bundle(ReferencedJournalAdmissionBundle) -> None
  validate() -> ValidatedReferencedJournalAdmission
      | ReferencedJournalAdmissionConflict | PersistenceFailure
  commit(ValidatedReferencedJournalAdmission)
      -> ReferencedJournalAdmissionReceipt
  rollback() -> None
```

`ReferencedJournalAdmissionReceipt` resolves exact J-AR17 and G-13 J-AR13
identities/hashes plus permitted projection tokens. It is reconstructible from
those records and is not J-AR14.

### 13.2 Ordered admission protocol

1. resolve existing J-AR17 state by source identity and source hash;
2. return the prior source/publication references when all semantic content
   matches;
3. reject source-ref reuse with a different source hash, body,
   provenance, contract version, or availability;
4. validate canonical source bytes and hash before constructing G-13;
5. prepare J-AR17, its exact G-13 J-AR13 publication, and only
   J-P09/J-P11/J-P12 projection updates;
6. prove the G-13 payload and publication basis bind the same J-AR17 source
   identity and hash; and
7. commit the complete set atomically.

This admission happens before the CT-1 reversal constructor consumes G-13. It
does not count as a CT-1 accounting event or application command.

### 12.3 Structural prohibition

The mode exposes no J-AR08 append and cannot translate, normalize, or re-author
the source as an Atlas journal. It cannot admit a business event, module product,
reporting version, arbitrary legacy record, or another referenced-state family.

## 14. Projection Deletion and Rebuild Contract

### 14.1 Rebuild input

A rebuild session receives:

```text
RebuildContext
  semantic_as_of_time
  requested_projection_families
  verification_mode
```

It enumerates the authoritative digest set, validates immutable hashes and all
Artifact J section 8.1 bindings, then rebuilds in Artifact J section 11 order.

### 14.2 Rebuild rules

- projection deletion never deletes J-AR records;
- exact lifecycle folds use causal order and declared state tokens;
- availability is evaluated at the injected semantic time;
- missing authoritative bytes, references, or bindings fail the rebuild;
- current projections are labelled with their source tokens;
- J-P13 is excluded from the semantic projection digest; and
- rebuilding emits no business event, accounting event, contract publication,
  effect claim, or command result.

Rebuild output remains isolated under its generation ref until the complete
requested set validates. Promotion replaces the prior complete generation
atomically. A query sees the prior complete generation, the newly promoted
generation, or an explicit projection-unavailable result that may be rebuilt
from authoritative state; it never observes a partial generation. Failure
discards the candidate generation and leaves the prior promoted set unchanged.

### 14.3 Digest parity

Every adapter must support the Artifact J digest comparisons:

```text
clean-start authoritative = restart authoritative
clean-start projection    = restart projection
clean-start projection    = rebuilt projection
canonical compatibility  = ratified Artifact F fixtures
```

Every adapter proves deterministic delete-and-rebuild parity through the core
suite. An adapter claiming durable persistence additionally proves parity across
an actual process restart through the durable extension in section 16.7.

## 15. Application-Step Coverage

The port contract supports every Artifact I step through ordinary modes; no
scenario step receives a private commit path.

| Steps | Unit-of-work use |
|---|---|
| Runtime baseline before I-S01 | The manifest-bound admission mode atomically admits exact governed configuration, period base facts, and declared source/evidence inputs without a domain event or G publication. |
| I-S01 | Candidate, module-product, command, and G-publication facets commit receipt, G-02, and result together. |
| I-S02 | Candidate bytes and exact G-02 are read; admitted event, G-01, and result commit together. |
| I-S03/I-S13 | Configuration and exact inputs are read; proposal treatment and result commit without an accounting event. |
| I-S04/I-S05/I-S14/I-S15 | Exact proposal token is checked; lifecycle event, G-04/G-05, result, and projections commit together. |
| I-S06 | Period base token is checked; hard-close event, G-04/G-05, result, and period projections commit together. |
| Post-I-S06 import seam | The bounded import mode atomically admits predecessor v1 and imported G-06 after the exact hard close. |
| I-S07/I-S08 | Exact upstream publications are read; Hermes or Argus versions, G publication, and result commit together. |
| I-S09/I-S10/I-S11 | Exact upstream products are read; Aegis versions, G publication, and result commit together. |
| I-S12 accepted | Exact directive and Atlas tokens are checked; case event, G-04/G-05, result, and projections commit together. |
| I-S12 rejected | Rejection result, G-14 disposition/evidence, and G-14 publication commit without an accounting object or event. |
| I-S16 | Proposal token and effect key are checked; posting event, journal/lines, effect claim, G-04/G-05, result, and projections commit together. |
| I-S17/I-S18/I-S19 | Exact case token is checked; case event, owned manifest where applicable, publications, result, and projections commit together. |
| I-S20 | Case token, predecessor, manifest, and publication key are checked; event, v2, claim, G-04/G-05/G-06, result, and projections commit together. |
| I-S21/I-S22 | Exact verification/readiness inputs are read; owner version, G publication, and result commit together. |
| I-S23/I-S24 | Exact governed inputs are read; Pythia version, G publication, and result commit together. |
| I-S25 | Exact G-12 is read; source-domain approval/rejection and candidate versions plus result commit together. |
| I-S26 | Exact approved candidate bytes are read; receipt, unsupported G-02, and result commit without G-01. |

### 15.1 CT-1 transaction proof

Before CT-1 commands begin, the referenced-journal admission mode atomically
admits J-AR17 and its G-13 publication. Every later row uses the ordinary
`CommandUnitOfWork`; none receives a scenario-private repository or commit path.

| CT-1 operation | Exact reads and arbitration | Authoritative commit |
|---|---|---|
| Referenced prior-journal admission | Canonical J-010 source body, provenance, contract/canonicalization versions, source hash, and semantic availability. | J-AR17, exact G-13 J-AR13, and J-P09/J-P11/J-P12 only; no J-AR08, J-AR14, accounting event, or effect. |
| `ReconcileCashApplicationIdentity` | Exact receipt/application parties, canonical party mapping, source refs, and reconciliation configuration. | Hermes J-AR02 reconciliation, G-03 J-AR13, J-AR14 result, and permitted projections. |
| `RunCashApplicationIdentityTest` | Exact Hermes G-03/L-MP05 reconciliation, G-13 J-010 projection, and test/configuration versions. | Argus J-AR02 test run and exception, G-07 J-AR13, J-AR14 result, and permitted projections. |
| I-C09 `ReviewAssuranceException` | Exact G-07 exception and evidence refs. | Aegis J-AR02 review, finding, and issue versions; G-08 J-AR13; J-AR14; permitted projections. |
| I-C11 `IssueRemediationDirective` | Exact issue version, policy, authority, and evidence. | Aegis J-AR02 directive and issue-treatment version; G-09 J-AR13; J-AR14; permitted projections. |
| `ApplyOpenPeriodCorrectionDirective` | Exact G-09 authority, open target-period token, and referenced J-010 identity. | J-AR14 accepted authority-validation result only; no accounting object, event, or G publication. |
| `ConstructReversalProposal` | First bind G-13 `source_hash` to the declared reversal input hash; only after equality is established may the pure `ConstructCorrectionProposal` planner derive and compare equal-and-opposite lines. | Atlas J-AR05 reversal treatment and J-AR14; J-P02 `DRAFT`; no accounting event and no posting-rule evaluation. |
| I-C04 `SubmitJournalProposal` for reversal | Exact reversal treatment and construction-result token. | `proposal.submitted`, G-04/G-05 J-AR13 publications, J-AR14, and proposal projections. |
| I-C14 `ApproveJournalProposal` for reversal | Exact submitted token, authority, evidence, and segregation-of-duties policy. | `proposal.approved`, G-04/G-05, J-AR14, and proposal projections. |
| I-C15 `PostJournalProposal` for reversal | Exact approved token, open-period token, J-010 binding, and reversal effect key. | `journal.posted`, J-011 header/lines as J-AR08, reversal J-AR15 claim, G-04/G-05, J-AR14, and projections. |
| `ConstructReplacementProposal` | Exact G-09 directive, J-010 identity, corrected customer identity, open period, mappings, and input hashes; use typed correction construction only. | Atlas J-AR05 replacement treatment and J-AR14; J-P02 `DRAFT`; no accounting event and no posting-rule evaluation. |
| I-C04 `SubmitJournalProposal` for replacement | Exact replacement treatment and construction-result token. | `proposal.submitted`, G-04/G-05, J-AR14, and proposal projections. |
| I-C14 `ApproveJournalProposal` for replacement | Exact submitted token, authority, evidence, and segregation-of-duties policy. | `proposal.approved`, G-04/G-05, J-AR14, and proposal projections. |
| I-C15 `PostJournalProposal` for replacement | Exact approved token, open-period token, correction basis, and a distinct replacement effect key. | `journal.posted`, J-012 header/lines as J-AR08, replacement J-AR15 claim, G-04/G-05, J-AR14, and projections. |
| `VerifyCashApplicationCorrection` | Exact J-010/J-011/J-012, both proposal histories, six accounting events, directive, effects, and evidence. | Argus J-AR02 verification, G-07 J-AR13, J-AR14, and permitted projections. |
| `UpdateCashApplicationIssue` | Exact prior Aegis issue version and exact Argus G-07 verification. | Successor Aegis J-AR02 issue version, G-08 `ISSUE_UPDATED` J-AR13, J-AR14 result, and permitted projections. |
| `UpdateCashApplicationIssue` | Exact prior Aegis issue version and exact Argus G-07 verification. | Successor Aegis J-AR02 issue version, G-08 `ISSUE_UPDATED` J-AR13, J-AR14 result, and permitted projections. |

The accounting-event sequence remains exactly:

```text
reversal:    proposal.submitted -> proposal.approved -> journal.posted
replacement: proposal.submitted -> proposal.approved -> journal.posted
```

J-010 remains non-authored, G-03 precedes the Argus identity test, J-011 and
J-012 use separate effect keys, the open period remains open, and the final
G-08 update remains Aegis-owned. CT-1 creates no restatement case, manifest,
reporting version, G-10/G-11/G-12 product, or approved-decision return.

## 16. Adapter Conformance Catalog

The K-T core tests run unchanged against the in-memory adapter and every later
persistent adapter. K-D tests are an additional capability suite for an adapter
claiming durable persistence; they do not alter the core semantics.

### 16.1 Boundary and contract tests

| ID | Required proof |
|---|---|
| K-T01 | No application-facing generic untyped append or independent repository commit exists. |
| K-T02 | Each K-defined J-AR family boundary accepts only its declared owner and typed body; once Artifact L populates the registry, J-AR02 accepts only a `ValidatedModuleProduct` from that registered descriptor/version. |
| K-T03 | Same immutable identity and bytes are stable; different bytes take the exact command, administrative-conflict, or invariant path defined for that mode. |
| K-T04 | Canonical bytes reproduce every staged semantic hash. |
| K-T05 | Normal reads cannot observe a record before `available_from`. |
| K-T06 | Declaration-only evidence remains declared after commit and rebuild; only committed matching bytes can report content verification. |
| K-T07 | Unknown J-AR02 discriminators, unregistered versions, raw bodies, and validator-version mismatches are rejected before staging. |
| K-T08 | Each administrative mode exposes its exact context, bundle, prior-receipt, validate, commit, conflict, and rollback types; no bundle enters through an implicit adapter channel. |

### 16.2 Transaction, concurrency, and observation tests

| ID | Required proof |
|---|---|
| K-T09 | Injected failure at every pre-commit stage leaves all authoritative and projection digests unchanged. |
| K-T10 | A projection failure inside command commit rolls back the authoritative writes. |
| K-T11 | Two commands using one current token produce at most one accepted state change. |
| K-T12 | The losing stale command preserves domain state; the target owner constructs and commits exactly the required rejection-only outcome from the adapter's exact conflict snapshot. |
| K-T13 | No read can observe a partial multi-record command or administrative write set. |
| K-T14 | Concurrent delivery of one command identity and digest commits once; the loser returns the committed prior result without committed planner effects. |
| K-T15 | Observation-sink failure after accepted, rejected, blocked, or prior-result resolution leaves authoritative and projection digests unchanged. |

### 16.3 Retry and effect tests

| ID | Required proof |
|---|---|
| K-T16 | Same command identity, versions, and digest returns the original result without planner execution. |
| K-T17 | Same command identity with different contract version, canonicalization version, or digest cannot change or supplement the original result. |
| K-T18 | A new command identity cannot repeat a consumed posting effect and commits only its required rejection outcome. |
| K-T19 | A new command identity cannot repeat a consumed publication effect and commits only its required rejection outcome. |
| K-T20 | Lost acknowledgement resolves through same-command retry without duplicate writes. |
| K-T21 | Command deduplication binds input contract version, canonicalization version, and digest; changing any one conflicts. |

### 16.4 Binding and rejection tests

| ID | Required proof |
|---|---|
| K-T22 | Each Artifact J section 8.1 binding fails the complete accepted write set when independently broken. |
| K-T23 | J-AR14 closure exactly enumerates outputs staged and committed by that command; pre-existing records can appear only as inputs. |
| K-T24 | Pre-construction rejection commits J-AR14/J-AR16/G-14 once and no Artifact F subject. |
| K-T25 | Invariant failure rolls back and is not relabelled as a domain or administrative conflict. |
| K-T26 | Rejection retry returns the original result and disposition without duplication. |
| K-T27 | The adapter returns only exact stale/effect facts; the target command owner constructs J-AR14 and the adapter validates it before commit. |

### 16.5 Admission, import, and rebuild tests

| ID | Required proof |
|---|---|
| K-T28 | Predecessor import is impossible before the exact hard-close event and view hash exist. |
| K-T29 | Import commits J-AR10/J-AR11/J-AR12/imported J-AR13 atomically and no prohibited family. |
| K-T30 | Identical import retry returns `ExactImportReceipt`; changed content or provenance returns `PreScopeImportConflict` without writes. |
| K-T31 | Referenced-journal admission commits only J-AR17, its G-13 J-AR13, and permitted projections; retry and conflict use their exact mode-specific outcomes. |
| K-T32 | Runtime baseline admission commits only manifest-declared J-AR02/J-AR04/J-AR07/J-AR12 records and permitted projections; every J-AR02 descriptor is baseline-eligible and not command-output-eligible. |
| K-T33 | Identical baseline retry returns `BaselineAdmissionReceipt`; changed manifest or record content returns `BaselineAdmissionConflict` without partial admission. |
| K-T34 | Clean runtime initialization uses the baseline port and contains no adapter-private authoritative seed state. |
| K-T35 | Deleting J-P01 through J-P12 changes no authoritative digest. |
| K-T36 | Rebuild reproduces the same projection digest at the same semantic time. |
| K-T37 | Rebuild failure on a missing body or broken binding performs no authoritative repair. |
| K-T38 | A partial or failed rebuild generation is never query-visible and leaves the prior promoted generation unchanged. |

### 16.6 Canonical scenario tests

| ID | Required proof |
|---|---|
| K-T39 | All twenty-six C-001 application steps and the bounded import seam use only the declared modes and facets. |
| K-T40 | Every row of the CT-1 transaction proof uses the declared interfaces, publishes Hermes G-03 before Argus testing, preserves J-010 non-authorship, binds G-13 before reversal derivation, and publishes Aegis G-08 after verification. |
| K-T41 | Canonical C-001 and CT-1 retain Artifact F bytes and terminal semantic digests. |
| K-T42 | Non-canonical identities and dates execute without literal-identity branches. |

### 16.7 Durable-adapter extension

These tests apply only when an adapter claims survival across process restart.
They run in addition to, not instead of, K-T01 through K-T37.

| ID | Required proof |
|---|---|
| K-D01 | After an actual process restart, same-command retry returns the original J-AR14 result without planner execution or new writes. |
| K-D02 | Posting and publication effect claims survive restart and reject a second command attempting the same effect. |
| K-D03 | Baseline, predecessor-import, and referenced-journal admission receipts survive restart and preserve their distinct retry/conflict outcomes. |
| K-D04 | Authoritative, projection, and canonical-compatibility digests match before restart, after reload, and after projection rebuild at the same semantic time. |
| K-D05 | A process stop after durable commit but before acknowledgement resolves through the original command or admission identity without duplicate state. |
| K-D06 | Semantic availability and exact-version query results remain unchanged across restart. |

## 17. Acceptance Criteria

Artifact K may be ratified only when all of the following hold.

- K-A01: one shared in-process persistence boundary serves every in-scope
  module without changing Artifact G ownership;
- K-A02: one application-command attempt opens at most one local command unit of
  work and no repository commits independently;
- K-A03: all seventeen J-AR families and thirteen J-P projections map to a typed
  facet and permitted mode; Artifact K fixes the mandatory J-AR02 registry
  interface but makes no claim that its subtype population is complete before
  Artifact L is ratified;
- K-A04: no application-facing untyped generic append or raw J-AR02 body can
  bypass semantic validation;
- K-A05: authoritative records are append-only and expose no update or delete;
- K-A06: one command reads against a stable transaction view and validates every
  expected Artifact J state token before commit;
- K-A07: semantic availability uses the injected as-of time on application,
  planner, query, projection, and trace paths;
- K-A08: the pure planner remains the only Artifact E guard implementation and
  has no persistence dependency;
- K-A09: a transition plan cannot commit until ownership, hashes, availability,
  concurrency, effects, bindings, and command closure all pass;
- K-A10: authoritative outputs, coordination records, G publications, effect
  claims, and projection replacements commit atomically;
- K-A11: command deduplication resolves before planner or domain execution;
- K-A12: same-command retry returns the immutable prior result without another
  event, record, effect, publication, disposition, or projection change;
- K-A13: mismatched command retry cannot overwrite or supplement the original
  command result;
- K-A14: posting and publication effect keys remain independently unique across
  different command identities;
- K-A15: two conflicting commands planned from one token produce at most one
  accepted state transition;
- K-A16: an expected stale, blocked, or domain rejection commits only its
  declared rejection records, and a first in-scope rejection records the result
  required by its command contract;
- K-A17: a binding, ownership, canonicalization, or corruption failure rolls
  back and is never disguised as a business rejection;
- K-A18: command acknowledgement ambiguity resolves by retrying the same command
  identity and digest;
- K-A19: boundary observations occur after commit and remain removable without
  changing domain truth; observation-sink failure cannot alter any semantic
  digest;
- K-A20: projections are aligned transactionally with their causes but can be
  deleted and rebuilt from authoritative records through isolated generations
  and atomic promotion without partial query visibility;
- K-A21: rebuild cannot append, publish, claim effects, or repair authoritative
  history;
- K-A22: pre-scope import uses one closed typed unit of work inside the same
  persistence boundary;
- K-A23: pre-scope import can commit only J-AR10/J-AR11/J-AR12/imported J-AR13
  and its permitted projections;
- K-A24: import availability and exact prerequisite hard-close state are
  validated before commit;
- K-A25: all Artifact J section 8.1 bindings are enforced before commit and
  again during rebuild;
- K-A26: every I-S01 through I-S26 write set is expressible without a
  scenario-private repository or commit path;
- K-A27: CT-1 uses the same ports, publishes Hermes G-03 before Argus testing,
  preserves J-010 non-authorship, binds G-13 before reversal derivation, and
  publishes Aegis G-08 after verification; every operation in section 15.1 maps
  exact reads, authoritative writes, effects, publications, results, and
  projections;
- K-A28: one core adapter conformance suite applies unchanged to every adapter,
  while an adapter claiming durability must also pass the explicit K-D restart
  and crash-recovery extension;
- K-A29: the contract does not select a database, ORM, physical schema,
  isolation-level label, package layout, or serialization library;
- K-A30: no public API, distributed transaction, message broker, outbox,
  background worker, or external side effect enters the unit of work;
- K-A31: canonical C-001 and CT-1 compatibility remains an adapter conformance
  obligation; and
- K-A32: the next runtime-message artifact can define exact G bodies without
  reopening persistence atomicity, ownership, retry, rebuild, or the
  discriminator-registry interface; and
- K-A33: CT-1 referenced prior state enters only through the bounded
  referenced-journal admission mode, remains non-authored, and publishes G-13
  atomically with J-AR17; and
- K-A34: final commit arbitration handles concurrent same-command delivery,
  stale state, and consumed effects without partial accepted writes or missing
  required rejection outcomes, while the adapter never authors J-AR14;
- K-A35: every authoritative precondition not created by an Artifact I command
  enters through one exact versioned runtime-baseline manifest; and
- K-A36: runtime baseline admission is closed to J-AR02/J-AR04/J-AR07/J-AR12,
  admits J-AR02 only through baseline-eligible/non-command-output registry
  descriptors, cannot publish or execute domain behaviour, cannot pre-admit
  predecessor proof content, and cannot be bypassed by adapter-private seed
  state; and
- K-A37: command retry identity binds input contract version, canonicalization
  version, and digest so historical retry remains unambiguous after restart; and
- K-A38: persistence never upgrades a declaration-only evidence hash to
  content-byte verification, including during digest calculation or rebuild;
- K-A39: baseline, predecessor-import, and referenced-journal modes each expose
  explicit context, bundle, prior-receipt, validate, commit, conflict, and
  rollback types without creating J-AR14;
- K-A40: command commit receipts exclude adapter-local transaction identity and
  remain reconstructible from J-AR14 plus its bound outputs; and
- K-A41: command closure contains only outputs staged and committed by that
  command, while every pre-existing authoritative reference is classified as an
  input.

## 18. Decisions Resolved and Still Open

### 18.1 Resolved by Artifact K

- one shared persistence boundary with typed owner facets;
- one command-scoped unit of work and no repository-local commit;
- stable read, staged write, validation, and atomic commit ordering;
- exact command deduplication before execution;
- independent posting and publication effect idempotency;
- Artifact J state tokens as the only semantic optimistic-concurrency tokens;
- adapter-owned conflict facts followed by target-owner rejection construction;
- command rejection, administrative conflict, and invariant-failure outcomes
  remain distinct;
- command output closure cannot be satisfied by pre-existing records;
- post-commit observational tracing;
- a separate closed predecessor-import transaction type;
- a manifest-bound runtime-baseline admission transaction type;
- a separate closed non-authored prior-journal admission transaction type;
- a fixed J-AR02 discriminator-registry interface whose finite runtime entries
  are populated by Artifact L;
- isolated projection generations and atomic rebuild promotion; and
- one reusable core conformance suite plus an explicit durable-adapter extension.

### 18.2 Still open for later Milestone 2 artifacts

1. exact minimum internal bodies for G-01 through G-14 and source-domain
   approved-decision return;
2. concrete clock, identity, and sequence-allocation ports;
3. physical database engine, schema, indexes, and transaction implementation;
4. migration compatibility and persisted contract-version policy;
5. exact module-product version bodies and finite Artifact L registry entries
   outside Artifact F;
6. evidence-byte storage beyond the bounded reporting proof;
7. exact projection checkpoint representation and operational rebuild tooling;
8. Milestone 2 assertion-report schema; and
9. runtime package layout and reversible library choices.

## 19. Recommended Next Artifact

Following Artifact K's ratification, the next artifact must define the minimum
internal runtime-message bodies for G-01 through G-14 and the approved-decision
return.

That artifact must remain closed to the C-001 and CT-1 proof need. Each message
must identify:

- authoritative publisher and permitted consumers;
- contract and canonicalization version;
- exact product identity and state token where applicable;
- canonical bytes or immutable content reference and matching hash;
- upstream publication and evidence references;
- purpose, period, scope, and readiness where required;
- semantic availability; and
- the publishing command or bounded import basis.

It must also populate the finite J-AR02
`ModuleProductDiscriminatorRegistry` entries required by those messages,
including semantic owner, permitted persistence modes, baseline and
command-output eligibility, validator identity, and supported canonicalization
versions.

It must not define a generic workflow envelope, speculative module events, a
public API schema, or a message broker.
