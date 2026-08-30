# Artifact F: Minimum Payload Contracts

Design sequence artifact F. This document freezes the smallest closed payload set capable of representing canonical transactions C-001 and CT-1 without introducing speculative object variants or accounting-event types.

Status: Design v0.2.1 - contract boundary ratified; reporting proof fixtures revised 2026-07-23

Binds:

- Artifact C: Accounting Object Model.
- Artifact E v0.2.1: Accounting State Machines and Command/Event Matrix.
- ADR-012: Freeze the Artifact F Payload Boundary.
- ADR-016: Bound Cryptographic Verification to Reporting Proof Bodies.
- Canonical transactions C-001 and CT-1.

## 0. Closure Rule

Artifact F covers:

- nine accounting object types;
- ten distinct accounting-event types;
- eleven C-001 accounting-event instances;
- six CT-1 accounting-event instances; and
- seventeen accounting-event instances in total.

A conforming contract version 1 serializer:

1. can serialize and deserialize every in-scope canonical payload without information loss;
2. rejects any field not declared by the selected contract and variant;
3. rejects an inapplicable conditional field even when that field exists in another variant;
4. cannot emit an unlisted object variant, event type, proposal origin, or posted-journal class; and
5. never interprets an `accounting_event` as a `business_event`.

Contract evolution requires a new positive integer `contract_version`. Version 1 contracts behave as if JSON Schema `additionalProperties` is `false` at every object level.

## 1. Explicit Scope

### 1.1 In-scope object contracts

| Object type | Exercised variants |
|---|---|
| `business_event` | `accounting.recognition.due`. |
| `posting_rule` | Active `PR-O2C-RECOG@v1`. |
| `journal_proposal` | Origins `AUTOMATED_POSTING`, `REVERSAL`, `REPLACEMENT`, and `RESTATEMENT_ADJUSTMENT`; terminal states exercised by the canonical traces. |
| `accounting_event` | The ten types in section 5. |
| `journal_entry` | Classes `REVERSAL`, `REPLACEMENT`, and `RESTATEMENT_ADJUSTMENT`. |
| `journal_line` | Lines belonging to J-011, J-012, and J-560. |
| `accounting_period` | States `OPEN`, `SOFT_CLOSED`, and `HARD_CLOSED`. |
| `reporting_version` | Published restatement successor `2026-06@v2`. |
| `restatement_case` | States `PROPOSED`, `ADJUSTMENTS_READY`, `APPROVED`, and `PUBLISHED`. |

### 1.2 Referenced-only payloads

These identifiers are resolved by another owner or by pre-existing state. Artifact F preserves their identity but does not define their payload schema:

- Aegis issue and remediation-directive objects;
- evidence artifacts and their storage representation;
- customer contracts and recognition schedules;
- J-010 and its lines, which predate the CT-1 correction trace;
- reporting version `2026-06@v1` and its statement content;
- policies, checklists, reconciliations, materiality assessments, and disclosure bases; and
- the immutable content addressed by a reporting version.

The reversal constructor must resolve J-010 through the ledger before producing P-REV-010@v1. Artifact F defines the resulting proposal and the reference to J-010, but deliberately does not add an `AUTOMATED_POSTING` journal-entry variant merely to embed the precondition.

The test corpus includes one read-only `referenced_journal_projection` for J-010. It contains only the immutable line tuples needed to prove that J-011 is equal and opposite. The projection is marked `authored_by_f = false`, is not one of the nine accounting objects, and cannot be emitted by an Artifact F domain serializer.

The fixture projection contains exactly:

| Field | Type |
|---|---|
| `fixture_id` | string |
| `projection_type` | constant `referenced_journal_projection` |
| `projection_version` | constant `1` |
| `authored_by_f` | constant `false` |
| `source_hash` | hash of the resolved immutable prior journal snapshot |
| `journal_id` | constant `J-010` |
| `ledger_period_id` | period id |
| `currency` | constant `GBP` |
| `line_tuples` | ordered line values containing the same fields as section 3.6 except `contract_version`, `journal_line_id`, and `journal_id` |

### 1.2.1 Assurance explicitly deferred to runtime resolution

Artifact F proves the checkable ledger-to-presentation chain:

```text
J-560 journal lines
-> frozen adjustment manifest
-> reporting-version lineage, content references, and hashes
```

