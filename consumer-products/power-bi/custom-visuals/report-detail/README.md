# Nexus Report Detail

The visual renders a detail grid or a financial trend from the page's existing
Power BI query. The grid formats governed amounts and status fields and opens
the Power BI evidence menu from the original row identity. The trend retains
the original measures, plots missing observations as gaps and uses the month
identity for selection. Both views declare zero Power BI privileges.

| Data role | Binding |
| --- | --- |
| `fields` | One to twelve original table fields in report order, including columns and measures. |
| `period` | One month identifier for the trend. |
| `series` | One to three measures at the same period grain and unit. |

Run `python build-integration.py` after generating the native pages and
Rollforward Assurance. It upgrades query bindings in place and reuses the
asserted cash and MRR schedules on their dashboard pages. Run `npm ci`,
`npm run typecheck`, `npm test`, `npm run package`, and
`python stage-package.py` to install the private package in the PBIP.
