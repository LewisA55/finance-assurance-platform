# Artifact M - Deterministic Time, Identity, and Sequence Authority Ports

Status: Design v0.2.1 - ratified 2026-08-05

## 0. Purpose and Closure Rule

Artifact M defines the minimum authority ports that let Milestone 2 construct
parameterised runtime records without reading an implicit wall clock, inventing
semantic identities inside a persistence adapter, or allocating versions by
mutable process-local counters.

It closes three questions left open by Artifacts I through L:

- where command and administrative-operation time values come from;
- how permanent semantic identities are supplied or deterministically granted;
  and
- how initial and successor version numbers and ordered child positions are
  derived without weakening optimistic concurrency.

The hard constraint is:

> Authority grants provide deterministic candidate values. They do not create
> domain truth, reserve a lifecycle transition, or grant permission to commit.

Artifact M is closed when:

- every authority request is bound to one exact operation key, authority seed
  digest, and governed authority-profile basis;
- identical requests reproduce identical grants across retry and restart;
- business-effective and source-recorded times remain supplied facts rather
  than clock outputs;
- the pure planner receives the deterministic time grant as immutable command
  input and never calls an authority port;
- identity and sequence grants are resolved once from the planner's typed output
  shape, then a non-branching materializer applies them without re-running domain
  logic;
- the persistence adapter validates granted values but never allocates semantic
  identities, times, or versions;
- C-001 and CT-1 reproduce their canonical identifiers and event timestamps
  through an injected canonical authority profile without branching on their
  literal values; and
- non-canonical instances run through the same contracts with different valid
  authority profiles and operation keys.

This artifact does not select a clock library, UUID algorithm, database
sequence, ORM, physical schema, distributed lock, public API, event broker, or
runtime package layout.

## 1. Binding Sources

Artifact M is subordinate to:

- the five invariants and architecture rules in `AGENTS.md`;
- Artifact C - Accounting Object Model;
- Artifact E v0.2.1 - Accounting State Machines and Command/Event Matrix;
- Artifact F v0.2.1 - Minimum Payload Contracts;
- Artifact G v0.2 - Module Ownership and Contract Map;
- Artifact H v0.3.1 - Executable Validation Harness Specification;
- Artifact I v0.2.2 - Runtime Application Boundary;
- Artifact J v0.2 - Authoritative Records and Rebuildable Projections;
- Artifact K v0.2.2 - Persistence Port and Transactional Unit-of-Work Contract;
- Artifact L v0.2.1 - Internal Runtime Message Contracts and Module-Product
  Registry;
- canonical transactions C-001 and CT-1; and
- ADR-003 through ADR-022.

Artifact F remains authoritative for accounting-event timestamp and identity
fields. Artifact J remains authoritative for permanent identity, version, state
token, and availability semantics. Artifact K remains authoritative for retry,
deduplication, concurrency, and atomic commit.

## 2. Rulings

### M-R01 - Authority is injected and explicit

Every command, administrative admission, query, and rebuild receives its
semantic time explicitly. Every runtime-authored semantic identity or version is
either supplied under its owning input contract or obtained through the ports in
this artifact.

No domain service, planner, repository facet, projection builder, serializer, or
persistence adapter may call an ambient wall clock, random identifier generator,
process-local counter, or database auto-increment for a semantic field.

### M-R02 - Economic and source times are not clock allocations

The following are supplied or resolved business facts and are never replaced by
an authority clock:

- service-period dates and accounting `effective_date`;
- source business-event `occurred_at` and source-system `recorded_at`;
- original publication time carried by a pre-scope import;
- contract, invoice, cash-receipt, and operational-decision effective dates;
- original and revised workforce start dates; and
- any other time whose meaning predates the receiving platform operation.

The receiving command validates and preserves those values byte-for-byte under
their owning contract.

### M-R03 - One operation time grant has three distinct meanings

An ordinary state-changing operation receives:

- `semantic_as_of_time`, which gates the exact records it may read;
- `action_at`, which records when the represented platform or evidenced human
  action occurred; and
- `recorded_at`, which records when the resulting immutable platform record is
  appended.

These values are not interchangeable. Accounting treatment remains controlled
by explicit `effective_date` and `ledger_period_id`, never by any grant value.

### M-R04 - System and declared actions are separate grant variants

`SYSTEM_ACTION` asks the authority profile to issue `action_at`.
`DECLARED_ACTION` carries an exact evidenced action timestamp in the semantic
input and asks the authority only to validate and bind it while issuing
`recorded_at`.

The declared timestamp is part of the authority seed and final command input
digest. A caller cannot change it under the same command or admission identity.

The owning command contract selects the variant; the caller does not. Artifact F
actions with `SYSTEM_POLICY` actor and authorization use `SYSTEM_ACTION`.
Actions with `PERSON` actor and `HUMAN` authorization use `DECLARED_ACTION` and
must bind the human-action evidence. Artifact L human review and source-domain
approval fields follow the same rule.

### M-R05 - Authority time is deterministic per logical operation

The same authority profile, operation key, authority seed digest, and action
variant must reproduce the same grant across redelivery and process restart.

A runtime provider may calculate or durably map the grant. It may not return a
new time merely because execution was retried later.

### M-R06 - Semantic visibility uses the supplied grant

Artifact K's rule remains unchanged:

```text
available_from <= semantic_as_of_time
```

The persistence adapter cannot substitute its transaction start time or database
clock. Newly committed publications normally become available no earlier than
their granted `recorded_at` and any stricter domain prerequisite.

### M-R07 - Authority behaviour is governed configuration

Every ordinary authority request names one exact committed J-AR04 authority
profile. The profile identifies the authority contract version and the
configured time, identity, and sequence providers used by that operation.

For commands, the profile is included in `CommandContext.authority_refs` and
therefore in the canonical command input digest. Reusing a command identity with
a different profile is a command-identity conflict, not a permissible retry.

### M-R08 - One closed operation basis drives all grants

Time, identity, and sequence requests share one `AuthorityOperationBasis`. The
basis binds the exact persistence mode, stable operation key, semantic input
digest, and authority profile. No port accepts an unbound `next()`, `now()`, or
`new_id()` call.

### M-R09 - Semantic identifiers remain opaque

Authority-issued identifiers are non-empty ASCII strings and retain the object
class and uniqueness rules already ratified by Artifacts F and J. Prefixes such
as `AE-`, `J-`, or `CMD-` are fixture readability conventions, not semantic
routing or global numbering policy.

No consumer may determine owner, record family, state, or permission by parsing
an identifier string.

### M-R10 - Command and correlation identity exist before command execution

Every externally initiated or internally coordinated command supplies a stable
`command_id` and `correlation_id` at the Artifact I application boundary. The
explicit application coordinator must construct the complete typed follow-on
command before dispatch; Artifact M does not introduce a command-ID factory or
workflow engine.

The persistence adapter never assigns either identity. Delivery retry always
uses the original command identity.