Artifact F does not prove that the resolved June v2 statement body equals the resolved June v1 statement body plus the manifest. Both statement bodies remain immutable referenced content outside the fixture bundle. That arithmetic must be tested by the reporting runtime after resolving and hash-verifying both content references. This is an explicit deferred acceptance test, not an assurance claim made by the closed fixture set.

### 1.3 Deferred

Version 1 cannot emit:

- any business-event type other than `accounting.recognition.due`;
- any posted-journal class other than the three listed above;
- any accounting-event type outside section 5;
- proposal rejection, supersession, void, approval revocation, exceptional reopen, re-close, or restatement withdrawal payloads;
- financial-statement rows or a statement-body schema;
- an Aegis-owned object body;
- currencies other than GBP; or
- a general posting-rule expression language.

## 2. Cross-Cutting Primitives

### 2.1 Identifiers and versions

- Identifiers are non-empty ASCII strings and are immutable within their object class.
- Human-legible fixture identifiers are authoritative scenario data, not a global numbering policy.
- Versioned objects store family identity and version separately.
- A reference to a versioned object is always fully qualified as `<family-id>@v<positive-integer>`.
- A family identifier alone is invalid where a version reference is required.

Example object identity:

```json
{"proposal_id":"P-551","proposal_version":1,"proposal_ref":"P-551@v1"}
```

### 2.2 Dates and timestamps

- Dates use `YYYY-MM-DD`.
- Period identifiers use `YYYY-MM`.
- Timestamps use RFC 3339 UTC with a trailing `Z`.
- `occurred_at` records when the represented domain action occurred.
- `recorded_at` records when the immutable event was appended.
- Accounting treatment uses an explicit `effective_date` and `ledger_period_id`; it is never inferred from either event timestamp.

### 2.3 Money

- Monetary values are signed or unsigned JSON integers in minor units as specified by the field contract.
- Currency is the ISO 4217 code `GBP` in contract version 1.
- Floating-point and decimal JSON numbers are invalid.
- A journal or proposal line has non-negative `debit_minor` and `credit_minor`; exactly one must be greater than zero.
- Aggregate debit and credit totals must be equal.

Examples:

```text
GBP 120,000 = 12000000
GBP 10,000  = 1000000
```

### 2.4 Hashes

A content hash is the literal prefix `sha256:` followed by 64 lowercase hexadecimal characters. Hashes cover canonical bytes defined by the referenced content's schema version.

### 2.5 Evidence references

An `evidence_ref` contains exactly:

| Field | Type | Rule |
|---|---|---|
| `ref_id` | string | Opaque permanent evidence identity. |
| `description` | string | Non-empty human-readable description. |
| `content_hash` | hash | SHA-256 hash of the referenced immutable content. |

Evidence storage, media type, and Aegis lifecycle are outside Artifact F.

### 2.6 Opaque typed references

An `opaque_ref` contains exactly:

| Field | Type |
|---|---|
| `object_type` | one of `contract`, `recognition_schedule`, `issue`, `remediation_directive`, `policy`, `checklist`, `reconciliation`, `materiality_assessment`, `disclosure_basis` |
| `object_id` | non-empty string |

The identifier is preserved byte-for-byte. Artifact F does not impose the owning domain's numbering rules.

### 2.7 Actor references

An `actor_ref` contains exactly:

| Field | Type |
|---|---|
| `actor_type` | `PERSON` or `SYSTEM_POLICY` |
| `actor_id` | non-empty string |
| `role` | `RULE_ENGINE`, `CORRECTION_ENGINE`, `CONTROLLER`, `CFO`, `POSTING_SERVICE`, or `REPORTING_SERVICE` |

### 2.8 Authorization context

An `authorization` contains exactly:

| Field | Type |
|---|---|
| `authority_mode` | `HUMAN` or `SYSTEM_POLICY` |
| `policy_ref` | `opaque_ref` whose `object_type` is `policy` |

### 2.9 Event identity and retries

- Every accounting event requires a globally unique `event_id`.
- `command_id` is the stable identity of one logical command and remains unchanged across delivery retries.
- Distinct logical commands must use different command identities. A repeated delivery is detected before event append and returns the original outcome; these one-command/one-event lifecycles accept at most one event per `command_id`.
- `correlation_id` is a non-empty trace identity. The canonical fixtures use `C-001` or `CT-1`.
- `causation_event_id` is either `null` for the first accounting event in a trace or the immediately causal accounting-event identity.
- Only `journal.posted` and `reporting_version.published` contain `idempotency_key`.
- `idempotency_key` is scoped to the financial or publication effect and subject. It prevents duplicate effect creation even if a caller incorrectly supplies a different `command_id` for a second attempt.
- Supplying `idempotency_key` on another event type is an unknown-field failure.

