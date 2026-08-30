# Slice A2 - Statutory Finance Source Substrate

Status: Complete and ratified through A2.4

## 0. Purpose

Slice A2 closes the statutory-finance weakness inherited from original Atlas
before Silver or Gold modelling begins. It adds transaction-generated banking,
asset, financing, lease, tax, equity, accrual, prepayment, intercompany,
consolidation, close, trial-balance, and three-statement source depth across the
same 66-month actual history established by Slice A1.

This is not a presentation enhancement. A2 changes the evidence available to
the later analytical product so balance-sheet, cash-flow, funding, tax, and
valuation analysis can reach the same depth as billing, SaaS, workforce, and
working capital.

## 1. Blocking correction

A2 rejects all of the following as an historical accounting basis:

- a synthetic opening balance sheet inserted independently of source records;
- retained earnings used as an unexplained balancing value;
- cash-flow statements inferred from a consumer workbook;
- fixed assets, debt, leases, or tax balances without source schedules;
- an unlimited revolver or minimum-cash financing plug;
- intercompany balances without bilateral confirmation and elimination; and
- a hard-close status produced before statutory reconciliations pass.

The A1 package remains valid as an operational and ledger Bronze baseline. It
does not become statutory authority merely because its journals balance.

## 2. Formation and opening policy

The synthetic group is modelled from formation on 2021-01-01. Its balance
before formation is exactly zero. The first balance sheet is derived from
source-backed formation transactions, including authorised equity issuance,
contracted debt drawdown, bank settlement, asset acquisition, and lease
commencement.

There is therefore no unexplained opening journal or retained-earnings plug.
Every first-period asset, liability, and equity value must be reproducible from
the same event, journal, subledger, and reconciliation paths used in later
periods.

## 3. Entity and consolidation boundary

The first A2 population contains:

- `NEXUS-UK`, the parent and principal operating entity;
- `NEXUS-US`, a wholly owned operating subsidiary; and
- `NEXUS-GROUP`, the consolidated reporting scope.

Entity accounting and group reporting remain distinct. Intercompany source
transactions post to the relevant entity ledgers through business events.
Consolidation eliminations are derived from accounting events and never
re-enter business-event posting-rule evaluation.

## 4. Truth and journal-origin boundaries

```text
source system record
-> BUSINESS_EVENT
-> posting-rule evaluation
-> entity source journal
-> entity subledger and trial-balance reconciliation

entity trial balances + confirmed intercompany positions
-> ACCOUNTING_EVENT
-> consolidation elimination journal
-> group trial balance

closed entity/group trial balance
-> statutory statement derivation
-> close and reporting-version publication
```

The boundaries are mandatory:

1. only `BUSINESS_EVENT` may enter the posting engine;
2. `ACCOUNTING_EVENT` records close, elimination, publication, reversal, and
   restatement governance and cannot enter that engine;
3. business-event journals and consolidation journals retain distinct origin
   classes;
4. statements are derived reports, not journal authors;
5. consumer calculations never flow back into A2 authority; and
6. predecessor and restated reporting versions remain simultaneously
   available.

## 5. Closed A2 source and control registry

The executable registry is
`src/finance_assurance/finance_data/statutory_gate.py`. It defines exact paths,
owners, record classes, grains, and ordered columns for 37 required datasets.
The fixed-asset and A2.2b additions separate causal source records, Hermes
admission, Atlas-derived schedules, and Argus results rather than treating
finance schedules as preassembled source truth.

| Domain | Required A2 datasets |
|---|---|
| Entity | legal entities |
| Banking | bank accounts, bank transactions, statement lines, monthly reconciliations |
| Fixed and intangible assets | asset register, monthly asset movements |
| Funding | debt instruments, monthly debt schedule |
| Leases | lease contracts, lifecycle events, monthly liability and right-of-use schedule |
| Tax | calculation inputs, monthly tax schedule, tax-loss vintage register |
| Equity | authorised equity movements |
| Other working capital | accrual and prepayment source events and schedules |
| Intercompany | bilateral transactions, confirmed balances |
| Consolidation | elimination journal lines |
| Accounting governance | accounting events, monthly close status |
| Statutory reporting | entity/group trial balance, statement lines, retained-earnings bridge, cash-flow reconciliation |
| Control | source admissions, Argus subledger results, statutory reconciliations |

