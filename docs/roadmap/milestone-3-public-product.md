# Milestone 3 - Bounded Public Product

Status: Complete and ratified 2026-08-12

## 1. Purpose

Milestone 3 turns the accepted finance and assurance runtime into one serious,
read-only portfolio application. It does not create a second source of finance
logic. Every public claim remains a projection over exact, revision-pinned
runtime authority.

Artifact O v0.2 and ADR-033 define the binding product boundary.

## 2. Phase 0 - Ratified Product Contract

Complete.

- one application with Hermes, Atlas, Argus, Aegis, and Pythia as lenses;
- three deterministic demo lifecycle operations;
- eleven one-to-one public query/view contracts;
- three flagship journeys and one bounded CT-1 supporting journey;
- `EXACT_ORIGINAL` compatibility reads only;
- no paid API, secret, hosted database, external dataset, or runtime network
  dependency; and
- no HTTP or UI implementation before the in-process facade is proven.

## 3. Phase 1 - Deterministic Demo and Query Facade

Phase 1 is deliberately split so contract closure cannot be confused with
scenario or query completion.

### Phase 1A - Public contract boundary

Implemented.

- strict, frozen, unknown-field-rejecting Pydantic contracts for O-V01 through
  O-V11;
- strict success and failure envelopes;
- exact `EXACT_ORIGINAL` enforcement;
- strict money, date, timestamp, hash, and variant handling;
- sorted and unique semantic source references; and
- one immutable O-Q01 through O-Q11 registry with one-to-one view mapping.

Phase 1A creates no HTTP route, UI component, demo mutation, or alternative
read engine.

### Phase 1B - Deterministic demo lifecycle

Implemented.

- implement O-C01 `InitialisePublicDemo`;
- implement O-C02 `RecreatePublicDemo` atomically;
- implement O-C03 `VerifyPublicDemo` as a read-only proof;
- materialise C-001 and CT-1 through ordinary runtime application and
  persistence paths; and
- prove clean-start, recreation, restart, and projection-rebuild semantic
  parity.

The implementation uses product-owned typed scenario descriptors and ordinary
candidate admission, module-command, accounting-application, and SQLite
persistence paths. It does not import the validation corpus or acceptance
replay. O-C02 verifies a complete replacement before atomic promotion, while
O-C03 performs every runtime and rebuild check against disposable copies so
the target workspace remains byte-for-byte unchanged.

Phase 1B also closes one runtime conformance gap exposed by the ordinary CT-1
path: module consumers now resolve exact G-06/G-13 publications admitted as
J-AR13 authoritative records, in addition to publications already present in
the in-memory lifecycle projection. This implements the ratified contract; it
does not add a new architecture decision.

### Phase 1C - In-process public queries

Implemented.

- implement O-Q01 through O-Q11 over one revision-pinned query session;
- construct O-V01 through O-V11 only from their permitted sources;
- preserve exact reporting versions, readiness, evidence state, and directed
  trace edges;
- reject unavailable or unverified claims rather than infer them; and
- prove public-view parity across restart and projection rebuild.

The query boundary accepts only strict version-1 discriminated requests and
opens exactly one runtime query session per response. A product-owned bounded
assembler derives the scenario entry-point index from persisted products and
publications, constructs each O-V contract from its permitted exact sources,
and returns sorted source references for every consumed authority. It neither
imports SQLite nor introduces a second trace, accounting, readiness, or
governance algorithm.

The executable proof covers both reconciliation and exception variants, the
three C-001 flagship journeys, the CT-1 supporting journey, safe typed
failures, exact scenario scoping, purpose-specific readiness, restart parity,
and projection-rebuild parity. HTTP and UI remain absent.

## 4. Later Phases

### Phase 2 - Read-only HTTP adapter

Expose only the finite Artifact O route set. The adapter performs transport
validation and safe error mapping; it has no SQLite, fixture, domain-command,
or finance-inference access.

Phase 2 is complete. A dependency-free ASGI adapter exposes exactly the eleven
Artifact O `GET /api/v1` routes and maps each route one-to-one to its existing
O-Q/O-V contract. Every request supplies an explicit view-contract version,
scenario, and semantic-as-of time; O-Q08 additionally requires exact period,
purpose, and scope. The adapter rejects unknown, missing, duplicate, malformed,
or body-bearing inputs, blocks every public write method, returns only closed
success or failure envelopes, and applies `Cache-Control: no-store` throughout.

