# Artifact Q - Governed Analytical Read Registry and Shared Semantic Dataset Contract

Status: Design v0.2 - ratified 2026-08-13

Resolution basis: all nine blocking findings in
`docs/roadmap/milestone-4-artifact-q-v01-critique.md` are incorporated below.

## 0. Purpose and Closure Rule

Artifact Q defines the finite governed analytical-read boundary required before
the Finance & Assurance Platform may create an Excel model or Power BI semantic
model.

Artifact P proved that exact public evidence can cross a deterministic,
offline-verifiable package boundary. It deliberately did not expose journal
lines, ledger semantics, source objects, or stable analytical dimensions.
Artifact Q adds only those missing products needed by the first shared local
consumer journeys. It does not create a warehouse, a second ledger, a generic
record export, or a consumer-specific finance model.

The analytical boundary closes only when:

1. `Q-ANALYTICS@v1` is assembled in the same package and from the same pinned
   runtime query session as `P-EVIDENCE@v1`;
2. its finite exact-query registry supplies the minimum journal, account,
   source-object, period, and posting-rule grains needed by both consumers;
3. every domain value comes from an exact authoritative record or one explicit
   Atlas-owned governed configuration version;
4. P's reporting, readiness, assurance, governance, decision, evidence, and
   trace datasets are reused by relationship rather than copied or rewritten;
5. account names, classifications, normal balances, control roles, and
   statement mappings come from an exact ledger-semantics catalogue and are
   never inferred from account identifiers;
6. C-001 and CT-1 remain distinct, parameterised, and fully traceable at their
   currently ratified depth;
7. the complete multi-registry package passes Artifact P's checksum, schema,
   relationship, snapshot, compatibility, atomicity, and reproduction rules;
   and
8. neither Excel nor Power BI is authorised until this registry is separately
   ratified, implemented, and cohesion-audited.

## 1. Binding Sources

Artifact Q is constrained by:

- the five repository invariants in `AGENTS.md`;
- Artifact G v0.2, module ownership and publish/consume contracts;
- Artifact I v0.2.2, finite application commands and queries;
- Artifact J v0.2, authoritative records and rebuildable projections;
- Artifact K v0.2.2, query sessions and persistence boundaries;
- Artifact L v0.2.1, strict internal runtime messages;
- Artifact N v0.2.1, persisted-contract compatibility;
- Artifact O v0.2, exact public product reads;
- Artifact P v0.2, verified package, registry, relationship, and evidence rules;
- C-001, the hard-close restatement reference transaction;
- CT-1, the open-period reversal and replacement reference transaction;
- ADR-035, Artifact P ratification; and
- ADR-036, implemented `P-EVIDENCE@v1` and its cohesion audit.

Artifact Q may add a typed application read and one exact governed
configuration prerequisite. It may not weaken an upstream ownership,
compatibility, readiness, evidence, or correction rule.

## 2. Product Outcome and First Use Cases

The product path becomes:

```text
ordinary runtime authority
-> one pinned query session
-> P-EVIDENCE@v1 exact public evidence
-> Q-ANALYTICS@v1 exact analytical reads
-> one verified multi-registry package
-> Excel consumer adapter
-> Power BI consumer adapter
```

Artifact Q is driven by four bounded use cases.

### Q-U01 - Journal explorer

Inspect posted journal headers and immutable lines by period, account, legal
entity, customer, contract, entry class, and exact source basis.

The user may compare exact debits and credits and may calculate a labelled
signed display amount. The consumer may not replace the platform's journal,
posting, or balance authority.

### Q-U02 - Restatement-to-ledger bridge

Start with the exact P-D07 June restatement bridge, follow its reporting version
and readiness context, and inspect the J-560 header and lines that support the
GBP 10,000 adjustment while June remains hard-closed.

The bridge amount comes from P-D07. It is not recomputed from journal lines and
then promoted as a replacement platform conclusion.

### Q-U03 - Correction-integrity drill-through

Start with the P-D13 CT-1 correction case, inspect the referenced J-010 source
projection separately from authored journals J-011 and J-012, and drill to the
exact reversal and replacement lines.

The source projection never becomes an authored journal. P-D13 remains the
authority for bind-before-compare status, corrected identity, and zero net
control-account movement.

### Q-U04 - Governed decision context

Place exact reporting values, purpose-specific readiness, frozen planning
inputs, and the governed decision beside the ledger facts that contributed to
the corrected reporting state.

P-D10 through P-D12 remain the authorities for readiness and decision use.
Artifact Q contributes drill-through context only.

## 3. Explicit Non-Goals

Artifact Q does not define:

- an Excel workbook, formulas, named ranges, or workbook layout;
- a Power BI project, DAX measure, theme, or visual;
- a trial-balance fact not already supported by posted journal records;
- a synthetic transaction-volume generator;
- a general ledger warehouse or arbitrary SQL access layer;
- generic enumeration of J-AR records;
- customer, vendor, employee, product, or legal-entity master-data catalogues;
- a new accounting event, posting workflow, readiness decision, or control;
- inferred account semantics derived from identifier text;
- an adapted or `TYPED_TARGET` public read;
- a paid API, credential, hosted dependency, or runtime network service; or
- a claim that canonical C-001 and CT-1 depth resembles an enterprise-scale
  analytical population.

## 4. Vocabulary

### 4.1 Governed analytical read

A strict, read-only application view assembled from named exact authoritative
records at one pinned query revision. It is not an authoritative record itself.

### 4.2 Ledger-semantics catalogue

An Atlas-owned exact J-AR04 configuration version defining the finite account
and statement-line semantics required to interpret the exported journal lines.
It is finance-domain configuration, not export metadata.

### 4.3 Analytical registry

The closed `Q-ANALYTICS@v1` set of sixteen dataset contracts. Registry identity
is distinct from `P-EVIDENCE@v1`; dataset identifiers are registry-qualified.

### 4.4 Domain value

A value whose meaning belongs to Hermes, Atlas, Argus, Aegis, Pythia, or the
shared runtime substrate. Domain values require exact source provenance.

### 4.5 Export metadata

Package mechanics such as `row_key`, query instance identity, registry version,
file path, schema version, and source ordinal. Export metadata may organise
domain values but may not change their meaning.

### 4.6 Consumer calculation

A formula owned by Excel or Power BI and visibly labelled as non-authoritative.
It may format or analyse governed inputs but cannot become a platform fact.

## 5. Binding Rulings

### Q-R01 - One multi-registry snapshot

Q-C01 opens one query session and uses it for P-Q00, all Artifact O queries,
Q-Q00, and every Artifact Q query. Opening a second analytical session is
prohibited.

### Q-R02 - The evidence registry is mandatory

`Q-ANALYTICS@v1` depends on `P-EVIDENCE@v1`. A package may contain P alone, but
it may not contain Q without P. An analytical consumer rejects a package that
does not contain and verify both exact registry versions.

Q-C01 is a new strict build request. It does not change P-C01's ratified
evidence-only contract or cause an existing evidence package to gain files.
Existing P-only packages remain verifiable and reproducible. A newly built
P-only package may have different snapshot values and bytes when the underlying
authoritative inventory legitimately changes.

### Q-R03 - Registry identity remains separate

Q-D01 through Q-D16 are registered only under `Q-ANALYTICS@v1`. They are never
silently appended to `P-EVIDENCE@v1`.

### Q-R04 - Exact-original reads only

Every domain source is `EXACT_ORIGINAL`. A future Artifact N adapted read needs
an explicit Artifact Q contract revision before it can enter a public package.

### Q-R05 - No persistence-shaped export boundary

