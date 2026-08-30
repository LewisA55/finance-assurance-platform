"""Strict Artifact S manifest, metadata, workbook, and lineage schemas."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, Field, model_validator

from finance_assurance.digestion.contracts import (
    ColumnRole,
    ColumnSemantic,
    DatasetCoordinate,
    MeasureDefinition,
    ModelTableBinding,
    PhysicalFormat,
    PhysicalType,
    ProfileCoordinate,
    RelationshipPlanEntry,
    SemanticTable,
    SourceType,
    Visibility,
)
from finance_assurance.handoff.contracts import HandoffContractModel
from finance_assurance.handoff.paths import validate_package_path
from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.contracts.primitives import (
    AsciiString,
    HashValue,
    NonNegativeInt,
    PositiveInt,
    Timestamp,
)

PackagePath = Annotated[str, AfterValidator(validate_package_path)]
XlsxStorageMode = Literal[
    "TEXT_EXACT",
    "TEXT_DATE_ISO",
    "TEXT_TIMESTAMP_UTC",
    "BOOLEAN_NATIVE",
    "NUMBER_EXACT",
    "TEXT_INT64",
]


class HandoffBinding(HandoffContractModel):
    handoff_ref: AsciiString
    source_model_ref: AsciiString
    source_model_digest: HashValue
    source_package_digest: HashValue


class SourceDocumentBinding(HandoffContractModel):
    path: PackagePath
    contract_version: AsciiString
    sha256: HashValue


class SourceDatasetBinding(HandoffContractModel):
    source_coordinate: DatasetCoordinate
    parquet_path: PackagePath
    parquet_sha256: HashValue
    logical_table_digest: HashValue
    technical_projection_digest: HashValue
    column_names: tuple[AsciiString, ...]


class JsonSourcePointer(HandoffContractModel):
    pointer_kind: Literal["JSON_POINTER"]
    source_document_path: PackagePath
    json_pointer: AsciiString


class DatasetCellPointer(HandoffContractModel):
    pointer_kind: Literal["DATASET_CELL"]
    source_coordinate: DatasetCoordinate
    selector_ref: AsciiString
    field_name: AsciiString


SourcePointer = Annotated[
    JsonSourcePointer | DatasetCellPointer,
    Field(discriminator="pointer_kind"),
]


class FieldProvenance(HandoffContractModel):
    target_json_pointer: AsciiString
    coverage: Literal["VALUE", "ARRAY_ORDER"]
    derivation_class: Literal["R_COPY", "R_PROJECTION", "S_GUIDANCE"]
    source_pointers: tuple[SourcePointer, ...]
    algorithm_ref: AsciiString

    @model_validator(mode="after")
    def pointer_count_matches_derivation(self) -> FieldProvenance:
        if self.derivation_class == "R_COPY" and len(self.source_pointers) != 1:
            raise ValueError("R_COPY requires exactly one source pointer")
        if self.derivation_class == "R_PROJECTION" and not self.source_pointers:
            raise ValueError("R_PROJECTION requires source pointers")
        if self.derivation_class == "S_GUIDANCE" and self.source_pointers:
            raise ValueError("S_GUIDANCE cannot carry source pointers")
        return self


class RCacheBinding(HandoffContractModel):
    cache_contract_version: Literal["duckdb-cache-manifest@v1"]
    model_ref: AsciiString
    source_package_digest: HashValue
    profile_coordinate: ProfileCoordinate
    database_path: PackagePath
    database_sha256: HashValue
    database_byte_count: PositiveInt
    engine: Literal["DUCKDB"]
    engine_version: Literal["1.5.5"]
    storage_compatibility_version: Literal["v1.5.0"]
    database_storage_version: Literal["v1.5.0+"]
    build_source_format: Literal["PARQUET"]
    schema_names: tuple[AsciiString, ...]
    metadata_table_names: tuple[AsciiString, ...]
    table_count: PositiveInt
    table_bindings_digest: HashValue
    read_only_consumer_required: Literal[True]


class SourceBindingTableEntry(ModelTableBinding):
    pass


class SourceBindingPayload(HandoffContractModel):
    profile_coordinate: ProfileCoordinate
    source_formats: tuple[PhysicalFormat, ...]
    r_paths: tuple[PackagePath, ...]
    r_cache_binding: RCacheBinding
    table_entries: tuple[SourceBindingTableEntry, ...]

    @model_validator(mode="after")
    def exact_profile_and_formats(self) -> SourceBindingPayload:
        if self.profile_coordinate != ProfileCoordinate(
            profile_id="LINEAGE", profile_version=1
        ):
            raise ValueError("S source binding requires LINEAGE@1")
        if self.source_formats != ("CSV", "PARQUET", "DUCKDB"):
            raise ValueError("S source binding requires all three R formats")
        if self.r_paths != (
            "model-manifest.json",
            "semantic-model.json",
            "relationships.json",
            "checksums.json",
            "model.digest",
            "noncanonical-cache.json",
        ):
            raise ValueError("R path registry must contain the six exact R paths")
        return self


class DataDictionaryTable(SemanticTable):
    primary_key: tuple[AsciiString, ...]
    unique_keys: tuple[tuple[AsciiString, ...], ...]


class DataDictionaryColumn(ColumnSemantic):
    ordinal: PositiveInt
    xlsx_storage_mode: XlsxStorageMode


class DataDictionaryPayload(HandoffContractModel):
    tables: tuple[DataDictionaryTable, ...]
    columns: tuple[DataDictionaryColumn, ...]


class RelationshipsPayload(HandoffContractModel):
    relationships: tuple[RelationshipPlanEntry, ...]


class MeasuresPayload(HandoffContractModel):
    measures: tuple[MeasureDefinition, ...]


class FieldRoleProjection(HandoffContractModel):
    source_coordinate: DatasetCoordinate
    source_name: AsciiString
    source_type: SourceType
    physical_type: PhysicalType
    column_role: ColumnRole
    default_visibility: Visibility
    default_summarization: Literal["NONE"]
    display_label: AsciiString
    display_folder: AsciiString | None
    format_hints: tuple[
        Literal[
            "MONEY_INTEGER_MINOR_UNITS",
            "RAW_INTEGER_SUMMARIZATION_NONE",
            "TIMESTAMP_UTC_MICROSECOND",
        ],
        ...,
    ]


class FieldRolesPayload(HandoffContractModel):
    fields: tuple[FieldRoleProjection, ...]


class DatasetPointer(HandoffContractModel):
    source_coordinate: DatasetCoordinate
    r_table_alias: AsciiString


class DirectedJoinStep(HandoffContractModel):
    step_ordinal: PositiveInt
    relationship_id: AsciiString
    from_coordinate: DatasetCoordinate
    from_fields: tuple[AsciiString, ...]
    to_coordinate: DatasetCoordinate
    to_fields: tuple[AsciiString, ...]
    projected_key_ref: AsciiString | None
    direction: Literal["FORWARD"]


class EvidenceStatusField(HandoffContractModel):
    source_coordinate: DatasetCoordinate
    field_name: AsciiString
    allowed_enum_values: tuple[AsciiString, ...]


class LineagePayload(HandoffContractModel):
    dataset_pointers: tuple[DatasetPointer, ...]
    directed_join_steps: tuple[DirectedJoinStep, ...]
    evidence_status_fields: tuple[EvidenceStatusField, ...]


ConsumerId = Literal["REACT", "EXCEL", "POWER_BI", "SQL"]


class ConsumerSuitabilityEntry(HandoffContractModel):
    consumer_id: ConsumerId
    supported_use_ids: tuple[AsciiString, ...]
    conditional_use_ids: tuple[AsciiString, ...]
    unsupported_use_ids: tuple[AsciiString, ...]
    required_upstream_expansion_ids: tuple[AsciiString, ...]
    required_source_paths: tuple[PackagePath, ...]


class ConsumerSuitabilityPayload(HandoffContractModel):
    consumers: tuple[ConsumerSuitabilityEntry, ...]
    synthetic_depth_notice: AsciiString

    @model_validator(mode="after")
    def exact_consumer_order(self) -> ConsumerSuitabilityPayload:
        if tuple(item.consumer_id for item in self.consumers) != (
            "REACT",
            "EXCEL",
            "POWER_BI",
            "SQL",
        ):
            raise ValueError("consumer suitability order must be exact")
        return self


class ValidationCheckRegistryPayload(HandoffContractModel):
    checks: tuple[dict[str, object], ...]
    contract_version: Literal["validation-check-registry@v1"]
    registry_id: Literal["S-VALIDATION-C001-CT1@v1"]
    selector_order: Literal["LEXICAL_SELECTOR_ID"]
    selectors: tuple[dict[str, object], ...]
    source_profile_id: Literal["LINEAGE"]
    source_profile_version: Literal[1]

    @model_validator(mode="after")
    def exact_registry_object(self) -> ValidationCheckRegistryPayload:
        if canonical_sha256(self.model_dump(mode="json")) != (
            "sha256:36255992b12b0176f290ec2fa033e5655d8ca4b3a2e4cbd3a522a1de295f7cb8"
        ):
            raise ValueError("validation registry payload must equal its authority")
        return self


MetadataPayload = (
    SourceBindingPayload
    | DataDictionaryPayload
    | RelationshipsPayload
    | MeasuresPayload
    | FieldRolesPayload
    | LineagePayload
    | ConsumerSuitabilityPayload
    | ValidationCheckRegistryPayload
)


class MetadataDocument(HandoffContractModel):
    contract_version: Literal[
        "handoff-source-binding@v1",
        "handoff-data-dictionary@v1",
        "handoff-relationships@v1",
        "handoff-measures@v1",
        "handoff-field-roles@v1",
        "handoff-lineage-guide@v1",
        "consumer-suitability@v1",
        "validation-check-registry@v1",
    ]
    handoff_binding: HandoffBinding
    source_documents: tuple[SourceDocumentBinding, ...]
    source_datasets: tuple[SourceDatasetBinding, ...]
    field_provenance: tuple[FieldProvenance, ...]
    payload: MetadataPayload

    @model_validator(mode="after")
    def envelope_matches_payload(self) -> MetadataDocument:
        expected_type = {
            "handoff-source-binding@v1": SourceBindingPayload,
            "handoff-data-dictionary@v1": DataDictionaryPayload,
            "handoff-relationships@v1": RelationshipsPayload,
            "handoff-measures@v1": MeasuresPayload,
            "handoff-field-roles@v1": FieldRolesPayload,
            "handoff-lineage-guide@v1": LineagePayload,
            "consumer-suitability@v1": ConsumerSuitabilityPayload,
            "validation-check-registry@v1": ValidationCheckRegistryPayload,
        }[self.contract_version]
        if not isinstance(self.payload, expected_type):
            raise ValueError("metadata contract does not match its payload model")
        provenance_keys = tuple(
            (item.target_json_pointer, item.coverage) for item in self.field_provenance
        )
        if provenance_keys != tuple(sorted(provenance_keys)) or len(
            provenance_keys
        ) != len(set(provenance_keys)):
            raise ValueError("field provenance must be lexical and unique")
        return self


class LimitationEntry(HandoffContractModel):
    limitation_id: AsciiString
    statement: AsciiString


class HandoffLimitations(HandoffContractModel):
    contract_version: Literal["handoff-limitations@v1"]
    limitations: tuple[LimitationEntry, ...]
    synthetic_data: Literal[True]
    synthetic_data_notice: AsciiString

    @model_validator(mode="after")
    def exact_limitations(self) -> HandoffLimitations:
        if canonical_sha256(self.model_dump(mode="json")) != (
            "sha256:a353c13d8ba10ffb0bfa08e68fdbff85d5a3fad3c8dcda8b94b168cf859f8914"
        ):
            raise ValueError("limitations object must equal its authority")
        return self


class MetadataManifestEntry(HandoffContractModel):
    path: PackagePath
    contract_version: AsciiString
    payload_sha256: HashValue
    source_document_bindings: tuple[SourceDocumentBinding, ...]
    source_dataset_bindings: tuple[SourceDatasetBinding, ...]
    algorithm_refs: tuple[AsciiString, ...]


class SqlManifestEntry(HandoffContractModel):
    path: PackagePath
    query_ids: tuple[AsciiString, ...]
    authority_ref: Literal["S-SQL-FIXTURES@v1"]
    authority_file_sha256: HashValue
    validation_registry_hash: HashValue | None


class HandoffManifest(HandoffContractModel):
    contract_version: Literal["handoff-manifest@v1"]
    handoff_ref: AsciiString
    source_model_ref: AsciiString
    source_model_path: Literal["source-model"]
    source_model_digest: HashValue
    source_package_ref: AsciiString
    source_package_digest: HashValue
    source_export_ref: AsciiString
    source_query_revision: NonNegativeInt
    source_semantic_as_of: Timestamp
    source_scenario_set_digest: HashValue
    source_compatibility_mode: Literal["EXACT_ORIGINAL"]
    source_verification_status: Literal["VERIFIED"]
    profile_id: Literal["LINEAGE"]
    profile_version: Literal[1]
    source_formats: tuple[PhysicalFormat, ...]
    synthetic_data: Literal[True]
    synthetic_data_notice: AsciiString
    table_count: PositiveInt
    source_row_count: NonNegativeInt
    catalogue_column_count: PositiveInt
    relationship_count: PositiveInt
    measure_count: PositiveInt
    validation_check_count: Literal[12]
    validation_registry_ref: Literal["S-VALIDATION-C001-CT1@v1"]
    validation_registry_hash: Literal[
        "sha256:36255992b12b0176f290ec2fa033e5655d8ca4b3a2e4cbd3a522a1de295f7cb8"
    ]
    canonical_digest_scope: tuple[PackagePath, ...]
    noncanonical_path_scope: tuple[PackagePath, ...]
    metadata_entries: tuple[MetadataManifestEntry, ...]
    sql_entries: tuple[SqlManifestEntry, ...]
    r_noncanonical_cache_manifest_path: PackagePath
    r_duckdb_path: PackagePath
    xlsx_noncanonical_manifest_path: PackagePath
    xlsx_type_map_ref: Literal["XLSX-TYPE-MAP@v1"]
    xlsx_type_map_hash: HashValue
    xlsx_writer_profile_ref: Literal["XLSXWRITER-3.2.9@v1"]
    xlsx_writer_profile_hash: HashValue
    xlsx_logical_workbook_digest: HashValue
    consumer_suitability_path: Literal["metadata/consumer-suitability.json"]
    producer_release: AsciiString
    built_at: Timestamp


class HandoffChecksumEntry(HandoffContractModel):
    path: PackagePath
    sha256: HashValue
    byte_count: NonNegativeInt


class HandoffChecksumLedger(HandoffContractModel):
    contract_version: Literal["handoff-checksum-ledger@v1"]
    files: tuple[HandoffChecksumEntry, ...]

    @model_validator(mode="after")
    def lexical_unique_paths(self) -> HandoffChecksumLedger:
        paths = tuple(item.path for item in self.files)
        if paths != tuple(sorted(paths)) or len(paths) != len(set(paths)):
            raise ValueError("handoff checksum paths must be lexical and unique")
        return self


class WorkbookColumnEntry(HandoffContractModel):
    ordinal: PositiveInt
    name: AsciiString
    source_type: SourceType
    nullability: bool
    storage_mode: XlsxStorageMode


class WorkbookNullCount(HandoffContractModel):
    name: AsciiString
    count: NonNegativeInt


class WorkbookSheetEntry(HandoffContractModel):
    sheet_kind: Literal["DATA", "METADATA"]
    source_dataset_coordinate: DatasetCoordinate | None
    metadata_sheet_id: AsciiString | None
    sheet_name: AsciiString
    table_name: AsciiString | None
    columns: tuple[WorkbookColumnEntry, ...]
    typed_rows_digest: HashValue
    row_count: NonNegativeInt
    column_count: PositiveInt
    null_counts: tuple[WorkbookNullCount, ...]

    @model_validator(mode="after")
    def exact_sheet_variant(self) -> WorkbookSheetEntry:
        if (self.source_dataset_coordinate is None) == (self.metadata_sheet_id is None):
            raise ValueError("workbook sheet requires exactly one identity")
        if self.sheet_kind == "DATA":
            if self.source_dataset_coordinate is None:
                raise ValueError("DATA sheet requires a source coordinate")
            if (self.row_count == 0) != (self.table_name is None):
                raise ValueError(
                    "DATA table name must be absent only for a zero-row sheet"
                )
        elif self.metadata_sheet_id is None or self.table_name is not None:
            raise ValueError("METADATA sheet requires metadata ID and no table")
        if self.column_count != len(self.columns):
            raise ValueError("workbook column count does not match columns")
        return self


class OpenXmlPartEntry(HandoffContractModel):
    path: PackagePath
    content_type: AsciiString
    sha256: HashValue
    relationship_type_ids: tuple[AsciiString, ...]


class NoncanonicalWorkbookManifest(HandoffContractModel):
    contract_version: Literal["handoff-manifest@v1"]
    handoff_ref: AsciiString
    source_model_ref: AsciiString
    source_model_digest: HashValue
    source_package_digest: HashValue
    workbook_path: Literal["excel/finance-assurance-data-pack.xlsx"]
    workbook_sha256: HashValue
    workbook_byte_count: PositiveInt
    writer_profile_ref: Literal["XLSXWRITER-3.2.9@v1"]
    writer_profile_hash: HashValue
    logical_workbook_digest: HashValue
    sheet_entries: tuple[WorkbookSheetEntry, ...]
    openxml_part_inventory: tuple[OpenXmlPartEntry, ...]