Every monetary field uses signed integer minor units and explicit currency.
Rates use declared basis-point scales. Source identities, business-event or
accounting-event references, entity, period, and reporting-version coordinates
are explicit rather than inferred from filenames or consumer logic.

## 6. Required roll-forwards

### 6.1 Cash and banking

Every GL cash movement must join to a bank transaction or a declared timing
item. Statement running balances reproduce from statement lines. For every
account and month:

```text
statement closing cash
+ outstanding receipts
- outstanding disbursements
+ other declared reconciling items
= GL cash
```

The unresolved difference must be zero before close. A cash shortfall is an
economic and readiness condition; it cannot generate debt automatically.

### 6.2 Fixed and intangible assets

For every asset and period:

```text
opening gross book value
+ additions
- disposals
= closing gross book value

opening accumulated depreciation
+ depreciation and amortisation
+ impairment
- accumulated depreciation on disposals
= closing accumulated depreciation

closing gross book value - closing accumulated depreciation = closing NBV
```

Additions, disposals, depreciation, amortisation, and impairment must reconcile
to the relevant GL accounts and business events.

### 6.3 Debt

For every debt instrument and period:

```text
opening principal + drawdowns - repayments = closing principal
facility limit - closing principal = undrawn facility
```

Interest is reproducible from contractual terms, principal, and time. A
drawdown requires a real instrument, available headroom, a business event, and
an authorisation reference. `UNLIMITED_REVOLVER`,
`MINIMUM_CASH_BALANCING_PLUG`, and `UNSOURCED_DEBT_DRAWDOWN` are forbidden.

### 6.4 Leases

Lease liability opening balance, interest accretion, cash payment, principal
reduction, and closing balance must reconcile by contract. The right-of-use
asset opening balance, depreciation, impairment, and closing value must
reconcile independently and then agree to GL movements.

### 6.5 Tax

Current tax, deferred tax, cash tax, tax payable, and tax-loss utilisation are
separate movements. Tax-loss vintages cannot become negative or be used before
generation. Tax expense and cash paid must not be made equal merely for
convenience.

### 6.6 Equity and retained earnings

Share issuance, dividends, reserves, and other equity changes require an
authorised source movement. For each entity and the group:

```text
opening retained earnings
+ net income
- dividends
+ declared other equity movements
= closing retained earnings
```

The bridge is a reconciliation derived from the income statement and equity
records. It is not a balancing journal authored by the statement generator.

### 6.7 Accruals and prepayments

Accrual and prepayment openings, additions, releases, expense recognition, and
closing balances reconcile by schedule and GL account. They cannot remain
embedded in undifferentiated operating-expense proxies.

### 6.8 Intercompany and consolidation

Every intercompany transaction names seller, buyer, amount, currency, both
entity business-event references, and transfer-pricing basis. Receivables and
payables agree by entity pair or produce a declared exception. Balanced
accounting-event-derived elimination journals remove intercompany balances and
results from the group trial balance.

## 7. Monthly statutory close

Each actual month follows this order:

1. source cutoff and late-event identification;
2. billing, revenue, procurement, payroll, asset, debt, lease, tax, accrual,
   prepayment, equity, and bank subledger reconciliation;
3. bank reconciliation;
4. intercompany confirmation;
5. entity trial-balance production and balance check;
6. accounting-event-derived consolidation eliminations;
7. group trial-balance production and balance check;
8. income statement, balance sheet, and cash-flow derivation;
9. retained-earnings and cash-flow reconciliation;
10. soft close; and
11. hard close only when every required reconciliation passes.

A hard-closed period is immutable. Later historical correction uses the
existing reversal or restatement paths and produces a successor reporting
version rather than silently rewriting the accepted period.

## 8. Statutory statements

The complete historical statement population covers every month from 2021-01
through 2026-06 at entity and group scope.

- The income statement comes from period activity in mapped revenue and
  expense accounts.
- The balance sheet comes from closing mapped balance-sheet accounts plus the
  exact retained-earnings bridge.
- The cash-flow statement uses registered operating, investing, and financing
  classifications and reconciles opening to closing cash.
- Every statement row carries reporting version and a digest binding it to the
  source trial balance.

