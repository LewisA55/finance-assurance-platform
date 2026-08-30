# Artifact I - Runtime Application Boundary and Parameterised C-001 Execution

Status: Design v0.2.2 - ratified 2026-08-05

## 0. Purpose and Boundary

Artifact I defines the exact application command, query, transaction, and
module-handoff sequence for one parameterised C-001 execution.

It answers:

> Which application boundary receives each input, which authoritative owner
> may act, which exact state is read, which domain command is planned, which
> records are committed, which Artifact G contract is published, and where can
> execution terminate without constructing a target domain object?

Artifact I defines application semantics. It does not define:

- a database schema;
- an HTTP API;
- public wire formats;
- a generic workflow engine;
- a new business-event or accounting-event type;
- a production evidence system; or
- independently deployed modules.

The command and query names in this artifact are stable design vocabulary for
Milestone 2 review. Their eventual Python names and package locations remain
reversible implementation choices.

## 1. Binding Sources

Artifact I is subordinate to:

- the five invariants and architecture rules in `AGENTS.md`;
- Artifact C - Accounting Object Model;
- Artifact E v0.2.1 - Accounting State Machines and Command/Event Matrix;
- Artifact F v0.2.1 - Minimum Payload Contracts;
- Artifact G v0.2 - Module Ownership and Contract Map;
- Artifact H v0.3.1 - Executable Validation Harness Specification;
- canonical transaction C-001;
- canonical transaction CT-1;
- ADR-012 through ADR-017; and
- the approved Milestone 2 Persistent Runtime Vertical Slice roadmap.

The canonical fixture identities remain examples. Runtime commands operate on
fully qualified parameter values and must not branch on `C-001`, `P-551`,
`RC-001`, `J-560`, Orion, or the 2026-06/2026-07 period pair.

## 2. Ratified Rulings

Artifact I ratifies the following rulings.

### I-R01 - One application boundary, multiple authoritative owners

Milestone 2 has one in-process application boundary. A command is routed to the
owner of the lifecycle it may change. The boundary never grants a caller direct
write access to another owner's state.

### I-R02 - Application orchestration is explicit and finite

C-001 is coordinated as an explicit sequence of typed application commands.
There is no workflow definition language, generic saga engine, arbitrary state
machine interpreter, or plugin-driven command router.

### I-R03 - One command, one local transaction

Each accepted application command commits one complete local write set or no
write set. The whole C-001 sequence is not one transaction.

Cross-module progress occurs only after the publisher's transaction commits an
exact versioned output. A consumer then begins a new command using that exact
published reference.

### I-R04 - Contract publication and observation are different

An Artifact G contract publication is durable application state required for a
later consumer. It is committed with its publisher's authoritative outcome.

`BoundaryObservation` remains a test instrument. It observes actual publication
and consumption calls but cannot cause, approve, reject, commit, or roll back a
domain transition.

### I-R05 - G-01 begins only after admission

A source-domain candidate presented to Hermes is not yet G-01. Hermes first
records a G-02 admission result. Only an accepted candidate is published by the
shared substrate as G-01 and becomes eligible for Atlas posting-rule evaluation.

The phrase "G-01 candidate" in the canonical narrative means a candidate
presented to the G-01 admission path; it does not mean that admission has already
succeeded.

### I-R06 - Only the recognition-due event completes G-01 in Milestone 2

Artifact F v0.2.1 defines only `accounting.recognition.due` as an authored
business-event contract. The approved Pythia hiring decision therefore returns
to candidate intake but cannot be admitted as a new hiring event in Milestone 2.

Hermes durably records an unsupported-event disposition through G-02. It does
not publish G-01, and Atlas is never called. This closes the decision-feedback
loop at the admission boundary without inventing a new event taxonomy.

### I-R07 - Aegis authority never substitutes for an Atlas transition

Aegis publishes the issue and remediation directive through G-08 and G-09.
Atlas consumes the exact directive, validates it, and independently plans
`restatement.proposed`. An invalid directive produces G-14 without an Artifact F
subject.

### I-R08 - Correction construction does not use the posting-rule evaluator

The restatement-adjustment proposal is derived by the typed correction
constructor under validated policy and directive authority. It never enters the
business-event posting-rule path.

### I-R09 - Exact versions drive every controlled use

Pythia may freeze inputs only after receiving an exact Atlas reporting version
and an exact Aegis readiness assessment for the same product version, purpose,
period, and scope.

### I-R10 - Queries cannot imply write authority

Every query returns read-only exact versions or explicitly labelled rebuildable
projections. Reading another module's product never permits local mutation or
republishing under the consumer's ownership.

### I-R11 - The source business domain approves operational action

Pythia owns the recommendation and decision product. It does not approve its own
operational recommendation.

The source business domain affected by the action owns independent approval and
the meaning of any resulting business-event candidate. Automated policy checks
may be retained as approval evidence, but do not become Pythia self-approval.

In Artifact G trace terms, the source business domain acts through the logical
`ApprovedDecision` boundary. This is neither a sixth platform module nor a
separate owner of Pythia's decision product.

In the Artifact G trace, the source business domain acts through the logical
`ApprovedDecision` boundary. That boundary is not a sixth module or a separate
owner.

