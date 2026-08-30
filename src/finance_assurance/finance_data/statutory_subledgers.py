"""Atlas posting rules for the A2.2b statutory subledger verticals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LeaseEventType = Literal[
    "LEASE_COMMENCED",
    "LEASE_PAYMENT_MADE",
    "RIGHT_OF_USE_ASSET_DEPRECIATED",
]
TaxEventType = Literal[
    "CURRENT_TAX_ACCRUED",
    "CURRENT_TAX_PAID",
    "DEFERRED_TAX_ASSET_RECOGNISED",
    "DEFERRED_TAX_ASSET_RELEASED",
]
WorkingCapitalEventType = Literal[
    "ACCRUAL_ESTIMATE_APPROVED",
    "ACCRUAL_SETTLED",
    "PREPAYMENT_PAID",
    "PREPAID_SERVICE_CONSUMED",
]


@dataclass(frozen=True, slots=True)
class AtlasPosting:
    """One deterministic Atlas posting instruction."""

    posting_rule_ref: str
    journal_amount_minor: int
    lines: tuple[tuple[str, int, int], ...]


@dataclass(frozen=True, slots=True)
class LeasePostingInput:
    """Admitted lease business-event facts available to Atlas."""

    origin_class: str
    event_type: LeaseEventType
    event_amount_minor: int
    principal_minor: int = 0
    interest_minor: int = 0


class AtlasLeasePostingRules:
    """Derive lease postings only from admitted business events."""

    def derive(self, value: LeasePostingInput) -> AtlasPosting:
        if value.origin_class != "BUSINESS_EVENT":
            raise ValueError("only BUSINESS_EVENT may enter lease posting")
        amount = value.event_amount_minor
        if amount < 0:
            raise ValueError("lease posting amount cannot be negative")
        if value.event_type == "LEASE_COMMENCED":
            return AtlasPosting(
                "PR-LEASE-COMMENCEMENT@v1",
                amount,
                (("1800", amount, 0), ("2500", 0, amount)),
            )
        if value.event_type == "LEASE_PAYMENT_MADE":
            if value.principal_minor + value.interest_minor != amount:
                raise ValueError("lease payment split does not equal cash payment")
            return AtlasPosting(
                "PR-LEASE-PAYMENT@v2",
                amount,
                (
                    ("2500", value.principal_minor, 0),
                    ("6500", value.interest_minor, 0),
                    ("1000", 0, amount),
                ),
            )
        if value.event_type == "RIGHT_OF_USE_ASSET_DEPRECIATED":
            return AtlasPosting(
                "PR-ROU-DEPRECIATION@v2",
                amount,
                (("6300", amount, 0), ("1810", 0, amount)),
            )
        raise ValueError(f"unsupported lease event: {value.event_type}")


@dataclass(frozen=True, slots=True)
class TaxPostingInput:
    """Admitted tax business-event facts available to Atlas."""

    origin_class: str
    event_type: TaxEventType
    event_amount_minor: int


class AtlasTaxPostingRules:
    """Derive current and deferred tax postings without conflating cash tax."""

    def derive(self, value: TaxPostingInput) -> AtlasPosting:
        if value.origin_class != "BUSINESS_EVENT":
            raise ValueError("only BUSINESS_EVENT may enter tax posting")
        amount = value.event_amount_minor
        if amount < 0:
            raise ValueError("tax posting amount cannot be negative")
        if value.event_type == "CURRENT_TAX_ACCRUED":
            return AtlasPosting(
                "PR-CURRENT-TAX-ACCRUAL@v1",
                amount,
                (("6600", amount, 0), ("2300", 0, amount)),
            )
        if value.event_type == "CURRENT_TAX_PAID":
            return AtlasPosting(
                "PR-CURRENT-TAX-PAYMENT@v1",
                amount,
                (("2300", amount, 0), ("1000", 0, amount)),
            )
        if value.event_type == "DEFERRED_TAX_ASSET_RECOGNISED":
            return AtlasPosting(
                "PR-DEFERRED-TAX-ASSET-RECOGNITION@v1",
                amount,
                (("1250", amount, 0), ("6600", 0, amount)),
            )
        if value.event_type == "DEFERRED_TAX_ASSET_RELEASED":
            return AtlasPosting(
                "PR-DEFERRED-TAX-ASSET-RELEASE@v1",
                amount,
                (("6600", amount, 0), ("1250", 0, amount)),
            )
        raise ValueError(f"unsupported tax event: {value.event_type}")


@dataclass(frozen=True, slots=True)
class WorkingCapitalPostingInput:
    """Admitted accrual or prepayment event facts available to Atlas."""

    origin_class: str
    event_type: WorkingCapitalEventType
    event_amount_minor: int
    expense_account_id: str


class AtlasWorkingCapitalPostingRules:
    """Derive explicit accrual and prepayment postings."""

    def derive(self, value: WorkingCapitalPostingInput) -> AtlasPosting:
        if value.origin_class != "BUSINESS_EVENT":
            raise ValueError("only BUSINESS_EVENT may enter working-capital posting")
        amount = value.event_amount_minor
        if amount < 0:
            raise ValueError("working-capital posting amount cannot be negative")
        if value.expense_account_id not in {"5000", "6000", "6100", "6200"}:
            raise ValueError("working-capital expense account is not permitted")
        if value.event_type == "ACCRUAL_ESTIMATE_APPROVED":
            return AtlasPosting(
                "PR-ACCRUAL-ESTIMATE@v1",
                amount,
                ((value.expense_account_id, amount, 0), ("2200", 0, amount)),
            )
        if value.event_type == "ACCRUAL_SETTLED":
            return AtlasPosting(
                "PR-ACCRUAL-SETTLEMENT@v1",
                amount,
                (("2200", amount, 0), ("1000", 0, amount)),
            )
        if value.event_type == "PREPAYMENT_PAID":
            return AtlasPosting(
                "PR-PREPAYMENT-CASH-ADDITION@v1",
                amount,
                (("1200", amount, 0), ("1000", 0, amount)),
            )
        if value.event_type == "PREPAID_SERVICE_CONSUMED":
            return AtlasPosting(
                "PR-PREPAYMENT-EXPENSE-RELEASE@v1",
                amount,
                ((value.expense_account_id, amount, 0), ("1200", 0, amount)),
            )
        raise ValueError(f"unsupported working-capital event: {value.event_type}")
