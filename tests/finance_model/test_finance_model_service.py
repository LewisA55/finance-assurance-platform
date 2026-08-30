"""Focused smoke checks for the recovered finance-model package."""

from finance_assurance.finance_model.service import FinanceModelService


def test_finance_model_service_is_available() -> None:
    assert FinanceModelService is not None
