"""Strict contracts for Artifact R's model-digestion boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.contracts.primitives import (
    AsciiString,
    HashValue,
    NonNegativeInt,
    PositiveInt,
    Timestamp,
)

RegistryId = Literal["P-EVIDENCE", "Q-ANALYTICS"]
ProfileId = Literal["CORE", "LINEAGE", "DIAGNOSTIC"]
PhysicalFormat = Literal["CSV", "PARQUET", "DUCKDB"]
DuckDBStorageCompatibilityVersion = Literal["v1.5.0"]
SourceType = Literal["text", "enum", "integer", "boolean", "date", "timestamp", "hash"]
PhysicalType = Literal[
    "UTF8",
    "INT64",
    "BOOLEAN",
    "DATE32",
    "TIMESTAMP_US_UTC",
]

# The complete future R2 writer option preset is independently hashed in R1.
# Including that digest in the profile-hash preimage prevents an option change
# from retaining the same advertised writer profile.
PINNED_PYARROW_OPTIONS_HASH = (
    "sha256:2642b3ea3f71badfff44760005b01ed1f80f9a571d823dc99fa6ef78f432b862"
)
PINNED_PARQUET_PROFILE_HASH = (
    "sha256:2702aa8812844e508d5b303c50b52e30ab9f20cf7b65c42c2d59f39171b85cb1"
)
ColumnRole = Literal[
    "DOMAIN_KEY",
    "DOMAIN_ATTRIBUTE",
    "DOMAIN_MEASURE_INPUT",
    "EVIDENCE_ATTRIBUTE",
    "SOURCE_TECHNICAL",
    "R_TECHNICAL",
]
Visibility = Literal["VISIBLE", "HIDDEN", "NOT_LOADED"]
LoadDisposition = Literal[
    "ACTIVE",
    "INACTIVE_ROLE_PLAYING",
    "NAVIGATION_ONLY",
    "VALIDATION_ONLY",
]
MeasureClass = Literal[
    "EXACT_VALUE",
    "ADDITIVE_GOVERNED_TOTAL",
    "CONSUMER_CALCULATION",
]


class DigestionContractModel(BaseModel):
    """Closed immutable model owned by Artifact R."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class RegistryCoordinate(DigestionContractModel):
    registry_id: RegistryId
    registry_version: Literal[1]


class ProfileCoordinate(DigestionContractModel):
    profile_id: ProfileId
    profile_version: Literal[1]


class DatasetCoordinate(DigestionContractModel):
    registry_id: RegistryId
    registry_version: Literal[1]
    dataset_id: AsciiString
    dataset_version: Literal[1]


class RelationshipKeyProjection(DigestionContractModel):
    relationship_id: AsciiString
    technical_column_name: AsciiString
    from_coordinate: DatasetCoordinate
    from_columns: tuple[AsciiString, ...]
    from_types: tuple[SourceType, ...]
    to_coordinate: DatasetCoordinate
    to_columns: tuple[AsciiString, ...]
    to_types: tuple[SourceType, ...]
    role: Literal["R_TECHNICAL"]
    visibility: Literal["HIDDEN"]

    @model_validator(mode="after")
    def endpoint_shapes_match(self) -> RelationshipKeyProjection:
        widths = {
            len(self.from_columns),
            len(self.from_types),
            len(self.to_columns),
            len(self.to_types),
        }
        if len(widths) != 1 or len(self.from_columns) < 2:
            raise ValueError("composite relationship endpoints must have equal width")
        if self.from_types != self.to_types:
            raise ValueError("composite relationship endpoint types must match")
        expected = f"_r_hk_{self.relationship_id.lower().replace('-', '_')}"
        if self.technical_column_name != expected:
            raise ValueError("technical relationship-key name is not canonical")
        return self


