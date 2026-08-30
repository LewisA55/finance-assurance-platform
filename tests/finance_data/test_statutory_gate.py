from finance_assurance.finance_data.statutory_gate import (
    FORBIDDEN_FINANCING_POLICIES,
    FORMATION_OPENING_BALANCE_MINOR,
    LEGAL_ENTITY_IDS,
    STATUTORY_ACCEPTANCE_CATALOGUE,
    STATUTORY_SOURCE_REGISTRY,
    validate_statutory_gate,
)


def test_a2_source_registry_is_closed_and_valid() -> None:
    validate_statutory_gate()

    assert len(STATUTORY_SOURCE_REGISTRY) == 37
    assert len({item.dataset_id for item in STATUTORY_SOURCE_REGISTRY}) == 37
    assert len({item.path for item in STATUTORY_SOURCE_REGISTRY}) == 37


def test_a2_acceptance_catalogue_is_exact_and_blocking() -> None:
    assert tuple(item.criterion_id for item in STATUTORY_ACCEPTANCE_CATALOGUE) == (
        tuple(f"A2-A{number:02d}" for number in range(1, 31))
    )
    assert all(
        item.claim and item.evidence_method
        for item in STATUTORY_ACCEPTANCE_CATALOGUE
    )


def test_a2_forbids_opening_and_financing_plugs() -> None:
    assert FORMATION_OPENING_BALANCE_MINOR == 0
    assert set(FORBIDDEN_FINANCING_POLICIES) == {
        "UNLIMITED_REVOLVER",
        "MINIMUM_CASH_BALANCING_PLUG",
        "UNSOURCED_DEBT_DRAWDOWN",
    }
    assert LEGAL_ENTITY_IDS == ("NEXUS-UK", "NEXUS-US")


def test_a2_money_columns_are_explicit_minor_units() -> None:
    monetary_columns = {
        column
        for dataset in STATUTORY_SOURCE_REGISTRY
        for column in dataset.columns
        if column.endswith("_minor")
    }
    monetary_datasets = tuple(
        dataset
        for dataset in STATUTORY_SOURCE_REGISTRY
        if set(dataset.columns).intersection(monetary_columns)
    )
    legacy_money_columns = {
        column
        for dataset in STATUTORY_SOURCE_REGISTRY
        for column in dataset.columns
        if column.endswith("_gbp") or column.endswith("_local")
    }

    assert len(monetary_columns) >= 60
    assert monetary_datasets
    assert all("currency" in dataset.columns for dataset in monetary_datasets)
    assert not legacy_money_columns


def test_a22_fixed_asset_module_ownership_is_explicit() -> None:
    by_id = {item.dataset_id: item for item in STATUTORY_SOURCE_REGISTRY}

    assert by_id["A2-CAPITAL-INVOICES"].owner == "HERMES"
    assert by_id["A2-FIXED-ASSET-REGISTER"].owner == "HERMES"
    assert by_id["A2-SOURCE-ADMISSION-RESULTS"].owner == "HERMES"
    assert by_id["A2-FIXED-ASSET-MOVEMENTS"].owner == "ATLAS"
    assert by_id["A2-FIXED-ASSET-CONTROL-RESULTS"].owner == "ARGUS"
    assert (
        by_id["A2-FIXED-ASSET-MOVEMENTS"].record_class
        == "ATLAS_DERIVED_SUBLEDGER"
    )
    assert (
        by_id["A2-FIXED-ASSET-CONTROL-RESULTS"].record_class
        == "ASSURANCE_RESULT"
    )


def test_a22b_statutory_subledger_module_ownership_is_explicit() -> None:
    by_id = {item.dataset_id: item for item in STATUTORY_SOURCE_REGISTRY}

    assert by_id["A2-LEASE-CONTRACTS"].owner == "HERMES"
    assert by_id["A2-TAX-CALCULATION-INPUTS"].owner == "HERMES"
    assert by_id["A2-ACCRUAL-SOURCE-EVENTS"].owner == "HERMES"
    assert by_id["A2-PREPAYMENT-SOURCE-EVENTS"].owner == "HERMES"
    assert by_id["A2-LEASE-SCHEDULE"].owner == "ATLAS"
    assert by_id["A2-TAX-SCHEDULE"].owner == "ATLAS"
    assert by_id["A2-ACCRUAL-SCHEDULE"].owner == "ATLAS"
    assert by_id["A2-PREPAYMENT-SCHEDULE"].owner == "ATLAS"
    assert (
        by_id["A2-STATUTORY-SUBLEDGER-CONTROL-RESULTS"].owner
        == "ARGUS"
    )


def test_a23_multi_entity_close_authorities_are_explicit() -> None:
    by_id = {item.dataset_id: item for item in STATUTORY_SOURCE_REGISTRY}

    assert by_id["A2-INTERCOMPANY-TRANSACTIONS"].owner == "HERMES"
    assert by_id["A2-INTERCOMPANY-BALANCES"].owner == "HERMES"
    assert by_id["A2-CONSOLIDATION-ELIMINATIONS"].owner == "ATLAS"
    assert by_id["A2-ACCOUNTING-EVENTS"].owner == "ATLAS"
    assert by_id["A2-STATUTORY-TRIAL-BALANCE"].owner == "ATLAS"
    assert by_id["A2-STATUTORY-STATEMENTS"].owner == "ATLAS"
    assert by_id["A2-STATUTORY-RECONCILIATIONS"].owner == "ARGUS"
    assert (
        by_id["A2-STATUTORY-TRIAL-BALANCE"].record_class
        == "ATLAS_DERIVED_REPORT"
    )
    assert (
        by_id["A2-STATUTORY-RECONCILIATIONS"].record_class
        == "ASSURANCE_RESULT"
    )