The adapter depends only on the public-query executor protocol, strict product
contracts, the finite registries, and canonical JSON serialization. It imports
no persistence implementation, fixture, domain-command, or demo-materialisation
module. Nineteen focused transport tests and the complete 191-test repository
suite pass.

### Mandatory post-Phase-2 cohesion audit

Before UI work, audit exact runtime sourcing, route/query/view one-to-one
coverage, compatibility mode, readiness pairing, evidence wording, reporting
history, read-only enforcement, offline operation, dependency direction, and
the inherited review register.

This audit passed and is recorded in
`docs/roadmap/milestone-3-post-phase2-cohesion-audit.md`.

### Phase 3 - Shared application shell

Build one responsive React shell with the five module lenses and explicit
scope, version, readiness, and evidence context.

Phase 3 is complete. The contained `web/` application now provides one
responsive shell for Overview, Hermes, Atlas, Argus, Aegis, Pythia, and shared
trace navigation. Overview, Atlas reporting-version detail, and the O-J01 trace
are live; later-module links remain visibly unavailable rather than resolving
to invented screens.

The browser calls only the Phase 2 HTTP surface. A local ASGI composition root
initialises or verifies the disposable demo through O-C01/O-C03, opens the
existing SQLite persistence boundary, and supplies the established public query
service to the unchanged HTTP adapter. It creates no alternative data source.
The client performs display formatting only and preserves integer minor units,
exact reporting references, query revision, compatibility mode, evidence state,
and the runtime-supplied directed trace.

The production build exposes exactly three browser routes at this phase:

```text
/
/atlas/reporting/:periodId/:versionRef
/trace/reporting/:reportingVersionRef/:statementField
```

The live local proof resolves O-V02, O-V05, and O-V10 through the frontend proxy;
the O-J01 trace returns the verified GBP 10,000 June v2 value and 42 directed
authority nodes.

### Phase 4 - Broken-quarter journey

Implement Hermes reconciliation, reporting history, Argus exception, Aegis
governance case, and purpose-specific readiness to complete O-J02 without
client-side finance or governance inference.

Phase 4 is complete. The product now exposes all five direct O-J02 views plus
the existing exact June v2 view through one shared six-step journey:

```text
O-V04 reporting history
-> O-V03 Hermes recognition-population gap
-> O-V06 Argus completeness exception
-> O-V07 Aegis governance and remediation chain
-> O-V05 immutable June v2 restatement
-> O-V08 exact purpose-specific readiness
```

The visible proof preserves June v1 at GBP 0 subscription revenue, June v2 at
GBP 10,000, and the server-published GBP 10,000 restatement bridge. It shows 12
expected recognition items, 11 posted items, one submitted-unposted item, one
deferred item, and the exact GBP 10,000 reconciliation gap without client-side
subtraction. The Argus observation remains distinct from Aegis review, finding,
issue, remediation, and verification. `REMEDIATION_VERIFIED` is not presented as
`CLOSED`. Readiness remains bound to `RV-2026-06@v2`, period `2026-06`, purpose
`HIRING-FORECAST`, and scope `NEXUS-GROUP`.

The Phase 4 route audit found and closed one inherited cohesion defect: O-V02
advertised the exact successor issue route `ISSUE-C001@v2`, while O-Q07 admitted
only the initial issue version. O-Q07 now accepts either exact issue version and
returns the same complete, immutable case chain; unrelated issue references
remain rejected.

The complete closure audit is recorded in
`docs/roadmap/milestone-3-post-phase4-cohesion-audit.md`.

### Phase 5 - Decision and correction journeys

Implement the Pythia governed-decision view for O-J03 and the CT-1
correction-integrity view for O-SJ01.

Phase 5 is complete. O-J03 consumes exact `RV-2026-06@v2`,
`READY-C001@v1`, purpose `HIRING-FORECAST`, and scope `NEXUS-GROUP`; presents
the GBP 6,500 monthly deferred-hire effect; and keeps the source-domain
`APPROVED` decision distinct from the returned `UNSUPPORTED` candidate. The
screen explicitly preserves the firewall preventing a Pythia output from
recursively entering the accounting-event posting engine.

