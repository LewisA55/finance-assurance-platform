from finance_assurance.analytics.acceptance import ACCEPTANCE_CATALOG, validate_catalog


def test_artifact_q_acceptance_catalog_is_closed() -> None:
    validate_catalog()

    assert len(ACCEPTANCE_CATALOG) == 45
    assert tuple(item.criterion_id for item in ACCEPTANCE_CATALOG) == tuple(
        f"Q-A{number:02d}" for number in range(1, 46)
    )
    assert all(item.evidence_tests for item in ACCEPTANCE_CATALOG)