The exporter consumes typed Artifact Q views. It cannot call SQLite, inspect
tables, receive a `QuerySession`, call `authoritative_records()` generically, or
accept raw J-AR envelopes as its public input.

### Q-R06 - Finite parameterised discovery

Q-Q00 receives an explicit typed descriptor whose identities come from the
composition root and parameterised scenario outputs. Q-C01 then reconciles
those identities exactly to the already-executed P/O evidence views before the
Q plan is accepted. Reusable query or export code cannot branch on `C-001`,
`CT-1`, J-560, J-011, J-012, J-010, or equivalent canonical literal patterns.

### Q-R07 - Q-Q00 does not create semantic authority

Q-Q00 identifies the closed subject plan and binds its descriptor hash. Q-D16
retains that basis for offline verification and reproduction. Discovery does
not become a finance, assurance, governance, or planning fact.

### Q-R08 - Account semantics require governed configuration

Account labels, account classes, normal balances, statement classes, control
roles, and statement-field mappings must come from one exact Atlas-owned
J-AR04 ledger-semantics catalogue. They cannot be parsed from `account_id`.

### Q-R09 - The catalogue is not a new accounting workflow

The ledger-semantics catalogue is admitted through the existing runtime
baseline mode. It cannot trigger posting, create an accounting event, alter a
posted journal, or enter the business-event posting engine.

### Q-R10 - Posted journal records remain exact and immutable

Q journal views copy J-AR08 header and ordered-line fields without rewriting
amounts, dates, periods, dimensions, or source identities.

### Q-R11 - Origin context is resolved, not guessed

The journal view may add origin context only by resolving the exact
`source_proposal_ref`, its J-AR05 treatment, and its declared origin basis.
Variant fields for other origin classes remain null.

### Q-R12 - Referenced state remains a separate class

The G-13/J-AR17 J-010 projection is exported only through referenced-journal
datasets. It cannot appear in authored journal datasets or acquire a J-AR08
semantic hash.

### Q-R13 - Business events remain the causal substrate

Q-D07 contains admitted J-AR03 business events only. Accounting events may
appear as journal lifecycle references, but they never become posting inputs or
business-event rows.

### Q-R14 - Accounting-period state must be exact

Q-D10 uses either exact J-AR07 base facts or an exact G-04/J-AR13 transition
publication at a named state token. It cannot export a rebuildable current
projection as if it were an immutable period version or infer state from a
journal posting date.

### Q-R15 - Posting rules remain content-addressed

Q-D11 copies the exact posting-rule identity, effective dates, content
reference, content hash, and evidence state. It does not invent posting-rule
logic from the journal lines that happened to result.

### Q-R16 - Input hashes remain ordered child facts

Proposal origin `input_hashes[]` become Q-D06 child rows in exact source order.
They are not joined into a delimited cell, sorted, deduplicated, or promoted to
verified bytes without an exact proof.

### Q-R17 - Evidence remains explicit and status-labelled

Evidence references on the ledger-semantics catalogue, journals, business
events, periods, and posting rules become Q-D12 rows. A hash is
`CONTENT_BYTES_VERIFIED` only when an exact proof resolves and verifies; all
other valid hashes remain `DECLARED_HASH_ONLY`.

### Q-R18 - Money remains integer minor units

Every governed amount is an integer minor-unit value paired with ISO-4217
currency. Floats and package-owned major-unit values are prohibited.

### Q-R19 - Artifact P facts are reused, not copied

Reporting values, restatement bridges, exceptions, governance cases,
readiness, limitations, governed decisions, correction conclusions, and J-P11
trace graphs remain only in P-D04 through P-D20. Q relates to those rows through
registered keys.

### Q-R20 - Cross-registry joins are declared

Matching field names do not create relationships. Every permitted P-to-Q or
Q-to-P join is registry-qualified, cardinality-labelled, and classified as
`CONSUMER_RELATIONSHIP` or `INTEGRITY_ONLY`.

### Q-R21 - Readiness cannot be inferred from ledger presence

The presence of a posted journal, balanced lines, verified content, or an
account mapping never implies fitness for a purpose. Controlled consumers must
use P-D10 together with P-D15 and P-D20.

### Q-R22 - Query source closure is invocation-local

Each Q query creates one Q-D13 execution row and only its own family-qualified
exact Q-D14 source rows. A reader reused across invocations cannot accumulate
source references.

### Q-R23 - Domain values and transport metadata stay separate

Q-D01 through Q-D12 and Q-D15 contain domain or evidence values plus only
stable keys. Q-D13, Q-D14, and Q-D16 contain query/export provenance. File names,
worksheet names, Power BI table names, routes, colours, and display formats are
excluded.

### Q-R24 - No volume is added for visual appeal

Version 1 proves the analytical contract at canonical depth. It cannot generate
extra months, customers, journals, or exceptions merely to populate a chart.

### Q-R25 - Consumer calculations are explicitly subordinate

Permitted consumer calculations include major-unit formatting, debit-minus-
credit signed display values, ratios, filters, and presentation totals. Each is
labelled `CONSUMER_CALCULATION` and cannot replace an exact P or Q value.

### Q-R26 - Unsupported or incomplete authority fails closed

Missing catalogue entries, unresolved journal lines, absent exact proposals,
ambiguous period tokens, broken referenced projections, or missing required P
rows reject the analytical registry build. Partial tables are not emitted.

### Q-R27 - Ordering and keys are deterministic

Query plans, dataset rows, evidence references, input hashes, schema columns,
relationship entries, and source rows have explicit deterministic ordering.
Repository or database iteration order is never relied upon.

### Q-R28 - Multi-registry verification is atomic

P-C02 verifies the complete declared registry set, all cross-registry
relationships, and the single package digest. P-only packages use relationship
contract v1; P-plus-Q packages use the closed relationship contract v2 defined
here. The verifier cannot declare P verified and silently ignore a broken Q
registry in the same package.

### Q-R29 - Consumer relationship parity is shared

Excel and Power BI receive the same `CONSUMER_RELATIONSHIP` registry. A
consumer may choose presentation-specific subsets, but it cannot invent a
different authoritative key or cardinality.

### Q-R30 - Canonical depth is disclosed

The package README and both later consumers must state that version 1 contains
the bounded C-001 and CT-1 reference cases. It proves governed integration and
traceability, not statistical coverage or enterprise transaction volume.

## 6. Exact Baseline Prerequisites

### 6.1 Ledger-semantics catalogue

Artifact Q introduces one baseline prerequisite:

```text
record_family: J-AR04
record_identity: LEDGER-SEMANTICS-DEMO@v1
owner: Atlas
contract: atlas.ledger_semantics_catalog@v1
```

The identifier above is illustrative composition-root data. Reusable code uses
the exact catalogue reference supplied by Q-Q00.

The strict body contains:

```text
contract_version
catalog_id
catalog_version
catalog_ref
effective_from
effective_to
status
accounts[]
statement_lines[]
mappings[]
evidence_refs[]
```

Each `accounts[]` entry contains exactly:

```text
account_id
account_name
account_class             # ASSET | LIABILITY | EQUITY | REVENUE | EXPENSE
normal_balance            # DEBIT | CREDIT
control_role              # AR | UNAPPLIED_CASH | NONE
```

Each `statement_lines[]` entry contains exactly:

```text
statement_field
statement_label
statement_class           # BALANCE_SHEET | INCOME_STATEMENT
display_order
```

Each `mappings[]` entry contains exactly:

```text
account_id
statement_field
mapping_role              # PRIMARY
```

