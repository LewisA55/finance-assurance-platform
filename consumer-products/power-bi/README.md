# Power BI Product Workspace

## Current report

NexusFinance is the Power BI source for the v0.3 product. It has 15 report
pages, a 19-table TMDL model and nine custom visual packages. It uses the same
sealed C2 delivery as Excel and React, with separately identified forecast
and accounting-replay inputs on the comparison pages.

- [Screenshot gallery](../../docs/public-release/power-bi/README.md) shows the live report and selected interactions.
- [NexusFinance.pbip](NexusFinance/NexusFinance.pbip) is the project to edit.
  Git tracks the PBIR report definition and TMDL semantic model beside it.
- `work/R2/NexusFinance.pbix` is the current local Desktop export with data
  already imported. The [validation record](validation/README.md) records its
  checksum and acceptance results.

## Open and refresh the source project

1. Verify the published `Q-FINANCE-C2@v1` delivery against the expected
   digest `sha256:7538132e08ea2b7e8c20f339db10e6c138cd2a08c71c4708c47c378d7c1b0141`.
   The repository's `finance-assurance-finance-delivery verify` command checks
   the physical seal and the upstream C1 and A24 packages.
2. After a clean checkout, build and stage the nine [custom visual
   packages](custom-visuals/README.md).
3. Open the PBIP in Power BI Desktop. Under **Transform data** then
   **Edit parameters**, set `C2Root` to the local verified delivery directory.
   The repository's usual build location is
   `build/finance-delivery/Q-FINANCE-C2-V1`.
4. Apply the change and refresh. The model imports its C2 tables from
   `powerbi/parquet/` and checks the delivery reference, publication status
   and detached digest label. The physical checksum check is step 1.

## Financial Performance and evidence

Financial Performance shows Nexus Group GBP statutory actuals from July 2025
through June 2026. Select a reporting-version link in the monthly grid and
choose **Drill through** then **Reporting Version Evidence**. In Desktop edit
mode, Ctrl+click **Back** to return to the source page.

The report cards abbreviate the amounts below in millions. Hover over a card
for the full amount.

| Measure | Expected GBP |
| --- | ---: |
| LTM revenue | 27,649,595.69 |
| June revenue | 2,288,009.65 |
| June EBITDA | (1,773,205.99) |
| June closing cash | 3,082,301.85 |

The June row opens `RV-NEXUS-GROUP-2026-06@v1` and shows the
hard-close and publication event references, five reconciliation statuses,
statutory-actuals reliability and source digest. C-001's original and
republished versions are available separately in Restatement Comparator.

## Cash, SaaS and close dashboards

| Page | Questions answered | C2 reconciliation |
| --- | --- | --- |
| Cash & Capital | What changed cash in June, and what debt and liquidity remained at the close? | Opening cash GBP 5,359,480.52 plus net movements of GBP (2,277,178.67) equals closing cash GBP 3,082,301.85. Gross debt is GBP 4,987,289.04, net debt is GBP 1,904,987.19, and available liquidity is GBP 33,582,301.85. |
| SaaS Performance | What were the June recurring revenue, retention, and product movements? | Group ending ARR GBP 26,800,564.68, ending MRR GBP 2,233,380.39, 957 active customers, and 99.14% NRR. |
| Close Assurance | Which versions were closed and published, and what did the C1 validators report? | The trailing year contains 12 hard-closed and published Group versions. The independent C1 readiness snapshot contains 15 passes and zero non-passes. |

Cash and debt balances are period-end snapshots. Cash flow movements add
across months, and the June cash bridge isolates the June reporting version.
SaaS ARR, customer count, and NRR use the published Group KPIs. The product
table and signed MRR bridge use the detailed SaaS movement mart. Group
customer counts and retention stay at their published grain.

The Cash & Capital and Close Assurance version tables use the same
reporting-version drill-through as Financial Performance. C1 readiness
controls retain their delivery-wide scope, independent of the month and
reporting version filters.

## Navigation and comparison pages

The report opens on the Nexus cover. **View objective** introduces the report
and links to the statements, comparisons, controls and lineage. **Open report** goes
directly to Financial Performance. The front pages use the checked-in artwork
and native Power BI navigation. `showcase/build-showcase.py` regenerates their
content from the source project.

The source project includes Statutory Statements, Rollforward Assurance,
Governed KPI Review, Close Governance, Assurance Controls and Dataset Lineage.
Financial Performance, Cash & Capital, SaaS Performance and Close Assurance
use Nexus metric cards, detail grids and trends. Cash & Capital and SaaS
Performance each include an asserted June rollforward. Reporting Version
Evidence is a hidden drill-through page.

Planning Variance compares budget, a synthetic May forecast vintage and
management actuals at department and account grain. Restatement Comparator
shows the original and republished C-001 amounts and their adjustment
evidence. The [comparison implementation](custom-visuals/comparison/README.md)
documents the source and reproducible adapter for each page.

## Source and local copies

Keep `NexusFinance/` as the editable project and `work/R2/` as the current
local review copy. Earlier exports and QA projects under `work/` are optional
local history. Staging a visual can recreate its QA project. Close any copy
in Power BI Desktop before removing it. Keep the verified C2 package for
future refreshes. Git ignores `work/`, `exports/` and Desktop `.pbi/` caches.

For a tagged release, include the exact C2 manifest reference and the
reconciliation evidence with the reviewed artifact.
