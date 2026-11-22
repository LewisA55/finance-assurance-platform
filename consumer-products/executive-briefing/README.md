# Nexus Group executive deck

A 12-slide, 16:9 deck for the June 2026 close. Each slide carries one message
as its title, one chart and a few callouts. Every figure links to the evidence
trace in the appendix (slides 11 and 12).

| Slide | Message |
|---|---|
| 1 | Cover |
| 2 | At a glance: cash cover, headline figures and the decision |
| 3 | Liquidity: cash against undrawn facility capacity |
| 4 | Facility: drawn and undrawn balances at each quarter-end since 2021 |
| 5 | Cash movement: the May to June net outflow bridge |
| 6 | Profitability: twelve months of revenue and EBITDA |
| 7 | Recurring revenue: ARR and monthly MRR churn |
| 8 | Working capital: overdue receivables against closing cash |
| 9 | Close and assurance: control rules, automated checks and their scope |
| 10 | Decision: owners, proposed dates and the timeline to quarter-end |
| 11–12 | Evidence trace, scope notes and delivery identity |

## Build

From the repository root, with the project Python environment active and the
verified C2 delivery at `build/finance-delivery/Q-FINANCE-C2-V1`:

~~~powershell
python consumer-products/executive-briefing/build.py
node consumer-products/executive-briefing/print.cjs
~~~

`build.py` verifies the C2 seal, binds to the published June Group version and
renders `deck.html` with `deck.css`. Charts are static SVG drawn by `charts.py`,
so the deck needs no network or JavaScript. Every sentence that characterises a
figure ("flat on May", "twice closing cash", "the highest of the twelve
months") is asserted, so the build fails rather than printing a claim the data
no longer supports. Cash cover uses observed outflow rates, repayments
included; it is a sensitivity, not a forecast. Decision dates are proposals,
set in working days after the close.

`print.cjs` checks that there are 12 slides, that each is exactly 1280 × 720
and that nothing spills past a slide's footer or edge, then prints the PDF. It
uses the workspace's Playwright installation; with Chrome or Edge installed,
set `NEXUS_PRINT_BROWSER` to the executable path. Both outputs go under
`exports/output/pdf/` beside this README.
