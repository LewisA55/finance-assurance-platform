# Milestone 5 Slice A2.2b - Statutory Subledgers

Status: Implemented and independently verified on 2026-08-24

## 1. Bounded outcome

A2.2b applies the source -> Hermes -> Atlas -> Argus pattern proven by fixed
assets to leases, tax and tax-loss vintages, accruals, and prepayments. It does
not implement multi-entity close, consolidation, complete statements, Aegis
workflow, Pythia scenarios, Silver/Gold, or consumer experiences.

## 2. Authority boundary

Independent source records are admitted without changing their truth class.
Only admitted `BUSINESS_EVENT` records enter the Atlas posting interfaces.
Atlas derives journals and monthly schedules. Argus publishes machine control
results and cannot mutate source or accounting state.

The executable registry expands from 32 to 37 authorities. The physical
package expands from 57 to 68 datasets by adding:

- lease contracts and lease lifecycle events;
- Atlas lease liability and right-of-use schedules;
- tax calculation inputs, tax schedules, and tax-loss vintages;
- accrual source events and Atlas accrual schedules;
- prepayment source events and Atlas prepayment schedules; and
- Argus statutory-subledger control results.

All posting-rule components reject `ACCOUNTING_EVENT` inputs.

## 3. Accounting treatment

Lease commencement recognises a right-of-use asset and lease liability.
Payments separate interest, principal, and cash. Right-of-use depreciation is
recorded independently from the liability schedule.

Tax keeps accounting profit or loss, permanent differences, temporary
differences, taxable profit, loss generation, loss utilisation, current tax,
cash tax, and deferred tax separate. The loss-making history generates six
annual tax-loss vintages. A declared recognition policy recognises a deferred
tax asset over a bounded portion of those losses; current tax and cash tax are
not fabricated merely to populate a schedule.

Accrual estimates recognise expense and an accrued liability. Later settlement
clears the liability against cash. Prepayment cash additions recognise an
asset; monthly consumption releases the asset to the registered expense
account.

## 4. Accepted package

- data reference: `ATLAS-FINANCE-STATUTORY-A22B@v1`;
- path: `build/finance-data-substrate/ATLAS-FINANCE-STATUTORY-A22B-V1`;
- 68 closed source, reference, derived, and control datasets;
- 4,207,578 rows across 66 actual months;
- 276 declared defects;
- 15 generated QA results, all passing; and
- digest:
  `sha256:b285c23cff0b07324f8ac8cf45c754ce0ca6b6e1fabec73b297c83df9e96fd00`.

The lease portfolio contains four contracts, 164 monthly schedules, GBP 4.30m
of initial lease liabilities, GBP 4.34m of historical cash payments, and a
June 2026 closing liability of GBP 0.49m. The closing right-of-use asset is GBP
0.45m.

The tax population contains 66 monthly provisions and six annual loss
vintages. June 2026 tax losses are GBP 96.34m and the policy-bound recognised
deferred-tax asset is GBP 7.23m.

Accruals contain 264 monthly schedules, GBP 1.19m of additions, and GBP 0.02m
open at June 2026. Prepayments contain 187 monthly schedules, GBP 0.75m of cash
additions, and GBP 0.07m open at June 2026.

Hermes publishes 1,117 ordinary A2.2b admissions, three warned late arrivals,
and one quarantined duplicate prepayment. The duplicate remains in Bronze and
creates no business event or journal. Argus publishes 1,127 passing controls
and one expected duplicate-source exception.

The expanded statutory population retains positive cash without changing the
accepted A2.1 funding plan. Independent statement replay gives minimum cash of
GBP 3,082,301.85; the finite revolver remains undrawn.

## 5. Independent verification

The verifier recalculates, from emitted Bronze rows:

1. exact source-payload hashes and Hermes decisions;
2. quarantine isolation and admitted event binding;
3. lease contract, liability, ROU, continuity, and GL identities;
4. tax input, payable, deferred-tax, loss-vintage, and GL identities;
5. accrual and prepayment source-to-schedule roll-forwards;
6. schedule-to-GL activity and cash effects;
7. Argus result integrity; and
8. bank-statement replay under the unchanged authorised funding plan.

Twenty-two focused finance-data tests pass, including deterministic package
rebuilding and negative origin-class paths. Ruff passes across the complete
finance-data implementation and tests. The current verifier remains compatible
with the accepted A1, A2.1, and A2.2a package inventories.

## 6. Next gate

A2.3 is next: intercompany source records, bilateral confirmations, entity
ledgers, accounting-event-derived eliminations, entity and group trial
balances, complete historical statements, retained-earnings and cash-flow
reconciliations, and monthly close state.