### 2.10 Derivation authority

`derivation_authority` has one stable shape:

| Field | Type |
|---|---|
| `authority_kind` | `POSTING_RULE` or `POLICY` |
| `authority_ref` | Fully qualified posting-rule ref when kind is `POSTING_RULE`; policy identity when kind is `POLICY` |

The field is never a string in one variant and an object in another.

## 3. Object Payload Contracts

All object contracts require `contract_version = 1`.

### 3.1 `business_event`

Contract version 1 supports only `event_type = accounting.recognition.due`.

Required fields:

| Field | Type |
|---|---|
| `contract_version` | integer, constant `1` |
| `business_event_id` | string |
| `event_type` | constant `accounting.recognition.due` |
| `correlation_id` | non-empty trace identity; `C-001` in the canonical fixture |
| `occurred_at` | timestamp |
| `recorded_at` | timestamp |
| `effective_date` | date |
| `source_system` | constant `REVENUE_SUBLEDGER` |
| `legal_entity_id` | string |
| `payload` | recognition-due payload |
| `evidence_refs` | non-empty array of `evidence_ref` |

The recognition-due `payload` contains exactly:

| Field | Type |
|---|---|
| `contract_ref` | `opaque_ref` of type `contract` |
| `recognition_schedule_ref` | `opaque_ref` of type `recognition_schedule` |
| `service_period_start` | date |
| `service_period_end` | date |
| `amount_minor` | positive integer |
| `currency` | constant `GBP` |

### 3.2 `posting_rule`

Artifact F does not define a rule language. It defines an immutable, hashed rule-content reference sufficient to reproduce the derivation when resolved.

| Field | Type |
|---|---|
| `contract_version` | integer, constant `1` |
| `posting_rule_id` | constant `PR-O2C-RECOG` |
| `rule_version` | positive integer |
| `posting_rule_ref` | fully qualified version ref |
| `trigger_event_type` | constant `accounting.recognition.due` |
| `effective_from` | date |
| `effective_to` | date or `null` |
| `status` | constant `ACTIVE` |
| `content_ref` | non-empty immutable content reference |
| `content_hash` | hash |
| `content_schema_version` | positive integer |
| `evidence_refs` | non-empty array of `evidence_ref` |

### 3.3 `journal_proposal`

Common required fields:

| Field | Type |
|---|---|
| `contract_version` | integer, constant `1` |
| `proposal_id` | string |
| `proposal_version` | positive integer |
| `proposal_ref` | fully qualified proposal ref matching the prior two fields |
| `status` | `SUBMITTED`, `APPROVED`, `POSTED`, or `DEFERRED` |
| `origin_type` | one of the four in section 1.1 |
| `origin_basis` | discriminated object defined below |
| `target_period_id` | period id |
| `effective_date` | date |
| `ledger_currency` | constant `GBP` |
| `proposed_lines` | ordered array of at least two proposal-line values |
| `total_debit_minor` | positive integer |
| `total_credit_minor` | same value as `total_debit_minor` |
| `prepared_by` | `actor_ref` |
| `created_at` | timestamp |
| `submitted_at` | timestamp |
| `evidence_refs` | non-empty array of `evidence_ref` |

Each proposal line contains exactly:

| Field | Type |
|---|---|
| `line_no` | positive integer unique within the proposal version |
| `account_id` | string |
| `debit_minor` | non-negative integer |
| `credit_minor` | non-negative integer |
| `currency` | constant `GBP` |
| `dimensions` | object containing exactly `legal_entity_id`, `customer_id`, and `contract_id`; the latter two may be `null` |

`origin_basis` is one of:

| `origin_type` | Exact fields in `origin_basis` |
|---|---|
| `AUTOMATED_POSTING` | `business_event_ref`, `posting_rule_ref`, `input_hashes` |
| `REVERSAL` | `reverses_journal_id`, `correction_policy_ref`, `directive_ref`, `input_hashes` |
| `REPLACEMENT` | `corrects_journal_id`, `correction_policy_ref`, `directive_ref`, `input_hashes` |
| `RESTATEMENT_ADJUSTMENT` | `restatement_case_id`, `restatement_policy_ref`, `directive_ref`, `predecessor_proposal_ref`, `input_hashes` |

