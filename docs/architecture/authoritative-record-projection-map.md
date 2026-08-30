# Artifact J - Authoritative Records and Rebuildable Projections

Status: Design v0.2 - ratified 2026-08-03

## 0. Purpose and Boundary

Artifact J defines which Milestone 2 records are authoritative, which records
are immutable owned values, which views are rebuildable projections, and which
exact inputs reproduce every state exposed by Artifact I.

It resolves the two persistence-boundary blockers carried by Artifact I:

1. how one frozen proposal treatment can pass through lifecycle states without
   changing bytes under the same fully qualified proposal reference; and
2. how the predecessor reporting version can exist with honest publication
   provenance without adding an accounting event to the C-001 trace.

Artifact J maps the write sets of I-S01 through I-S26. It does not define:

- physical tables, columns, indexes, or foreign keys;
- a database product;
- repository or unit-of-work interfaces;
- public API payloads;
- new Artifact F object or accounting-event contracts;
- the full internal bodies of G-01 through G-14;
- a generic event-sourcing framework; or
- retention, archival, tenancy, or production evidence storage.

The record names in this artifact are semantic roles. They do not imply one
table per role or one generic table for unrelated module products.

## 1. Binding Sources

Artifact J is subordinate to:

- the five invariants and architecture rules in `AGENTS.md`;
- Artifact C - Accounting Object Model;
- Artifact E v0.2.1 - Accounting State Machines and Command/Event Matrix;
- Artifact F v0.2.1 - Minimum Payload Contracts;
- Artifact G v0.2 - Module Ownership and Contract Map;
- Artifact H v0.3.1 - Executable Validation Harness Specification;
- Artifact I v0.2 - Runtime Application Boundary;
- canonical transactions C-001 and CT-1;
- ADR-003 through ADR-018; and
- the Milestone 2 Persistent Runtime Vertical Slice draft.

Artifact F remains authoritative for its closed external payload boundary.
Artifact J defines internal persistence semantics needed to reproduce that
boundary; it does not add fields to Artifact F payloads.

Canonical identities and dates are proof examples only. Record selection,
availability, rebuild, and concurrency logic operate on supplied exact
identities and times and must not branch on C-001, CT-1, P-551, RC-001, J-010,
or the canonical period pair.

## 2. Proposed Rulings

### J-R01 - Authoritative records are immutable

An authoritative record is appended once under a permanent identity. The same
identity cannot later resolve to different semantic bytes.

Corrections create another record, version, event, or governed relationship.
They never update historical authoritative content in place.

### J-R02 - Projections are disposable

A lifecycle state, current-state index, exact object view, trace graph, or
availability index is a projection when its complete content can be rebuilt
from declared authoritative records.

Deleting a projection cannot delete evidence, command outcomes, financial
effects, contract publications, or the records needed to rebuild it.

### J-R03 - Record roles do not expand the nine-object model

One Artifact C accounting object may require several persistence roles. For
example, `journal_proposal` uses an immutable treatment record, immutable
accounting events, and a rebuildable lifecycle projection.

Those roles are representations of one accounting object and its history. They
are not additional accounting object classes.

### J-R04 - Proposal treatment and lifecycle are separate

Each fully qualified `proposal_ref` identifies exactly one immutable treatment
version: origin, derivation basis, target period, date, currency, ordered lines,
totals, preparer, creation time, and treatment evidence.

Lifecycle status is not stored by rewriting that treatment. It is derived from
the treatment's creation command and the ordered accounting events whose
subject is that exact `proposal_ref`.

### J-R05 - Exact proposal state is pinned by a state token

An exact proposal view is identified internally by:

```text
proposal_ref + proposal_state_token
```

For `DRAFT`, the state token is the accepted construction command-result
identity. For every event-backed state, it is the latest accounting-event
identity included in the view.

The token is contract-publication metadata and a query parameter. It is not a
new Artifact F field or a new accounting object identity.

### J-R06 - Artifact F proposal payloads are exact derived views

The Artifact F `journal_proposal` payload is assembled from:

```text
immutable proposal treatment
+ first proposal.submitted event
+ lifecycle state as of an explicit state token
= exact Artifact F proposal view
```

`submitted_at` comes from the first accepted `proposal.submitted` event.
`status` comes from the state reached at the requested token. All treatment
fields come from the immutable treatment record.

Artifact F does not serialize `DRAFT`. Canonical terminal payloads remain
byte-identical. Submitted, approved, deferred, and posted views can be rebuilt
without overwriting the treatment.

### J-R07 - Predecessor v1 is an evidenced pre-scope import

The predecessor reporting version is admitted through a bounded pre-scope
import bundle. The bundle contains:

- the immutable predecessor reporting core;
- the committed canonical reporting-content bytes and hash;
- original publication time and authority provenance;
- import identity, source, time, and evidence; and
- an explicit semantic availability time.

The import attests that publication occurred outside the bounded C-001
accounting-event trace. It does not claim the Milestone 2 run published v1.

### J-R08 - Pre-scope import is not an accounting event

Admitting the predecessor does not append `reporting_version.published`, consume
a publication effect key, or increase the eleven-event C-001 sequence.

The import receipt is authoritative infrastructure provenance. The imported
reporting version remains Atlas-owned accounting truth after admission, but its
origin remains visibly `PRE_SCOPE_IMPORT`.

### J-R09 - Import candidates are not authoritative imported state