O-SJ01 reuses the shared Hermes, Argus, and Aegis routes under the exact CT-1
scenario before terminating at O-V11. It presents J-010 as referenced-only
G-13 state, binds its hash before comparison, preserves separate immutable
J-011 reversal and J-012 replacement journals, displays their server-verified
balance results, corrects `CUST-VEGA` to `CUST-ORION`, and displays the
server-published GBP 0 control-account net movement. The browser performs none
of those accounting or assurance calculations.

The production build now exposes exactly ten browser routes. The complete
closure audit is recorded in
`docs/roadmap/milestone-3-post-phase5-cohesion-audit.md`.

Phase 5 is complete. O-J03 consumes exact `RV-2026-06@v2`,
`READY-C001@v1`, purpose `HIRING-FORECAST`, and scope `NEXUS-GROUP`; presents
the GBP 6,500 monthly deferred-hire effect; and keeps the source-domain
`APPROVED` decision distinct from the returned `UNSUPPORTED` candidate. The
screen explicitly preserves the firewall preventing a Pythia output from
recursively entering the accounting-event posting engine.

O-SJ01 reuses the shared Hermes, Argus, and Aegis routes under the exact CT-1
scenario before terminating at O-V11. It presents J-010 as referenced-only
G-13 state, binds its hash before comparison, preserves separate immutable
J-011 reversal and J-012 replacement journals, displays their server-verified
balance results, corrects `CUST-VEGA` to `CUST-ORION`, and displays the
server-published GBP 0 control-account net movement. The browser performs none
of those accounting or assurance calculations.

The production build now exposes exactly ten browser routes. The complete
closure audit is recorded in
`docs/roadmap/milestone-3-post-phase5-cohesion-audit.md`.

### Phase 6 - Public hardening

Close accessibility, responsive-layout, offline-boundary, deterministic-build,
local startup, and repository walkthrough requirements.

Phase 6 is complete. All ten finite browser routes now pass one shared semantic
shell test covering language, landmarks, skip navigation, busy/live state, and
synthetic-data disclosure. The mobile shell presents all six modules in a
bounded bottom navigation with 48-pixel targets. Normal muted text now meets
WCAG AA contrast against the paper surface, and the stylesheet explicitly
supports reduced motion, increased contrast, and forced-colour operation.

The application publishes a product-specific social preview with host-derived
Open Graph and X metadata. It adds no runtime image, font, model, telemetry,
API-key, external-service, or hosted-data dependency.

`public_product.py serve` starts the verified local API and shell together.
`public_product.py verify` performs two builds, canonicalizes only vinext's
fresh preview/prerender security salts, requires every other output byte to
produce the same application digest, starts a disposable demo, and verifies the
same-origin O-V01 response remains `EXACT_ORIGINAL`. The complete audit is in
`docs/roadmap/milestone-3-post-phase6-cohesion-audit.md`.

No in-app browser was connected during this phase. Manual screenshot,
viewport, screen-reader, and keyboard traversal evidence therefore remains a
named Phase 7 acceptance requirement; Phase 6 does not claim that evidence.

### Phase 7 - Acceptance and final audit

Implemented.

`finance_assurance.product_acceptance` now provides the closed O-A01 through
O-A33 catalogue and deterministic Milestone 3 report. One command runs the
unchanged clean-checkout Milestone 1/2 boundary, all Python product proofs,
TypeScript, ESLint, rendered-product tests, repeatable application builds, local
same-origin startup, and the public compatibility boundary:

```text
uv run --locked python -m finance_assurance.product_acceptance --require-clean
```

Manual evidence is not inferred from static or rendered checks. The strict
`milestone-3-manual-browser-evidence@v1` input is bound to the accepted Git
revision and verifies the hashes of referenced desktop, tablet, and mobile
screenshots. Its review procedure is in
`docs/roadmap/milestone-3-manual-browser-review.md`.

## 5. Current Gate

Phase 5 is complete only when O-J03 preserves exact input and approval/admission
boundaries, O-SJ01 preserves non-authoring and bind-before-compare correction
semantics, every direct journey route renders, and the browser derives no
finance, assurance, governance, readiness, or admission conclusion. That gate
is now closed.

The automated Phase 7 boundary, final cohesion audit, and connected-browser
review are complete. O-A28 and O-A29 are backed by strict revision-bound
evidence rather than inferred from rendered tests. Milestone 3 is ratified only
for the revision whose clean-checkout report returns all 33 criteria as `PASS`.
