# Canonical Transaction CT-1

## Summary

Nexus receives GBP 120,000 from Orion Manufacturing Ltd in July 2026. The receipt is initially applied to the wrong customer, Vega Industrial Ltd, while July remains open.

Because an incorrect journal was posted in an open correction path, CT-1 uses reversal and replacement rather than restatement.

## Correction Flow

```text
wrong application posted as J-010
-> frozen equal-and-opposite reversal proposal
-> accounting_event: proposal.submitted
-> accounting_event: proposal.approved
-> accounting_event: journal.posted
-> immutable reversal journal J-011
-> frozen replacement proposal for Orion
-> accounting_event: proposal.submitted
-> accounting_event: proposal.approved
-> accounting_event: journal.posted
-> immutable replacement journal J-012
```

CT-1 exists to prove the reversal arm of the accounting lifecycle.

## Design Role

C-001 and CT-1 should remain distinct:

- C-001 proves submitted-but-unposted proposal, hard-close preservation, and restatement publication.
- CT-1 proves wrong posted journal, open-period correction, reversal, and replacement.
