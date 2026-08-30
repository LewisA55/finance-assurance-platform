# Artifact Q v0.1 Hard Critique

Status: NOT RATIFIABLE - bounded v0.2 correction required

Date: 2026-08-13

## 1. Scope

This critique tests Artifact Q v0.1 against the implemented Finance & Assurance
Platform rather than only against its internal prose and counts.

The review covers:

- the strict Artifact P build request, manifest, registry, package writer,
  verifier, reproducer, and relationship grammar;
- the exact runtime query surface and records in the materialised public demo;
- J-AR03, J-AR04, J-AR05, J-AR06, J-AR07, J-AR08, J-AR13, and J-AR17 source
  availability;
- the implemented P-D01 through P-D21 contracts and their keys;
- C-001 and CT-1 subject closure;
- the proposed ledger-semantics catalogue;
- Q-D01 through Q-D15 field provenance and relationships; and
- backward compatibility of the existing P-only evidence package.

Artifact Q's direction is correct. The blockers are contract-resolution and
traceability gaps, not a reason to change the product thesis or abandon the
shared P-plus-Q package.

## 2. Structural Results

The stated inventory is internally correct:

```text
30 rulings                 Q-R01 through Q-R30
4 use cases                Q-U01 through Q-U04
7 query/view types         Q-Q00/Q-V00 through Q-Q06/Q-V06
10 query invocations       exact stated v1 plan
1 build operation          Q-C01
15 datasets                Q-D01 through Q-D15
23 relationships           Q-RL01 through Q-RL23
36 acceptance criteria     Q-A01 through Q-A36
```

Identifiers are sequential, and the file contains no non-ASCII bytes, tabs, or
trailing whitespace. Those facts establish document hygiene only; they do not
close the semantic blockers below.

## 3. Blocking Findings

### Q-B01 - The second discovery descriptor is not retained by the package

Q-C01 requires both `p_discovery_descriptor_ref` and
`q_discovery_descriptor_ref`, but the existing strict
`governed-export-package@v1` manifest retains only:

```text
discovery_descriptor_ref
discovery_descriptor_hash
```

Those fields currently identify P-Q00. No Q dataset retains Q-Q00's descriptor
identity and hash. Q-D13 retains a canonical request hash, but that is not the
same contract: it does not identify the exact governed descriptor used to
construct the analytical subject plan.

Consequences:

- the package cannot prove which Q descriptor produced its analytical rows;
- P-C03 cannot reconstruct Q-C01 from the manifest basis;
- a resealed package could replace one valid Q subject plan with another while
  retaining only query-level hashes; and
- Q-R01, Q-R06, Q-R07, Q-R27, Q-R28, Q-A02, Q-A19, Q-A33, and Q-A34 are not
  fully executable.

Recommended repair:

- add one Q analytical-context dataset containing the Q descriptor reference,
  descriptor hash, P descriptor reference/hash, registry dependency, snapshot
  coordinates, and scenario-set digest;
- bind that dataset in the manifest and checksum closure;
- require P-C03 to recover the exact Q descriptor basis from that row for a
  P-plus-Q package; and
- keep the package-format manifest fields unchanged for P-only compatibility.

This is preferable to overloading the manifest's existing P descriptor fields
or silently replacing them with a composite descriptor.

### Q-B02 - July `OPEN` is not currently available as the exact state Q promises

Q-R14, Q-Q05, Q-D10, the C-001/CT-1 proofs, and Q-A16 require June
`HARD_CLOSED` and July `OPEN` as exact accounting-period states.

A read-only probe against `build/public-demo.sqlite3` at the current semantic
time proved:

```text
2026-06 current token       AE-C001-003
2026-06 exact G-04 view     available, HARD_CLOSED

2026-07 current token       BASELINE:<projection digest>
2026-07 exact G-04 view     unavailable
```

The July value exists in J-P04 as a rebuildable baseline projection, but no
exact G-04 publication exists for that baseline state. The canonical fixture
does define a July `OPEN` accounting-period object, and J-AR07 is the ratified
authoritative family for period base facts, but the current public demo does not
persist a July J-AR07 record.

