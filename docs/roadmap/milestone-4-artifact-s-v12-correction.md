# Artifact S v0.12 Bounded Correction

Status: COMPLETE - ready for independent reassessment

Date: 2026-08-23

## 1. Scope

This correction addresses only S11-B01 and S11-B02 from the independent v0.11
reassessment:

- make every positive seal an idempotent fixed point of its reseal algorithm;
  and
- replace target-delta failure lookup with checkpoint-specific semantic
  predicates.

The authenticated v0.11 provenance vectors are retained byte-for-byte. No
package tree, R3 ownership, SQL, workbook profile, failure code, checkpoint,
recipe, operator, finance semantic, product boundary, or consumer claim changes.
Production loaders remain pinned, and no handoff or consumer output is emitted.

## 2. New executable authority

The correction adds:

- `tests/fixtures/local-analytical-handoff/mutation-positive-context-v4.json`;
- `tests/handoff/v12_authority_builder.py`;
- `tests/handoff/v12_logical_resolver.py`; and
- `tests/handoff/test_v12_authority_correction.py`.

Pinned authority hashes:

```text
mutation-positive-context-v4.json file
sha256:323b56bb4089b8ba9415f3890c1656a17908c35e1eed2df3297cf1792cb935b7

mutation-positive-context-v4.json object
sha256:997e59acd3416dc2645cceb8123de8d43456dca79f0785523261a0e7743292d2
```

The v0.11 metadata authority remains exactly:

```text
metadata-positive-logical-vectors-v4.json file
sha256:bc3a90f5a833c8c45f9de12e780a48a1513f2660b1e705230d2d8b6ad0f59ac0
```

## 3. Idempotent authoritative reseals

The v0.12 builder and resolver share the same pure component and digest-chain
functions. Positive model, source-cache, staged-cache, S-canonical, XLSX,
noncanonical-manifest, and staged-canonical seals are therefore fixed points.
All six reseal contracts make zero changes over an untouched context.

Seal values now live at sixteen explicit logical binding coordinates on the
actual `SOURCE_MODEL`, `SOURCE_HANDOFF`, and `STAGING` document realms. They
represent checksum ledgers, cache/workbook manifests, and detached digest
bodies. Reseals mutate these binding targets directly; there is no detached
`seal_state` map or synthetic seal realm.

Source and staged R cache seals are separate. Their positive logical digests
match because the cache preimage normalizes the realm while retaining the exact
model manifest and DuckDB logical values. A staged mutation changes only the
two staged cache bindings.

Across the seventeen negative reseals:

```text
source R cache plus S noncanonical    3 binding targets changed
S canonical                          3 binding targets changed
S XLSX binary/logical                 3 binding targets changed
R model                              3 binding targets changed
staged R cache                       2 binding targets changed
staged canonical                     3 binding targets changed
```

Every resulting binding equals a fresh computation from the mutated private
context. Resealed requests use the value at the actual handoff-digest binding.

## 4. Semantic checkpoint predicates

The resolver defines forty-one named semantic rules and does not capture a
generic positive baseline. Predicates now evaluate the property represented by
the checkpoint, including:

- exact governed source, metadata, validation, and SQL authority equality;
- source/cache and reproduction/cache logical equivalence;
- forbidden recursive digest fields and unexpected package paths;
- XLSX safe-integer representation, null absence, formula/external-link
  absence, and worksheet capacity including the header row;
- path type, output absence, supported writer membership, and runtime
  availability;
- R3 profile version, digest syntax, copy stability, binary-member integrity,
  and reproduced canonical digest equality; and
- operation-specific runtime fault state.

Recipes are still applied only after their declared checkpoint. Validation
stops at the first predicate failure. Recipe field 9 and fixture outcomes are
used only after observation by the test.

## 5. Adversarial controls

All forty-one negative recipes retain their admitted first checkpoint and
public failure. Additional controls prove that:

- changing the expected checkpoint does not change an observed failure;
- changing that same negative recipe to row count three produces no capacity
  failure;
- row count 1,048,575 is admitted for one header row while 1,048,576 fails;
- an alternate value whose resolved path kind remains `DIRECTORY` passes the
  path firewall; and
- every clean reseal is idempotent before any mutation.

## 6. Verification

```text
focused v0.12 tests       6 passed
complete handoff tests   31 passed
complete repository     300 passed
Ruff                     All checks passed
```

The only expected warning is the existing inability to create `.pytest_cache`;
repository-local `--basetemp` paths are used successfully.

## 7. Gate

The bounded v0.12 correction is complete and ready for independent structural
and semantic reassessment. It is not ratified. Phase S1 resumption, production
loader repointing, handoff generation, and consumer work remain blocked until
that reassessment passes.
