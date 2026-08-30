# Artifact O - Public Product Layer and Flagship Journey Contract

Status: Design v0.2 - ratified 2026-08-10

## 0. Purpose and Closure Rule

Artifact O defines the first public product boundary over the ratified Finance &
Assurance Platform runtime.

Milestone 2 proved that parameterised business events can pass through Hermes,
Atlas, Argus, Aegis, and Pythia; that the resulting authority survives restart
and rebuild; and that an exact reporting value can be traced to its source and
evidence. Artifact O decides how a public user may understand that result
without exposing persistence internals or moving finance logic into a browser.

The product layer is closed only when it defines:

- one public application with five module lenses;
- one deterministic synthetic demo workspace;
- three complete flagship journeys and one supporting correction proof;
- the finite public query and view-model registry needed by those journeys;
- the boundary between public reads and out-of-band demo lifecycle operations;
- the minimum navigation, interaction, accessibility, and failure semantics;
- a zero-paid-service baseline that works without runtime network access;
- a phased implementation and cohesion-audit sequence; and
- executable acceptance criteria for the public product layer.

Artifact O does not define a new accounting object, business event, accounting
event, module product, posting rule, assurance test, governance workflow, or
planning model. Its `O-V*` values are derived presentation views. They are not
authoritative records and cannot be consumed by the accounting or module
engines.

The hard closure rule is:

> A fresh clone must be able to materialise the bounded synthetic demo, serve
> all public journeys, and reproduce their governed claims without paid API
> keys, private credentials, external datasets, hosted infrastructure, direct
> database reads, or client-side financial inference.

## 1. Binding Sources

Artifact O is governed by:

- the product thesis and five invariants in `AGENTS.md`;
- canonical transactions C-001 and CT-1;
- Artifact C - Accounting Object Model;
- Artifact E v0.2.1 - Accounting State Machines and Command/Event Matrix;
- Artifact F v0.2.1 - Minimum Payload Contracts;
- Artifact G v0.2 - Module Ownership and Contract Map;
- Artifact H v0.3.1 - Executable Validation Harness Specification;
- Artifact I v0.2.2 - Runtime Application Boundary;
- Artifact J v0.2 - Authoritative Record and Projection Map;
- Artifact K v0.2.2 - Persistence Port and Transactional Unit of Work;
- Artifact L v0.2.1 - Internal Runtime Message Contracts;
- Artifact M v0.2.1 - Deterministic Authority Ports;
- Artifact N v0.2.1 - Persisted Contract Compatibility;
- the passed Milestone 2 Phase 7 acceptance boundary; and
- ADR-001 through ADR-032.

Where a public view conflicts with an exact runtime record, Artifact G contract,
purpose-specific readiness assessment, or verified evidence state, the public
view is wrong. Presentation convenience never overrides upstream authority.

## 2. Product Thesis and Audience

The public product demonstrates one proposition:

> Enterprise financial information is useful only when its origin, accounting
> treatment, assurance state, governance basis, and permitted decision use can
> be shown together.

The primary audience is a hiring manager, finance professional, auditor, or
technical reviewer evaluating the platform as a portfolio project. The product
must let that user understand its value within minutes, while preserving enough
depth to inspect the exact architecture claim.

The public experience must answer four questions:

1. What happened financially?
2. Can the reported result be trusted, and for what purpose?
3. What failed, who governed the correction, and what history was preserved?
4. How did the governed result affect a forward-looking decision?

The mythological module names remain product lenses, not separate products:

| Lens | Public question | Authoritative responsibility remains with |
|---|---|---|
| Hermes | Where did the information come from, and did the sources reconcile? | Existing Hermes products and G-01 to G-03 contracts |
| Atlas | What was recorded, reported, corrected, and republished? | Existing accounting records and G-04 to G-06 contracts |
| Argus | What test failed, and what evidence supports the exception? | Existing assurance products and G-07 contract |
| Aegis | What was concluded, remediated, and approved for use? | Existing governance products and G-08 to G-10 contracts |
| Pythia | Which governed inputs were frozen, and what decision followed? | Existing planning products and G-11 to G-12 contracts |

## 3. Vocabulary

### 3.1 Public product layer

The transport, derived view models, application shell, and user journeys placed
over the existing runtime application ports. It owns presentation semantics
only.

### 3.2 Demo workspace

A disposable SQLite workspace created from ratified baseline configuration and
parameterised synthetic scenario inputs through ordinary runtime boundaries.
It is not a fixture reader disguised as a product database.

### 3.3 Demo manifest

A derived declaration of the scenario families, semantic time, runtime release,
database state, expected proof capabilities, and synthetic-data notice exposed
by one materialised demo workspace.

### 3.4 Public query

A read-only application operation returning one finite `O-V*` view from one
revision-pinned query session. It is not a generic J-AR record browser.

### 3.5 Public view model

A typed, non-authoritative projection assembled from exact records and labelled
runtime projections. It carries the source identities and query revision needed
to explain its claims.

### 3.6 Flagship journey

A bounded sequence of public queries and screens that proves one platform
claim from authoritative runtime state. A journey is not a scripted animation
or a static narrative fixture.

### 3.7 Deterministic narrative

Short explanatory text selected from version-controlled templates using closed
statuses already present in the view. It is not generated by an LLM and may not
introduce a conclusion absent from the underlying records.

## 4. Rulings

### O-R01 - One public application retains five lenses

The public product is one application shell over one shared substrate. Hermes,
Atlas, Argus, Aegis, and Pythia are navigation and ownership lenses. They do not
receive separate databases, authentication systems, deployments, or competing
copies of authoritative state.

### O-R02 - The product layer is never authoritative

No `O-V*` view, browser state, URL, cache, or formatted value may become a
posting input, control result, readiness assessment, or planning authority.
Every product-layer claim is derived from ratified J-AR records, J-P labelled
projections, and Artifact G publications.

### O-R03 - The public browser surface is read-only