### M-R11 - Identity allocation is bulk, named, and call-order independent

After the single pure planner or typed non-lifecycle operation returns its typed
outcome, one operation requests a complete set of named identity slots for that
exact output shape, canonicalized by `slot_name`. For an accepted command, the
set also contains the finite conflict-rejection alternative permitted by
Artifact K arbitration. The identity authority returns one immutable grant set
bound to the complete canonical request hash.

Calling for identities one at a time, relying on caller order, or requesting an
undeclared slot is prohibited. Reordering an unchanged slot set has no effect;
adding, removing, or changing a slot changes the request hash and is not the
same grant.

The application cannot precompute domain outputs merely to request grants before
planning. A planned rejection requests only its exact rejection outputs because
it cannot proceed to accepted-plan arbitration. Unused conflict-alternative
grants create no fact. This preserves one planner invocation and one identity
request without requiring a second, outcome-dependent planning pass.

### M-R12 - An identity grant creates no authoritative fact

An unused grant is not a J-AR record, lifecycle transition, reservation,
publication, effect claim, or evidence item. Only a successful Artifact K commit
creates authoritative state.

Implementations may leave unused opaque candidates after rollback. Semantic
identifiers are not required to be gap-free.

### M-R13 - Identity collisions fail closed

If a granted permanent identity already resolves to different semantic content,
the accepted write set fails as an invariant or identity conflict under Artifact
K. The application cannot silently request a replacement identity and retry the
same plan.

Same identity and same canonical semantic content remains governed by the
existing retry or existing-record rules.

### M-R14 - Versions are derived from exact predecessor state

The sequence port supports only:

- initial family version `1`; and
- successor version `predecessor_version + 1` bound to an exact predecessor
  reference and Artifact J state token.

It does not search for a maximum, resolve `latest`, reserve ranges, or permit a
caller-selected skip.

### M-R15 - A sequence grant is not a concurrency token

Two commands planned against the same predecessor may derive the same candidate
successor number. Artifact K's expected state token and final commit arbitration
decide which command, if either, commits.

The losing command cannot retain the candidate number as an alternative branch
or retry against a newly resolved predecessor.

### M-R16 - Ordered child positions derive from frozen business order

Proposal and journal line numbers are the semantic ordered-child sequences in
Artifact M. The sequence request binds the complete ordered line-content hashes
and returns positions `1..n`.

Restatement-manifest order, ordered references, and causal event order retain
their already-ratified explicit ordering rules. They do not receive hidden
counter values.

### M-R17 - Accounting causality is not a numeric sequence

Accounting events remain ordered by exact `correlation_id` and
`causation_event_id`. The sequence authority cannot invent a missing causal
predecessor, reorder events, or turn an ordinal into an Artifact F causation
reference.

### M-R18 - Effect keys are deterministic semantic derivations

Posting and reporting-publication idempotency keys are derived from the exact
effect class and target semantic reference under the existing Artifact F/K
effect-key contract. They are not authority-profile outputs, random identities,
or version counters.

The same financial or publication effect derives the same key even under a
different command identity or authority profile. Artifact K's independent
effect registry remains authoritative for whether the key is already consumed.
The J-AR15 claim's permanent identity is the owning effect contract's canonical
derivation from that exact effect class and key; it is not a separate identity
authority allocation.

### M-R19 - Planner and persistence responsibilities remain unchanged

The application service resolves the operation basis and deterministic time
grant before invoking the pure planner or typed non-lifecycle operation. The
planner returns one typed `TransitionPlan | Rejection`; a typed non-lifecycle
operation returns its equivalent owner result. Neither contains authority-made
identity or sequence facts.

The application resolves the closed identity and sequence plan from that single
typed result, obtains the grants once, and materializes the result without
re-evaluating a guard, posting rule, correction rule, or owner policy. The
planner cannot call an authority port. The adapter validates staged values
against grants and exact state but cannot allocate or reinterpret them.

### M-R20 - Administrative modes use their existing stable keys

Runtime-baseline admission, pre-scope reporting import, and referenced-journal
admission use the manifest, import, and source identities already fixed by
Artifact K as their operation keys. They do not fabricate command identities or
J-AR14 results.

### M-R21 - Semantic and diagnostic generated values remain distinct

Authority-issued values that appear in a ratified object, event, module product,
publication, attestation, or command result are semantic and participate in its
canonical hash.

Adapter transaction times, database row identities, lock versions, local file
paths, projection-generation diagnostics, and post-commit observation timing are
non-semantic and cannot enter those hashes or state tokens.

### M-R22 - Artifact M adds no domain record or event class

Authority requests and grants are typed application values. They do not add
J-AR18, G-15, an eleventh accounting event, a new business-event type, or a
generic workflow object.

### M-R23 - Baseline profile bootstrap is sealed and bounded

Runtime-baseline admission cannot require its authority profile to be committed
before the transaction that admits that same profile. For that mode only, the
baseline manifest carries one sealed authority-profile candidate, exact intended
J-AR04 identity, and canonical hash.

The provider registry may resolve the candidate by that exact identity and hash
for validation. The profile becomes ordinary committed J-AR04 configuration only
if the complete baseline transaction commits. Every other mode requires an
already committed and semantically available profile.

### M-R24 - Authority contracts are strict and canonically hashable

Every request, basis, slot, and grant is a closed version-1 semantic value.
Unknown fields and unsupported discriminators are rejected. Hashes use Artifact
L's `SORTED_KEYS_COMPACT_UTF8_V1` canonicalization and SHA-256 treatment; a
value's own hash field is excluded from the bytes that hash binds.

### M-R25 - Authority failure cannot masquerade as a domain outcome

A malformed pre-context authority request is not an accepted application
command. A determinism or allocation failure after opening a unit of work is an
invariant failure. Neither may fabricate a domain rejection, J-AR14, or G-14.
Expected command rejections and persistence conflicts retain their Artifact I/K
semantics.

### M-R24 - Authority contracts are strict and canonically hashable

Every request, basis, slot, and grant is a closed version-1 semantic value.
Unknown fields and unsupported discriminators are rejected. Hashes use Artifact
L's `SORTED_KEYS_COMPACT_UTF8_V1` canonicalization and SHA-256 treatment; a
value's own hash field is excluded from the bytes that hash binds.

### M-R23 - Baseline profile bootstrap is sealed and bounded

Runtime-baseline admission cannot require its authority profile to be committed
before the transaction that admits that same profile. For that mode only, the
baseline manifest carries one sealed authority-profile candidate, exact intended
J-AR04 identity, and canonical hash.

The provider registry may resolve the candidate by that exact identity and hash
for validation. The profile becomes ordinary committed J-AR04 configuration only
if the complete baseline transaction commits. Every other mode requires an
already committed and semantically available profile.

## 3. Time Provenance Classes

Every in-scope time field belongs to exactly one class.

