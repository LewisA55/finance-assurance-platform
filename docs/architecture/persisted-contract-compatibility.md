# Artifact N - Persisted Contract Compatibility and Migration Semantics

Status: Design v0.2.1 - ratified 2026-08-05

## 0. Purpose and Closure Rule

Artifact N defines how a later runtime release can read, verify, replay, rebuild,
and consume authoritative records written under an earlier ratified contract
without rewriting historical truth or selecting a physical database migration
tool.

Its scope is semantic compatibility, not storage migration.

The governing rule is:

> A contract may evolve. An authoritative record does not. Its original bytes,
> contract coordinate, canonicalization treatment, identity, and semantic hash
> remain permanently bound.

Artifact N is closed when:

- every persisted authoritative record declares the exact contract and
  canonicalization coordinates needed to verify it;
- a runtime proves support for every coordinate already present before it may
  serve commands, queries, or rebuilds;
- exact historical reads never upcast or rewrite stored bytes;
- any adapted read is deterministic, governed, labelled, and traceable to its
  original authoritative reference;
- a new write version is selected explicitly by exact command/output family and
  semantic time rather than by `latest`;
- command deduplication binds every compatibility policy and adapted-input
  treatment that affected planning;
- projection rebuild can consume mixed persisted versions without mutating
  authoritative history;
- C-001 and CT-1 remain byte-compatible under the current version-1 baseline;
  and
- no speculative Artifact F v2, G contract, J-AR family, Artifact L body,
  workflow, database, ORM, or migration framework is introduced.

Artifact N does not define a physical table, column migration, backfill job,
deployment orchestrator, rolling-upgrade protocol, public API version, external
event schema, or data-retention policy.

## 1. Binding Sources

Artifact N is subordinate to:

- the five invariants and architecture rules in `AGENTS.md`;
- Artifact F v0.2.1 - Minimum Payload Contracts;
- Artifact H v0.3.1 - Executable Validation Harness Specification;
- Artifact I v0.2.2 - Runtime Application Boundary;
- Artifact J v0.2 - Authoritative Records and Rebuildable Projections;
- Artifact K v0.2.2 - Persistence Port and Transactional Unit-of-Work Contract;
- Artifact L v0.2.1 - Internal Runtime Message Contracts and Module-Product
  Registry;
- Artifact M v0.2.1 - Deterministic Time, Identity, and Sequence Authority Ports;
- canonical transactions C-001 and CT-1; and
- ADR-012 through ADR-023.

Artifact F remains authoritative for its payload versions. Artifact J remains
authoritative for immutable record identity and rebuild sources. Artifact K
remains authoritative for atomic commit, retry, and six persistence modes.
Artifact L remains authoritative for G and J-AR02 body versions. Artifact M
remains authoritative for authority-contract and canonicalization values used by
runtime construction.

## 2. Vocabulary and Migration Axes

### 2.1 Runtime release

A runtime release is deployable code. Its build number is not a semantic
contract version and never enters authoritative business or accounting content
unless a ratified contract explicitly requires an implementation reference.

### 2.2 Semantic contract version

A semantic contract version selects the closed fields, variants, invariants,
ownership, and validation rules for one typed value. Existing examples include:

- Artifact F `contract_version`;
- Artifact L `g_contract_version` and `body_contract_version`;
- J-AR02 `body_contract_version`;
- Artifact K command `input_contract_version`;
- Artifact M `authority_contract_version`; and
- reporting or evidence `content_schema_version`.

These versions remain distinct. Artifact N does not coerce them into one global
integer or compare unlike version types lexically.

### 2.3 Canonicalization version

A canonicalization version defines the exact bytes hashed for a logical value.
It is not a body schema version. Changing canonicalization does not authorize a
body change, and changing a body contract does not silently change
canonicalization.

### 2.4 Physical schema version

A physical schema version describes storage layout. It is outside Artifact N.
Moving unchanged semantic bytes between physical layouts is not a semantic
contract migration.

### 2.5 Compatibility adaptation

A compatibility adaptation is a pure read-time transformation from one exact
semantic contract coordinate to another approved read coordinate. It creates a
derived view, not a replacement authoritative record.

### 2.6 Projection migration

A projection migration is deletion and deterministic rebuild of J-P01 through
J-P12 into one declared projection contract. It never mutates J-AR01 through
J-AR17.

## 3. Rulings

### N-R01 - Authoritative bytes are never migrated in place

An authoritative record retains forever:

- record family and permanent identity;
- exact record-contract coordinate;
- exact body-contract coordinate where one exists;
- original canonicalization version;
- canonical body bytes or immutable content reference;
- body/content hash;
- complete authoritative semantic hash; and
- original upstream, evidence, creation, and availability bindings.

A later runtime cannot rewrite, normalize, default, rename, reserialize, or
rehash those fields under a newer version.

### N-R02 - Every authoritative record has an explicit contract stamp

J-AR01 through J-AR17 use an outer `PersistedContractStamp` in addition to any
version fields already present inside their body. The stamp does not duplicate
or replace body fields; equality is required wherever both carry the same
version fact.

The stamp is semantic and participates in the J-AR record hash.

The outer stamp is the bootstrap contract that lets a runtime select a decoder
before it can trust the body's own version fields. Retaining both forms is
therefore deliberate rather than redundant: the outer stamp selects the body
decoder, and validation then requires every duplicated inner version fact to
equal the stamp.

### N-R03 - Contract coordinates are typed, not one universal string

Artifact F, G, J-AR02, command input, authority, internal J-AR, and bounded
content coordinates use a closed discriminated union. A consumer cannot infer a
contract family by parsing `v1`, `G-v0.2`, an identifier prefix, or a record
body.

### N-R04 - Persisted-version support is a startup invariant

Before serving any semantic operation, a runtime compares the persisted
contract inventory with its exact implementation manifest and governed
compatibility policy.

If any persisted authoritative coordinate lacks its required decoder,
canonicalizer, validator, and approved replay treatment, the runtime fails the
compatibility preflight. It does not serve partially supported data.

Milestone 2 deliberately has no bounded read-only degradation mode. Such a mode
would require compatibility gating for every operation and an operational
continuity policy, while this milestone has neither a production deployment nor
an availability requirement. A failed preflight may still expose its diagnostic
receipt or failure to an operator, but no semantic command, query, publication,
or rebuild is served.

