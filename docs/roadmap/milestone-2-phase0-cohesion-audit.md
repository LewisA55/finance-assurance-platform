# Milestone 2 Phase 0 Cohesion Audit

Status: Passed 2026-08-05 - Milestone 2 Phase 0 complete

## 1. Purpose

This is the mandatory hard audit after Artifact N ratification and before
Milestone 2 Phase 1 kernel extraction. It determines whether the Phase 0 design
is closed enough to permit reversible runtime-package and persistence-port
implementation work.

The audit reconciles:

- the five platform invariants and `AGENTS.md`;
- Artifacts C through H as the inherited accounting and executable baseline;
- Artifacts I v0.2.2, J v0.2, K v0.2.2, L v0.2, M v0.2.1, and N v0.2.1;
- ADR-018 through ADR-024;
- canonical transactions C-001 and CT-1;
- the Milestone 2 roadmap and M2-A01 through M2-A19;
- the existing H0 through H7 implementation and all current tests; and
- README and roadmap claims about current scope and completion state.

The ratified baseline under review is commit `70dad8b`, which closes Artifact N
v0.2 and ADR-024.

## 2. Audit Rule

The audit may correct stale wording, missing trace links, or an implementation-
independent contradiction in the Phase 0 documents. It may not silently add a
business process, event type, record family, G contract, persistence mode,
workflow framework, database, public API, or deployment topology.

Any material semantic correction must amend the owning artifact and enter the
append-only decision log. Reversible package-layout or library recommendations
remain implementation choices rather than architecture decisions.

## 3. Method

The review proceeds in dependency order and records evidence before verdict:

1. mechanically verify artifact status, numbered-contract continuity, ASCII and
   whitespace hygiene, ADR coverage, and repository references;
2. trace the five invariants and the business/accounting event firewall through
   every command, record, message, authority, persistence, and compatibility
   boundary;
3. reconcile each owner, publisher, consumer, and writer across I, J, K, and L;
4. reconcile command inputs and outputs against J-AR/J-P ownership, K unit-of-
   work closure, M authority slots, and N contract coordinates;
5. replay C-001 and CT-1 on paper through ordinary I-N paths, including every
   retry, effect, readiness, evidence, compatibility, and rebuild obligation;
6. challenge failure semantics, especially pre-construction rejection,
   unsupported input, corruption, stale state, identity conflict, rollback,
   restart, and rebuild failure;
7. compare Phase 0 coverage with M2-A01 through M2-A19 and the roadmap's stated
   design outputs; and
8. search for stale current claims and accidental physical or distributed-
   systems assumptions.

## 4. Ratified Inventory Baseline

| Artifact | Status | Closed numbered inventory |
|---|---|---|
| I | v0.2.2 ratified 2026-08-05 | 11 rulings, 23 commands, 20 queries, 26 execution steps, 24 acceptance criteria |
| J | v0.2 ratified 2026-08-03 | 19 rulings, 17 authoritative families, 13 projections, 30 acceptance criteria |
| K | v0.2.2 ratified 2026-08-05 | 22 rulings, 6 persistence modes, 42 core tests, 6 durable tests, 41 acceptance criteria |
| L | v0.2 ratified 2026-08-04 | 20 rulings, 20 module-product discriminators, 30 acceptance criteria |
| M | v0.2.1 ratified 2026-08-05 | 25 rulings, 45 conformance tests, 41 acceptance criteria |
| N | v0.2.1 ratified 2026-08-05 | 28 rulings, 54 conformance tests, 45 acceptance criteria |

ADR coverage is continuous from ADR-018 through ADR-025. The Phase 0 artifact
status lines and ratification dates agree with those decisions.

## 5. Audit Tracks

| Track | Question | Status |
|---|---|---|
| A. Vocabulary and versioning | Do all artifacts use the same object, message, owner, version, canonicalization, and availability meanings? | Passed |
| B. Event firewall | Can only an admitted business event drive posting-rule evaluation, with accounting events permanently excluded? | Passed |
| C. Ownership and handoffs | Does every product and G contract have exactly one writer and every required consumer? | Passed |
| D. Authoritative closure | Do J-AR/J-P ownership, K atomic closure, retries, effects, and rebuilds agree? | Passed |
| E. Authority and compatibility | Do M grants and N contract bindings enter command identity once, before planning, without circularity? | Passed |
| F. Canonical proofs | Do parameterised C-001 and CT-1 traverse ordinary I-N paths with no fixture-literal branch? | Passed |
| G. Evidence and readiness | Are evidence status, reproducibility, and purpose-specific reliance preserved end to end? | Passed |
| H. Scope and roadmap | Are all Phase 0 outputs present without selecting physical or distributed infrastructure? | Passed |