A sealed, parameterised import candidate may be supplied before the historical
scenario is replayed. Before admission it is external bootstrap input, not
J-AR10, J-AR11, J-AR12, J-AR13, G-06, or an application-readable projection.

After the exact I-S06 hard-close exists and the attested original publication
time has passed, the bounded import subsystem validates and atomically appends
the imported reporting core, attestation, verified proof content, and imported
G-06 publication through the same authoritative persistence boundary.

Every application query, domain-state load, planner input, projection, trace,
and G-contract read must additionally enforce `available_from`.

For C-001:

```text
June hard-close time
< predecessor original publication time
<= attested import time
<= semantic availability time
<= first G-06 consumer time
```

Before import commit, only the bounded bootstrap/import subsystem may inspect
the external candidate for integrity. No command, planner, owner query,
consumer, projection, or trace path may observe or infer v1. After commit but
before a later `available_from`, those same paths still treat it as unavailable.

### J-R10 - Imported publication is idempotent and content-bound

The logical import effect is unique on:

```text
object type + reporting_version_ref + content_hash
```

Repeating the same import returns the original receipt. Reusing the reporting
version reference with different content, provenance, or publication time is an
identity conflict and is rejected.

### J-R11 - Stateful accounting views rebuild from events and owned values

- proposal state rebuilds from proposal treatment plus proposal events;
- period state rebuilds from immutable period base facts plus period events;
- restatement-case state rebuilds from restatement events, exact linked
  journals, and the immutable owned manifest value; and
- reporting history rebuilds from immutable reporting-version records and
  their publication origins.

An Artifact F state snapshot may be cached or published by hash, but it is not a
second source of lifecycle truth.

### J-R12 - G publications are authoritative handoff records

When an Artifact I command publishes a G contract required by a later command,
the publisher atomically appends an immutable contract-publication record with
the exact product reference, state token where applicable, canonical payload
bytes or an immutable payload-content reference, payload hash, contract and
canonicalization versions, publisher, purpose or scope, upstream references,
evidence, availability time, and publishing command identity. A pre-scope
imported G-06 publication binds the import attestation instead of inventing a
publishing command.

An observer trace is not this record and cannot substitute for it.

### J-R13 - Consumption is proved by the consumer outcome

A successful consumer command persists the exact upstream publication
references in its own authoritative outcome and command result. A separate
semantic consumption-acknowledgement record is not required in Milestone 2.

The approved-decision return is not a numbered G contract. Its authoritative
handoff consists of exact source-domain J-AR02 approval and candidate versions.
I-S26 pins those identities and content hashes directly; no synthetic J-AR13
publication is created for symmetry.

Boundary observations may record the same call for H6 and M2 trace assertions,
but remain removable diagnostic evidence rather than domain truth.

### J-R14 - Command results and effect claims are authoritative coordination

Command results, G-14 dispositions, and posting or publication effect claims are
immutable authoritative coordination records. They are not accounting objects,
but deleting them would weaken retry, rejection, or financial-effect guarantees;
therefore they are not projections.

### J-R15 - Optimistic concurrency uses authoritative change tokens

A state-changing command supplies the exact state token it planned against.
Commit succeeds only when that token is still current within the same local
transaction.

For event-backed accounting lifecycles the token is the last accepted event ID;
for an eventless draft it is the construction command-result ID; for a declared
base state with no in-scope event it is the base-record identity plus canonical
base-record hash; and for immutable module products it is the exact
product-version reference.

### J-R16 - The platform remains hybrid, not fully event sourced

Accounting events are sufficient to rebuild lifecycle transitions, but not all
authoritative content. Proposal treatments, posted journal lines, manifest
bodies, reporting content, module-owned outputs, import attestations, command
results, and effect claims remain independent immutable records.

The platform must not claim that replaying accounting events alone rebuilds the
runtime.

### J-R17 - Semantic digests ignore physical storage choices

Clean-start, restart, and rebuild comparison uses canonical semantic records,
relationships, exact state views, and availability. It excludes generated row
keys, page layout, insertion order between independent streams, adapter metadata,
and projection checkpoint locations.

All projection comparisons use the same injected semantic `as_of_time`.
Wall-clock time at test execution or process restart is never part of equality.

### J-R18 - Candidate content remains replayable

A candidate receipt retains the exact contract and canonicalization versions,
canonical candidate bytes or an immutable content reference resolving those
bytes, and the matching payload hash. A hash without resolvable bytes is not a
replayable receipt.

An approved source-domain candidate may reuse its exact J-AR02 content reference
when I-S26 creates J-AR01. The receipt does not duplicate bytes merely to prove
custody, but the referenced content must remain authoritative and available.

### J-R19 - Pre-scope import is one bounded administrative operation

The import seam is a single typed pre-scope reporting-version admission
operation within the shared in-process application boundary. It is not an
Artifact I domain command, a second application boundary, or a general import
framework.

It accepts only the declared predecessor import candidate, uses J-AR11 import
identity for retry and conflict handling, commits J-AR10/J-AR11/J-AR12/J-AR13
atomically, and returns the immutable import receipt. It cannot admit business
events, emit accounting events, consume an ordinary publication effect key, or
create a non-imported reporting version.

## 3. Record Vocabulary