### N-R05 - Exact read remains the primary historical read

An exact read returns the original contract stamp, canonical bytes or immutable
content reference, and authoritative hash. It never adapts to an active write
version and never labels adapted bytes as original.

### N-R06 - Adapted reads are explicit derived views

A caller requesting a different read coordinate must name that exact target. An
approved deterministic adapter may produce a `CompatibilityReadView` that
retains the original authoritative reference and full adaptation binding.

The view has no J-AR identity, cannot satisfy an `AuthoritativeRef`, and may be
deleted and reconstructed.

### N-R07 - There is no implicit latest version

Commands, queries, publications, rebuilds, registries, and adapters select exact
coordinates. The terms `latest`, `current schema`, and `most recent compatible`
are invalid semantic selectors.

### N-R08 - Compatibility cannot cross truth or event classes

An adapter cannot transform:

- `accounting_event` into `business_event`;
- business-event truth into accounting truth;
- an exception into a finding or issue;
- a recommendation into operational approval;
- declaration-only evidence into verified evidence; or
- a non-authored G-13 source into an Atlas-authored journal.

The business/accounting event firewall therefore survives all contract versions.
Source and target must also retain the same semantic family: Artifact F payload
class and discriminator, G contract ID/body discriminator/publisher, J-AR record
family, J-AR02 product discriminator/owner, governed-configuration discriminator,
command owner/type, authority value class, or bounded-content discriminator as
applicable.

### N-R09 - Compatibility adapters are pure and finite

Each adapter:

- names one exact source and target coordinate;
- has a stable adapter identity and contract version;
- validates the source before transformation;
- has no clock, random generator, persistence, network, authority-port, or
  workflow dependency;
- returns deterministic target logical bytes or a typed incompatibility;
- preserves the original authoritative reference; and
- rejects unknown fields under the source contract before adapting.

### N-R10 - An adapter may derive but may not invent

Target fields may be populated only from:

- exact source fields;
- deterministic calculations over those fields; or
- exact governed configuration named by the compatibility policy and included
  in the adaptation binding.

An adapter cannot fabricate missing evidence, authority, accounting dates,
currency, identity, state tokens, lineage, or business meaning. If the target
requires unavailable meaning, no compatibility edge exists.

### N-R11 - Reverse and lossy adaptation are prohibited in Milestone 2

The Milestone 2 runtime supports exact reads and approved forward read adapters
only. It does not downcast a newer authoritative body into an older body, drop
fields, coerce an unknown enum, or claim semantic equality after information
loss.

A future need for a bounded external downcast requires a separate artifact and
cannot become an authoritative write path.

### N-R12 - Adaptation is exact or one direct edge

For one source and target coordinate, the governed policy selects either:

- `EXACT`, with zero adapters;
- `ADAPTED`, with one exact direct forward adapter; or
- `UNSUPPORTED`.

Multiple eligible adapters, chained transforms, cycles, self-declared edges, or
runtime graph search by preference are invalid. A later target that must read an
older source requires one explicitly ratified direct adapter for that exact
source/target pair.

### N-R13 - Compatibility policy is governed J-AR04 configuration

One exact J-AR04 compatibility-policy version declares:

- supported persisted read coordinates;
- command-consumable target coordinates;
- active write coordinates by Artifact K operation mode, owner, operation type,
  and output type;
- approved direct adapters;
- required canonicalizer and validator identities;
- projection target coordinates;
- effective range; and
- exact required capability bindings for activated decoders, validators,
  canonicalizers, and adapters.

The policy is configuration, not code and not a generic transformation language.
The initial policy may enter only through the sealed runtime-baseline bootstrap.
Milestone 2 defines no live successor-policy admission or activation path. The
first real successor policy requires an explicit configuration-maintenance
contract, including any necessary Artifact I/K extension and a separate ADR; it
cannot reuse runtime-baseline admission by implication or authorize itself.

### N-R14 - Code capability and governance activation remain separate

The runtime contains a finite `ContractImplementationRegistry`. Its manifest
states which decoders, validators, canonicalizers, and adapters the build can
execute.

Presence in the runtime does not activate a contract version. The exact J-AR04
compatibility policy must also permit that use at the operation's semantic time.

The sole bootstrap exception is decoding and verifying the exact compatibility
policy itself. Startup supplies either one committed policy ref/hash or the
runtime-baseline sealed candidate. The runtime may use only the manifest-named
policy decoder and canonicalizer for that verification; it cannot read or serve
ordinary semantic records until the complete preflight passes.

### N-R15 - One active write coordinate exists per authored output contract

For each Artifact K operation mode, semantic owner, operation type, output
family, and discriminator, the compatibility policy selects exactly one active
write coordinate for every runtime-authored output. New writes use that
coordinate natively from the typed domain or administrative result.

Supplied records admitted by runtime baseline, pre-scope import, or referenced
journal custody retain their supplied coordinates. New attestations, custody
records, evidence declarations, and J-AR13 publications authored by those modes
use their exact mode-specific active write selections.

The runtime does not dual-write two semantic contract versions, create a shadow
authoritative copy, or produce a newer authoritative record by upcasting an old
record.

### N-R16 - Write-version activation is time and operation bound

The active write selection is resolved at `semantic_as_of_time` from one exact
compatibility-policy reference. For commands, that policy reference and selected
output coordinates enter the authority seed and final Artifact K command input
digest. For administrative modes, they enter the exact manifest, import, or
source-admission semantic basis and receipt/conflict identity.

For a command, the bound selection set is the finite union of output families
permitted by Artifact M's exact slot-plan descriptor, including accepted,
rejection, and arbitration alternatives. The planner later chooses the actual
subset. An unused coordinate selection creates no record and does not require an
outcome-dependent second digest.

A retry uses the original selection. Changing policy or output coordinate under
the same operation identity is a command-identity or mode-specific
administrative conflict.

### N-R17 - Historical inputs remain exact upstream authorities

When a command consumes an adapted read view, its authoritative upstream
references still point to the original J-AR records and hashes. The command
input also binds a `CompatibilityBinding` that records the source coordinate,
target read coordinate, policy, adapter chain, and adapted body hash.

An adapter output never replaces source lineage.

### N-R18 - State and effect tokens do not migrate