| Class | Source | Examples | May authority overwrite it? |
|---|---|---|---:|
| Economic date | Business or accounting input | `effective_date`, service dates, reporting period | No |
| Source occurrence | Source-domain canonical input | admitted business-event `occurred_at`, cash receipt time | No |
| Source recording | Source-system canonical input | admitted business-event `recorded_at` | No |
| Action time | `OperationTimeGrant.action_at` or evidenced declared action | accounting-event occurrence, review, approval, publication | Only through the selected grant variant |
| Platform recording | `OperationTimeGrant.recorded_at` | accounting-event append, candidate receipt, publication visibility floor | Yes, by exact grant only |
| Semantic as-of | `OperationTimeGrant.semantic_as_of_time` or query/rebuild grant | availability-gated reads | Yes, by exact grant only |
| Diagnostic time | Adapter or observer | transaction duration, log timestamp | Not semantic |

`created_at` and `updated_at` fields in Artifact L are action-time fields unless
their body explicitly preserves an earlier creation time. An Aegis issue
successor therefore preserves the original `created_at` and receives the new
command's `action_at` as `updated_at`.

## 4. Shared Authority Operation Basis

Every request to a port in sections 5 through 7 contains:

```text
AuthorityOperationBasis
  authority_contract_version       # constant 1
  authority_canonicalization_version # SORTED_KEYS_COMPACT_UTF8_V1
  authority_canonicalization_version # SORTED_KEYS_COMPACT_UTF8_V1
  authority_profile_basis          # COMMITTED_PROFILE or
                                   # SEALED_BASELINE_PROFILE
  operation_mode                   # COMMAND, RUNTIME_BASELINE,
                                   # PRE_SCOPE_IMPORT,
                                   # REFERENCED_JOURNAL_ADMISSION,
                                   # QUERY, or REBUILD
  operation_key
  authority_seed_digest
```

`authority_profile_basis` is exactly one of:

```text
CommittedAuthorityProfileBasis
  basis_type                       # COMMITTED_PROFILE
  authority_profile_ref            # exact J-AR04 AuthoritativeRef

SealedBaselineAuthorityProfileBasis
  basis_type                       # SEALED_BASELINE_PROFILE
  baseline_manifest_ref
  intended_profile_ref             # intended J-AR04 identity
  candidate_profile_hash
```

`SEALED_BASELINE_PROFILE` is permitted only for `RUNTIME_BASELINE`.

The six `operation_mode` values match Artifact K's closed persistence modes.
Artifact M does not create another persistence mode.

### 4.1 Operation-key construction

| Mode | Stable operation key | Authority seed digest basis |
|---|---|---|
| `COMMAND` | `command_owner + command_id` | Exact canonical caller/domain input plus authority-profile basis, excluding all authority grants |
| `RUNTIME_BASELINE` | Baseline manifest reference | Manifest hash plus complete admitted-bundle semantic digest |
| `PRE_SCOPE_IMPORT` | J-AR11 `import_id` | Sealed candidate, prerequisite state, reporting content, provenance, and profile |
| `REFERENCED_JOURNAL_ADMISSION` | Source-journal reference plus source hash | Canonical source, provenance, G-13 body, and profile |
| `QUERY` | Caller request identity plus query type | Exact declared as-of time, query parameters, requested versions, purpose, scope, and profile |
| `REBUILD` | Rebuild request identity | As-of time, requested projection families, verification mode, and profile |

An empty operation key, unsupported mode, unresolved profile basis, or malformed
seed digest is rejected before any grant is issued.

### 4.2 Authority profile

The exact authority-profile candidate contains at least:

```text
AuthorityProfile
  profile_ref
  authority_contract_version       # constant 1
  time_provider_ref
  identity_provider_ref
  sequence_provider_ref
  timestamp_format                  # UTC RFC 3339 with trailing Z
  identity_character_policy         # non-empty ASCII
  supported_identity_classes[]
  supported_sequence_kinds[]
  effective_from
  effective_to
  canonical_content_hash
```

Provider resolution uses the following semantic interface:

```text
AuthorityProviderRegistry
  resolve(authority_profile_basis)
      -> ResolvedAuthorityProviderSet | AuthorityRequestFailure

ResolvedAuthorityProviderSet
  profile_identity
  profile_hash
  authority_contract_version
  time_authority
  identity_authority
  sequence_authority
```

The resolved set is application composition, not a persisted domain record or a
service-locator capability exposed to planners.

The profile is configuration, not an allocation ledger. Changing a provider or
algorithm requires a successor configuration version. Existing command retries
remain bound to the original exact profile.

For ordinary modes, runtime composition selects a provider implementation by the
exact committed profile identity and hash. After the time grant supplies
`semantic_as_of_time`, the unit of work must load that exact J-AR04 record and
validate its hash, availability, and effective range before planning. Provider
selection alone never proves semantic availability.

Failure to resolve the configured provider by exact reference and hash is a
pre-context authority failure. Once the unit of work is open, a matching J-AR04
record that is not yet semantically available follows the target owner's normal
unavailable-input outcome; a record/profile hash mismatch is an invariant
failure.

For `RUNTIME_BASELINE`, the same validation uses the sealed candidate bound by
the manifest. A mismatch between candidate bytes, declared hash, and configured
provider fails the whole admission. This is the only bootstrap exception.

For ordinary modes, runtime composition selects a provider implementation by the
exact committed profile identity and hash. After the time grant supplies
`semantic_as_of_time`, the unit of work must load that exact J-AR04 record and
validate its hash, availability, and effective range before planning. Provider
selection alone never proves semantic availability.

For `RUNTIME_BASELINE`, the same validation uses the sealed candidate bound by
the manifest. A mismatch between candidate bytes, declared hash, and configured
provider fails the whole admission. This is the only bootstrap exception.

Canonical C-001 and CT-1 use an injected fixture profile that reproduces their
ratified values. The fixture mapping is configuration keyed by full operation
basis; application code does not branch on `C-001`, `CT-1`, `P-551`, or any
canonical literal.

### 4.3 Seed digest and command input digest

The authority seed digest exists before any grant. It covers the complete
caller/domain input, declared action time where applicable, exact upstream and
state references already supplied by the request, and authority-profile basis.
It excludes authority-issued time, identities, and sequences.

After the deterministic time grant is issued, the application constructs
Artifact K's command input digest over the seed input plus the complete time
grant. That final digest is used for command deduplication and is stored by
J-AR14. Output identity and sequence grants remain deterministic construction
inputs; they are not caller input and do not create a digest cycle.

Because the time grant is deterministic from the seed, identical logical retry
reconstructs the same Artifact K input digest. A changed seed or profile under
the same command identity produces a different final digest and therefore the
existing command-identity conflict.

### 4.4 Canonical hash boundaries

- `basis_hash` binds the complete `AuthorityOperationBasis`.
- A request hash binds its complete basis and conditional request fields.
- A time or sequence `grant_hash` binds the complete grant except that hash
  field.
- `grant_set_hash` binds the basis hash plus the complete slot-sorted identity
  grants and excludes only `grant_set_hash` itself.