## 6. Mechanical Baseline Results

The opening mechanical pass confirms:

- all six Phase 0 artifacts are ratified and indexed;
- numbered inventories are continuous and unique within each artifact;
- Artifact N remains 28 rulings, 54 tests, and 45 acceptance criteria after
  ratification;
- the existing validation harness passes H0 through H7;
- the current test suite passes 67 tests and Ruff reports no violations; and
- ratification introduced no implementation, fixture, database, public API, UI,
  authentication, broker, or deployment change.

### 6.1 Initial vocabulary reconciliation

The first Track A pass confirms:

- Artifact J owns thirteen projections, but J-P13 is an append-only boundary
  observation trace outside semantic transaction, rebuild, promotion, and
  projection-digest treatment. K and N therefore correctly rebuild and version
  J-P01 through J-P12 while still recognizing J-P13 as the thirteenth typed
  projection facet.
- Artifact L fixes `g_contract_version = G-v0.2` and body contract version 1;
  Artifact N preserves those as separate typed coordinates and does not parse
  the `G-v0.2` label to infer body version.
- Artifact F payload version, Artifact L body version, Artifact M authority
  version, Artifact N policy version, and canonicalization version remain
  distinct axes. No artifact treats them as one global version or selects an
  implicit latest value.
- J-AR17 referenced state and G-13 publication remain explicitly non-authoring;
  neither compatibility adaptation nor persistence custody can turn J-010 into
  an Atlas-authored J-AR08 journal.

Track A passes after the Artifact I v0.2.2 lifecycle terminology correction.

Two coverage questions are deliberately open for the semantic pass:

1. whether the roadmap's Phase 0 `runtime evidence port` is fully and
   unambiguously realized across J-AR12, K facets, L evidence-bearing messages,
   and N compatibility treatment, or still needs one explicit boundary map; and
2. whether N's conformance catalog plus the roadmap's M2-A01 through M2-A19 is a
   sufficiently closed Milestone 2 executable acceptance catalog, or whether a
   separate implementation-facing catalog remains required before Phase 1.

These are audit questions, not findings. Neither authorizes a new record family
or framework.

## 7. Findings

### M2-P0-F01 - Hermes consumes G-04 outside the closed consumer registry

Classification: blocking contradiction.

Status: resolved in Artifact I v0.2.2.

Artifact I section 9 makes I-C07 `ReconcileRecognitionPopulation` consume G-02,
G-04, and G-05. Its detailed I-S07 step consumes the submitted/deferred proposal
and accounting-event stream to quantify expected, posted, submitted-unposted,
and deferred populations. Artifact G and Artifact L section 5 permit Hermes to
consume G-05 for lineage but omit Hermes from G-04 consumers.

The runtime therefore cannot both implement I-C07 as specified and enforce L's
closed consumer registry. Expanding G-04 consumption would change the ratified
ownership contract and ripple through N's exact G coordinate. The smaller repair
is to remove G-04 from I-C07 and state that the bounded C-001 reconciliation
uses the exact source recognition schedule, Hermes admission/lineage state, and
Atlas G-05 lifecycle events. Argus remains the G-04 consumer that freezes and
tests the full accounting-object population at I-S08.

### M2-P0-F02 - Artifact I reifies lifecycle projections as authoritative versions

Classification: required cohesion correction.

Status: resolved in Artifact K v0.2.2.

Status: resolved in Artifact I v0.2.2.

Artifact I's current command and C-001 sequence still describes an immutable
hard-closed period version, initial and successor restatement-case versions,
approved lifecycle representations, and a terminal posted proposal treatment.
Artifacts J and K subsequently resolve those concepts differently:

- proposal treatment is immutable J-AR05 created at construction;
- proposal, period, and restatement-case lifecycle state is rebuilt from J-AR06
  events and exposed through J-P02 through J-P07 exact/current views; and
- G-04 publishes the exact Artifact F view at an authoritative state token.

I-S18 and I-S19 also omit their G-04/G-05 publications from the detailed atomic
write lists even though I's command map and J/K/L require them. Artifact I should
be amended to call these values exact state views or projections, preserve the
unchanged treatment, and list the required publications. Its historical section
12 design question may remain as historical context if an explicit note points
to Artifact J's resolution.

### M2-P0-F03 - Artifact M states that J-560 identities precede planning

Classification: blocking self-contradiction.

Status: resolved in Artifact M v0.2.1.

