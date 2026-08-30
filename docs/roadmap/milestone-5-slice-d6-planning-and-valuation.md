# Milestone 5 Slice D6 - Governed Planning and Valuation

Status: Implementation authorised on 2026-08-26

## 0. Objective

Slice D6 completes the first React finance-product buildout with a governed
`/planning-valuation` experience. It does not execute forecast or valuation
formulae in React. It first creates a sealed `PYTHIA-D6@v1` result package over
the exact June 2026 Atlas snapshot and then exposes those published results to
the browser-local DuckDB-Wasm query layer.

D6 answers six management questions:

1. What do the approved Base and draft Bull/Bear operating inputs imply?
2. Do the forecast income statement, balance sheet and cash flow reconcile?
3. When is the committed revolving facility exhausted?
4. What additional funding is required after that point?
5. Does terminal free cash flow support a perpetuity-growth DCF?
6. Which exact actuals snapshot, assumptions, model run and controls produced
   each result?

## 1. Pythia execution authority

`PYTHIA-D6@v1` consumes the sealed `Q-FINANCE-C2@v1` delivery digest
`sha256:47ac28ea7cd7880815cb03f875c31bf064d7101e5574db48266a949fccfc8366`.
It binds all scenarios to `RV-NEXUS-GROUP-2026-06@v1`, preserves Atlas actuals
without mutation, and executes 120 forecast months for each of Base, Bull and
Bear.

The result package contains:

- three governed scenario rows;
- 360 integrated monthly forecast rows;
- three scenario valuation-readiness rows;
- 75 WACC and terminal-growth sensitivity states;
- ten validator-produced execution controls;
- versioned assumptions and source-to-result lineage;
- CSV and Parquet physical results; and
- a checksum inventory and detached package digest.

The published Pythia digest is
`sha256:ddb713a3d22090ffa80c495b8d37fc19a4e4bfb78f41ee2075f0f45169fbca32`.

## 2. Approval and reliability boundary

Base retains its Atlas `APPROVED` and locked status and is published as an
`APPROVED_FORECAST_RESULT`. Bull and Bear retain their `DRAFT` status and are
published as `DRAFT_SCENARIO_RESULT`. Execution and sealing make a result
reproducible; they do not approve draft assumptions.

Pythia results are not statutory actuals. Each row carries the exact actuals
reporting version, assumption-set reference, model-run reference, source data
digest, finance-delivery digest, value authority and purpose-specific
reliability state.

## 3. Integrated model boundary

The bounded model derives monthly:

- revenue, gross profit, EBITDA, EBIT, tax and net income;
- accounts receivable, accounts payable, deferred revenue, prepayments and
  accruals;
- capital expenditure and depreciation;
- term debt amortisation, revolver use, interest and available liquidity;
- operating, investing and financing cash flow;
- cash, net debt, assets, liabilities and equity; and
- unlevered free cash flow.

The cash-flow rollforward and balance-sheet equation reconcile to zero for all
360 scenario-months. The revolver is limited to the committed June 2026
facility. Once exhausted, Pythia reports the unmet funding requirement instead
of creating an unlimited debt or minimum-cash plug.

## 4. Economic result

The existing Atlas planning inputs are economically loss-making in every
scenario. For Base, the first 60 months produce GBP 198.0m of revenue, negative
GBP 139.8m EBITDA and negative GBP 144.3m unlevered free cash flow. The first
unfunded liquidity gap occurs in October 2027 and the ten-year peak additional
funding requirement is GBP 368.0m.

Bull scales revenue and costs more aggressively and breaches earlier. Bear
reduces both and breaches later. None reaches positive terminal-year free cash
flow. Pythia therefore publishes the explicit-period present value for
traceability but withholds terminal value, enterprise-value completion and the
DCF sensitivity outputs that depend on a positive terminal cash flow.

This is a governed decision result, not a model failure. A supportable DCF now
requires an authorised management-action scenario, recapitalisation or revised
operating plan rather than an arithmetic workaround.

## 5. React consumer boundary

The React route provides:

- Base, Bull and Bear scenario switching with visible approval status;
- five-year revenue, EBITDA, free-cash-flow and funding indicators;
- a ten-year integrated forecast trend;
- scenario comparison and funding-gap timing;
- an annual three-statement bridge and horizon-end balance proof;
- DCF precondition and sensitivity guardrails; and
- Pythia validator, lineage and package-authority evidence.

React performs only bounded grouping, display formatting and chart projection
over published result rows. It contains no forecast, financing, tax, DCF or
terminal-value engine.

## 6. Acceptance

- the Pythia package independently verifies against its C2 input seal;
- all 360 forecasts balance and cash-reconcile;
- Base approval and Bull/Bear draft states remain distinct;
- terminal value is absent wherever terminal free cash flow is negative;
- the D6 runtime contains the five exact Pythia result tables;
- the route remains browser-local and read-only;
- 38 focused finance-product tests pass;
- 15 shared rendering and hardening tests pass, including the explicit D6
  server-render assertion; and
- typecheck, lint and production build complete with no new lint warning.
