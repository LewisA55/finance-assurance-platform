"""Application contracts for the governed Silver and Gold finance model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FinanceModelBuildRequest:
    """Build one governed analytical warehouse profile over an A2.4 authority."""

    source_package_path: Path
    output_path: Path
    expected_source_digest: str
    built_at: str
    model_ref: str = "Q-FINANCE-B1@v1"

    def validate(self) -> None:
        if not self.model_ref or not self.model_ref.isascii():
            raise ValueError("model_ref must be non-empty ASCII text")
        if not self.expected_source_digest.startswith("sha256:"):
            raise ValueError("expected_source_digest must be a SHA-256 reference")
        if not self.built_at.endswith("Z"):
            raise ValueError("built_at must be a UTC timestamp ending in Z")
        source = self.source_package_path.resolve()
        output = self.output_path.resolve()
        if output == source or source in output.parents:
            raise ValueError("finance-model output cannot be inside its source package")


@dataclass(frozen=True)
class FinanceModelBuildResult:
    """Stable result returned after a successful governed model build."""

    model_ref: str
    source_data_ref: str
    source_package_digest: str
    package_digest: str
    model_semantic_digest: str
    output_path: Path
    silver_model_count: int
    gold_dataset_count: int
    governance_model_count: int
    dbt_test_count: int
    independent_control_count: int
    status: str = "PUBLISHED"


@dataclass(frozen=True)
class FinanceModelVerifyRequest:
    """Verify one governed model package against its exact A2.4 authority."""

    source_package_path: Path
    package_path: Path
    expected_source_digest: str
    expected_package_digest: str | None = None


@dataclass(frozen=True)
class FinanceModelVerifyResult:
    """Stable result returned by the independent logical verifier."""

    model_ref: str
    source_data_ref: str
    source_package_digest: str
    package_digest: str
    model_semantic_digest: str
    checked_model_count: int
    checked_gold_dataset_count: int
    checked_dbt_test_count: int
    checked_control_count: int
    status: str = "VERIFIED"