Policy and directive fields use `opaque_ref`. Each `input_hashes` value is a content hash.

### 3.4 `accounting_event`

The accounting-event object is the shared envelope in section 4 plus exactly one event-type-specific `basis` and `payload` from section 5.

### 3.5 `journal_entry`

Common required fields:

| Field | Type |
|---|---|
| `contract_version` | integer, constant `1` |
| `journal_id` | string |
| `entry_class` | `REVERSAL`, `REPLACEMENT`, or `RESTATEMENT_ADJUSTMENT` |
| `source_proposal_ref` | fully qualified proposal ref |
| `posted_by_event_id` | `journal.posted` event identity |
| `ledger_period_id` | period id |
| `effective_date` | date |
| `posted_at` | timestamp |
| `currency` | constant `GBP` |
| `total_debit_minor` | positive integer |
| `total_credit_minor` | same value as `total_debit_minor` |
| `line_refs` | ordered array of at least two unique journal-line identities |
| `correction_basis` | discriminated object |
| `evidence_refs` | non-empty array of `evidence_ref` |

`correction_basis` is one of:

| `entry_class` | Exact fields |
|---|---|
| `REVERSAL` | `reverses_journal_id` |
| `REPLACEMENT` | `corrects_journal_id`, `directive_ref` |
| `RESTATEMENT_ADJUSTMENT` | `restatement_case_id`, `directive_ref` |

### 3.6 `journal_line`

| Field | Type |
|---|---|
| `contract_version` | integer, constant `1` |
| `journal_line_id` | string |
| `journal_id` | string |
| `line_no` | positive integer unique within the journal |
| `account_id` | string |
| `debit_minor` | non-negative integer |
| `credit_minor` | non-negative integer |
| `currency` | constant `GBP` |
| `dimensions` | exact dimensions object defined for proposal lines |

### 3.7 `accounting_period`

Common fields:

| Field | Type |
|---|---|
| `contract_version` | integer, constant `1` |
| `period_id` | period id |
| `start_date` | date |
| `end_date` | date |
| `status` | `OPEN`, `SOFT_CLOSED`, or `HARD_CLOSED` |
| `ledger_currency` | constant `GBP` |
| `evidence_refs` | array of `evidence_ref` |

State-specific fields are exclusive:

| Status | Additional required fields |
|---|---|
| `OPEN` | `opened_at` |
| `SOFT_CLOSED` | `soft_closed_at`, `soft_close_event_id` |
| `HARD_CLOSED` | `hard_closed_at`, `hard_close_event_id`, `close_policy_ref` |

### 3.8 `reporting_version`

Artifact F defines the publication record, not the statement body.

| Field | Type |
|---|---|
| `contract_version` | integer, constant `1` |
| `reporting_version_id` | string |
| `period_id` | constant `2026-06` in C-001 |
| `version` | positive integer |
| `reporting_version_ref` | fully qualified version ref |
| `predecessor_version_ref` | fully qualified reporting-version ref |
| `restatement_case_id` | string |
| `content_ref` | immutable content reference |
| `content_hash` | hash |
| `content_schema_version` | positive integer |
| `adjustment_manifest_hash` | hash |
| `published_at` | timestamp |
| `published_by_event_id` | `reporting_version.published` event identity |
| `evidence_refs` | non-empty array of `evidence_ref` |

### 3.9 `restatement_case`

All lifecycle snapshots contain the same declared fields; nullability and array cardinality are state-conditional.

| Field | Type |
|---|---|
| `contract_version` | integer, constant `1` |
| `restatement_case_id` | string |
| `status` | `PROPOSED`, `ADJUSTMENTS_READY`, `APPROVED`, or `PUBLISHED` |
| `scope_period_ids` | non-empty ordered array of period ids |
| `trigger_ref` | `opaque_ref` of type `issue` |
| `directive_ref` | `opaque_ref` of type `remediation_directive` |
| `owner_ref` | `actor_ref` |
| `linked_journal_ids` | ordered array of journal ids |
| `adjustment_manifest` | ordered array of manifest-entry values |
| `manifest_hash` | hash or `null` |
| `approver_ref` | `actor_ref` or `null` |
| `approved_at` | timestamp or `null` |
| `published_version_refs` | ordered array of fully qualified reporting-version refs |
| `evidence_refs` | non-empty array of `evidence_ref` |

