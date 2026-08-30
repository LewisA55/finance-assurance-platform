# Executable Schema Backlog

These items implement already-ratified Artifact F behaviour. They do not reopen the payload-contract boundary.

## F-EXE-001: Bind Referenced Projection to Reversal Input

Status: Closed 2026-08-02 by H2-05

Target: executable schema validation and fixture harness

The harness must assert:

```text
referenced J-010 projection.source_hash
=
P-REV-010@v1 origin_basis.input_hashes[0]
```

Only after that binding passes may it prove that J-011 is mechanically equal and opposite to the projected J-010 lines.

Implemented by the pure H2 integrity layer. The executable proof also mutates
both the binding and a projected line independently, confirming that binding
failure is reported before reversal-line comparison.

## F-EXE-002: Exercise Command Retry and Deduplication

Status: Closed 2026-08-02 by H4-01 through H4-04

Target: stateful command/event harness

The harness must demonstrate:

- repeated delivery of one logical command under the same `command_id` returns the original outcome;
- the retry appends no second accounting event;
- a different event cannot be appended under a consumed `command_id`; and
- posting or publication under an already-consumed effect-scoped `idempotency_key` is rejected even when a different command identity is supplied.

Implemented by the immutable command-result and effect registries. H4-01 proves
same-command replay, H4-02 proves a consumed command identity cannot be rebound,
and H4-03/H4-04 independently prove posting and publication effect deduplication
under fresh command identities.
