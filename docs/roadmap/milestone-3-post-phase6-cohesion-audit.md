# Milestone 3 Post-Phase-6 Cohesion Audit

Status: Passed 2026-08-11; manual browser evidence carried to Phase 7

## 1. Purpose

This audit tests whether public hardening changed only the presentation,
packaging, and verification surface around the ratified Artifact O product. It
does not add finance semantics, authoritative data, a new read engine, a public
write path, an external service, or a hosted operating claim.

## 2. Gate Result

PASS for Phase 6 implementation. The finite product remains one shell over the
same eleven O-Q/O-V contracts and ordinary runtime authority. Accessibility,
responsive layout, offline operation, deterministic application build, local
startup, social presentation, and repository walkthrough requirements now have
executable evidence.

Manual browser visual, keyboard, and assistive-technology evidence was not
available because no browser surface was connected. That evidence is an
explicit Phase 7 acceptance prerequisite and is not implied by this pass.

## 3. Findings Closed

| Finding | Resolution |
|---|---|
| Six modules in five mobile columns | The bottom navigation now uses six bounded columns, horizontal safety overflow, and 48-by-48-pixel minimum targets. |
| Muted normal text at 4.28:1 | The shared muted colour is now `#5b6965`, producing 5.09:1 against the primary paper surface and 5.50:1 against bright panels. |
| Skip target not programmatically focusable | `main` is now a `tabIndex=-1` fragment target and exposes its loading state through `aria-busy`. |
| Runtime verification changes silently | The verification chip is a polite live status region. |
| Contrast modes incomplete | Increased-contrast and forced-colour rules complement the existing reduced-motion rule. |
| No one-command product startup | `public_product.py serve` owns both local process lifecycles and full Windows/POSIX process-tree cleanup. |
| Build identity changed randomly | Build and deployment identities are derived from versioned deployable inputs. |
| Security entropy prevented byte comparison | The verifier shape-checks and canonicalizes only the generated preview ID and two prerender-secret manifest values; every other output byte remains in the digest. |
| No portfolio social representation | One project-specific Open Graph image and host-derived metadata now represent the real product language and visual system. |

## 4. Cohesion Matrix

| Area | Result | Evidence |
|---|---|---|
| Route closure | PASS | All ten finite browser routes server-render through the same shell and semantic landmark contract. |
| Public API closure | PASS | The startup verifier reaches O-V01 through the browser-facing same-origin proxy and receives `EXACT_ORIGINAL`. |
| Read-only boundary | PASS | No route, launcher, test, or UI change adds a public mutation or direct persistence dependency. |
| Browser authority | PASS | The client still formats and navigates only; no finance, assurance, governance, readiness, or admission algorithm moved into React. |
| Accessibility source contract | PASS | Language, skip navigation, labelled primary navigation, main busy state, live verification status, visible focus, reduced motion, increased contrast, and forced-colour behavior are asserted. |
| Responsive shell | PASS | The six-module mobile navigation and minimum touch targets are executable stylesheet assertions. |
| Offline/cost boundary | PASS | Runtime source contains no absolute external fetch, model/API key, telemetry key, hosted database, or paid-service dependency. Runtime dependencies remain React and React DOM only. |
| Deterministic application build | PASS | Two builds produced digest `cb4feaf05e6be149941b556302e5a3708eee5ffb9427653d16ae1301efa2c6df` after exact generated-security-salt normalization. |
| Security treatment | PASS | Random preview and prerender secrets remain random; their shapes and exact allowlisted locations are validated rather than weakened or broadly excluded. |
| Local startup | PASS | A disposable database, ordinary ASGI composition root, vinext shell, same-origin proxy, and exact O-V01 contract started and stopped under one command. |
| Social metadata | PASS | The page derives the absolute image URL from the incoming host and publishes product-specific Open Graph/X metadata without hard-coding a deployment domain. |
| Hosting scope | PASS | No deployment or public operational claim was introduced. Hosting remains deferred. |

## 5. Automated Verification

Executed from the repository environment on 2026-08-11:

```text
npm run typecheck
Passed

npm run lint
Passed

npm test
9 passed; ten application routes built

ruff check --no-cache src tests public_product.py
Passed

python public_product.py verify --api-port 8014 --web-port 3014
Deterministic application build:
cb4feaf05e6be149941b556302e5a3708eee5ffb9427653d16ae1301efa2c6df
Local startup: verified
Same-origin O-V01 boundary: EXACT_ORIGINAL
```

The unchanged Milestone 1 and Milestone 2 acceptance boundaries are rerun in
Phase 7. Phase 6 changed no runtime domain or persistence implementation.

## 6. Manual Acceptance Register

The following are blocking Phase 7 evidence, not silent residuals:

1. inspect overview, O-J01, O-J02, O-J03, and O-SJ01 at desktop, tablet, and
   320-pixel mobile widths;
2. traverse every journey using only keyboard input and confirm visible focus;
3. exercise skip navigation and bottom navigation with a browser accessibility
   tree;
4. confirm no horizontal page overflow outside the explicitly scrollable
   context, statement, and journey regions;
5. capture representative portfolio screenshots; and
6. record screen-reader names/order for the shared shell and one dense journey.

## 7. Next Gate

Phase 7 may begin. It must rerun the unchanged architecture and runtime
acceptance boundaries, complete the manual browser register above, verify
restart/rebuild parity and offline operation, and issue the final
product/architecture cohesion audit before any hosting decision.
