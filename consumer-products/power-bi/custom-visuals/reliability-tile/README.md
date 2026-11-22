# Nexus Reliability Tile - P5 v0.1

Implemented local development visual. Desktop checks cover the June values,
intended-use selection and reporting-version drill-through.

This package renders one governed Revenue, Closing Cash or Ending ARR claim.
`policy.json` pins the three source authority/reliability tuples, readiness
authority mapping, intended purpose and delivery identities. The generated
Power Query adapter joins metric readiness and checks coverage. DAX withholds
the value for unsupported purpose or ambiguous selection. The renderer checks
the contract again and clears old content before every update.

The intended purpose is `CFO_EXECUTIVE_REVIEW`. Selecting `STATUTORY_SIGN_OFF`
in the review page deliberately withholds values because this policy has not
assessed that use. This does not assert that the underlying statements are
unreliable. With no purpose filter, the report explicitly defaults to CFO review.

## Build and stage

From this directory, with Node 24 and the repository Python environment:

```powershell
npm ci
python build-integration.py
npm run typecheck
npm test
npm run package
python stage-package.py
```

`build-integration.py` deterministically generates capabilities, visual metadata,
two TMDL tables, two relationships and the Governed KPI Review page. It updates
only its owned integration files plus the model/page registries. It does not
read or change the sealed delivery. The semantic adapter reads C2 at refresh.

`stage-package.py` installs the compiled private visual into the source PBIP's
ignored `CustomVisuals/` directory, registers it in `report.json` and copies the
project to `consumer-products/power-bi/work/NexusFinance-P5-QA`. It sets the QA
copy's C2Root to this repository's delivery. Rerunning staging replaces the QA
source files; save separate copies of any manual QA edits before doing so.

Compiled artifacts are generated, not committed. Run packaging and staging
after a clean checkout before opening the custom-visual page. The source PBIP
retains the portable C2Root placeholder. Existing native pages remain available.

## Local renderer acceptance

```powershell
node_modules/.bin/esbuild test/preview.ts --bundle --outfile=.tmp/preview.js
Copy-Item test/preview.html .tmp/preview.html
node test/browser-acceptance.cjs
```

The browser check reuses the repository web workspace's installed Playwright.
The preview uses the real renderer with mocked Power BI host services and
labelled failure fixtures. It is not proof of Desktop refresh, DAX evaluation,
host selection or drill-through. Screenshot outputs are in `.tmp/`.

## Validation record - 2026-11-09

- TypeScript compilation and `.pbiviz` packaging.
- 18 contract/DOM tests covering eligibility, missing assessment, unsupported
  purpose, wrong identity/authority, unsafe numbers, duplicate and truncated
  data, conflicting results and stale-value removal.
- Browser renderer checks for three exact values, three withholding states,
  keyboard evidence expansion, resizing and no browser exceptions.
- All 198 source metric-period rows match the pinned authority, reliability,
  version and readiness coverage contracts.
- Microsoft's capabilities schema and all new PBIR files validate.
- Microsoft's TOM deserializes the nine-table TMDL model successfully.
- C2 physical inventory, detached seal and all 232 file checksums match.

The complete delivery CLI reached its workbook-verification step but could not
finish because `FAP_ARTIFACT_NODE` and `FAP_ARTIFACT_RUNTIME_DIR` were not
configured. The physical checks above were completed separately; no new full
workbook-verification pass is claimed.

Expected June values are Revenue GBP 2,288,009.65, Closing Cash GBP 3,082,301.85
and Ending ARR GBP 26,800,564.68.

On 2026-11-15 the full review PBIP refreshed in Desktop. Governed KPI Review
displayed the three June amounts. Selecting Statutory sign-off withheld all
three with the intended-use reason, and clearing it restored the amounts.
The Revenue tile opened `RV-NEXUS-GROUP-2026-06@v1` in Reporting Version
Evidence. The page defaults to June through a visible page filter. The
multi-period and missing-assessment cases are covered by local contract tests.

## Boundaries

This first version has fixed finance styling and an English interface. Formatting
pane controls, localization, Service testing and export acceptance remain future
work. Interactions respect the host capability flag; partial highlighting is
deliberately disabled. Evidence references are relation/row pointers; no evidence
digest is invented for these source marts.

The visual declares no privileges and makes no network calls. It is not
certified. The pinned build-tool dependency audit reports 10 moderate findings
in the development tooling; resolve those before a certification submission.
The local package uses explicitly non-deliverable author contact metadata and a
placeholder support URL; replace these before distribution.

C-001 and CT-1 named withholding fixtures check that a blocked model state
cannot expose a numeric value. They do not claim to execute the full accounting
scenarios. The renderer cannot post, reopen, republish or promote governance
objects. Eligibility is a usage policy, not an access-control substitute.
