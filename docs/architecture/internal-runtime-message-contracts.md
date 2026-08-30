# Artifact L - Internal Runtime Message Contracts and Module-Product Registry

Status: Design v0.2.1 - ratified 2026-08-10

## 0. Purpose and Closure Rule

Artifact L defines the minimum internal runtime-message bodies required by the
parameterised C-001 and CT-1 proofs. It closes three boundaries left open by
Artifact K:

1. the exact bodies carried by G-01 through G-14;
2. the finite J-AR02 `ModuleProductDiscriminatorRegistry`; and
3. the source-domain approved-decision return consumed by I-S26.

This is not a public API, transport schema, event-broker design, generic message
framework, or physical persistence model. The contracts describe semantic
bytes inside one modular monolith. A later adapter may store those bytes inline
or behind an immutable content reference, but it must reproduce the same bytes
and hashes.

Artifact L is closed when:

- every G contract has one exact version-1 body or a direct binding to an
  already-ratified Artifact F body;
- every J-AR02 product instantiated by C-001 or CT-1 resolves through one of the
  finite descriptors in section 7;
- every descriptor identifies one owner, validator, persistence mode, and
  eligibility treatment;
- the approved-decision return binds exact G-12, approval, and candidate
  versions without inventing G-15;
- a strict serializer rejects unknown fields, variants, discriminators, and
  contract versions; and
- C-001 and CT-1 can be traced using only the bodies and registry entries in
  this document.

The v0.1 critique found two inherited CT-1 sequencing contradictions. The
ratified Artifact I v0.2.2 and Artifact K v0.2.2 amendments now represent both
through ordinary owner commands and the shared unit-of-work boundary. Section
12 proves the reconciled sequence without expanding the payload set.

The v0.2.1 conformance amendment closes the independent end-to-end review. It
corrects the G-02 consumer map and stale prose, admits L-MP01/L-MP02 only as
registered J-AR02 products alongside a manifest-bound J-P04 projection, makes
cross-family references closed structured values, and requires every exact
reference to resolve at its semantic time. Declaration-only evidence remains a
real exact J-AR12 declaration and is never upgraded to content-byte verified.
All applicable section 10 bindings now run before commit and again during
projection rebuild.

## 1. Binding Sources

Artifact L is subordinate to:

- the five invariants and architecture rules in `AGENTS.md`;
- Artifact C - Accounting Object Model;
- Artifact E v0.2.1 - Accounting State Machines and Command/Event Matrix;
- Artifact F v0.2.1 - Minimum Payload Contracts;
- Artifact G v0.2 - Module Ownership and Contract Map;
- Artifact H v0.3.1 - Executable Validation Harness Specification;
- Artifact I v0.2.2 - Runtime Application Boundary;
- Artifact J v0.2 - Authoritative Records and Rebuildable Projections;
- Artifact K v0.2.2 - Persistence Port and Transactional
  Unit-of-Work Contract;
- canonical transactions C-001 and CT-1; and
- ADR-003 through ADR-031.

Artifact F remains authoritative for its nine object contracts, ten distinct
accounting-event contracts, and referenced-journal proof projection. Artifact L
does not add, rename, default, or reinterpret any Artifact F field.

Canonical identities, amounts, dates, parties, and periods are proof examples.
Validation and routing use supplied discriminators and exact references and must
not branch on C-001, CT-1, P-551, RC-001, J-010, Orion, Vega, or the canonical
period pair.

## 2. Rulings

### L-R01 - Internal messages are semantic contracts

G messages are in-process immutable values committed as J-AR13 publications.
They are not HTTP requests, queue records, database rows, or user-interface
models. A transport added later must adapt to these contracts rather than
changing their meaning.

### L-R02 - Semantic and body versions remain distinct

Every G publication declares:

```text
g_contract_version = G-v0.2
body_contract_version = 1
canonicalization_version = SORTED_KEYS_COMPACT_UTF8_V1
```

`g_contract_version` identifies the ratified Artifact G ownership contract.
`body_contract_version` selects one strict body in this artifact or Artifact F.
Changing either version changes the command input digest and publication
identity treatment.

### L-R03 - One exact publication envelope carries closed bodies

All G publications use the J-AR13 envelope in section 4. The shared envelope
does not make unrelated bodies interchangeable. `contract_id` plus
`body_discriminator` selects exactly one section 6 body and rejects fields
belonging to another contract or variant.

### L-R04 - Canonical content is logical, not physical

The publication and module-product contracts contain logically resolvable
canonical bytes. An adapter may store those bytes inline or through an immutable
content reference, but an exact read must resolve the bytes and reproduce the
declared hash without external redelivery.

### L-R05 - References are exact and availability-gated

Every upstream contract, authoritative record, configuration, product, and
state reference is exact. No message contains an unqualified family reference
or asks a consumer to select `latest`. A reference unavailable at the command's
semantic as-of time is not a valid input.

### L-R06 - J-AR02 is a finite discriminated family

J-AR02 accepts only the twenty descriptors in section 7. Adding a descriptor,
body variant, or contract version is an architecture contract change. Raw JSON,
unknown discriminators, and owner assertions do not produce a
`ValidatedModuleProduct`.

### L-R07 - Baseline and command output are mutually exclusive

Only the recognition schedule and party-identity mapping descriptors are
baseline eligible. They are not command-output eligible. Every other J-AR02
descriptor is command-output eligible and cannot enter through runtime-baseline
admission.

### L-R08 - G-01 remains the posting-engine firewall

G-01 carries exactly an admitted Artifact F version-1 `business_event` with
`event_type = accounting.recognition.due`. A candidate, admission result,
accounting event, reconciliation, exception, directive, readiness assessment,
forecast, decision, or command disposition cannot satisfy its body contract.

### L-R09 - G-04 and G-05 reuse Artifact F exactly

G-04 carries one exact Artifact F accounting-object view per publication. G-05
carries one exact Artifact F accounting-event body. Artifact L adds no wrapper
inside either payload. A command may atomically publish more than one G-04
record, but each record retains one exact product identity and state token.

### L-R10 - G-06 describes publication without self-readiness

G-06 carries one exact reporting-version product and its content identity,
publication origin, and lineage. It contains no readiness status. Imported and
restatement-published variants remain distinct and closed.

### L-R11 - Assurance and governance products remain separate

G-07 references an Argus test run plus exception, or one Argus verification.
G-08 references Aegis review, finding, and issue products. An exception cannot
stand in for a finding, an issue cannot rewrite an exception, and verification
does not close an issue without a later Aegis command.

### L-R12 - Readiness is exact and purpose-specific

G-10 identifies one reporting version, its exact G-06 publication, one purpose,
one period, and one scope. Version 1 permits only `BLOCKED` and `APPROVED`, the
two outcomes instantiated by C-001. Missing, stale, or mismatched readiness is
not approval.

### L-R13 - G-11 freezes; G-12 decides

G-11 freezes exact G-06, G-10, assumption, and exclusion references. G-12 binds
one decision only to that frozen snapshot. Pythia cannot change actuals,
readiness, or operational approval through either body.

### L-R14 - Operational approval is not a G contract

The source business domain publishes no G-15. I-S25 creates exact J-AR02
approval and candidate versions. The direct `ApprovedDecisionReturn` in section
9 binds those versions to G-12 and is consumed by normal candidate intake.