Version 1 contains exactly the four accounts and four statement lines exercised
by C-001 and CT-1, with one primary mapping for each account. No other account
or statement line is added in anticipation of a future process.

The canonical v1 catalogue entries are fixed as:

| Account id | Account name | Class | Normal balance | Control role | Statement field | Statement label | Statement class | Display order |
|---|---|---|---|---|---|---|---|---:|
| `ACC-AR` | Accounts receivable | `ASSET` | `DEBIT` | `AR` | `accounts_receivable_minor` | Accounts receivable | `BALANCE_SHEET` | 10 |
| `ACC-DEFERRED-REVENUE` | Deferred revenue | `LIABILITY` | `CREDIT` | `NONE` | `deferred_revenue_minor` | Deferred revenue | `BALANCE_SHEET` | 20 |
| `ACC-UNAPPLIED-CASH` | Unapplied cash | `LIABILITY` | `CREDIT` | `UNAPPLIED_CASH` | `unapplied_cash_minor` | Unapplied cash | `BALANCE_SHEET` | 30 |
| `ACC-SUBSCRIPTION-REVENUE` | Subscription revenue | `REVENUE` | `CREDIT` | `NONE` | `subscription_revenue_minor` | Subscription revenue | `INCOME_STATEMENT` | 10 |

The account, statement-line, and mapping arrays serialize independently in
their registered deterministic orders. The table above is a compact semantic
presentation, not permission to duplicate the mapping inside `accounts[]`.

The persisted record uses a registered exact-original contract stamp for
`atlas.ledger_semantics_catalog@v1`. The runtime baseline manifest names that
exact identity and hash, and Artifact N startup compatibility validation must
accept the stamp before any Q query is available. Version 1 has no compatibility
adapter or typed-target read path.

The catalogue has exactly one evidence reference, and baseline admission also
includes the matching exact J-AR12 evidence record. The evidence content hash
remains `DECLARED_HASH_ONLY` unless separately committed canonical content bytes
justify promotion; admission of the J-AR12 record alone does not verify those
external bytes.

Catalogue validation requires:

- identity/version consistency;
- unique account and statement-field identities;
- every account mapping to one declared statement field;
- positive unique display order within each statement class;
- an account class compatible with its declared normal balance and mapped
  statement class under the exact v1 matrix below;
- exact evidence references; and
- no field outside the contract.

This catalogue does not create reporting values. It identifies how exact
ledger accounts are described and grouped when a consumer analyses them.

The exact v1 compatibility matrix is:

| Account class | Normal balance | Permitted statement class | Permitted control role |
|---|---|---|---|
| `ASSET` | `DEBIT` | `BALANCE_SHEET` | `AR` or `NONE` |
| `LIABILITY` | `CREDIT` | `BALANCE_SHEET` | `UNAPPLIED_CASH` or `NONE` |
| `EQUITY` | `CREDIT` | `BALANCE_SHEET` | `NONE` |
| `REVENUE` | `CREDIT` | `INCOME_STATEMENT` | `NONE` |
| `EXPENSE` | `DEBIT` | `INCOME_STATEMENT` | `NONE` |

Contra accounts and any additional control role require a future catalogue
contract version rather than an undocumented exception.

### 6.2 Accounting-period base facts

The canonical July correction period is baseline-admitted as an exact J-AR07
record. Its identity, dates, currency, initial `OPEN` state, and evidence are the
authoritative base facts from which J-P04 is rebuilt.

June `HARD_CLOSED` remains sourced from the exact G-04 J-AR13 publication at the
hard-close event token. Q does not manufacture a July `period.opened` event or
G-04 publication merely to make the two variants look alike.

## 7. Finite Query and View Registry

Artifact Q defines seven query types and seven corresponding view contracts.
All queries require `query_id`, `query_contract_version`, `scenario_ref` or
workspace scope as applicable, `semantic_as_of_time`, and their exact subject
coordinates.

### Q-Q00 / Q-V00 - ResolveAnalyticalPlan

Consumes the strict Q discovery descriptor and returns:

- descriptor identity and hash;
- exact `Q-ANALYTICS@v1` registry identity;
- required `P-EVIDENCE@v1` dependency;
- workspace and scenario set;
- exact ledger-semantics catalogue reference;
- three authored-journal requests;
- one admitted-business-event request;
- one referenced-journal request;
- two exact accounting-period requests with declared source variants;
- one posting-rule request; and
- the deterministic ordered query plan.

Q-Q00 does not enumerate persistence. After the P/O plan has executed in the
same session, it requires exact set equality between the descriptor and:

```text
C-001 journal, event, and posting rule  <-> O-V10 directed trace nodes
CT-1 journals and source projection     <-> O-V11 correction view
June reporting period                   <-> O-V04/O-V05
July correction period                  <-> exact selected journal periods
scenario membership                     <-> P-V00/O-V01
```

The ledger-semantics catalogue reference is the only new authority supplied by
the Q descriptor. Extra, missing, duplicate, or cross-scenario subjects reject
the plan.

### Q-Q01 / Q-V01 - GetLedgerSemantics

Returns one exact typed `atlas.ledger_semantics_catalog@v1` J-AR04 record and
its source envelope identity. Other J-AR04 configuration classes are rejected.

### Q-Q02 / Q-V02 - GetAuthoredJournal

Returns one exact J-AR08 journal header, all ordered exact J-AR08 lines, the
exact J-AR05 source proposal treatment, the posting accounting event, and the
strictly resolved origin fields applicable to that proposal variant.

For C-001 only, Q-V02 may follow the proposal's exact declared
`predecessor_proposal_ref` once to recover the automated business-event and
posting-rule origin. A missing predecessor, a second predecessor hop, or any
generic transitive traversal is rejected. Q-V02 is not a replacement J-P11
trace engine.

It is invoked three times in v1: once for C-001 and twice for CT-1.

### Q-Q03 / Q-V03 - GetSourceBusinessEvent

Returns one admitted J-AR03 business event with its exact temporal, source,
legal-entity, contract, recognition-schedule, service-period, amount, currency,
and evidence fields.

### Q-Q04 / Q-V04 - GetReferencedJournal

Returns a strict bound pair:

- one exact J-AR17 referenced source containing the immutable journal body; and
- one exact G-13 J-AR13 publication containing the projection class,
  `authored_by_f`, declared source hash, publication basis, and authoritative
  source reference.

Q-V04 emits no result unless G-13 `source_hash` equals the J-AR17 semantic hash,
the publication's upstream authoritative reference identifies that exact
J-AR17 record and hash, and the shared source fields (`journal_id`,
`ledger_period_id`, `currency`, and ordered `line_tuples`) are exactly equal.
Projection metadata is validated separately; the two complete payloads are not
claimed to be byte-identical.

### Q-Q05 / Q-V05 - GetAccountingPeriodState

Returns one strict state-basis variant:

```text
BASE_FACT
  -> exact J-AR07 period base facts and semantic hash

TRANSITION_PUBLICATION
  -> exact G-04 J-AR13 view at the named lifecycle token
     plus the exact J-AR06 transition event
```

The July correction period uses `BASE_FACT`. The June hard-close state uses
`TRANSITION_PUBLICATION`. A J-P04 current projection is never a Q-V05 source.

It is invoked for the June reporting period and July correction period.

### Q-Q06 / Q-V06 - GetPostingRuleBasis

Returns one exact J-AR04 posting rule whose identity matches the C-001 proposal
origin, including content-address and evidence fields.

The v1 plan contains ten invocations in exact order:

```text
Q-Q00 x 1
Q-Q01 x 1
Q-Q02 x 3
Q-Q03 x 1
Q-Q04 x 1
Q-Q05 x 2
Q-Q06 x 1
```

## 7A. Analytical Build Operation

### Q-C01 - BuildGovernedAnalyticalExport

Q-C01 is the only new package-producing operation. Its strict request contains:

```text
request_contract_version       # governed-analytical-export-request@v1
export_ref
workspace_ref
semantic_as_of
exported_at
output_path
p_discovery_descriptor_ref
q_discovery_descriptor_ref
```

The required registry set is fixed by the request contract as:

```text
P-EVIDENCE@v1
Q-ANALYTICS@v1
```

The caller cannot supply an arbitrary registry list. Q-C01 delegates to the
same canonical serializers, schemas, relationship registry, staging discipline,
checksum ledger, package digest, and atomic promotion machinery as Artifact P.
It emits the existing `governed-export-package@v1` package format.

P-C01 remains the evidence-only build operation. P-C02 verifies either the
ratified P-only registry set or the ratified P-plus-Q set declared by a package.
Q-D16 retains the second discovery basis needed by a P-plus-Q package. P-C03
reproduces the exact registry set and both descriptor bases named by the source
package and therefore cannot upgrade an old P-only package during reproduction.

The upgraded verifier remains able to verify existing P-only packages. The P
registry schemas, paths, contract hash, and semantics remain unchanged. New
runtime authority may legitimately change P snapshot values and the resulting
package digest; Artifact Q promises contract compatibility, not identical bytes
across different authoritative inventories.

## 8. Dataset Registry

`Q-ANALYTICS@v1` contains exactly sixteen datasets.

| Dataset | Name | Semantic owner | Exact source | Grain |
|---|---|---|---|---|
| Q-D01 | `accounts` | Atlas | Q-V01 | one account catalogue entry |
| Q-D02 | `statement_lines` | Atlas | Q-V01 | one statement-line definition |
| Q-D03 | `account_statement_mappings` | Atlas | Q-V01 | one account-to-statement mapping |
| Q-D04 | `journal_headers` | Atlas | Q-V02 | one authored posted journal |
| Q-D05 | `journal_lines` | Atlas | Q-V01 plus Q-V02 | one immutable authored journal line enriched by one exact account mapping |
| Q-D06 | `journal_input_hashes` | Atlas/shared substrate | Q-V02 | one ordered proposal-origin input hash |
| Q-D07 | `business_events` | source business domain/shared substrate | Q-V03 | one admitted business event |
| Q-D08 | `referenced_journals` | Atlas read boundary | Q-V04 | one bound non-authored source/publication pair |
| Q-D09 | `referenced_journal_lines` | Atlas read boundary | Q-V01 plus Q-V04 | one referenced line tuple enriched by one exact account mapping |
| Q-D10 | `accounting_periods` | Atlas | Q-V05 | one exact period-state basis |
| Q-D11 | `posting_rules` | Atlas | Q-V06 | one exact posting-rule version |
| Q-D12 | `analytical_evidence_bindings` | source owner plus export steward | Q-V01-Q-V06 | one evidence ref attached to one Q row |
| Q-D13 | `analytical_query_executions` | shared substrate | Q-V00-Q-V06 | one exact Q query invocation |
| Q-D14 | `analytical_query_sources` | shared substrate | Q-V01-Q-V06 | one exact semantic source per invocation |
| Q-D15 | `ledger_semantics_catalogues` | Atlas | Q-V01 | one exact ledger-semantics catalogue version |
| Q-D16 | `analytical_context` | shared substrate/export steward | Q-V00 plus P package context | one exact analytical package context |

### 8.1 Q-D01 `accounts`

```text
row_key
catalog_ref
account_id
account_name
account_class
normal_balance
control_role
```

### 8.2 Q-D02 `statement_lines`

```text
row_key
catalog_ref
statement_field
statement_label
statement_class
display_order
```

### 8.3 Q-D03 `account_statement_mappings`

```text
row_key
catalog_ref
account_id
statement_field
mapping_role             # PRIMARY
```

### 8.4 Q-D04 `journal_headers`

```text
row_key
scenario_ref
journal_id
record_semantic_hash
entry_class
source_proposal_ref
source_proposal_semantic_hash
posted_by_event_id
ledger_period_id
effective_date
posted_at
currency
total_debit_minor
total_credit_minor
origin_type
source_lineage_mode
source_business_event_ref
source_posting_rule_ref
source_projection_ref
reverses_journal_id
corrects_journal_id
restatement_case_ref
directive_ref
restatement_policy_ref
correction_policy_ref
predecessor_proposal_ref
predecessor_proposal_semantic_hash
```

The origin fields form a strict union. Policy roles and source-journal roles are
not collapsed into generic columns: reversal uses `reverses_journal_id`,
replacement uses `corrects_journal_id`, restatement uses
`restatement_policy_ref`, and reversal/replacement use
`correction_policy_ref`. Only fields applicable to the exact proposal origin
are non-null. For a restatement adjustment, the query may follow the exact
predecessor proposal to expose its business event and posting rule, but
`source_lineage_mode = PREDECESSOR_ORIGIN` and the predecessor's exact semantic
hash make that indirection explicit. Reversal and replacement sources use
`DIRECT_ORIGIN`. Their `source_projection_ref` is the resolved family-qualified
`J-AR17:<record_identity>` key; the distinct `reverses_journal_id` or
`corrects_journal_id` field preserves the proposal's original business id.

### 8.5 Q-D05 `journal_lines`

```text
row_key
scenario_ref
journal_id
journal_line_id
line_no
account_id
statement_field
debit_minor
credit_minor
currency
legal_entity_id
customer_id
contract_id
record_semantic_hash
```

No signed or major-unit amount is a governed Q-D05 field.

### 8.6 Q-D06 `journal_input_hashes`

```text
row_key
scenario_ref
journal_id
input_ordinal
input_hash
verification_status
verification_proof_ref
```

`verification_status` is `CONTENT_BYTES_VERIFIED` only when an exact proof is
available, and then `verification_proof_ref` is required. Otherwise it is
`DECLARED_HASH_ONLY` and `verification_proof_ref` is null.

### 8.7 Q-D07 `business_events`

```text
row_key
scenario_ref
business_event_ref
event_type
correlation_id
occurred_at
recorded_at
effective_date
source_system
legal_entity_id
contract_ref
recognition_schedule_ref
service_period_start
service_period_end
amount_minor
currency
record_semantic_hash
```

The v1 union contains only `accounting.recognition.due`. A second business-event
type requires a contract revision; it cannot add nullable columns ad hoc.

### 8.8 Q-D08 `referenced_journals`

```text
row_key
scenario_ref
source_projection_ref
source_hash
j_ar17_semantic_hash
g13_publication_ref
g13_publication_semantic_hash
g13_payload_hash
g13_upstream_authoritative_ref
g13_source_record_semantic_hash
projection_type
projection_version
journal_id
ledger_period_id
currency
authored_by_f
publication_basis_type
publication_admission_identity
publication_referenced_source_ref
```

`authored_by_f` is copied from the exact G-13 publication and must be false in
v1. `source_hash` must equal `j_ar17_semantic_hash`, and
`g13_source_record_semantic_hash` must identify that same exact J-AR17 source.
`source_projection_ref` is the family-qualified analytical key
`J-AR17:<record_identity>` and is the value related to P-D13; `journal_id`
retains the source body's unqualified business identifier.
The row is rejected unless the G-13 `journal_id`, `ledger_period_id`, `currency`,
and ordered `line_tuples` exactly equal the corresponding J-AR17 source fields.
G-13-only projection metadata and J-AR17-only contract metadata are not compared
as if the complete payloads had the same schema.

