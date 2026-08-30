"""Strict Artifact P package, discovery, and verification contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, model_validator

from finance_assurance.product.contracts import PublicContractModel
from finance_assurance.product.query_models import PublicQuery
from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.contracts.primitives import (
    AsciiString,
    HashValue,
    NonNegativeInt,
    PositiveInt,
    Timestamp,
)


class ExportContractModel(PublicContractModel):
    """Closed immutable model owned by the Artifact P boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ExpectedEntryPoint(ExportContractModel):
    scenario_ref: AsciiString
    journey_id: Literal["O-J01", "O-J02", "O-J03", "O-SJ01"]
    semantic_role: AsciiString
    exact_ref: AsciiString
    source_kind: Literal[
        "AUTHORITATIVE_RECORD",
        "CONTRACT_PUBLICATION",
        "LABELLED_PROJECTION",
    ]
    availability: Literal["AVAILABLE", "UNAVAILABLE"]


class ExportScenarioDescriptor(ExportContractModel):
    scenario_ref: AsciiString
    canonical_family: Literal["C-001", "CT-1"]
    public_role: AsciiString
    query_requests: tuple[PublicQuery, ...]
    expected_entry_points: tuple[ExpectedEntryPoint, ...]

    @model_validator(mode="after")
    def requests_belong_to_scenario(self) -> ExportScenarioDescriptor:
        if not self.query_requests:
            raise ValueError("a scenario descriptor requires query requests")
        if any(
            str(item.scenario_ref) != self.scenario_ref
            for item in self.query_requests
        ):
            raise ValueError("every query request must belong to its scenario descriptor")
        if any(
            item.scenario_ref != self.scenario_ref
            for item in self.expected_entry_points
        ):
            raise ValueError("every entry point must belong to its scenario descriptor")
        if any(
            str(item.semantic_as_of_time)
            != str(self.query_requests[0].semantic_as_of_time)
            for item in self.query_requests
        ):
            raise ValueError("scenario query requests must share one semantic time")
        return self


class ExportDiscoveryDescriptor(ExportContractModel):
    discovery_contract_version: Literal[1]
    discovery_descriptor_ref: AsciiString
    workspace_ref: AsciiString
    semantic_as_of: Timestamp
    scenario_descriptors: tuple[ExportScenarioDescriptor, ...]

    @model_validator(mode="after")
    def scenario_set_is_closed(self) -> ExportDiscoveryDescriptor:
        families = tuple(item.canonical_family for item in self.scenario_descriptors)
        if families != ("C-001", "CT-1"):
            raise ValueError("P-Q00 requires the ordered C-001 and CT-1 scenario set")
        refs = tuple(item.scenario_ref for item in self.scenario_descriptors)
        if len(refs) != len(set(refs)):
            raise ValueError("scenario references must be unique")
        if any(
            str(query.semantic_as_of_time) != str(self.semantic_as_of)
            for scenario in self.scenario_descriptors
            for query in scenario.query_requests
        ):
            raise ValueError("all discovery queries must share semantic_as_of")
        return self

    @property
    def descriptor_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))


class DiscoveryScenario(ExportContractModel):
    scenario_ref: AsciiString
    canonical_family: Literal["C-001", "CT-1"]
    public_role: AsciiString


class OwnedQueryRequest(ExportContractModel):
    scenario_ref: AsciiString
    request: PublicQuery


class ExportDiscoveryView(ExportContractModel):
    view_contract: Literal["P-V00"]
    view_contract_version: Literal[1]
    workspace_ref: AsciiString
    discovery_descriptor_ref: AsciiString
    discovery_descriptor_hash: HashValue
    query_revision: NonNegativeInt
    semantic_as_of: Timestamp
    compatibility_mode: Literal["EXACT_ORIGINAL"]
    scenario_set_digest: HashValue
    scenarios: tuple[DiscoveryScenario, ...]
    query_requests: tuple[OwnedQueryRequest, ...]
    entry_points: tuple[ExpectedEntryPoint, ...]


class BuildGovernedExport(ExportContractModel):
    export_ref: AsciiString
    workspace_ref: AsciiString
    semantic_as_of: Timestamp
    exported_at: Timestamp
    output_path: Path
    discovery_descriptor_ref: AsciiString
    contract_version: Literal["governed-export-package@v1"]


