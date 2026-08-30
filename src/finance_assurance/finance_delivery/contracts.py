"""Strict public contracts for the Q-FINANCE C2 consumer delivery."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class FinanceDeliveryContract(BaseModel):
    """Closed immutable consumer-delivery wire model."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class FinanceDeliveryBuildRequest(FinanceDeliveryContract):
    contract_version: Literal["q-finance-c2-build-request@v1"]
    delivery_ref: Literal["Q-FINANCE-C2@v1"]
    finance_model_package_path: Path
    source_data_package_path: Path
    expected_finance_model_digest: str
    expected_source_data_digest: str
    output_path: Path
    workbook_output_path: Path
    preview_output_path: Path
    built_at: str
    producer_release: str

    @field_validator(
        "expected_finance_model_digest", "expected_source_data_digest"
    )
    @classmethod
    def digest_shape(cls, value: str) -> str:
        if len(value) != 71 or not value.startswith("sha256:"):
            raise ValueError("expected digest must be one canonical SHA-256 value")
        return value


class FinanceDeliveryBuildResult(FinanceDeliveryContract):
    contract_version: Literal["q-finance-c2-build-result@v1"]
    status: Literal["PUBLISHED"]
    delivery_ref: Literal["Q-FINANCE-C2@v1"]
    output_path: Path
    workbook_output_path: Path
    delivery_digest: str
    finance_model_digest: str
    model_semantic_digest: str
    source_data_digest: str
    mart_count: int
    conformed_dimension_count: int
    delivered_table_count: int
    mart_row_count: int
    delivered_row_count: int
    react_parquet_file_count: int
    powerbi_parquet_file_count: int
    csv_file_count: int
    powerbi_relationship_count: int
    powerbi_measure_count: int
    workbook_sheet_count: int
    workbook_data_sheet_count: int
    validation_control_count: int


class FinanceDeliveryVerifyRequest(FinanceDeliveryContract):
    contract_version: Literal["q-finance-c2-verify-request@v1"]
    delivery_path: Path
    finance_model_package_path: Path
    source_data_package_path: Path
    expected_delivery_digest: str
    expected_finance_model_digest: str
    expected_source_data_digest: str

    @field_validator(
        "expected_delivery_digest",
        "expected_finance_model_digest",
        "expected_source_data_digest",
    )
    @classmethod
    def digest_shape(cls, value: str) -> str:
        if len(value) != 71 or not value.startswith("sha256:"):
            raise ValueError("expected digest must be one canonical SHA-256 value")
        return value


class FinanceDeliveryVerifyResult(FinanceDeliveryContract):
    contract_version: Literal["q-finance-c2-verify-result@v1"]
    status: Literal["VERIFIED"]
    delivery_ref: Literal["Q-FINANCE-C2@v1"]
    delivery_digest: str
    finance_model_digest: str
    model_semantic_digest: str
    source_data_digest: str
    checked_file_count: int
    checked_table_count: int
    checked_row_count: int
    checked_reconciliation_count: int
    checked_workbook_sheet_count: int
    canonical_bytes_status: Literal["VERIFIED"]
    parquet_replay_status: Literal["VERIFIED"]
    csv_replay_status: Literal["VERIFIED"]
    workbook_replay_status: Literal["VERIFIED"]