The baseline browser application exposes queries and navigation only. It does
not expose domain commands, arbitrary uploads, approvals, corrections, scenario
edits, SQL, or generic record mutation. This permits an honest no-authentication
public demo over synthetic data.

### O-R04 - Demo lifecycle operations are operational and finite

Initialise, recreate, and verify are the only Artifact O demo lifecycle
operations. They are invoked at startup or through local developer tooling,
not through public HTTP routes. Rebuild replaces only the disposable demo
workspace and never issues domain deletes against authoritative records.

### O-R05 - Demo state is produced through ordinary runtime paths

The demo initializer installs the ratified runtime baseline and executes the
parameterised C-001 and CT-1 families through the existing application,
publication, and persistence boundaries. It may not copy terminal tables,
import validation fixtures as operational state, or mutate SQLite directly.

### O-R06 - The baseline has zero paid-service dependency

A fresh clone must demonstrate every Artifact O journey without an OpenAI or
other LLM API, paid market-data API, hosted database, external identity provider,
analytics service, or private credential. After dependencies are installed, the
running demo requires no network connection.

External adapters may be designed later, but they can never be required for the
baseline portfolio proof.

### O-R07 - All business data is visibly synthetic

Every public screen identifies the company and transactions as synthetic. Demo
names, documents, identifiers, and evidence must contain no real client,
employer, engagement, employee, bank, or personal data.

### O-R08 - Public reads use application ports only

The product query service may call the existing runtime query boundary and
bounded product assemblers. The HTTP adapter and UI may not query SQLite,
repository implementations, validation fixtures, H-layer reports, or internal
tables directly.

### O-R09 - One request uses one pinned semantic view

Every public query opens one revision-pinned runtime query session with an
explicit semantic-as-of time. All records contributing to one response must
come from that session. A response must not mix revisions or silently advance
to a newer current projection during assembly.

### O-R10 - Public contracts are purpose-built, not generic records

Artifact O exposes only the finite `O-Q*` queries and `O-V*` views required by
the flagship and supporting journeys. It does not expose generic J-AR family
lookup, arbitrary module-product search, unrestricted graph traversal, or raw
database browsing as a public API.

Exact internal identities remain visible as traceability metadata where useful,
but internal payload shape is not itself the public contract.

### O-R11 - As-was and as-restated history remain simultaneous

Atlas views must present June v1 and June v2 as distinct immutable reporting
versions. The UI may label the latest applicable version only when the exact
version is also shown; it may never replace, hide, or rewrite the predecessor.

### O-R12 - Readiness is exact and purpose-specific

No view may show a reporting result as generally trusted. Readiness is displayed
against the exact reporting-version, purpose, period, and scope tuple. Pythia
views may show controlled use only when the exact approved readiness record
bound to their planning input is present.

### O-R13 - Traceability is directed and evidence-gated

A statement-value trace is exposed only through the existing directed J-P11
logic and only when the reporting content bytes are verified. The product layer
may group or label nodes for readability, but it may not infer missing edges,
join on coincidental dimensions, or fabricate a complete chain.

### O-R14 - Evidence status is stated honestly

`CONTENT_BYTES_VERIFIED`, `DECLARED_HASH_ONLY`, missing evidence, and unavailable
evidence remain visibly distinct. A hash string alone is not described as
content verification. A view must fail or degrade explicitly when its claim
requires a stronger evidence state than is available.

### O-R15 - The client formats finance values but does not calculate them

Accounting balances, restatement bridges, readiness results, risk conclusions,
and decision effects are computed server-side from existing runtime authority.
The client may format integer minor units with an ISO-4217 currency, calculate
layout-only percentages supplied by the server, and filter already returned
display rows. It may not reconstruct journals, net adjustments, infer readiness,
or recalculate a financial statement.

### O-R16 - Module ownership remains visible

Every view states which module published the underlying conclusion and which
upstream module products it consumed. Shared presentation does not blur the
difference between a Hermes reconciliation, Argus exception, Aegis issue, Atlas
reporting version, and Pythia decision.

### O-R17 - Narrative is deterministic and bounded

Human-readable summaries come from versioned templates keyed only by closed
view states. The template identifier is testable. No AI-generated commentary,
free-form recommendation engine, or non-deterministic prose is part of the
baseline.

### O-R18 - The product never guesses `latest`

URLs and query inputs carry exact versioned references where history matters.
Any convenience link labelled current or latest is resolved server-side from a
labelled runtime projection and returns the exact selected identity. Absence or
ambiguity fails visibly.

### O-R19 - Failure states are product states

Not bootstrapped, not found, unavailable, unverified content, revision conflict,
unsupported persisted contract, and internal trace break are distinct public
outcomes. The application may explain them, but must not convert them into zero,
empty, approved, or successful values.

### O-R20 - The interface is an operational finance product

The first screen is a working platform overview, not a marketing hero. The
visual system prioritises hierarchy, comparison, auditability, and dense but
readable financial information. Status is never communicated by colour alone;
keyboard navigation, visible focus, semantic headings, table labelling, and
reduced-motion support are baseline requirements.

### O-R21 - Local reproducibility is the deployment floor

Local execution from a fresh clone is the authoritative deployment proof. A
hosted public instance, container, or static portfolio wrapper may be added,
but cannot weaken local reproducibility or become required to exercise the
journeys. SQLite remains behind the persistence port and no hosted database is
introduced by Artifact O.

### O-R22 - C-001 leads; CT-1 remains visibly proven

The three flagship journeys use C-001 because it alone proves the complete
platform loop through Pythia. CT-1 remains a supporting correction-integrity
journey showing reversal, replacement, exact source-hash binding, and zero net
control-account movement. CT-1 does not acquire readiness or planning output
for symmetry.

### O-R23 - Public compatibility reads are exact-original only

Artifact O version 1 public queries resolve authoritative inputs only through
Artifact N `EXACT_ORIGINAL` read mode. They may not consume a `TYPED_TARGET`
adapted view as if it were original authority.

