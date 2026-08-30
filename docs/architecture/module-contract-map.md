# Artifact G: Module Ownership and Publish/Consume Contract Map

Design sequence artifact G. This document fixes ownership and cross-module
handoffs for the shared enterprise substrate and the five product lenses. It
does not define new payload schemas.

Status: Design v0.2 - ratified 2026-07-23

Binds:

- the five platform invariants;
- Artifact C: Accounting Object Model;
- Artifact E v0.2.1: Accounting State Machines and Command/Event Matrix;
- Artifact F v0.2: Minimum Payload Contracts;
- canonical transactions C-001 and CT-1; and
- ADR-001: Use One Platform With Product Lenses.

## 0. Purpose and Closure Rule

The platform is one system with a shared enterprise substrate. Hermes, Atlas,
Argus, Aegis, and Pythia are capability lenses over that substrate, not
applications with private copies of enterprise truth.

Artifact G is complete when:

1. every in-scope object and lifecycle has one authoritative writer;
2. every cross-module handoff has a named publisher and named consumers;
3. a consumer cannot silently reinterpret or mutate a publisher's record;
4. C-001 and CT-1 can execute using only the listed handoffs;
5. accounting events remain structurally unable to re-enter the business-event
   posting engine; and
6. purpose-specific readiness accompanies controlled downstream use.

Artifact G defines semantic contracts: ownership, meaning, direction,
versioning, and permitted use. Artifact F remains authoritative for the
accounting payloads it ratified. Payload contracts for Hermes, Argus, Aegis,
and Pythia are deferred until their minimum canonical cases require them.

## 1. Ownership Vocabulary

The following terms are not interchangeable.

| Term | Meaning |
|---|---|
| Semantic owner | Defines what an object or contract means. |
| Authoritative writer | The only boundary permitted to create lifecycle state or append an authoritative transition for the object. |
| Publisher | Exposes an immutable or versioned contract to consumers. |
| Consumer | Reads a published contract for a declared purpose without acquiring ownership of it. |
| Derivation owner | Owns a new projection whose inputs retain exact references to upstream records. |

A producer of an underlying fact is not automatically the semantic owner of
every projection derived from that fact. A consumer may derive a new product,
but it must:

- give the projection a new identity;
- declare its semantics and owner;
- pin the exact upstream contract versions and object versions used; and
- preserve the evidence and lineage needed to reproduce it.

Copying an object into a module-local table does not transfer ownership.

## 2. The Shared Enterprise Substrate

The shared enterprise substrate is infrastructure, not a sixth product module.
It contains:

- the immutable business-event log;
- canonical object identities and source-to-canonical mappings;
- the contract registry;
- immutable evidence references;
- cross-module lineage edges; and
- append-only publication metadata.

### 2.1 Business-event ownership

The domain that performs or authorises a real-world action owns the meaning of
that business event. For example:

- a simulated billing source produces `invoice.issued`;
- an operational workflow produces `cash.applied`; and
- an approved Pythia decision may produce `hiring.deferred`.

Hermes governs admission, conformance, identity resolution, provenance, and
delivery into the shared event log. Hermes does not acquire the semantic
ownership of an event merely because it admitted it.

Only an admitted `business_event` may enter the Atlas posting-rule evaluator.
No `accounting_event`, governance event, assurance result, readiness
assessment, forecast, or reporting publication may enter that interface.

### 2.2 Evidence ownership

Evidence is immutable after publication. The module that creates an evidence
artifact owns its content and publishes its reference. Other modules may:

- link the evidence reference;
- add a separate review or attestation artifact; or
- challenge its sufficiency.

They may not rewrite the original evidence or reuse its identity for different
content.

### 2.3 Contract admission

Every published contract instance declares:

- contract identifier and positive integer version;
- publisher;
- object identity and object version where applicable;
- event or record time;
- semantic grain;
- lineage and evidence references required by that contract; and
- integrity hash where the bound artifact requires one.

Unknown versions, undeclared fields, invalid lifecycle states, and unresolved
required references are rejected or quarantined. They are never silently
coerced.

## 3. Truth and Interpretation Boundaries

