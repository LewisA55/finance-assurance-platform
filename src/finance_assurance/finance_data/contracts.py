"""Application contracts for the finance data substrate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

SUPPORTED_SCALE_PROFILES = ("SMOKE", "PORTFOLIO", "FULL")
SUPPORTED_STATUTORY_CONTRACT_VERSIONS = ("A2.3", "A2.4")


@dataclass(frozen=True)
class ScaleProfile:
    """Deterministic population-size parameters."""

    profile_id: str
    customer_count: int
    vendor_count: int
    employee_count: int
    monthly_invoice_share_pct: int
    payment_success_pct: int


SCALE_PROFILES = {
    "SMOKE": ScaleProfile(
        profile_id="SMOKE",
        customer_count=24,
        vendor_count=12,
        employee_count=36,
        monthly_invoice_share_pct=80,
        payment_success_pct=94,
    ),
    "PORTFOLIO": ScaleProfile(
        profile_id="PORTFOLIO",
        customer_count=1_000,
        vendor_count=120,
        employee_count=450,
        monthly_invoice_share_pct=88,
        payment_success_pct=95,
    ),
    "FULL": ScaleProfile(
        profile_id="FULL",
        customer_count=2_500,
        vendor_count=300,
        employee_count=900,
        monthly_invoice_share_pct=90,
        payment_success_pct=96,
    ),
}


@dataclass(frozen=True)
class FinanceDataBuildRequest:
    """Build one deterministic source-plus-Bronze package."""

    data_ref: str
    output_path: Path
    built_at: str
    scale_profile: str = "PORTFOLIO"
    seed: int = 42
    history_start: date = date(2021, 1, 1)
    actuals_end: date = date(2026, 6, 30)
    reporting_currency: str = "GBP"
    statutory_contract_version: str = "A2.4"

    def validate(self) -> None:
        if not self.data_ref or not self.data_ref.isascii():
            raise ValueError("data_ref must be non-empty ASCII text")
        if self.scale_profile not in SUPPORTED_SCALE_PROFILES:
            raise ValueError("scale_profile is not supported")
        if self.history_start.day != 1:
            raise ValueError("history_start must be the first day of a month")
        if self.actuals_end < self.history_start:
            raise ValueError("actuals_end precedes history_start")
        if len(self.reporting_currency) != 3 or not self.reporting_currency.isalpha():
            raise ValueError("reporting_currency must be a three-letter code")
        if not self.built_at.endswith("Z"):
            raise ValueError("built_at must be a UTC timestamp ending in Z")
        if (
            self.statutory_contract_version
            not in SUPPORTED_STATUTORY_CONTRACT_VERSIONS
        ):
            raise ValueError("statutory_contract_version is not supported")


@dataclass(frozen=True)
class FinanceDataBuildResult:
    """Stable result returned by a successful package build."""

    data_ref: str
    output_path: Path
    package_digest: str
    scale_profile: str
    dataset_count: int
    source_row_count: int
    bronze_table_count: int
    defect_count: int
    history_month_count: int
    status: str = "PUBLISHED"


@dataclass(frozen=True)
class FinanceDataVerifyResult:
    """Stable result returned by independent package verification."""

    data_ref: str
    package_digest: str
    checked_dataset_count: int
    checked_source_row_count: int
    checked_bronze_table_count: int
    checked_defect_count: int
    status: str = "VERIFIED"


@dataclass(frozen=True)
class FinanceDataReproduceRequest:
    """Rebuild one sealed package from its own canonical request metadata."""

    source_package_path: Path
    reproduction_output_path: Path
    expected_digest: str | None = None


@dataclass(frozen=True)
class FinanceDataReproduceResult:
    """Canonical-source and logical-Bronze reproduction result."""

    data_ref: str
    source_package_digest: str
    reproduced_package_digest: str
    canonical_file_count: int
    checked_dataset_count: int
    checked_source_row_count: int
    checked_bronze_table_count: int
    reproduction_output_path: Path
    status: str = "REPRODUCED"