- Caller order is non-semantic for identity slots; ordered member hashes remain
  semantic for proposal and journal lines.
- No adapter or provider diagnostic enters an authority hash.

## 5. Deterministic Time Authority Port

### 5.1 Request and grant

```text
OperationTimeRequest
  basis
  action_time_mode                  # SYSTEM_ACTION or DECLARED_ACTION
  declared_action_at                # required only for DECLARED_ACTION

OperationTimeGrant
  basis_hash
  semantic_as_of_time
  action_at
  recorded_at
  action_time_mode
  grant_hash

SemanticAsOfRequest
  basis                             # QUERY or REBUILD only
  declared_as_of_time

SemanticAsOfGrant
  basis_hash
  semantic_as_of_time               # equals declared_as_of_time
  grant_hash
```

```text
DeterministicTimeAuthority
  grant_operation_time(OperationTimeRequest)
      -> OperationTimeGrant | AuthorityRequestFailure

  grant_as_of_time(SemanticAsOfRequest)
      -> SemanticAsOfGrant | AuthorityRequestFailure
```

`grant_as_of_time` is used by read-only query and rebuild modes. It validates and
binds the exact declared as-of time in the authority seed; it does not invent
as-of, action, or recording time.

### 5.2 Temporal rules

- Every authority-issued timestamp is UTC RFC 3339 with trailing `Z`.
- `action_at <= recorded_at` always holds.
- For `SYSTEM_ACTION`, `semantic_as_of_time <= action_at`.
- For `DECLARED_ACTION`, the declared action must not follow `recorded_at`; its
  relationship to `semantic_as_of_time` is validated against the command's
  business meaning and exact evidence.
- Actor and authorization type must select the required action-time variant;
  supplying the other variant is a contract failure.
- Every exact input used by the operation satisfies
  `available_from <= semantic_as_of_time`.
- A new ordinary G publication uses an `available_from` not earlier than the
  grant's `recorded_at` and any stricter domain bound.
- Pre-scope import retains `original_published_at`; its imported
  `available_from` is not earlier than original publication, hard close,
  import action, or platform recording.
- No grant changes an economic effective date or ledger period.
- Query and rebuild `semantic_as_of_time` equals their declared request value
  byte-for-byte after contract validation.

### 5.3 Field projection

| Runtime field | Authority source |
|---|---|
| Accounting-event `occurred_at` | `action_at` |
| Accounting-event `recorded_at` | `recorded_at` |
| J-AR02 `created_at` for a new product | `action_at` |
| Admission `assessed_at`, reconciliation `performed_at` | `action_at` |
| Test `executed_at`, review `reviewed_at`, directive `requested_at` | `action_at` |
| Readiness `assessed_at`, planning `frozen_at`, governed decision `produced_at` | `action_at` |
| Source-domain approval `decided_at` | evidenced declared `action_at` |
| Issue successor `updated_at` | `action_at`; original `created_at` preserved |
| Reporting-version `published_at` | publication command `action_at` |
| J-AR11 `imported_at` | import `action_at` |
| Candidate receipt time | `recorded_at` |
| Source-domain candidate `occurred_at` / `recorded_at` | approval `action_at` / operation `recorded_at` |
| G-14 `recorded_at` | operation `recorded_at` |
| New J-AR13 `available_from` | at least `recorded_at` |
| Command or administrative semantic reads | `semantic_as_of_time` |

An owning contract may impose a stricter relationship. It cannot silently choose
a different time source.

## 6. Deterministic Identity Authority Port

### 6.1 Identity request

```text
IdentitySlot
  slot_name
  identity_class                   # DOMAIN_FAMILY, AUTHORITATIVE_RECORD,
                                   # CONTRACT_PUBLICATION,
                                   # DOMAIN_CHILD, or DIAGNOSTIC_GENERATION
  record_family                    # J-AR01 through J-AR17 when applicable
  product_discriminator            # Artifact L discriminator when applicable
  parent_ref                       # existing parent, child identity only
  parent_slot_name                 # same-plan parent, child identity only

IdentityPlanRequest
  basis
  slots[]                          # complete set, canonicalized by slot_name

IdentityGrant
  slot_name
  identity_class
  permanent_identity

IdentityGrantSet
  basis_hash
  request_hash
  grants[]
  grant_set_hash
```

```text
DeterministicIdentityAuthority
  grant_identities(IdentityPlanRequest)
      -> IdentityGrantSet | AuthorityRequestFailure
```

### 6.2 Identity classes

| Class | In-scope use |
|---|---|
| `DOMAIN_FAMILY` | Proposal, restatement-case, issue, reporting-version, or module-product family identity |
| `AUTHORITATIVE_RECORD` | Permanent J-AR record identity under its declared record family |
| `CONTRACT_PUBLICATION` | Permanent J-AR13 publication identity |
| `DOMAIN_CHILD` | Proposal-line or journal-line identity under an exact parent |
| `DIAGNOSTIC_GENERATION` | Rebuild generation reference; non-semantic |

An identity class is not write permission. Record-family and product ownership
remain enforced by Artifacts G, I, J, K, and L.

A `DOMAIN_CHILD` slot contains exactly one of `parent_ref` and
`parent_slot_name`. A same-plan parent slot must exist in the canonical request
and resolve before the child grant is derived. Non-child slots prohibit both
fields. This permits a new journal and its lines to be granted in one complete
request without a second allocation pass.

### 6.3 Determinism and uniqueness

- Identical complete slot sets return byte-identical grant sets regardless of
  caller order; returned grants are canonicalized by `slot_name`.
- Different slot names under one request return distinct identities where the
  owning contract requires distinct permanent records.
- Different requests cannot knowingly issue the same permanent identity within
  a uniqueness scope.
- A collision detected during staging or commit fails closed; no fallback
  allocation occurs.
- The provider must reproduce grants after process restart either by deterministic
  calculation or a durable mapping outside domain truth.
- Provider implementation details never appear in a semantic identifier.

### 6.4 Values that are not identity grants

The following remain exact inputs or deterministic semantic derivations:

- source-system and business-object identities;
- command and correlation identities;
- actor and evidence identities;
- Artifact F opaque references;
- content and semantic hashes;
- `effective_date` and period identifiers;
- state tokens;
- posting and publication effect keys; and
- version numbers and line positions governed by section 7.

### 6.5 Closed slot-plan registry

The application may request only slots resolved from:

```text
AuthoritySlotPlanRegistry
  resolve(
    operation_mode,
    command_or_admission_type,
    input_contract_version
  ) -> AuthoritySlotPlanDescriptor | UnsupportedSlotPlan

  instantiate(descriptor, typed_outcome)
      -> IdentityPlanRequest + SequenceRequest[] | UnsupportedOutputShape

AuthoritySlotPlanDescriptor
  operation_mode
  command_or_admission_type
  input_contract_version
  permitted_identity_slot_templates[]
  permitted_sequence_kinds[]
  dynamic_cardinality_basis[]
```

