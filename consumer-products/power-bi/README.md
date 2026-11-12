# Power BI Product Workspace

## Intended product

The v0.3 Power BI product will demonstrate a governed semantic model and a
small number of purposeful report experiences over the same C2 delivery
package consumed by Excel and React.

## Milestone 1

[NexusFinance.pbip](NexusFinance/NexusFinance.pbip) opens the TMDL semantic
model and enhanced PBIR report. Financial Performance shows Nexus Group GBP
statutory actuals from July 2025 through June 2026. Right-click a reporting
version in the monthly table and select **Drill through** then
**Reporting Version Evidence**. In Desktop edit mode, Ctrl+click **Back** to
return to Financial Performance.

1. Verify the published `Q-FINANCE-C2@v1` delivery against the expected
   digest `sha256:7538132e08ea2b7e8c20f339db10e6c138cd2a08c71c4708c47c378d7c1b0141`.
   The repository's `finance-assurance-finance-delivery verify` command checks
   the physical seal and the upstream C1 and A24 packages.
2. Open the PBIP in Power BI Desktop. Under **Transform data** then
   **Edit parameters**, set `C2Root` to the local verified delivery directory.
   The repository's usual build location is
   `build/finance-delivery/Q-FINANCE-C2-V1`.
3. Apply the change and refresh. The model imports its tables from
   `powerbi/parquet/` and checks the delivery reference, publication status
   and detached digest label. The physical checksum check is step 1.

Desktop refresh and DAX Query View reconciled the four measures below. The
report cards abbreviate the values in millions.

| Measure | Expected GBP |
| --- | ---: |
| LTM revenue | 27,649,595.69 |
| June revenue | 2,288,009.65 |
| June EBITDA | (1,773,205.99) |
| June closing cash | 3,082,301.85 |

The June row drilled into `RV-NEXUS-GROUP-2026-06@v1` and showed the
hard-close and publication event references, five reconciliation statuses,
statutory-actuals reliability and source digest. Ctrl+clicking **Back** in
Desktop returned to Financial Performance. The drill-through uses the full
version reference. For C-001, a later published restatement would
retain its own version and require a separately governed delivery. For CT-1,
an open-period reversal or replacement stays outside the hard-closed
actuals in this delivery.

## Native page buildout

The three additional pages use the same pinned delivery and the native
Power BI canvas. Financial Performance remains the landing page.

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

Desktop refreshed all seven tables and rendered the three new pages. A
live DAX query matched 17 of 17 checks, including the cash and MRR bridge
deltas, Group and product ARR, the close and readiness counts, and the
original LTM revenue. Cash & Capital opened June version evidence and
Close Assurance opened May version evidence.

## Working boundary

P5 development adds a **Governed KPI Review** page with Revenue, Closing Cash
and Ending ARR. See the [implementation and acceptance record](custom-visuals/reliability-tile/README.md)
for package generation, purpose gating and the isolated `work/NexusFinance-P5-QA`
copy. Contract/browser/schema checks pass; Desktop acceptance of this new page
is pending. The custom package must be built and staged after a clean checkout.

- Keep model design, field roles, measure specifications, security design,
  TMDL/PBIP text source and validation specifications in this tracked
  directory when they are authored.
- Keep active `.pbix` files, imported delivery copies, desktop cache and
  rendered exports in `work/` or `exports/`; both are ignored.
- Publish the reviewed PBIX/PBIP as a tagged release asset with the exact C2
  manifest reference and reconciliation evidence.

The current `work/` directory is for private authoring only. It is deliberately
outside the v0.1 source boundary. The active Desktop file is kept locally as
`work/finance-assurance-platform.pbix` so future authoring has one stable home.

The reviewable PBIP text source lives under `NexusFinance/`. Power BI Desktop
`.pbi/` cache directories remain ignored at any depth.