| Term | Meaning | Deletable and rebuildable? |
|---|---|---:|
| Authoritative domain record | Immutable owned fact or outcome whose loss changes domain truth. | No |
| Authoritative coordination record | Immutable command, effect, import, or contract record required to prove execution. | No |
| Owned value record | Immutable content nested semantically within an owning object, such as a restatement manifest. | No |
| Accounting event | Immutable Atlas lifecycle action in the closed Artifact F stream. | No |
| Exact derived view | Canonical object payload rebuilt as of an explicit authoritative token. | Yes |
| Current projection | Latest operational view rebuilt from authoritative inputs. | Yes |
| Referenced-state projection | Content-addressed read view such as G-13 that does not acquire object authorship. | Yes, if its declared source remains available |
| Boundary observation | Diagnostic record of an actual publish or consume call. | Yes |
| Evidence body | Immutable bytes where content verification is claimed. | No |
| Declared evidence reference | Immutable identity and declared hash where no body is committed. | No |

Rebuildable does not mean unimportant. Exact views and projections may be
persisted for performance, but correctness cannot depend on their survival.

## 4. Authoritative Record Families

The following are logical record families, not proposed tables.

| Code | Record family | Owner | Authoritative content |
|---|---|---|---|
| J-AR01 | Candidate receipt | Shared substrate | Candidate identity; contract and canonicalization versions; canonical bytes or immutable content reference; matching payload hash; source; receipt time; approval; and upstream references. |
| J-AR02 | Module-owned product version | Declared module or source domain | Admission, reconciliation, test, exception, review, finding, issue, directive, readiness, verification, planning snapshot, decision, approval, or source-candidate content under an exact version. |
| J-AR03 | Admitted business event | Source domain through shared substrate | Exact authored business-event payload admitted under G-01. |
| J-AR04 | Configuration version | Owning domain | Posting rule, policy, contract registry, assumption, and other exact governed configuration used by a command. |
| J-AR05 | Proposal treatment version | Atlas | Immutable treatment fields for one fully qualified `proposal_ref`; no mutable lifecycle status. |
| J-AR06 | Accounting event | Atlas | Exact Artifact F event bytes and causal identity. |
| J-AR07 | Accounting-period base facts | Atlas | Period identity, dates, currency, declared initial state, and evidence needed before in-scope transitions. |
| J-AR08 | Posted journal and lines | Atlas | Immutable header and ordered line records created by `journal.posted`. |
| J-AR09 | Restatement manifest value | Atlas within `restatement_case` | Ordered reconciled presentation entries and canonical manifest hash. |
| J-AR10 | Reporting-version core | Atlas | Exact period/version identity, content identity, publication time, publication origin, predecessor and restatement basis where applicable. |
| J-AR11 | Pre-scope import attestation | Atlas import boundary | Imported object identity, source hash, provenance, exact prerequisite hard-close state, original publication basis, import basis, and semantic availability. |
| J-AR12 | Evidence or bounded proof content | Evidence/content boundary or owning module | Immutable evidence or reporting-proof bytes and verified hash, or an explicit declaration-only evidence reference. |
| J-AR13 | G contract publication | Contract publisher | Exact durable product handoff, canonical payload bytes or immutable content reference and hash, versioned canonicalization, availability metadata, and publishing command or pre-scope import basis. |
| J-AR14 | Command result | Target command owner | Accepted, rejected, blocked, or prior-result outcome plus exact input and committed-output identities and hashes. |
| J-AR15 | Effect claim | Effect owner | Uniqueness claim and produced financial or reporting effect for posting and publication. |
| J-AR16 | G-14 disposition | Rejected command target | Subject-free pre-construction rejection, request, authority, reason, and evidence. |
| J-AR17 | Referenced-state source | Atlas read boundary without Artifact F authorship | Immutable content, source hash, source identity, and provenance required to rebuild a G-13 view such as J-010. |

J-AR02 is a classification, not permission to persist unrelated module products
through an untyped generic body. Each version must retain its object or product
type, exact version identity, owner, contract discriminator, canonical body and
hash, upstream references, evidence references, and creation basis. Each module
retains its own semantic contract and owner.

For J-AR17, Atlas owns custody, integrity checking, and G-13 exposure. It does
not claim authorship of the historical journal or convert the source into an
Artifact F accounting object.

## 5. Resolution of Proposal Identity and Lifecycle

### 5.1 Immutable treatment content

J-AR05 contains the Artifact F proposal fields except `status` and
`submitted_at`:

- contract, family, version, and fully qualified proposal identity;
- origin type and origin basis;
- target period and effective date;
- ledger currency;
- ordered proposed lines and balanced totals;
- preparer and creation time; and
- treatment evidence references.

The record also retains its construction command-result reference and canonical
treatment hash as internal persistence metadata.

I-S03 and I-S13 create J-AR05 in an eventless `DRAFT` state. Their accepted
J-AR14 command result binds the proposal reference and treatment hash. Once
accepted, the treatment bytes never change. Submission confirms the same hash
as governance-frozen; it does not store the treatment a second time. A
regenerated persisted draft must receive a new proposal version; Milestone 2
does not implement draft regeneration.

### 5.2 Lifecycle derivation

The proposal projection starts at `DRAFT` from J-AR05 and its accepted
construction command. Artifact E transitions are then folded in causal order:

| Event | Required prior state | Resulting state |
|---|---|---|
| `proposal.submitted` | `DRAFT` | `SUBMITTED` |
| `proposal.approved` | `SUBMITTED` | `APPROVED` |
| `proposal.deferred` | `SUBMITTED` | `DEFERRED` |
| `journal.posted` | `APPROVED` | `POSTED` |

