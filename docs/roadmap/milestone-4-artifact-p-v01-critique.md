# Milestone 4 - Artifact P v0.1 Hard Critique

Status: Complete; all blocking findings incorporated into v0.2 draft

## 1. Scope

This review tested Artifact P v0.1 field by field against the implemented
Artifact O contracts and assemblers. It separately examined snapshot reuse,
dataset sufficiency, decision-effect grain, domain-versus-transport provenance,
query discovery, ownership, and relationship semantics.

No implementation was authorised by this review. Its purpose was to determine
whether the design was honest enough to enter ratification.

## 2. Verdict on v0.1

Artifact P v0.1 was not ratifiable.

Its package, canonical serialization, hashing, readiness, history, traceability,
and atomic-publication concepts were strong. Its central source assumption was
not: Artifact O is a deliberately curated public-journey boundary and is not a
sufficient analytical source for an Excel model or Power BI semantic model.

## 3. Blocking Findings and v0.2 Disposition

### F1 - Artifact O was too narrow for the claimed analytical consumers

Artifact O does not publish journal lines, recognition schedules, business
events, source populations, reusable account attributes, trial-balance detail,
or general finance facts and dimensions.

Disposition:

- Artifact P v0.2 defines the package and `P-EVIDENCE@v1` evidence registry;
- Artifact O remains the exact source for those evidence datasets;
- a separate future architecture artifact must define a finite governed
  analytical-read registry over the same runtime query session; and
- Excel and Power BI remain blocked until that registry is ratified,
  implemented, audited, and present in a verified Artifact P package.

### F2 - The CT-1 reconciliation request was not discoverable

The current O-V entry points lead to CT-1 correction verification, not to
`RECON-CT1@v1`. The existing tests supplied the reconciliation subject
explicitly, which an exporter could not copy without canonical knowledge.

Disposition:

- v0.2 introduces P-Q00/P-V00 finite export discovery;
- P-Q00 accepts a strict typed discovery descriptor supplied beside the
  parameterised demo descriptor;
- the descriptor contains exact scenario-owned Artifact O request bodies;
- P-Q00 validates the complete plan against one immutable runtime session; and
- no subject literal, route parsing, label parsing, or generic enumeration is
  permitted in export code.

### F3 - The package snapshot invariant was misstated

Artifact O opens one query session per public response. Reusing one reader for
an export would contaminate later invocation `source_refs` with earlier reads.
Success envelopes also do not expose workspace or a separate runtime revision,
and a combined package correctly contains multiple scenario refs.

Disposition:

- P-C01 opens exactly one persistence `QuerySession`;
- every P-Q00/O-Q invocation uses that same immutable session;
- every O-Q invocation receives a fresh public reader;
- query revision and semantic time must agree across all results;
- Artifact O compatibility remains `EXACT_ORIGINAL`; and
- each result scenario must belong to P-Q00's exact complete scenario set.

The public HTTP rule remains unchanged because P-C01 is one internal operation,
not one HTTP response containing multiple views.

### F4 - Arbitrary scenario subsets were unsupported

O-V01 is workspace-wide and includes both reference scenarios. O-V02 is a
C-001 overview. Filtering either view would create new Artifact P semantics.

Disposition:

- P-C01 no longer accepts an arbitrary scenario subset;
- the package uses P-Q00's exact complete scenario set; and
- subset packages require a successor contract.

### F5 - P-D21 added unsupported scenario identity

O-V01 `ScenarioEntryPoint` does not carry `scenario_ref`; its O-Q01 envelope is
C-001 even though the view includes a CT-1 entry point.

Disposition:

- P-D21 scenario ownership comes from P-Q00's typed scenario-owned query plan;
- the remaining entry-point fields are exact O-V01 copies; and
- no journey-id-to-scenario inference remains.

### F6 - The proposed decision-effect child grain did not exist

O-V09 publishes one governed decision with position, dates, and monthly cost.
It does not publish an effect object or `effects[]` collection. The former
P-D13 duplicated P-D11 and relabelled decision fields as a new semantic grain.

Disposition:

- the decision-effect dataset was removed;
- the governed-decision row retains the exact O-V09 fields; and
- an effect dataset is deferred until a successor source contract publishes a
  genuine effect collection.

Dataset identifiers P-D13 onward were reassigned within the still-unratified
draft; no public or persisted contract existed to preserve.

### F7 - Column provenance and ownership were prose-only

The v0.1 schema could not mechanically distinguish copied domain values,
parent-context copies, ordinals, stable row keys, constants, and other Artifact
P metadata. Composite views were also assigned ambiguous single owners.

Disposition:

- every column declares `value_origin`, `source_path`, and `transformation`;
- package-only values are explicitly transport or structural metadata;
- every dataset declares one export steward and one or more semantic owners;
- copied module labels retain the exact Artifact O enum; and
- composite public views no longer invent one authoritative owner.

### F8 - Query provenance and relationships were not closed

One P-D19 row could not distinguish repeated O-Q05 calls. It lacked the exact
query request/version identity. The relationship registry also used prose
wildcards and represented a polymorphic parent relationship as though it were a
normal BI join.

Disposition:

- query provenance is split into P-D18 `query_executions` and P-D19
  `query_sources`;
- every invocation retains its canonical request hash, exact scope, contract
  version, revision, semantic time, compatibility mode, and local sources;
- repeated O-Q05 calls have distinct query-instance identities;
- scenario relationships expand to explicit serialized entries;
- polymorphic parent and graph-edge checks are `INTEGRITY_ONLY`; and
- only declared `CONSUMER_RELATIONSHIP` entries may become Excel or Power BI
  model relationships.

## 4. Dataset Review Summary

The following v0.2 grains are supported as exact copies or lossless structural
reshapes once P-Q00 is ratified:

- package and scenario context;
- module lens summaries;
- both Hermes reconciliation variants;
- Atlas reporting versions, values, and restatement bridge;
- both Argus exception variants;
- exact Aegis governance case and readiness rows;
- Pythia governed decision and frozen inputs;
- CT-1 correction case and journal summaries;
- exact reference bindings;
- unchanged J-P11 trace nodes and directed edges;
- exact query executions and invocation-local source closure;
- readiness limitation values; and
- scenario-owned public entry points.

Journal lines and other analytical grains remain deliberately absent. Their
absence is a product-boundary decision, not an accidental omission.

## 5. Remaining v0.2 Ratification Questions

The next critique should now focus on:

1. whether P-Q00 is finite enough to avoid becoming generic discovery;
2. whether its typed descriptor and validation rule are fully parameterised;
3. whether every column source path and transformation can be implemented
   mechanically;
4. whether the explicit relationship families are complete; and
5. whether the analytical-registry extension point is narrow enough to preserve
   Artifact P package semantics.

Artifact P v0.2 remains a draft. This review records closure of the v0.1
findings; it does not ratify v0.2.
