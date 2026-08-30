# Finance and Assurance Module Operating Model

Status: Direction accepted; fixed-asset and statutory-subledger verticals implemented

## 1. Product hierarchy

The platform remains one product rather than five applications. Atlas is the
primary finance product and the only accounting authority. Hermes, Argus,
Aegis, and Pythia are focused capability lenses over the shared substrate.

The shared substrate is infrastructure. It is not a sixth module and does not
own source-domain, accounting, assurance, governance, or planning meaning.

## 2. Target flow

```text
independent source-system record
-> Hermes immutable admission, identity, quarantine, and lineage
-> admitted business event
-> Atlas versioned posting rule
-> canonical subledger movement and journal proposal
-> approved immutable journal
-> entity trial balance and reporting version
-> Argus observation or exception
-> Aegis disposition, remediation directive, and readiness
-> Pythia scenario overlay over an exact approved snapshot
```

Only an admitted business event may enter posting-rule evaluation. An
accounting event, Argus result, Aegis directive, or Pythia output cannot enter
that interface.

## 3. Refined module roles

### Hermes

Hermes owns immutable raw admission, source/file identity, ingestion and event
time, schema validation, quarantine, duplicate and late-arrival handling,
canonical identity mapping, and source-to-accounting lineage. Source domains
retain semantic ownership of their records. Hermes does not decide accounting
treatment or whether an accounting balance is correct.

### Atlas

Atlas consumes admitted business events and owns posting rules, journal
proposals, approvals, posted journals, subledger projections, periods, trial
balances, consolidation, reporting versions, and statements. It does not
rewrite source records or self-approve purpose-specific readiness.

### Argus

Argus owns versioned tests, frozen test populations, machine observations,
exceptions, and reproducible evidence. It tests source records and Atlas state
but cannot mutate either or create a formal governance conclusion.

### Aegis

Aegis owns review dispositions, findings, issues, remediation directives,
readiness, and sign-off. Aegis may authorise a correction but Atlas remains the
only boundary permitted to construct and post an adjusting journal.

### Pythia

Pythia consumes an exact Atlas reporting version and exact Aegis readiness
assessment. It owns frozen planning snapshots, assumption sets, scenarios,
forecasts, recommendations, and decisions. It never overwrites actuals or
selects an implicit latest snapshot.

## 4. Migration policy

Accepted A1 and A2.1 packages remain immutable and verifiable. Their combined
business-event and source-journal generator is a transitional implementation,
not the target module boundary. New A2.2 domains introduce independent source
records, explicit admission, and Atlas-derived accounting before the existing
operational domains are migrated to the same pattern.

Generated ERP trial balances and statements may remain independent source
reports. They are reconciliands and evidence; they are not permitted to author
the Atlas ledger or governed statements.

Artifact P, Q, R, and S remain internal governance and delivery machinery.
They must support the finance product without becoming its visible product
hierarchy or creating consumer calculations as governed truth.

## 5. First vertical: fixed assets

The first implementation covers:

```text
capital purchase order
-> goods receipt
-> supplier invoice and settlement
-> asset lifecycle record
-> Hermes admission
-> Atlas capitalisation and payment journals
-> asset register and monthly roll-forward
-> depreciation, impairment, and disposal journals
-> GL and cash reconciliation
-> Argus fixed-asset controls
```

This vertical ends at machine assurance results. Aegis case management,
Pythia CapEx scenarios, complete statutory close, and consumer experiences are
separate bounded phases.

## 6. Second vertical: statutory subledgers

A2.2b extends the same boundary to:

```text
lease contracts and lifecycle events
tax calculation inputs
accrual and prepayment source events
-> Hermes admission, warnings, and quarantine
-> admitted business events
-> Atlas lease, tax, accrual, and prepayment posting rules
-> Atlas monthly subledger schedules
-> GL, cash, and continuity reconciliation
-> Argus machine controls and exceptions
```

The package preserves the distinction between current tax, cash tax, tax-loss
vintages, and deferred tax. Lease liabilities and right-of-use assets roll
forward independently. Accruals and prepayments are explicit schedules rather
than expense proxies.

## 7. Third vertical: multi-entity close

A2.3 completes the historical accounting state:

```text
bilateral intercompany source records and confirmations
-> Hermes exact-record admission
-> entity BUSINESS_EVENT postings in Atlas
-> entity trial balances
-> ACCOUNTING_EVENT consolidation eliminations
-> group trial balance
-> three statements, retained earnings, and cash reconciliation
-> soft close, hard close, and reporting-version publication
-> Argus statutory reconciliation results
```

Hermes owns source integrity, Atlas remains the only accounting and reporting
authority, and Argus recomputes control outcomes. Aegis and Pythia do not enter
this historical close path. A2.4 has now reproduced and ratified the complete
boundary. The next authorised work is the shared Silver/Gold finance model.

## 6. Second vertical: statutory subledgers

A2.2b extends the same boundary to:

```text
lease contracts and lifecycle events
tax calculation inputs
accrual and prepayment source events
-> Hermes admission, warnings, and quarantine
-> admitted business events
-> Atlas lease, tax, accrual, and prepayment posting rules
-> Atlas monthly subledger schedules
-> GL, cash, and continuity reconciliation
-> Argus machine controls and exceptions
```

The package preserves the distinction between current tax, cash tax, tax-loss
vintages, and deferred tax. Lease liabilities and right-of-use assets roll
forward independently. Accruals and prepayments are explicit schedules rather
than expense proxies. The next product boundary remains A2.3 multi-entity close
and statements; Aegis and Pythia do not enter the A2.2b accounting path.
