# Milestone 2 Phase 6 Remediation: F3 and F4

Status: Complete 2026-08-09 - final Phase 6 gate subsequently passed

## 1. Scope

This bounded pass resolves two read-boundary blockers from the post-Phase-6
cohesion audit:

- F4: I-Q05, I-Q06, and I-Q11 lacked their exact token-bound forms; and
- F3: J-P11 guessed through ambiguous references and traversed authority edges
  in both directions.

It does not implement the J-AR01 candidate-receipt producer required by F5.

## 2. F4 Resolution - Exact and Labelled-Current Reads

The method boundary now makes reliance explicit:

| Artifact I query | Exact operation | Operational current operation |
|---|---|---|
| I-Q05 | `get_accounting_period_exact(period_id, state_token)` | `get_current_accounting_period(period_id)` |
| I-Q06 | `get_journal_proposal_exact(proposal_ref, state_token)` | `get_current_journal_proposal(proposal_ref)` |
| I-Q11 | `get_restatement_case_exact(case_id, state_token)` | `get_current_restatement_case(case_id)` |

Exact operations require an Artifact J lifecycle token and resolve one exact
G-04 J-AR13 publication. They return the exact Artifact F body, named token,
state label, and ordered J-AR06 lifecycle evidence through that token. Proposal
reads additionally return the immutable J-AR05 treatment. They never infer the
latest state.

Current operations remain explicitly labelled `CURRENT_REBUILDABLE`. Their
`state_label` is separate from their `exactness_token`: the former describes
the folded state, while the latter identifies the latest visible accounting
event. A baseline-only projection uses an explicit baseline digest token rather
than pretending a status label is authority.

This pass also corrects F6 lifecycle publication stamps from status labels to
their ratified accounting-event IDs. G-04 payloads still contain their exact
Artifact F status; the J-AR13 envelope now carries the actual J-P03/J-P05/J-P07
token.

## 3. F3 Resolution - Directed Strict J-P11

The trace builder no longer scans arbitrary `_ref` fields, creates bidirectional
edges, or returns a connected component. It starts at the exact J-AR10 reporting
version and follows a finite typed set of upstream relationships only.

Internal bindings are resolved by exact record identity within their required
J-AR family. A typed alias may be used only when no exact identity exists and
exactly one authoritative record matches. Zero matches fail as a broken
internal binding; multiple matches fail as ambiguous. The published
restatement case is bound by case identity, `PUBLISHED` state, and exact
manifest hash rather than by a loose case alias.

Only declared evidence, policy, source-system, contract, schedule, and content
references may terminate as labelled external nodes. Those leaves remain
distinguishable as evidence, authority, or source references.

Every returned edge points from a derived claim to one upstream authority. No
reverse edge is synthesized. Consequently a downstream consumer or sibling
record that refers to the reporting version cannot enter a
reporting-to-source trace.

## 4. Executable Proofs

The tests prove:

- exact submitted and deferred views of P-551@v1 remain independently
  reproducible;
- exact hard-close and restatement views resolve by named accounting-event
  token with ordered lifecycle evidence;
- proposal, period, and restatement exact/current result semantics match
  between the in-memory and SQLite adapters;
- semantic-time filtering exposes the hard-close exact view only at its
  recorded time;
- the directed C-001 path reaches J-560, P-551@v2, P-551@v1,
  PR-O2C-RECOG@v1, BE-C001-RECOG-202606, and REVENUE_SUBLEDGER in the upstream
  direction;
- the business-event/source end cannot traverse back to the reporting root;
- an unrelated downstream reporting consumer is excluded;
- ambiguous and broken internal bindings raise `ReadModelError`; and
- the directed J-P11 semantic digest remains identical after projection
  deletion, rebuild, database close, and restart.

## 5. Verification and Next Gate

Ruff passes. All 120 tests pass. The independent H0 through H7 validation
harness also passes without modification.

No ratified architecture changed and no ADR is required. This pass adds no new
command, event taxonomy, repository, workflow framework, API, UI, or
distributed infrastructure.

F5 was subsequently resolved by the ordinary J-AR01 candidate-receipt producer
and I-Q01 restart/rebuild proof recorded in
`docs/roadmap/milestone-2-phase6-remediation-f5.md`. The final cohesion audit
passes.
