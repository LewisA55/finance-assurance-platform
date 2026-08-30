# Milestone 3 Phase 7 Cohesion Audit

Status: passed and ratified 2026-08-12

Date: 2026-08-12

## 1. Verdict

The public product remains aligned with the platform thesis and Artifact O.
Phase 7 adds an acceptance boundary; it does not add a second finance engine,
new workflow semantics, external services, or speculative product scope.

The automated foundation is strong enough for the flagship portfolio product:

- the closed catalogue contains exactly O-A01 through O-A33;
- the unchanged Milestone 1/2 acceptance command is a mandatory lower gate;
- all public claims remain revision-pinned projections over ordinary runtime
  and persistence paths;
- the web gate covers all finite journeys and rejects paid, secret, telemetry,
  and external-runtime dependencies;
- deterministic build verification preserves generated security entropy while
  requiring every deployable semantic byte to agree; and
- the report is canonical and distinguishes `PASS`, `FAIL`, and `BLOCKED`.

Milestone 3 is ratified. O-A28 and O-A29 are supported by recorded, hashed,
revision-bound browser evidence produced after the connected-browser review.

## 2. Phase 7 Implementation

The acceptance implementation is isolated in
`finance_assurance.product_acceptance`; the product runtime does not import it.
It provides:

1. a closed 33-row Artifact O evidence catalogue;
2. a deterministic report containing test inventory, quality gates, application
   build digest, inherited Milestone 2 report digest, and criterion outcomes;
3. one clean-checkout runner composing Milestones 1, 2, and 3;
4. strict, revision-bound manual browser evidence; and
5. verified screenshot content hashes constrained to the evidence directory.

Missing manual evidence produces `BLOCKED`. Invalid, stale, escaping, absent,
or hash-mismatched evidence produces `FAIL`. Neither state can become `PASS`
through automated accessibility tests alone.

## 3. Executed Evidence

The implementation pass produced the following direct results:

| Boundary | Result |
|---|---|
| Ruff, repository-wide | PASS |
| Product, M3 acceptance, and unchanged H0-H7 segment | 131 passed |
| Runtime and persistence segment | 72 passed |
| Python total | 203 passed |
| TypeScript | PASS |
| ESLint | PASS |
| Rendered public-product suite | 10 passed |
| Deterministic double build | PASS |
| Application build digest | Revision-specific; recorded in the generated report |
| Local API and web startup | PASS |
| Same-origin O-V01 compatibility | `EXACT_ORIGINAL` |
| Manual desktop/tablet/mobile review | PASS - 27 route/viewport combinations |

The Python suite was executed in two bounded segments after an aggregate shell
capture exceeded its execution window. Both segments passed; the split changed
only process orchestration, not test scope or assertions.

The first clean composed run then exposed a stale 180-second timeout in the
Milestone 2 runner. The expanded 203-test suite correctly exceeded that historic
limit. The runner timeout is now 600 seconds, the outer M3 inheritance gate is
900 seconds, timeouts become explicit failed command results, and old generated
reports are removed before execution. This is an orchestration correction; no
test, criterion, or assertion was removed or weakened.

## 4. Cohesion Findings

### 4.1 No authority inversion

The acceptance package consumes reports, tests, public endpoints, and build
outputs. It cannot commit domain state and is outside both the runtime and
public query packages.

### 4.2 No weakened inherited gate

O-A31 invokes `finance_assurance.acceptance --require-clean`. Milestone 3 cannot
replace or reinterpret the Milestone 1/2 result.

### 4.3 Manual evidence is a first-class boundary

The review is bound to one Git revision, all five browser journeys, and three
ordered viewport classes. Keyboard, focus, navigation, screen-reader order,
overflow, exact governed context, and screenshots must all pass. Screenshot
files are content-hashed and may not resolve outside the evidence directory.

### 4.4 No false completion claim

Automated accessibility and responsive assertions remain insufficient on their
own. The final report promotes O-A28 and O-A29 only because the connected review
produced the separate revision-bound evidence required by the schema.

### 4.5 Browser findings were fixed at the product boundary

The manual pass found encoded direct-route subjects, a framework navigation
shim that destabilised live hydration, three page-level responsive overflows,
and a missing visible governed-decision reference. The bounded corrections add
no domain rule, authoritative store, workflow, external service, or client-side
finance inference. Direct-route decoding, native anchors, constrained wrapping,
and explicit identity display now match the finite public contract.

## 5. Residual Register

| ID | Residual | Severity | Closure |
|---|---|---:|---|
| M3-R02 | Optional public hosting remains unselected | Deferred | Decide only after local Milestone 3 ratification; hosting must not change product semantics |

M3-R02 is not a Milestone 3 acceptance blocker. Artifact O explicitly sets
local reproducibility as the deployment floor and defers the hosting provider.

## 6. Ratification Rule

Milestone 3 is ratified for the exact revision whose clean-checkout acceptance
command returns `PASS` with 33 passing criteria and no failed or blocked quality
gate. Generated evidence is not portable to another revision. Optional hosting
is the only deferred product-delivery choice and may not change the accepted
semantics.
