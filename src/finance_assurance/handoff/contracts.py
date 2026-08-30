"""Strict public operation contracts for Artifact S."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from finance_assurance.runtime.contracts.primitives import (
    AsciiString,
    HashValue,
    NonNegativeInt,
    PositiveInt,
    Timestamp,
)

Operation = Literal["S-C01", "S-C02", "S-C03"]
FailureCode = Literal[
    "INVALID_REQUEST",
    "SOURCE_PACKAGE_UNAVAILABLE",
    "SOURCE_PACKAGE_VERIFICATION_FAILED",
    "MODEL_VERIFICATION_FAILED",
    "R3_CACHE_INVALID",
    "PATH_FIREWALL_VIOLATION",
    "INVENTORY_MISMATCH",
    "SOURCE_CHANGED_DURING_COPY",
    "METADATA_DERIVATION_MISMATCH",
    "VALIDATION_REGISTRY_MISMATCH",
    "SQL_REGISTRY_MISMATCH",
    "XLSX_PROFILE_UNAVAILABLE",
    "XLSX_CAPACITY_EXCEEDED",
    "XLSX_STRUCTURE_INVALID",
    "XLSX_LOGICAL_MISMATCH",
    "NONCANONICAL_BINARY_MISMATCH",
    "OUTPUT_OCCUPIED",
    "ATOMIC_PUBLICATION_FAILED",
    "DIGEST_MISMATCH",
    "BUILD_FAILED",
]
FailurePhase = Literal[
    "PRECHECK",
    "SOURCE_VERIFY",
    "STAGE",
    "COPY",
    "DERIVE",
    "XLSX",
    "SEAL",
    "VERIFY",
    "PUBLISH",
    "REPRODUCE",
]
ClaimStatus = Literal["VERIFIED", "FAILED", "NOT_CHECKED"]
SourcePathState = Literal["UNCHANGED", "NOT_APPLICABLE", "NOT_CHECKED"]
OutputPathState = Literal["ABSENT", "PREEXISTING_UNCHANGED", "NOT_APPLICABLE"]


class HandoffContractModel(BaseModel):
    """Closed immutable Artifact S wire model."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class BuildLocalAnalyticalHandoff(HandoffContractModel):
    request_contract_version: Literal["build-local-analytical-handoff-request@v1"]
    handoff_ref: AsciiString
    source_model_path: Path
    source_package_path: Path
    expected_model_digest: HashValue
    expected_source_package_digest: HashValue
    required_profile_id: Literal["LINEAGE"]
    required_profile_version: Literal[1]
    required_formats: tuple[Literal["CSV", "PARQUET", "DUCKDB"], ...]
    output_path: Path
    producer_release: AsciiString
    built_at: Timestamp
    xlsx_type_map_ref: Literal["XLSX-TYPE-MAP@v1"]
    xlsx_type_map_hash: Literal[
        "sha256:41b42f86d6620e042e1137b352fee44018ecfa34b980fb4bca4f33eeb71e48dd"
    ]
    xlsx_writer_profile_ref: Literal["XLSXWRITER-3.2.9@v1"]
    xlsx_writer_profile_hash: Literal[
        "sha256:1a7dc795c0f09c22db462051c1190cf8b86dea7f03c6e79b4990fa1637c15f76"
    ]
    validation_registry_ref: Literal["S-VALIDATION-C001-CT1@v1"]
    validation_registry_hash: Literal[
        "sha256:36255992b12b0176f290ec2fa033e5655d8ca4b3a2e4cbd3a522a1de295f7cb8"
    ]

    @model_validator(mode="after")
    def exact_source_shape(self) -> BuildLocalAnalyticalHandoff:
        if self.required_formats != ("CSV", "PARQUET", "DUCKDB"):
            raise ValueError("required formats must be exact CSV, Parquet, DuckDB")
        return self


class BuildLocalAnalyticalHandoffResult(HandoffContractModel):
    result_contract_version: Literal["build-local-analytical-handoff-result@v1"]
    status: Literal["PUBLISHED"]
    handoff_ref: AsciiString
    handoff_path: Path
    handoff_digest: HashValue
    source_model_ref: AsciiString
    source_model_digest: HashValue
    source_package_digest: HashValue
    canonical_file_count: PositiveInt
    noncanonical_file_count: PositiveInt
    table_count: PositiveInt
    source_row_count: NonNegativeInt
    catalogue_column_count: PositiveInt
    relationship_count: PositiveInt
    measure_count: PositiveInt
    validation_check_count: PositiveInt
    workbook_logical_digest: HashValue
    checked_sheet_count: PositiveInt