## 3. Parameter Set

One parameterised C-001 family instance is identified by a stable
`correlation_id`. The following values are supplied or resolved; none is inferred
from a canonical literal.

### 3.1 Source-domain inputs

- business-event identity;
- source system and source-record identity;
- legal entity;
- customer, contract, and recognition-schedule references;
- service-period start and end;
- recognition effective date;
- integer minor-unit amount;
- Artifact F contract version and currency;
- source occurrence and recording timestamps; and
- immutable evidence references.

### 3.2 Accounting configuration

- exact active posting-rule reference and resolved content hash;
- account mapping for deferred revenue and subscription revenue;
- required dimensions;
- affected ledger period;
- eligible open correction period;
- close-exception policy;
- restatement policy;
- approval and segregation-of-duties policy;
- materiality and disclosure-basis references; and
- evidence requirements.

### 3.3 Existing governed state

- affected period in `SOFT_CLOSED` state before hard close;
- correction period in `OPEN` state;
- predecessor reporting version for the affected period;
- recognition schedule population used by Hermes and Argus;
- close checklist and reconciliation state;
- actor identities and authority; and
- the planning purpose for which readiness may later be assessed.

The predecessor reporting version remains declared bootstrap state for this
milestone. Artifact F contains no original-publication event for it, so Artifact
I must not invent one.

## 4. Application Ports

The runtime exposes four kinds of in-process port.

### 4.1 Command port

Accepts one typed command with:

- stable command identity;
- correlation identity;
- declared target owner;
- exact upstream references;
- actor and authority context;
- expected state or version where concurrency matters; and
- evidence references required to make the decision.

It returns one of:

- committed command result;
- deterministic rejection;
- blocked result with exact unmet dependency; or
- prior result for a duplicate command delivery.

### 4.2 Query port

Returns exact immutable records or labelled projections. A query never resolves
an implicit `latest` for cross-module consumption.

### 4.3 Contract publication port

Commits an exact Artifact G semantic output under its authoritative publisher.
It preserves contract version, product or subject version, purpose, upstream
references, outcome, and evidence.

### 4.4 Observation port

Receives proof metadata after an actual publish or consume call. Removing the
observer must not alter command results, stored state, or later contract
availability.

## 5. Command Catalog

### 5.1 Source admission and Atlas initial treatment

| ID | Application command | Owner | Required result |
|---|---|---|---|
| I-C01 | `AssessBusinessEventCandidate` | Hermes | G-02 admission result; accepted input becomes eligible for G-01 publication. |
| I-C02 | `PublishAdmittedBusinessEvent` | Shared substrate | Exact G-01 admitted business event; no accounting interpretation. |
| I-C03 | `EvaluateAdmittedBusinessEvent` | Atlas | Invoke the existing `EvaluatePostingRule` planner command and derive one draft proposal treatment. |
| I-C04 | `SubmitJournalProposal` | Atlas | Invoke `SubmitProposal`; append `proposal.submitted`; preserve the submitted proposal identity and content. |
| I-C05 | `DeferJournalProposalAtClose` | Atlas | Invoke `DeferProposal`; append `proposal.deferred`; preserve an unposted terminal treatment. |
| I-C06 | `HardCloseAccountingPeriod` | Atlas | Invoke `HardClosePeriod`; append `period.hard_closed`; never hide the deferred proposal. |

### 5.2 Assurance and governance

| ID | Application command | Owner | Required result |
|---|---|---|---|
| I-C07 | `ReconcileRecognitionPopulation` | Hermes | Versioned G-03 comparison of expected recognition and recorded accounting populations. |
| I-C08 | `RunRecognitionCompletenessTest` | Argus | Frozen test result and G-07 exception when expected recognition is missing. |
| I-C09 | `ReviewAssuranceException` | Aegis | Separate review disposition, finding, and issue through G-08. |
| I-C10 | `AssessReportingReadiness` | Aegis | G-10 assessment for an exact reporting version, purpose, period, and scope. |
| I-C11 | `IssueRemediationDirective` | Aegis | G-09 directive naming Atlas, requested outcome, issue, policy, and evidence. |
| I-C12 | `ApplyRestatementDirective` | Atlas | Validate the exact G-09 input; invoke `ProposeRestatement` or publish subject-free G-14 rejection. |

### 5.3 Atlas correction and publication

| ID | Application command | Owner | Required result |
|---|---|---|---|
| I-C13 | `ConstructRestatementProposal` | Atlas | Invoke `ConstructCorrectionProposal` with `RESTATEMENT_ADJUSTMENT`; no accounting event and no posting-rule evaluation. |
| I-C14 | `ApproveJournalProposal` | Atlas | Invoke `ApproveProposal`; append `proposal.approved` only after authority, evidence, and segregation checks pass. |
| I-C15 | `PostJournalProposal` | Atlas | Invoke `PostProposal`; atomically append `journal.posted`, preserve the immutable proposal treatment, and create immutable journal header and lines. |
| I-C16 | `LinkRestatementAdjustment` | Atlas | Invoke the existing command; append `restatement.adjustment_linked` and publish the exact successor case view at that event token. |
| I-C17 | `FreezeRestatementManifest` | Atlas | Reconcile manifest entries to journal lines; append `restatement.adjustments_ready`; freeze manifest and hash. |
| I-C18 | `ApproveRestatement` | Atlas | Append `restatement.approved` after materiality, evidence, manifest, and disclosure review. |
| I-C19 | `PublishRestatedReportingVersion` | Atlas | Append `reporting_version.published`; create immutable successor reporting version; preserve predecessor. |