A manifest entry contains exactly:

| Field | Type |
|---|---|
| `journal_line_ref` | journal-line identity |
| `ledger_period_id` | constant `2026-07` in C-001 |
| `presented_period_id` | constant `2026-06` in C-001 |
| `account_id` | string |
| `debit_minor` | non-negative integer |
| `credit_minor` | non-negative integer |
| `currency` | constant `GBP` |
| `basis_ref` | `opaque_ref` of type `policy` |

State guards:

- `PROPOSED`: manifest is empty, `manifest_hash`, `approver_ref`, and `approved_at` are null, and published versions are empty. Linked journals may be empty or populated.
- `ADJUSTMENTS_READY`: linked journals and manifest are non-empty, `manifest_hash` is non-null, approval fields are null, and published versions are empty.
- `APPROVED`: manifest remains frozen, approval fields are non-null, and published versions are empty.
- `PUBLISHED`: all approval fields remain populated and `published_version_refs` is non-empty.

## 4. Shared Accounting-Event Envelope

Every accounting-event payload contains exactly these common fields before event-specific conditional fields are applied:

| Field | Type |
|---|---|
| `contract_version` | integer, constant `1` |
| `event_id` | string |
| `event_type` | one of the ten types in section 5 |
| `subject_ref` | object containing exactly `object_type` and `object_ref` |
| `command_id` | string |
| `correlation_id` | non-empty trace identity; canonical fixtures use `C-001` or `CT-1` |
| `causation_event_id` | prior accounting-event identity or `null` |
| `occurred_at` | timestamp |
| `recorded_at` | timestamp |
| `actor` | `actor_ref` |
| `authorization` | authorization context |
| `basis` | event-type-specific basis |
| `payload` | event-type-specific payload |
| `evidence_refs` | non-empty array of `evidence_ref` |

`subject_ref.object_type` is one of `journal_proposal`, `accounting_period`, or `restatement_case`. `object_ref` must be fully versioned when its subject is versioned. Immutable `journal_entry` and `reporting_version` records are products of transitions, not transition subjects.

`journal.posted` and `reporting_version.published` additionally require `idempotency_key`. It is prohibited on the other eight event types.

## 5. Ten Accounting-Event Contracts

The following are the only event types contract version 1 can emit.

### 5.1 `proposal.submitted`

`basis` contains exactly:

- `basis_type = PROPOSAL_SUBMISSION`;
- `derivation_authority` using the stable shape in section 2.10;
- `input_hashes` as a non-empty hash array;
- `total_debit_minor`, `total_credit_minor`, and `currency`; and
- `dimensions_resolved = true`.

`payload` contains exactly `proposal_ref`, `from_status = DRAFT`, and `to_status = SUBMITTED`.

### 5.2 `proposal.deferred`

`basis` contains exactly:

- `basis_type = CLOSE_EXCEPTION`;
- `close_policy_ref`;
- `reason_code = RECOGNITION_NOT_POSTED_BEFORE_CLOSE`;
- `owner_ref`;
- `target_treatment = RESTATEMENT_REVIEW`; and
- `expires_on`.

`payload` contains exactly `proposal_ref`, `from_status = SUBMITTED`, and `to_status = DEFERRED`.

### 5.3 `period.hard_closed`

`basis` contains exactly:

- `basis_type = PERIOD_CLOSE`;
- `close_policy_ref`, `checklist_ref`, and `trial_balance_hash`;
- `reconciliation_refs`;
- `unresolved_submitted_count = 0`;
- `unresolved_approved_count = 0`; and
- `deferred_proposal_refs`, containing `P-551@v1` in C-001.

`payload` contains exactly `period_id`, `from_status = SOFT_CLOSED`, and `to_status = HARD_CLOSED`.

### 5.4 `restatement.proposed`

`basis` contains exactly:

- `basis_type = RESTATEMENT_INITIATION`;
- `trigger_ref`, `directive_ref`, and `materiality_ref`; and
- `scope_period_ids`.

`payload` contains exactly `restatement_case_id` and `to_status = PROPOSED`.

### 5.5 `proposal.approved`

