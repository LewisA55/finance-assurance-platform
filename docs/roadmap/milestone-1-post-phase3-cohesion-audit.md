# Milestone 1 Post-Phase 3 Cohesion Audit

Status: Passed 2026-08-02 - Phase 4 may begin

## 1. Purpose

This is the mandatory hard audit after the complete immutable conformance
baseline and before commands, planners, stores, or mutation enter the harness.
It reconciles:

- the five platform invariants and `AGENTS.md`;
- Artifacts C, E v0.2.1, F v0.2.1, G v0.2, and H v0.3.1;
- canonical transactions C-001 and CT-1;
- all six fixture files and both non-domain proof boundaries;
- ADR-012 through ADR-017;
- the executable-schema backlog and Milestone 1 roadmap; and
- implementation and tests through H2.

The executable baselines reviewed were:

- `fa179d1`: pre-Phase 2 cohesion audit;
- `ee5abe6`: strict Artifact F contract boundary and H1; and
- `707e733`: pure accounting-integrity baseline and H2.

## 2. Audit Method

The review traced every H0, H1, and H2 claim back to its source obligation,
checked current-status language separately from historical records, inspected
the strict models and negative mutations, replayed the harness twice, and
challenged the Phase 3-to-Phase 4 handoff against Artifact E's broader state
machines and Artifact F's deliberately closed payload set.

The audit specifically tested whether the implementation had:

- collapsed raw and validated corpus state;
- authored J-010 or either reporting proof body as an Artifact F object;
- allowed an accounting event to become posting-rule input;
- compared reversal lines before binding the source projection;
- treated a balanced ledger as sufficient accounting correctness;
- silently reopened June or posted J-560 into the hard-closed period;
- overwritten reporting v1 while proving v2;
- claimed byte verification for evidence bodies that are not committed;
- added a speculative object, event, command, or module contract; or
- reported H3 as passing before state-store digests exist.

None of those prohibited outcomes is present.

## 3. Findings Resolved During the Audit

Three non-architectural assurance gaps were found and closed:

1. H2-02 already joined each posting event to a proposal and journal, but did
   not explicitly assert the journal's `source_proposal_ref` or the proposal's
   terminal `POSTED` state. Both are now part of the pure posting-chain check.
2. H2-06 relied correctly on passed H1 discriminated models, but its H2-local
   assertion counted lifecycle forms without restating the state-conditional
   field rules. The pure check now independently verifies the `PROPOSED`,
   `ADJUSTMENTS_READY`, `APPROVED`, and `PUBLISHED` guards.
3. H2-11 resolved and hash-verified both reporting bodies and the reporting
   object, but did not explicitly bind the publication event's predecessor,
   manifest, content reference, content hash, schema version, and output
   reference to that object. The full publication chain is now asserted.

These fixes strengthen already-ratified obligations. They do not change an
object field, event type, fixture byte, ownership boundary, or architecture
decision, so no new ADR is required.

## 4. Cohesion Results

### 4.1 Object and event boundaries

- Artifact F remains nine object types, ten accounting-event types, and
  seventeen event instances.
- J-010 remains one read-only G-13 projection with `authored_by_f = false`.
- Reporting proof bodies remain test-only content resolved by exact reference
  and hash; they are not financial-statement domain contracts.
- Successful Artifact E transitions outside Artifact F remain deferred.

### 4.2 Truth and ownership boundaries

- Only `business_event` passes the posting-rule input predicate.
- All Artifact F accounting objects and accounting events remain Atlas-owned.
- Aegis issue and directive bodies remain opaque references.
- The future G-14 command disposition remains outside accounting events and
  requires no invented Artifact F subject.

### 4.3 Accounting and temporal integrity

- Four proposals, three journals, and three posting events reconcile in integer
  GBP minor units through their exact proposal-event-journal links.
- The J-010 source hash is bound before J-011 is compared by account,
  dimensions, currency, side, and amount.
- J-560 remains a July ledger journal; June remains `HARD_CLOSED`.
- RC-001's manifest reconciles to J-560 and presents only into its June scope.
- June v1 remains independently retrievable while v2 proves the GBP 10,000
  revenue/deferred-revenue bridge.

### 4.4 Evidence and cryptographic claims

- Only the two reporting proof bodies are content-byte verified, as ADR-016
  requires.
- Nineteen evidence identities retain stable declared hashes without a false
  content-resolution claim.
- The publication event, reporting object, manifest, and v2 proof content now
  form one explicit lineage chain.

### 4.5 Executable status

- H0 passes 7/7.
- H1 passes 14/14.
- H2 passes 11/11.
- The full test suite passes 35 tests.
- Ruff passes.
- Two complete H0-H2 runs produce byte-identical output.
- F-EXE-001 is closed by H2-05; F-EXE-002 remains correctly open for H4.

## 5. Phase 4 Constraints Confirmed

Phase 4 may implement the pure planner under these constraints:

1. `plan(command, immutable_state)` is the only guard implementation.
2. Planning returns a complete `TransitionPlan` or stable rejection and performs
   no I/O or mutation.
3. Commands needed only to exercise deferred Artifact E transitions may exist
   as rejection inputs; they do not author a new Artifact F event variant.
4. Accepted plans remain limited to transitions exercised by C-001 and CT-1.
5. Each in-scope transition family includes at least one accepted control case,
   so the planner cannot pass by rejecting every command.
6. Phase 4 closes H3 guard correctness only. H3's before/after digest and
   no-mutation claim cannot close until Phase 5 stores and registries exist.
7. Command identity and effect idempotency may be represented in planner input,
   but their stateful retry behaviour remains Phase 5/H4 work.
8. A pre-construction directive rejection must not invent an Artifact F subject;
   its G-14 disposition is committed only through the later transactional path.

## 6. Verdict

No architecture, contract, fixture, ownership, or temporal contradiction blocks
Phase 4. The immutable H0-H2 baseline is cohesive and sufficiently strong to
become the read-only input boundary for the pure planner.

The next mandatory overarching audit remains after Phase 7 and before
Milestone 1 closure.