### L-R15 - An approved candidate is not an admitted event

The source-domain `workforce.hiring.deferred` candidate remains J-AR02 until
Hermes assesses it. Artifact F does not support that event type in Milestone 2,
so I-S26 produces G-02 `UNSUPPORTED`, no G-01, and no Atlas invocation.

### L-R16 - G-13 remains non-authoring referenced state

G-13 carries the exact parameterised form of Artifact F's read-only
`referenced_journal_projection`. Its publication binds J-AR17 and its source
hash. It cannot be persisted as J-AR08, emitted by an Artifact F domain
serializer, or treated as G-04/G-05.

### L-R17 - G-14 is rejection-only in Milestone 2

Artifact G permits a broader disposition vocabulary, but the bounded runtime
instantiates only pre-construction `REJECTED`. Accepted commands terminate
through J-AR14 and ordinary owner outputs. Invariant failures create no
fabricated G-14 result.

### L-R18 - Evidence treatment travels by exact J-AR12 reference

Every message requiring evidence carries exact J-AR12 references. The resolved
J-AR12 record distinguishes `VERIFIED_CONTENT` from `DECLARATION_ONLY`.
Attaching a declared hash never upgrades it to verified content.

### L-R19 - Contract publication and boundary observation remain different

J-AR13 is authoritative and survives restart. J-P13 observations are emitted
after commit and remain removable. An observation cannot replace a publication,
consumer outcome, approved-decision return, or command result.

### L-R20 - CT-1 producer authority remains outside payload metadata

The CT-1 G-03 and G-08 bodies do not invent their publishers through metadata.
Hermes produces G-03 through `ReconcileCashApplicationIdentity`; Aegis produces
the successor G-08 through `UpdateCashApplicationIssue`. Both use the ordinary
command and unit-of-work paths defined by the ratified I/K amendments.

## 3. Closed Scalar and Reference Conventions

Artifact L reuses Artifact F primitives where their meaning already exists:

- dates are `YYYY-MM-DD`;
- timestamps are timezone-qualified RFC 3339 values;
- money uses integer minor units plus ISO 4217 currency;
- hashes use `sha256:` followed by 64 lowercase hexadecimal characters;
- actor, opaque, and evidence semantics remain those of Artifact F; and
- fully qualified version references end in `@v<n>` for positive integer `n`.

No floating-point number is permitted. An inapplicable field is absent, not
`null`, unless a body below explicitly permits `null`.

### 3.1 Authoritative reference

Artifact K's reference is used unchanged:

```text
AuthoritativeRef
  record_family        # J-AR01 through J-AR17
  record_identity
  semantic_hash
```

### 3.2 Contract-publication reference

```text
ContractPublicationRef
  publication_authoritative_ref  # constrained to J-AR13
  contract_id          # G-01 through G-14
  g_contract_version   # G-v0.2
  product_ref
  payload_hash
```

All five fields must resolve to one J-AR13 record.

### 3.3 Module-product reference

```text
ModuleProductRef
  product_authoritative_ref      # constrained to J-AR02
  product_discriminator
  product_ref
  body_contract_version
  body_hash
```

All five fields must resolve to one exact J-AR02 version. The nested
`product_authoritative_ref.semantic_hash` binds the complete J-AR02 record;
`body_hash` separately binds its reusable canonical body.

### 3.4 Exact semantic reference

Where a body intentionally permits more than one reference family, it uses the
following closed union:

```text
ExactSemanticRef
  ref_kind                       # AUTHORITATIVE, PUBLICATION, MODULE_PRODUCT
  authoritative_ref              # present only for AUTHORITATIVE
  publication_ref                # present only for PUBLICATION
  module_product_ref             # present only for MODULE_PRODUCT
```

Exactly one conditional field is present and must match `ref_kind`.

### 3.5 Ordered references

Arrays whose business order matters preserve that order. Set-like arrays are
canonicalized by their complete permanent reference. Duplicate references are
rejected; they are not silently removed.

## 4. J-AR13 Publication Envelope

Every G publication contains exactly:

| Field | Contract |
|---|---|
| `publication_ref` | Permanent J-AR13 identity. |
| `contract_id` | One of G-01 through G-14. |
| `g_contract_version` | Constant `G-v0.2`. |
| `body_contract_version` | Positive integer; constant `1` in this artifact. |
| `body_discriminator` | Exact body or Artifact F object discriminator selected by section 5. |
| `canonicalization_version` | Constant `SORTED_KEYS_COMPACT_UTF8_V1`. |
| `publisher` | Exact publisher permitted by section 5. |
| `product_ref` | Permanent or fully qualified exact product identity. |
| `product_state_token` | Required only where section 5 says `STATE_TOKEN`; otherwise absent. |
| `canonical_payload` | Exact section 6 body as a logical value. |
| `payload_hash` | SHA-256 of canonical payload bytes only. |
| `upstream_publication_refs` | Ordered exact G publication references consumed by the publisher. |
| `upstream_authoritative_refs` | Ordered exact non-G authoritative inputs required to reproduce the output. |
| `evidence_refs` | Ordered exact J-AR12 authoritative references. |
| `available_from` | Earliest semantic time at which application and query reads may expose the publication. |
| `publication_basis` | Exactly one basis variant below. |

`publication_basis` is one of:

| Basis | Exact fields |
|---|---|
| `COMMAND` | `basis_type`, `command_owner`, `command_id`, `command_result_ref` |
| `PRE_SCOPE_IMPORT` | `basis_type`, `import_attestation_ref` |
| `REFERENCED_JOURNAL_ADMISSION` | `basis_type`, `referenced_source_ref`, `admission_identity` |

The canonical payload excludes the J-AR13 envelope. `payload_hash` therefore
remains stable if physical storage or post-commit observation metadata changes.
The J-AR13 authoritative semantic hash separately binds the complete envelope.

## 5. G Contract Registry

The table is closed for body contract version 1. `STATE_TOKEN` means the exact
Artifact J lifecycle token is mandatory. `VERSION_REF` means the product's own
fully qualified immutable version is sufficient. `PERMANENT_ID` means the
product is immutable but not a versioned family.

| ID | Publisher | Permitted consumers in this slice | Body | Exactness |
|---|---|---|---|---|
| G-01 | `SharedSubstrate` | Atlas; Argus where declared | Artifact F `business_event` | `PERMANENT_ID` |
| G-02 | `Hermes` | SharedSubstrate, Atlas, Argus | `G02AdmissionResult` | `VERSION_REF` |
| G-03 | `Hermes` | Argus, Aegis, Atlas | `G03ReconciliationResult` | `VERSION_REF` |
| G-04 | `Atlas` | Argus, Aegis; Pythia for a declared product | One exact Artifact F accounting-object view | `STATE_TOKEN` for lifecycles; otherwise `PERMANENT_ID` |
| G-05 | `Atlas` | Argus, Aegis, Hermes | Artifact F `accounting_event` | `PERMANENT_ID` |
| G-06 | `Atlas` | Argus, Aegis, Pythia | `G06ReportingVersion` | `VERSION_REF` |
| G-07 | `Argus` | Aegis; Atlas as informational reader | `G07AssuranceResult` | `VERSION_REF` |
| G-08 | `Aegis` | Argus, Atlas; Pythia where reliance is affected | `G08GovernanceResult` | `VERSION_REF` |
| G-09 | `Aegis` | Atlas | `G09RemediationDirective` | `VERSION_REF` |
| G-10 | `Aegis` | Pythia | `G10ReadinessAssessment` | `VERSION_REF` |
| G-11 | `Pythia` | Argus, Aegis | `G11PlanningInputSnapshot` | `VERSION_REF` |
| G-12 | `Pythia` | Argus, Aegis, Atlas, `ApprovedDecision` source-domain boundary | `G12GovernedDecision` | `VERSION_REF` |
| G-13 | `AtlasReadBoundary` | Argus, typed correction constructors | `G13ReferencedJournal` | `VERSION_REF` plus source hash |
| G-14 | `Atlas` | Requesting Aegis; Argus where relevant | `G14CommandRejection` | `VERSION_REF` |