A future public view that intentionally presents an adapted read requires an
explicit successor `O-V*` contract version, a visible compatibility label, and
an append-only architecture decision before exposure. An adapted view remains
derived and non-authoritative even after public-contract approval.

## 5. Demo Workspace Contract

### 5.1 Closed scenario set

Artifact O materialises exactly two scenario families:

| Scenario ref | Canonical family | Public role |
|---|---|---|
| `DEMO-C001-RESTATEMENT@v1` | C-001 | Complete source-to-decision flagship story |
| `DEMO-CT1-CORRECTION@v1` | CT-1 | Supporting reversal-and-replacement integrity proof |

These are parameterised runtime executions, not direct copies of the Artifact F
fixture corpus. Canonical identifiers may be retained in the first public demo
for recognition, but no application branch may depend on those literals.

### 5.2 Demo manifest

The demo manifest contains only:

```text
demo_contract_version
workspace_ref
runtime_release
semantic_as_of_time
synthetic_data_notice
scenario_refs[]
scenario_statuses[]
scenario_entry_points[]
authoritative_inventory_digest
projection_generation_ref
available_journeys[]
```

The manifest does not claim that every evidence body is locally available. It
describes capability, not readiness or financial truth.

Each `scenario_entry_points[]` member binds one semantic public role, such as
`reporting_history`, `recognition_reconciliation`, `governance_issue`,
`governed_decision`, or `correction_verification`, to the exact reference
returned by the executed scenario. This index is derived and rebuildable. It
must be captured from ordinary command results and publications, never filled
from canonical literal IDs or treated as business authority.

### 5.3 Demo lifecycle operations

| ID | Operation | Input | Required result |
|---|---|---|---|
| O-C01 | `InitialisePublicDemo` | Empty workspace target plus exact baseline and scenario descriptors | One valid demo workspace produced through runtime ports; fails if the target already contains unrecognised state |
| O-C02 | `RecreatePublicDemo` | Existing disposable demo workspace plus the same exact descriptors | Replacement workspace with the same semantic inventory and journey results; old workspace is never partially overwritten |
| O-C03 | `VerifyPublicDemo` | Workspace ref plus expected scenario and contract coordinates | Read-only verification report covering compatibility preflight, scenario presence, exact view availability, and semantic digests |

O-C01 and O-C02 are developer/startup operations. They are not Artifact I
domain commands and produce no new business or accounting event type. O-C03 is
read-only.

### 5.4 Reproducibility

Given identical ratified inputs and runtime versions:

```text
clean initialisation result
= full demo recreation result
= restart result
= projection rebuild result
```

Equality is semantic. Disposable workspace identity, SQLite page layout, file
path, transport port, and response timing are excluded. Authoritative identity,
semantic hashes, reporting content, readiness binding, decision output, and
trace graph are included.

## 6. Public Query Envelope

Every successful `O-Q*` response has this logical envelope:

```text
view_contract
view_contract_version
scenario_ref
semantic_as_of_time
query_revision
compatibility_read_mode
data
source_refs[]
```

Rules:

- `view_contract` is one exact `O-V*` identifier;
- `view_contract_version` is explicit and never inferred as latest;
- `query_revision` identifies the pinned runtime read used for the response;
- `compatibility_read_mode` is the constant `EXACT_ORIGINAL` in Artifact O;
- `data` contains only fields permitted by the selected `O-V*` contract;
- `source_refs` is a sorted, unique list of exact authoritative or labelled
  projection references actually consumed; and
- transport metadata such as request ID or response duration remains outside
  the semantic body.

The product query service rejects an unknown field, view discriminator,
scenario reference, or unsupported view version at its own public boundary.
Artifact O does not change Artifact N's persisted contract stamps.

### 6.1 Public scalar and strictness conventions

- `view_contract_version` is the positive integer constant `1` in Artifact O;
- `demo_contract_version` is the positive integer constant `1`;
- identifiers and references are non-empty strings and remain case-sensitive;
- money is an integer minor-unit value plus ISO-4217 currency;
- dates and timestamps retain the existing runtime formats;
- object fields are closed and unknown fields fail validation;
- variant-only fields are absent outside their variant rather than emitted as
  misleading nulls; and
- arrays whose order has no business meaning are returned in a documented,
  deterministic order.

A future public view version is a product-contract change. It does not change
the underlying Artifact F, G, L, or J-AR contract merely because its
presentation shape evolves.

### 6.2 Public failure envelope

A failed query returns no success `data` and uses:

```text
error_code
message
scenario_ref
subject_ref
query_revision
```

The closed baseline error codes are:

```text
DEMO_NOT_INITIALISED
NOT_FOUND
UNAVAILABLE
UNVERIFIED_CONTENT
REVISION_CONFLICT
UNSUPPORTED_CONTRACT
TRACE_INTEGRITY_FAILURE
INTERNAL_FAILURE
```

`query_revision` is present only when a runtime query session was opened. It is
absent for `DEMO_NOT_INITIALISED` and startup compatibility failure.

`query_revision` is present only when a runtime query session was opened. It is
absent for `DEMO_NOT_INITIALISED` and startup compatibility failure.

`message` is safe, deterministic explanatory text. Internal paths, SQL, stack
traces, credentials, and arbitrary exception strings never enter the public
response.

## 7. Finite Public Query and View Registry

The registry is closed for Artifact O. Each query returns the correspondingly
numbered view.