The registry is populated only from the outputs already fixed by Artifacts I,
J, K, and L:

| Operation family | Permitted semantic slot templates |
|---|---|
| Candidate assessment | Candidate receipt; declared Hermes admission product; G-02 publication; command result |
| Admitted-event publication | Admitted business event; G-01 publication; command result |
| Proposal construction | Proposal family/treatment; proposal lines from exact rule or correction input; command result |
| Proposal/period/case transition | Accounting event; newly created lifecycle-subject family where applicable; required G-04/G-05 publications; command result; G-14/disposition/evidence-declaration union only where Artifact I permits pre-construction rejection |
| Module-owned analysis/governance/planning command | Exact Artifact L J-AR02 product discriminators; required J-AR12 evidence declaration where fixed by Artifact J; required G publication; command result |
| Journal posting | Accounting event; journal; journal lines from exact approved proposal; J-AR15 claim identity derived from effect key; G-04/G-05 publications; command result |
| Reporting publication | Accounting event; reporting version; J-AR15 claim identity derived from effect key; G-04/G-05/G-06 publications; command result |
| Source-domain approval | Exact approval and conditional candidate J-AR02 products; command result; no invented G publication |
| Runtime baseline | Manifest-declared identities only; no runtime semantic identity slots |
| Pre-scope reporting import | Imported G-06 publication and any proof-content slots not already supplied by the sealed candidate; J-AR11 `import_id` and sealed reporting refs remain supplied |
| Referenced prior journal | J-AR17 custody and G-13 publication slots; source journal identities remain supplied |
| Query/rebuild | No semantic identity slots; rebuild may request one diagnostic generation slot |

Dynamic line cardinality and ordered member hashes are resolved only from the
single typed planner or owner-operation result. The result must itself bind the
exact governed posting rule, correction input, or approved proposal already
included in the authority seed. Registry instantiation is structural extraction,
not a second planner or domain decision. The registry cannot introduce a record
family, Artifact L discriminator, G contract, or command result not permitted by
those binding artifacts.

## 7. Deterministic Sequence Authority Port

### 7.1 Closed sequence kinds

Artifact M permits exactly two semantic sequence kinds:

```text
FAMILY_VERSION
ORDERED_CHILD_POSITION
```

Post-commit observation positions and rebuild-generation diagnostics are
non-semantic and remain outside this port.

### 7.2 Request and grant

```text
SequenceRequest
  basis
  sequence_kind
  scope_ref
  predecessor_ref                  # absent only for an initial family
  predecessor_version              # absent only for an initial family
  predecessor_state_token          # required for a successor family version
  ordered_member_hashes[]          # required only for ordered children

SequenceGrant
  basis_hash
  sequence_kind
  scope_ref
  values[]
  predecessor_ref
  predecessor_state_token
  grant_hash
```

```text
DeterministicSequenceAuthority
  grant_sequence(SequenceRequest)
      -> SequenceGrant | AuthorityRequestFailure
```

### 7.3 Family-version rules

For `FAMILY_VERSION`:

- no predecessor yields exactly `[1]`;
- an exact predecessor version `n` yields exactly `[n + 1]`;
- predecessor reference, version, and state token must agree;
- a family identifier alone cannot substitute for the exact predecessor;
- skipped, negative, zero, caller-selected, or multi-value grants are rejected;
  and
- final commit still compares the exact Artifact J state token.

This applies to the in-scope proposal, module-product, issue, and
reporting-version families where a new version is required. Restatement-case and
accounting-period lifecycle state is event-token derived and receives no family
sequence. A canonical version already supplied through baseline or pre-scope
import is validated, not reallocated.

### 7.4 Ordered-child rules

For `ORDERED_CHILD_POSITION`:

- `scope_ref` is the exact parent proposal or journal identity;
- `ordered_member_hashes` is non-empty and preserves every member, including
  byte-identical members where the owning line contract permits them;
- returned values are exactly `[1, 2, ..., n]` in the supplied frozen order;
- changing order or content changes the request and grant hash; and
- commit validates line identity, position, parent, totals, and journal binding.

The port does not sort business content. The proposal or correction constructor
must freeze the intended order before requesting proposal or journal positions.

### 7.5 Authority failure boundary

`AuthorityRequestFailure` is a closed non-authoritative result:

```text
AuthorityRequestFailure
  authority_contract_version       # constant 1
  failure_class                    # REQUEST_CONTRACT_FAILURE,
                                   # PROFILE_RESOLUTION_FAILURE,
                                   # DETERMINISM_FAILURE,
                                   # IDENTITY_COLLISION_FAILURE, or
                                   # SEQUENCE_PREDECESSOR_FAILURE
  reason_code
  operation_key
  request_hash                     # present when canonical request exists
```

A request/profile failure before a valid `CommandContext` exists means the
application boundary has not accepted a command attempt. It creates no J-AR14 or
G-14; caller correction or infrastructure recovery may present the same logical
request again.

After a unit of work is open, an authority determinism, identity, or sequence
failure is an invariant failure. The transaction rolls back and the application
does not fabricate a domain rejection. Expected stale-state and effect-consumed
outcomes continue through Artifact K arbitration and are never reclassified as
authority failures.

## 8. Composition With Artifact K

### 8.1 Ordinary command order

The ordinary command path is refined as follows without changing Artifact K's
unit-of-work semantics:

1. receive or derive stable command and correlation identities;
2. resolve the exact authority-profile basis and canonical authority seed
   digest;
3. obtain the deterministic operation-time grant;
4. construct the unchanged Artifact K `CommandContext`, using the grant's
   `semantic_as_of_time` and including the profile in `authority_refs`;
5. open `CommandUnitOfWork` and resolve the prior J-AR14 before domain
   execution;
6. if a matching prior result exists, return it and do not plan or stage;
7. load exact records and state tokens at the granted semantic time;
8. invoke the single pure planner or typed non-lifecycle operation with the
   command, immutable state, and deterministic time grant;
9. resolve the closed output-slot plan from that one typed result, including the
   permitted Artifact K conflict alternative for an accepted command;
10. request the complete named identity grant set and applicable sequence grants;
11. materialize canonical outputs from the typed result and grants without
    re-running domain logic;
12. stage and validate the complete accepted or rejection-only set; and
13. arbitrate and commit through Artifact K, then emit removable observations.

Authority requests are deterministic and non-authoring. Calling them before a
failed commit does not create a partial domain write.

### 8.2 Command input and output binding

The authority-profile basis is part of the authority seed and the exact time
grant is part of the final command input digest. Identity and sequence grant
hashes are reproducible from:

- command owner and identity;
- authority seed digest;
- exact authority-profile basis;
- exact upstream references and state tokens; and
- the exact typed outcome and its registry-resolved output slots.

The committed J-AR14 remains the authoritative proof of command outcome and
enumerates the actual output identities and hashes. Artifact M does not add a
parallel authority-result record.

### 8.3 Expected rejection