`basis` contains exactly:

- `basis_type = PROPOSAL_APPROVAL`;
- `decision_maker`;
- `sod_check_passed = true`;
- `period_guard_state = OPEN`; and
- `period_guard_passed = true`.

`payload` contains exactly `proposal_ref`, `from_status = SUBMITTED`, and `to_status = APPROVED`.

### 5.6 `journal.posted`

This event additionally requires `idempotency_key`.

`basis` contains exactly:

- `basis_type = JOURNAL_POSTING`;
- `proposal_ref`;
- `balance_debit_minor`, `balance_credit_minor`, and `currency`;
- `period_id` and `period_state = OPEN`; and
- `period_guard_passed = true`.

`payload` contains exactly `proposal_ref`, `journal_id`, `entry_class`, `from_status = APPROVED`, and `to_status = POSTED`.

### 5.7 `restatement.adjustment_linked`

`basis` contains exactly:

- `basis_type = RESTATEMENT_LINK`;
- `restatement_case_id`;
- `journal_id`;
- `entry_class = RESTATEMENT_ADJUSTMENT`; and
- `class_check_passed = true`.

`payload` contains exactly `restatement_case_id`, `journal_id`, and `status = PROPOSED`.

### 5.8 `restatement.adjustments_ready`

`basis` contains exactly:

- `basis_type = RESTATEMENT_MANIFEST`;
- `restatement_case_id`;
- `linked_journal_ids`;
- `manifest_hash`;
- `manifest_debit_minor`, `manifest_credit_minor`, and `currency`; and
- `reconciles_to_journal_lines = true`.

`payload` contains exactly `restatement_case_id`, `from_status = PROPOSED`, and `to_status = ADJUSTMENTS_READY`.

### 5.9 `restatement.approved`

`basis` contains exactly:

- `basis_type = RESTATEMENT_APPROVAL`;
- `restatement_case_id`;
- `manifest_hash`;
- `materiality_ref`; and
- `disclosure_basis_ref`.

`payload` contains exactly `restatement_case_id`, `from_status = ADJUSTMENTS_READY`, and `to_status = APPROVED`.

### 5.10 `reporting_version.published`

This event additionally requires `idempotency_key`.

Its `subject_ref` is the transitioning `restatement_case` RC-001. The immutable reporting version created by publication appears in `payload.reporting_version_ref`.

`basis` contains exactly:

- `basis_type = REPORTING_PUBLICATION`;
- `restatement_case_id`;
- `predecessor_version_ref`;
- `manifest_hash`;
- `content_ref`, `content_hash`, and `content_schema_version`; and
- `publication_policy_ref`.

`payload` contains exactly `reporting_version_ref`, `restatement_case_id`, `restatement_from_status = APPROVED`, and `restatement_to_status = PUBLISHED`.

## 6. Canonical Instance Inventory

### 6.1 C-001 object identities

| Object type | Canonical identities |
|---|---|
| `business_event` | `BE-C001-RECOG-202606`. |
| `posting_rule` | `PR-O2C-RECOG@v1`. |
| `journal_proposal` | `P-551@v1`, `P-551@v2`. |
| `accounting_period` | `2026-06`, `2026-07`. |
| `restatement_case` | `RC-001`. |
| `journal_entry` | `J-560`. |
| `journal_line` | `J-560-L1`, `J-560-L2`. |
| `reporting_version` | `RV-2026-06@v2`; predecessor `RV-2026-06@v1` is referenced-only. |

J-560 contains:

```text
Dr ACC-DEFERRED-REVENUE       1,000,000 minor units
Cr ACC-SUBSCRIPTION-REVENUE   1,000,000 minor units
ledger period                 2026-07
presented period              2026-06
```

### 6.2 CT-1 object identities

| Object type | Canonical identities |
|---|---|
| Referenced prior journal | `J-010`; payload deferred from F. |
| `journal_proposal` | `P-REV-010@v1`, `P-REP-010@v1`. |
| `journal_entry` | `J-011`, `J-012`. |
| `journal_line` | `J-011-L1`, `J-011-L2`, `J-012-L1`, `J-012-L2`. |
| `accounting_period` | `2026-07`. |

J-011 contains:

```text
Dr ACC-AR / CUST-VEGA          12,000,000 minor units
Cr ACC-UNAPPLIED-CASH          12,000,000 minor units
```

J-012 contains:

```text
Dr ACC-UNAPPLIED-CASH          12,000,000 minor units
Cr ACC-AR / CUST-ORION         12,000,000 minor units
```

## 7. Worked Accounting-Event Traces

The exact serialized fixtures live beside this document:

- `fixtures/canonical-object-payloads.jsonl` contains canonical payloads for the eight non-event accounting object types. The two accounting-event files provide the ninth type and complete the nine-object union. The outer `fixture_id` / `object_type` / `payload` wrapper belongs only to the test fixture; only the nested `payload` is the domain object.
- `fixtures/restatement-case-snapshots.jsonl` demonstrates every exercised non-terminal RC-001 state, including both empty and linked `PROPOSED` forms. The terminal `PUBLISHED` form remains in the canonical object fixture file.
- `fixtures/referenced-state-projections.jsonl` contains the non-authored J-010 projection used only for equal-and-opposite testing.
- `fixtures/reporting-content-proof-bodies.jsonl` contains the two non-domain, test-only canonical bodies used to resolve and cryptographically verify the June v1-to-v2 reporting bridge.
- `fixtures/c001-accounting-events.jsonl` contains eleven JSON objects.
- `fixtures/ct1-accounting-events.jsonl` contains six JSON objects.

### 7.1 C-001 trace

| Sequence | Event id | Event type | Subject |
|---|---|---|---|
| 1 | `AE-C001-001` | `proposal.submitted` | `P-551@v1` |
| 2 | `AE-C001-002` | `proposal.deferred` | `P-551@v1` |
| 3 | `AE-C001-003` | `period.hard_closed` | `2026-06` |
| 4 | `AE-C001-004` | `restatement.proposed` | `RC-001` |
| 5 | `AE-C001-005` | `proposal.submitted` | `P-551@v2` |
| 6 | `AE-C001-006` | `proposal.approved` | `P-551@v2` |
| 7 | `AE-C001-007` | `journal.posted` | `P-551@v2` |
| 8 | `AE-C001-008` | `restatement.adjustment_linked` | `RC-001` |
| 9 | `AE-C001-009` | `restatement.adjustments_ready` | `RC-001` |
| 10 | `AE-C001-010` | `restatement.approved` | `RC-001` |
| 11 | `AE-C001-011` | `reporting_version.published` | `RC-001` |

### 7.2 CT-1 trace

| Sequence | Event id | Event type | Subject |
|---|---|---|---|
| 1 | `AE-CT1-001` | `proposal.submitted` | `P-REV-010@v1` |
| 2 | `AE-CT1-002` | `proposal.approved` | `P-REV-010@v1` |
| 3 | `AE-CT1-003` | `journal.posted` | `P-REV-010@v1` |
| 4 | `AE-CT1-004` | `proposal.submitted` | `P-REP-010@v1` |
| 5 | `AE-CT1-005` | `proposal.approved` | `P-REP-010@v1` |
| 6 | `AE-CT1-006` | `journal.posted` | `P-REP-010@v1` |

The union is ten distinct event types. CT-1 adds six instances but no eleventh event type.

## 8. Closure and Rejection Tests

### 8.1 Positive tests

| Test | Expected result |
|---|---|
| F-P01 | Deserialize every nested canonical object payload using the contract selected by its fixture wrapper. |
| F-P02 | Deserialize and reserialize all eleven C-001 events byte-equivalently after canonical key ordering. |
| F-P03 | Deserialize and reserialize all six CT-1 events byte-equivalently after canonical key ordering. |
| F-P04 | Resolve every non-null `causation_event_id` to the immediately preceding causal event in the same correlation. |
| F-P05 | Reconcile every proposal, journal, and posted-event debit and credit total. |
| F-P06 | Confirm that only the original C-001 business event is eligible for the posting-rule evaluator. |
| F-P07 | Reconcile the C-001 manifest totals and line references to J-560. |
| F-P08 | First prove `J-010 projection.source_hash = P-REV-010@v1 origin_basis.input_hashes[0]`; then prove J-011 is mechanically equal and opposite by account, dimensions, currency, and amount. |
| F-P09 | Deserialize the empty and linked `PROPOSED`, `ADJUSTMENTS_READY`, `APPROVED`, and `PUBLISHED` RC-001 snapshots against their state guards. |
| F-P10 | Stateful harness: redeliver a logical command under the same `command_id` and return the original result without appending another event. |