Lifecycle state tokens remain exact original event, base-record,
construction-result, or product-version tokens. Posting and publication effect
keys remain derived from their original semantic targets.

An adapted view cannot create a new state token, reset concurrency, or permit a
second financial or publication effect.

### N-R19 - Canonical hashes are verified under their original version

The runtime resolves the canonicalizer named by the persisted record and
reproduces the original body and semantic hashes before trusting that record.

If an adapted target view is needed, it receives a separate target body hash and
adaptation hash. Neither overwrites or substitutes for the original hashes.

### N-R20 - Canonicalization evolution does not imply semantic evolution

The same body contract may later support another canonicalization version only
through an explicit contract-policy entry and conformance proof. Old hashes
remain verified with the old canonicalizer. A new canonicalization cannot be
used to rehash existing authoritative records in place.

### N-R21 - Projection versions are derived and labelled

Every promoted J-P01 through J-P12 generation declares:

- projection contract coordinate;
- compatibility-policy reference and hash;
- activated-capability digest;
- semantic as-of time;
- complete source-coordinate inventory digest;
- activated-adapter inventory digest; and
- resulting projection digest.

These are projection-generation semantics, not new authoritative domain facts.

### N-R22 - Rebuild is mixed-version aware and write silent

Rebuild verifies every authoritative record under its own stamp, resolves only
the policy-approved read view needed by the target projection, and preserves the
Artifact J dependency order.

It cannot rewrite authoritative bytes, append a migrated copy, emit a business
or accounting event, publish G, claim an effect, or create J-AR14.

### N-R23 - Cross-version digests are not falsely compared

Authoritative inventory digests remain stable because authoritative records do
not change. Projection digests are comparable only when projection contract,
policy, activated-capability digest, semantic as-of time, and source inventory are
identical.

Different projection versions may be semantically compatible without being
byte-equal. Artifact N never calls unequal versioned bytes identical.

### N-R24 - Unsupported input has boundary-specific handling

- An external candidate with an unsupported declared contract follows Hermes
  G-02 `UNSUPPORTED` handling and produces no G-01.
- A command presented with an unavailable or unsupported persisted input returns
  the target owner's typed unsupported-input outcome before planning.
- Compatibility preflight or rebuild encountering an unsupported persisted
  coordinate fails the whole operation.
- A malformed stored body or hash mismatch is corruption/invariant failure, not
  an unsupported business event.

### N-R25 - Administrative modes preserve supplied historical contracts

Runtime baseline, pre-scope import, and referenced-journal admission validate
their exact supplied contract and canonicalization coordinates. They cannot
normalize candidates to the active write version before commit.

Identical retry resolves against the original supplied coordinate and content.
A changed coordinate under the same administrative identity is a conflict.

### N-R26 - Compatibility support is monotonic for persisted history

Once a contract coordinate exists in authoritative persistence, a later runtime
release cannot drop the ability to decode, validate, canonicalize, and replay it
while those records remain in scope.

Adding a new active write coordinate does not retire the historical read path.

### N-R27 - Contract change remains an architecture decision

Adding a body version, G ownership version, Artifact F event or variant,
J-AR02 discriminator, command version, canonicalization version, or compatibility
adapter requires review, fixtures, conformance tests, and an append-only ADR.

Editing a registry row as operational configuration is prohibited.

### N-R28 - Current production registries remain on the ratified baseline only

Artifact N defines the compatibility mechanism but does not invent a successor
domain contract. The initial policy recognizes only the already-ratified
Artifact F v1, Artifact L body v1, current G ownership version, current command
input versions, Artifact M authority v1, current content schemas, and
`SORTED_KEYS_COMPACT_UTF8_V1`.

Adapter machinery is tested with non-domain conformance values. Those
values cannot be persisted as J-AR, published through G, or enter C-001/CT-1.

## 4. Typed Contract Coordinates

### 4.1 Closed coordinate union

```text
ContractCoordinate =
    ArtifactFPayloadCoordinate
  | GPublicationBodyCoordinate
  | ModuleProductBodyCoordinate
  | GovernedConfigurationCoordinate
  | AuthoritativeRecordCoordinate
  | CommandInputCoordinate
  | AuthorityContractCoordinate
  | BoundedContentCoordinate

ArtifactFPayloadCoordinate
  coordinate_type                   # ARTIFACT_F_PAYLOAD
  payload_class                     # BUSINESS_EVENT, ACCOUNTING_OBJECT,
                                    # or ACCOUNTING_EVENT
  body_discriminator
  payload_contract_version

GPublicationBodyCoordinate
  coordinate_type                   # G_PUBLICATION_BODY
  g_contract_version
  contract_id                       # G-01 through G-14
  body_discriminator
  body_contract_version

GovernedConfigurationCoordinate
  coordinate_type                   # GOVERNED_CONFIGURATION
  configuration_discriminator
  configuration_contract_version

ModuleProductBodyCoordinate
  coordinate_type                   # MODULE_PRODUCT_BODY
  product_discriminator
  body_contract_version

AuthoritativeRecordCoordinate
  coordinate_type                   # AUTHORITATIVE_RECORD
  record_family                     # J-AR01 through J-AR17
  record_contract_version

CommandInputCoordinate
  coordinate_type                   # COMMAND_INPUT
  command_owner
  command_type
  input_contract_version

AuthorityContractCoordinate
  coordinate_type                   # AUTHORITY_CONTRACT
  authority_contract_version

BoundedContentCoordinate
  coordinate_type                   # BOUNDED_CONTENT
  content_discriminator
  content_schema_version
```

Every variant is strict and rejects unknown fields. Version values retain the
type fixed by their owning artifact. The union provides routing, not permission.

### 4.2 Canonicalization coordinate

Canonicalization remains separate:

```text
CanonicalizationCoordinate
  canonicalization_version
```

The current value is `SORTED_KEYS_COMPACT_UTF8_V1`. A future value requires its
own implementation and policy entry even when the body contract is unchanged.

### 4.3 Current baseline coordinates

The initial compatibility policy recognizes:

| Family | Current coordinate |
|---|---|
| Artifact F bodies | Exact listed discriminator with `contract_version = 1` |
| J-AR01 through J-AR17 envelopes | Exact family with `record_contract_version = 1` |
| G publications | `g_contract_version = G-v0.2`, exact G ID/body, body version 1 |
| J-AR02 module products | Exact L-MP01 through L-MP20 discriminator, body version 1 |
| Artifact I and CT-1 command inputs | Exact owner/type, input version 1 |
| Artifact M authority values | Authority contract version 1 |
| Artifact N compatibility policy | `platform.compatibility_policy`, policy contract version 1 |
| Reporting/evidence content | Exact existing content discriminator and schema version |
| Canonicalization | `SORTED_KEYS_COMPACT_UTF8_V1` |

The J-AR outer record version is an internal record-envelope coordinate. It does
not alter the nested Artifact F or Artifact L body.

## 5. Persisted Contract Stamp and Exact Record

### 5.1 Persisted contract stamp

```text
PersistedContractStamp
  stamp_contract_version            # constant 1
  record_contract                   # AuthoritativeRecordCoordinate
  body_contract                     # exact coordinate; absent only where the
                                    # J-AR body has no separately versioned body
  canonicalization                  # CanonicalizationCoordinate
  canonical_body_hash
```

Where the body repeats a contract or canonicalization value, the repeated value
must equal the stamp. Mismatch rejects commit and fails rebuild.

Examples:

- J-AR06 stamps its internal record version and the exact Artifact F
  `accounting_event` coordinate;
- J-AR02 stamps its internal record version and exact Artifact L module-product
  discriminator/body version;
- J-AR13 stamps its internal record version and exact G publication-body
  coordinate; and
- J-AR10 stamps its record version while its content reference separately names
  the bounded reporting-content coordinate.

### 5.2 Version-complete exact read

Artifact N refines, without changing the ownership of, Artifact K's
`ExactRecord` result:

```text
VersionedExactRecord
  authoritative_ref
  owner
  contract_stamp
  canonical_body_or_content_ref
  upstream_refs[]
  evidence_refs[]
  creation_basis
  available_from
```

`authoritative_ref.semantic_hash` must reproduce from the complete record,
including its contract stamp. An exact read never returns a body without its
stamp.

## 6. Implementation Registry and Governed Policy

### 6.1 Runtime implementation manifest

```text
ContractImplementationRegistry
  manifest() -> RuntimeContractManifest
  decoder_for(ContractCoordinate) -> DecoderCapability | UnsupportedCoordinate
  validator_for(ContractCoordinate) -> ValidatorCapability | UnsupportedCoordinate
  canonicalizer_for(CanonicalizationCoordinate)
      -> CanonicalizerCapability | UnsupportedCanonicalization
  adapter_for(AdapterCoordinate) -> AdapterCapability | UnsupportedAdapter

RuntimeContractManifest
  manifest_contract_version         # constant 1
  supported_contract_coordinates[]
  supported_canonicalization_coordinates[]
  supported_adapter_coordinates[]
  manifest_hash
```

The manifest is a deterministic capability declaration for one runtime build.
It is not J-AR, J-P, G, an installable plugin registry, or a service locator
available to domain planners.

### 6.2 Compatibility policy

```text
CompatibilityPolicy
  policy_contract_version           # constant 1
  policy_ref                        # exact J-AR04 version
  required_capability_bindings[]
  persisted_read_support[]
  command_read_targets[]
  active_write_selections[]
  adapter_path_selections[]
  projection_target_selections[]
  effective_from
  effective_to
  canonical_policy_hash
```

Every collection is canonicalized by its complete typed key. Duplicate or
overlapping active selections are rejected.

### 6.3 Support declarations

```text
PersistedReadSupport
  source_contract
  source_canonicalization
  exact_read_enabled                # must be true for persisted history
  command_read_enabled
  rebuild_enabled

ActiveWriteSelection
  operation_mode                   # one of Artifact K's six modes
  semantic_owner
  operation_type
  output_family
  output_discriminator
  target_contract
  target_canonicalization

AdapterPathSelection
  source_contract
  source_canonicalization
  target_contract
  target_canonicalization
  resolution_type                  # EXACT or ADAPTED
  adapter_ref                      # required only for ADAPTED
  adapter_configuration_refs[]     # exact J-AR04 refs; may be empty

ProjectionTargetSelection
  projection_id                    # J-P01 through J-P12
  projection_contract_version
  required_read_targets[]

RequiredCapabilityBinding
  capability_type                  # DECODER, VALIDATOR, CANONICALIZER,
                                   # or ADAPTER
  capability_coordinate
  implementation_hash
```

The policy cannot declare support absent from the runtime manifest. Additional
inactive capabilities in the manifest are permitted and do not change policy,
command, adaptation, or projection semantics. The canonical digest of the
policy's complete sorted capability bindings is the
`activated_capability_digest`.
Additional inactive capabilities in the runtime manifest are permitted and do
not change policy, command, adaptation, or projection semantics.

```text
RequiredCapabilityBinding
  capability_type                   # DECODER, VALIDATOR, CANONICALIZER,
                                    # or ADAPTER
  capability_coordinate
  implementation_hash
```

The canonical digest of the policy's complete sorted bindings is the
`activated_capability_digest`.

### 6.4 Compatibility preflight

```text
CompatibilityStartupBasis =
    CommittedCompatibilityPolicyBasis
  | SealedBaselineCompatibilityPolicyBasis

CommittedCompatibilityPolicyBasis
  basis_type                        # COMMITTED_POLICY
  policy_ref
  policy_semantic_hash

SealedBaselineCompatibilityPolicyBasis
  basis_type                        # SEALED_BASELINE_POLICY
  baseline_manifest_ref
  intended_policy_ref
  candidate_policy_hash

PersistedContractInventory
  inventory_contract_version        # constant 1
  entries[]                         # PersistedContractInventoryEntry values
  authoritative_inventory_digest

PersistedContractInventoryEntry
  source_contract
  source_canonicalization
  record_count
  ordered_authoritative_refs_digest # binds sorted identity + semantic hash

CompatibilityPreflight
  assess(
    CompatibilityStartupBasis,
    PersistedContractInventory,
    RuntimeContractManifest,
    CompatibilityPolicy
  ) -> CompatibilityPreflightReceipt | CompatibilityPreflightFailure
```

The receipt identifies the exact inventory, manifest, and policy hashes. It is a
runtime admission diagnostic, not J-AR14 or a new persistence mode.
`SEALED_BASELINE_POLICY` is valid only inside runtime-baseline admission. Every
later startup uses one exact committed policy reference and hash; neither form
may select `latest`.