A domain or conflict rejection uses the same operation-time grant as its logical
command. A retry returns the original J-AR14 result. It does not issue a new
semantic rejection time, G-14 identity, or publication identity.

## 9. Administrative, Query, and Rebuild Modes

### 9.1 Runtime baseline

The baseline manifest supplies every admitted semantic identity, timestamp,
version, and hash. The authority ports validate the manifest's exact profile and
operation basis but do not renumber or retime baseline truth.

Any admission receipt diagnostics may use the operation time grant. They do not
become J-AR14 or alter admitted record hashes.

### 9.2 Pre-scope reporting import

The sealed predecessor supplies historical publication and content values. The
import operation:

- preserves `original_published_at`;
- uses its grant for `imported_at`, platform recording, and the visibility floor;
- preserves J-AR11 `import_id` as the exact supplied operation and record
  identity, while obtaining any genuinely new imported J-AR13 or proof-content
  identities through named slots; and
- returns the prior exact import receipt on identical retry.

It emits no command identity, accounting event, or ordinary publication effect.

### 9.3 Referenced prior journal

The exact source journal identity and hash form the stable operation key. Source
journal identities, lines, and historical values remain supplied. Any new
J-AR17 custody identity and G-13 J-AR13 publication identity use named slots
bound to that source hash.

Identical retry reproduces the same grants and returns the prior receipt. A
different source hash under the same source reference is a conflict, not a new
allocation.

### 9.4 Query

A query receives only a `SemanticAsOfGrant`. It allocates no semantic identity or
version. Repeating the same exact query at the same semantic time returns the
same semantic records even if wall-clock time advances.

### 9.5 Rebuild

A rebuild receives an explicit as-of grant and may receive a non-semantic
`DIAGNOSTIC_GENERATION` identity. It reuses authoritative semantic identifiers,
versions, times, and hashes exactly. It cannot call the semantic sequence port,
allocate replacement domain identities, or repair missing history.

## 10. Allocation Responsibility Matrix

| Value | Supplied | Identity authority | Sequence authority | Time authority | Derived by domain/configuration |
|---|---:|---:|---:|---:|---:|
| Every `command_id` | Yes | No | No | No | No |
| Source or platform `correlation_id` | Yes | No | No | No | No |
| Business/source object ID | Yes | No | No | No | No |
| Runtime-authored J-AR permanent record ID except supplied administrative identities and J-AR15 | No | Yes | No | No | No |
| J-AR11 `import_id` and manifest-supplied administrative identity | Yes | No | No | No | No |
| J-AR15 effect-claim identity | No | No | No | No | Exact effect class and key |
| Domain family ID | No where runtime-authored | Yes | No | No | No |
| Family version number | No | No | Yes | No | No |
| Accounting `event_id` | No | Yes | No | No | No |
| `causation_event_id` | Exact prior event | No | No | No | Validated from state |
| Proposal/journal-line identity | No | Yes | No | No | No |
| Proposal/journal-line number | No | No | Yes | No | No |
| Contract-publication identity | No | Yes | No | No | No |
| Effect key | No | No | No | No | Exact effect class and subject |
| Content hash | No | No | No | No | Canonical bytes |
| Economic effective date | Yes | No | No | No | No |
| Platform action/recording time | No or evidenced action | No | No | Yes | No |
| `semantic_as_of_time` | No | No | No | Yes | No |
| Adapter row ID or lock version | Physical only | No | No | No | Adapter-private |

## 11. C-001 Authority Proof

### 11.1 Accounting-event grants

The canonical fixture authority profile must reproduce the eleven event grants
below from the same port used by non-canonical runs.

| Event slot | `event_id` | `action_at` | `recorded_at` |
|---|---|---|---|
| Submit original proposal | `AE-C001-001` | `2026-07-03T09:00:00Z` | `2026-07-03T09:00:01Z` |
| Defer original proposal | `AE-C001-002` | `2026-07-09T16:00:00Z` | `2026-07-09T16:00:01Z` |
| Hard close period | `AE-C001-003` | `2026-07-10T18:00:00Z` | `2026-07-10T18:00:01Z` |
| Propose restatement | `AE-C001-004` | `2026-07-12T09:00:00Z` | `2026-07-12T09:00:01Z` |
| Submit correction proposal | `AE-C001-005` | `2026-07-13T09:00:00Z` | `2026-07-13T09:00:01Z` |
| Approve correction proposal | `AE-C001-006` | `2026-07-13T10:00:00Z` | `2026-07-13T10:00:01Z` |
| Post correction journal | `AE-C001-007` | `2026-07-13T10:05:00Z` | `2026-07-13T10:05:01Z` |
| Link adjustment | `AE-C001-008` | `2026-07-13T10:15:00Z` | `2026-07-13T10:15:01Z` |
| Freeze manifest | `AE-C001-009` | `2026-07-13T11:00:00Z` | `2026-07-13T11:00:01Z` |
| Approve restatement | `AE-C001-010` | `2026-07-13T14:00:00Z` | `2026-07-13T14:00:01Z` |
| Publish reporting version | `AE-C001-011` | `2026-07-14T09:00:00Z` | `2026-07-14T09:00:01Z` |

The profile does not infer these values from event order or identifier prefixes.
It resolves them from the exact operation basis and declared slots.

### 11.2 Version and identity grants

C-001 additionally proves:

- the initial automated proposal family version is `P-551@v1`;
- the restatement correction uses the exact predecessor and derives
  `P-551@v2`;
- the predecessor reporting version is supplied through pre-scope import and is
  not reallocated;
- the initial restatement-case family identity `RC-001` is granted for
  `restatement.proposed`, while every later case state is derived from its exact
  accounting-event token and receives no family-version sequence;
- the successor reporting version derives version 2 from that exact predecessor;
- Aegis issue successors derive only from exact predecessor references and state
  tokens, while restatement-case state remains event-token derived;
- J-560 and its line identities are granted after the typed posting outcome fixes
  the journal-line shape and before materialization; they become authoritative
  only with `journal.posted`; and
- posting and publication effect keys derive from exact targets independently
  of command identities.

### 11.3 Retry and non-canonical proof

Redelivering any C-001 command under the same identity and input digest returns
the original J-AR14 and creates no new grant-dependent output. A non-canonical
instance replaces identities and dates through its supplied inputs and authority
profile while preserving all slot, version, timing, ownership, and causality
rules.

## 12. CT-1 Authority Proof

### 12.1 Accounting-event grants

| Event slot | `event_id` | `action_at` | `recorded_at` |
|---|---|---|---|
| Submit reversal | `AE-CT1-001` | `2026-07-11T09:00:00Z` | `2026-07-11T09:00:01Z` |
| Approve reversal | `AE-CT1-002` | `2026-07-11T09:30:00Z` | `2026-07-11T09:30:01Z` |
| Post reversal | `AE-CT1-003` | `2026-07-11T09:31:00Z` | `2026-07-11T09:31:01Z` |
| Submit replacement | `AE-CT1-004` | `2026-07-11T09:40:00Z` | `2026-07-11T09:40:01Z` |
| Approve replacement | `AE-CT1-005` | `2026-07-11T10:00:00Z` | `2026-07-11T10:00:01Z` |
| Post replacement | `AE-CT1-006` | `2026-07-11T10:01:00Z` | `2026-07-11T10:01:01Z` |