The truth layers accumulate; no layer overwrites a prior layer.

| Layer | Primary boundary | Publishes | Does not claim |
|---|---|---|---|
| Business-event truth | Source domain through shared substrate | Material actions and state transitions | That every source recorded the action correctly. |
| Source-system truth | Hermes | What sources recorded, their mappings, lineage, and disagreements | The correct accounting or governance treatment. |
| Accounting truth | Atlas | Proposals, journals, books, periods, and reporting versions | That the information is suitable for every purpose. |
| Assurance observation | Argus | Tests, exceptions, and reproducible test evidence | A formal governance conclusion. |
| Governed truth | Aegis | Dispositions, findings, issues, directives, and purpose-specific readiness | A different accounting amount or ledger history. |
| Decision-use truth | Pythia | Input snapshots, scenarios, forecasts, recommendations, and decisions | Authority to rewrite actuals or bypass governance. |

Atlas owns the books. Aegis owns whether a named data product version is
permitted for a named purpose. Pythia owns the future projection it creates
from those governed inputs.

## 4. Authoritative Object Ownership

### 4.1 Ratified accounting objects

| Object | Semantic owner and authoritative writer | Permitted external interaction |
|---|---|---|
| `business_event` | Source business domain; admitted through shared substrate | Hermes validates and traces it. Atlas and other declared consumers read it. |
| `posting_rule` | Atlas | Aegis may approve a policy basis; Argus may test operation. Neither mutates the rule. |
| `journal_proposal` | Atlas | Argus and Aegis may inspect and reference exact versions. |
| `accounting_event` | Atlas | Other modules consume the append-only stream. It never enters the posting engine. |
| `journal_entry` | Atlas | Read-only consumption and independent assurance are permitted. |
| `journal_line` | Atlas | Read-only consumption and independent assurance are permitted. |
| `accounting_period` | Atlas | Aegis may issue a directive; only Atlas transitions period state. |
| `reporting_version` | Atlas | Aegis assesses readiness; Pythia consumes an exact version. |
| `restatement_case` | Atlas | Aegis owns the trigger, directive, and readiness consequences; only Atlas owns the accounting restatement lifecycle. |

`restatement_case` remains Atlas-owned even when an Aegis issue or directive
initiates it. The directive is authority to consider and execute a treatment;
it is not itself an accounting transition. Atlas validates the authority,
executes the appropriate command, and publishes the resulting accounting
event.

### 4.2 Module-owned objects outside Artifact F

The following ownership assignments are semantic boundaries only. Their
minimum payloads are not defined here.

| Module | Owned object families |
|---|---|
| Hermes | admission result, source-lineage record, identity mapping, reconciliation result, source-quality observation |
| Argus | test definition, test run, exception, assurance evidence |
| Aegis | review disposition, finding, issue, remediation directive, readiness assessment, governance attestation |
| Pythia | planning input snapshot, assumption set, scenario, forecast version, recommendation, decision |

### 4.3 Artifact F actor roles

Artifact F actor roles describe who or what performed an accounting action.
They do not create a second ownership axis. When these roles appear on an
Artifact F object or accounting event, they act within Atlas's authoritative
accounting boundary.

| Artifact F role | Execution boundary in Artifact F | Meaning |
|---|---|---|
| `RULE_ENGINE` | Atlas | Evaluates an admitted business event against a versioned posting rule and prepares an automated proposal. |
| `CORRECTION_ENGINE` | Atlas | Runs a typed reversal, replacement, or restatement-adjustment constructor under validated authority. |
| `CONTROLLER` | Atlas | Performs an accounting approval, close, deferral, or restatement action. |
| `CFO` | Atlas | Performs the accounting publication or restatement approval represented by the Artifact F event. |
| `POSTING_SERVICE` | Atlas | Atomically validates and posts an approved proposal. |
| `REPORTING_SERVICE` | Atlas | Publishes an immutable reporting version from an approved restatement case. |

The same person may separately act in an Aegis workflow, but that action must
be represented by an Aegis-owned contract. For example, the `CONTROLLER` on
`restatement.proposed` is Atlas acting on validated Aegis references; it is not
Aegis directly creating RC-001. An `actor_ref.role` alone never grants module
write authority. The target object, contract publisher, and command boundary
determine that authority.