`SubmitJournalProposal` is used for both the original automated proposal and the
restatement-adjustment proposal. Artifact I does not create a second command
type merely because the origin differs.

### 5.4 Verification, readiness, and decision

| ID | Application command | Owner | Required result |
|---|---|---|---|
| I-C20 | `VerifyRestatementOutcome` | Argus | G-07 verification of journal, manifest, publication, and evidence lineage. |
| I-C21 | `FreezePlanningInputs` | Pythia | G-11 snapshot containing exact G-06, G-10, assumption, purpose, and exclusion references. |
| I-C22 | `ProduceGovernedDecision` | Pythia | G-12 result and hiring-deferral recommendation derived only from the frozen snapshot. |
| I-C23 | `ApproveOperationalDecision` | Source business domain | Independent approval or rejection; an approval may author a candidate linked to G-12 but cannot publish G-01. |

`AssessReportingReadiness` is one command type executed twice against different
product versions. Before remediation it blocks the declared use. After verified
remediation it may approve that exact use.

## 6. Query Catalog

| ID | Query | Owner of returned truth | Exact purpose |
|---|---|---|---|
| I-Q01 | `GetCandidateReceipt` | Shared substrate | Retrieve source candidate, intake identity, and current admission disposition. |
| I-Q02 | `GetAdmissionResult` | Hermes | Retrieve exact G-02 version and provenance basis. |
| I-Q03 | `GetBusinessEvent` | Source domain through substrate | Retrieve admitted event bytes by permanent identity. |
| I-Q04 | `GetPostingRule` | Atlas configuration | Retrieve exact rule version, effective range, content reference, and hash. |
| I-Q05 | `GetAccountingPeriod` | Atlas | Retrieve exact immutable version or labelled current period projection. |
| I-Q06 | `GetJournalProposal` | Atlas | Retrieve exact treatment version and lifecycle evidence without implicit latest resolution. |
| I-Q07 | `GetRecognitionReconciliation` | Hermes | Retrieve exact expected-versus-recorded population comparison. |
| I-Q08 | `GetAssuranceResult` | Argus | Retrieve frozen test inputs, version, outcome, exceptions, and evidence. |
| I-Q09 | `GetGovernanceIssue` | Aegis | Retrieve exact finding, issue, treatment, and remediation state. |
| I-Q10 | `GetRemediationDirective` | Aegis | Retrieve exact G-09 authority and requested outcome. |
| I-Q11 | `GetRestatementCase` | Atlas | Retrieve the exact case view at a named state token, including scope, linked journals, manifest, and publication state. |
| I-Q12 | `GetJournal` | Atlas | Retrieve immutable header and ordered lines by journal identity. |
| I-Q13 | `GetReportingVersion` | Atlas | Retrieve an exact reporting version; predecessor and successor remain independent. |
| I-Q14 | `ResolveReportingContent` | Shared evidence boundary | Resolve and hash-check exact content where bytes are committed. |
| I-Q15 | `GetReadinessAssessment` | Aegis | Retrieve readiness by exact product, version, purpose, period, and scope. |
| I-Q16 | `GetPlanningInputSnapshot` | Pythia | Retrieve exact G-11 inputs and exclusions. |
| I-Q17 | `GetGovernedDecision` | Pythia | Retrieve exact G-12 result and its frozen input reference. |
| I-Q18 | `GetCommandResult` | Target command owner | Retrieve original accepted, rejected, blocked, or duplicate-delivery result. |
| I-Q19 | `GetCommandDisposition` | Target command owner | Retrieve G-14 where target-object construction never began. |
| I-Q20 | `TraceReportingValue` | Shared read boundary | Traverse reporting content to reporting version, manifest, journal, proposal, rule or policy, business event, source, and evidence. |

Cross-module commands use exact query results as inputs. `Get*` names do not
permit a caller to retrieve a family and choose the latest member locally.

## 7. Authoritative Write Classes

Artifact I defines ownership and purpose, not physical tables.

| Owner | Authoritative write classes in C-001 |
|---|---|
| Source business domain | Business-event meaning, source-record identity, independent operational approval, and approved candidate meaning. |
| Shared substrate | Candidate receipt, admitted-event storage, exact contract publication identity, and approved-decision return receipt. |
| Hermes | Admission result, provenance mapping, reconciliation result, and unsupported-event disposition. |
| Atlas | Posting-rule version; immutable proposal treatment; accounting-period base facts; accounting events that determine proposal, period, and case lifecycle; journal header and lines; restatement manifest; reporting versions; Atlas command results and G-14 dispositions. |
| Argus | Test run, frozen population reference, exception, verification result, and reproducible evidence reference. |
| Aegis | Review disposition, finding, issue, remediation directive, readiness assessment, and governance command result. |
| Pythia | Planning-input snapshot, decision product, and Pythia command result. |