class VerifyLocalAnalyticalHandoff(HandoffContractModel):
    request_contract_version: Literal["verify-local-analytical-handoff-request@v1"]
    handoff_path: Path
    source_package_path: Path
    expected_handoff_digest: HashValue
    expected_model_digest: HashValue
    expected_source_package_digest: HashValue
    verification_scope: Literal["FULL_HANDOFF_EQUIVALENCE"]


class VerifyLocalAnalyticalHandoffResult(HandoffContractModel):
    result_contract_version: Literal["verify-local-analytical-handoff-result@v1"]
    status: Literal["VERIFIED"]
    handoff_digest: HashValue
    source_model_digest: HashValue
    source_package_digest: HashValue
    checked_canonical_file_count: PositiveInt
    checked_noncanonical_file_count: PositiveInt
    checked_table_count: PositiveInt
    checked_column_count: PositiveInt
    checked_relationship_count: PositiveInt
    checked_measure_count: PositiveInt
    checked_validation_count: PositiveInt
    checked_sheet_count: PositiveInt
    canonical_byte_status: Literal["VERIFIED"]
    same_build_binary_status: Literal["VERIFIED"]
    logical_equivalence_status: Literal["VERIFIED"]


class ReproduceLocalAnalyticalHandoff(HandoffContractModel):
    request_contract_version: Literal[
        "reproduce-local-analytical-handoff-request@v1"
    ]
    source_handoff_path: Path
    source_package_path: Path
    reproduction_output_path: Path
    expected_handoff_digest: HashValue
    expected_model_digest: HashValue
    expected_source_package_digest: HashValue


class ReproduceLocalAnalyticalHandoffResult(HandoffContractModel):
    result_contract_version: Literal[
        "reproduce-local-analytical-handoff-result@v1"
    ]
    status: Literal["REPRODUCED"]
    expected_handoff_digest: HashValue
    source_handoff_digest: HashValue
    reproduced_handoff_digest: HashValue
    expected_model_digest: HashValue
    actual_model_digest: HashValue
    expected_source_package_digest: HashValue
    actual_source_package_digest: HashValue
    reproduced_handoff_path: Path
    canonical_byte_status: Literal["VERIFIED"]
    duckdb_logical_status: Literal["VERIFIED"]
    xlsx_logical_status: Literal["VERIFIED"]

    @model_validator(mode="after")
    def all_reproduction_digests_match(
        self,
    ) -> ReproduceLocalAnalyticalHandoffResult:
        if not (
            self.source_handoff_digest
            == self.reproduced_handoff_digest
            == self.expected_handoff_digest
        ):
            raise ValueError("handoff reproduction digests must all match")
        if self.actual_model_digest != self.expected_model_digest:
            raise ValueError("reproduced model digest does not match")
        if self.actual_source_package_digest != self.expected_source_package_digest:
            raise ValueError("reproduced source package digest does not match")
        return self


class HandoffOperationFailure(HandoffContractModel):
    failure_contract_version: Literal["handoff-operation-failure@v2"]
    operation: Operation
    failure_code: FailureCode
    failure_phase: FailurePhase
    failure_checkpoint: AsciiString
    message: AsciiString
    expected_handoff_digest: HashValue | None
    actual_handoff_digest: HashValue | None
    expected_model_digest: HashValue | None
    actual_model_digest: HashValue | None
    expected_source_package_digest: HashValue | None
    actual_source_package_digest: HashValue | None
    canonical_byte_status: ClaimStatus
    same_build_binary_status: ClaimStatus
    logical_equivalence_status: ClaimStatus
    staging_removed: bool
    source_package_path_state: SourcePathState
    source_model_path_state: SourcePathState
    source_handoff_path_state: SourcePathState
    output_path_state: OutputPathState

    @model_validator(mode="after")
    def failure_is_one_exact_admission(self) -> HandoffOperationFailure:
        from finance_assurance.handoff.failure_registry import FAILURE_REGISTRY

        FAILURE_REGISTRY.validate_failure(self)
        return self