class BuildGovernedExportResult(ExportContractModel):
    export_ref: AsciiString
    package_path: Path
    package_digest: HashValue
    query_revision: NonNegativeInt
    semantic_as_of: Timestamp
    dataset_count: PositiveInt
    row_count: NonNegativeInt


VerificationStatus = Literal[
    "VERIFIED",
    "MISSING_FILE",
    "UNREGISTERED_FILE",
    "HASH_MISMATCH",
    "PACKAGE_DIGEST_MISMATCH",
    "SCHEMA_INVALID",
    "ROW_INVALID",
    "KEY_VIOLATION",
    "RELATIONSHIP_VIOLATION",
    "SNAPSHOT_MISMATCH",
    "UNSUPPORTED_CONTRACT",
    "UNSUPPORTED_COMPATIBILITY_MODE",
]


class VerificationResult(ExportContractModel):
    status: VerificationStatus
    package_path: Path
    package_digest: HashValue | None = None
    checked_file_count: NonNegativeInt = 0
    checked_dataset_count: NonNegativeInt = 0
    message: AsciiString


class ReproductionResult(ExportContractModel):
    status: Literal[
        "REPRODUCED",
        "DIGEST_MISMATCH",
        "SOURCE_REVISION_UNAVAILABLE",
        "BUILD_FAILED",
    ]
    expected_digest: HashValue
    actual_digest: HashValue | None
    query_revision: NonNegativeInt | None
    message: AsciiString


class DatasetRegistryEntry(ExportContractModel):
    registry_id: Literal["P-EVIDENCE", "Q-ANALYTICS"]
    registry_version: Literal[1]
    storage_key: Literal["p-evidence-v1", "q-analytics-v1"]
    dataset_ids: tuple[AsciiString, ...]
    registry_contract_hash: HashValue

    @model_validator(mode="after")
    def registry_coordinate_is_closed(self) -> DatasetRegistryEntry:
        expected_storage = {
            "P-EVIDENCE": "p-evidence-v1",
            "Q-ANALYTICS": "q-analytics-v1",
        }
        if self.storage_key != expected_storage[self.registry_id]:
            raise ValueError("registry_id and storage_key do not form a closed pair")
        return self


class DatasetManifestEntry(ExportContractModel):
    dataset_id: AsciiString
    dataset_version: Literal[1]
    registry_id: Literal["P-EVIDENCE", "Q-ANALYTICS"]
    export_steward: AsciiString
    semantic_owners: tuple[AsciiString, ...]
    relative_path: AsciiString
    schema_path: AsciiString
    row_count: NonNegativeInt
    data_sha256: HashValue
    schema_sha256: HashValue
    source_query_ids: tuple[AsciiString, ...]
    source_view_ids: tuple[AsciiString, ...]
    semantic_source_refs: tuple[AsciiString, ...]


class GovernedExportManifest(ExportContractModel):
    contract_version: Literal["governed-export-package@v1"]
    export_ref: AsciiString
    workspace_ref: AsciiString
    discovery_descriptor_ref: AsciiString
    discovery_descriptor_hash: HashValue
    runtime_release: AsciiString
    query_revision: NonNegativeInt
    semantic_as_of: Timestamp
    exported_at: Timestamp
    compatibility_mode: Literal["EXACT_ORIGINAL"]
    synthetic_data: Literal[True]
    synthetic_data_notice: AsciiString
    scenario_refs: tuple[AsciiString, ...]
    scenario_set_digest: HashValue
    authoritative_inventory_digest: HashValue
    projection_generation_ref: AsciiString
    dataset_entries: tuple[DatasetManifestEntry, ...]
    dataset_registries: tuple[DatasetRegistryEntry, ...]
    relationship_contract_version: Literal[1, 2]
    producer_release: AsciiString


class ChecksumEntry(ExportContractModel):
    relative_path: AsciiString
    sha256: HashValue


class ChecksumLedger(ExportContractModel):
    checksum_contract_version: Literal[1]
    files: tuple[ChecksumEntry, ...]
