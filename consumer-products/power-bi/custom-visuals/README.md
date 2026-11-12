# Power BI custom visuals

This directory owns the design, source and tests for purposeful Power BI
custom visuals over governed finance and assurance data.

[Custom visual specification v0.1](specification-v0.1.md) proposes eight reusable
primitives, their data roles and Power BI capability mappings, source adapters,
evidence boundaries and acceptance criteria. It is a design proposal, not an
implemented or certified visual library.

[P5 implementation](reliability-tile/README.md) now contains the first local
development package, semantic adapter and Governed KPI Review page. Contract,
renderer and schema validation are recorded there. Desktop acceptance remains
pending; the design document continues to describe the wider proposed library.

The recommended first delivery is the Reliability-Gated KPI Tile (P5), followed
by the Rollforward Bridge (P2) and Statement Matrix (P1). A shared assertion
contract supports the later Reconciliation Tie-Out Panel (P3). The specification
records the additional governed data needed for the full Two-Stage Variance
Bridge (P7) and Restatement Comparator (P8).

The existing native PBIP remains the accepted baseline. Visual implementation,
new semantic adapters and report replacement follow separately after design
review. Internal HTML/CSS/SVG rendering is in scope; dataset-supplied HTML and
external runtime services are not.

Compiled packages and local development outputs must remain outside Git or be
published as deliberate release assets.
