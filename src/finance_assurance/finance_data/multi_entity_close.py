"""Atlas rules for bilateral intercompany posting and consolidation elimination."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

IntercompanySide = Literal["SELLER", "BUYER"]


@dataclass(frozen=True, slots=True)
class IntercompanyPostingInput:
    """Admitted bilateral source fact presented to Atlas posting rules."""

    origin_class: str
    side: IntercompanySide
    amount_minor: int
    buyer_expense_account_id: str


@dataclass(frozen=True, slots=True)
class IntercompanyPosting:
    """One deterministic Atlas intercompany journal instruction."""

    posting_rule_ref: str
    journal_amount_minor: int
    lines: tuple[tuple[str, int, int], ...]


class AtlasIntercompanyPostingRules:
    """Derive entity postings only from admitted business events."""

    def derive(self, value: IntercompanyPostingInput) -> IntercompanyPosting:
        if value.origin_class != "BUSINESS_EVENT":
            raise ValueError("only BUSINESS_EVENT may enter intercompany posting")
        if value.amount_minor <= 0:
            raise ValueError("intercompany posting amount must be positive")
        if value.buyer_expense_account_id not in {"6000", "6200"}:
            raise ValueError("unsupported intercompany buyer expense account")
        if value.side == "SELLER":
            return IntercompanyPosting(
                posting_rule_ref="PR-INTERCOMPANY-SELLER-SERVICE@v1",
                journal_amount_minor=value.amount_minor,
                lines=(
                    ("1150", value.amount_minor, 0),
                    ("4100", 0, value.amount_minor),
                ),
            )
        if value.side == "BUYER":
            return IntercompanyPosting(
                posting_rule_ref="PR-INTERCOMPANY-BUYER-SERVICE@v1",
                journal_amount_minor=value.amount_minor,
                lines=(
                    (value.buyer_expense_account_id, value.amount_minor, 0),
                    ("2050", 0, value.amount_minor),
                ),
            )
        raise ValueError(f"unsupported intercompany side: {value.side}")


@dataclass(frozen=True, slots=True)
class ConsolidationEliminationInput:
    """Governed accounting event presented to consolidation rules."""

    origin_class: str
    amount_minor: int
    buyer_expense_account_id: str


@dataclass(frozen=True, slots=True)
class ConsolidationElimination:
    """Balanced group-only elimination that never enters source posting."""

    rule_ref: str
    lines: tuple[tuple[str, int, int], ...]


class AtlasConsolidationEliminationRules:
    """Derive group eliminations only from accounting lifecycle events."""

    def derive(
        self, value: ConsolidationEliminationInput
    ) -> ConsolidationElimination:
        if value.origin_class != "ACCOUNTING_EVENT":
            raise ValueError(
                "only ACCOUNTING_EVENT may enter consolidation elimination"
            )
        if value.amount_minor <= 0:
            raise ValueError("consolidation elimination amount must be positive")
        if value.buyer_expense_account_id not in {"6000", "6200"}:
            raise ValueError("unsupported intercompany buyer expense account")
        return ConsolidationElimination(
            rule_ref="AE-CONSOLIDATE-INTERCOMPANY-SERVICE@v1",
            lines=(
                ("4100", value.amount_minor, 0),
                (value.buyer_expense_account_id, 0, value.amount_minor),
                ("2050", value.amount_minor, 0),
                ("1150", 0, value.amount_minor),
            ),
        )
