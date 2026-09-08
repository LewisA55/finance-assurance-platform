from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from finance_assurance.pythia import (
    PythiaBuildRequest,
    PythiaService,
    PythiaVerifyRequest,
)

ROOT = Path(__file__).resolve().parents[2]
DELIVERY = ROOT / "build" / "finance-delivery" / "Q-FINANCE-C2-V1"


def _delivery_digest() -> str:
    return (DELIVERY / "finance-delivery.digest").read_text(encoding="ascii").strip()


def test_pythia_build_executes_governed_integrated_forecast(tmp_path: Path) -> None:
    output = tmp_path / "PYTHIA-D6-V1"
    service = PythiaService()
    result = service.build(
        PythiaBuildRequest(
            contract_version="pythia-d6-build-request@v1",
            pythia_ref="PYTHIA-D6@v1",
            finance_delivery_path=DELIVERY,
            expected_finance_delivery_digest=_delivery_digest(),
            output_path=output,
            built_at="2026-08-26T12:00:00Z",
            producer_release="0.1.0",
        )
    )
    assert result.status == "PUBLISHED"
    assert result.forecast_row_count == 360
    assert result.sensitivity_row_count == 75

    forecast = pq.read_table(output / "parquet" / "fct_pythia_forecast_monthly.parquet")
    assert forecast.num_rows == 360
    assert set(forecast.column("scenario_code").to_pylist()) == {"BASE", "BULL", "BEAR"}
    assert set(forecast.column("balance_sheet_difference_minor").to_pylist()) == {0}
    assert set(forecast.column("cash_rollforward_difference_minor").to_pylist()) == {0}

    scenarios = pq.read_table(
        output / "parquet" / "dim_pythia_scenario.parquet"
    ).to_pylist()
    assert {row["finance_delivery_digest"] for row in scenarios} == {
        _delivery_digest()
    }

    controls = json.loads(
        (output / "metadata" / "assumptions.json").read_text(encoding="utf-8")
    )
    assert controls["actuals_reporting_version_ref"] == "RV-NEXUS-GROUP-2026-06@v1"

    verified = service.verify(
        PythiaVerifyRequest(
            contract_version="pythia-d6-verify-request@v1",
            package_path=output,
            finance_delivery_path=DELIVERY,
            expected_pythia_digest=result.pythia_digest,
            expected_finance_delivery_digest=_delivery_digest(),
        )
    )
    assert verified.status == "VERIFIED"
    assert verified.checked_forecast_row_count == 360


def test_pythia_keeps_approval_and_valuation_boundaries(tmp_path: Path) -> None:
    output = tmp_path / "PYTHIA-D6-V1"
    result = PythiaService().build(
        PythiaBuildRequest(
            contract_version="pythia-d6-build-request@v1",
            pythia_ref="PYTHIA-D6@v1",
            finance_delivery_path=DELIVERY,
            expected_finance_delivery_digest=_delivery_digest(),
            output_path=output,
            built_at="2026-08-26T12:00:00Z",
            producer_release="0.1.0",
        )
    )
    assert result.control_count == 11
    scenarios = pq.read_table(output / "parquet" / "dim_pythia_scenario.parquet").to_pylist()
    assert next(row for row in scenarios if row["scenario_code"] == "BASE")[
        "pythia_result_status"
    ] == "APPROVED_FORECAST_RESULT"
    assert all(
        row["pythia_result_status"] == "DRAFT_SCENARIO_RESULT"
        for row in scenarios
        if row["scenario_code"] != "BASE"
    )
    valuations = pq.read_table(output / "parquet" / "mart_pythia_valuation.parquet").to_pylist()
    valuation_by_scenario = {row["scenario_code"]: row for row in valuations}
    assert valuation_by_scenario["BULL"]["valuation_status"] == "READY"
    assert valuation_by_scenario["BULL"]["terminal_value_minor"] is not None
    assert valuation_by_scenario["BULL"]["pythia_result_status"] == "DRAFT_SCENARIO_RESULT"
    for code in ("BASE", "BEAR"):
        assert valuation_by_scenario[code]["valuation_status"] == "BLOCKED_NEGATIVE_TERMINAL_FCF"
        assert valuation_by_scenario[code]["terminal_value_minor"] is None
    sensitivity = pq.read_table(
        output / "parquet" / "mart_pythia_dcf_sensitivity.parquet"
    ).to_pylist()
    assert sum(row["valuation_status"] == "READY" for row in sensitivity) == 25