### 12.2 Correction proof

CT-1 additionally proves:

- J-010 and its historical times and identities remain supplied G-13 source
  state and are never reallocated;
- Hermes G-03 and Argus/Aegis module products use owner-scoped named identity and
  version grants;
- reversal and replacement proposal families use independent exact grants;
- J-011 and J-012 use different journal and line identity slots;
- reversal and replacement effect keys derive independently from their exact
  proposal targets;
- G-13 source-hash binding occurs before reversal line derivation; and
- the final Aegis issue update derives its successor version from the exact prior
  issue and G-07 verification.

CT-1 allocates no restatement case, reporting version, G-10, G-11, G-12, or
approved-decision return.

## 13. Failure and Retry Matrix

| Condition | Required outcome |
|---|---|
| Ambient wall-clock or random generator used for semantic field | Fail conformance |
| Provider registry cannot resolve exact committed profile identity and hash | Pre-context authority failure; no command result |
| Exact J-AR04 profile is not yet available at granted semantic time | Target-owner unavailable-input outcome before planning |
| Loaded J-AR04 profile hash differs from provider basis | Invariant failure; roll back |
| Same operation basis produces a different grant | Authority invariant failure |
| Same command identity names different profile, seed, or final command input digest | Command-identity conflict; preserve original result |
| Unknown identity class, sequence kind, or slot | Reject authority request |
| Declared action timestamp changes under same operation identity | Identity/input conflict; write nothing |
| `action_at > recorded_at` | Reject grant |
| Required input unavailable at `semantic_as_of_time` | Reject or block command under owning policy |
| Publication availability predates required bound | Reject staged write set |
| Permanent identity collides with different semantic content | Roll back; no fallback identity |
| Successor sequence lacks exact predecessor state token | Reject sequence request |
| Successor sequence skips a version | Reject sequence request |
| Concurrent commands derive same successor from same predecessor | Artifact K arbitration permits at most one commit |
| Ordered-child hashes change after grant | Reject staged write set |
| Effect key reused under different command | Commit required effect-consumed rejection only |
| Failure before commit | No authoritative allocation record exists; identical retry reproduces grants |
| Lost acknowledgement after commit | Reopen with same command identity/digest and return original J-AR14 |
| Restart before retry | Same profile and basis reproduce same grants or prior result |
| Rebuild attempts to allocate semantic replacement identity | Fail rebuild |

## 14. Conformance Catalog

Artifact M's implementation must make the following tests executable.

| ID | Required proof |
|---|---|
| M-T01 | Static dependency check finds no ambient clock call in planner, domain operation, repository facet, serializer, or adapter semantic-write path. |
| M-T02 | Source occurrence, source recording, effective dates, and original publication time survive runtime handling byte-unchanged. |
| M-T03 | Identical time requests return byte-identical grants across two calls. |
| M-T04 | Identical time requests return byte-identical grants across process restart. |
| M-T05 | A different authority profile under the same command identity produces command-identity conflict rather than a new execution. |
| M-T06 | `SYSTEM_ACTION` grants satisfy semantic-as-of, action, and recording ordering. |
| M-T07 | `DECLARED_ACTION` preserves the evidenced timestamp and rejects a changed declared time on retry. |
| M-T08 | Normal reads and publications enforce exact semantic availability bounds. |
| M-T09 | Query replay at the same semantic as-of time ignores later wall-clock time. |
| M-T10 | Pre-scope import preserves original publication and satisfies hard-close, import, recording, and availability ordering. |
| M-T11 | One complete named identity request returns the same byte-equivalent slot-sorted grant set independent of caller order or provider call internals. |
| M-T12 | Adding, removing, or changing an identity slot changes or rejects the request rather than shifting unrelated identities; reordering an unchanged set does not. |
| M-T13 | Distinct required slots cannot resolve to one permanent identity in the same uniqueness scope. |
| M-T14 | A semantic identity collision with different content rolls back without fallback allocation. |
| M-T15 | Identifier prefixes and fixture formats are never used for owner, type, or routing decisions. |
| M-T16 | External initial command identity is required before opening the command unit of work. |
| M-T17 | Every internally coordinated follow-on command arrives with a stable supplied command identity before dispatch; changing that identity is a distinct logical command subject to ordinary state and effect guards. |
| M-T18 | Initial family sequence returns exactly version 1. |
| M-T19 | Exact predecessor version `n` and state token return exactly version `n+1`. |
| M-T20 | Missing, stale, skipped, or family-only predecessor input is rejected. |
| M-T21 | Two commands against one predecessor may derive the same candidate successor, but at most one commits under Artifact K arbitration. |
| M-T22 | Ordered proposal/journal-line hashes return positions `1..n`; reordered or changed hashes invalidate the grant. |
| M-T23 | Accounting causality resolves exact predecessor event identities and never a numeric sequence. |
| M-T24 | Posting and publication effect keys remain identical for the same target under different command identities and authority profiles. |
| M-T25 | The planner cannot resolve a port or construct an undeclared grant. |
| M-T26 | The persistence adapter cannot allocate semantic time, identity, version, line position, or effect key. |
| M-T27 | Identical command retry before a successful write reproduces grant candidates and commits at most one outcome. |
| M-T28 | Lost acknowledgement retry returns the original J-AR14 and outputs without reissuing semantic values. |
| M-T29 | All three administrative write modes use their declared operation keys and preserve their distinct retry/conflict outcomes. |
| M-T30 | Rebuild may allocate only a diagnostic generation identity and reproduces all semantic values from authoritative inputs. |
| M-T31 | Canonical C-001 reproduces all eleven exact event identities and timestamp pairs. |
| M-T32 | Canonical CT-1 reproduces all six exact event identities and timestamp pairs. |
| M-T33 | Non-canonical C-001 and CT-1 instances use the same slots and rules without literal-identity branches. |
| M-T34 | Authority-issued semantic fields participate in canonical object hashes while adapter diagnostic values do not. |
| M-T35 | Unknown mode, profile, identity class, slot, or sequence kind is rejected before planning. |
| M-T36 | An instrumented rebuild receives its explicit as-of grant but makes no semantic identity or sequence allocation call and preserves all authoritative times. |
| M-T37 | Runtime baseline validates and commits one sealed authority-profile candidate without requiring it to pre-exist; mismatched bytes, identity, hash, or provider fail atomically. |
| M-T38 | Every basis, request, and grant rejects unknown fields and reproduces its declared canonical hash under `SORTED_KEYS_COMPACT_UTF8_V1`. |
| M-T39 | Pre-context authority failure creates no command result, while a post-open determinism/allocation failure rolls back as an invariant failure without fabricated J-AR14 or G-14. |
| M-T40 | Same-plan child slots resolve only through an existing parent slot; missing, cyclic, dual, or non-child parent declarations are rejected. |
| M-T41 | Every I-S01 through I-S26 operation, both CT-1 producer repairs, and every Artifact K administrative mode resolves one closed slot-plan descriptor; an extra output slot or discriminator is rejected. |
| M-T42 | A proposal or journal command invokes its planner exactly once, derives line cardinality and ordered hashes from that typed result, obtains grants afterward, and materializes without a second guard or domain-rule evaluation. |
| M-T43 | Posting/publication derives the J-AR15 claim identity from the exact effect class and key, while reconciliation and pre-construction rejection include their required J-AR12 evidence-declaration slots; none requests an undeclared identity-authority slot. |
| M-T44 | Initial restatement proposal grants one restatement-case family identity, while every later case transition reuses that identity and advances only by exact accounting-event token. |
| M-T45 | Pre-scope import uses the exact supplied `import_id` as J-AR11 identity, allocates no replacement for it, and grants only genuinely new records absent from the sealed candidate. |
| M-T41 | Every I-S01 through I-S26 operation, both CT-1 producer repairs, and every Artifact K administrative mode resolves one closed slot-plan descriptor; an extra output slot or discriminator is rejected. |
| M-T38 | Every basis, request, and grant rejects unknown fields and reproduces its declared canonical hash under `SORTED_KEYS_COMPACT_UTF8_V1`. |