`ApprovedDecision` is the logical source-business-domain boundary ratified by
I-R11. It is not a module, new truth layer, or owner of the G-12 product.

### 5.1 Body-discriminator values

The J-AR13 `body_discriminator` is closed as follows:

| Contract | Permitted value |
|---|---|
| G-01 | `business_event` |
| G-02 | `G02AdmissionResult` |
| G-03 | `G03ReconciliationResult` |
| G-04 | `journal_proposal`, `accounting_period`, `restatement_case`, or `journal_entry` |
| G-05 | `accounting_event` |
| G-06 | `G06ReportingVersion` |
| G-07 | `G07AssuranceResult` |
| G-08 | `G08GovernanceResult` |
| G-09 | `G09RemediationDirective` |
| G-10 | `G10ReadinessAssessment` |
| G-11 | `G11PlanningInputSnapshot` |
| G-12 | `G12GovernedDecision` |
| G-13 | `G13ReferencedJournal` |
| G-14 | `G14CommandRejection` |

No other value is valid for body contract version 1.

## 6. Exact G Message Bodies

Every table lists the complete fields in that body. Fields defined only in the
J-AR13 envelope are not repeated inside the payload.

### 6.1 G-01 - admitted business event

The canonical payload is exactly Artifact F version-1 `business_event`. Only
`accounting.recognition.due` is supported. Its J-AR13 envelope must bind:

- the accepted G-02 publication;
- the exact J-AR01 candidate receipt and J-AR03 admitted event;
- identical candidate and event payload hashes; and
- the I-C02 command result.

No L-specific field is added inside the Artifact F payload.

### 6.2 G-02 - source admission and lineage result

`G02AdmissionResult` is exactly the canonical body of
`hermes.business_event_admission_result`:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified admission-result version. |
| `candidate_receipt_ref` | Exact J-AR01 authoritative reference. |
| `candidate_type` | Supplied source candidate discriminator. |
| `candidate_payload_hash` | Must equal the J-AR01 canonical payload hash. |
| `source_domain_ref` | Opaque source-domain reference. |
| `source_record_ref` | Opaque source-record reference. |
| `outcome` | `ACCEPTED`, `REJECTED`, `QUARANTINED`, or `UNSUPPORTED`. |
| `reason_code` | Absent for `ACCEPTED`; required otherwise. |
| `eligible_for_g01` | `true` only for `ACCEPTED`; `false` otherwise. |
| `assessed_at` | Timestamp. |

For I-S26, `candidate_type = workforce.hiring.deferred`, `outcome =
UNSUPPORTED`, and `eligible_for_g01 = false`. The literal identity and dates
remain parameterised.

### 6.3 G-03 - reconciliation result

`G03ReconciliationResult` is a strict union selected by
`reconciliation_type`.

Common fields:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified Hermes reconciliation version. |
| `reconciliation_type` | `RECOGNITION_POPULATION` or `CASH_APPLICATION_IDENTITY`. |
| `scope_ref` | Exact opaque scope identity. |
| `result` | `RECONCILED` or `FAILED`. |
| `performed_at` | Timestamp. |

`RECOGNITION_POPULATION` additionally contains exactly:

| Field | Contract |
|---|---|
| `period_id` | Presented accounting period. |
| `recognition_schedule_ref` | Exact `source.recognition_schedule` module-product reference. |
| `expected_item_count` | Non-negative integer. |
| `expected_amount_minor` | Non-negative integer. |
| `posted_item_count` | Non-negative integer. |
| `posted_amount_minor` | Non-negative integer. |
| `submitted_unposted_count` | Non-negative integer. |
| `deferred_count` | Non-negative integer. |
| `difference_minor` | Signed integer equal to expected minus posted. |
| `currency` | ISO 4217 currency shared by the amounts. |

`CASH_APPLICATION_IDENTITY` additionally contains exactly:

| Field | Contract |
|---|---|
| `cash_application_ref` | Exact source application reference. |
| `receipt_party_ref` | Opaque party reference resolved from the receipt. |
| `application_party_ref` | Opaque party reference used by the posting. |
| `party_mapping_ref` | Exact `hermes.party_identity_mapping` module-product reference. |
| `identity_match` | Boolean. |

`result = RECONCILED` if and only if the quantified difference is zero or the
identity match is true for the selected variant.

### 6.4 G-04 - accounting object view

Each G-04 publication carries exactly one Artifact F version-1 body selected by
`object_type` in publication metadata. Version 1 permits only:

- `journal_proposal` at an exact Artifact J proposal state token;
- `accounting_period` at an exact base or accounting-event token;
- `restatement_case` at an exact case event token; or
- immutable `journal_entry`.

Journal lines are resolved from the exact J-AR08 journal named by the
`journal_entry.line_refs`; they are not embedded into a new G-04 bundle shape.
A command publishing a proposal plus a journal or case emits distinct G-04
J-AR13 records in the same command unit of work.

### 6.5 G-05 - accounting event

The canonical payload is exactly one Artifact F version-1 `accounting_event`.
The J-AR13 product identity equals the event identity, and the payload hash
equals the exact J-AR06 hash. No accounting event can satisfy G-01.

### 6.6 G-06 - reporting version

`G06ReportingVersion` contains common fields:

| Field | Contract |
|---|---|
| `reporting_version_ref` | Fully qualified reporting-version reference. |
| `period_id` | Presented period. |
| `content_ref` | Immutable reporting-content reference. |
| `content_hash` | SHA-256 of canonical reporting-content bytes. |
| `content_schema_version` | Positive integer. |
| `publication_origin` | `PRE_SCOPE_IMPORT` or `RESTATEMENT_PUBLICATION`. |
| `published_at` | Original publication timestamp. |

`PRE_SCOPE_IMPORT` additionally contains exactly:

| Field | Contract |
|---|---|
| `import_attestation_ref` | Exact J-AR11 authoritative reference. |
| `original_authority_ref` | Opaque original publication-authority reference. |
| `source_ref` | Opaque archive or source-system reference. |

`RESTATEMENT_PUBLICATION` additionally contains exactly:

| Field | Contract |
|---|---|
| `predecessor_version_ref` | Exact available predecessor reporting version. |
| `restatement_case_ref` | Exact Atlas case reference at its published token. |
| `manifest_hash` | Frozen J-AR09 manifest hash. |
| `published_by_event_id` | Exact `reporting_version.published` event identity. |
| `publication_effect_ref` | Exact J-AR15 authoritative reference. |

The imported variant uses `PRE_SCOPE_IMPORT` publication basis. The successor
uses `COMMAND`. Neither variant contains readiness.

