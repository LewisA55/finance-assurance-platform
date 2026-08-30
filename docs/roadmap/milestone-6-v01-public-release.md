# Milestone 6 - v0.1 Public Release Gate

## Outcome

Release `v0.1 - Governed Finance Platform + React Intelligence Product` as a
coherent, reproducible portfolio repository. Excel and Power BI remain later
consumer products over the same governed analytical handoff.

## Included

- synthetic source events, posting and accounting lifecycle services;
- governed Bronze, typed Silver and Gold finance models;
- assurance, remediation and planning boundaries;
- local analytical handoff and authenticated React runtime data;
- browser-local DuckDB-Wasm React intelligence product;
- public architecture, artifact and reproducibility documentation;
- automated Python, React, dependency and release-hygiene gates.

## Excluded

- generated warehouses and full analytical delivery packages;
- Excel and Power BI binaries or finished consumer models;
- local screenshots, cover experiments, consumer-product workspaces and working
  notes;
- credentials, machine-specific paths and hosted authority claims.

## Ratification Evidence

The milestone can be tagged only when all of the following pass from the
candidate source tree:

1. `python -m ruff check .`
2. `python -m pytest -q`
3. `python scripts/check_public_release.py`
4. `npm run lint`
5. `npm run typecheck`
6. `npm run test:finance`
7. `npm run audit:dependencies`
8. `npm test`

The local tag does not authorise a push, hosted deployment or public release.
Those remain separate user-controlled actions.