Other Artifact E proposal events remain deferred unless their payload contract
is later ratified. They are not invented by Artifact J.

The fold rejects:

- an event for an unknown treatment;
- a state transition whose `from_status` differs from the prior projection;
- a second terminal transition;
- an event whose subject and payload proposal references disagree; or
- a causal order that skips the required predecessor.

### 5.3 Exact views and references

`GetJournalProposal` must accept either:

- an exact `proposal_ref` plus `proposal_state_token`; or
- a request for the labelled current projection for local operational use.

Cross-module commands and G-04 publications must use the first form. They may
not use an implicit current state.

For P-551@v1, the following remain independently reproducible:

```text
P-551@v1 + AE-C001-001 -> status SUBMITTED
P-551@v1 + AE-C001-002 -> status DEFERRED
```

The exact submitted view does not become false when the later deferred view is
published.

### 5.4 Artifact F compatibility

The Artifact F serializer receives an exact derived view, never an unpinned
current projection. It adds:

- `status` from the requested lifecycle token; and
- `submitted_at` from the first submission event.

It then applies the existing closed contract and canonical serializer. No field
is added, defaulted, or renamed.

The expected terminal views remain:

- P-551@v1 at AE-C001-002 -> canonical `DEFERRED` fixture bytes;
- P-551@v2 at AE-C001-007 -> canonical `POSTED` fixture bytes;
- P-REV-010@v1 at its posting event -> canonical `POSTED` fixture bytes; and
- P-REP-010@v1 at its posting event -> canonical `POSTED` fixture bytes.

## 6. Resolution of the Predecessor Reporting Version

### 6.1 Reporting-version core

J-AR10 uses one internal core with a discriminated publication origin.

Common semantic content is:

- reporting version identity, family, period, and version;
- content reference, hash, and schema version;
- original publication time;
- evidence references; and
- publication origin.

`RESTATEMENT_PUBLICATION` additionally binds:

- predecessor reporting-version reference;
- restatement-case identity;
- manifest hash;
- `reporting_version.published` event identity; and
- publication effect claim.

`PRE_SCOPE_IMPORT` instead binds:

- pre-scope import attestation identity;
- original publication authority and evidence;
- source system or archive identity; and
- semantic availability time.

Artifact F v0.2.1 serializes only the exercised restatement-successor variant.
The imported predecessor is an internal Artifact C reporting version and G-06
product; Artifact J does not claim that Artifact F can emit a v1 object payload.

### 6.2 Import attestation

J-AR11 must contain at least:

```text
import_id
imported_object_type = reporting_version
reporting_version_ref
canonical_core_hash
content_ref
content_hash
content_schema_version
prerequisite_period_id
prerequisite_close_event_id
prerequisite_close_view_hash
original_published_at
available_from
original_authority_ref
source_ref
imported_at
imported_by
import_command_or_manifest_ref
evidence_refs
```

This is a minimum semantic body, not a public payload or physical schema.
`imported_at` must not precede `original_published_at`, and `available_from`
must not precede the import, original publication, or represented hard close.
The prerequisite period, event, and view hash must resolve to one exact
`HARD_CLOSED` Atlas state for the imported reporting period.

The canonical predecessor content body already committed under ADR-016 is the
verified content for the C-001 import. Other declared evidence remains subject
to the declared-versus-verified boundary.

Artifact J therefore claims cryptographic verification of the imported
reporting content, not of every approval or provenance evidence body. Any
publication-basis reference without committed bytes remains explicitly
declaration-only.

The imported G-06 record is published by the Atlas import boundary with
`publication_origin = PRE_SCOPE_IMPORT`. J-AR11 separately preserves the
original external publication authority, so import ownership does not rewrite
historical provenance.

### 6.3 Temporal seam in C-001

The sealed import candidate is a parameterised scenario input, but no imported
authoritative record or G-06 exists at scenario start. The bounded import
transaction runs only after the June hard-close and original publication time.

This refines Artifact I section 3.3's phrase "declared bootstrap state": the
declared precondition is the sealed predecessor candidate, proof content, and
provenance needed for later admission, not an already consumable J-AR10 or G-06.
I-S06 preserves that candidate without claiming Atlas has imported it.

The seam occurs between I-S06 and the first step that requires predecessor
G-06. It is not an Artifact I application command and does not author a domain
transition. It is one local bootstrap/import transaction through the same
persistence boundary, producing ordinary immutable imported state for read-only
consumption.

The runtime proof must show:

1. before import commit, J-AR10, J-AR11, J-AR12, J-AR13, G-06, and every derived
   predecessor projection are absent;
2. the attestation's exact hard-close event and view hash resolve and precede
   `original_published_at`;
3. the import transaction atomically binds the reporting core, attestation,
   verified v1 content, and imported G-06 publication;
4. every application, planner, query, projection, and trace path keeps G-06
   unavailable until `available_from`;
5. I-S08 and I-S10 consume that exact predecessor publication;
6. I-S20 publishes v2 through the ordinary event and effect path;
7. v2 names the exact imported v1 predecessor; and
8. v1 remains byte-unchanged and independently retrievable.

### 6.4 Import replay and conflict rules

An identical import retry returns the original J-AR11 receipt and does not
create another reporting version or G-06 publication.

The import is rejected if:

- the reporting-version reference already has a different core or content hash;
- the content hash does not match committed bytes where verification is claimed;
- original publication time is not supported by evidence;
- the prerequisite period, hard-close event, or exact view hash does not
  resolve to the imported reporting period's `HARD_CLOSED` state;