### 6.7 G-07 - assurance result and exception

`G07AssuranceResult` is selected by `result_type`.

`ASSURANCE_EXCEPTION` contains exactly:

| Field | Contract |
|---|---|
| `result_type` | Constant `ASSURANCE_EXCEPTION`. |
| `test_run_ref` | Exact Argus test-run module-product reference. |
| `exception_ref` | Exact Argus exception module-product reference. |
| `test_outcome` | Constant `FAILED`. |
| `assertion` | `COMPLETENESS` or `ACCURACY`, as fixed by the referenced product contract. |
| `severity` | `BLOCKING` for recognition completeness; `HIGH` for cash identity. |

`ASSURANCE_VERIFICATION` contains exactly:

| Field | Contract |
|---|---|
| `result_type` | Constant `ASSURANCE_VERIFICATION`. |
| `verification_ref` | Exact Argus verification module-product reference. |
| `verification_outcome` | `PASSED` or `FAILED`. |

The G-07 body does not contain a finding, issue, readiness status, or correcting
entry.

### 6.8 G-08 - governance result

`G08GovernanceResult` is selected by `governance_result_type`.

`EXCEPTION_GOVERNED` contains exactly:

| Field | Contract |
|---|---|
| `governance_result_type` | Constant `EXCEPTION_GOVERNED`. |
| `review_ref` | Exact Aegis review module-product reference. |
| `finding_ref` | Exact Aegis finding module-product reference. |
| `issue_ref` | Exact Aegis issue module-product reference. |
| `source_exception_ref` | Exact Argus exception module-product reference. |

`ISSUE_UPDATED` contains exactly:

| Field | Contract |
|---|---|
| `governance_result_type` | Constant `ISSUE_UPDATED`. |
| `issue_ref` | Exact successor Aegis issue module-product reference. |
| `verification_ref` | Exact Argus verification module-product reference. |
| `prior_issue_ref` | Exact predecessor issue module-product reference. |

An `ISSUE_UPDATED` body may report `REMEDIATION_VERIFIED` or `CLOSED` only
through the referenced Aegis issue version. Argus verification alone does not
change that state.

### 6.9 G-09 - remediation directive

`G09RemediationDirective` is exactly the canonical body of
`aegis.remediation_directive`:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified directive version. |
| `issue_ref` | Exact current Aegis issue module-product reference. |
| `target_module` | Constant `Atlas`. |
| `requested_outcome` | `RESTATEMENT` or `OPEN_PERIOD_REVERSAL_AND_REPLACEMENT`. |
| `affected_period_id` | Period whose accounting or presentation is affected. |
| `eligible_correction_period_id` | Required open correction period. |
| `policy_ref` | Exact J-AR04 correction or restatement policy reference. |
| `requested_by` | Actor reference. |
| `requested_at` | Timestamp. |

It contains no journal lines, proposal treatment, restatement-case state, or
proof that the requested outcome occurred.

### 6.10 G-10 - purpose-specific readiness

`G10ReadinessAssessment` is exactly the canonical body of
`aegis.readiness_assessment`:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified readiness-assessment version. |
| `reporting_version_ref` | Exact reporting-version identity. |
| `reporting_publication_ref` | Exact matching G-06 publication reference. |
| `period_id` | Same period as the reporting version. |
| `scope_ref` | Exact controlled-use scope. |
| `purpose_ref` | Exact planning-purpose reference. |
| `status` | `BLOCKED` or `APPROVED`. |
| `basis_refs` | Non-empty ordered `ExactSemanticRef` values. |
| `limitation_codes` | Non-empty for `BLOCKED`; empty for `APPROVED`. |
| `assessed_by` | Actor reference. |
| `assessed_at` | Timestamp. |

The reporting version, G-06 payload, and readiness body must agree on product
and period. A corrected successor cannot inherit predecessor readiness.

### 6.11 G-11 - planning input snapshot

`G11PlanningInputSnapshot` is exactly the canonical body of
`pythia.planning_input_snapshot`:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified planning-snapshot version. |
| `reporting_version_ref` | Exact Atlas reporting version. |
| `reporting_publication_ref` | Exact G-06 publication reference. |
| `readiness_ref` | Exact Aegis readiness module-product reference. |
| `readiness_publication_ref` | Exact G-10 publication reference. |
| `purpose_ref` | Must equal the G-10 purpose. |
| `period_id` | Must equal G-06 and G-10 period. |
| `scope_ref` | Must equal the G-10 scope. |
| `assumption_refs` | Ordered exact J-AR04 assumption references. |
| `exclusion_refs` | Ordered exact authoritative references; may be empty. |
| `frozen_at` | Timestamp. |

Only an `APPROVED` G-10 for the same G-06 product can produce this body.

### 6.12 G-12 - governed decision

`G12GovernedDecision` is exactly the canonical body of
`pythia.governed_decision`:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified decision-product version. |
| `decision_type` | Constant `HIRING_DEFERRAL`. |
| `planning_snapshot_ref` | Exact G-11 module-product reference. |
| `planning_publication_ref` | Exact G-11 publication reference. |
| `position_ref` | Opaque workforce-position reference. |
| `original_start_date` | Date. |
| `recommended_start_date` | Later date. |
| `monthly_cost_minor` | Non-negative integer minor units. |
| `currency` | ISO 4217 currency. |
| `reason_code` | Constant `ACTUALS_READINESS_DELAY` in body version 1. |
| `produced_at` | Timestamp. |

The body is a governed recommendation product, not operational approval. The
recommended date must be later than the original date.

### 6.13 G-13 - referenced accounting-state projection

`G13ReferencedJournal` contains exactly the parameterised fields of Artifact
F's read-only proof projection:

| Field | Contract |
|---|---|
| `projection_type` | Constant `referenced_journal_projection`. |
| `projection_version` | Constant `1`. |
| `authored_by_f` | Constant `false`. |
| `source_hash` | Hash of the exact J-AR17 canonical source. |
| `journal_id` | Referenced immutable prior-journal identity. |
| `ledger_period_id` | Period identity. |
| `currency` | Constant `GBP` for Artifact F compatibility. |
| `line_tuples` | Ordered line tuples exactly as defined by Artifact F section 1.2. |

The J-AR13 upstream authoritative references contain exactly the corresponding
J-AR17 source. G-13 carries no `product_state_token`; `source_hash` is the
immutable source binding required by the `VERSION_REF plus source hash`
contract.

### 6.14 G-14 - pre-construction command rejection

`G14CommandRejection` contains exactly:

| Field | Contract |
|---|---|
| `disposition_ref` | Fully qualified J-AR16 disposition version. |
| `command_owner` | Target owner; `Atlas` in the current slice. |
| `command_id` | Stable rejected command identity. |
| `command_type` | Exact application command type. |
| `requesting_module` | `Aegis` in the C-001 rejection proof. |
| `target_module` | Constant `Atlas` in the current slice. |
| `request_ref` | Exact request or G-09 directive reference. |
| `disposition` | Constant `REJECTED`. |
| `reason_code` | Versioned rejection-policy reason code. |
| `recorded_at` | Timestamp. |
| `authority_refs` | Ordered `ExactSemanticRef` values for authority evaluated. |

The body has no Artifact F subject, accounting object, accounting event,
financial effect, or target lifecycle token.