class RelationshipPlanEntry(DigestionContractModel):
    relationship_id: AsciiString
    relationship_type: Literal["STANDARD", "POLYMORPHIC_PARENT"]
    enforcement: Literal["CONSUMER_RELATIONSHIP", "INTEGRITY_ONLY"]
    from_registry: RegistryId
    from_dataset: AsciiString
    from_columns: tuple[AsciiString, ...]
    to_registry: RegistryId | None = None
    to_dataset: AsciiString | None = None
    to_columns: tuple[AsciiString, ...] = ()
    allowed_target_coordinates: tuple[DatasetCoordinate, ...] = ()
    load_disposition: LoadDisposition
    relationship_role: AsciiString
    projected_key_ref: AsciiString | None = None
    cross_filter_direction: Literal["ONE_TO_MANY", "NONE"]
    consumer_reason: AsciiString

    @model_validator(mode="after")
    def relationship_variant_is_closed(self) -> RelationshipPlanEntry:
        if self.relationship_type == "STANDARD":
            if self.to_registry is None or self.to_dataset is None:
                raise ValueError("standard relationships require one exact target")
            if not self.from_columns or not self.to_columns:
                raise ValueError("standard relationships require endpoint columns")
            if self.allowed_target_coordinates:
                raise ValueError("standard relationships cannot carry allowed targets")
        else:
            if self.to_registry is not None or self.to_dataset is not None:
                raise ValueError("polymorphic relationships cannot carry one target")
            if self.from_columns or self.to_columns:
                raise ValueError("polymorphic endpoint columns use upstream selectors")
            if not self.allowed_target_coordinates:
                raise ValueError("polymorphic relationships require allowed targets")
        if self.load_disposition == "ACTIVE":
            if self.enforcement != "CONSUMER_RELATIONSHIP":
                raise ValueError("only consumer relationships may be active")
            if self.cross_filter_direction != "ONE_TO_MANY":
                raise ValueError("active relationships require one-to-many filtering")
        elif self.cross_filter_direction != "NONE":
            raise ValueError("non-active relationships cannot filter")
        return self


class ColumnSemantic(DigestionContractModel):
    source_coordinate: DatasetCoordinate
    source_name: AsciiString
    source_type: SourceType
    physical_type: PhysicalType
    nullable: bool
    enum_values: tuple[AsciiString, ...]
    value_origin: AsciiString
    transformation: AsciiString
    column_role: ColumnRole
    default_visibility: Visibility
    default_summarization: Literal["NONE"]
    display_label: AsciiString
    display_folder: AsciiString | None = None

    @model_validator(mode="after")
    def enum_and_visibility_are_closed(self) -> ColumnSemantic:
        if self.source_type == "enum" and not self.enum_values:
            raise ValueError("enum columns require the exact source enum set")
        if self.source_type != "enum" and self.enum_values:
            raise ValueError("only source enum columns may carry enum values")
        if self.default_visibility == "NOT_LOADED":
            raise ValueError("R v1 source columns cannot be NOT_LOADED")
        return self


class MeasureDefinition(DigestionContractModel):
    measure_id: AsciiString
    measure_name: AsciiString
    source_registry_id: RegistryId
    source_dataset_id: AsciiString
    source_field: AsciiString
    classification: MeasureClass
    aggregation: Literal["SELECT_EXACT", "SUM"]
    required_grain: tuple[AsciiString, ...]
    required_grouping: tuple[AsciiString, ...]
    currency_policy: Literal["SINGLE_EXACT_CURRENCY"]
    reporting_version_policy: Literal[
        "NONE",
        "EXACT_REPORTING_VERSION",
        "EXACT_PREDECESSOR_SUCCESSOR_PAIR",
    ]
    population_class: AsciiString
    multirow_behavior: Literal["BLANK_OR_ERROR", "SUM_SAME_CURRENCY"]
    non_combinable_with: tuple[AsciiString, ...]
    default_format: AsciiString

    @model_validator(mode="after")
    def measure_semantics_are_closed(self) -> MeasureDefinition:
        if self.classification == "EXACT_VALUE":
            if self.aggregation != "SELECT_EXACT":
                raise ValueError("exact values require SELECT_EXACT")
            if self.multirow_behavior != "BLANK_OR_ERROR":
                raise ValueError("exact values must reject ambiguous row context")
        elif self.classification == "ADDITIVE_GOVERNED_TOTAL":
            if self.aggregation != "SUM":
                raise ValueError("additive totals require SUM")
            if self.required_grouping != ("scenario_ref", "currency"):
                raise ValueError("journal totals require scenario/currency grouping")
            if self.multirow_behavior != "SUM_SAME_CURRENCY":
                raise ValueError("additive totals require same-currency behavior")
        return self