Q cannot label the current J-P04 value as exact merely because it is stable in
the demo.

Recommended repair:

- baseline-admit the canonical July period as exact J-AR07 state;
- make Q-V05 a strict two-variant read:
  `BASE_FACT` from J-AR07 or `TRANSITION_PUBLICATION` from exact G-04/J-AR13;
- add `state_basis_type`, `state_authoritative_ref`, and
  `state_record_semantic_hash` to Q-D10;
- require a state token/publication only for the transition variant; and
- continue prohibiting J-P04 from the exported authoritative row.

This uses the existing record model. It does not require a fake `period.opened`
event or a synthetic G-04 command publication.

### Q-B03 - The proposed nullable relationships are not representable by the current relationship contract

Q-RL18 through Q-RL20 are described as nullable relationships. Artifact P's
implemented standard relationship validator has no nullable semantics: it
constructs the source key for every selected row, so `(None,)` fails against
the target key set.

The implemented grammar supports only:

- required standard relationships;
- a single equality condition;
- polymorphic parents; and
- no `IS_NOT_NULL`, variant-union, or optional foreign-key rule.

The manifest also fixes `relationship_contract_version = 1`.

Consequences:

- a valid restatement row would fail the source-projection relationship;
- valid reversal/replacement rows would fail business-event and posting-rule
  relationships; and
- implementing an undocumented null skip would change verifier semantics
  without a contract version.

Recommended repair:

- define relationship contract version 2 for P-plus-Q packages while retaining
  version 1 for P-only packages;
- define the exact condition grammar used by v2;
- prefer equality conditions on a closed source-basis discriminator where
  possible;
- use `IS_NOT_NULL` only if an equality discriminator cannot express the rule;
  and
- add negative tests proving that a non-null unresolved origin fails while the
  non-applicable variant remains valid.

### Q-B04 - Scenario membership and the restatement drill-through path are under-related

Q-D04 through Q-D09 carry `scenario_ref`, but no Q relationship requires those
references to resolve to P-D02. Q-D13 may also carry scenario scope without the
equivalent of P-RL15.

The C-001 restatement use case also lacks a registered path from Q-D04's
`restatement_case_ref` to the existing P reporting model. The value is present,
but matching names do not create a relationship under Q-R20.

Consequences:

- a mistyped or cross-scenario analytical row can pass relationship validation;
- Excel and Power BI do not receive the same declared scenario dimension path;
- Q-U02 depends on an unregistered manual join; and
- Q-A24 does not actually prove complete shared-model relationships.

Recommended repair:

- add one logical scenario-membership relationship family, expanded to explicit
  registry-qualified entries for Q-D04 through Q-D09;
- add a conditional Q-D13 scenario-scope relationship to P-D02;
- relate restatement-origin Q-D04 rows to the unique P-D05 successor reporting
  version through `(scenario_ref, restatement_case_ref)`; and
- keep that origin relationship out of the consumer model if its purpose is
  integrity/drill-through rather than filter propagation.

### Q-B05 - Q-Q00 validates scenario membership, but not analytical subject completeness

Q-R06 correctly prohibits literal branching. However, Q-Q00 currently accepts
the composition-root subject descriptor and checks only that it belongs to the
same P scenario set. It does not prove that the selected subjects are the exact
subjects already exposed by the ratified P/O journeys.

A caller could substitute another existing J-AR08 journal or omit the correct
source basis while retaining valid scenario identifiers and the required
invocation count.

The exact closure is already available:

- C-001 J-560, its business event, and its posting rule are named by O-V10's
  exact directed trace;
- CT-1 J-011, J-012, and the J-010 source are named by O-V11;
- the June reporting period is named by O-V04/O-V05; and
- the July correction period is the exact ledger period of the selected
  authored and referenced journals.

Recommended repair:

- execute the P/O evidence plan before compiling the final Q plan in the same
  pinned session;
