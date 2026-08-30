"""Strict contracts for governed Pythia scenario execution."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class PythiaContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class PythiaBuildRequest(PythiaContract):
    contract_version: Literal["pythia-d6-build-request@v1"]
    pythia_ref: Literal["PYTHIA-D6@v1"]
    finance_delivery_path: Path
    expected_finance_delivery_digest: str
    output_path: Path
    built_at: str
    producer_release: str

    @field_validator("expected_finance_delivery_digest")
    @classmethod
    def digest_shape(cls, value: str) -> str:
        if len(value) != 71 or not value.startswith("sha256:"):
            raise ValueError("expected digest must be one canonical SHA-256 value")
        return value


class PythiaBuildResult(PythiaContract):
    contract_version: Literal["pythia-d6-build-result@v1"]
    status: Literal["PUBLISHED"]
    pythia_ref: Literal["PYTHIA-D6@v1"]
    output_path: Path
    pythia_digest: str
    finance_delivery_digest: str
    actuals_reporting_version_ref: str
    scenario_count: int
    forecast_month_count: int
    forecast_row_count: int
    valuation_row_count: int
    sensitivity_row_count: int
    control_count: int


class PythiaVerifyRequest(PythiaContract):
    contract_version: Literal["pythia-d6-verify-request@v1"]
    package_path: Path
    finance_delivery_path: Path
    expected_pythia_digest: str
    expected_finance_delivery_digest: str

    @field_validator("expected_pythia_digest", "expected_finance_delivery_digest")
    @classmethod
    def digest_shape(cls, value: str) -> str:
        if len(value) != 71 or not value.startswith("sha256:"):
            raise ValueError("expected digest must be one canonical SHA-256 value")
        return value


class PythiaVerifyResult(PythiaContract):
    contract_version: Literal["pythia-d6-verify-result@v1"]
    status: Literal["VERIFIED"]
    pythia_ref: Literal["PYTHIA-D6@v1"]
    pythia_digest: str
    finance_delivery_digest: str
    checked_file_count: int
    checked_scenario_count: int
    checked_forecast_row_count: int
    checked_control_count: int