| Query | View | Purpose | Minimum authoritative basis |
|---|---|---|---|
| O-Q01 `GetDemoManifest` | O-V01 `DemoManifestView` | Establish scope, synthetic status, and reproducibility | Demo lifecycle verification plus runtime inventory digest |
| O-Q02 `GetPlatformOverview` | O-V02 `PlatformOverviewView` | Summarise the complete platform loop without replacing module detail | Exact scenario entry points, selected C-001 G-02/G-03/G-06/G-07/G-08/G-10/G-11/G-12 products, and exact reporting history |
| O-Q03 `GetSourceReconciliation` | O-V03 `SourceReconciliationView` | Explain source lineage and the exact reconciliation gap | Exact G-03 product/publication plus its recognition-schedule or party-mapping inputs and G-13/J-AR17 where required by the variant |
| O-Q04 `GetReportingHistory` | O-V04 `ReportingHistoryView` | Compare immutable as-was and as-restated versions | Exact J-AR10 history, matching G-06 publications, and J-AR12 content resolution |
| O-Q05 `GetReportingVersion` | O-V05 `ReportingVersionView` | Inspect one exact reporting version and statement content | Exact J-AR10, matching G-06 publication, and exact J-AR12 state |
| O-Q06 `GetAssuranceException` | O-V06 `AssuranceExceptionView` | Show the test, exception, assertion, variant result, and evidence basis | Exact Argus J-AR02 products, G-07, J-AR12 refs, and one derived navigation link from the scenario index |
| O-Q07 `GetGovernanceCase` | O-V07 `GovernanceCaseView` | Show review, finding, issue, remediation, verification, and the exact successor issue state | Exact Aegis/Argus products and G-08/G-09 publications |
| O-Q08 `GetReadinessMatrix` | O-V08 `ReadinessMatrixView` | Show permitted use by exact purpose, product, period, and scope | Exact G-06 and purpose-specific G-10 records |
| O-Q09 `GetGovernedDecision` | O-V09 `GovernedDecisionView` | Show frozen governed inputs, operational approval, returned candidate, and its admission outcome | Exact G-11/G-12, approved G-10/J-AR10, source-domain approval/candidate products, and candidate G-02 |
| O-Q10 `TraceReportingValue` | O-V10 `ReportingValueTraceView` | Trace one verified statement value through authority and evidence | Existing verified content resolution and directed J-P11 result |
| O-Q11 `GetCorrectionIntegrity` | O-V11 `CorrectionIntegrityView` | Prove CT-1 reversal/replacement integrity without extending its scope | Exact G-13, journals/lines, correction products, events, and verification |

### 7.1 O-V01 - DemoManifestView

Required data:

```text
workspace_ref
runtime_release
synthetic_data_notice
scenario_summaries[]
scenario_entry_points[]
authoritative_inventory_digest
projection_generation_ref
verification_status
```

### 7.2 O-V02 - PlatformOverviewView

Required data:

```text
company_label
reporting_period
headline_reporting_version_ref
headline_values[]
module_summaries[]
machine_exception_count
governance_issue_states[]
readiness_summary[]
governed_decision_ref
journey_links[]
```

Every headline value carries amount minor units, currency, exact reporting
version, evidence status, and a trace link. Counts are server-derived from the
closed demo products, not generic production aggregations.

### 7.3 O-V03 - SourceReconciliationView

Required data:

```text
reconciliation_ref
reconciliation_type
scope_ref
performed_at
source_refs[]
reconciliation_status
downstream_exception_ref
```

The view is a strict union selected by `reconciliation_type`.

`RECOGNITION_POPULATION` additionally contains:

```text
period_id
expected_item_count
posted_item_count
submitted_unposted_count
deferred_count
expected_amount_minor
posted_amount_minor
difference_minor
currency
```

`CASH_APPLICATION_IDENTITY` additionally contains:

```text
cash_application_ref
receipt_party_ref
application_party_ref
party_mapping_ref
identity_match
```

Hermes exposes the disagreement. It does not state the accounting correction.

### 7.4 O-V04 - ReportingHistoryView

Required data:

```text
period_id
versions[]
restatement_bridge[]
```

Each version contains its exact reference, publication origin and timestamp,
content verification status, selected statement values, and source publication. The
bridge identifies predecessor, successor, adjustment amount, currency, and
restatement case. It does not net the versions in the client.

### 7.5 O-V05 - ReportingVersionView

Required data:

```text
reporting_version_ref
period_id
version
publication_origin
published_at
statement_values[]
currency
content_ref
content_verification_status
traceable_fields[]
```

The view is a strict union selected by `publication_origin`.

`PRE_SCOPE_IMPORT` additionally contains:

```text
import_attestation_ref
original_authority_ref
source_ref
```

`RESTATEMENT_PUBLICATION` additionally contains:

```text
predecessor_version_ref
restatement_case_ref
manifest_hash
published_by_event_id
```

When content is declaration-only, statement fields whose proof requires bytes
are unavailable rather than silently populated.

### 7.6 O-V06 - AssuranceExceptionView

Required data:

```text
test_run_ref
test_definition_ref
exception_ref
assertion
severity
evidence_refs[]
related_governance_case_ref
```

The view is a strict union selected by `exception_type`.

`RECOGNITION_COMPLETENESS` additionally contains:

```text
subject_refs[]
period_id
expected_amount_minor
actual_amount_minor
difference_minor
currency
```

`CASH_APPLICATION_IDENTITY` additionally contains:

```text
receipt_party_ref
application_party_ref
journal_id
amount_minor
currency
```

The machine observation remains distinct from a finding or issue.

### 7.7 O-V07 - GovernanceCaseView

Required data:

```text
exception_ref
review_ref
review_disposition
finding_ref
initial_issue_ref
initial_issue_status
owner_ref
remediation_directive_ref
correction_refs[]
verification_ref
prior_issue_refs[]
final_issue_ref
final_issue_status
readiness_refs[]
```

The view preserves the chain:

```text
exception
-> review disposition
-> finding
-> issue
-> remediation
-> verification
-> successor issue state
```

The successor may be `REMEDIATION_VERIFIED` or `CLOSED` according to the exact
issue version. The view may not collapse those objects into one generic case
status or imply closure when only verification exists.

### 7.8 O-V08 - ReadinessMatrixView

Required data:

```text
reporting_version_ref
period_id
rows[]
```

Each row contains:

```text
purpose_ref
scope_ref
status
basis_refs[]
limitation_codes[]
assessed_by_ref
readiness_ref
```

Rows for different purposes remain independent. The view never synthesises one
global readiness status.