class ParquetWriterProfile(DigestionContractModel):
    profile_id: AsciiString
    profile_version: Literal[1]
    implementation: Literal["PYARROW"]
    implementation_version: Literal["25.0.0"]
    compression_codec: Literal["ZSTD"]
    compression_level: Literal[3]
    row_group_size: Literal[65536]
    dictionary_encoding: Literal[True]
    statistics_mode: Literal["ALL"]
    data_page_version: Literal["1.0"]
    timestamp_unit: Literal["MICROSECOND"]
    timestamp_timezone: Literal["UTC"]
    schema_metadata_policy: Literal["R_CONTRACT_AND_SOURCE_COORDINATE_ONLY"]
    writer_version: Literal["finance-assurance-pyarrow-writer@v1"]
    profile_hash: Literal[
        "sha256:2702aa8812844e508d5b303c50b52e30ab9f20cf7b65c42c2d59f39171b85cb1"
    ]

    @model_validator(mode="after")
    def profile_hash_matches(self) -> ParquetWriterProfile:
        body = self.model_dump(mode="json", exclude={"profile_hash"})
        hash_preimage = {
            "profile": body,
            "writer_options_hash": PINNED_PYARROW_OPTIONS_HASH,
        }
        if self.profile_hash != canonical_sha256(hash_preimage):
            raise ValueError("Parquet writer profile hash does not match its body")
        return self


class ModelTableBinding(DigestionContractModel):
    source_registry_id: RegistryId
    source_registry_version: Literal[1]
    source_dataset_id: AsciiString
    source_dataset_version: Literal[1]
    source_dataset_name: AsciiString
    primary_consumption_class: ProfileId
    included_by_profile: ProfileId
    semantic_owners: tuple[AsciiString, ...]
    source_schema_path: AsciiString
    source_schema_hash: HashValue
    source_data_hash: HashValue
    row_count: NonNegativeInt
    primary_key: tuple[AsciiString, ...]
    unique_keys: tuple[tuple[AsciiString, ...], ...]
    default_sort: tuple[AsciiString, ...]
    logical_table_digest: HashValue
    technical_projection_digest: HashValue
    relationship_key_projections: tuple[AsciiString, ...]
    csv_path: AsciiString | None = None
    csv_hash: HashValue | None = None
    parquet_path: AsciiString | None = None
    parquet_hash: HashValue | None = None
    physical_schema_fingerprint: HashValue | None = None
    duckdb_schema: AsciiString | None = None
    duckdb_object: AsciiString | None = None

    @model_validator(mode="after")
    def physical_coordinates_cooccur(self) -> ModelTableBinding:
        pairs = (
            ("CSV", self.csv_path, self.csv_hash),
            ("PARQUET", self.parquet_path, self.parquet_hash),
            ("DUCKDB", self.duckdb_schema, self.duckdb_object),
        )
        for label, left, right in pairs:
            if (left is None) != (right is None):
                raise ValueError(f"{label} table coordinates must co-occur")
        if (self.parquet_path is None) != (self.physical_schema_fingerprint is None):
            raise ValueError("Parquet path and physical schema must co-occur")
        return self


class ModelManifest(DigestionContractModel):
    contract_version: Literal["consumer-model@v1"]
    model_ref: AsciiString
    source_package_ref: AsciiString
    source_package_digest: HashValue
    source_export_ref: AsciiString
    source_query_revision: NonNegativeInt
    source_semantic_as_of: Timestamp
    source_scenario_set_digest: HashValue
    source_compatibility_mode: Literal["EXACT_ORIGINAL"]
    source_registry_coordinates: tuple[RegistryCoordinate, ...]
    source_relationship_contract_version: Literal[2]
    source_verification_status: Literal["VERIFIED"]
    source_verification_contract: Literal["governed-export-verification@v1"]
    profile_id: ProfileId
    profile_version: Literal[1]
    requested_formats: tuple[PhysicalFormat, ...]
    producer_release: AsciiString
    built_at: Timestamp
    parquet_writer_profile_ref: Literal["PYARROW-25@v1"] | None = None
    parquet_writer_profile_hash: Literal[
        "sha256:2702aa8812844e508d5b303c50b52e30ab9f20cf7b65c42c2d59f39171b85cb1"
    ] | None = None
    synthetic_data: Literal[True]
    synthetic_data_notice: AsciiString
    table_entries: tuple[ModelTableBinding, ...]
    semantic_catalogue_path: AsciiString
    relationship_catalogue_path: AsciiString
    checksum_ledger_path: AsciiString
    canonical_digest_scope: tuple[AsciiString, ...]
    noncanonical_cache_manifest_path: Literal["noncanonical-cache.json"] | None = None

    @model_validator(mode="after")
    def manifest_coordinates_are_closed(self) -> ModelManifest:
        if self.source_registry_coordinates != (
            RegistryCoordinate(registry_id="P-EVIDENCE", registry_version=1),
            RegistryCoordinate(registry_id="Q-ANALYTICS", registry_version=1),
        ):
            raise ValueError("source registry coordinates must be exact P then Q")
        canonical_formats = tuple(
            item
            for item in ("CSV", "PARQUET", "DUCKDB")
            if item in self.requested_formats
        )
        if not self.requested_formats or self.requested_formats != canonical_formats:
            raise ValueError("manifest formats must be unique and canonical")
        has_parquet = "PARQUET" in self.requested_formats
        if has_parquet != (
            self.parquet_writer_profile_ref is not None
            and self.parquet_writer_profile_hash is not None
        ):
            raise ValueError("manifest Parquet profile binding is incomplete")
        has_duckdb = "DUCKDB" in self.requested_formats
        if has_duckdb and not has_parquet:
            raise ValueError("manifest DUCKDB requires PARQUET")
        if has_duckdb != (self.noncanonical_cache_manifest_path is not None):
            raise ValueError("manifest DuckDB cache binding is incomplete")
        if any(
            has_duckdb
            != (entry.duckdb_schema is not None and entry.duckdb_object is not None)
            for entry in self.table_entries
        ):
            raise ValueError("manifest DuckDB table bindings are incomplete")
        if any("duckdb" in item.lower() for item in self.canonical_digest_scope):
            raise ValueError("DuckDB cannot enter the canonical digest scope")
        return self


