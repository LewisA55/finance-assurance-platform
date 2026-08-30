from __future__ import annotations

from pytest import raises

from finance_assurance.finance_data.multi_entity_close import (
    AtlasConsolidationEliminationRules,
    AtlasIntercompanyPostingRules,
    ConsolidationEliminationInput,
    IntercompanyPostingInput,
)


def test_intercompany_entity_rules_are_business_event_guarded_and_balanced() -> None:
    rules = AtlasIntercompanyPostingRules()
    seller = rules.derive(
        IntercompanyPostingInput("BUSINESS_EVENT", "SELLER", 125_000, "6200")
    )
    buyer = rules.derive(
        IntercompanyPostingInput("BUSINESS_EVENT", "BUYER", 125_000, "6200")
    )

    assert seller.lines == (("1150", 125_000, 0), ("4100", 0, 125_000))
    assert buyer.lines == (("6200", 125_000, 0), ("2050", 0, 125_000))
    assert sum(line[1] for line in seller.lines) == sum(
        line[2] for line in seller.lines
    )
    assert sum(line[1] for line in buyer.lines) == sum(
        line[2] for line in buyer.lines
    )
    with raises(ValueError, match="only BUSINESS_EVENT"):
        rules.derive(
            IntercompanyPostingInput("ACCOUNTING_EVENT", "SELLER", 1, "6200")
        )


def test_consolidation_rules_accept_only_accounting_events() -> None:
    rules = AtlasConsolidationEliminationRules()
    elimination = rules.derive(
        ConsolidationEliminationInput("ACCOUNTING_EVENT", 125_000, "6200")
    )

    assert elimination.lines == (
        ("4100", 125_000, 0),
        ("6200", 0, 125_000),
        ("2050", 125_000, 0),
        ("1150", 0, 125_000),
    )
    assert sum(line[1] for line in elimination.lines) == sum(
        line[2] for line in elimination.lines
    )
    with raises(ValueError, match="only ACCOUNTING_EVENT"):
        rules.derive(
            ConsolidationEliminationInput("BUSINESS_EVENT", 1, "6200")
        )
