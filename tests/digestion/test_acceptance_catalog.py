from finance_assurance.digestion.acceptance import (
    ACCEPTANCE_CATALOG,
    validate_catalog,
)


def test_r_acceptance_catalog_is_closed_and_traceable() -> None:
    validate_catalog()

    assert len(ACCEPTANCE_CATALOG) == 48
    assert tuple(item.criterion_id for item in ACCEPTANCE_CATALOG) == tuple(
        f"R-A{number:02d}" for number in range(1, 49)
    )
    assert all(item.evidence_tests for item in ACCEPTANCE_CATALOG)
