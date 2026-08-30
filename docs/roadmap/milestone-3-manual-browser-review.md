# Milestone 3 Manual Browser Review

Artifact O requires recorded manual browser evidence in addition to automated
accessibility and responsive checks. The acceptance runner reads
`build/milestone-3-manual-browser-evidence.json` by default. This generated
evidence is revision-bound and is not replaced by a prose assertion.

The review covers overview, O-J01, O-J02, O-J03, and O-SJ01 in that order. It
uses desktop, tablet, and 320-pixel mobile viewports and records:

- complete keyboard traversal and visible focus;
- skip-link and bottom-navigation operation;
- screen-reader names, landmarks, and reading order;
- absence of horizontal overflow;
- preservation of exact version, readiness, evidence, and material-value
  context; and
- relative screenshot references and verified SHA-256 hashes for all three
  viewport classes.

The JSON contract is
`milestone-3-manual-browser-evidence@v1`. The executable schema lives in
`finance_assurance.product_acceptance.manual`. Evidence is accepted only when
its `repository_revision` equals the revision under acceptance.

Until this evidence exists, O-A28 and O-A29 and therefore Milestone 3 remain
`BLOCKED`; they are never inferred from automated checks.

## Executed review

The final review was executed on 2026-08-12 in the connected in-app browser
against the ordinary local API and web composition. It covered nine finite
routes across desktop (1440x900), tablet (768x1024), and mobile (320x800): 27
route/viewport combinations in total.

The review confirmed one main landmark, one product heading, named navigation,
ordered journey headings, explicit synthetic-data disclosure, runtime-verified
context, exact governed references, and no error boundary or page-level
horizontal overflow. The skip target and global visible-focus treatment remain
part of the executable shell contract; native anchors preserve ordinary
keyboard navigation without a client navigation runtime.

Four defects were corrected before evidence generation:

- encoded `@` subjects are decoded at the O-J03 and O-SJ01 route boundaries;
- the framework link shim was removed from the finite read-only navigation;
- tablet/mobile flow, bottom-navigation, and long trace identifiers no longer
  widen the page; and
- the exact governed decision reference is visible in O-J03.

The generated evidence JSON and its three SHA-256-bound screenshots live under
`build/`; they are deliberately not versioned because acceptance binds them to
the exact repository revision under review.

The clean-checkout acceptance run validates the evidence, its screenshot
hashes, and the repository revision before reporting O-A28 and O-A29 as `PASS`.

## Executed review

The final review was executed on 2026-08-12 in the connected in-app browser
against the ordinary local API and web composition. It covered nine finite
routes across desktop (1440x900), tablet (768x1024), and mobile (320x800): 27
route/viewport combinations in total.

The review confirmed one main landmark, one product heading, named navigation,
ordered journey headings, explicit synthetic-data disclosure, runtime-verified
context, exact governed references, and no error boundary or page-level
horizontal overflow. The skip target and global visible-focus treatment remain
part of the executable shell contract; native anchors preserve ordinary
keyboard navigation without a client navigation runtime.

Four defects were corrected before evidence was accepted:

- encoded `@` subjects are decoded at the O-J03 and O-SJ01 route boundaries;
- the framework link shim was removed from the finite read-only navigation;
- tablet/mobile flow, bottom-navigation, and long trace identifiers no longer
  widen the page; and
- the exact governed decision reference is visible in O-J03.

The generated evidence JSON and its three SHA-256-bound screenshots live under
`build/`; they are deliberately not versioned because acceptance binds them to
the exact repository revision under review.