class DuckDBCacheTableBinding(DigestionContractModel):
    source_coordinate: DatasetCoordinate
    duckdb_schema: AsciiString
    duckdb_object: AsciiString
    parquet_path: AsciiString
    parquet_hash: HashValue
    row_count: NonNegativeInt
    column_names: tuple[AsciiString, ...]
    logical_table_digest: HashValue
    technical_projection_digest: HashValue

    @model_validator(mode="after")
    def cache_table_is_closed(self) -> DuckDBCacheTableBinding:
        if not self.column_names or self.column_names[0] != "row_key":
            raise ValueError("DuckDB cache tables must retain source column order")
        return self


class NoncanonicalCacheManifest(DigestionContractModel):
    cache_contract_version: Literal["duckdb-cache-manifest@v1"]
    model_ref: AsciiString
    source_package_digest: HashValue
    profile_coordinate: ProfileCoordinate
    database_path: Literal["warehouse/finance-assurance.duckdb"]
    database_sha256: HashValue
    database_byte_count: PositiveInt
    engine: Literal["DUCKDB"]
    engine_version: Literal["1.5.5"]
    storage_compatibility_version: Literal["v1.5.0"]
    database_storage_version: Literal["v1.5.0+"]
    build_source_format: Literal["PARQUET"]
    schema_names: tuple[AsciiString, ...]
    metadata_table_names: tuple[AsciiString, ...]
    table_entries: tuple[DuckDBCacheTableBinding, ...]
    read_only_consumer_required: Literal[True]

    @model_validator(mode="after")
    def cache_inventory_is_closed(self) -> NoncanonicalCacheManifest:
        if self.schema_names != (
            "p_evidence_v1",
            "q_analytics_v1",
            "model_meta",
        ):
            raise ValueError("DuckDB cache schemas must use the exact R3 inventory")
        if self.metadata_table_names != (
            "cache_profile",
            "documents",
            "table_bindings",
        ):
            raise ValueError("DuckDB metadata tables must use the exact R3 inventory")
        coordinates = tuple(item.source_coordinate for item in self.table_entries)
        objects = tuple(
            (item.duckdb_schema, item.duckdb_object) for item in self.table_entries
        )
        if len(coordinates) != len(set(coordinates)) or len(objects) != len(
            set(objects)
        ):
            raise ValueError("DuckDB cache table bindings must be unique")
        return self


class SemanticTable(DigestionContractModel):
    source_coordinate: DatasetCoordinate
    physical_alias: AsciiString
    display_label: AsciiString
    primary_consumption_class: ProfileId
    included_by_profile: ProfileId
    semantic_owners: tuple[AsciiString, ...]
    default_sort: tuple[AsciiString, ...]
    column_names: tuple[AsciiString, ...]

    @model_validator(mode="after")
    def table_shape_is_closed(self) -> SemanticTable:
        if not self.physical_alias.startswith("r_"):
            raise ValueError("portable table aliases must use the r_ prefix")
        if len(self.physical_alias) > 63:
            raise ValueError("portable table aliases cannot exceed 63 characters")
        if not self.column_names or self.column_names[0] != "row_key":
            raise ValueError("semantic tables must retain source column order")
        if self.default_sort != ("row_key",):
            raise ValueError("R v1 tables require row_key ordering")
        return self