## 5. Module Responsibilities and Prohibitions

### 5.1 Hermes

Hermes consumes source records, candidate business events, and the G-05
accounting-event stream for source-to-accounting lineage. It publishes
admission decisions, provenance, mappings, reconciliations, and source-quality
observations.

Its G-05 consumption is limited to attaching immutable backward and forward
lineage between admitted source events and the accounting actions Atlas
published. Hermes may report a missing, duplicate, or unresolved lineage edge.
It may not reinterpret the accounting treatment, change an accounting event,
or publish accounting truth.

Hermes must not:

- decide an accounting treatment;
- construct, approve, post, reverse, or restate a journal;
- declare a formal finding or issue;
- set purpose-specific readiness; or
- alter the meaning supplied by a source domain.

### 5.2 Atlas

Atlas consumes admitted business events, versioned accounting configuration,
and valid governance directives. It publishes the accounting object set,
accounting-event stream, books, and reporting versions.

Atlas must not:

- rewrite source or business-event history;
- modify or suppress an Argus exception;
- create an Aegis review disposition on Aegis's behalf;
- self-certify a reporting version for a controlled downstream purpose; or
- treat an accounting event as posting-rule input.

### 5.3 Argus

Argus consumes source lineage, reconciliations, accounting objects, reporting
versions, and versioned test definitions. It publishes machine-generated test
results, exceptions, and reproducible evidence.

Argus must not:

- mutate source or accounting records;
- post a correcting journal;
- convert an exception into a formal finding without human governance review;
- approve remediation or readiness; or
- hide a failed test by changing its population after execution.

### 5.4 Aegis

Aegis consumes exceptions, assurance evidence, accounting products, and
governance policy. It publishes review dispositions, findings, issues,
remediation directives, attestations, and purpose-specific readiness.

Aegis must not:

- alter an Argus exception or its original evidence;
- recalculate or overwrite accounting truth;
- transition an Atlas accounting object;
- publish a reporting version; or
- treat a directive as proof that its requested outcome occurred.

### 5.5 Pythia

Pythia consumes an exact Atlas data-product version together with the exact
Aegis readiness assessment that permits the intended use. It publishes frozen
input snapshots, scenarios, forecasts, recommendations, and governed
decisions.

Pythia must not:

- select an implicit "latest" actual or readiness version;
- use a blocked input for the blocked purpose;
- mutate actuals or readiness;
- construct accounting events or journals; or
- feed a planning output directly into the posting engine.

An approved operational decision may emit a new business event through the
shared admission boundary. It then follows the same lineage, validation, and
posting path as any other business event.

## 6. Publish/Consume Contract Registry

The identifiers below name semantic contracts, not wire schemas.