### 8.2 Negative tests

| Test | Mutation | Expected rejection |
|---|---|---|
| F-N01 | Add any undeclared field at any nesting level. | Unknown field. |
| F-N02 | Encode a monetary value as `120000.00`. | Non-integer money. |
| F-N03 | Use `P-551` where a proposal version ref is required. | Incomplete version reference. |
| F-N04 | Add `idempotency_key` to `proposal.submitted`. | Inapplicable conditional field. |
| F-N05 | Remove `idempotency_key` from `journal.posted` or publication. | Missing required conditional field. |
| F-N06 | Emit `AUTOMATED_POSTING` as `journal_entry.entry_class`. | Unexercised variant. |
| F-N07 | Emit an event type outside section 5. | Unknown discriminator. |
| F-N08 | Use an `accounting_event` as posting-rule input. | Event-stream firewall violation. |
| F-N09 | Include `corrects_journal_id` in a reversal basis. | Cross-variant field leakage. |
| F-N10 | Include `reverses_journal_id` in a restatement adjustment. | Cross-variant field leakage. |
| F-N11 | Change a manifest amount without changing `manifest_hash`. | Integrity failure. |
| F-N12 | Publish with predecessor `RV-2026-06` rather than `RV-2026-06@v1`. | Incomplete version reference. |
| F-N13 | Use ledger period `2026-06` for J-560. | Hard-closed-period violation. |
| F-N14 | Use a presented period outside RC-001 scope. | Restatement-scope violation. |
| F-N15 | Repeat a posting or publication idempotency key. | Duplicate financial effect. |
| F-N16 | Supply an Aegis issue body rather than an opaque reference. | Ownership-boundary violation. |
| F-N17 | Set `unresolved_submitted_count` above zero on `period.hard_closed`. | Unresolved-proposal close violation. |
| F-N18 | Set `unresolved_approved_count` above zero on `period.hard_closed`. | Approved-but-unposted close violation. |
| F-N19 | Set `sod_check_passed` to false on `proposal.approved`. | Segregation-of-duties violation. |
| F-N20 | Change a J-011 account, dimension, side, currency, or amount so it is not equal and opposite to J-010. | Reversal-integrity violation. |
| F-N21 | Stateful harness: attempt to append a new event under a `command_id` that already produced an event. | Duplicate command production. |

## 9. Ratification Basis

Artifact F v0.2 is ratified on the following basis:

1. the scope inventory contains no object or event needed only by a hypothetical future scenario;
2. every field in sections 2 through 5 appears in at least one canonical object or event fixture, except fields required to express an exercised conditional state;
3. every object fixture and all seventeen event fixtures parse as JSON and match their declared contract;
4. the ten-type and seventeen-instance counts are machine-checkable;
5. no float, ambiguous family reference, undeclared field, or accounting-event posting trigger can pass validation;
6. C-001 preserves the separation between July 2026 ledger effect and June 2026 presentation effect; and
7. CT-1 proves reversal and replacement while J-010 remains immutable, non-authored referenced prior state;
8. the fixture bundle proves J-011 is mechanically equal and opposite to the J-010 projection; and
9. the document explicitly defers June v1-to-v2 statement-body arithmetic to runtime content resolution rather than claiming fixture-level proof.

Artifact H now defines the executable acceptance boundary for translating these
contracts into schemas and tests. The Milestone 1 roadmap selects Pydantic v2
as a reversible implementation choice; Artifact F itself remains independent
of schema technology.

### 9.1 v0.2.1 reporting-proof fixture revision

Artifact F v0.2.1 does not change a domain field, object variant, event type,
serializer rule, or authored-object count.

It adds two non-domain reporting proof bodies:

| Reporting version | Canonical body SHA-256 |
|---|---|
| `RV-2026-06@v1` | `sha256:3063f711a55ac58193d7c80072ff3bd24e18ba31a2fd9de0b7171d8c5cb120fd` |
| `RV-2026-06@v2` | `sha256:4671f8ba1b80e250c39b50c9f4e15d5aa5efa82cc4b50ac3cc72e52758cbdfd5` |

The v2 hash replaces the earlier illustrative value wherever the reporting
version and publication event refer to that exact content. Other evidence
hashes remain illustrative declared values. Artifact F requires their format,
reference consistency, and immutability but does not claim content-byte
verification for them.
