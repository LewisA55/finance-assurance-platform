# Milestone 2 Phase 7 - Acceptance, Audit, and Closure

Status: Passed 2026-08-10 - Milestone 2 complete

## 1. Purpose

Phase 7 converts the implemented persistent runtime into one independently
reproducible milestone result. It does not add domain behavior. It closes the
gap between passing component tests and accepting the complete Milestone 2
platform foundation.

The closure boundary must:

- run the unchanged Artifact H H0-H7 report;
- execute the closed M2-A01 through M2-A19 acceptance catalogue;
- run Ruff and the complete pytest suite;
- compare clean-start, restart, and authority-backed rebuild semantics for
  C-001 and CT-1;
- preserve the product runtime's independence from validation code;
- enforce the milestone's deferred-scope boundary; and
- emit one canonical machine-readable Milestone 2 report.

## 2. Executable Acceptance Boundary

`finance_assurance.acceptance` is a closure-time verification package outside
`finance_assurance.runtime`. It may consume the ratified validation corpus and
the implemented runtime together; the product runtime may not import it or the
Artifact H validation layer.

The boundary contains:

- a closed nineteen-row acceptance catalogue with executable test evidence;
- deterministic JUnit normalization that excludes time, host, paths, and other
  environment metadata;
- a runtime proof that executes both canonical families through SQLite and
  compares clean-start, restart, and rebuilt full-state digests;
- static guards for validation imports, deferred product surfaces, and deferred
  infrastructure dependencies;
- a canonical `milestone-2-acceptance-report@v1`; and
- a clean-worktree gate that prevents M2-A19 from passing against uncommitted
  implementation bytes.

The runtime proof is executed twice in independent temporary databases. Only
semantic identities, counts, statuses, and hashes enter the report.

## 3. Hard Audit Findings Resolved

The Phase 7 implementation review found and corrected three issues before the
candidate was accepted.

1. Artifact H's optional `root` argument is a fixture-directory override, not
   a repository root. Passing the repository root blocked H0 while an older
   successful report remained on disk. The combined runner now uses Artifact
   H's canonical fixture resolution and overwrites both reports on every run.
2. The initial M2-A03 and M2-A18 mappings were directionally correct but too
   indirect. M2-A03 now binds the explicit event-stream firewall and invalid
   G-01 proof. M2-A18 now binds both static surface checks and the closed event
   and workflow taxonomies.
3. Runtime construction helpers previously lived only under `tests/`. They now
   live in the acceptance package because both the full suite and the closure
   report use them. This does not move validation code into the product runtime;
   `finance_assurance.runtime` remains dependency-clean.

No finding changed an Artifact C-N contract, event type, object type, owner,
state transition, persistence rule, or module boundary. No ADR is required.

## 4. Final Results

The committed candidate at `abc6402` passed the clean-worktree closure run:

```text
H0-H7 PASS
RUFF PASS
PYTEST PASS (130 tests)
C001 RESTART-REBUILD PASS
CT1 RESTART-REBUILD PASS
M2 PASS (19/19)
```

M2-A01 through M2-A19 pass. The generated report records nineteen passes, zero
failures, and zero blocks. Both runtime families reproduce one full-state
semantic digest across clean execution, process restart, and authority-backed
projection rebuild.

## 5. Locked Closure Command

From a clean checkout with the locked development environment:

```text
uv run --locked python -m finance_assurance.acceptance --require-clean
```

The command writes:

- `build/validation-report.json` for the unchanged Milestone 1 H0-H7 result;
  and
- `build/milestone-2-report.json` for M2-A01 through M2-A19.

Any Ruff failure, pytest failure, H-layer failure or block, missing evidence
test, semantic mismatch, runtime dependency violation, scope expansion, dirty
worktree, or failed acceptance criterion returns a non-zero exit code.

## 6. Verdict

No architecture, contract, persistence, ownership, accounting, temporal,
evidence, dependency, or scope contradiction blocks closure. Milestone 2 is
accepted and provides the persistent, parameterised, traceable application
foundation on which the public product layer can now be designed.

The accurate status is:

> Ratified architecture baseline; accepted Milestone 2 implementation; product
> surfaces intentionally deferred to the next bounded milestone.