- `available_from` precedes original publication or attested import time;
- canonical C-001 availability does not follow the hard close; or
- the same import identity is reused with different semantic content.

## 7. Rebuildable Projection Catalog

| Code | Projection | Rebuild sources | Exactness token |
|---|---|---|---|
| J-P01 | Candidate disposition | Replayable J-AR01 content plus exact admission product versions | Candidate receipt and admission version refs |
| J-P02 | Proposal current lifecycle | J-AR05 plus ordered J-AR06 proposal events | Construction command result or last event ID |
| J-P03 | Proposal Artifact F as-of view | J-AR05 plus first submission event plus events through requested token | Proposal state token |
| J-P04 | Accounting-period current state | J-AR07 plus ordered J-AR06 period events | J-AR07 identity plus base hash, then last period event ID |
| J-P05 | Accounting-period Artifact F as-of view | J-AR07 plus period events through requested token | Base-state token or period event ID |
| J-P06 | Restatement-case current state | Restatement J-AR06 events, linked J-AR08 journals, and J-AR09 manifest | Last case event ID |
| J-P07 | Restatement-case Artifact F as-of view | Same inputs through requested token | Case event ID |
| J-P08 | Reporting history by period | J-AR10 plus J-AR11 where imported | Exact reporting-version refs |
| J-P09 | Contract availability | J-AR13 and import availability | Publication ID and availability time |
| J-P10 | Current module-product index | Versioned J-AR02 records | Exact product-version ref |
| J-P11 | End-to-end trace graph | J-AR01 through J-AR17 exact references | Source record and target product refs |
| J-P12 | G-13 referenced journal view | Immutable J-AR17 source plus J-AR13 | Source hash |
| J-P13 | Boundary observation trace | Actual publish/consume calls and command inputs | Observation sequence; non-semantic |

J-P13 can be deleted without changing any command result. J-P11 can be rebuilt
even if J-P13 is absent.

## 8. Logical Uniqueness and Concurrency Constraints

These constraints must survive any later database choice.

| Constraint | Required semantic rule |
|---|---|
| Immutable identity | One record kind and permanent identity resolve to one canonical semantic hash. |
| Candidate identity | Same source domain and candidate identity with the same contract, canonical bytes, and payload hash is a retry; different content is a conflict; missing resolvable bytes is invalid. |
| Business-event identity | One admitted event identity resolves to one Artifact F payload hash. |
| Proposal treatment | `proposal_ref` is unique; family/version is unique; treatment hash cannot change. |
| Proposal state | Commit compares the expected proposal state token with the current token. |
| Accounting event | `event_id` is globally unique; `command_id` is unique for one logical transition within its owner. |
| Causal event order | A correlation stream cannot append an event whose declared causal predecessor is absent or not current where immediate causation is required. |
| Period state | An eventless base token is J-AR07 identity plus canonical hash; later commits compare the last period event ID; hard close cannot be overwritten. |
| Journal posting | One proposal version cannot produce two posting effects; effect key is independently unique. |
| Journal identity | Journal header identity is unique; ordered line identities and line numbers are unique within it. |
| Restatement manifest | One frozen manifest hash binds one ordered body for the case version; later mutation is rejected. |
| Reporting version | Reporting-version ref is unique and immutable; predecessor must exist and be available. |
| Publication effect | Publication idempotency key is independently unique for the target reporting version. |
| Pre-scope import | Imported object ref plus content hash is idempotent; conflicting content or provenance is rejected. |
| G publication | Contract ID, version, publisher, product ref, and product state token identify one immutable handoff. |
| Command result | Owner plus command ID identifies one immutable result; mismatched retry input is rejected. |
| G-14 disposition | One rejected pre-construction command has at most one immutable disposition. |
| Projection checkpoint | A checkpoint is replaceable and must name the last authoritative token included. |

### 8.1 Required cross-record bindings

Uniqueness alone cannot prove that records committed together describe the same
outcome. Every accepted write set validates the following bindings before
commit, and rebuild validates them again.

| Binding | Required equality and relationship |
|---|---|
| Candidate admission | J-AR01 canonical bytes reproduce its payload hash; G-02 names that receipt and hash; accepted admission permits only a J-AR03/G-01 payload derived from those exact bytes. |
| Business-event publication | J-AR03 identity and canonical hash equal the G-01 J-AR13 product identity, payload bytes, and hash; the publishing J-AR14 names both outputs. |
| Proposal lifecycle | Every proposal J-AR06 subject and payload ref equal one J-AR05 `proposal_ref`; `from_status` equals the prior state token; `to_status` equals the rebuilt result; G-04 bytes and hash equal the exact view at the new token. |
| Journal posting | `journal.posted` proposal and journal refs equal J-AR05 and J-AR08; the journal source proposal, class, period, totals, lines, J-AR15 effect subject/key, G-04/G-05 publications, and J-AR14 outputs all agree. |
| Restatement manifest | J-AR09 ordered body hashes to the manifest hash in `restatement.adjustments_ready`, reconciles to exact J-AR08 lines, and produces the G-04 case view at that event token. |
| Reporting publication | `reporting_version.published`, successor J-AR10, J-AR15 effect claim, G-04/G-05/G-06 publications, and J-AR14 output refs agree on case, predecessor, manifest, successor identity, content, hash, and publication key. |
| Pre-scope predecessor | J-AR11 binds the exact J-AR10 core, J-AR12 reporting bytes and hash, prerequisite J-AR06 hard-close event and view hash, and imported G-06 J-AR13; no J-AR15 publication claim exists. |
| General G publication | J-AR13 canonical payload bytes reproduce its hash and exact product/state token; publisher and command or import basis match the authoritative owner outcome. |
| Command closure | Every accepted J-AR14 enumerates the identities and hashes of all authoritative records and contract publications committed by that command; no listed output may be absent or belong to another command. |
| Approved-decision return | Source-domain approval and candidate J-AR02 versions bind exact G-12, approval evidence, and candidate content; the I-S26 J-AR01 receipt resolves that same candidate version and hash. |