### 7.9 O-V09 - GovernedDecisionView

Required data:

```text
planning_input_ref
reporting_version_ref
readiness_ref
purpose_ref
scope_ref
frozen_input_refs[]
decision_ref
decision_type
position_ref
original_start_date
recommended_start_date
monthly_cost_minor
currency
reason_code
approval_ref
approval_outcome
candidate_ref
candidate_admission_outcome
```

`candidate_admission_outcome` distinguishes an approved decision returned as a
candidate from an admitted business event. The view must not imply that Pythia
self-admitted its output.

### 7.10 O-V10 - ReportingValueTraceView

Required data:

```text
reporting_version_ref
statement_field
statement_value_minor
currency
content_verification_status
nodes[]
edges[]
```

Each node retains role, record family, record identity, and semantic hash where
available. Each edge retains its directed relationship. Presentation grouping
does not change the graph returned by J-P11.

### 7.11 O-V11 - CorrectionIntegrityView

Required data:

```text
source_projection_ref
source_projection_hash
reversal_proposal_ref
reversal_journal_ref
replacement_proposal_ref
replacement_journal_ref
identity_before
identity_after
reversal_binding_status
journal_balance_results[]
control_account_net_movement_minor
currency
verification_ref
issue_update_ref
```

The view presents the exact Argus verification whose check results prove that
the runtime bound the reversal to the source hash before comparing lines. It
does not rerun or self-certify the assurance test. The displayed numeric
control-account movement is a bounded read-model calculation over exact
immutable journal lines and must agree with the verification's boolean result.

### 7.12 Runtime assembly map

Artifact O does not require a second read engine. The product query facade
composes the existing runtime query service as follows:

| Public query | Existing bounded runtime capability | Permitted Artifact O addition |
|---|---|---|
| `GetDemoManifest` (O-Q01) | Compatibility preflight, inventory digest, and exact query revision | Derived demo-manifest reader over the sealed scenario entry-point index |
| `GetPlatformOverview` (O-Q02) | Exact module-product, reporting-history, readiness, and decision reads | Bounded overview assembler over exact entry-point refs |
| `GetSourceReconciliation` (O-Q03) | `get_recognition_reconciliation` and exact G-13/J-AR17 reads | Variant-specific reconciliation assembler |
| `GetReportingHistory` (O-Q04) | `get_reporting_history` and `resolve_reporting_content` | Match each exact version to its exact G-06 publication and derive the verified bridge |
| `GetReportingVersion` (O-Q05) | `get_reporting_version` and `resolve_reporting_content` | Match one exact G-06 publication and expose its origin-specific lineage |
| `GetAssuranceException` (O-Q06) | `get_assurance_result` | Resolve the exact test run, exception, evidence refs, and related-case navigation ref |
| `GetGovernanceCase` (O-Q07) | `get_governance_issue`, `get_remediation_directive`, and exact verification reads | Walk only explicit review/finding/issue/directive/verification references |
| `GetReadinessMatrix` (O-Q08) | `get_readiness_assessment` | Resolve the finite readiness refs named by the scenario entry-point index |
| `GetGovernedDecision` (O-Q09) | `get_controlled_planning_input`, `get_governed_decision`, and exact source-domain products | Join only explicit G-11/G-12, approval, candidate, and G-02 references |
| `TraceReportingValue` (O-Q10) | `trace_reporting_value` | Presentation labels and grouping over the unchanged directed graph |
| `GetCorrectionIntegrity` (O-Q11) | `get_journal`, exact G-13/J-AR17 reads, and correction verification | Present the existing bind-before-compare verification and derive only the numeric zero-net display projection |

Any additional runtime query method introduced for this facade must be a
bounded semantic read over the existing revision-pinned query session. It may
not expose repository enumeration, SQLite, a generic latest lookup, or a second
trace algorithm.

### 7.13 Closed nested item shapes

The arrays used by the eleven views are not open JSON bags. Their baseline item
shapes are:

`scenario_summary`:

```text
scenario_ref
canonical_family
status
public_role
entry_point_count
```

`scenario_entry_point`:

```text
journey_id
semantic_role
exact_ref
source_kind
availability
```

`source_kind` is `AUTHORITATIVE_RECORD`, `CONTRACT_PUBLICATION`, or
`LABELLED_PROJECTION`. It does not turn the derived entry-point index into
authority.

`headline_value` and `statement_value`:

```text
field
label
amount_minor
currency
reporting_version_ref
content_verification_status
trace_available
```

`module_summary`:

```text
module
summary_code
primary_product_ref
route
```

`governance_issue_state`:

```text
issue_ref
status
owner_ref
```

`readiness_summary`:

```text
readiness_ref
reporting_version_ref
period_id
purpose_ref
scope_ref
status
basis_refs[]
limitation_codes[]
assessed_by_ref
```

`readiness_row` repeats the matrix's top-level reporting version and period only
by context and therefore contains exactly:

```text
readiness_ref
purpose_ref
scope_ref
status
basis_refs[]
limitation_codes[]
assessed_by_ref
```

`journey_link`:

```text
journey_id
label
route
availability
```

`reporting_version_summary`:

```text
reporting_version_ref
version
publication_origin
published_at
content_verification_status
statement_values[]
```

`restatement_bridge_item`:

```text
predecessor_version_ref
successor_version_ref
statement_field
adjustment_minor
currency
restatement_case_ref
```

`journal_balance_result`:

```text
journal_ref
debits_minor
credits_minor
currency
balanced
```

`trace_node` is the existing J-P11 node shape:

```text
node_ref
role
record_family
record_identity
semantic_hash
```

`semantic_hash` is nullable only for a J-P11 node explicitly labelled as an
external source or evidence reference that has no persisted semantic hash.

`trace_edge` is the existing J-P11 edge shape:

```text
source_ref
target_ref
relationship
```

Arrays of exact refs contain only strings and use the authoritative order when
the upstream contract defines one. Otherwise they are lexically sorted. A view
may omit an entire variant-only field as allowed above; it may not add an
unregistered nested field.