Artifact M section 11.2 says J-560 and its line identities are granted before
planning. M-R11, M-R19, and section 8.1 require the opposite ordering: invoke the
single planner or typed owner operation, derive the closed output shape, then
request identity and sequence grants before materialization and staging. ADR-023
ratified that planner-first resolution explicitly.

The section 11.2 sentence must state that the identities are granted after the
typed posting outcome fixes the journal-line shape and before materialization;
they become authoritative only if `journal.posted` commits. No contract or test
count needs to change.

### M2-P0-F04 - K's CT-1 Argus row omits the required G-03 input

Classification: required cohesion correction.

Artifact I states that `RunCashApplicationIdentityTest` cannot begin without the
exact Hermes G-03 publication. Artifact L's L-MP08 body requires an exact L-MP05
`reconciliation_ref`. Artifact K section 15.1 lists only G-13, test definition,
and configuration reads for that command.

The K row must add the exact Hermes G-03/L-MP05 reconciliation input. This is a
traceability repair to the existing transaction path, not a new command or
handoff.

### 7.1 Event-firewall result

Track B passes. I-C03 accepts only exact G-01 business-event input; all correction
construction uses the separate typed correction planner; L fixes G-01 as the
only posting-engine boundary; K and M cannot invent a planner route from a
persistence or authority type; and N prohibits compatibility across business-
event and accounting-event classes. C-001 invokes posting-rule evaluation once,
while CT-1 invokes it zero times.

### 7.2 Evidence-boundary result so far

The roadmap's runtime-evidence-port requirement is provisionally satisfied as a
composed semantic boundary rather than a new record family:

- I-Q14 names the exact content-resolution query;
- J-AR12 distinguishes verified bytes from declaration-only evidence;
- K's content/evidence facet defines exact resolution and permitted staging;
- L messages carry exact J-AR12 references and never infer verification; and
- N gives bounded content its own typed contract coordinate and preserves the
  original verification treatment through compatibility.

Phase 1 may name a code-level protocol around this behavior. Doing so is a
reversible package/interface choice and does not require another Phase 0
semantic artifact.

### 7.3 Authoritative closure result

Track D finds no second persistence path or mutable-authority loophole. J-AR01
through J-AR17 have one semantic owner, J-P01 through J-P12 are disposable and
rebuildable, and J-P13 remains post-commit observation only. K validates every
authoritative append, cross-record binding, effect claim, state token, G
publication, and J-AR14 output closure in one local unit of work. N adds
compatibility derivation to J-AR14 outside `committed_outputs[]` and therefore
does not reopen K-A41.

Track D passes with the Artifact I v0.2.2 lifecycle-authority wording aligned to
J and K.

### 7.4 Authority and compatibility result

M and N compose without a digest or allocation cycle:

- the caller supplies command/correlation identity and exact semantic inputs;
- the authority profile, compatibility policy, output-coordinate union, and
  compatibility intents enter the authority seed before the deterministic time
  grant;
- K resolves prior command outcome before semantic body loading or adaptation;
- the planner or typed owner operation runs once;
- identity and sequence slots derive from that typed outcome; and
- native outputs commit under exact N-selected coordinates.

Adapters cannot call persistence, authority ports, planners, or other adapters.
State tokens, effect keys, source references, and evidence status remain bound
to original authority. Runtime baseline, import, referenced-journal, query, and
rebuild modes retain their separate K/M/N semantics. No circular bootstrap or
implicit policy-maintenance path remains.

### 7.5 Canonical-proof result

C-001 closes through the ordinary I-S01 through I-S26 sequence, the pre-scope
import seam, all eleven Artifact F accounting events, exact readiness, Pythia
decision use, and normal candidate re-entry. CT-1 closes through baseline party
mapping, referenced J-010 custody, Hermes reconciliation, Argus/Aegis treatment,
two ordinary correction proposal lifecycles, separate effects, verification,
and final issue update.

No application rule branches on C-001, CT-1, P-551, J-010, or another canonical
literal. M's fixture authority profile is keyed by full operation basis, and N
keeps both canonical transactions on exact version-1 paths. F04 is the only
missing transaction-row input found in the canonical crosswalk.

For the executed G trace, Phase 5 must make the permitted Argus and Aegis reads
of Pythia G-11/G-12 products through ordinary `QuerySession` calls so J-P13
observations arise from real calls. These reads create no extra authoritative
consumer record or command and are already permitted by Artifacts G, I, J, K,
and L.

### 7.6 Evidence, readiness, and truth-layer result

