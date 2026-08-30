# Canonical Transaction C-001

## Summary

Orion Manufacturing Ltd signs a 12-month SaaS contract with Nexus for GBP 120,000. The contract starts on 1 June 2026 and ends on 31 May 2027. Billing is annual and upfront. Revenue is recognised straight-line at GBP 10,000 per month.

The June recognition proposal exists and is submitted, but it is explicitly deferred under close-exception policy rather than approved and posted before June hard close. Argus detects that the recognition schedule expected one posted June recognition journal but found none. Aegis governs the issue. Atlas preserves the original June reporting version and publishes June v2 through the restatement arm.

## Key Design Choice

C-001 uses restatement, not reversal.

There is no original posted June recognition journal to reverse. The missed GBP 10,000 exists as a submitted but unposted proposal. Because June is hard-closed when the completeness gap is found, the adjustment is posted under restatement policy in the open July 2026 correction period while June is republished as v2. July is canonical C-001 scenario data, not a platform rule for all restatements.

## Event and Object Flow

```text
business_event: accounting.recognition.due
-> posting_rule: PR-O2C-RECOG
-> journal_proposal: P-551@v1
-> accounting_event: proposal.submitted
-> accounting_event: proposal.deferred
-> accounting_event: period.hard_closed
-> Argus completeness exception
-> Aegis finding and issue
-> accounting_event: restatement.proposed
-> restatement_case: RC-001 proposed
-> journal_proposal: P-551@v2 restatement treatment
-> accounting_event: proposal.submitted
-> accounting_event: proposal.approved
-> accounting_event: journal.posted
-> journal_entry and journal_line records in ledger period 2026-07
-> accounting_event: restatement.adjustment_linked
-> frozen presentation-adjustment manifest maps the correction to 2026-06
-> accounting_event: restatement.adjustments_ready
-> accounting_event: restatement.approved
-> accounting_event: reporting_version.published
-> reporting_version: 2026-06 v2
```

The flow contains the eleven accounting-event instances fixed by Artifact F.

Only the original `business_event` enters the posting-rule evaluator. None of the accounting events re-enter the engine.

## Accounting Impact

Original June reporting version:

```text
Revenue             GBP 0
Deferred revenue    GBP 120,000
```

Restated June reporting version:

```text
Revenue             GBP 10,000
Deferred revenue    GBP 110,000
```

## Assurance Result

`ARG-O2C-002` contract-to-revenue completeness fails:

```text
expected_recognition_journals = 1
posted_recognition_journals = 0
submitted_unposted_proposals = 1
deferred_proposals = 1
difference_gbp = 10,000
severity = blocking
```