### 8.9 Q-D09 `referenced_journal_lines`

```text
row_key
scenario_ref
source_projection_ref
journal_id
line_no
account_id
statement_field
debit_minor
credit_minor
currency
legal_entity_id
customer_id
contract_id
```

### 8.10 Q-D10 `accounting_periods`

```text
row_key
period_id
state_basis_type         # BASE_FACT | TRANSITION_PUBLICATION
state_authoritative_ref
state_record_semantic_hash
state_token
status
start_date
end_date
ledger_currency
opened_at
soft_closed_at
soft_close_event_id
hard_closed_at
hard_close_event_id
close_policy_ref
state_publication_ref
transition_event_ref
```

For `BASE_FACT`, `state_authoritative_ref` identifies exact J-AR07;
`state_token`, `state_publication_ref`, and `transition_event_ref` are null. For
`TRANSITION_PUBLICATION`, `state_authoritative_ref` identifies exact G-04
J-AR13; the state token, G-04 publication, and exact J-AR06 transition event are
required. Status-specific fields form the same strict union as the selected
exact period contract. J-P04 is never a source.

### 8.11 Q-D11 `posting_rules`

```text
row_key
posting_rule_ref
posting_rule_id
rule_version
trigger_event_type
effective_from
effective_to
status
content_ref
content_hash
content_schema_version
record_semantic_hash
```

### 8.12 Q-D12 `analytical_evidence_bindings`

```text
row_key
parent_dataset_id
parent_row_key
evidence_ordinal
evidence_role
evidence_ref
description
content_hash
verification_status
verification_proof_ref
```

The parent dataset union is closed to Q-D04, Q-D07, Q-D08, Q-D10, Q-D11, and
Q-D15.
Evidence shared by multiple exact parents remains one binding per parent.
`evidence_role` is closed to `CATALOGUE_EVIDENCE`, `JOURNAL_EVIDENCE`,
`PROPOSAL_EVIDENCE`, `POSTING_EVENT_EVIDENCE`, `BUSINESS_EVENT_EVIDENCE`,
`REFERENCED_PUBLICATION_EVIDENCE`, `PERIOD_EVIDENCE`, and
`POSTING_RULE_EVIDENCE`. Q-D04 therefore preserves the distinct evidence of the
immutable header, its source proposal, and its posting event without collapsing
those authority classes. `verification_proof_ref` is required exactly when
`verification_status = CONTENT_BYTES_VERIFIED` and is null for
`DECLARED_HASH_ONLY`.

### 8.13 Q-D13 `analytical_query_executions`

```text
row_key
query_instance_ref
query_id
view_contract
view_contract_version
scope_type
scope_ref
canonical_request_hash
query_revision
semantic_as_of
compatibility_mode
```

### 8.14 Q-D14 `analytical_query_sources`

```text
row_key
query_instance_ref
source_ordinal
source_family
source_ref
```

Q-Q00 has no Q-D14 rows because its descriptor hash is package configuration,
not semantic authority. Q-V01 through Q-V06 publish exact invocation-local
source closure. Exact J-AR12 evidence records and any exact record used to
justify `CONTENT_BYTES_VERIFIED` are part of that closure; they cannot be
borrowed from another invocation. `source_ref` is interpreted only with
`source_family`; identical identifier strings in different J-AR or G
publication families never collide.

### 8.15 Q-D15 `ledger_semantics_catalogues`

```text
row_key
catalog_id
catalog_version
catalog_ref
effective_from
effective_to
status
record_semantic_hash
```

Q-D15 preserves the exact governed configuration version that Q-D01 through
Q-D03 expand. Catalogue evidence attaches to Q-D15 through Q-D12; it is not
duplicated onto every account or mapping row.

### 8.16 Q-D16 `analytical_context`

```text
row_key
p_package_context_row_key
workspace_ref
p_discovery_descriptor_ref
p_discovery_descriptor_hash
q_discovery_descriptor_ref
q_discovery_descriptor_hash
evidence_registry_id
evidence_registry_version
analytical_registry_id
analytical_registry_version
query_revision
semantic_as_of
compatibility_mode
scenario_set_digest
ledger_semantics_catalog_ref
relationship_contract_version
```

Q-D16 preserves the second descriptor basis needed to verify and reproduce a
P-plus-Q package. Its runtime coordinates must equal the linked P-D01 package
context. `relationship_contract_version` is exactly `2` in v1.

### 8.17 Canonical row expectations

The v1 C-001/CT-1 package has this exact finite inventory:

| Dataset | Rows | Basis |
|---|---:|---|
| Q-D01 | 4 | four exercised accounts |
| Q-D02 | 4 | four exercised statement lines |
| Q-D03 | 4 | one primary mapping per account |
| Q-D04 | 3 | J-560, J-011, J-012 |
| Q-D05 | 6 | two lines per authored journal |
| Q-D06 | 3 | one ordered input hash per selected proposal |
| Q-D07 | 1 | C-001 recognition-due event |
| Q-D08 | 1 | bound J-010 J-AR17/G-13 pair |
| Q-D09 | 2 | two referenced J-010 line tuples |
| Q-D10 | 2 | June transition publication and July base fact |
| Q-D11 | 1 | C-001 posting rule |
| Q-D12 | 14 | exact evidence-binding inventory below |
| Q-D13 | 10 | one row per finite query invocation |
| Q-D14 | 38 | invocation-local exact source inventory below |
| Q-D15 | 1 | one ledger-semantics catalogue version |
| Q-D16 | 1 | one analytical package context |

Q-D12's fourteen rows are nine authored-journal bindings, one business-event
binding, one G-13 publication binding, one June-period binding, one posting-rule
binding, and one catalogue binding. July contributes no Q-D12 row because its
ratified J-AR07 base fact has an empty evidence list.

Q-D14's 38 rows decompose by invocation as:

```text
Q-Q01 ledger catalogue                    2
Q-Q02 C-001 authored journal              9
Q-Q02 CT-1 reversal journal               8
Q-Q02 CT-1 replacement journal            8
Q-Q03 business event                      2
Q-Q04 referenced journal pair             3
Q-Q05 June transition state               3
Q-Q05 July base fact                      1
Q-Q06 posting rule                        2
                                           --
total                                     38
```

The reversal invocation includes exact J-AR17 as the Q-D06 proof source. Its
proposal and posting event share one exact evidence authority, which appears
once in invocation-local source closure even though Q-D12 preserves both
semantic evidence roles. Q-Q04 reads J-AR17 independently as part of its own
strict G-13 pair; source closure is not deduplicated across invocations.

The counts are canonical acceptance data, not a claim of enterprise analytical
volume. A contract revision is required before the v1 registry may emit a
different inventory for these two reference scenarios.

## 9. Field-Origin and Transformation Law

Every schema column declares exactly one origin class:

```text
EXACT_VIEW_FIELD
EXACT_ENVELOPE_FIELD
LOSSLESS_CHILD_EXPANSION
LOSSLESS_VARIANT_FLATTEN
PARENT_CONTEXT_COPY
CATALOGUE_ENTRY
GOVERNED_CATALOGUE_LOOKUP
QUERY_METADATA
PACKAGE_STRUCTURAL_METADATA
```

Rules:

- `EXACT_VIEW_FIELD` and `EXACT_ENVELOPE_FIELD` name the Q-V path;
- `CATALOGUE_ENTRY` is permitted only for Q-V01 fields backed by the exact
  J-AR04 catalogue;