Any mismatch rejects the complete write set. A projection may not repair or
mask an authoritative binding failure.

Physical unique indexes are deferred. The later persistence contract must prove
that its chosen mechanism enforces every applicable row in one local
transaction.

## 9. I-S01 Through I-S26 Record Map

The table lists semantic writes. Projection updates occur in the same local
transaction as their authoritative causes but remain disposable.

| Step | Authoritative records appended | Projection or exact view affected | Durable G handoff |
|---|---|---|---|
| I-S01 | Replayable J-AR01 candidate receipt; Hermes J-AR02 admission result; J-AR14 command result | J-P01 candidate disposition | G-02 through J-AR13 |
| I-S02 | J-AR03 admitted business event; J-AR14 command result | J-P09 availability; J-P11 trace | G-01 through J-AR13 |
| I-S03 | Atlas J-AR05 automated proposal treatment; J-AR14 command result | J-P02 `DRAFT` proposal | None |
| I-S04 | J-AR06 `proposal.submitted`; J-AR14 command result | J-P02/J-P03 `SUBMITTED` | G-04 exact proposal view and G-05 event |
| I-S05 | J-AR06 `proposal.deferred`; J-AR14 command result | J-P02/J-P03 `DEFERRED` | G-04 exact proposal view and G-05 event |
| I-S06 | J-AR06 `period.hard_closed`; J-AR14 command result | J-P04/J-P05 `HARD_CLOSED` | G-04 exact period view and G-05 event |
| Bootstrap input before I-S01 | Sealed external import candidate only; no J-AR or G record | No application-readable projection | None |
| Pre-scope import seam after I-S06 | Atomically append J-AR10 predecessor v1, J-AR11 attestation, verified J-AR12 content, and imported J-AR13 publication | J-P08 indexes v1; J-P09 enforces `available_from` | Imported G-06, explicitly pre-scope |
| I-S07 | Hermes J-AR02 reconciliation and evidence declaration; J-AR14 command result | J-P10/J-P11 | G-03 through J-AR13 |
| I-S08 | Argus J-AR02 test run and exception; J-AR14 command result | J-P10/J-P11 | G-07 through J-AR13 |
| I-S09 | Aegis J-AR02 review, finding, and issue versions; J-AR14 command result | J-P10 issue index | G-08 through J-AR13 |
| I-S10 | Aegis J-AR02 blocked readiness version; J-AR14 command result | J-P10 readiness index | G-10 through J-AR13 |
| I-S11 | Aegis J-AR02 directive and issue-treatment version; J-AR14 command result | J-P10 issue/directive index | G-09 through J-AR13 |
| I-S12 accepted | J-AR06 `restatement.proposed`; J-AR14 command result | J-P06/J-P07 `PROPOSED` | G-04 exact case view and G-05 event |
| I-S12 rejected | J-AR14 rejected result; J-AR16 disposition; evidence declaration | No accounting projection | G-14 through J-AR13 |
| I-S13 | Atlas J-AR05 restatement proposal treatment; J-AR14 command result | J-P02 `DRAFT` proposal | None |
| I-S14 | J-AR06 `proposal.submitted`; J-AR14 command result | J-P02/J-P03 `SUBMITTED` | G-04 exact proposal view and G-05 event |
| I-S15 | J-AR06 `proposal.approved`; J-AR14 command result | J-P02/J-P03 `APPROVED` | G-04 exact proposal view and G-05 event |
| I-S16 | J-AR06 `journal.posted`; J-AR08 header and lines; J-AR15 posting claim; J-AR14 command result | J-P02/J-P03 `POSTED`; J-P11 trace | G-04 journal/proposal views and G-05 event |
| I-S17 | J-AR06 `restatement.adjustment_linked`; J-AR14 command result | J-P06/J-P07 linked `PROPOSED` view | G-04 exact case view and G-05 event |
| I-S18 | J-AR09 frozen manifest; J-AR06 `restatement.adjustments_ready`; J-AR14 command result | J-P06/J-P07 `ADJUSTMENTS_READY` | G-04 exact case view and G-05 event |
| I-S19 | J-AR06 `restatement.approved`; J-AR14 command result | J-P06/J-P07 `APPROVED` | G-04 exact case view and G-05 event |
| I-S20 | J-AR06 `reporting_version.published`; J-AR10 successor v2; J-AR15 publication claim; J-AR14 command result | J-P06/J-P07 `PUBLISHED`; J-P08 history | G-04 case, G-05 event, and G-06 successor |
| I-S21 | Argus J-AR02 verification result; J-AR14 command result | J-P10/J-P11 | G-07 through J-AR13 |
| I-S22 | Aegis J-AR02 successor readiness version; J-AR14 command result | J-P10 readiness index | G-10 through J-AR13 |
| I-S23 | Pythia J-AR02 planning-input snapshot; J-AR14 command result | J-P10 planning index | G-11 through J-AR13 |
| I-S24 | Pythia J-AR02 decision product; J-AR14 command result | J-P10 decision index | G-12 through J-AR13 |
| I-S25 | Exact source-domain J-AR02 approval or rejection and, if approved, candidate versions; J-AR14 command result | J-P10 approval index | Direct approved-decision handoff by exact J-AR02 refs and hashes; not J-AR13 |
| I-S26 | New replayable J-AR01 receipt referencing the exact approved candidate content; Hermes J-AR02 unsupported admission result; J-AR14 command result | J-P01 unsupported disposition | G-02 through J-AR13; no G-01 |

