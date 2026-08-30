# Milestone 2 Phase 5: Executed Module Contracts

Status: Complete 2026-08-05

## 1. Outcome

The runtime now executes the finite Artifact L module-product registry and
G-01 through G-14 publication envelope through the same Artifact K persistence
boundary used by accounting commands. Module names remain semantic owners and
product lenses; they do not own databases, repositories, dispatchers, or
transaction managers.

Phase 5 adds no transport, broker, workflow framework, API, UI, authentication,
tenant model, or second store. The in-process contracts are immutable semantic
values inside the modular monolith.

## 2. Closed Contract Boundary

`ContractPublication` implements the exact J-AR13 envelope with separate G and
body versions, canonical payload hash, publisher, product identity, exactness
token where required, lineage, evidence, availability, and publication basis.
The registry admits only the ratified publisher, consumer, discriminator, and
version combinations.

`ValidatedModuleProduct` implements the finite command-output portion of the
twenty-entry J-AR02 registry. Unknown discriminators, owners, fields, floats,
hashes, or baseline-only products fail before persistence. The durable codec
registers these types explicitly; persisted data cannot name an arbitrary
runtime class.

The implementation corrected one exactness issue found during the Phase 5
audit: G-13 uses its fully qualified version reference plus the bound J-AR17
source hash. It does not carry a lifecycle `product_state_token`. Only G-04
lifecycle views require that token, exactly as Artifact L section 5 specifies.

## 3. One Transaction Path

Non-accounting module commands produce one `ModuleCommandOutcome` and use the
existing command-result, arbitration, validation, commit, retry, and rollback
path. The outcome retains every module product, authoritative admitted event,
J-AR13 publication, and consumed publication reference created or used by that
command.

Atlas accounting publications are not emitted after the accounting command.
G-04, G-05, and G-06 values ride inside the owning planner transition's
immutable creation closure. The J-AR06 event, relevant accounting/reporting
records, J-AR13 publications, J-AR14 result, and any J-AR15 effect therefore
commit or roll back together.

G-14 uses the rejection arm of that same unit of work. Its J-AR13 publication,
J-AR14 rejected result, and J-AR16 disposition are one atomic rejection-only
set. G-14 cannot claim an accepted command or become an Artifact F event.

## 4. Publish and Consume Rules

The boundary enforces:

- exact publisher ownership and command publication basis;
- registry-permitted consumers, including the approved-decision source
  boundary;
- semantic availability before consumption;
- unique consumed and upstream publication identities;
- publisher output closure and immutable product identity;
- exact J-AR12 evidence-reference form without upgrading declaration-only
  evidence to verified content;
- G-02 admission/eligibility agreement;
- G-03 quantified or identity reconciliation agreement;
- G-10 reporting-version binding and purpose-specific status;
- G-11 matching G-06 plus approved G-10 reliance; and
- G-12 binding to its frozen G-11 input.

Pythia cannot infer readiness from a reporting version. A blocked or mismatched
G-10 cannot become a planning input merely because G-06 exists.

## 5. Observations Are Not Authority

J-P13 boundary observations are generated only after a successful ordinary or
administrative commit. They record actual publish and consume handoffs and are
de-duplicated by deterministic observation identity.

The observation sink is removable. Sink failure is swallowed after commit and
cannot change command outcome, authoritative state, retry identity, or rebuild.
No observation can replace J-AR13, a consumer command outcome, or the
approved-decision return.

## 6. G-13 and Event-Stream Firewall

Referenced-journal admission now validates a complete typed G-13 envelope,
referenced-journal publication basis, J-AR17 identity, and exact source hash.
The admitted projection keeps `authored_by_f = false`, never enters J-AR08, and
is observed only after its administrative transaction succeeds.

CT-1 consumes G-13 through Argus and the already-proven correction constructor.
It does not transform the prior journal into a business event. Accounting
events and G publications remain structurally unable to re-enter the G-01
posting-rule input.

## 7. Executable Proofs

The Phase 5 tests prove:

- Hermes G-02 and SharedSubstrate G-01 commit through ordinary owner commands;
- the admitted business event is J-AR03 and its G-01 publication is J-AR13;
- Atlas G-04, G-05, and G-06 publish atomically with their owning C-001
  accounting commands and survive restart;
- the C-001 governance/planning path executes G-03, G-07, G-08, G-09, G-10,
  G-11, and G-12 with real persisted publish/consume handoffs;
- CT-1 executes identity reconciliation, exception governance, correction
  verification, and issue update through G-03, G-07, and G-08 while consuming
  non-authored G-13;
- G-14 commits only with its rejected result and disposition;
- illegal consumers, premature availability, missing evidence form, duplicate
  identities, inconsistent reconciliation/readiness, and broken lineage fail
  without mutation;
- observation failure cannot roll back authority;
- module command retry and publications survive SQLite restart; and
- the unchanged H0 through H7 suite remains green.

Ruff passes. All 107 tests pass.

## 8. Scope Guard and Phase 6 Entry

Phase 5 deliberately does not add public read models. Phase 6 may now build
exact-version and labelled-current queries over the authoritative records
already committed here. It must derive traceability from J-AR02/J-AR03,
J-AR05/J-AR06, J-AR08/J-AR10, J-AR12/J-AR13/J-AR14/J-AR15/J-AR17 and their
existing projections. It may not introduce dashboard-oriented denormalization,
infer readiness, or treat J-P13 observations as lineage authority.
