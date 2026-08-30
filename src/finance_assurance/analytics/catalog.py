"""Finite Atlas-owned ledger semantics required by Artifact Q v0.2."""

from __future__ import annotations

from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.contracts.primitives import EvidenceRef

CATALOG_REF = "LEDGER-SEMANTICS-DEMO@v1"
CATALOG_EVIDENCE_REF = "EVD-LEDGER-SEMANTICS-001"


def ledger_catalog_evidence() -> EvidenceRef:
    return EvidenceRef(
        ref_id=CATALOG_EVIDENCE_REF,
        description="Approved synthetic ledger-semantics catalogue",
        content_hash=canonical_sha256(
            {
                "catalog_ref": CATALOG_REF,
                "purpose": "Artifact Q governed ledger semantics",
                "synthetic": True,
            }
        ),
    )


def ledger_semantics_catalog() -> dict[str, object]:
    evidence = ledger_catalog_evidence()
    return {
        "contract_version": 1,
        "catalog_id": "LEDGER-SEMANTICS-DEMO",
        "catalog_version": 1,
        "catalog_ref": CATALOG_REF,
        "effective_from": "2026-01-01",
        "effective_to": None,
        "status": "ACTIVE",
        "accounts": [
            {"account_id": "ACC-AR", "account_name": "Accounts receivable", "account_class": "ASSET", "normal_balance": "DEBIT", "control_role": "AR"},
            {"account_id": "ACC-DEFERRED-REVENUE", "account_name": "Deferred revenue", "account_class": "LIABILITY", "normal_balance": "CREDIT", "control_role": "NONE"},
            {"account_id": "ACC-SUBSCRIPTION-REVENUE", "account_name": "Subscription revenue", "account_class": "REVENUE", "normal_balance": "CREDIT", "control_role": "NONE"},
            {"account_id": "ACC-UNAPPLIED-CASH", "account_name": "Unapplied cash", "account_class": "LIABILITY", "normal_balance": "CREDIT", "control_role": "UNAPPLIED_CASH"},
        ],
        "statement_lines": [
            {"statement_field": "accounts_receivable_minor", "statement_label": "Accounts receivable", "statement_class": "BALANCE_SHEET", "display_order": 10},
            {"statement_field": "deferred_revenue_minor", "statement_label": "Deferred revenue", "statement_class": "BALANCE_SHEET", "display_order": 20},
            {"statement_field": "subscription_revenue_minor", "statement_label": "Subscription revenue", "statement_class": "INCOME_STATEMENT", "display_order": 10},
            {"statement_field": "unapplied_cash_minor", "statement_label": "Unapplied cash", "statement_class": "BALANCE_SHEET", "display_order": 30},
        ],
        "mappings": [
            {"account_id": "ACC-AR", "statement_field": "accounts_receivable_minor", "mapping_role": "PRIMARY"},
            {"account_id": "ACC-DEFERRED-REVENUE", "statement_field": "deferred_revenue_minor", "mapping_role": "PRIMARY"},
            {"account_id": "ACC-SUBSCRIPTION-REVENUE", "statement_field": "subscription_revenue_minor", "mapping_role": "PRIMARY"},
            {"account_id": "ACC-UNAPPLIED-CASH", "statement_field": "unapplied_cash_minor", "mapping_role": "PRIMARY"},
        ],
        "evidence_refs": [evidence.model_dump(mode="json")],
    }


def july_open_period() -> dict[str, object]:
    return {
        "contract_version": 1,
        "period_id": "2026-07",
        "start_date": "2026-07-01",
        "end_date": "2026-07-31",
        "status": "OPEN",
        "ledger_currency": "GBP",
        "evidence_refs": [],
        "opened_at": "2026-07-01T00:00:00Z",
    }
