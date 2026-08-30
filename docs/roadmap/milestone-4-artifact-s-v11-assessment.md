# Artifact S v0.11 Structural and Semantic Reassessment

Status: NOT RATIFIABLE - two bounded executable-authority blockers

Date: 2026-08-23

## 1. Scope and method

This independent reassessment tested the bounded v0.11 correction against the
two findings from v0.10, all forty-one private mutation recipes, all six reseal
contracts, the authenticated R provenance inputs, the retained R3 and consumer
boundaries, and the complete repository regression.

The assessment added two adversarial controls beyond the v0.11 tests:

- execute every reseal over an untouched positive context and require no state
  change; and
- replace the XLSX-capacity mutation with a lower row count and require the
  capacity validator not to report overflow.

## 2. Evidence that passes

The provenance blocker is closed. Every embedded source body hashes to its
declared `SourceDocumentBinding.sha256`, repeated paths have byte-identical
bodies, JSON inputs parse under their named R contracts, and `model.digest` is
the exact LF-terminated digest of the checksum-ledger bytes. All R-derived
pointers resolve from the authenticated parse, including the retained semantic
column index 79 and relationship indices 25 and 26.

All forty-one declared mutations still reach their admitted checkpoint and
public failure under the supplied negative recipes. Changing recipe field 9 no
longer changes the observed result. The complete regression passes with 294
tests and Ruff is clean. Production authority loaders remain pinned, R remains
the DuckDB owner, and no handoff or consumer output is emitted.

## 3. Blocking finding S11-B01 - positive seals are not fixed points

The positive v0.11 `seal_state` is not constructed with the same formulas used
by the reseal executor. Resealing an untouched context changes the following
fields:

```text
R cache plus noncanonical manifest   s_noncanonical_manifest_digest
S canonical                         handoff_digest
S XLSX                               s_noncanonical_manifest_digest
R model                              r_model_digest
staged canonical                    staged_handoff_digest
```

Only the cache-only path is idempotent. A non-empty `reseal_state_changes`
result can therefore arise from inconsistent positive initialization rather
than from the mutation under test. The changed-field assertion is not yet
reliable executable evidence.

## 4. Blocking finding S11-B02 - checkpoint rules are delta detectors

The v0.11 validator returns a failure when the target differs from its captured
positive baseline, subject only to an optional logical kind. It does not
evaluate the checkpoint-specific predicate named by the failure.

An adversarial copy of `XLSX_CAPACITY_OVERFLOW` changed the row count from four
to three. The resolver still returned:

```text
C01_XLSX_CAPACITY_VERIFIED
XLSX_CAPACITY_EXCEEDED
```

Reducing the row count cannot exceed worksheet capacity. The result proves that
the failure label remains encoded by a target-to-outcome table. Expected-
checkpoint independence passes, but semantic validator independence does not.

## 5. Bounded v0.12 correction sequence

No package tree, R3 ownership, metadata projection, provenance, SQL, workbook
profile, failure code, checkpoint, recipe, operator, product, or consumer change
is required. The next correction must only:

1. construct positive seal values with the exact pure functions used by every
   reseal and require all six clean reseals to be idempotent;
2. bind changed seal values to explicit logical checksum, manifest, and detached
   digest coordinates rather than a detached state-change counter;
3. replace generic baseline inequality with checkpoint-specific predicates for
   capacity, paths, writer support, runtime availability, digest equality,
   workbook representation, source equivalence, and governed authority
   equality;
4. retain expected checkpoints and fixture failures only as post-observation
   assertions; and
5. add benign and boundary controls proving that lower/in-capacity row counts
   and valid directory paths do not inherit negative outcomes.

Historical authorities and the v0.11 authenticated provenance vectors must
remain unchanged. Production loaders must not be repointed.

## 6. Verdict

Artifact S v0.11 is not ratifiable. Its provenance correction passes, but its
positive reseal state and validator semantics do not provide independent
executable evidence. Phase S1 resumption, loader repointing, handoff generation,
and consumer work remain blocked pending a bounded v0.12 correction and another
independent reassessment.