- `GOVERNED_CATALOGUE_LOOKUP` is permitted only for Q-D05 and Q-D09
  `statement_field`, using the unique Q-V01 account mapping;
- `GOVERNED_CATALOGUE_LOOKUP` is permitted only for Q-D05 and Q-D09
  `statement_field`, using the unique Q-V01 account mapping;
- `LOSSLESS_CHILD_EXPANSION` preserves source order and parent identity;
- `LOSSLESS_VARIANT_FLATTEN` fixes every nullable field in the registered
  schema and rejects a new variant;
- `PARENT_CONTEXT_COPY` may repeat scenario or journal identity only;
- query and package metadata cannot populate a domain-valued column; and
- no transformation may parse business meaning from an identifier string.

Q-D04 is the only intentionally wide union row. Q-D12 is the only polymorphic
parent dataset. Those exceptions are explicit and closed.

## 10. Relationship Registry

When both registries are present, `relationships.json` adds the following
registry-qualified relationships. Conditions shown below are part of the
relationship contract, not consumer inference.

Relationship contract v2 supports two closed shapes:

```text
standard relationship
  relationship_id
  relationship_type = STANDARD
  from_registry
  from_dataset
  from_columns[]
  to_registry
  to_dataset
  to_columns[]
  cardinality
  required
  enforcement
  condition?             # { column, equals }

polymorphic-parent relationship
  relationship_id
  relationship_type = POLYMORPHIC_PARENT
  from_registry
  from_dataset
  discriminator_column
  key_column
  allowed_targets[]      # each has registry, dataset, and key columns
  required
  enforcement
```

Contract v2 does not reinterpret Artifact P's v1 relationship file. A P-only
package remains on v1. A P-plus-Q package serializes the complete P and Q
relationship set under v2 and validates every entry against this closed grammar.
Every inherited P relationship object remains byte-for-byte identical to its
v1 registry definition; Q relationships use the same field names and equality-
condition shape. The P registry contract hash therefore remains unchanged.

```text
Q-RL01: Q-D03.account_id -> Q-D01.account_id
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL02: Q-D03.statement_field -> Q-D02.statement_field
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL03: Q-D05.journal_id -> Q-D04.journal_id
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL04: Q-D05.account_id -> Q-D01.account_id
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL05: Q-D05.statement_field -> Q-D02.statement_field
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL06: Q-D06.journal_id -> Q-D04.journal_id
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL07: Q-D09.source_projection_ref -> Q-D08.source_projection_ref
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL08: Q-D09.account_id -> Q-D01.account_id
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL09: Q-D09.statement_field -> Q-D02.statement_field
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL10: Q-D04.ledger_period_id -> Q-D10.period_id
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL11: Q-D08.ledger_period_id -> Q-D10.period_id
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL12: Q-D12.(parent_dataset_id, parent_row_key)
  -> closed registered Q parent row
  [many-to-one, required, INTEGRITY_ONLY]

Q-RL13: Q-D14.query_instance_ref -> Q-D13.query_instance_ref
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL14: P-D06.statement_field -> Q-D02.statement_field
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL15: P-D07.statement_field -> Q-D02.statement_field
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL16: P-D13.source_projection_ref -> Q-D08.source_projection_ref
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL17: P-D14.journal_ref -> Q-D04.journal_id
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL18: Q-D04.source_business_event_ref -> Q-D07.business_event_ref
  [many-to-one, required when source_lineage_mode = PREDECESSOR_ORIGIN,
   INTEGRITY_ONLY, condition = {column: source_lineage_mode,
   equals: PREDECESSOR_ORIGIN}]

Q-RL19: Q-D04.source_posting_rule_ref -> Q-D11.posting_rule_ref
  [many-to-one, required when source_lineage_mode = PREDECESSOR_ORIGIN,
   INTEGRITY_ONLY, condition = {column: source_lineage_mode,
   equals: PREDECESSOR_ORIGIN}]

Q-RL20: Q-D04.source_projection_ref -> Q-D08.source_projection_ref
  [many-to-one, required when source_lineage_mode = DIRECT_ORIGIN,
   INTEGRITY_ONLY, condition = {column: source_lineage_mode,
   equals: DIRECT_ORIGIN}]

Q-RL21: Q-D01.catalog_ref -> Q-D15.catalog_ref
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL22: Q-D02.catalog_ref -> Q-D15.catalog_ref
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL23: Q-D03.catalog_ref -> Q-D15.catalog_ref
  [many-to-one, required, CONSUMER_RELATIONSHIP]

Q-RL24: each of Q-D04 through Q-D09 scenario_ref -> P-D02.scenario_ref
  [many-to-one, required, CONSUMER_RELATIONSHIP; serialized as six registry-
   qualified standard entries]

Q-RL25: Q-D13.scope_ref -> P-D02.scenario_ref
  [many-to-one, required when scope_type = SCENARIO, INTEGRITY_ONLY,
   condition = {column: scope_type, equals: SCENARIO}]

Q-RL26: Q-D04.(scenario_ref, restatement_case_ref)
  -> P-D05.(scenario_ref, restatement_case_ref)
  [many-to-one, required when origin_type = RESTATEMENT_ADJUSTMENT,
   INTEGRITY_ONLY, condition = {column: origin_type,
   equals: RESTATEMENT_ADJUSTMENT}]

Q-RL27: Q-D16.p_package_context_row_key -> P-D01.row_key
  [many-to-one, required, INTEGRITY_ONLY]

Q-RL28: Q-D16.ledger_semantics_catalog_ref -> Q-D15.catalog_ref
  [many-to-one, required, INTEGRITY_ONLY]
```

Q-RL18 through Q-RL20 require the applicable source to resolve exactly once and
the inapplicable source columns to remain null. They are not imported as Power
BI model relationships because they represent a strict origin union rather than
a uniform star-schema dimension.

Q-RL24 is one logical family and six serialized relationship entries. The
serialized ids are `Q-RL24-Q-D04` through `Q-RL24-Q-D09` in source-dataset
order. The package verifier validates the expanded entries separately and
reports their fully qualified source dataset. Relationships and datasets are
always indexed by `(registry_id, dataset_id)`; a duplicate dataset id in another
registry is not a collision.

P-only packages retain Artifact P's original relationship set. The extra
cross-registry relationships are required whenever Q is declared.

## 11. Package Integration

The canonical package extends only by registered directories:

```text
schemas/q-analytics-v1/Q-D01.schema.json ... Q-D16.schema.json
data/q-analytics-v1/Q-D01.csv ... Q-D16.csv
```

The same `manifest.json`, `relationships.json`, `checksums.json`, and
`package.digest` bind both registries. `dataset_registries[]` contains exactly:

```text
P-EVIDENCE@v1
Q-ANALYTICS@v1
```

for an analytical package. Registry order is lexical by registry id. Dataset
identity remains `(registry_id, dataset_id)`.

The top-level package contract remains `governed-export-package@v1` because
Artifact P deliberately defined `dataset_registries[]` as its extension point
and required a future analytical registry to be named there. Artifact Q closes
that extension point to exactly two supported manifest variants:

| Registry set | Dataset-entry registry variants | Relationship version |
|---|---|---:|
| `P-EVIDENCE@v1` | `P-EVIDENCE` only | 1 |
| `P-EVIDENCE@v1`, `Q-ANALYTICS@v1` | `P-EVIDENCE` or `Q-ANALYTICS` | 2 |