## 8. Flagship Journeys

### O-J01 - Trace a reported number

Claim proved:

> A user can trace the restated June subscription-revenue value from the public
> report to the exact accounting, business-event, source, rule, and evidence
> authority in bounded steps.

Sequence:

```text
O-Q02 Platform overview
-> select June v2 subscription revenue
-> O-Q05 exact reporting version
-> O-Q10 directed reporting-value trace
-> inspect exact source identities and verification state
```

Required visible result:

- June v2 subscription revenue is GBP 10,000;
- the amount is represented as `1000000` minor units plus `GBP` on the public
  boundary;
- reporting content is `CONTENT_BYTES_VERIFIED`;
- the trace includes reporting version, accounting event, journal, proposal,
  posting rule, admitted business event, source reference, and evidence; and
- no missing internal edge is inferred by the product layer.

### O-J02 - Explain a broken quarter and its correction

Claim proved:

> A balanced ledger can still contain an accounting completeness error, and the
> platform preserves both the original report and the governed correction.

Sequence:

```text
O-Q04 June reporting history
-> inspect v1 as-was result
-> O-Q03 Hermes reconciliation gap
-> O-Q06 Argus completeness exception
-> O-Q07 Aegis governance and remediation chain
-> inspect v2 as-restated result
-> O-Q08 purpose-specific readiness
```

Required visible result:

- trial-balance integrity remains passed while recognition completeness fails;
- June v1 and v2 remain separately retrievable;
- the GBP 10,000 adjustment is linked to the restatement case;
- exception, finding, issue, remediation, verification, and the successor issue
  state are not collapsed or overstated as closure;
- the hard-closed June period is not presented as silently reopened; and
- corrected and formally approved-for-use states remain distinct.

### O-J03 - Follow governed truth into a decision

Claim proved:

> Planning consumes an exact reporting version only with its exact approved
> readiness assessment, and a governed decision returns to operations as a new
> candidate rather than recursively entering accounting.

Sequence:

```text
O-Q08 readiness matrix
-> select the approved planning purpose and exact June v2
-> O-Q09 frozen planning input and governed decision
-> inspect the deferred-hire operational effect
-> inspect the returned candidate and its admission status
```

Required visible result:

- the planning input binds June v2 and its matching readiness version;
- predecessor readiness is never substituted;
- the decision defers the bounded synthetic hire and shows the exact GBP 6,500
  monthly cost effect already present in the canonical scenario;
- the approved decision and returned business-event candidate remain distinct;
  and
- no Pythia output re-enters the accounting-event stream.

### O-SJ01 - Prove reversal and replacement integrity

CT-1 is a supporting journey rather than a fourth flagship claim.

Sequence:

```text
O-Q03 customer-identity reconciliation
-> O-Q06 identity exception
-> O-Q07 directive and verified issue update
-> O-Q11 correction-integrity proof
```

Required visible result:

- the prior journal remains referenced-only G-13 state;
- the reversal input is bound to its exact declared source hash before line
  comparison;
- reversal and replacement journals are separately balanced and immutable;
- the corrected customer identity is explicit; and
- combined control-account movement is zero.

## 9. Information Architecture

The baseline route inventory is:

```text
/
/hermes/reconciliation/:productRef
/atlas/reporting/:periodId
/atlas/reporting/:periodId/:versionRef
/argus/exceptions/:exceptionRef
/aegis/cases/:issueRef
/aegis/readiness/:reportingVersionRef
/pythia/decisions/:decisionRef
/trace/reporting/:reportingVersionRef/:statementField
/corrections/:correctionRef
```

The persistent application shell contains:

- a synthetic-data banner;
- scenario identity and semantic-as-of context;
- navigation for Overview, Hermes, Atlas, Argus, Aegis, and Pythia;
- a shared trace entry point;
- exact reference copy/open affordances;
- evidence and readiness legends; and
- a visible local-demo/runtime status indicator.

The route does not carry financial truth independently. On direct navigation,
the server resolves the exact referenced view or returns a typed failure.

## 10. HTTP Transport Boundary

Artifact O requires one versioned read-only JSON transport over the product
query service. Framework choice is deferred, but the semantic route set is:

```text
GET /api/v1/demo
GET /api/v1/overview
GET /api/v1/hermes/reconciliations/{product_ref}
GET /api/v1/atlas/reporting-periods/{period_id}
GET /api/v1/atlas/reporting-versions/{version_ref}
GET /api/v1/argus/exceptions/{exception_ref}
GET /api/v1/aegis/cases/{issue_ref}
GET /api/v1/aegis/readiness/{reporting_version_ref}
GET /api/v1/pythia/decisions/{decision_ref}
GET /api/v1/traces/reporting-values/{version_ref}/{statement_field}
GET /api/v1/corrections/{verification_ref}
```

Exact purpose and scope parameters required by O-Q08 are explicit query
parameters. They are never inferred from the requesting screen.

The transport may add health and static-asset endpoints, but these are not
product queries. No public `POST`, `PUT`, `PATCH`, or `DELETE` route exists in
the baseline.

The baseline may use `no-store`. If HTTP caching is later enabled, it must vary
by exact route input, view-contract version, scenario, semantic-as-of time, and
query revision. A stale cache may not label itself as a newer reporting or
readiness version.

## 11. Presentation and Interaction Contract

### 11.1 Financial values

- the server supplies integer minor units and ISO-4217 currency;
- the client formats them for display without binary-float accounting maths;
- negatives, zero, unavailable, and not-applicable remain distinct;
- source minor units are inspectable in technical detail views; and
- rounding used only for display is labelled and never changes the exact value.

### 11.2 Status and evidence

- every status has text, not colour alone;
- blocking, review, approved, closed, and unavailable states use a shared legend;
- machine exceptions and human governance conclusions have visibly different
  labels;
- evidence verification state appears beside evidence-dependent claims; and
- purpose-specific readiness appears beside the value or decision that consumes
  it, not only on a separate administration page.