The external bootstrap input and import seam are deliberately not assigned a
new Artifact I step. The first has no authoritative write. The second is one
bounded import transaction through the same persistence boundary. Neither is
another C-001 application command or accounting transition.

## 10. CT-1 Reconciliation

CT-1 uses the same record roles with these differences:

- J-010 enters as immutable J-AR17 source state and is exposed only as J-P12
  under G-13;
- J-010 never becomes J-AR08 authored by Artifact F or the Milestone 2 runtime;
- reversal and replacement each receive their own J-AR05 proposal treatment;
- their submission, approval, and posting actions append ordinary J-AR06 events;
- J-011 and J-012 are ordinary immutable J-AR08 journals and lines;
- posting creates separate J-AR15 effect claims for each proposal; and
- no restatement manifest, reporting version, readiness, or Pythia product is
  created.

The reversal constructor must consume the exact G-13 publication and prove:

```text
G-13 source_hash
= reversal proposal declared input_hash
before reversal-line derivation or comparison
```

The G-13 source and contract publication are authoritative inputs. J-P12 itself
remains a non-authoring projection.

## 11. Rebuild Procedure

Projection rebuild is deterministic and ordered by dependency, not by physical
table order.

1. Verify immutable identities and canonical hashes for J-AR01 through J-AR17.
2. Load configuration versions, import attestations, evidence availability, and
   accounting-period opening facts.
3. Rebuild candidate and contract-availability projections.
4. Rebuild proposal `DRAFT` states from treatment records and construction
   command results.
5. Fold accounting events in causal order to rebuild proposal, period, and
   restatement-case lifecycle projections.
6. Bind journal effects, manifest bodies, and reporting-version cores to their
   creating events and effect claims.
7. Rebuild module-product and purpose-specific readiness indexes from exact
   owned versions.
8. Rebuild end-to-end trace edges from immutable upstream references.
9. Optionally regenerate boundary observations from an executed replay; never
   treat regenerated observations as authoritative outcomes.
10. Produce semantic digests and compare them with clean-start and restart
    digests.

A rebuild fails rather than guessing if an event references an absent treatment,
an owned value body is missing, a publication refers to an unavailable product,
or a hash-bound relationship cannot be reproduced.

## 12. Semantic Digest Sets

Milestone 2 requires three named digest sets.

Every set is evaluated at one declared semantic `as_of_time`, carried as report
context. Clean-start, restart, and rebuild comparisons reuse that same value.

### 12.1 Authoritative digest

Includes canonical semantic bytes for:

- all J-AR01 through J-AR17 records present in the scenario;
- exact relationships and origin discriminators;
- content verification status; and
- semantic availability times.

### 12.2 Projection digest

Includes canonical bytes for J-P01 through J-P12 after rebuild. It excludes
checkpoint IDs, adapter metadata, and J-P13 observations.

### 12.3 Canonical compatibility digest

Includes the Artifact F payloads and reporting proof bodies required by H0-H7.
For canonical inputs, these bytes must remain identical to the ratified fixture
corpus.

The required equality is:

```text
clean-start authoritative digest = restart authoritative digest
clean-start projection digest    = restart projection digest
clean-start projection digest    = rebuilt projection digest
canonical compatibility digest   = ratified fixture digest
```

## 13. Failure and Recovery Rules

| Failure | Required result |
|---|---|
| Duplicate immutable identity with different hash | Reject; write nothing. |
| Candidate receipt lacks resolvable canonical bytes or its hash differs | Reject admission; do not publish G-02 acceptance or G-01. |
| Stale lifecycle token | Reject before append; preserve prior command result rules. |
| Event append succeeds but projection update fails before commit | Roll back both within the local transaction. |
| Projection is lost after commit | Rebuild from authoritative records; no domain event is re-emitted. |
| Command retry after restart | Return J-AR14 result; do not append another event. |
| Posting or publication retry under a new command ID | Return or reject through J-AR15 claim; do not duplicate effect. |
| Import retry with identical content | Return original J-AR11 receipt. |
| Import retry with changed content or provenance | Reject identity conflict. |
| Any application, planner, domain, projection, query, or trace read requests predecessor before availability | Return unavailable or omit it; do not expose or infer G-06. |
| Import prerequisite close event or view hash does not resolve | Reject import; do not expose predecessor or imported G-06. |
| Reporting successor references absent or unavailable predecessor | Reject publication. |
| Manifest body missing but hash remains | Rebuild fails; hash alone cannot reproduce the presentation bridge. |
| Any section 8.1 binding differs or cannot be reproduced | Reject before commit, or fail rebuild if historical corruption is detected. |
| Boundary observation sink fails | Preserve committed authoritative outcome; retry or omit observation. |