`DatasetRegistryEntry` and `DatasetManifestEntry` therefore become closed
discriminated unions keyed by `registry_id`; they do not become arbitrary ASCII
registries. The Q variants fix Q's registry version, storage key, dataset ids,
and registry contract hash exactly. Any other registry set, duplicate registry,
registry/version pairing, or relationship-version pairing is
`UNSUPPORTED_CONTRACT`.

An Artifact-P-era verifier is not required to understand a new Q package. The
upgraded verifier is required to preserve verification and reproduction of old
P-only packages and to validate both closed variants. This is compatible
extension of the package envelope, not mutation of `P-EVIDENCE@v1`.

Q-C01 must:

1. validate both discovery descriptors before opening a staging directory;
2. open one query session;
3. execute P-Q00 and the Artifact O public views needed by P;
4. resolve Q-Q00 and prove exact subject-set equality against those already-
   executed P/O views;
5. bind both descriptors to the same revision and semantic time;
6. execute each remaining query through a fresh invocation-local reader;
7. tabularise P and Q without one registry reading the other's generated CSV;
8. validate all schemas, composite registry/dataset keys, relationships, and
   snapshot coordinates;
9. write one closed checksum ledger and digest; and
10. promote the staging directory atomically only after complete verification.

The Q implementation may extend the Artifact P package service and verifier. It
must not fork a second package format or alter the P-C01 request contract,
P-EVIDENCE schemas, or P-only registry semantics. Existing P-only packages must
still verify and reproduce after the extension.

## 12. C-001 Proof

A valid C-001 analytical package proves all of the following:

1. the ledger-semantics catalogue contains the exact deferred-revenue and
   subscription-revenue accounts and statement mappings;
2. Q-D04 contains J-560 as `RESTATEMENT_ADJUSTMENT` only;
3. Q-D05 contains its two ordered exact journal lines for GBP 10,000;
4. J-560's ledger period is July while P-D07's presented reporting period is
   June;
5. Q-D10 contains June `HARD_CLOSED` from exact G-04/J-AR13 plus J-AR06 and
   July `OPEN` from exact J-AR07 as separate source-basis variants;
6. Q-D04 resolves J-560 through P-551@v2 and then through the exact predecessor
   proposal to the admitted recognition event and posting rule;
7. Q-D07 preserves occurred, recorded, and effective time separately;
8. Q-D11 preserves the exact posting-rule version and content hash;
9. P-D05 retains June v1 and v2 separately;
10. P-D07 remains the authority for the GBP 10,000 restatement bridge;
11. P-D10 retains purpose-specific readiness and limitations; and
12. the combined model can drill from P reporting facts to statement-line
    semantics, account mapping, journal header, journal lines, event, rule, and
    evidence without direct persistence access.

The package must not claim that J-560 was posted into June. It was posted in an
eligible open correction period and represented in the June v2 publication.

## 13. CT-1 Proof

A valid CT-1 analytical package proves all of the following:

1. Q-D08 contains J-010 only as a non-authored referenced projection;
2. Q-D08 binds exact J-AR17 to exact G-13 by authoritative reference, semantic
   hash, canonical payload equality, and declared source hash before any line
   comparison;
3. Q-D09 contains its exact two line tuples and wrong-customer identity;
4. Q-D04 contains separate authored reversal J-011 and replacement J-012 rows;
5. Q-D05 contains two exact lines for each authored journal;
6. Q-D04 resolves the exact reversal/replacement proposals, policies,
   directive, and referenced source projection;
7. Q-D06 retains each source hash in original order and with honest verification
   status;
8. Q-D10 contains July `OPEN` from the exact J-AR07 base fact rather than a
   rebuildable J-P04 projection;
9. P-D13 remains the authority for `BOUND_BEFORE_COMPARE`, identity correction,
   and GBP 0 control-account net movement;
10. P-D14 resolves to Q-D04 through the declared cross-registry relationship;
11. no CT-1 reporting-version, readiness, or Pythia row is invented; and
12. the consumer can compare referenced, reversal, and replacement lines while
    preserving their three different authority classes.

## 14. Consumer Boundary

Artifact Q authorises later consumer artifacts to:

- import verified P and Q CSVs only after offline package verification;
- create only registered `CONSUMER_RELATIONSHIP` joins;
- format integer minor units as major currency values while retaining source
  columns;
- add clearly labelled workbook or DAX calculations;
- filter and group by exact dimensions;
- create navigation and presentation metadata locally; and
- show links back to source row keys, evidence bindings, and query provenance.

It does not authorise a consumer to:

- read SQLite, runtime repositories, or public HTTP routes as a hidden second
  source;
- replace P-D07 restatement adjustments with recalculated differences;
- derive readiness from journal balance or evidence presence;
- restate P-D13 correction conclusions;
- change account class, normal balance, or statement mapping;
- merge J-010 with J-011/J-012 into one journal class;
- silently convert a `DECLARED_HASH_ONLY` value to verified;
- write back into the platform; or
- claim enterprise coverage from canonical-depth data.

The later Excel and Power BI artifacts must each publish a field disposition
table separating:

```text
GOVERNED_SOURCE
CONSUMER_CALCULATION
PRESENTATION_METADATA
```

## 15. Failure Semantics

The analytical registry build rejects with a stable error class when:

```text
ANALYTICAL_DESCRIPTOR_INVALID
REGISTRY_DEPENDENCY_MISSING
SNAPSHOT_MISMATCH
UNSUPPORTED_COMPATIBILITY_MODE
LEDGER_CATALOGUE_MISSING
LEDGER_CATALOGUE_INVALID
ACCOUNT_MAPPING_MISSING
EXACT_JOURNAL_MISSING
JOURNAL_LINE_CLOSURE_BROKEN
PROPOSAL_ORIGIN_UNRESOLVED
BUSINESS_EVENT_UNRESOLVED
REFERENCED_JOURNAL_UNRESOLVED
PERIOD_STATE_UNRESOLVED
POSTING_RULE_UNRESOLVED
EVIDENCE_STATUS_INVALID
RELATIONSHIP_VIOLATION
UNREGISTERED_DATASET
ATOMIC_PROMOTION_FAILED
```

Failure produces no final package and leaves no staging residue. Existing
verified packages are never overwritten.

## 16. Implementation Sequence

### Phase Q1 - Typed configuration and queries

- define and baseline-admit the exact ledger-semantics catalogue;
- implement Q-Q00 through Q-Q06 as strict application reads;
- prove exact-original semantics, invocation-local sources, and parameterised
  identities; and
- add negative tests for wrong discriminators, missing lines, ambiguous period
  tokens, and broken origin resolution.

### Phase Q2 - Registry and package integration

- implement Q-D01 through Q-D16 schemas and tabularisation;
- implement Q-C01 as the fixed P-plus-Q build request while preserving P-C01;
- add `Q-ANALYTICS@v1` to the existing registry machinery;
- extend the relationship registry with Q-RL01 through Q-RL28 under relationship
  contract v2 while preserving P-only contract v1;
- build P and Q from one session and one staging transaction; and
- extend offline verification and reproduction across both registries.

### Phase Q3 - Canonical proofs and cohesion audit

- prove C-001 and CT-1 row, lineage, authority-class, and relationship parity;
- rerun H0-H7, Milestone 2, Artifact O, and Artifact P substantive gates;
- audit dependency direction, account semantics, readiness reuse, and package
  atomicity; and
- ratify implementation only after the multi-registry package reproduces from a
  clean checkout.

Only then may the first Excel consumer artifact begin. Power BI follows from
the same verified package and relationship registry, not a separate extract.

## 17. Acceptance Criteria

- Q-A01: an analytical package declares both `P-EVIDENCE@v1` and
  `Q-ANALYTICS@v1`.
