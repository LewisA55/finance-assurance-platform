# Milestone 4 Post-Analytical-Registry Cohesion Audit

Status: PASSED - 2026-08-13

## 1. Scope

This audit tests the bounded Artifact Q v0.2 implementation authorised by
ADR-037. It covers the finite `Q-ANALYTICS@v1` read registry, the closed
P-plus-Q package variant, the upgraded offline verifier and reproducer, and the
continued validity of the existing P-only package.

It does not assess an Excel workbook, Power BI model, wider synthetic
population, public download route, paid API, credential, or production data
warehouse. None has been introduced.

## 2. Implemented Boundary

The implementation adds:

- one exact Atlas-owned ledger-semantics catalogue and its evidence authority;
- one exact July 2026 J-AR07 accounting-period base fact;
- Q-Q00 plus Q-Q01 through Q-Q06 and Q-V00 through Q-V06;
- `Q-ANALYTICS@v1`, containing Q-D01 through Q-D16;
- Q-RL01 through Q-RL28, with Q-RL24 serialized once per declared source
  dataset;
- Q-C01 as a strict two-registry build over one pinned query session;
- the two closed package variants: P-only relationship v1 and P-plus-Q
  relationship v2;
- offline composite `(registry_id, dataset_id)` validation;
- exact Q reproduction through the existing package contract; and
- a closed Q-A01 through Q-A45 acceptance catalogue.

The canonical Q build retains exactly ten query executions, fourteen evidence
bindings, thirty-eight invocation-local source rows, and all sixteen ratified
dataset counts.

## 3. Hard Findings and Resolution

### F1 - Dense initial implementation obscured review

The first Q registry and tabularizer draft used compressed one-line structures.
This was not semantically wrong, but it was below the repository's auditability
standard. All Q modules were formatted and decompressed before further work.

Resolution: closed. Ruff passes across the repository.

### F2 - Q-D08 hash fields were initially typed as text

The first registry draft reused a text-column shortcut for the J-AR17 and G-13
hash coordinates. That would have weakened canonical CSV validation.

Resolution: closed. Every Q-D08 hash coordinate now uses the registered hash
type and the offline verifier checks the source-binding equalities.

### F3 - Q-D14 source closure needed the exact ratified deduplication rule

Generic deduplication produced thirty-six rows and no deduplication produced
thirty-nine. Artifact Q requires thirty-eight: semantic-role repetitions remain
visible except for the reversal proposal and posting event's shared exact
evidence authority, which appears once within that invocation.

Resolution: closed. The query assembler applies only that bounded collapse and
the verifier requires exactly thirty-eight Q-D14 rows.

### F4 - Dataset identity was not composite throughout verification

The first verifier extension keyed parsed data by `dataset_id` after validating
the manifest's composite identity. That worked only because P and Q currently
use distinct prefixes and did not meet Q-A43.

Resolution: closed. Parsed registries and relationship endpoints now use exact
`(registry_id, dataset_id)` coordinates. Many-to-one and polymorphic relations
require exactly one registered target.

### F5 - Q-Q00 subject equality was implicit

The first build validated snapshot coordinates but did not explicitly reconcile
the selected journals, event, posting rule, source projection, periods, and
scenarios against the already-executed P/O evidence and parameterised scenario
outputs.

Resolution: closed. Q-C01 now rejects a mismatched subject plan before executing
domain Q reads. A negative test also proves staging cleanup and absence of a
final package.

### F6 - Q-Q00 instance identity used the wrong preimage

The initial structural Q-Q00 instance reference reused a Q-Q01-shaped object and
therefore did not share the Q-Q00 canonical request hash preimage.

Resolution: closed. Q-D13 derives both the Q-Q00 request hash and instance
reference from the exact Q-Q00 canonical request body.

### F7 - Q criteria were not yet machine-mapped to evidence

The implementation initially had focused tests but no Q-A01 through Q-A45
catalogue comparable to Artifact P.

Resolution: closed. The Q catalogue is finite, validated, and included in the
single Milestone 4 P+Q acceptance report.

## 4. Cohesion Results

The audit confirms:

- P-only packages still verify under `P-EVIDENCE@v1` and relationship v1;
- Q cannot verify without its required P registry;
- P-plus-Q packages contain exactly thirty-seven datasets and relationship v2;
- all P and Q queries share one query revision and semantic-as-of time;
- Q reads only exact registered records and never reads SQLite directly;
- J-AR08 authored journals remain distinct from J-AR17/G-13 referenced state;
- reversal input verification resolves the exact family-qualified J-AR17 proof;
- the ledger catalogue is the only new Q descriptor-supplied authority;
- journal totals, strict origin variants, account mappings, period bases, and
  cross-registry relationships are checked offline;
- one-byte Q tampering is rejected;
- a mismatched Q subject plan is rejected atomically; and
- the complete package reproduces byte-for-byte from revision 42.

## 5. Executable Evidence

The final acceptance command is:

```text
.venv\Scripts\python.exe governed_outputs.py acceptance
```

Results:

- Ruff: PASS;
- pytest: 222 tests collected and PASS;
- P-A01 through P-A45: PASS;
- Q-A01 through Q-A45: PASS;
- P-only offline verification: VERIFIED;
- P-only reproduction: REPRODUCED;
- P-plus-Q offline verification: VERIFIED;
- P-plus-Q reproduction: REPRODUCED; and
- machine-readable report: `build/milestone-4-report.json`, overall PASS.

The first retained local analytical package is:

```text
build/governed-outputs/Q-ANALYTICS-DEMO
```

It contains thirty-seven datasets, 706 rows, seventy-nine checked files, query
revision 42, and digest
`sha256:3e803d0854444cb3698bdf64302753ed0696bc99e8c9b959d313c9df6998a727`.
Offline verification returns `VERIFIED`; exact reproduction returns the same
digest.

## 6. Residual Boundaries

No blocking cohesion issue remains inside the ratified Artifact Q scope.

The package still represents deliberately narrow canonical depth: C-001 and
CT-1, four accounts, four statement lines, three authored journals, one
referenced journal, and two period bases. It is not described as an enterprise
warehouse or broad accounting population.

Excel and Power BI are now unblocked at the governed-source boundary, but remain
separate consumer artifacts. They must import only a successfully verified
P-plus-Q package, keep workbook/model assumptions separate from governed values,
and may not create new finance authority.

## 7. Verdict

PASS.

The Artifact Q v0.2 implementation is cohesive with the runtime, public-product,
Artifact P, persistence, evidence, and compatibility boundaries. The next
authorised design step is the first local consumer contract, beginning with the
Excel model unless a different consumer order is explicitly chosen.