- reconcile every Q scenario subject against those exact P/O outputs;
- allow only the ledger-semantics catalogue reference as a genuinely new
  descriptor-supplied authority;
- derive or validate the period set from the exact reporting and journal
  subjects; and
- reject extra, missing, duplicate, or cross-scenario subjects.

This makes Q discovery an extension of the governed evidence boundary rather
than a parallel hand-authored subject list.

### Q-B06 - Q-Q04 conflates the J-AR17 source with its G-13 publication

The actual J-AR17 record for J-010 contains the immutable source body and exact
semantic hash, but its semantic body does not contain:

```text
authored_by_f
projection_type
projection_version
source_hash
publication identity
```

Those projection-class fields are published by the paired exact G-13 J-AR13
record `PUB-G13-CT1-J010`. That publication also proves the hash binding from
its G-13 payload to the J-AR17 authoritative reference.

Q-Q04 currently says it returns an exact G-13/J-AR17 projection but does not
define the pair or the binding test. Q-D08 then appears to source all fields
from one object that does not contain them.

Recommended repair:

- make Q-V04 a strict bound pair of one J-AR17 source and one exact G-13 J-AR13
  publication;
- require G-13 `source_hash` to equal the J-AR17 semantic hash before emitting
  any row;
- retain the G-13 publication reference, payload hash, publication basis, and
  source authoritative reference in Q-D08 or its evidence/lineage children;
- source `authored_by_f = false` from the exact G-13 payload, not a package
  constant; and
- preserve the `J-AR17:<identity>` analytical key required by P-D13.

### Q-B07 - Verified hash statuses have no proof reference

Q-D06 and Q-D12 carry `verification_status`, but neither dataset identifies the
exact proof source used when the status is `CONTENT_BYTES_VERIFIED`.

For example, the CT-1 reversal input hash can be verified against exact J-AR17
bytes. Merely writing `CONTENT_BYTES_VERIFIED` alongside the hash does not let
an offline reviewer reproduce why it was promoted above `DECLARED_HASH_ONLY`.

Recommended repair:

- add nullable `verification_proof_ref` to Q-D06 and Q-D12;
- require it exactly when status is `CONTENT_BYTES_VERIFIED`;
- require it to resolve through Q-D14 source closure or an exact registered Q/P
  row containing the canonical bytes/hash; and
- reject a proof reference for `DECLARED_HASH_ONLY`.

### Q-B08 - The ledger-semantics contract duplicates its mapping and leaves its validation matrix unstated

The proposed catalogue places `statement_field_ref` inside each `accounts[]`
entry, Q-D01 repeats it, and Q-D03 publishes the same account-to-statement
mapping again. That gives one domain mapping two on-wire homes and creates an
avoidable equality invariant.

The catalogue also requires account class, normal balance, and statement class
to match a finite v1 rule table, but the table is not actually written down. A
strict validator cannot implement that sentence without making a design choice.

Recommended repair:

- define separate `accounts[]`, `statement_lines[]`, and `mappings[]` collections
  in the exact catalogue body;
- remove `statement_field_ref` from the account entry and Q-D01;
- make Q-D03 the only governed account-to-statement mapping table;
- keep Q-D05/Q-D09 `statement_field` as an explicit governed-catalogue lookup;
  and
- publish the exact v1 class/balance/statement/control-role matrix in Artifact
  Q so the serializer and validator have no discretion.

### Q-B09 - P-C01 byte compatibility is impossible after the new baseline records

Q-A03 says Q-C01 leaves P-C01 evidence-only output byte-compatible. That is too
strong and is false for the proposed implementation.

Adding the ledger-semantics J-AR04 record and the missing July J-AR07 record
changes the authoritative inventory. O-V01 and P-D01 deliberately expose the
authoritative inventory digest and query revision. Therefore a newly
materialised P-only evidence package from the expanded baseline must have
different domain bytes and a different package digest.

What can and should remain compatible is:

- the P-C01 request contract;
- the `P-EVIDENCE@v1` dataset schemas, paths, registry hash, and semantics;
- verification of already-created P-only packages by the upgraded verifier;
- exact reproduction of an old package while its named source revision remains
  available; and
- the rule that P-C01 does not add Q files.

Recommended repair:

- replace `byte-compatible` with `contract- and registry-compatible`;
- explicitly allow ordinary snapshot values and package digests to change when
  the authoritative runtime inventory changes; and
- test old P-only package verification separately from new-runtime P-C01 output.

## 4. Non-Blocking Tightening

### Q-N01 - Bound predecessor traversal to one declared edge

Q-V02's C-001 origin enrichment is defensible, but it should say that the query
may follow exactly the declared `predecessor_proposal_ref` once. It is not a
second generic J-P11 traversal engine.

### Q-N02 - Use family-qualified authoritative references everywhere

Q-D14 `source_ref`, Q-D10 state authority, and Q-D06 proof references should use
family-qualified exact references. Bare identities are insufficient where two
record families may share an identifier.

### Q-N03 - Key verifier data by composite registry identity

The implemented P verifier currently indexes datasets by `dataset_id` because
only P exists. Q already states that dataset identity is
`(registry_id, dataset_id)`. The implementation should refactor to that composite
key even though P-D and Q-D prefixes happen not to collide.

### Q-N04 - Keep the catalogue identifier illustrative

The draft correctly labels `LEDGER-SEMANTICS-DEMO@v1` as composition-root data.
The v0.2 pass should ensure no acceptance wording accidentally promotes it to a
reusable-code literal.

### Q-N05 - Define the exact canonical row expectations after the repairs

Once the analytical-context and period-source changes settle, the C-001 and
CT-1 proofs should name the expected canonical row counts for every Q dataset.
That will make implementation drift immediately visible without claiming those
counts are enterprise volume.

## 5. What Is Already Strong

The following choices survive critique:

- one P-plus-Q package and one pinned query session;
- a separate `Q-ANALYTICS@v1` registry rather than expanding P-EVIDENCE;
- a separate Q-C01 request rather than mutating P-C01;
- exact-original reads only;
- no generic J-AR, SQL, SQLite, HTTP, or browser export boundary;
- integer minor units and explicit currency;
- separate authored and referenced journal datasets;
- reuse of P reporting, readiness, assurance, governance, decision, correction,
  and trace conclusions;
- one Atlas-owned ledger-semantics catalogue instead of inferred account names;
- statement-field enrichment from governed configuration rather than consumer
  logic;
- consumer calculations remaining explicitly subordinate;
- no synthetic-volume expansion for visual appeal; and
- Excel and Power BI remaining blocked until Q implementation passes a cohesion
  audit.

## 6. Recommended v0.2 Repair Sequence

1. Close authoritative source semantics first:
   - Q-B02 exact period variants;
   - Q-B05 evidence-bound discovery; and
   - Q-B06 bound G-13/J-AR17 referenced state.
2. Close package and compatibility semantics:
   - Q-B01 analytical context and reproduction basis; and
   - Q-B09 P-only compatibility wording and tests.
3. Close relationship semantics:
   - Q-B03 relationship contract v2; and
   - Q-B04 scenario/restatement relationships.
4. Close proof and catalogue semantics:
   - Q-B07 proof references; and
   - Q-B08 normalized catalogue plus exact validation matrix.
5. Apply Q-N01 through Q-N05, recount the artifact, and repeat the C-001/CT-1
   proofs against the actual runtime.

## 7. Verdict

Artifact Q v0.1 is not ratifiable.

The core architecture is sound and no product-level redesign is required. The
nine blockers are bounded corrections needed to make the promised analytical
package reproducible, exact, relationship-safe, and compatible with the
implemented evidence package.

No Excel workbook, Power BI semantic model, wider synthetic population, or
Artifact Q implementation should begin until a v0.2 draft resolves Q-B01
through Q-B09 and passes this critique again.