| ID | Contract | Publisher | Required consumers | Meaning and constraint |
|---|---|---|---|---|
| G-01 | Admitted business event | Shared substrate after Hermes admission | Atlas; Argus where relevant | An immutable domain event with validated identity and provenance. The only posting-engine input class. |
| G-02 | Source admission and lineage result | Hermes | Shared substrate, Atlas, Argus | Acceptance, rejection, mapping, and source provenance for a candidate event or record. Does not assert accounting correctness. The shared substrate consumes an accepted result only to admit G-01; it acquires no Hermes semantic ownership. |
| G-03 | Reconciliation result | Hermes | Argus; Aegis and Atlas as declared readers | A versioned comparison of named source populations. A failed result does not itself post an adjustment. |
| G-04 | Accounting object set | Atlas | Argus, Aegis; Pythia for declared products | Exact Artifact F objects and later compatible versions. Consumers receive read-only records. |
| G-05 | Accounting-event stream | Atlas | Argus, Aegis; Hermes for lineage | Immutable evidence of accounting actions and transitions. Explicitly barred from G-01 and the posting engine. |
| G-06 | Reporting version | Atlas | Argus, Aegis, Pythia | Immutable identity and content reference for one published view. It carries no self-issued readiness claim. |
| G-07 | Assurance result and exception | Argus | Aegis; Atlas as informational reader | Machine observation over a frozen population, test version, parameters, execution, and evidence. Not yet a finding. |
| G-08 | Governance disposition, finding, and issue | Aegis | Argus, Atlas; Pythia where reliance is affected | Human-governed conclusion that preserves links to the underlying exceptions and evidence. |
| G-09 | Remediation directive | Aegis | Named accountable module | Authorisation and requested outcome. The receiver publishes separate execution events and evidence. |
| G-10 | Purpose-specific readiness assessment | Aegis | Pythia and every controlled consumer | Status for an exact data product, version, period, scope, and purpose. Missing or stale readiness is not approval. |
| G-11 | Planning input snapshot | Pythia | Argus, Aegis | Frozen set of exact reporting, readiness, assumption, and exclusion references used by a model run. |
| G-12 | Scenario, forecast, recommendation, and decision | Pythia | Aegis, Argus; Atlas as informational reader | Versioned decision product. Only a separately approved operational action may become a new G-01 candidate. |
| G-13 | Referenced accounting-state projection | Atlas read boundary | Argus; correction constructors as declared readers | Content-addressed, minimal read projection of immutable accounting state outside Artifact F's authored fixture boundary. It is not an Artifact F object and cannot be emitted by its domain serializer. |
| G-14 | Command disposition | Target module receiving a cross-module command | Requesting module; Argus and Aegis where relevant | Observable acceptance, rejection, or pre-construction failure keyed to the command and request. It requires no target domain object and is not an accounting event. |

All contracts may reference immutable evidence through the shared evidence
boundary. A reference does not grant the consumer permission to change the
evidence.

## 7. Contract Use Rules

### 7.1 Exact-version consumption

Consumers pin the contract version and the upstream object or product version.
They do not resolve an unqualified family identifier or select "latest" at
execution time.

If an upstream producer publishes a correction:

- the prior record remains immutable;
- the producer emits a successor event or object version;
- existing downstream products retain their original input references; and
- a consumer that adopts the correction publishes a new derived-product
  version.

### 7.2 Readiness pairing

For a controlled downstream purpose, value and readiness form a pair:

```text
Atlas data product version
+ Aegis readiness assessment version
+ declared purpose and scope
-> permitted Pythia input
```

A readiness assessment cannot change the value. A corrected value cannot
silently inherit readiness from its predecessor.

### 7.3 Commands and outcomes

A cross-module directive or command expresses requested authority. It is never
substituted for an outcome event.

```text
Aegis remediation directive
-> Atlas command validation
-> Atlas accounting transition
-> Atlas accounting event
-> Argus verification
-> Aegis closure decision
```

Rejected, deferred, and failed commands remain observable. The requesting
module does not write the target module's state.

### 7.4 Delivery and replay

Logical command identity remains stable across delivery retries. Where the
bound payload contract requires an idempotency key, the target uses it to
protect the effect across distinct command attempts.

Retrying delivery may reproduce an acknowledgement. It must not create:

- a second accounting transition;
- a duplicate reporting publication;
- a new exception for the same test-run result; or
- a second governance disposition for the same command attempt.

Runtime retry behaviour remains an executable-harness concern.

### 7.5 Pre-construction command disposition

A target module may reject or fail a command before a proposal, restatement
case, test run, issue, or scenario exists. That outcome is published through
G-14 rather than forced into an object-scoped domain event.

At minimum, the semantic contract identifies:

- stable command identity;
- requesting and target modules;
- request or directive reference;
- disposition: `ACCEPTED`, `REJECTED`, or `FAILED`;
- reason code and recorded time; and
- evidence references where required.

G-14 is a platform control contract. It is not one of Artifact F's nine
objects, is not one of its ten accounting-event types, and cannot enter the
posting engine. `ACCEPTED` means only that the target accepted the command for
processing. A later domain event separately proves any resulting state change.

## 8. C-001 Contract Proof

C-001 uses the following handoffs and no direct cross-module writes.