No statement line may be supplied only by Excel, React, Power BI, or a
presentation-basis proxy.

## 9. A2 acceptance gate

The executable catalogue defines exactly `A2-A01` through `A2-A30`. The gate
blocks on:

- closed package and Bronze equivalence;
- zero-opening formation replay;
- business-event/accounting-event firewall;
- banking, asset, debt, lease, tax, equity, accrual, and prepayment controls;
- bilateral intercompany agreement and elimination replay;
- entity and group trial-balance equality;
- monthly balance-sheet, net-income, retained-earnings, and cash-flow
  identities;
- close prerequisites and statement lineage; and
- deterministic canonical reproduction.

Passing arithmetic alone is insufficient. The evidence method named by each
criterion must produce the first failure from the built package rather than
copying an expected result from the registry.

## 10. Bounded implementation phases

### A2.0 - Gate authority

Complete. The initial 26-dataset registry, 30-criterion acceptance catalogue, zero
opening policy, entity boundary, forbidden financing policies, and structural
tests are checked in.

### A2.1 - Formation, entity and treasury foundation

Complete. Legal entities, source-backed formation, bank accounts,
transaction-to-bank movement binding, statement replay, monthly bank
reconciliations, authorised equity movements, and finite debt facilities are
implemented in `ATLAS-FINANCE-STATUTORY-A21@v1`.

The fixed funding plan contains GBP 50.0m formation equity, GBP 15.0m term
debt, GBP 20.0m Series B equity in 2024-01, and GBP 25.0m growth equity in
2025-04. The separate GBP 20.0m revolver is finite and remains undrawn. These
amounts and dates are source records with business events, balanced journals,
and board-authorisation references; they are not calculated from a minimum
cash target.

All 56,321 bank transactions bind to source-GL cash and one statement line.
All 126 required bank-account months reconcile to zero, statement running
balances replay exactly, and the portfolio minimum cash balance is GBP
5,795,788.10. Debt schedules cover both instruments for all 66 months and
reconcile principal, headroom, continuity, and interest. The independent
verifier recomputes these claims from emitted Bronze rows.

### A2.2 - Statutory subledgers

Fixed-asset portion complete. The accepted
`ATLAS-FINANCE-STATUTORY-A22-FA@v1` package implements 21 independent capital
purchase-order, receipt, invoice, settlement, and asset-registration chains;
five formation assets; 1,011 Atlas monthly movements; explicit depreciation,
amortisation, impairment, and disposal; Hermes admission and quarantine; and
Argus machine results.

The duplicate capital invoice remains in Bronze, is hash-bound to a Hermes
quarantine decision, creates no business event or journal, and is surfaced as
one Argus exception. Source-chain, roll-forward, GL, AP, cash, and assurance
controls are independently recomputed from the emitted database.

Leases, tax and tax losses, accruals, and prepayments are complete in
`ATLAS-FINANCE-STATUTORY-A22B@v1`. Four source-backed lease contracts roll
through liability and ROU schedules. Tax inputs produce six loss vintages and
a policy-bound deferred-tax asset without fabricating current or cash tax.
Accrual and prepayment events roll into explicit monthly schedules. One
duplicate prepayment remains in Bronze, is quarantined by Hermes, creates no
business event or journal, and is surfaced by Argus.

### A2.3 - Multi-entity close and statements

Complete. Independent bilateral records enter Hermes before Atlas derives the
seller and buyer journals. Consolidation eliminations originate only from
accounting events and never re-enter the business-event posting engine. Atlas
publishes 66 monthly trial balances, income statements, balance sheets, cash
flows, retained-earnings bridges, cash reconciliations, and hard-close versions
for `NEXUS-UK`, `NEXUS-US`, and `NEXUS-GROUP`. Argus independently records five
passing statutory reconciliation results for every period and scope.

### A2.4 - Package and independent audit

Complete. The portfolio-scale A2.4 package and an independent reproduction have
the same digest and 82 byte-identical canonical/seal files. All thirty
acceptance criteria pass, including explicit formation replay, cross-statement
net income, five-control hard-close prerequisites, and
statement-to-source lineage. Silver/Gold Slice B is authorised over the exact
ratified data reference and digest; no consumer product is implied by that
authorisation.