## 15. Acceptance Criteria

Artifact M may be ratified only when all of the following hold.

- M-A01: all semantic time, identity, and sequence sources are explicit and
  injectable;
- M-A02: economic dates and source occurrence/recording times are preserved as
  supplied truth;
- M-A03: one operation-time grant distinguishes semantic as-of, action, and
  recording time;
- M-A04: system and declared action variants are closed and validated;
- M-A05: identical operation basis and authority profile reproduce identical
  grants across retry and restart;
- M-A06: semantic availability always uses the injected as-of value and never an
  adapter clock;
- M-A07: every ordinary authority profile is an exact available J-AR04 reference
  included in command authority and input digest;
- M-A08: all three ports share one closed six-mode operation basis;
- M-A09: semantic identifiers are opaque and no prefix carries authority;
- M-A10: command identity exists before deduplication and remains stable across
  delivery retry;
- M-A11: identity allocation is complete-set, named-slot, and call-order
  independent;
- M-A12: an unused grant creates no authoritative or lifecycle state;
- M-A13: identity collision with different semantic content fails without silent
  reallocation;
- M-A14: initial and successor versions derive only as `1` and exact
  predecessor `n+1`;
- M-A15: every successor sequence binds an exact Artifact J predecessor state
  token;
- M-A16: proposal and journal line positions bind frozen ordered line hashes;
- M-A17: accounting-event causality remains reference-based rather than numeric;
- M-A18: effect keys derive independently of command identity;
- M-A19: planners and persistence adapters cannot call authority allocation
  functions;
- M-A20: baseline, import, and referenced-journal modes use their ratified stable
  keys without J-AR14;
- M-A21: semantic authority-issued fields and adapter diagnostics remain
  structurally distinct;
- M-A22: no J-AR, G, Artifact F object/event, or workflow class is added;
- M-A23: all authority request and grant variants reject unknown fields and
  unsupported discriminators;
- M-A24: C-001 reproduces its eleven canonical accounting-event identities and
  timestamp pairs through the injected profile;
- M-A25: CT-1 reproduces its six canonical accounting-event identities and
  timestamp pairs through the injected profile;
- M-A26: canonical compatibility does not require branching on a canonical
  identifier or date;
- M-A27: non-canonical instances preserve the same authority slot and sequencing
  contracts;
- M-A28: lost acknowledgement and process restart preserve the original
  committed outcome;
- M-A29: query and rebuild semantics remain fixed to explicit as-of time;
- M-A30: rebuild cannot allocate or repair semantic history;
- M-A31: the complete M-T01 through M-T45 catalog is implementable without a
  database or physical schema decision; and
- M-A32: Artifact F payloads, Artifact L bodies, Artifact K modes, and all five
  platform invariants remain unchanged; and
- M-A33: runtime baseline resolves its authority profile only through the sealed,
  manifest-bound bootstrap variant, while every other mode requires committed
  available J-AR04 configuration; and
- M-A34: authority bases, requests, and grants use strict version-1 contracts and
  reproducible canonical hash boundaries; and
- M-A35: the authority failure taxonomy preserves the boundary between an
  unaccepted application request, invariant failure, expected command rejection,
  and Artifact K conflict arbitration; and
- M-A36: child-identity requests support one existing or same-plan parent without
  permitting missing, cyclic, or ambiguous parentage; and
- M-A37: one finite slot-plan registry closes every C-001, CT-1, and
  administrative output set without permitting speculative identities;
- M-A38: dynamic proposal and journal output shape comes from the single typed
  planner result before authority materialization, with no duplicated domain
  logic; and
- M-A39: J-AR15 effect-claim identity and the reconciliation/pre-construction
  J-AR12 evidence declarations follow their exact existing contracts without
  hidden allocation;
  and
- M-A40: a restatement case receives one granted family identity at creation and
  no family-version sequence at any lifecycle transition; and
- M-A41: pre-scope import preserves its exact supplied J-AR11 `import_id` and
  never allocates a replacement administrative identity.

## 16. Decisions Resolved and Deferred

### 16.1 Resolved by Artifact M

- explicit separation of economic, source, action, recording, as-of, and
  diagnostic time;
- one deterministic time grant per logical operation;
- governed authority profiles bound into operation identity and command digest;
- bulk named-slot semantic identity allocation;
- exact initial/successor version derivation;
- proposal and journal-line position derivation;
- stable supplied command and correlation identity at the application boundary;
- effect-key derivation outside identity allocation; and
- retry/restart behaviour for every grant type.

### 16.2 Deferred beyond Artifact M

1. provider implementation and library choice;
2. migration compatibility and persisted contract-version policy;
3. physical database engine, schema, indexes, and transactions;
4. runtime evidence port and content-byte storage beyond the bounded reporting
   proof;
5. projection checkpoint representation and operational rebuild tooling;
6. Milestone 2 assertion-report schema;
7. runtime package layout; and
8. public API, transport, authentication, UI, deployment, or multi-tenant design.

## 17. Recommended Next Move

Draft the next design artifact for migration compatibility and persisted
contract-version semantics. It must define how ratified version-1 authority,
message, record, and canonicalization contracts remain readable and replayable
after a successor contract is introduced, without selecting a database or
physical migration tool.

Database selection and runtime package extraction remain premature until that
compatibility boundary is ratified and the Milestone 2 cohesion audit confirms
that the complete Phase 0 design remains implementable as one vertical slice.