Rebuildable current projections exist for operational queries, but never become
a competing owner of these records.

## 8. Exact Parameterised C-001 Sequence

Each numbered step begins only after the prior required publication commits.
Steps with the same owner still use separate commands where Artifact E records a
separate lifecycle action.

### Stage A - Candidate admission

#### I-S01 - Receive and assess candidate

Command: I-C01 `AssessBusinessEventCandidate`.

Reads:

- candidate payload and contract version;
- source identity and provenance;
- prior candidate or event identity for duplicate detection;
- evidence references; and
- supported business-event contract registry.

Accepted write set:

- immutable candidate receipt;
- exact G-02 accepted admission result; and
- durable command result.

Rejected write set:

- immutable candidate receipt;
- exact G-02 rejected or quarantined result; and
- durable command result.

No rejected candidate is written as an admitted business event.

I-C01 has one semantic target owner: Hermes. The shared substrate persists the
candidate receipt as infrastructure within the command's atomic write set; it
does not acquire the source meaning or become a second admission owner.

#### I-S02 - Publish admitted recognition event

Command: I-C02 `PublishAdmittedBusinessEvent`.

Precondition: exact accepted G-02 result for the same candidate bytes.

Atomic write set:

- immutable admitted `accounting.recognition.due` business event;
- G-01 publication by the shared substrate; and
- durable command result.

The G-01 publication is the only input later accepted by I-C03.

### Stage B - Original accounting treatment and close

#### I-S03 - Evaluate posting rule

Command: I-C03 `EvaluateAdmittedBusinessEvent`.

Consumes:

- exact G-01 event;
- exact active posting-rule version;
- rule content hash and resolved inputs;
- legal entity, accounts, dimensions, amount, and target period; and
- current target-period projection.

Domain planner command: `EvaluatePostingRule` with `input_stream = BUSINESS_EVENT`.

Result:

- balanced draft proposal treatment with `AUTOMATED_POSTING` origin;
- derivation references and input hashes;
- durable command result; and
- no accounting event or journal.

#### I-S04 - Submit original proposal

Command: I-C04 `SubmitJournalProposal`.

Domain planner command: `SubmitProposal`.

Atomic write set:

- `proposal.submitted` accounting event;
- Atlas G-04/G-05 publications; and
- durable command result.

The immutable proposal treatment was created by I-S03. Submission changes only
event-derived lifecycle state and publishes the exact G-04 view at that token.

#### I-S05 - Defer original proposal

Command: I-C05 `DeferJournalProposalAtClose`.

Domain planner command: `DeferProposal`.

Atomic write set:

- `proposal.deferred` accounting event;
- exact deferred proposal view linked to the unchanged submitted treatment;
- Atlas G-04/G-05 publications; and
- durable command result.

The submitted history remains independently identifiable. No journal exists.

#### I-S06 - Hard-close affected period

Command: I-C06 `HardCloseAccountingPeriod`.

Domain planner command: `HardClosePeriod`.

Preconditions include balanced trial balance, ready reconciliations, no
unresolved submitted or approved proposals, and explicit treatment of the
deferred proposal.

Atomic write set:

- `period.hard_closed` accounting event;
- exact hard-closed period view at the new event token;
- Atlas G-04/G-05 publications; and
- durable command result.

The predecessor reporting version is preserved as declared existing state. The
close command does not invent its publication event.

### Stage C - Completeness assurance

#### I-S07 - Publish recognition reconciliation

Command: I-C07 `ReconcileRecognitionPopulation`.

Consumes the exact source schedule, Hermes G-02 lineage, Atlas G-05 proposal
lifecycle and posting events, and reporting-period scope. Hermes does not consume
G-04; Argus freezes the exact accounting-object population at I-S08.

Atomic write set:

- versioned G-03 reconciliation result;
- evidence references and population hashes; and
- durable command result.

Hermes reports the disagreement but does not decide the accounting correction.

#### I-S08 - Run completeness test

Command: I-C08 `RunRecognitionCompletenessTest`.

Consumes exact G-03, G-04, G-05, and predecessor G-06 references.

Expected result for the C-001 family:

```text
expected recognition = one quantified treatment
posted recognition   = zero
submitted unposted   = one
deferred             = one
difference           = parameterised recognition amount
```

Atomic write set:

- frozen Argus test run;
- blocking completeness exception;
- G-07 publication; and
- durable command result.

### Stage D - Governance and remediation authority

#### I-S09 - Review exception and open issue

Command: I-C09 `ReviewAssuranceException`.

Consumes the exact G-07 result and evidence.

Atomic write set:

- review disposition;
- finding and issue version;
- G-08 publication; and
- durable command result.

No Atlas object changes.

#### I-S10 - Block predecessor reporting use

Command: I-C10 `AssessReportingReadiness`.

Consumes the exact predecessor G-06 reporting version, issue, purpose, period,
scope, and evidence.

Atomic write set:

- G-10 blocked readiness assessment for the exact predecessor product; and
- durable command result.

The reporting value is not changed.

#### I-S11 - Issue restatement directive

Command: I-C11 `IssueRemediationDirective`.

Atomic write set:

