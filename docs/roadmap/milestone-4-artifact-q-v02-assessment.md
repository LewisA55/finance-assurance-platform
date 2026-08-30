# Artifact Q v0.2 Ratification Assessment

Status: RATIFIED - ADR-037 accepted 2026-08-13

Date: 2026-08-13

## 1. Scope

This assessment re-tests Artifact Q v0.2 against:

- all nine blocking findings and five non-blocking findings from the v0.1 hard
  critique;
- the implemented Artifact P contracts, registry, relationship grammar,
  package writer, verifier, and reproducer;
- the materialised C-001 and CT-1 authoritative records;
- the exact Artifact P dataset keys used by Q's cross-registry relationships;
- the ratified Artifact F accounting-period and referenced-state fixtures; and
- the repository invariants governing authority, readiness, evidence, and
  reproducibility.

The result is positive. No unresolved contract-boundary blocker remains.

## 2. Structural Results

The revised inventory is internally consistent and mechanically verified:

```text
30 rulings                 Q-R01 through Q-R30
4 use cases                Q-U01 through Q-U04
7 query/view types         Q-Q00/Q-V00 through Q-Q06/Q-V06
10 query invocations       exact stated v1 plan
1 build operation          Q-C01
16 datasets                Q-D01 through Q-D16
28 logical relationships   Q-RL01 through Q-RL28
45 acceptance criteria     Q-A01 through Q-A45
```

Q-RL24 deliberately expands into six serialized relationships. Identifiers are
sequential. The document contains zero non-ASCII bytes, tabs, or trailing
whitespace.

## 3. Blocking-Finding Closure

| Finding | Resolution | Result |
|---|---|---|
| Q-B01 | Q-D16 retains both descriptor identities/hashes, the P-D01 context link, shared snapshot coordinates, registry versions, catalogue ref, and relationship version. | CLOSED |
| Q-B02 | Q-V05/Q-D10 now distinguish exact J-AR07 `BASE_FACT` from G-04/J-AR13 `TRANSITION_PUBLICATION`; J-P04 is prohibited. | CLOSED |
| Q-B03 | P-only packages retain relationship contract v1; P-plus-Q packages use a closed v2 grammar with equality-conditioned origin relationships. | CLOSED |
| Q-B04 | Scenario membership, scenario-scoped query execution, restatement-case integrity, P package context, and catalogue context are explicitly related. | CLOSED |
| Q-B05 | Q-Q00 proves exact subject-set equality against already-executed P/O views; only the catalogue is new descriptor-supplied authority. | CLOSED |
| Q-B06 | Q-V04/Q-D08 bind J-AR17 to G-13 by exact upstream authority, source hash, payload hash, and shared-field equality without conflating the two schemas. | CLOSED |
| Q-B07 | Q-D06 and Q-D12 require family-qualified proof refs exactly for `CONTENT_BYTES_VERIFIED`. | CLOSED |
| Q-B08 | The catalogue is normalized into accounts, statement lines, and mappings with one closed validation matrix. | CLOSED |
| Q-B09 | Compatibility is correctly limited to P request/registry/schema/verification semantics and old-package support; new runtime snapshots may produce new bytes. | CLOSED |

## 4. Non-Blocking-Finding Closure

- Q-N01: predecessor traversal is limited to one declared edge.
- Q-N02: query sources, period authority, and verification proofs are family-
  qualified.
- Q-N03: dataset and relationship identity is the composite
  `(registry_id, dataset_id)`.
- Q-N04: the demonstration catalogue identity remains composition-root data,
  never a reusable-code literal.
- Q-N05: section 8.17 fixes the canonical row count for every Q dataset and
  decomposes the two non-obvious Q-D12/Q-D14 counts.

## 5. Additional Second-Pass Corrections

The v0.2 review found and corrected three issues beyond the original critique.

First, full G-13 and J-AR17 payloads are not byte-identical: G-13 legitimately
adds projection metadata and J-AR17 retains source-contract metadata. Artifact Q
now requires equality of the shared source fields plus exact hash and upstream-
authority binding. It no longer makes an impossible byte-equivalence claim.

Second, proposal variants no longer collapse `reverses_journal_id` and
`corrects_journal_id`, or restatement and correction policy refs, into generic
columns. The strict origin union preserves their distinct business meanings.

Third, the multi-registry package extension is now explicit. The top-level v1
envelope retains the extension point Artifact P reserved, while registry and
dataset manifest entries become a closed discriminator union supporting only P
or P-plus-Q. Inherited P relationship objects and the P registry contract hash
remain unchanged.

## 6. Canonical Proof Result

The frozen v1 Q inventory is internally derivable from the current reference
cases:

- four accounts, four statement lines, and four mappings;
- three authored journals and six authored lines;
- one referenced journal and two referenced lines;
- one business event, one posting rule, and two exact period-state bases;
- fourteen evidence bindings;
- ten query executions and thirty-eight invocation-local sources;
- one catalogue header and one analytical context row.

The reversal-journal invocation reads exact J-AR17 independently to justify its
verified proposal input hash, even though Q-Q04 reads that authority again for
the G-13 pair. Within the reversal invocation, its proposal and posting event
share one evidence authority; source closure contains that authority once while
Q-D12 retains both semantic roles.

## 7. Ratification Judgment

Artifact Q v0.2 is ratifiable and is ratified by ADR-037.

ADR-037 authorizes only the finite catalogue/base-fact prerequisites,
Q-Q00 through Q-Q06, Q-D01 through Q-D16, Q-C01, relationship contract v2, and
the required P verifier/reproducer extension.

It does not authorize Excel, Power BI, wider synthetic populations, generic
record export, direct persistence access, paid APIs, credentials, or a second
package format. Those remain behind the completed Q implementation and cohesion
audit.