class SemanticCatalogue(DigestionContractModel):
    catalogue_contract_version: Literal["semantic-catalogue@v1"]
    model_ref: AsciiString
    profile_coordinate: ProfileCoordinate
    source_package_digest: HashValue
    tables: tuple[SemanticTable, ...]
    columns: tuple[ColumnSemantic, ...]
    relationships: tuple[RelationshipPlanEntry, ...]
    measures: tuple[MeasureDefinition, ...]
    format_hints: tuple[AsciiString, ...]
    consumer_capabilities: tuple[AsciiString, ...]


class BuildConsumerModel(DigestionContractModel):
    request_contract_version: Literal["build-consumer-model-request@v1"]
    model_ref: AsciiString
    source_package_path: Path
    expected_source_package_digest: HashValue
    profile_id: ProfileId
    profile_version: Literal[1]
    formats: tuple[PhysicalFormat, ...]
    parquet_writer_profile_ref: Literal["PYARROW-25@v1"] | None = None
    parquet_writer_profile_hash: Literal[
        "sha256:2702aa8812844e508d5b303c50b52e30ab9f20cf7b65c42c2d59f39171b85cb1"
    ] | None = None
    duckdb_storage_compatibility_version: (
        DuckDBStorageCompatibilityVersion | None
    ) = None
    output_path: Path
    producer_release: AsciiString
    built_at: Timestamp

    @model_validator(mode="after")
    def requested_formats_are_closed(self) -> BuildConsumerModel:
        canonical = tuple(
            item for item in ("CSV", "PARQUET", "DUCKDB") if item in self.formats
        )
        if not self.formats or self.formats != canonical:
            raise ValueError(
                "formats must be non-empty, unique, and canonically ordered"
            )
        if "DUCKDB" in self.formats and "PARQUET" not in self.formats:
            raise ValueError("DUCKDB requires PARQUET")
        parquet_refs = (
            self.parquet_writer_profile_ref,
            self.parquet_writer_profile_hash,
        )
        if ("PARQUET" in self.formats) != all(
            item is not None for item in parquet_refs
        ):
            raise ValueError("PARQUET and its exact writer coordinate must co-occur")
        if ("DUCKDB" in self.formats) != (
            self.duckdb_storage_compatibility_version is not None
        ):
            raise ValueError("DUCKDB and its storage version must co-occur")
        return self


class BuildConsumerModelResult(DigestionContractModel):
    result_contract_version: Literal["build-consumer-model-result@v1"]
    model_ref: AsciiString
    model_path: Path
    model_digest: HashValue
    source_package_digest: HashValue
    profile_id: ProfileId
    profile_version: Literal[1]
    canonical_file_count: PositiveInt
    noncanonical_cache_file_count: NonNegativeInt
    table_count: PositiveInt
    source_row_count: NonNegativeInt
    technical_projection_count: NonNegativeInt


class VerifyConsumerModel(DigestionContractModel):
    request_contract_version: Literal["verify-consumer-model-request@v1"]
    model_path: Path
    source_package_path: Path
    expected_model_digest: HashValue
    expected_source_package_digest: HashValue
    verification_scope: Literal["FULL_SOURCE_EQUIVALENCE"]


class VerifyConsumerModelResult(DigestionContractModel):
    result_contract_version: Literal["verify-consumer-model-result@v1"]
    status: Literal["VERIFIED", "FAILED"]
    model_digest: HashValue | None = None
    source_package_digest: HashValue | None = None
    checked_file_count: NonNegativeInt
    checked_table_count: NonNegativeInt
    checked_column_count: NonNegativeInt
    checked_relationship_count: NonNegativeInt
    message: AsciiString


class ReproduceConsumerModel(DigestionContractModel):
    request_contract_version: Literal["reproduce-consumer-model-request@v1"]
    source_model_path: Path
    source_package_path: Path
    reproduction_output_path: Path
    expected_model_digest: HashValue
    expected_source_package_digest: HashValue


class ReproduceConsumerModelResult(DigestionContractModel):
    result_contract_version: Literal["reproduce-consumer-model-result@v1"]
    status: Literal[
        "REPRODUCED",
        "DIGEST_MISMATCH",
        "SOURCE_PACKAGE_UNAVAILABLE",
        "WRITER_PROFILE_UNAVAILABLE",
        "BUILD_FAILED",
    ]
    expected_model_digest: HashValue
    actual_model_digest: HashValue | None = None
    source_package_digest: HashValue | None = None
    message: AsciiString