- exact G-09 directive naming Atlas and the requested restatement outcome;
- successor issue treatment state where required; and
- durable command result.

The directive contains no restatement-case state and no journal lines.

#### I-S12 - Atlas validates directive and proposes restatement

Command: I-C12 `ApplyRestatementDirective`.

Consumes exact G-08/G-09 references and current Atlas period/proposal state.

On valid authority, Atlas invokes `ProposeRestatement`.

Accepted atomic write set:

- `restatement.proposed` accounting event;
- initial restatement-case identity whose state is derived from
  `restatement.proposed` and scoped to the affected period;
- Atlas G-04/G-05 publications; and
- durable command result.

Before-object rejection writes only:

- durable rejected command result;
- G-14 disposition linked to request and directive; and
- evidence of the rejection basis.

It creates no restatement case or accounting event.

### Stage E - Correction journal

#### I-S13 - Construct restatement-adjustment proposal

Command: I-C13 `ConstructRestatementProposal`.

Consumes the exact restatement-case view at its state token, deferred predecessor proposal,
restatement policy, G-09 directive, correction-period state, mappings, and input
hashes.

Domain planner command: `ConstructCorrectionProposal` with
`origin_type = RESTATEMENT_ADJUSTMENT`.

Result:

- balanced draft correction treatment;
- target is the eligible open correction period;
- origin basis references the restatement case, policy, directive, predecessor,
  and input hashes;
- durable command result; and
- no accounting event and no posting-rule evaluation.

#### I-S14 - Submit correction proposal

Command: I-C04 `SubmitJournalProposal`.

Atomic write set:

- `proposal.submitted` accounting event;
- Atlas G-04/G-05 publications; and
- durable command result.

The correction treatment created by I-S13 remains byte-immutable. Submission
publishes its exact state-specific view.

#### I-S15 - Approve correction proposal

Command: I-C14 `ApproveJournalProposal`.

Atomic write set:

- `proposal.approved` accounting event;
- exact approved proposal view at the new event token;
- Atlas G-04/G-05 publications; and
- durable command result.

The approver cannot equal the preparer where policy prohibits self-approval.

#### I-S16 - Post correction journal

Command: I-C15 `PostJournalProposal`.

Atomic write set:

- `journal.posted` accounting event;
- exact posted proposal view while the immutable treatment remains unchanged;
- immutable journal header and ordered lines;
- independently consumed posting effect key;
- Atlas G-04/G-05 publications; and
- durable command result.

The journal posts in the open correction period, not the hard-closed presented
period.

### Stage F - Restatement governance and publication

#### I-S17 - Link adjustment

Command: I-C16 `LinkRestatementAdjustment`.

Atomic write set:

- `restatement.adjustment_linked` accounting event;
- successor restatement-case view at the new event token with the governed
  journal relationship;
- Atlas G-04/G-05 publications; and
- durable command result.

#### I-S18 - Freeze manifest

Command: I-C17 `FreezeRestatementManifest`.

Atomic write set:

- reconciled presentation-adjustment manifest;
- immutable manifest hash;
- `restatement.adjustments_ready` accounting event;
- exact successor restatement-case view at that event token;
- Atlas G-04/G-05 publications; and
- durable command result.

Every manifest entry must reconcile to exact posted journal lines, and every
presented period must fall within case scope.

#### I-S19 - Approve restatement

Command: I-C18 `ApproveRestatement`.

Atomic write set:

- `restatement.approved` accounting event;
- exact approved case view at that event token;
- Atlas G-04/G-05 publications; and
- durable command result.

#### I-S20 - Publish successor reporting version

Command: I-C19 `PublishRestatedReportingVersion`.

Atomic write set:

- `reporting_version.published` accounting event;
- immutable successor reporting version;
- exact published case view at that event token;
- independently consumed publication effect key;
- Atlas G-04/G-05/G-06 publications; and
- durable command result.

The predecessor reporting version remains retrievable and byte-unchanged.

### Stage G - Verification and governed use

#### I-S21 - Verify correction and publication

Command: I-C20 `VerifyRestatementOutcome`.

Consumes exact journal, proposal, manifest, case, accounting events, predecessor
and successor reporting versions, proof content, and evidence.

Atomic write set:

- frozen Argus verification result;
- G-07 publication; and
- durable command result.

#### I-S22 - Assess successor readiness

Command: I-C10 `AssessReportingReadiness`.

Consumes exact successor G-06, G-07 verification, issue, purpose, period, scope,
and evidence.

Atomic write set:

- successor G-10 readiness assessment; and
- durable command result.

Corrected does not mean approved. Approval exists only if this command commits
an approving assessment for the declared purpose.

#### I-S23 - Freeze planning inputs

Command: I-C21 `FreezePlanningInputs`.

Consumes exact matching G-06 and G-10 versions plus declared assumptions and
exclusions.

Atomic write set:

- immutable G-11 planning-input snapshot; and
- durable command result.

Missing, blocked, stale, or mismatched readiness terminates here without a
planning snapshot.

#### I-S24 - Produce governed decision

Command: I-C22 `ProduceGovernedDecision`.

Consumes only the exact G-11 snapshot.

Atomic write set:

- immutable G-12 decision product;
- traceable recommendation basis; and
- durable command result.

Pythia does not modify Atlas values or Aegis readiness.

### Stage H - Decision approval and return

#### I-S25 - Approve operational decision

Command: I-C23 `ApproveOperationalDecision`.

Consumes exact G-12 and approval evidence.

Atomic write set:

- immutable approval or rejection;
- when approved, an immutable source-domain candidate linked to G-12; and
- durable command result.

Approval is independent of Pythia. It is not an accounting event, does not post
anything, and does not itself publish G-01.

#### I-S26 - Return candidate to admission

Command: I-C01 `AssessBusinessEventCandidate`, reused through normal intake.

Consumes the source-domain candidate authored by I-C23, with its exact G-12 and
approval references.

Milestone 2 expected outcome:

- shared substrate stores the immutable candidate receipt;
- Hermes assesses the candidate against the supported contract registry;
- Hermes publishes a G-02 unsupported-event disposition because no hiring-event
  contract is ratified;
- no G-01 event is published;
- Atlas is not invoked; and
- the result remains observable and traceable to G-12.

This is a finite, honest loop. It proves that decisions return through normal
admission without pretending that an unsupported event was admitted.

## 9. Command-to-Contract Map

| Command | Consumes | Publishes |
|---|---|---|
| I-C01 | Candidate intake | G-02 |
| I-C02 | Accepted G-02 | G-01 |
| I-C03 | G-01 and exact rule | Atlas command result; draft treatment only |
| I-C04 to I-C06 | Atlas exact state | G-04 and G-05 |
| I-C07 | Source schedule, Hermes G-02 lineage, and Atlas G-05 | G-03 |
| I-C08 | G-03, G-04, G-05, G-06 | G-07 |
| I-C09 | G-07 | G-08 |
| I-C10 | G-06, G-07/G-08 | G-10 |
| I-C11 | G-08 | G-09 |
| I-C12 | G-08 and G-09 | G-04/G-05 when accepted; G-14 when rejected before construction |
| I-C13 | G-04 and G-09 | Atlas command result; draft treatment only |
| I-C14 to I-C19 | Exact Atlas state | G-04, G-05, and G-06 where applicable |
| I-C20 | G-04, G-05, G-06 | G-07 |
| I-C21 | Exact G-06 and G-10 | G-11 |
| I-C22 | G-11 | G-12 |
| I-C23 | G-12 | Source-domain approval and, when approved, candidate meaning |
| I-C01 reused | Approved source-domain candidate | Candidate receipt and G-02; no G-01 in Milestone 2 |

## 10. Transaction and Failure Rules

### 10.1 Atomicity

For one command, the following succeed or fail together:

- authoritative object or event records;
- command result;
- effect-key consumption where applicable;
- contract publication;
- projection checkpoint; and
- G-14 disposition where the command has no target object.

An observational trace write is not part of this atomic set.

### 10.2 Duplicate delivery

The same command identity returns the original result and publishes no second
event, object version, effect, contract record, or disposition.

A different command identity using a consumed posting or publication effect key
is rejected without repeating the effect.

### 10.3 Stale version

A command that planned against a superseded exact version is rejected or
blocked before commit. The runtime never silently re-resolves `latest` and
retries against changed state.

### 10.4 Missing evidence

Where evidence is a precondition, an unavailable required body or hash mismatch
blocks or rejects the command according to the owning policy. The runtime
preserves the attempted command result and does not falsely label declared-only
hashes as content verified.

### 10.5 Consumer failure

The publisher's already committed output remains authoritative if a later
consumer command fails. The failed consumer result is observable. The consumer
does not roll back or rewrite the publisher's state.

## 11. Rejection Matrix

| Boundary | Required rejection or block |
|---|---|
| Candidate contract unsupported | G-02 unsupported or quarantined; no G-01. |
| Duplicate event identity with different bytes | Reject identity conflict; do not replace prior event. |
| Accounting event offered to I-C03 | Reject input class before posting-rule evaluation. |
| Governance or forecast output offered to I-C03 | Reject input class before posting-rule evaluation. |
| Rule inactive or ineffective for event date | Reject evaluation with exact rule reference. |
| Proposal lines unbalanced or dimensions unresolved | Reject submission; append no accounting event. |
| Close with unresolved submitted proposal | Reject unless a valid explicit deferral already exists. |
| Aegis attempts to create restatement case | Reject cross-owner write. |
| Invalid directive before case construction | G-14 plus command result; no Artifact F subject. |
| Correction constructor routed to posting-rule engine | Reject structural route. |
| Approval violates segregation of duties | Reject approval; proposal remains unchanged. |
| Post into hard-closed target period | Reject posting. |
| Restatement adjustment lacks case identity | Reject posting. |
| Manifest does not reconcile to journal lines | Reject freeze; manifest remains unfrozen. |
| Publication predecessor missing or manifest hash changed | Reject publication. |
| Readiness missing or belongs to different product version | Block controlled Pythia use. |
| Pythia selects implicit latest | Reject query or command. |
| Unapproved decision returned to intake | Reject candidate construction. |
| Approved hiring candidate unsupported by contract registry | G-02 unsupported; no G-01 and no Atlas call. |
| Pythia attempts to approve its own recommendation | Reject cross-owner approval. |
| G-13 source hash does not equal reversal input hash | Reject before reversal-line derivation or comparison. |