## 7. Compatibility Adapters and Read Views

### 7.1 Adapter coordinate

```text
AdapterCoordinate
  adapter_id
  adapter_contract_version
  source_contract
  source_canonicalization
  target_contract
  target_canonicalization
  implementation_hash

ResolvedAdapterConfigurationSet
  configuration_refs[]             # exact J-AR04 refs, canonical order
  typed_configuration_values[]     # immutable validated logical values
  configuration_set_hash

CompatibilityAdapter
  adapt(
    source_logical_value,
    ResolvedAdapterConfigurationSet
  ) -> target_logical_value | CompatibilityFailure
```

The application boundary resolves every declared configuration ref through the
unit of work, validates availability at semantic as-of time, constructs the
immutable configuration set, and then invokes the adapter. An adapter accepts
only its declared source logical value and that resolved set. It cannot inspect
persistence rows, fetch configuration, or select another adapter dynamically.

### 7.2 Adaptation binding

```text
CompatibilityIntent
  source_authoritative_ref
  expected_source_contract_stamp
  target_contract
  target_canonicalization
  compatibility_policy_ref
  compatibility_policy_hash
  resolution_type                  # EXACT or ADAPTED
  adapter_ref                      # present only for ADAPTED
  adapter_configuration_refs[]
  intent_hash

CompatibilityBinding
  intent                            # complete CompatibilityIntent
  verified_source_authoritative_ref
  verified_source_contract_stamp
  source_body_hash
  verified_configuration_refs[]
  configuration_set_hash
  target_body_hash
  adaptation_hash
```

`intent_hash` binds every preceding intent field. `adaptation_hash` binds the
complete intent plus every verified binding field. For `EXACT`, `adapter_ref` is
absent, both configuration collections are empty, target
contract/canonicalization equal the source, and target body hash equals source
body hash.

### 7.3 Read view

```text
CompatibilityReadView
  binding
  target_logical_body
```

The view is valid only if:

1. the source exact read validates under its original stamp;
2. the policy permits the exact path at semantic as-of time;
3. the direct adapter exists in the runtime manifest and matches its declared
   implementation hash when `resolution_type = ADAPTED`;
4. adapter source and target coordinates equal the binding exactly;
5. every declared adapter configuration resolves exactly, is available at the
   operation's semantic as-of time, and reproduces the immutable configuration
   set hash supplied to the adapter;
6. target bytes validate under the target contract;
7. the target hash and adaptation hash reproduce; and
8. the adapter does not cross a prohibited semantic class.

### 7.4 No domain adapters in the initial policy

The initial Milestone 2 policy uses only `EXACT` paths for C-001 and CT-1.
Artifact N's adapter mechanics are proven using a validation-only value family
that has no J-AR coordinate, G contract, Artifact F discriminator, or persistence
permission.

No actual version-2 domain body exists until a later artifact defines and
ratifies one.

The conformance harness may define a local `CompatibilityProbeCoordinate` and a
two-version strict body solely for adapter and activation tests. That coordinate
is not a `ContractCoordinate`: production registries, policies, serializers,
persistence facets, command slot plans, and G publishers must reject it. A
registry test double may expose the probe as an extra inactive capability to
prove that executable presence does not grant production authority.

## 8. Command and Write-Version Semantics

### 8.1 Command preparation order

Artifact M's command order is extended without changing planner or persistence
ownership:

1. resolve command identity, semantic input, exact compatibility-policy ref,
   full Artifact M output-coordinate union, and complete compatibility intents;
2. bind policy, output selections, and intent hashes into the authority seed;
3. resolve the deterministic time grant and complete Artifact K's input digest;
4. open `CommandUnitOfWork` and resolve prior J-AR14 before semantic reads;
5. load exact authoritative inputs at `semantic_as_of_time`;
6. verify every loaded source equals its declared intent ref, hash, and stamp;
7. resolve exact or approved compatibility read views and bindings;
8. invoke the single pure planner or typed owner operation with those immutable
   verified views;
9. resolve Artifact M output slots from the typed result under the selected
   native output contracts;
10. materialize, validate, arbitrate, and commit through Artifact K.

The committed J-AR14 retains every executed compatibility binding in
`input_derivation_bindings[]`, a provenance collection distinct from
`committed_outputs[]`. A binding describes how an authoritative input was
interpreted; it is not an authoritative output identity and cannot satisfy
Artifact K's output-closure enumeration. A same-command retry returns that
original result before loading or adapting again. An intent is command input; a
verified binding is an execution result and never changes the already-resolved
input digest.

Neither compatibility adaptation nor output-version selection may occur inside
the planner or persistence adapter.

### 8.2 Retry behavior

The same command identity can return its prior J-AR14 only when input contract,
canonicalization, semantic digest, compatibility policy, source bindings, and
active output selections match the original command.

An already committed result is never reinterpreted under another policy. If a
future ratified maintenance contract activates a successor, same-command retry
must still resolve the original result first. Before commit, presenting another
policy changes the input digest and therefore conflicts under the same command
identity.

### 8.3 Native writes only

The selected output serializer receives the typed domain result directly. It
does not receive an older serialized body for upcast-and-save. This preserves
strict target validation and prevents historical migration code from becoming a
write path.

## 9. Canonicalization and Hash Evolution

### 9.1 Original-hash verification

For every persisted record:

```text
original logical body
-> original canonicalizer
-> original canonical bytes
-> original body hash
-> original record-envelope semantic hash
```

Every arrow is reproduced before the record is trusted.

### 9.2 Adapted-view hashing

For an adapted read:

```text
verified original logical body
-> approved direct adapter
-> target logical body
-> target canonicalizer
-> target body hash
-> CompatibilityBinding.adaptation_hash
```

The target hash proves the derived view only. It is not an alternate hash for
the original J-AR record.

### 9.3 Canonicalizer retention

The implementation registry must retain a conforming canonicalizer for every
canonicalization coordinate in the persisted inventory. Replacing the
implementation is permitted only when conformance proves byte-identical output
for the complete supported corpus and the manifest identity treatment remains
honest.

## 10. Projection Rebuild and Query Semantics

### 10.1 Rebuild context

Artifact N adds a compatibility basis to Artifact K's existing rebuild input:

```text
ProjectionCompatibilityContext
  compatibility_policy_ref
  compatibility_policy_hash
  activated_capability_digest
  projection_target_selections[]
  semantic_as_of_time
```

This is a rebuild input, not another persistence mode.

### 10.2 Rebuild algorithm

For one isolated generation:

1. inventory all in-scope authoritative contract stamps;
2. pass compatibility preflight;
3. verify authoritative hashes under original canonicalizers;
4. rebuild in Artifact J dependency order;
5. adapt only the exact read views declared by each target projection;
6. retain original authoritative refs in every derived trace;
7. calculate the source, adapter, and projection digests;
8. run all Artifact J/K/L cross-record bindings; and
9. atomically promote the complete generation.

A failure leaves the prior promoted generation query-visible and unchanged.

### 10.3 Query modes

Queries use one of two explicit modes:

```text
EXACT_ORIGINAL
TYPED_TARGET
```

`EXACT_ORIGINAL` returns the version-complete exact record.
`TYPED_TARGET` requires an exact target coordinate and returns a labelled
compatibility read view. A query cannot silently adapt because the caller omitted
a version.

### 10.4 Cache treatment

An adapted-view cache, if later implemented, is a projection keyed by source
authoritative ref/hash, target coordinate, policy hash, adapter identity/hash,
and
semantic as-of time. It is disposable and cannot satisfy an authoritative read.

## 11. Administrative Modes

### 11.1 Runtime baseline

Baseline admission validates every manifest-declared record under its supplied
stamp and the sealed compatibility policy candidate. It cannot rewrite a
baseline body into the active write version.

The baseline transaction commits only if its active or sealed startup policy
supports the admission operation and the resulting authoritative inventory. A
policy candidate included in that transaction must also pass a non-activating
preflight against the resulting inventory and intended runtime capabilities.

For initial bootstrap, the sealed candidate is the policy used by that bounded
preflight. Runtime-baseline admission is not callable as a live configuration
maintenance path once ordinary authoritative history exists. Milestone 2
therefore neither admits nor activates a successor compatibility policy; that
future capability requires its own typed application and persistence contract.

### 11.2 Pre-scope reporting import

The import preserves the predecessor's reporting core, content schema,
canonicalization, J-AR11 `import_id`, and original publication provenance. It
cannot republish the predecessor merely to place it under the current write
coordinate.

### 11.3 Referenced prior journal

J-010 retains its exact source contract, canonicalization, bytes, source hash,
and non-authored status. G-13 may expose a typed read view only when the policy
declares the path. No adapter may turn J-010 into J-AR08 or Artifact F authorship.

## 12. C-001 Compatibility Proof

C-001 must pass the following sequence:

1. the baseline inventory declares every exact current Artifact F, J-AR, G,
   J-AR02, command, authority, content, and canonicalization coordinate;
2. compatibility preflight proves the runtime manifest and initial policy cover
   that inventory;
3. every canonical input and all eleven accounting events validate under their
   original version-1 contracts;
4. the pre-scope v1 reporting version retains its supplied content schema,
   canonicalization, import identity, and original publication provenance;
5. all G-01 through G-12 and G-14 publications retain G-v0.2/body-v1 stamps;
6. the pure planner and typed owner operations consume `EXACT` read paths only;
7. every new output uses the initial policy's exact current native write
   coordinate;
8. command results bind the compatibility policy and exact source paths;
9. restart under another runtime build with the same activated capabilities
   returns the same J-AR14 results and exact reads;
10. deleting J-P01 through J-P12 and rebuilding under the same target coordinates
    reproduces the existing projection and canonical-compatibility digests; and
11. adding inactive validation-only adapter capability changes neither C-001
    policy, hashes, outputs, nor projection digests.

No domain v2 record is required or permitted in this proof.

## 13. CT-1 Compatibility Proof

CT-1 additionally proves:

- J-010 exact source bytes and source hash remain authoritative for G-13 custody
  under their original supplied coordinate;
- the bind-before-derive reversal check compares against the original J-010
  source hash, never an adapted-view hash;
- reversal and replacement proposals, events, J-011, and J-012 use current native
  write coordinates without rewriting J-010;
- both posting effect keys remain stable across runtime release and compatibility
  preflight;
- the final Aegis issue successor retains exact prior issue and verification
  references even if a future query uses an adapted read view; and
- rebuild reproduces all six accounting events and terminal correction state
  without a migrated authoritative copy.

CT-1 creates no readiness, Pythia, reporting-version, or domain-v2 compatibility
path.

## 14. Failure and Decision Matrix

| Condition | Required outcome |
|---|---|
| Persisted coordinate absent from runtime manifest | Fail compatibility preflight; serve nothing |
| Persisted coordinate absent from governed policy | Fail compatibility preflight |
| Startup policy ref/hash is absent or mismatched | Fail compatibility bootstrap; serve nothing |
| Sealed policy basis is used outside runtime baseline | Reject startup basis |
| Successor policy is submitted through runtime baseline | Reject unsupported operation; create no record |
| Original decoder or canonicalizer unavailable | Fail exact read and preflight |
| Original body fails its declared validator | Corruption/invariant failure |
| Original hash does not reproduce | Corruption/invariant failure |
| Stamp and nested body version disagree | Reject commit or fail rebuild |
| Caller asks for `latest` | Contract failure |
| Target read coordinate omitted | Return exact original only; do not adapt |
| No approved source-to-target path | Typed unsupported-contract outcome |
| Two adapter paths are declared for one source/target | Reject compatibility policy |
| Policy declares a chained or ambiguous adaptation | Reject compatibility policy |
| Adapter changes event/truth class | Reject adapter capability and policy |
| Adapter requires missing evidence or meaning | Mark path unsupported; do not default |
| Adapter output fails target validator | Compatibility invariant failure |
| Adapter is nondeterministic | Compatibility invariant failure |
| Adapter target hash changes after restart | Compatibility invariant failure |
| Active write selection is absent or overlapping | Reject compatibility policy |
| Same command ID resolves another policy or write version | Command-identity conflict |
| Same administrative identity resolves another policy or authored-output version | Mode-specific admission/import conflict |
| New command ID attempts consumed financial effect | Existing J-AR15 rejection path |
| Rebuild encounters unsupported persisted coordinate | Fail isolated generation; preserve promoted one |
| Projection target changes | Build a separate labelled generation; no cross-version byte-equality claim |
| Baseline candidate would create unsupported inventory | Reject baseline atomically |
| Import changes coordinate under same `import_id` | Pre-scope import conflict |
| Referenced journal changes source contract/hash | Referenced-journal admission conflict |
| External candidate contract unsupported | Hermes G-02 `UNSUPPORTED`; no G-01 |
| Declaration-only evidence passes an adapter | Remains declaration-only |

