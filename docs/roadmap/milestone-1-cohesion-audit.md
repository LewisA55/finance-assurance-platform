# Milestone 1 Cohesion Audit

Status: Pre-Phase 2 audit passed 2026-08-02

Baseline commit audited: `a0c3b69`

## Purpose

This audit tests the implemented foundation against the complete durable design
baseline before Artifact F is frozen into strict executable contracts.

The review covers:

- the five platform invariants and event-stream firewall;
- Artifacts C, E, F, G, and H;
- C-001 and CT-1;
- ADR-001 through ADR-017;
- the six canonical fixture files;
- Milestone 0 and Milestone 1 roadmaps;
- executable backlog items F-EXE-001 and F-EXE-002;
- Phase 0/1 implementation and tests; and
- README claims and repository paths.

## Hard Findings Resolved

### 1. RC-001 fixture ownership wording

Artifact H described `restatement-case-snapshots.jsonl` as containing all five
exercised projections. It contains the four non-terminal forms; terminal
`PUBLISHED` is the canonical `restatement_case` object. Artifact F already
defined that split and H0 correctly proves the five-form union.

Resolution: Artifact H advances to v0.3.1 as a wording clarification only. No
fixture, test ID, count, or acceptance boundary changes.

### 2. Artifact F implementation status

Artifact F still described schema technology as undecided and executable
translation as future work. The contract remains technology-independent, but
the active roadmap now selects Pydantic v2 as a reversible implementation
choice.

Resolution: distinguish the technology-neutral contract from the chosen
Milestone 1 implementation.

### 3. Historical decision register

`open-decisions.md` contained only resolved questions, referenced Artifact E
v0.2 rather than v0.2.1, and could be mistaken for the authoritative ADR log.

Resolution: mark it closed and historical, update the settled Artifact E
version, and retain `decision-log.md` as the only authoritative append-only
record.

### 4. C-001 narrative completeness

The product-level event flow omitted several accounting events even though the
fixtures and Artifact F correctly fixed eleven instances.

Resolution: list submission of P-551@v2 and the restatement link, readiness,
approval, and publication steps explicitly. The transaction mechanics do not
change.

### 5. Test ownership after Phase 1

The deterministic runner test remained in the Phase 0 substrate suite after
the runner began executing H0.

Resolution: the runner assertion moves to the H0 suite; Phase 0 retains only
runtime and protocol tests.

## Findings Confirmed as Intentionally Unchanged

- ADR-017 describes the harness as unbuilt because it records the state at
  ratification. That historical statement is not a current status claim.
- Artifact G v0.2 binds the v0.2 domain contract. Artifact F v0.2.1 changed
  only non-domain reporting proof fixtures, so G does not require re-ratification.
- Artifact E contains valid transitions beyond Artifact F's closed event set.
  Artifact H explicitly defers executing those transitions in Milestone 1.
- F-EXE-001 and F-EXE-002 remain open: they close in H2 and H4 respectively.
- Artifact C includes conceptual business-event examples beyond the first
  executable payload boundary; they do not expand Artifact F v1.

## Executable Baseline Confirmed

- `RawCorpusIndex` is separate from the future `ValidatedCorpusIndex` and is
  recursively immutable.
- Canonical serialization is independent of Pydantic and uses compact,
  lexically sorted UTF-8 JSON bytes.
- All six fixture files remain the sole corpus and are not rewritten.
- H0 proves the nine-type union as eight non-event object types plus
  `accounting_event`.
- H0 combines four supplemental RC-001 snapshots with terminal `PUBLISHED`.
- Both reporting proof bodies are cryptographically verified.
- Declared-only evidence remains reference/hash consistency only.
- J-010 remains one non-authored G-13 projection.
- Phase 1 introduces no posting evaluator; the accounting-event firewall
  remains a structural requirement for independent H2 and H6 proof.

## Audit Conclusion

No unresolved architecture or contract blocker remains before Phase 2.

The next hard cohesion audit occurs after Phase 3 and before Phase 4, when H0,
H1, and H2 form the complete immutable conformance baseline and before any
stateful command behavior is introduced.
