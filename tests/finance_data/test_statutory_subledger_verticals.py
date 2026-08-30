from __future__ import annotations

from pytest import raises

from finance_assurance.finance_data.statutory_subledgers import (
    AtlasLeasePostingRules,
    AtlasTaxPostingRules,
    AtlasWorkingCapitalPostingRules,
    LeasePostingInput,
    TaxPostingInput,
    WorkingCapitalPostingInput,
)


def test_atlas_lease_rules_separate_liability_interest_cash_and_rou() -> None:
    rules = AtlasLeasePostingRules()
    payment = rules.derive(
        LeasePostingInput(
            origin_class="BUSINESS_EVENT",
            event_type="LEASE_PAYMENT_MADE",
            event_amount_minor=5_500_000,
            principal_minor=4_500_000,
            interest_minor=1_000_000,
        )
    )
    depreciation = rules.derive(
        LeasePostingInput(
            origin_class="BUSINESS_EVENT",
            event_type="RIGHT_OF_USE_ASSET_DEPRECIATED",
            event_amount_minor=5_000_000,
        )
    )

    assert payment.lines == (
        ("2500", 4_500_000, 0),
        ("6500", 1_000_000, 0),
        ("1000", 0, 5_500_000),
    )
    assert depreciation.lines == (
        ("6300", 5_000_000, 0),
        ("1810", 0, 5_000_000),
    )


def test_atlas_tax_rules_keep_current_cash_and_deferred_tax_distinct() -> None:
    rules = AtlasTaxPostingRules()

    current = rules.derive(
        TaxPostingInput(
            origin_class="BUSINESS_EVENT",
            event_type="CURRENT_TAX_ACCRUED",
            event_amount_minor=12_000_000,
        )
    )
    deferred = rules.derive(
        TaxPostingInput(
            origin_class="BUSINESS_EVENT",
            event_type="DEFERRED_TAX_ASSET_RECOGNISED",
            event_amount_minor=7_500_000,
        )
    )

    assert current.lines == (("6600", 12_000_000, 0), ("2300", 0, 12_000_000))
    assert deferred.lines == (("1250", 7_500_000, 0), ("6600", 0, 7_500_000))


def test_atlas_working_capital_rules_are_event_guarded_and_balanced() -> None:
    rules = AtlasWorkingCapitalPostingRules()
    prepayment = rules.derive(
        WorkingCapitalPostingInput(
            origin_class="BUSINESS_EVENT",
            event_type="PREPAYMENT_PAID",
            event_amount_minor=12_000_000,
            expense_account_id="6200",
        )
    )

    assert prepayment.lines == (("1200", 12_000_000, 0), ("1000", 0, 12_000_000))
    with raises(ValueError, match="only BUSINESS_EVENT"):
        rules.derive(
            WorkingCapitalPostingInput(
                origin_class="ACCOUNTING_EVENT",
                event_type="ACCRUAL_ESTIMATE_APPROVED",
                event_amount_minor=1_000_000,
                expense_account_id="6200",
            )
        )