## 7. Finite J-AR02 Discriminator Registry

Every descriptor uses:

```text
body_contract_version = 1
supported_canonicalization_versions = [SORTED_KEYS_COMPACT_UTF8_V1]
```

`BASELINE` means `RuntimeBaselineAdmissionUnitOfWork`; `COMMAND` means
`CommandUnitOfWork`. No descriptor permits both.

| ID | Product discriminator | Owner | Mode | Baseline | Command output | Validator |
|---|---|---|---|---:|---:|---|
| L-MP01 | `source.recognition_schedule` | SourceDomain | BASELINE | true | false | `L-VAL-MP01` |
| L-MP02 | `hermes.party_identity_mapping` | Hermes | BASELINE | true | false | `L-VAL-MP02` |
| L-MP03 | `hermes.business_event_admission_result` | Hermes | COMMAND | false | true | `L-VAL-MP03` |
| L-MP04 | `hermes.recognition_population_reconciliation` | Hermes | COMMAND | false | true | `L-VAL-MP04` |
| L-MP05 | `hermes.cash_application_identity_reconciliation` | Hermes | COMMAND | false | true | `L-VAL-MP05` |
| L-MP06 | `argus.recognition_completeness_test_run` | Argus | COMMAND | false | true | `L-VAL-MP06` |
| L-MP07 | `argus.recognition_completeness_exception` | Argus | COMMAND | false | true | `L-VAL-MP07` |
| L-MP08 | `argus.cash_application_identity_test_run` | Argus | COMMAND | false | true | `L-VAL-MP08` |
| L-MP09 | `argus.cash_application_identity_exception` | Argus | COMMAND | false | true | `L-VAL-MP09` |
| L-MP10 | `argus.restatement_verification` | Argus | COMMAND | false | true | `L-VAL-MP10` |
| L-MP11 | `argus.cash_application_correction_verification` | Argus | COMMAND | false | true | `L-VAL-MP11` |
| L-MP12 | `aegis.exception_review` | Aegis | COMMAND | false | true | `L-VAL-MP12` |
| L-MP13 | `aegis.finding` | Aegis | COMMAND | false | true | `L-VAL-MP13` |
| L-MP14 | `aegis.issue` | Aegis | COMMAND | false | true | `L-VAL-MP14` |
| L-MP15 | `aegis.remediation_directive` | Aegis | COMMAND | false | true | `L-VAL-MP15` |
| L-MP16 | `aegis.readiness_assessment` | Aegis | COMMAND | false | true | `L-VAL-MP16` |
| L-MP17 | `pythia.planning_input_snapshot` | Pythia | COMMAND | false | true | `L-VAL-MP17` |
| L-MP18 | `pythia.governed_decision` | Pythia | COMMAND | false | true | `L-VAL-MP18` |
| L-MP19 | `source.operational_decision_approval` | SourceDomain | COMMAND | false | true | `L-VAL-MP19` |
| L-MP20 | `source.business_event_candidate` | SourceDomain | COMMAND | false | true | `L-VAL-MP20` |

L-MP05 is produced only by the Hermes-owned
`ReconcileCashApplicationIdentity` command. Registry presence is not permission
for another command or persistence mode to bypass that ownership.

### 7.1 Validated module-product record

A descriptor validates one exact J-AR02 semantic value:

```text
ValidatedModuleProduct
  product_discriminator
  body_contract_version
  semantic_owner
  canonicalization_version
  canonical_body
  body_hash
  upstream_publication_refs[]
  upstream_authoritative_refs[]
  evidence_refs[]
  creation_basis
  available_from
  semantic_hash
```

`canonical_body` includes the fully qualified `product_ref`. `creation_basis`
is exactly one of:

- `BASELINE` with `baseline_manifest_ref`; or
- `COMMAND` with `command_owner` and `command_id`.

`body_hash` is computed over `canonical_body` and is the hash used by a G
payload or replayable candidate receipt. `semantic_hash` is computed over the
canonical bytes of every preceding field, including `body_hash`, and therefore
binds identity, owner, lineage, evidence, availability, and creation basis. The
registry descriptor itself is selected by discriminator and body contract
version and is not supplied by the caller.

## 8. Exact J-AR02 Bodies

Every body contains only the fields explicitly listed below or incorporated by
an exact reused G body. A reused G body retains its own timestamp vocabulary;
it does not acquire a synthetic `created_at` field. Evidence, upstream refs,
creation basis, owner, availability, and canonicalization are in the enclosing
validated product and are not duplicated.

### 8.1 Baseline products

`source.recognition_schedule` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified schedule-product version. |
| `created_at` | Timestamp. |
| `recognition_schedule_ref` | Opaque recognition-schedule reference. |
| `contract_ref` | Opaque customer-contract reference. |
| `legal_entity_id` | Non-empty string. |
| `customer_id` | Non-empty string. |
| `service_period_start` | Date. |
| `service_period_end` | Date not before start. |
| `recognition_effective_date` | Date within the represented service period. |
| `amount_minor` | Positive integer minor units. |
| `currency` | ISO 4217 currency. |
| `source_record_ref` | Opaque source-record reference. |

`hermes.party_identity_mapping` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified mapping-product version. |
| `created_at` | Timestamp. |
| `mapping_ref` | Opaque mapping identity. |
| `source_party_ref` | Opaque source-party reference. |
| `canonical_party_ref` | Opaque canonical-party reference. |
| `mapping_method` | Constant `DECLARED_SOURCE_MATCH`. |
| `effective_from` | Date. |
| `effective_to` | Date not before `effective_from`, or `null`. |
| `status` | Constant `ACTIVE`. |

### 8.2 Hermes command products

`hermes.business_event_admission_result` is exactly the G-02 body in section
6.2.

`hermes.recognition_population_reconciliation` is exactly the common and
`RECOGNITION_POPULATION` G-03 fields in section 6.3.

`hermes.cash_application_identity_reconciliation` is exactly the common and
`CASH_APPLICATION_IDENTITY` G-03 fields in section 6.3.

### 8.3 Argus test and exception products

`argus.recognition_completeness_test_run` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified test-run version. |
| `created_at` | Timestamp. |
| `test_definition_ref` | Exact J-AR04 authoritative reference. |
| `reconciliation_ref` | Exact L-MP04 module-product reference. |
| `period_id` | Same period as the reconciliation. |
| `population_refs` | Non-empty ordered `ExactSemanticRef` values. |
| `population_hashes` | Ordered hashes with one entry per population ref. |
| `executed_at` | Timestamp not before all inputs were available. |
| `outcome` | Constant `FAILED`. |
| `exception_ref` | Fully qualified L-MP07 identity created in the same command. |

`argus.recognition_completeness_exception` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified exception version. |
| `created_at` | Timestamp. |
| `test_run_ref` | Fully qualified L-MP06 identity created in the same command. |
| `assertion` | Constant `COMPLETENESS`. |
| `severity` | Constant `BLOCKING`. |
| `subject_refs` | Non-empty ordered `ExactSemanticRef` values. |
| `expected_amount_minor` | Non-negative integer. |
| `actual_amount_minor` | Non-negative integer. |
| `difference_minor` | Signed integer equal to expected minus actual. |
| `currency` | ISO 4217 currency shared by the amounts. |
| `period_id` | Presented accounting period. |
| `status` | Constant `OPEN`. |