| Step | Publisher -> consumer | Contract | Proof |
|---|---|---|---|
| 1 | Source domain -> shared substrate | G-01 candidate | The June recognition-due event states the business action and retains source meaning. |
| 2 | Hermes -> shared substrate and Atlas | G-02 then G-01 | Hermes validates identity and provenance, then admits the event without deciding its accounting treatment. |
| 3 | Atlas -> shared substrate | G-04 and G-05 | Atlas evaluates `PR-O2C-RECOG@v1`, creates P-551@v1, records submission and deferral, and hard-closes June. |
| 4 | Atlas and Hermes -> Argus | G-02, G-03, G-04, G-05, G-06 | Argus freezes the expected recognition population and finds the submitted-but-unposted proposal and June completeness gap. |
| 5 | Argus -> Aegis | G-07 | Argus publishes the exception and evidence; it does not create a formal issue. |
| 6 | Aegis -> Atlas and controlled consumers | G-08, G-09, G-10 | Aegis confirms the finding, opens the issue, blocks affected uses, and issues a remediation directive. It does not open RC-001 or post J-560. |
| 7 | Atlas -> Argus and Aegis | G-04, G-05, G-06 | Atlas owns RC-001, creates P-551@v2 and J-560, freezes the manifest, and publishes `2026-06@v2` while June remains hard-closed. |
| 8 | Argus -> Aegis | G-07 | Argus independently verifies the correction, manifest, and publication lineage. |
| 9 | Aegis -> Pythia | G-10 | Aegis publishes a successor readiness assessment for the exact v2 reporting product and intended forecasting purpose. |
| 10 | Atlas and Aegis -> Pythia | G-06 and G-10 | Pythia freezes the exact reporting and readiness versions in G-11 before producing G-12. |
| 11 | Pythia -> Argus and Aegis | G-11 and G-12 | Pythia publishes the frozen input snapshot, the governed forecast result, and the deferred-hire decision. Argus can reproduce the model inputs; Aegis can verify that the decision used the permitted product, version, purpose, and scope. |
| 12 | Approved operational decision -> shared substrate | G-12 then G-01 candidate | The separately approved hiring deferral returns through normal business-event admission. It is not posted directly from Pythia and can affect the next period only after G-01 admission. |

None of the C-001 accounting events re-enters G-01 or the posting-rule
evaluator. The Aegis directive authorises treatment but never becomes the
restatement transition itself. Steps 1 through 12 exercise every contract from
G-01 through G-12; G-13 and G-14 are separately exercised or bounded by CT-1
and the failure tests.

## 9. CT-1 Contract Proof

| Step | Publisher -> consumer | Contract | Proof |
|---|---|---|---|
| 1 | Hermes and Atlas -> Argus | G-03 and G-13 | Hermes publishes the customer-identity reconciliation. Atlas's read boundary exposes the immutable J-010 proof projection without claiming it as an Artifact F-authored object or accounting event. |
| 2 | Argus -> Aegis | G-07 | Argus publishes the cash-application exception and evidence. |
| 3 | Aegis -> Atlas | G-08 and G-09 | Aegis confirms the issue and directs correction; it does not construct reversal lines. |
| 4 | Atlas -> Argus and Aegis | G-04 and G-05 | Atlas's typed correction constructors create reversal P-REV-010@v1 and replacement P-REP-010@v1, then post J-011 and J-012. |
| 5 | Argus -> Aegis | G-07 | Argus verifies J-011 is equal and opposite to the exact J-010 hash declared as reversal input and that J-012 uses the corrected customer. |
| 6 | Aegis -> Argus and Atlas | G-08 | Aegis verifies remediation and closes or updates the issue. CT-1 has no controlled planning use, so this proof does not publish G-10 merely for symmetry. |

CT-1 proves that Hermes may expose a disagreement, Argus may identify an
exception, and Aegis may require treatment while Atlas remains the only writer
of accounting state.

CT-1 ends when the open-period correction is independently verified and its
governance issue is updated. It has no controlled planning consumer and
therefore is not required to exercise G-10, G-11, or G-12. If a later CT-1
data product is consumed for a controlled Pythia purpose, the G-06 plus G-10
pairing becomes mandatory at that point.

## 10. Prohibited Cross-Module Edges

The following edges are invalid by construction:

```text
accounting_event -> posting_rule evaluator
Argus exception -> journal mutation
Aegis directive -> accounting-state mutation
Aegis readiness -> reporting-value mutation
Pythia forecast -> accounting-event stream
consumer-local copy -> replacement of publisher authority
referenced state projection -> Artifact F object authorship
command disposition -> accounting-state transition
```

Also prohibited:

- direct writes into another module's owned lifecycle store;
- unversioned cross-module references;
- implicit adoption of a successor version;
- silent contract-field coercion;
- changing test inputs after a result is published;
- treating every exception as a finding or issue;
- closing an issue merely because a directive was accepted; and
- treating an attached evidence reference as proof of sufficient evidence.

## 11. Failure Behaviour

| Failure | Required behaviour |
|---|---|
| Unknown contract version | Reject or quarantine; do not downgrade silently. |
| Missing required upstream reference | Reject publication or mark execution failed with evidence. |
| Missing readiness for a controlled purpose | Block that use; absence is not approval. |
| Readiness refers to a different product version | Block consumption and expose the mismatch. |
| Duplicate delivery | Preserve one logical outcome and return a stable acknowledgement. |
| Upstream correction after downstream publication | Preserve both versions; require a new downstream product to adopt the correction. |
| Directive rejected before a target object exists | Publish G-14 with the rejection and basis; do not invent an Artifact F subject or mutate target state. |
| Evidence unavailable or hash mismatch | Fail verification and prevent reliance that requires that evidence. |

## 12. Acceptance Tests for Ratification

Artifact G may be ratified only when all of the following are true:

- G-A01: every owned object family has exactly one authoritative writer.
- G-A02: the shared substrate is not treated as a sixth product module.
- G-A03: Hermes can admit and trace an event without owning its business
  meaning or accounting treatment.
- G-A04: Atlas is the authoritative writer for the eight Atlas-owned Artifact F
  object types; `business_event` remains source-domain-owned.
- G-A05: Aegis can initiate remediation without directly opening or
  transitioning an Atlas restatement case.
- G-A06: Argus exceptions remain distinct from Aegis findings and issues.
- G-A07: Pythia can consume a reporting version only with exact,
  purpose-specific readiness when that use is controlled.
- G-A08: every consumer pins exact contract and object versions.
- G-A09: C-001 completes through G-01 to G-12 without a direct cross-module
  write.
- G-A10: CT-1 completes through the listed contracts while Atlas remains the
  only writer of J-011 and J-012.
- G-A11: no accounting event, governance event, or forecast can satisfy the
  G-01 posting-engine input type.
- G-A12: evidence remains immutable and traceable across every handoff.
- G-A13: retry, rejection, deferral, and stale-version outcomes remain
  observable.
- G-A14: no semantic payload schema beyond the canonical need is introduced.
- G-A15: J-010 is consumed through G-13 as non-authored referenced state and
  is never represented as an Artifact F-authored G-04 or G-05 record.
- G-A16: every Artifact F actor role executes inside the Atlas boundary when
  acting on an Artifact F object or event.
- G-A17: a pre-construction rejection is observable through G-14 without
  inventing an accounting-event subject.

## 13. Design Consequences Proposed for Ratification

Artifact G proposes the following rulings:

1. the shared enterprise substrate is infrastructure, not a sixth module;
2. source domains own business-event meaning while Hermes owns admission and
   lineage;
3. Atlas owns all accounting lifecycles, including `restatement_case`;
4. Aegis directives authorise requested outcomes but never mutate target
   module state;
5. readiness is an Aegis-owned, purpose-specific contract paired with an exact
   data-product version;
6. Pythia may return an approved operational decision only through the
   business-event admission boundary; and
7. all cross-module consumption is version-pinned, read-only, and
   evidence-preserving;
8. referenced pre-scope accounting state is exposed through a non-authoring
   G-13 read contract; and
9. commands rejected before object construction are exposed through G-14,
   outside the accounting-event ontology.

The next design artifact should define the first executable validation
acceptance criteria and test harness boundary. Module payload schemas should
remain deferred until that harness proves which fields are minimally required.