## 15. Conformance Catalog

Artifact N's eventual implementation must make the following tests executable.

| ID | Required proof |
|---|---|
| N-T01 | Every J-AR01 through J-AR17 exact read returns a strict persisted contract stamp. |
| N-T02 | Stamp/body version or canonicalization mismatch is rejected. |
| N-T03 | Authoritative bytes and hashes remain unchanged after runtime restart and projection rebuild. |
| N-T04 | Startup preflight rejects one unsupported persisted contract coordinate. |
| N-T05 | Startup preflight rejects one unavailable original canonicalizer. |
| N-T06 | Preflight receipt binds exact inventory, manifest, and policy hashes. |
| N-T07 | Exact historical read returns original bytes and no adapter binding. |
| N-T08 | Typed target read requires an explicit target coordinate. |
| N-T09 | An approved deterministic adapter returns a labelled non-authoritative read view. |
| N-T10 | The read view retains the original authoritative ref and source hash. |
| N-T11 | An adapted view cannot satisfy an AuthoritativeRef or state expectation. |
| N-T12 | Unknown source fields fail source validation before adapter execution. |
| N-T13 | Missing target meaning causes unsupported path rather than a default. |
| N-T14 | Adapter attempts to cross business/accounting event classes are rejected. |
| N-T15 | Adapter attempts to upgrade evidence verification are rejected. |
| N-T16 | Two eligible adapters, a chained transform, or an ambiguous source/target selection rejects policy. |
| N-T17 | Same adapter input and policy produce byte-identical target and adaptation hashes across restart. |
| N-T18 | No domain planner, typed owner operation, or persistence adapter can resolve an adapter registry directly. |
| N-T19 | Runtime capability absent from policy is inactive. |
| N-T20 | Policy capability absent from runtime manifest fails preflight. |
| N-T21 | Each runtime-authored output contract in all six Artifact K modes has exactly one active native write selection; supplied historical records are excluded. |
| N-T22 | A native write serializes the typed result directly and never upcasts persisted source bytes. |
| N-T23 | Same command identity with another compatibility policy conflicts. |
| N-T24 | Same command identity with another active output coordinate conflicts. |
| N-T25 | Same committed command retry resolves original J-AR14 from its stored policy binding before any current-policy interpretation; presenting another policy to an uncommitted retry is the N-T23 identity conflict. |
| N-T26 | Command input digest binds the complete compatibility intent before UOW open; the verified post-load binding is retained in J-AR14 `input_derivation_bindings[]` without recomputing that digest. |
| N-T27 | State tokens and effect keys are unchanged by adapted query/read treatment. |
| N-T28 | Original body hash verifies only under its recorded canonicalization version. |
| N-T29 | Target view hash never replaces the source AuthoritativeRef semantic hash. |
| N-T30 | Rebuild verifies mixed source coordinates before projection work begins. |
| N-T31 | Rebuild emits no authoritative record, event, publication, effect, or command result. |
| N-T32 | Failed compatibility rebuild leaves the prior promoted generation unchanged. |
| N-T33 | Projection digest comparison requires identical target, policy, activated-capability digest, as-of, and source inventory. |
| N-T34 | Runtime baseline rejects a candidate inventory unsupported by its sealed policy/manifest. |
| N-T35 | Pre-scope import preserves exact content schema, canonicalization, `import_id`, and provenance. |
| N-T36 | Referenced-journal admission preserves exact J-010 source coordinate and non-authored status. |
| N-T37 | Unsupported external candidate produces G-02 `UNSUPPORTED` and no G-01. |
| N-T38 | Canonical C-001 remains exact-path only and reproduces all eleven events and terminal digests. |
| N-T39 | Canonical CT-1 remains exact-path only and reproduces all six events, effects, and terminal digests. |
| N-T40 | A second runtime build with the same semantic capabilities reads and rebuilds C-001/CT-1 identically. |
| N-T41 | Adding inactive validation-only adapter capability changes no canonical domain output or digest. |
| N-T42 | A validation-only two-version value proves forward adaptation without becoming J-AR, G, Artifact F, or module-product state. |
| N-T43 | No registry or policy row uses implicit `latest`, version-string parsing, or physical schema identity. |
| N-T44 | The harness-local probe policy retains its v1 read path after selecting probe v2 for writes, while the production policy parser continues to reject probe coordinates. |
| N-T45 | Declaration-only evidence remains declaration-only through exact read, adapted read, command binding, and rebuild. |
| N-T46 | Committed startup resolves one exact policy ref/hash before ordinary reads and never selects `latest`. |
| N-T47 | Sealed compatibility-policy bootstrap is accepted only inside atomic runtime-baseline admission; mismatch or reuse elsewhere fails before semantic service. |
| N-T48 | The application resolves every adapter configuration as an exact available J-AR04 ref, supplies one immutable validated `ResolvedAdapterConfigurationSet`, and binds its refs and hash into policy, adaptation hash, and command input digest; adapter fetches and undeclared access fail. |
| N-T49 | Persisted inventory digest changes when any authoritative identity or semantic hash changes, even when coordinate counts remain equal. |
| N-T50 | Runtime-baseline admission accepts the sealed initial compatibility policy only; a successor-policy attempt through that port is rejected without creating a record or changing active policy. |
| N-T51 | Baseline, import, and referenced-journal retries bind their original policy and authored-output selections; a changed selection produces the existing mode-specific conflict. |
| N-T52 | Command authority seed and input digest bind the complete slot-plan output-coordinate union before planning; accepted, rejected, and conflict outcomes select subsets without recomputing the digest. |
| N-T53 | Matching J-AR14 retry returns before exact body load or adapter execution; instrumented compatibility readers and adapters receive zero calls. |
| N-T54 | Every executed compatibility binding appears only in J-AR14 `input_derivation_bindings[]`; none appears in `committed_outputs[]`, and Artifact K output closure still enumerates only records created by the command. |