- Q-A02: P and Q share one exact query revision, semantic time, workspace,
  scenario set, and compatibility mode.
- Q-A03: Q-C01 is the only v1 analytical build request, requires exactly P and
  Q, cannot verify without that dependency, and leaves P-C01's request,
  registry, schema, relationship-v1, verification, and reproduction contracts
  unchanged.
- Q-A04: every Q domain read is `EXACT_ORIGINAL`.
- Q-A05: reusable Q code contains no canonical C-001, CT-1, journal, period,
  customer, contract, or account branching.
- Q-A06: the exporter depends on typed Q views and has no direct persistence,
  SQL, SQLite, state, fixture, HTTP, or web dependency.
- Q-A07: Q-D15 preserves the ledger-semantics catalogue as an exact Atlas-owned
  J-AR04 baseline record with a strict contract and evidence.
- Q-A08: all Q-D01 accounts and Q-D02 statement lines are unique; every Q-D03
  mapping resolves exactly once at both ends; and the account class, normal
  balance, statement class, and control role satisfy the closed v1 matrix.
- Q-A09: no account semantic field is parsed from `account_id`.
- Q-A10: Q-D04 contains exactly the three authored journals declared by Q-Q00.
- Q-A11: every Q-D04 header resolves all ordered Q-D05 lines and reconciles to
  its exact debit and credit totals.
- Q-A12: every Q-D04 origin union matches the exact J-AR05 proposal variant and
  contains no cross-variant leakage.
- Q-A13: Q-D06 preserves exact input-hash order and honest verification status,
  with a proof ref required only for verified content bytes.
- Q-A14: Q-D07 contains admitted business events only and preserves all three
  time concepts.
- Q-A15: Q-D08 binds exact J-AR17 and exact G-13 by authoritative reference,
  semantic hash, declared source hash, G-13 payload hash, and exact equality of
  their shared source fields before Q-D09 is emitted; it does not claim the two
  complete payloads are byte-identical, and the referenced class never enters
  Q-D04/Q-D05.
- Q-A16: Q-D10 contains June hard-closed from the exact G-04/J-AR13 plus J-AR06
  transition basis and July open from exact J-AR07 base facts; it never sources
  J-P04.
- Q-A17: Q-D11 resolves the exact C-001 posting-rule identity and content hash.
- Q-A18: Q-D12 retains every required evidence reference, including G-13
  publication evidence, and never promotes a declared hash without verified
  bytes and an exact verification proof ref.
- Q-A19: Q-D13 contains exactly ten v1 query invocations in the registered
  order.
- Q-A20: Q-D14 contains only invocation-local, family-qualified exact sources
  and none for Q-Q00.
- Q-A21: Q-D01 through Q-D12 and Q-D15 contain no file, worksheet, Power BI,
  route, colour, or display-format metadata.
- Q-A22: all governed money values are integer minor units with currency and no
  float appears in a canonical file.
- Q-A23: P reporting, readiness, exception, governance, decision, correction,
  and trace values are related but not duplicated into Q.
- Q-A24: Q-RL01 through Q-RL28 validate under relationship contract v2 with
  exact registry-qualified keys, declared cardinality, and closed conditions.
- Q-A25: P-D06 and P-D07 resolve their statement fields to Q-D02.
- Q-A26: P-D13 resolves its source projection to Q-D08 and P-D14 resolves both
  authored journals to Q-D04.
- Q-A27: each Q-D04 origin variant resolves its conditionally required source
  event, posting rule, or source projection exactly once and leaves
  inapplicable source columns null.
- Q-A28: C-001 preserves June hard-close, July posting, June v1/v2 history, and
  the exact GBP 10,000 P-D07 bridge.
- Q-A29: CT-1 preserves separate referenced, reversal, and replacement classes,
  exact customer identities, bind-before-compare status, and the P-D13 GBP 0
  conclusion.
- Q-A30: CT-1 creates no reporting, readiness, or decision row.
- Q-A31: a broken account mapping, journal-line closure, period state, origin
  binding, or cross-registry relation rejects the entire build.
- Q-A32: a failed build leaves no final package or staging residue and does not
  overwrite an existing verified package.
- Q-A33: P-C02 detects missing, extra, tampered, resealed-invalid, and
  snapshot-divergent Q files.
- Q-A34: P-C03 reproduces byte-identical P and Q registry bytes and one package
  digest from the exact source revision.
- Q-A35: H0-H7 and the substantive Milestone 2, O, and P gates remain green.
- Q-A36: repository documentation discloses canonical depth and does not claim
  enterprise analytical coverage.
- Q-A37: Q-D16 preserves both discovery descriptor identities and hashes, the
  exact P package-context link, and all shared snapshot coordinates.
- Q-A38: Q-Q00 accepts only when its journal, event, rule, source projection,
  period, and scenario subject sets equal the already-executed P/O view sets;
  only the catalogue reference may be descriptor-supplied new authority.
- Q-A39: every verified input hash or evidence hash names the exact,
  family-qualified proof used and that proof resolves through invocation-local
  Q-D14 source closure or an exact registered P/Q row; declared-only hashes name
  no proof.
- Q-A40: all Q-D04 through Q-D09 scenario refs resolve to P-D02, and every
  scenario-scoped Q-D13 row resolves to P-D02.
- Q-A41: a restatement-adjustment Q-D04 row resolves to the exact P-D05
  restatement case without turning that integrity link into a consumer fact.
- Q-A42: P-only packages continue to validate with relationship contract v1;
  P-plus-Q packages require the complete v2 grammar and relationship set.
- Q-A43: dataset identity and relationship validation use the composite key
  `(registry_id, dataset_id)` throughout.
- Q-A44: the canonical C-001/CT-1 build matches every Q-D01 through Q-D16 row
  count and the Q-D12/Q-D14 decompositions fixed in section 8.17.
- Q-A45: an upgraded clean-checkout verifier accepts a prior valid P-only
  package, accepts a valid P-plus-Q package, rejects a Q-without-P package, and
  reproduces each package without changing its declared registry set.

## 18. Structural Inventory and Ratification Gate

Artifact Q v0.2 contains exactly:

- 30 rulings: Q-R01 through Q-R30;
- 4 bounded use cases: Q-U01 through Q-U04;
- 7 query/view types: Q-Q00/Q-V00 through Q-Q06/Q-V06;
- 10 query invocations in the canonical v1 plan;
- 1 analytical build operation: Q-C01;
- 16 datasets: Q-D01 through Q-D16;
- 28 logical relationships: Q-RL01 through Q-RL28, with Q-RL24 expanding to six
  serialized entries; and
- 45 acceptance criteria: Q-A01 through Q-A45.

Before ratification, critique must specifically test:

1. whether the ledger-semantics catalogue is the minimum honest new authority
   or an avoidable expansion;
2. whether Q-D04's resolved origin union preserves exact lineage without
   silently becoming a new trace engine;
3. whether every cross-registry relationship is cardinality-safe for future
   account and statement growth;
4. whether P and Q can be assembled atomically through the implemented Artifact
   P package format without weakening P-C01 or P-only verification;
5. whether canonical-depth rows are sufficient to prove the first Excel and
   Power BI models without adding decorative synthetic volume; and
6. whether any domain value has leaked into export-owned metadata or any
   consumer calculation has been mistaken for platform authority.

Artifact Q v0.2 is ratified by ADR-037. It authorises only the bounded
implementation and cohesion audit defined here. No Excel workbook, Power BI
model, or wider synthetic population is authorised by this artifact.
