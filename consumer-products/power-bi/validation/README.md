# Power BI validation

This directory records semantic-model and report acceptance checks for the
[NexusFinance source project](../NexusFinance/NexusFinance.pbip).

Financial totals on the C2 pages must reconcile to the same snapshot used by
React and the Excel product. The comparison pages declare their additional
inputs and evidence in the report.

## Current Desktop export (2026-11-21)

- Refreshed against the sealed Q-FINANCE-C2@v1 delivery. The seal and all 232
  file checksums passed. Checked eight navigation targets in the PBIR.
- Materialised 56 June management planning rows from the sealed C2 package and
  a versioned prior-year forecast policy. In Desktop, Subscription Revenue
  showed GBP 2,348,784.83 budget, GBP 2,542,060.16 forecast and GBP
  2,288,009.60 management actual. Changing the account to Hosting Cost of
  Revenue showed the cost increase as adverse and the cost decrease as
  favourable. Both movements tied to their respective anchors.
- The C-001/CT-1 H7 suite passed. The Desktop restatement comparator showed
  the original and republished snapshots, GBP 10,000 of additional
  subscription revenue, and GBP 10,000 less deferred revenue. The changes
  linked to the two J-560 lines and republication AE-C001-011.
- All nine packages passed type checking and all 149 visual tests. The 19
  TMDL tables and 15 relationships parsed in TOM. Compared the 15 migrated
  detail and trend query bindings against the previous PBIX.
- The new Financial Performance grid opened the exact June reporting version
  in Desktop. The evidence page displayed the close context, lifecycle event
  references, reconciliations and source digest together.
- Exported `work/R2/NexusFinance.pbix` from Desktop. Verified its archive,
  embedded data model, 15 pages, nine custom visual packages, full-width
  exception register and active cover. SHA-256
  `b8e1b634043796a58b182698ab41ec2119ce6ac53cad7d793cf026f43a70e9f8`.

## Earlier Desktop checks

- The first dashboard pass matched 17 of 17 DAX checks, including cash and
  MRR movements, Group and product ARR, close and readiness counts, and LTM
  revenue. Cash & Capital opened June version evidence and Close Assurance
  opened May version evidence.
- The 13-page cover and objective build rendered in Desktop. TOM parsed 17
  tables and 15 relationships, and seven visual packages passed 144 tests.