## 16. Acceptance Criteria

Artifact N may be ratified only when:

- N-A01: authoritative records remain byte-immutable across runtime and contract
  evolution;
- N-A02: every J-AR record has a complete strict persisted contract stamp;
- N-A03: contract coordinate variants remain typed and non-interchangeable;
- N-A04: all persisted coordinates must pass compatibility preflight before
  semantic service begins;
- N-A05: exact read always preserves original bytes, versions, and hashes;
- N-A06: adapted reads are explicitly targeted, labelled, derived, and
  non-authoritative;
- N-A07: no semantic path selects `latest` or infers a version from identity;
- N-A08: compatibility cannot cross event streams, truth layers, governance
  states, authorship, or evidence-verification boundaries;
- N-A09: adapters are pure, deterministic, strict, and registry bounded;
- N-A10: missing semantic meaning blocks adaptation rather than creating a
  default;
- N-A11: downcast and lossy adaptation are outside Milestone 2;
- N-A12: each adaptation is exact or one unique direct edge;
- N-A13: compatibility activation is exact governed J-AR04 configuration;
- N-A14: runtime capability cannot self-authorize use;
- N-A15: every runtime-authored output family across all six Artifact K modes
  has one active native write coordinate while supplied history remains exempt;
- N-A16: output-version selection is bound to semantic time and command digest;
- N-A17: adapted inputs retain original upstream authoritative references;
- N-A18: state tokens, causality, concurrency, and effect keys do not migrate;
- N-A19: original and adapted hashes remain distinct and reproducible;
- N-A20: canonicalization evolution never rehashes historical authority;
- N-A21: every projection generation declares its compatibility basis;
- N-A22: rebuild is mixed-version aware, isolated, deterministic, and write
  silent;
- N-A23: cross-version projections are never claimed byte-equal without an
  identical compatibility basis;
- N-A24: unsupported external input, unsupported persisted input, and corrupted
  history remain distinct outcomes;
- N-A25: baseline, import, and referenced-journal modes preserve supplied
  historical coordinates;
- N-A26: support for persisted historical coordinates is monotonic;
- N-A27: every new semantic version or adapter remains an architecture change;
- N-A28: the current production registry adds no speculative domain successor;
- N-A29: compatibility policy and runtime implementation manifest have separate
  identities and hashes;
- N-A30: command preparation performs compatibility work outside the planner and
  adapter commit logic;
- N-A31: current C-001 uses exact paths only and reproduces all existing
  authoritative and projection proofs;
- N-A32: current CT-1 uses exact paths only and preserves J-010 authorship,
  reversal binding, effects, and terminal state;
- N-A33: the complete N-T01 through N-T54 catalog is implementable without a
  physical database or migration tool;
- N-A34: Artifact F payloads, G contracts, J-AR families, Artifact L bodies,
  Artifact K modes, and Artifact M authority semantics remain unchanged;
- N-A35: the validation-only successor family has no production persistence or
  publication permission; and
- N-A36: no physical schema, deployment, API, transport, or retention decision is
  smuggled into semantic compatibility;
- N-A37: policy bootstrap uses one exact committed reference or one bounded
  sealed baseline candidate without circular self-authorization; and
- N-A38: direct adapters preserve semantic family, owner, contract ID, and
  discriminator boundaries; and
- N-A39: adapter configuration is exact, governed, availability-gated, and
  reproducibly bound rather than fetched implicitly; and
- N-A40: persisted inventory binds every authoritative identity and semantic hash,
  not merely version counts; and
- N-A41: runtime-baseline admission is initial-bootstrap only; Milestone 2 has no
  live successor-policy admission or activation path, and a future path requires
  an explicit contract and ADR; and
- N-A42: every administrative retry binds its original compatibility policy and
  authored-output coordinate selections; and
- N-A43: command output-version binding uses the complete Artifact M slot-plan
  union before planning and never an outcome-dependent digest; and
- N-A44: prior-result resolution remains ahead of exact content loading and all
  compatibility adaptation; and
- N-A45: J-AR14 retains compatibility bindings as input-derivation provenance
  without adding them to Artifact K's authoritative output closure.

## 17. Decisions Resolved and Deferred

### 17.1 Resolved by Artifact N

- immutable original-byte retention across semantic contract evolution;
- explicit typed contract coordinates and canonicalization coordinates;
- version-complete exact reads;
- startup compatibility preflight;
- governed native write-version selection;
- deterministic labelled read adaptation;
- original-reference preservation through adapted command inputs;
- canonical hash treatment across versions;
- mixed-version projection rebuild semantics;
- administrative-mode compatibility;
- outer-stamp bootstrap decoding with strict nested-version equality;
- global fail-fast startup semantics for unsupported persisted history;
- application-resolved immutable adapter configuration;
- J-AR14 input-derivation provenance outside authoritative output closure;
- initial-bootstrap-only compatibility-policy admission; and
- honest C-001/CT-1 compatibility without inventing domain v2.

### 17.2 Deferred beyond Artifact N

1. the first real successor domain contract and its fields;
2. successor compatibility-policy admission, activation, and maintenance;
3. physical database engine, schema, indexes, and migration scripts;
4. deployment ordering, rolling upgrades, and multi-process coordination;
5. evidence-byte storage beyond the bounded reporting proof;
6. projection checkpoint representation and operational rebuild tooling;
7. Milestone 2 assertion-report schema;
8. runtime package layout and implementation libraries;
9. public API, transport, authentication, UI, and deployment; and
10. archival, retention, legal hold, backup, and disaster recovery policy.

## 18. Ratification Review and Next Move

The v0.2 tightening pass closes the outer-stamp bootstrap question, selects
global fail-fast startup for Milestone 2, separates J-AR14 compatibility
provenance from output closure, removes unsupported live reuse of the baseline
port, and defines the adapter configuration data path.

Ratification confirms that direct adapters are the conservative Milestone 2
boundary; J-AR15 identity, state tokens, and original references remain stable;
the validation-only successor family proves the mechanism without inventing a
domain v2; and no rule requires a relational schema or deployment topology.

Run a full Milestone 2 Phase 0 cohesion audit across Artifacts I through N. Only
that audit should decide whether the design is closed enough to select the first
reversible runtime package layout and physical persistence implementation.