`argus.cash_application_identity_test_run` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified test-run version. |
| `created_at` | Timestamp. |
| `test_definition_ref` | Exact J-AR04 authoritative reference. |
| `reconciliation_ref` | Exact L-MP05 module-product reference. |
| `referenced_journal_publication_ref` | Exact G-13 publication reference. |
| `population_refs` | Non-empty ordered `ExactSemanticRef` values. |
| `population_hashes` | Ordered hashes with one entry per population ref. |
| `executed_at` | Timestamp not before all inputs were available. |
| `outcome` | Constant `FAILED`. |
| `exception_ref` | Fully qualified L-MP09 identity created in the same command. |

`argus.cash_application_identity_exception` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified exception version. |
| `created_at` | Timestamp. |
| `test_run_ref` | Fully qualified L-MP08 identity created in the same command. |
| `assertion` | Constant `ACCURACY`. |
| `severity` | Constant `HIGH`. |
| `receipt_party_ref` | Opaque party reference resolved from the receipt. |
| `application_party_ref` | Opaque customer reference used by the journal. |
| `journal_id` | Same referenced prior journal as G-13. |
| `amount_minor` | Positive integer minor units. |
| `currency` | Same currency as the referenced journal. |
| `status` | Constant `OPEN`. |

### 8.4 Argus verification products

`argus.restatement_verification` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified verification version. |
| `created_at` | Timestamp. |
| `verification_type` | Constant `RESTATEMENT_OUTCOME`. |
| `journal_ref` | Exact J-AR08 authoritative reference. |
| `manifest_ref` | Exact J-AR09 authoritative reference. |
| `predecessor_reporting_ref` | Exact predecessor J-AR10 authoritative reference. |
| `successor_reporting_ref` | Exact successor J-AR10 authoritative reference. |
| `reporting_publication_ref` | Exact successor G-06 publication reference. |
| `check_results` | Closed boolean object below. |
| `outcome` | `PASSED` or `FAILED`. |

Its `check_results` contains exactly one boolean for each:

- `journal_posted`;
- `manifest_reconciled`;
- `reporting_bridge_reproduced`;
- `publication_lineage_complete`; and
- `required_evidence_available`.

`argus.cash_application_correction_verification` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified verification version. |
| `created_at` | Timestamp. |
| `verification_type` | Constant `CASH_APPLICATION_CORRECTION`. |
| `source_journal_ref` | Exact J-AR17 authoritative reference. |
| `source_hash` | Must equal J-AR17 and G-13 source hash. |
| `reversal_journal_ref` | Exact J-AR08 authoritative reference. |
| `replacement_journal_ref` | Exact J-AR08 authoritative reference. |
| `check_results` | Closed boolean object below. |
| `outcome` | `PASSED` or `FAILED`. |

Its `check_results` contains exactly one boolean for each:

- `reversal_source_bound`;
- `reversal_equal_and_opposite`;
- `replacement_customer_correct`;
- `journals_balanced`; and
- `control_account_net_zero`.

For both verification products, `outcome = PASSED` if and only if every check is
true; otherwise it is `FAILED`.

### 8.5 Aegis governance products

`aegis.exception_review` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified review version. |
| `created_at` | Timestamp. |
| `exception_ref` | Exact L-MP07 or L-MP09 module-product reference. |
| `review_outcome` | Constant `CONFIRMED`. |
| `reviewed_by` | Actor reference. |
| `reviewed_at` | Timestamp. |
| `conclusion_code` | Versioned governance-policy conclusion code. |

`aegis.finding` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified finding version. |
| `created_at` | Timestamp. |
| `review_ref` | Fully qualified L-MP12 identity created in the same command. |
| `finding_type` | `RECOGNITION_OMISSION` or `CASH_APPLICATION_IDENTITY_MISMATCH`. |
| `assertion` | `COMPLETENESS` or `ACCURACY`, consistent with finding type. |
| `affected_refs` | Non-empty ordered `ExactSemanticRef` values. |
| `conclusion_code` | Same conclusion code as the review. |

`aegis.issue` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified issue version matching ID and version. |
| `created_at` | Initial issue creation timestamp, preserved across versions. |
| `issue_id` | Stable issue family identity. |
| `issue_version` | Positive integer. |
| `prior_issue_ref` | Exact prior L-MP14 module-product reference; absent for version 1. |
| `finding_refs` | Non-empty ordered finding identities; each resolves to L-MP13. |
| `status` | `OPEN`, `TREATMENT_APPROVED`, `REMEDIATION_VERIFIED`, or `CLOSED`. |
| `owner_ref` | Actor reference. |
| `directive_refs` | Ordered exact L-MP15 module-product references; may be empty. |
| `verification_refs` | Ordered exact L-MP10/L-MP11 module-product references; may be empty. |
| `updated_at` | Timestamp not before `created_at`. |

`aegis.remediation_directive` is exactly the G-09 body in section 6.9.

`aegis.readiness_assessment` is exactly the G-10 body in section 6.10.

### 8.6 Pythia products

`pythia.planning_input_snapshot` is exactly the G-11 body in section 6.11.

`pythia.governed_decision` is exactly the G-12 body in section 6.12.

### 8.7 Source-domain decision products

`source.operational_decision_approval` is selected by `outcome`.

Common fields:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified approval version. |
| `created_at` | Timestamp. |
| `decision_ref` | Exact L-MP18 module-product reference. |
| `decision_publication_ref` | Exact G-12 publication reference. |
| `outcome` | `APPROVED` or `REJECTED`. |
| `decided_by` | Source-domain actor reference. |
| `decided_at` | Timestamp not before G-12 availability. |
| `approval_policy_ref` | Exact J-AR04 authoritative reference. |

`APPROVED` additionally requires `candidate_ref`. `REJECTED` prohibits it.

`source.business_event_candidate` contains exactly:

| Field | Contract |
|---|---|
| `product_ref` | Fully qualified source-candidate version. |
| `created_at` | Timestamp. |
| `candidate_type` | Constant `workforce.hiring.deferred`. |
| `source_domain_ref` | Opaque affected source-domain reference. |
| `decision_ref` | Exact L-MP18 module-product reference. |
| `approval_ref` | Fully qualified L-MP19 identity created in the same command. |
| `correlation_id` | Non-empty trace identity. |
| `occurred_at` | Operational approval timestamp. |
| `recorded_at` | Candidate recording timestamp not before occurrence. |
| `effective_date` | Date on which the deferral becomes effective. |
| `position_ref` | Same workforce-position reference as G-12. |
| `original_start_date` | Same original date as G-12. |
| `revised_start_date` | Same recommended date as approved G-12. |
| `monthly_cost_minor` | Same non-negative amount as G-12. |
| `currency` | Same currency as G-12. |
| `reason_code` | Constant `ACTUALS_READINESS_DELAY`. |

The candidate's operational values must equal the approved G-12 recommendation.
It intentionally lacks an Artifact F `contract_version` and is not an Artifact
F business event.

## 9. Approved-Decision Return

`ApprovedDecisionReturn` is a typed application input, not J-AR13 and not a new
authoritative record family. It contains exactly:

| Field | Contract |
|---|---|
| `return_contract_version` | Constant `1`. |
| `decision_publication_ref` | Exact G-12 contract-publication reference. |
| `approval_ref` | Exact `source.operational_decision_approval` module-product reference. |
| `candidate_ref` | Exact `source.business_event_candidate` module-product reference. |
| `candidate_payload_hash` | Must equal the candidate module-product body hash. |

I-S26 accepts the return only when:

1. G-12 resolves and equals the decision named by the approval;
2. the approval outcome is `APPROVED` and names the candidate;
3. the candidate binds the same decision and approval;
4. the candidate operational values equal the approved recommendation;
5. every referenced product and publication is available; and
6. J-AR01 custody retains or resolves the exact candidate canonical bytes.

A mismatched or rejected return creates no candidate receipt. A valid return
reaches ordinary I-C01 admission and is expected to produce G-02
`UNSUPPORTED` in Milestone 2.

## 10. Cross-Record Binding Matrix

Every accepted command and every rebuild checks the applicable row.

| Boundary | Required binding |
|---|---|
| G-01 | Candidate receipt hash = accepted G-02 candidate hash = J-AR03 hash = G-01 payload hash. |
| G-02 | J-AR13 payload bytes equal the exact L-MP03 canonical body; candidate and outcome agree with J-AR01. |
| G-03 | J-AR13 payload bytes equal L-MP04 or L-MP05; every population or mapping ref resolves and is available. |
| G-04 | Payload bytes equal the exact Artifact F view at the J-AR13 state token. |
| G-05 | Product identity and payload hash equal the exact J-AR06 event. |
| G-06 import | Payload, J-AR10, J-AR11, verified J-AR12 content, and import basis agree; no J-AR15 exists. |
| G-06 successor | Payload, J-AR10, predecessor, event, case, manifest, and J-AR15 publication effect agree. |
| G-07 exception | Test run and exception resolve, agree on each other, and are both outputs of the publishing command. |
| G-07 verification | Verification input refs and checks reproduce its outcome. |
| G-08 governed exception | Review, finding, issue, and source exception form one exact chain. |
| G-08 issue update | Successor issue names the prior issue and exact Argus verification. |
| G-09 | Directive owner, issue, target, policy, periods, and requested outcome agree with the publishing Aegis command. |
| G-10 | Reporting identity, G-06 publication, purpose, period, scope, and readiness all match. |
| G-11 | G-06 and G-10 refer to the same product, period, purpose, and scope; G-10 is `APPROVED`. |
| G-12 | Decision names the exact G-11 product and publication; recommendation fields derive only from the frozen snapshot. |
| G-13 | J-AR17 source hash = G-13 `source_hash`; correction construction binds that hash before deriving lines. |
| G-14 | J-AR16 and G-14 payload agree on command, request, target, rejection reason, and evidence; no target object exists. |
| Approved return | G-12, approval, candidate, and I-S26 receipt bind exact identities, hashes, and operational values. |

Any mismatch rejects the complete write set. A projection or observation cannot
repair an authoritative mismatch.

## 11. C-001 Runtime Proof

The parameterised C-001 sequence instantiates these exact bodies.

| Runtime stage | Products and publications |
|---|---|
| Baseline | L-MP01 recognition schedule plus exact J-AR04/J-AR07/J-AR12 inputs; no G publication. |
| I-S01 | L-MP03 and G-02 `ACCEPTED`. |
| I-S02 | J-AR03 and exact Artifact F G-01. |
| I-S03 | Atlas treatment only; no G publication. |
| I-S04/I-S05 | Artifact F proposal G-04 plus event G-05 at exact tokens. |
| I-S06 | Artifact F period G-04 plus hard-close G-05. |
| Import seam | G-06 `PRE_SCOPE_IMPORT` with J-AR10/J-AR11/J-AR12. |
| I-S07 | L-MP04 and G-03 `RECOGNITION_POPULATION`. |
| I-S08 | L-MP06/L-MP07 and G-07 `ASSURANCE_EXCEPTION`. |
| I-S09 | L-MP12/L-MP13/L-MP14 and G-08 `EXCEPTION_GOVERNED`. |
| I-S10 | L-MP16 and G-10 `BLOCKED` for predecessor v1. |
| I-S11 | L-MP15, successor L-MP14, and G-09 `RESTATEMENT`. |
| I-S12 accepted | Artifact F case G-04 and event G-05. |
| I-S12 rejected proof | J-AR16 and G-14 `REJECTED`; no Artifact F subject. |
| I-S13 | Atlas treatment only; no G publication. |
| I-S14/I-S15 | Artifact F correction proposal G-04 plus event G-05. |
| I-S16 | Artifact F proposal and journal G-04 publications plus posting G-05. |
| I-S17 to I-S19 | Exact case G-04 and case-event G-05 publications. |
| I-S20 | Exact case G-04, publication-event G-05, and successor G-06. |
| I-S21 | L-MP10 and G-07 `ASSURANCE_VERIFICATION`. |
| I-S22 | L-MP16 and G-10 `APPROVED` for successor v2. |
| I-S23 | L-MP17 and G-11. |
| I-S24 | L-MP18 and G-12. |
| I-S25 | L-MP19 `APPROVED` plus L-MP20; direct approved-decision return only. |
| I-S26 | J-AR01 plus L-MP03 and G-02 `UNSUPPORTED`; no G-01. |

The proof uses all G-01 through G-12 bodies and G-14. It never routes an
accounting event, G publication, readiness product, or decision into posting-rule
evaluation.

## 12. CT-1 Reconciliation After Producer Repair

Artifact L v0.1 found two sequencing contradictions between Artifact G and the
later Artifact I/K execution maps. They were command-coverage gaps, not payload
ambiguities. The ratified I/K amendments apply the minimum repairs below.

### 12.1 Hermes G-03 producer

Artifact G section 9 requires Hermes to publish G-03 before Argus runs the CT-1
identity test. Artifact I v0.2.2 contains the Hermes command, and Artifact K
v0.2.2 maps it before the Argus test.

The ordinary Hermes command before `RunCashApplicationIdentityTest` is:

```text
ReconcileCashApplicationIdentity
  reads: L-MP02 party mapping + exact cash-application source refs
  writes: L-MP05 + G-03 J-AR13 + J-AR14
```

The command uses the existing `CommandUnitOfWork`, adds no Artifact F object or
event, and gives the Argus test the exact `reconciliation_ref` already required
by L-MP08.

### 12.2 Aegis G-08 producer

Artifact G section 9 says CT-1 ends after Aegis consumes Argus verification and
publishes a G-08 issue update or closure. Artifact I v0.2.2 includes the Aegis
command, and Artifact K v0.2.2 maps it after verification.

The ordinary Aegis command after `VerifyCashApplicationCorrection` is:

```text
UpdateCashApplicationIssue
  reads: exact prior L-MP14 issue + L-MP11 verification/G-07
  writes: successor L-MP14 + G-08 ISSUE_UPDATED + J-AR14
```

The command uses the existing `CommandUnitOfWork`, does not mutate the Argus
verification, and introduces no generic governance workflow.

### 12.3 CT-1 proof after the two repairs