## 12. Persistence-Boundary Issues Exposed by Artifact I

Artifact I exposes two questions that Milestone 1 could safely treat as
canonical bootstrap or terminal evidence but a persistent runtime must resolve.

### 12.1 Proposal identity and lifecycle

Artifact I exposes one unresolved persistence question that Milestone 1 did not
need to settle.

Artifact C describes a `journal_proposal` as a frozen, versioned treatment.
Artifact E transitions proposal lifecycle state. Artifact F serialises one
`status` within the proposal payload and the canonical fixtures contain the
terminal status for each treatment version.

Milestone 2 also requires the submitted treatment to remain retrievable before
it becomes deferred, approved, or posted. It must not overwrite bytes under the
same fully qualified proposal reference while claiming that reference is
immutable.

Before persistence schema design, the next artifact must decide whether:

1. frozen proposal treatment content and lifecycle projection are represented
   separately, with Artifact F payloads published as exact state-specific views;
2. every lifecycle state is an immutable snapshot with a distinct snapshot
   identity while retaining one treatment-version identity; or
3. another representation can satisfy exact-reference immutability, Artifact E
   transitions, and canonical Artifact F byte compatibility without adding a
   tenth accounting object.

Artifact I does not choose silently. Any choice must prove:

- the submitted state remains independently reconstructable;
- exact cross-module references never change meaning;
- canonical terminal payload bytes remain unchanged;
- proposal content is not duplicated under competing owners; and
- current-state projection can be deleted and rebuilt.

This is a ratification blocker for the persistence artifact, not for defining
the application sequence.

### 12.2 Predecessor reporting-version bootstrap and time

C-001 requires the original reporting version as the population Argus tests and
as the predecessor that the restated version supersedes. Artifact F does not
contain the original `reporting_version.published` event; the predecessor is
declared bootstrap state.

The parameterised application sequence also begins before the affected period
is hard-closed. A persistent runtime therefore cannot honestly claim that the
same sequence created the predecessor reporting version. It also cannot import
an Artifact F reporting version silently, because reporting versions are created
only through publication and every authoritative claim requires provenance.

Before persistence schema design, the next artifact must decide whether:

1. Milestone 2 begins with a separately evidenced pre-scope publication import
   whose original publication occurred outside the bounded event trace;
2. the executable boundary begins after original publication and treats the
   earlier proposal/close chain as imported history, reducing what the runtime
   itself executes; or
3. the accounting-event boundary must be deliberately expanded through a new
   design decision to represent original publication.

Artifact I recommends option 1 for further design because it preserves the
eleven-event canonical trace and still allows the full application sequence to
execute. That import must remain visibly pre-scope, carry immutable provenance,
be unavailable to controlled consumers before its declared publication point,
and never masquerade as an event produced by the Milestone 2 run.

The next artifact must prove that:

- predecessor v1 has a real publication basis and immutable content identity;
- its availability is temporally consistent with hard close;
- its import cannot be replayed as a second publication effect;
- successor v2 references the exact imported predecessor;
- canonical v1 bytes remain unchanged; and
- no fabricated accounting event is added to the eleven-event C-001 trace.

This is also a ratification blocker for the persistence artifact, not for the
application sequence.

## 13. CT-1 Reconciliation

Artifact I is centred on C-001, but its application boundary must also support
CT-1 without special ownership rules.

### Shared commands

CT-1 reuses:

- I-C04 `SubmitJournalProposal`;
- I-C14 `ApproveJournalProposal`;
- I-C15 `PostJournalProposal`;
- I-C09 review and issue governance;
- I-C11 directive publication;
- I-Q06, I-Q08 through I-Q12, I-Q18, I-Q19, and I-Q20.

### CT-1-specific application commands

CT-1 needs seven case-specific application commands, including two typed
construction commands under the existing `ConstructCorrectionProposal` domain
planner command:

- `ReconcileCashApplicationIdentity`, owned by Hermes, publishing the exact
  customer-identity G-03 reconciliation before assurance testing;
- `RunCashApplicationIdentityTest`, publishing the CT-1 G-07 exception;
- `ApplyOpenPeriodCorrectionDirective`, validating the exact G-09 authority;
- `ConstructReversalProposal`, first proving the G-13 projection source hash
  equals the declared reversal input hash, then and only then deriving and
  comparing the equal-and-opposite reversal lines;
- `ConstructReplacementProposal`, consuming the same incorrect journal identity
  and exact G-09 directive; and
- `VerifyCashApplicationCorrection`, publishing the CT-1 G-07 verification; and
- `UpdateCashApplicationIssue`, owned by Aegis, consuming that exact
  verification and publishing the successor issue through G-08.

The reversal and replacement construction commands are correction constructors,
not posting-rule evaluation. The Hermes reconciliation, Argus assurance, and
Aegis governance commands are typed non-lifecycle operations owned by their
respective modules; none may invoke the business-event posting engine.