Track G passes. Evidence remains either verified content or declaration-only
J-AR12 authority through staging, publication, compatibility, query, and
rebuild. The same hash format never upgrades absent bytes to verified content.
Readiness remains an Aegis-owned version keyed by exact data product, purpose,
period, and scope. Pythia can freeze inputs only from matching exact G-06 and
G-10 versions; neither a corrected value nor a predecessor assessment implies
approval.

Business-event, source-system, accounting, assurance, governed, and decision-
use truth remain distinct. No reconciliation, exception, directive, readiness,
forecast, or approval overwrites a prior truth layer.

### 7.7 Scope result

Track H passes at the semantic level. The Phase 0 set defines the in-process
application boundary, authoritative records/projections, six persistence modes,
strict internal messages, deterministic authority ports, compatibility, evidence
resolution, canonical proofs, and acceptance ownership. It selects no database,
ORM, public transport, authentication system, UI, broker, background worker,
module deployment, or generic workflow.

## 8. Milestone 2 Acceptance Ownership Crosswalk

| Criterion | Primary design owners | Phase 0 status |
|---|---|---|
| M2-A01 | I application boundary; K persistence boundary | Covered |
| M2-A02 | I-R05/I-R06; L-R08; K owner enforcement; N-R08 | Covered |
| M2-A03 | I rejection matrix; L closed bodies; N semantic-class prohibition | Covered |
| M2-A04 | Artifact H planner baseline; K-R07/K-R08; M-R19 | Covered |
| M2-A05 | K command/effect semantics and K-D tests; M retry grants; N retry bindings | Covered by future durable implementation proof |
| M2-A06 | K atomic commit, arbitration, rollback, and failure tests | Covered by future adapter proof |
| M2-A07 | J rebuild sources; K rebuild session; N mixed-version rebuild | Covered |
| M2-A08 | J/K semantic digests; M deterministic grants; N compatibility basis | Covered by future durable implementation proof |
| M2-A09 | I/J/K C-001 maps; M authority proof; N compatibility proof | Covered |
| M2-A10 | I/K/L CT-1 maps; M authority proof; N compatibility proof | Covered |
| M2-A11 | Artifact F/H baseline; N exact version-1 paths | Covered |
| M2-A12 | I publication/observation split; J-P13; K post-commit observation; L-R19 | Covered |
| M2-A13 | I exact G-06/G-10 pairing; L G-10/G-11 bodies; J exact refs | Covered |
| M2-A14 | ADR-016; J-AR12; K staging; L-R18; N bounded content | Covered |
| M2-A15 | Phase 1 dependency rule and explicit roadmap prohibition | Implementation gate defined |
| M2-A16 | Existing H0-H7 suite remains the unchanged regression gate | Executable today |
| M2-A17 | G/L ownership registry; I owner map; K owner enforcement | Covered |
| M2-A18 | I-N non-goals and roadmap section 14 | Covered |
| M2-A19 | Roadmap Phase 7 plus future Milestone 2 assertion report | Intentionally deferred to implementation |

This crosswalk is the implementation-facing Milestone 2 acceptance catalog.
Artifact-level conformance tests remain the detailed proofs; another speculative
schema catalog is not required before Phase 1.

Findings are classified as:

- blocking contradiction;
- required cohesion correction;
- non-blocking implementation clarification; or
- stale documentation only.

## 9. Exit Gate

The audit passes only when:

- every audit track is marked passed with direct artifact evidence;
- both canonical transactions close through ordinary I-N boundaries;
- all material findings are resolved and logged where required;
- H0 through H7, the complete test suite, Ruff, and documentation hygiene pass;
- M2-A01 through M2-A19 have an explicit design owner and future executable
  proof location; and
- the first Phase 1 move can be described as dependency separation without a
  domain-semantic or persistence-product decision.

Until then, no runtime package extraction or database selection begins.

## 10. Verdict and Correction Record

The semantic audit passes. It found and resolved two blocking contradictions and
two required cohesion corrections, with no product-level redesign:

1. amend Artifact I so I-C07 uses only its permitted reconciliation inputs;
2. align Artifact I's current lifecycle wording and I-S18/I-S19 publications
   with Artifact J/K authority;
3. correct the single planner/grant ordering sentence in Artifact M; and
4. add the exact Hermes G-03/L-MP05 input to K's CT-1 Argus row.

ADR-025 records the bounded cohesion correction across I, K, M, and N. All
numbered inventories remain unchanged. H0-H7, the complete test suite, Ruff,
cross-reference checks, and documentation hygiene pass. Phase 0 is closed and
Phase 1 may begin dependency separation without selecting a database or changing
domain semantics.