### 11.3 Trace interaction

The trace defaults to a readable ordered path and permits expansion into the
full directed graph. Each node exposes its module role, exact identity, record
family, and semantic hash. External source or evidence nodes are explicitly
labelled as external or declaration-only where applicable.

### 11.4 Accessibility

The baseline must meet WCAG 2.2 AA for the implemented journeys, including:

- keyboard access to navigation, tables, dialogs, and trace inspection;
- visible focus and skip navigation;
- semantic headings, lists, tables, and form labels;
- sufficient contrast in normal, hover, focus, and disabled states;
- non-colour status indicators;
- reduced-motion handling; and
- meaningful loading, empty, and error announcements.

Automated checks are necessary but are not treated as proof of complete WCAG
conformance. Milestone 3 also records manual keyboard, focus-order, zoom,
responsive-reflow, and status-comprehension review for the bounded journeys.

### 11.5 Responsive scope

Desktop is the primary analytical layout. Tablet and mobile must preserve all
claims and navigation, but may convert wide tables and the trace graph into
stacked summaries. Responsive treatment may not hide readiness, evidence state,
exact version identity, or material adjustment values.

## 12. Security, Privacy, and Cost Boundary

The baseline contains:

- synthetic data only;
- no user accounts or authentication flow;
- no secrets in browser bundles or repository history;
- no arbitrary file upload;
- no user-authored HTML, Markdown, SQL, or expression execution;
- no public state-changing route;
- no runtime call to an external network service; and
- no telemetry that requires a third-party account.

Dependency installation may require normal package-registry access. Runtime
operation and all flagship journeys do not.

If a hosted demo is later exposed to the internet, transport hardening, rate
limiting, security headers, dependency scanning, and operational logging are
deployment concerns. They do not authorize authentication, multitenancy, or
mutable public workflows under Artifact O.

## 13. Explicit Non-Goals

Artifact O does not include:

- live ERP, CRM, bank, payroll, or market-data integrations;
- LLM-generated findings, summaries, forecasts, or recommendations;
- paid APIs or hosted-service requirements;
- user registration, login, roles, or multitenancy;
- arbitrary scenario builders or configurable workflow engines;
- uploads, data editing, control authoring, approvals, or remediation entry;
- a generic BI semantic layer or ad hoc report builder;
- a new forecasting algorithm;
- a generic graph database or lineage platform;
- database-per-module, microservices, a broker, or distributed transactions;
- public exposure of generic J-AR reads or SQLite tables;
- production backup, legal hold, disaster recovery, or client-data policy; or
- replacement of the original Atlas repository in place.

These may be considered only after the bounded public product is demonstrably
useful. None is required for portfolio credibility.

## 14. Milestone 3 Build Sequence

### Phase 0 - Ratify the product contract

- critique Artifact O against Artifacts G, I, J, L, N, C-001, and CT-1;
- close every contradiction or implicit public inference;
- ratify the finite query/view registry and flagship journeys; and
- record the accepted product boundary in the decision log.

### Phase 1 - Deterministic demo and product query facade

- implement O-C01 through O-C03;
- materialise both scenario families through ordinary runtime paths;
- implement `O-Q01` through `O-Q11` as in-process product queries;
- validate closed `O-V01` through `O-V11` contracts; and
- prove restart and rebuild parity for every public view.

This phase creates no HTTP server or UI.

### Phase 2 - Read-only HTTP adapter

- expose the finite `/api/v1` route inventory;
- preserve one pinned query revision per response;
- implement closed success and failure envelopes;
- add transport contract, caching, input-validation, and error-safety tests; and
- prove the adapter has no SQLite, validation-fixture, or domain-command access.

### Mandatory post-Phase-2 cohesion audit

Before UI implementation expands the visible surface, conduct a hard audit of:

- public views against their exact runtime sources;
- Artifact N `EXACT_ORIGINAL` enforcement and rejection of `TYPED_TARGET` input;
- route/view/query one-to-one coverage;
- purpose-specific readiness pairing;
- evidence-verification wording;
- as-was/as-restated history;
- public read-only enforcement;
- zero-paid-service and offline-runtime operation; and
- dependency direction from UI to product query service to runtime ports; and
- closure of every blocking item in
  `docs/roadmap/milestone-3-inherited-review-register.md`.

No UI phase starts with an unresolved authority, inference, or contract gap.

### Phase 3 - Application shell and trace journey

- build the shared shell, navigation, synthetic-data disclosure, and legends;
- implement Overview, Atlas reporting version, and Trace views;
- complete O-J01 end to end; and
- establish the accessible visual system with production data shapes.

### Phase 4 - Broken-quarter journey

- implement Hermes reconciliation, reporting history, Argus exception, Aegis
  governance case, and readiness views;
- complete O-J02 end to end; and
- verify that v1 history, v2 restatement, and governance stages remain distinct.

### Phase 5 - Decision and correction journeys

- implement Pythia governed-decision view and complete O-J03;
- implement the CT-1 correction-integrity view and complete O-SJ01; and
- prove that the returned decision candidate and referenced G-13 state preserve
  their non-authoring boundaries.

### Phase 6 - Portfolio hardening

- complete responsive and WCAG 2.2 AA checks for the bounded journeys;
- add loading, unavailable, failure, and direct-route states;
- document local setup, demo reset, architecture, and journey walkthroughs;
- add screenshots or a short deterministic demonstration capture;
- package a local one-command startup; and
- evaluate an optional public host without making it authoritative.

### Phase 7 - Milestone 3 acceptance and audit

- run Milestone 1 H0-H7 and Milestone 2 acceptance unchanged;
- run all Artifact O acceptance checks from a clean checkout;
- reproduce every view after restart and projection rebuild;
- verify offline runtime operation with no credentials;
- conduct the final product/architecture cohesion audit; and
- publish one machine-readable Milestone 3 result.

## 15. Acceptance Criteria

Artifact O may be ratified only when these requirements are unambiguous and
executable. Milestone 3 may close only when its implementation proves that:

- O-A01: one application shell presents five module lenses over one shared
  substrate;
- O-A02: no public view or client state becomes authoritative input;
- O-A03: the baseline browser surface is read-only;
- O-A04: O-C01 through O-C03 are the only demo lifecycle operations and remain
  outside public HTTP;
- O-A05: demo state is produced through ordinary runtime and persistence ports;
- O-A06: all journeys run without paid APIs, private credentials, hosted
  infrastructure, external datasets, or runtime network access;
- O-A07: all displayed business data is explicitly synthetic;
- O-A08: the product query and transport layers cannot access SQLite or
  validation fixtures directly;
- O-A09: one response is assembled from one semantic-as-of time and pinned
  query revision;
- O-A10: the registry contains exactly O-Q01 through O-Q11 and O-V01 through
  O-V11 for the baseline;
- O-A11: June v1 and v2 remain distinct, exact, and simultaneously retrievable;
- O-A12: readiness is shown only for its exact product, purpose, period, and
  scope;
- O-A13: planning controlled use requires the exact approved readiness bound to
  its frozen input;
- O-A14: statement-value trace requires verified content and directed J-P11
  authority;
- O-A15: declaration-only evidence is never labelled content-verified;
- O-A16: the client performs formatting but no accounting, assurance,
  governance, readiness, or planning calculation;
- O-A17: module ownership and consumed upstream products remain visible;
- O-A18: narrative text is deterministic, versioned, and non-generative;
- O-A19: no route, query, or view infers an unspecified latest version;
- O-A20: every closed public failure has a distinct non-success representation;
- O-A21: all financial values preserve integer minor units and currency through
  the public boundary;
- O-A22: O-J01 proves the verified GBP 10,000 June v2 trace in bounded steps;
- O-A23: O-J02 proves the completeness failure, governance chain, immutable v1,
  and v2 restatement without reopening June;
- O-A24: O-J03 proves exact readiness pairing, the governed hiring decision,
  and candidate-versus-admission distinction;
- O-A25: O-SJ01 proves G-13 non-authoring, bind-before-compare reversal,
  balanced correction journals, and zero net control-account movement;
- O-A26: local clean initialisation, restart, and rebuild produce semantically
  identical public views;
- O-A27: direct navigation, loading, unavailable, unverified, not-found, and
  internal-failure states are implemented without false data;
- O-A28: the implemented journeys pass the selected automated accessibility
  checks and a recorded manual review against the stated WCAG 2.2 AA
  interaction baseline;
- O-A29: desktop, tablet, and mobile retain exact version, readiness, evidence,
  and material-value context;
- O-A30: the public repository contains no required secret and emits no runtime
  external-network call in the baseline proof;
- O-A31: Milestone 1 H0-H7 and Milestone 2 acceptance remain unchanged and
  passing; and
- O-A32: one clean-checkout Milestone 3 command verifies the demo, public
  contracts, journeys, automated accessibility checks, offline boundary, and
  deterministic result, while the acceptance record separately identifies the
  required manual accessibility review; and
- O-A33: every Artifact O version-1 response declares `EXACT_ORIGINAL`, and a
  `TYPED_TARGET` adapted read is rejected unless a successor public contract and
  architecture decision explicitly permit it.

## 16. Structural Inventory

Artifact O contains:

- 23 rulings: O-R01 through O-R23;
- 3 demo lifecycle operations: O-C01 through O-C03;
- 11 public queries: O-Q01 through O-Q11;
- 11 public views: O-V01 through O-V11;
- 3 flagship journeys: O-J01 through O-J03;
- 1 supporting journey: O-SJ01; and
- 33 acceptance criteria: O-A01 through O-A33.

These counts are structural checks, not evidence of correctness.

## 17. Decisions Resolved and Deferred

### 17.1 Resolved by Artifact O

- one serious public finance application rather than five products;
- C-001 as the complete flagship loop and CT-1 as a supporting correction proof;
- read-only public operation over a deterministic disposable demo workspace;
- finite product queries and derived public views rather than raw record access;
- exact version, readiness, evidence, and traceability presentation rules;
- exact-original public compatibility reads, with adapted reads requiring an
  explicit successor public contract and architecture decision;
- no client-side finance or governance inference;
- no paid API, credential, hosted database, external dataset, or runtime network
  dependency;
- deterministic templates rather than LLM-generated commentary;
- local reproducibility as the deployment floor;
- a mandatory cohesion audit after the HTTP boundary and before UI expansion;
  and
- a clean-checkout public-product acceptance gate.

### 17.2 Deferred beyond Artifact O

1. frontend framework, component library, and build tool;
2. HTTP framework and process topology;
3. visual tokens, typography, iconography, and final brand treatment;
4. optional public hosting provider and domain;
5. deployment-specific rate limiting, observability, and analytics;
6. user authentication, administration, uploads, and mutable workflows;
7. expanded synthetic company processes beyond C-001 and CT-1;
8. optional external data or AI adapters;
9. production backup, retention, legal hold, and disaster recovery; and
10. any successor `O-V*` public contract version.

The first two choices are implementation decisions to make immediately after
ratification. They must satisfy this artifact but do not alter its product
semantics merely because a particular tool is selected.

## 18. Ratification Review and Next Move

The ratification critique focuses on six possible failure classes:

1. a public view that invents or aggregates a claim not available from the
   current runtime query boundary;
2. a journey that hides the distinction between source, accounting, governed,
   and decision-use truth;
3. a readiness, evidence, history, or traceability label that is stronger than
   its authoritative basis;
4. a demo operation that bypasses the ordinary runtime or quietly becomes a
   public mutation surface; and
5. a product requirement that introduces paid infrastructure or a speculative
   platform capability; and
6. an Artifact N adapted read that is exposed without an explicit successor
   public contract and visible compatibility label.

All six checks pass. Artifact O v0.2 is ratified by ADR-033. Milestone 3
implementation and acceptance are complete under ADR-034.