`ReconcileCashApplicationIdentity` uses the ordinary command boundary. It reads
the exact receipt and application parties plus the canonical party mapping, then
atomically commits one Hermes reconciliation version, G-03 publication, and
command result. `RunCashApplicationIdentityTest` cannot begin without that exact
G-03 publication.

`UpdateCashApplicationIssue` also uses the ordinary command boundary. It reads
the exact prior issue and G-07 verification, then atomically commits one
successor Aegis issue version, G-08 `ISSUE_UPDATED` publication, and command
result. Verification alone never mutates or closes the issue.

### Required differences

- J-010 remains non-authored G-13 state;
- the target period remains open;
- Hermes publishes exact G-03 identity reconciliation before Argus testing;
- reversal and replacement are separate proposal and posting command sequences;
- Aegis publishes the successor G-08 issue state after Argus verification;
- there is no restatement case, manifest, or reporting publication;
- there is no G-10, G-11, G-12, or approved-decision return; and
- Atlas remains the only accounting writer.

This confirms that Artifact I defines one application boundary without forcing
every canonical case through every module.

## 14. Acceptance Criteria

Ratification establishes that all of the following hold.

- I-A01: every application command has exactly one authoritative target owner;
- I-A02: each accepted command commits one complete local transaction or none;
- I-A03: for each parameterised C-001 execution, its one admitted
  `accounting.recognition.due` business event is the only input that invokes
  posting-rule evaluation;
- I-A04: correction construction uses a separate typed path with no accounting
  event until submission;
- I-A05: each parameterised C-001 execution produces exactly the eleven ratified
  Artifact F accounting-event variants in canonical causal order through the
  listed Atlas commands;
- I-A06: Aegis publishes authority while Atlas alone creates and transitions the
  restatement case;
- I-A07: invalid pre-construction authority terminates through G-14 without an
  Artifact F subject;
- I-A08: the hard-closed affected period is never reopened or used as the
  correction ledger period;
- I-A09: predecessor and successor reporting versions remain independently
  retrievable;
- I-A10: Argus verification precedes successor readiness approval;
- I-A11: Pythia freezes exact matching G-06 and G-10 references before G-12;
- I-A12: the approved decision returns to candidate intake without directly
  writing a business event or accounting state;
- I-A13: the unsupported hiring candidate produces G-02 but no G-01 in
  Milestone 2;
- I-A14: durable G contract publications arise from actual owner commands;
- I-A15: boundary observations arise from actual publish and consume calls and
  remain removable without changing outcomes;
- I-A16: no query grants mutation authority or resolves implicit latest for a
  controlled use;
- I-A17: duplicate delivery, stale version, effect idempotency, and consumer
  failure follow section 10;
- I-A18: CT-1 reuses the same application boundary without acquiring restatement
  or Pythia work for symmetry;
- I-A19: both persistence-boundary issues in section 12 are carried as blocking
  inputs to the next artifact, and no physical schema is ratified first; and
- I-A20: no database schema, API route, UI workflow, event broker, or generic
  orchestration framework is smuggled into the application contract;
- I-A21: CT-1 binds the exact G-13 projection source hash to the declared
  reversal input hash before deriving or comparing reversal lines; and
- I-A22: Pythia cannot approve its own recommendation; operational approval and
  candidate meaning remain owned by the source business domain;
- I-A23: CT-1 consumes an exact Hermes G-03 customer-identity reconciliation
  before Argus publishes its G-07 exception; and
- I-A24: CT-1 ends only after Aegis consumes the exact Argus verification and
  publishes a successor issue version through G-08.

## 15. Decisions Still Open

Artifact I intentionally leaves these decisions for the next design step:

This list records Artifact I's original handoff state. Artifacts J through N now
resolve items 1 through 8. The current v0.2.2 sequence uses J's immutable
treatment plus event-derived lifecycle representation and its bounded pre-scope
reporting import; the historical questions below are not current implementation
choices.

1. proposal treatment identity versus lifecycle-state representation;
2. predecessor reporting-version import, provenance, and availability time;
3. exact minimum internal bodies for G-02, G-03, G-07 through G-12, and approved
   decision records;
4. the durable representation of a G contract publication;
5. which G publications require retained consumption acknowledgements;
6. candidate receipt identity and deduplication basis before G-02;
7. how deterministic clock and identity allocation enter commands;
8. the exact current-state version used for stale-write detection;
9. whether unsupported decision candidates are `REJECTED` or `QUARANTINED` in
   the minimum Hermes vocabulary; and
10. which evidence bodies beyond the two reporting proofs must be committed for
   Milestone 2 acceptance.

Database product, table layout, indexes, migration tooling, API protocols, and
UI concerns remain outside Artifact I.

## 16. Recommended Next Artifact

The next artifact should resolve authoritative records and rebuildable
projections before a database is selected.

It must begin with both persistence-boundary issues in section 12, then map each
I-S01 through I-S26 write set to:

- immutable authoritative input records;
- immutable authoritative outcome records;
- lifecycle or current-state projections;
- exact rebuild sources;
- uniqueness and concurrency constraints; and
- semantic digests used for clean-start, restart, and rebuild equivalence.

Only after that map passes C-001 and CT-1 should the project compare storage
engines or draft a physical schema.
