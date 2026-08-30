# Milestone 3 Post-Phase-2 Cohesion Audit

Status: Passed 2026-08-10

## 1. Purpose

This audit is the mandatory gate between the finite public HTTP boundary and
visible UI expansion. It tests whether Phase 2 preserved Artifact O's authority,
reliability, evidence, history, cost, and dependency boundaries while exposing
O-Q01 through O-Q11 over HTTP.

The audit does not assess visual design, accessibility, browser routing, or
deployment topology. Those remain later Milestone 3 work.

## 2. Gate Result

PASS. No blocking authority, inference, or contract gap remains at the Phase 2
boundary.

The implementation adds one ASGI adapter, one immutable eleven-route registry,
and transport tests. It does not create a second read engine, persistence path,
finance calculation, generic record endpoint, or mutable public workflow.

## 3. Mandatory Audit Matrix

| Area | Result | Evidence |
|---|---|---|
| Exact runtime sourcing | PASS | Every accepted route constructs one strict `PublicQuery` and calls one `PublicQueryExecutor.execute`. `PublicQueryService` remains the only implementation and opens one revision-pinned runtime query session. |
| Route/query/view one-to-one coverage | PASS | `PUBLIC_HTTP_ROUTES` contains eleven unique route templates, all and only O-Q01 through O-Q11, and eleven unique O-V outputs. Import-time guards and focused tests fail on divergence. |
| Artifact N compatibility mode | PASS | All eleven successful HTTP responses declare `EXACT_ORIGINAL`. Existing strict public-contract tests reject `TYPED_TARGET`; the adapter cannot inject or adapt compatibility reads. |
| Purpose-specific readiness pairing | PASS | O-Q08 requires exact `reporting_version_ref`, `period_id`, `purpose_ref`, and `scope_ref`; missing values fail transport validation. O-Q09 continues to expose the exact readiness reference bound to the governed decision. |
| Evidence-verification wording | PASS | The adapter serializes the already validated O-V bodies without relabelling. `CONTENT_BYTES_VERIFIED` and `DECLARED_HASH_ONLY` remain distinct product-contract values, and unavailable or unverified trace results remain typed failures. |
| As-was/as-restated history | PASS | O-Q04 and O-Q05 remain exact-reference reads. June v1 and v2 are simultaneously retrievable, and the GBP 10,000 restatement bridge is supplied by the in-process assembler rather than calculated in transport. |
| Public read-only enforcement | PASS | The route registry contains `GET` semantics only. POST, PUT, PATCH, DELETE, and HEAD receive 405 with `Allow: GET`; demo lifecycle operations remain absent; GET bodies are rejected. |
| Offline and zero-paid-service operation | PASS | The ASGI adapter uses the Python standard library plus already locked project dependencies. It performs no runtime network call and requires no API key, account, hosted service, or new package. |
| Dependency direction | PASS | HTTP depends on the product query protocol, product contracts and registries, and canonical serialization. An AST boundary test rejects SQLite, fixture, validation, command, and demo-materialisation imports. |
| Inherited review register | PASS | M3-IR01 through M3-IR03 remain closed in `milestone-3-inherited-review-register.md`; Phase 2 introduces no contradictory evidence. |

## 4. Transport Contract Findings

The following rules are executable rather than conventional:

1. every route requires `view_contract_version=1`, one closed scenario reference,
   and the sealed demo semantic-as-of timestamp;
2. unknown, missing, duplicate, malformed, or surplus query parameters fail as
   `UNSUPPORTED_CONTRACT` without opening a query session;
3. O-Q08 period, purpose, and scope are explicit inputs and are never inferred;
4. path references remain exact and trailing-slash alternatives do not silently
   create a second route;
5. every success and failure is compact canonical JSON with
   `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`;
6. application failures map deterministically to HTTP status without adding,
   removing, or rewriting semantic fields; and
7. an unexpected executor/startup failure becomes the closed
   `DEMO_NOT_INITIALISED` 503 state and never exposes exception text.

No generic `/records`, `/query`, SQL, fixture, or lifecycle endpoint exists.

## 5. Verification Record

Executed from the repository environment on 2026-08-10:

```text
ruff check --no-cache src tests
All checks passed

pytest tests/product/test_http_adapter.py -q
19 passed

pytest -q
191 passed
```

The full suite includes the unchanged Milestone 1 H0-H7 and Milestone 2
acceptance proofs alongside the Artifact O demo, contract, query, and transport
checks.

## 6. Residual Scope

The following are intentionally not Phase 2 claims:

- a long-running development or production ASGI server;
- browser application assets or client-side routing;
- CORS or cross-origin deployment policy;
- rate limiting, hosted observability, or internet-facing operations; and
- visual, responsive, keyboard, or WCAG review.

These omissions do not weaken the HTTP application contract. They prevent
deployment and UI concerns from entering the semantic adapter prematurely.

## 7. Next Gate

Phase 3 may begin. It must build the shared application shell and O-J01 trace
journey over this exact HTTP surface, without client-side finance inference or
new product queries. Any required semantic field absent from O-V01 through
O-V11 is a contract finding, not permission for the UI to query runtime storage
directly.