## 14. Acceptance Criteria

Artifact J may be ratified only when all of the following hold.

- J-A01: every I-S01 through I-S26 write set maps to authoritative records and
  any affected projection;
- J-A02: every authoritative record has one semantic owner and immutable
  identity;
- J-A03: no current projection is required to reconstruct its own authoritative
  source;
- J-A04: one proposal treatment version is stored once and never overwritten by
  lifecycle changes;
- J-A05: submitted, approved, deferred, and posted proposal views are
  independently reproducible from an explicit state token;
- J-A06: canonical terminal proposal views remain byte-identical to Artifact F;
- J-A07: cross-module proposal references pin treatment identity and lifecycle
  state without adding an Artifact F field;
- J-A08: deleting J-P02 and J-P03 loses no proposal history;
- J-A09: predecessor v1 has immutable content, real publication provenance, and
  a bounded pre-scope import attestation;
- J-A10: predecessor import binds an exact hard-close event and view hash;
  availability follows that close and precedes its first controlled consumption;
- J-A11: importing v1 adds no accounting event and consumes no ordinary
  publication effect key;
- J-A12: identical import retry is idempotent and conflicting import is rejected;
- J-A13: successor v2 names the exact imported v1 and leaves v1 byte-unchanged;
- J-A14: proposal, period, and restatement-case projections rebuild from the
  declared records without hidden fixture state;
- J-A15: manifest bodies, journal lines, and reporting content remain
  authoritative even though their lifecycle indexes are rebuildable;
- J-A16: every durable G handoff is an authoritative publication record committed
  with its publisher outcome or atomically admitted with its pre-scope import
  attestation;
- J-A17: consumer outcomes retain exact upstream publication references without
  requiring a second semantic acknowledgement store;
- J-A18: command results, G-14 dispositions, and effect claims survive projection
  deletion and process restart;
- J-A19: stale-write protection uses an authoritative event, construction-result,
  base-record, or exact product-version token rather than a mutable projection
  timestamp;
- J-A20: G-13 rebuilds from immutable J-AR17 source state, remains a
  non-authoring projection, and binds CT-1 before reversal derivation;
- J-A21: clean-start, restart, and rebuilt semantic digests compare the same
  domain content while excluding physical storage details;
- J-A22: the architecture makes no claim that accounting events alone rebuild
  the platform;
- J-A23: no database product, physical schema, public API, new accounting event,
  or tenth accounting object is introduced; and
- J-A24: the two persistence blockers in Artifact I are resolved rather than
  carried into physical schema design;
- J-A25: every candidate receipt retains or resolves exact canonical bytes, and
  I-S02 remains executable after restart without external redelivery;
- J-A26: every multi-record accepted write and every rebuild validates all
  section 8.1 cross-record bindings;
- J-A27: the approved-decision handoff uses exact source-domain J-AR02 approval
  and candidate versions consumed by I-S26 without inventing a G contract;
- J-A28: every J-AR13 retains exact canonical payload bytes or an immutable
  content reference plus contract and canonicalization versions sufficient to
  reproduce the historical handoff; and
- J-A29: the predecessor remains external sealed input before I-S06, then one
  bounded import transaction atomically creates J-AR10/J-AR11/J-AR12/J-AR13
  only after its exact prerequisite hard-close state exists; and
- J-A30: the pre-scope import operation remains inside the shared application
  boundary, is typed only for the declared predecessor, and cannot become a
  second domain-command or general ingestion framework.

## 15. Decisions Resolved and Still Open

### 15.1 Resolved by Artifact J

- proposal treatment and lifecycle persistence are separate;
- exact proposal state uses an authoritative state token;
- Artifact F proposal payloads are derived exact views;
- predecessor v1 uses a pre-scope import attestation and availability gate;
- the import is not an accounting event or ordinary publication effect;
- durable G publications are authoritative coordination records;
- separate semantic consumption acknowledgements are unnecessary;
- candidate receipts retain replayable canonical content as well as identity
  and hash;
- event, construction-result, base-record, or exact product-version identities
  supply lifecycle stale-write tokens;
- exact hard-close state and global as-of visibility constrain predecessor
  import;
- multi-record command outcomes satisfy explicit atomic binding invariants;
- approved-decision return uses exact source-domain product versions without a
  synthetic G publication; and
- current projections are disposable and rebuildable.

### 15.2 Still open for later Milestone 2 artifacts

1. exact minimum internal message bodies for G-01 through G-14;
2. repository, transaction, and persistence-port interfaces;
3. clock, identity, and sequence-allocation ports;
4. exact module-product version shapes outside Artifact F;
5. which evidence bodies beyond the two reporting proofs are committed;
6. migration and schema-compatibility rules;
7. physical storage engine and schema;
8. projection checkpoint frequency and operational rebuild tooling; and
9. Milestone 2 assertion-report schema.

## 16. Recommended Next Artifact

After Artifact J passes critique, the next artifact should define the
persistence port and transactional unit-of-work contract against these semantic
record roles.

That artifact may compare adapter capabilities, but it must remain independent
of a database product. A physical engine should be selected only after an
in-memory adapter proves:

- immutable append and exact retrieval;
- optimistic concurrency through state tokens;
- command and effect idempotency;
- atomic authoritative writes plus projection updates;
- pre-scope import availability;
- projection deletion and deterministic rebuild; and
- clean-start, restart-shaped, and rebuild digest parity.
