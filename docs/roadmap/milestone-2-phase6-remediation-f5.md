# Milestone 2 Phase 6 Remediation: F5

Status: Complete 2026-08-09 - post-Phase-6 gate passed

## 1. Scope

This bounded pass resolves the final blocker from the post-Phase-6 cohesion
audit: J-AR01 candidate custody had a finite I-Q01 read but no ordinary I-C01
producer.

The pass implements only the ratified source-admission boundary. It adds no
administrative admission mode, event type, workflow framework, repository, or
module-specific persistence path.

## 2. Ordinary I-C01 Write Set

`CandidateAdmissionService.assess` executes through the existing Artifact K
command unit of work owned semantically by Hermes. One successful assessment
command atomically commits:

- one replayable shared-substrate J-AR01 `CandidateReceipt`;
- one Hermes J-AR02 `hermes.business_event_admission_result`;
- one exact G-02 J-AR13 publication; and
- one J-AR14 command result.

Candidate custody is infrastructure supporting I-C01. It does not give Hermes
ownership of source business meaning and does not create a second semantic
command.

The command service and both persistence adapters validate the exact bindings:

```text
J-AR01 canonical body
  -> candidate payload hash
  -> Hermes admission result
  -> G-02 payload
  -> J-AR14 command closure
```

Missing custody, duplicated identity, inconsistent source identity, payload
hash mismatch, missing G-02, or a partial commit fails the complete write set.

## 3. Derived Admission Outcomes

The caller supplies candidate content and provenance, not an admission outcome.
The finite Milestone 2 registry derives:

| Candidate | Result | G-01 eligibility |
|---|---|---:|
| Valid Artifact F `accounting.recognition.due` version 1 | `ACCEPTED` | true |
| Declared supported type with invalid or unsupported contract bytes | `REJECTED` | false |
| Any unratified type, including `workforce.hiring.deferred` | `UNSUPPORTED` | false |

Rejected and unsupported candidates retain immutable custody and their exact
G-02 disposition. They do not become J-AR03 business events.

## 4. Business-Event Firewall

I-C02 now requires one exact accepted G-02 publication. Before G-01 can commit,
the shared-substrate command proves that:

- G-02 is `ACCEPTED` and `eligible_for_g01 = true`;
- the named J-AR01 receipt exists;
- the J-AR03/G-01 event bytes reproduce the J-AR01 candidate payload hash; and
- G-01 names the exact G-02, candidate receipt, and admitted event.

A rejected or unsupported candidate cannot cross the G-01 boundary. Candidate
receipts and G publications never enter the posting engine; only the resulting
J-AR03 `BusinessEvent` may be evaluated by Atlas.

## 5. I-Q01

`RuntimeQueryService.get_candidate_receipt` now returns one pinned read shape
containing:

- the exact J-AR01 receipt;
- the exact Hermes J-AR02 admission result;
- the exact G-02 J-AR13 publication;
- the derived outcome; and
- the explicit G-01 eligibility flag.

The query fails closed if custody does not resolve exactly one admission product
and one matching G-02 publication. The same semantic receipt and disposition
survive command retry, SQLite restart, and projection rebuild. J-P01 is derived
on demand from those exact records; this pass does not add another persisted
projection store.

## 6. Executable Proof

The regression suite proves:

- accepted, rejected, and unsupported disposition derivation;
- mandatory J-AR01/J-AR02/G-02 closure;
- no direct repository mutation or administrative-mode bypass;
- rejected-candidate exclusion from J-AR03/G-01;
- adapter-level cross-record enforcement shared by memory and SQLite;
- atomic rollback under an injected `command_before_commit` failure;
- same-command retry without duplicate authority;
- changed-input reuse of a command identity rejected without mutation;
- I-Q01 after restart and after disposable projection rebuild; and
- existing C-001 G-02 to G-01 handoff through the same path.

Final verification:

- Ruff: pass;
- pytest: 126 passed; and
- H0-H7 plus H3 guard validation: pass.

## 7. Architecture Status

No ADR is required. This pass implements Artifacts I, J, K, L, and M without
changing a ratified boundary.

F1 through F6 are now resolved. The follow-up post-Phase-6 cohesion audit found
no remaining blocker, so Phase 7 may begin.