| Order | Runtime result |
|---:|---|
| 1 | Runtime baseline admits L-MP02 party mapping. |
| 2 | Referenced-journal admission commits J-AR17 and G-13. |
| 3 | New Hermes command commits L-MP05 and G-03. |
| 4 | Argus test commits L-MP08/L-MP09 and G-07 exception. |
| 5 | Aegis review commits L-MP12/L-MP13/L-MP14 and G-08. |
| 6 | Aegis directive commits L-MP15, successor L-MP14, and G-09. |
| 7 | Existing authority validation and reversal/replacement commands produce the six Artifact F events and J-011/J-012. |
| 8 | Argus verification commits L-MP11 and G-07 verification. |
| 9 | New Aegis command commits successor L-MP14 and G-08 `ISSUE_UPDATED`. |

The source hash is still bound before reversal derivation. CT-1 creates no
restatement case, reporting version, readiness, planning snapshot, decision, or
approved-decision return.

## 13. Rejection Rules

| Failure | Required result |
|---|---|
| Unknown G ID or body version | Reject before J-AR13 staging. |
| G body contains an unlisted field | Reject body contract; do not coerce. |
| Unknown J-AR02 discriminator/version | Return `UnsupportedDiscriminator`; no write. |
| Registry owner differs from command owner | Reject ownership before staging. |
| Baseline record uses command-only descriptor | `BaselineAdmissionConflict`; no J-AR14. |
| Command tries to emit baseline-only descriptor | Reject command write set. |
| Canonical bytes do not reproduce hash | Invariant failure; fabricate no domain rejection. |
| Missing or unavailable exact upstream ref | Reject or block according to owning command contract. |
| G-01 payload is not the supported Artifact F business event | Reject before posting-rule evaluation. |
| G-04/G-05 body differs from Artifact F | Reject compatibility binding. |
| G-06 imported variant claims ordinary command publication | Reject origin/basis mismatch. |
| G-10 does not match G-06 product, period, purpose, or scope | Block controlled use. |
| G-11 uses blocked or mismatched readiness | Reject snapshot creation. |
| Source domain approval does not bind exact G-12 | Reject approval write set. |
| Returned candidate differs from approved recommendation | Reject before J-AR01 custody. |
| G-13 hash differs from reversal input hash | Reject before line derivation or comparison. |
| G-14 includes a target object or event | Reject rejection package. |

## 14. Acceptance Criteria

Artifact L may be ratified only when all of the following hold.

- L-A01: G-01 through G-14 each resolve to exactly one version-1 body contract;
- L-A02: G-01, G-04, and G-05 reuse Artifact F bodies byte-for-byte;
- L-A03: the J-AR13 envelope carries exact versions, body discriminator,
  publisher, product, state token where required, canonical bytes, hash,
  lineage, evidence, availability, and creation basis;
- L-A04: G semantic version, body contract version, and canonicalization version
  remain distinct;
- L-A05: every cross-module reference is exact and availability-gated;
- L-A06: the registry contains exactly twenty J-AR02 discriminators with no
  wildcard, raw-body, or generic owner entry;
- L-A07: each registry entry has one owner, mode, validator, eligibility pair,
  and supported canonicalization version;
- L-A08: only L-MP01 and L-MP02 are baseline eligible, and neither is a command
  output;
- L-A09: every other module-product entry is command-output eligible and barred
  from baseline admission;
- L-A10: every `ValidatedModuleProduct` hash binds its body, identity, owner,
  lineage, evidence, availability, and creation basis;
- L-A11: C-001 uses only the products and bodies listed in section 11;
- L-A12: C-001 reaches Pythia with exact matching G-06 and approved G-10 before
  G-11 and G-12;
- L-A13: Pythia's G-12 product contains no operational approval claim;
- L-A14: source-domain approval and candidate versions bind G-12 without a new G
  contract or record family;
- L-A15: the approved candidate returns through ordinary Hermes admission and
  produces G-02 `UNSUPPORTED`, no G-01, in Milestone 2;
- L-A16: G-13 remains a J-AR17-backed non-authoring projection and cannot cross
  G-04/G-05;
- L-A17: G-14 version 1 represents only a subject-free pre-construction
  rejection and creates no target lifecycle state;
- L-A18: evidence verification status is resolved from exact J-AR12 and never
  inferred from hash format;
- L-A19: publication persistence and boundary observation remain structurally
  separate;
- L-A20: unknown fields, versions, variants, and discriminators are rejected;
- L-A21: integer minor units are used for every monetary value and no float is
  accepted;
- L-A22: canonical identities can be replaced by semantically valid supplied
  identities without changing routing logic;
- L-A23: every section 10 binding is enforced before commit and during rebuild;
- L-A24: CT-1 still binds G-13 source hash before reversal-line derivation or
  comparison;
- L-A25: CT-1 creates no G-10, G-11, G-12, or approved-decision return;
- L-A26: Artifact I contains a Hermes producer step for CT-1 G-03 before the
  Argus identity test;
- L-A27: Artifact I contains an Aegis G-08 issue-update step after CT-1 Argus
  verification;
- L-A28: Artifact K maps both added CT-1 commands through the ordinary
  `CommandUnitOfWork` with no scenario-private commit path;
- L-A29: the registry and bodies introduce no generic workflow state machine,
  message broker, public API, or plugin contract; and
- L-A30: no database, table, index, ORM, or physical content-storage choice is
  implied by this artifact.

L-A26 through L-A28 are satisfied by the ratified Artifact I v0.2.2 and
Artifact K v0.2.2 amendments.

## 15. Decisions Resolved and Still Open

### 15.1 Resolved by Artifact L

- exact version-1 bodies for G-01 through G-14;
- one strict J-AR13 semantic envelope;
- a finite twenty-entry J-AR02 registry;
- baseline-versus-command-output eligibility;
- exact readiness purpose and scope representation for C-001;
- direct approved-decision return without G-15;
- `UNSUPPORTED` as the I-S26 G-02 outcome;
- G-13 and G-14 non-authoring payload boundaries; and
- canonicalization and hash treatment for internal runtime messages;
- structured exact-reference resolution with semantic availability; and
- pre-commit and rebuild enforcement of all applicable section 10 bindings.

### 15.2 Resolved by the ratified I/K amendments

1. Artifact I v0.2.2 contains the Hermes CT-1 G-03 producer before Argus
   testing, and Artifact K v0.2.2 maps its atomic write set; and
2. Artifact I v0.2.2 contains the post-verification Aegis G-08 issue update,
   and Artifact K v0.2.2 maps its atomic write set.

### 15.3 Historical handoff beyond Artifact L

The following list records the handoff as it stood when Artifact L v0.2 was
ratified. Artifacts M and N and the Milestone 2 implementation have since
resolved the first three items and the projection-checkpoint portion of item 5.
The list is retained as historical sequencing evidence, not current backlog.

1. concrete clock, identity, and sequence-allocation ports;
2. migration compatibility and persisted contract-version policy;
3. physical database engine, schema, indexes, and transactions;
4. evidence-byte storage beyond the bounded reporting proof;
5. projection checkpoint representation and operational rebuild tooling;
6. Milestone 2 assertion-report schema;
7. runtime package layout; and
8. any public API, transport, authentication, UI, or deployment design.

## 16. Current Handoff

The original next step produced Artifact M, followed by Artifact N and the
Milestone 2 runtime. Those historical dependencies are now implemented. The
current handoff is Artifact O and the public product layer: it may consume only
the exact, availability-gated contracts ratified here and may not weaken a
declaration-only evidence or adapted compatibility read into a stronger public
claim. Artifact F remains unchanged.
