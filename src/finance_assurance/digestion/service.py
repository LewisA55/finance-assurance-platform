"""Artifact R build, verify, and reproduce application service through Phase R3."""

from __future__ import annotations

import gc
import json
import shutil
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import ValidationError

from finance_assurance.analytics.registry import DATASET_BY_ID as Q_DATASET_BY_ID
from finance_assurance.digestion.contracts import (
    BuildConsumerModel,
    BuildConsumerModelResult,
    DatasetCoordinate,
    ModelManifest,
    ModelTableBinding,
    ProfileCoordinate,
    ReproduceConsumerModel,
    ReproduceConsumerModelResult,
    SemanticCatalogue,
    SemanticTable,
    VerifyConsumerModel,
    VerifyConsumerModelResult,
)
from finance_assurance.digestion.duckdb_cache import (
    DUCKDB_CACHE_MANIFEST_PATH,
    DUCKDB_ENGINE_VERSION,
    DUCKDB_STORAGE_COMPATIBILITY_VERSION,
    build_duckdb_cache,
    duckdb_schema,
    read_duckdb_cache_manifest,
    validate_duckdb_runtime,
    verify_duckdb_cache,
)
from finance_assurance.digestion.keys import assert_no_key_collisions, relationship_key
from finance_assurance.digestion.registry import (
    ALL_DATASET_COORDINATES,
    COLUMN_ROLE_REGISTRY,
    MEASURE_REGISTRY,
    PRIMARY_CONSUMPTION_CLASS,
    PROFILE_DATASET_IDS,
    R_CONTRACT_VERSION,
    RELATIONSHIP_KEY_PROJECTIONS,
    portable_alias,
    registry_contract_hash,
    relationship_plan,
    validate_registry,
    validate_relationship_graph,
)
from finance_assurance.digestion.writer import (
    PARQUET_WRITER_PROFILE,
    PYARROW_WRITE_OPTIONS,
    WRITER_PROFILE_REF,
    validate_writer_runtime,
)
from finance_assurance.exports.contracts import (
    ChecksumEntry,
    ChecksumLedger,
    GovernedExportManifest,
)
from finance_assurance.exports.registry import DATASET_BY_ID as P_DATASET_BY_ID
from finance_assurance.exports.serialization import (
    canonical_json_bytes,
    parse_canonical_csv,
    sha256_bytes,
)
from finance_assurance.exports.service import verify_governed_export
from finance_assurance.runtime.canonical import canonical_sha256

MODEL_CONTRACT = "consumer-model@v1"
SEMANTIC_CONTRACT = "semantic-catalogue@v1"
SOURCE_VERIFICATION_CONTRACT = "governed-export-verification@v1"
FORMAT_HINTS = (
    "MONEY_INTEGER_MINOR_UNITS",
    "RAW_INTEGER_SUMMARIZATION_NONE",
    "TIMESTAMP_UTC_MICROSECOND",
)
CONSUMER_CAPABILITIES = (
    "DIRECT_SQL",
    "EXCEL_ADAPTER",
    "POWER_BI_ADAPTER",
    "REACT_ANALYTICAL_ADAPTER",
)


class ConsumerModelError(RuntimeError):
    """A fail-closed Artifact R build error."""


class _VerificationFailure(RuntimeError):
    pass


def _atomic_publish(staging: Path, final_path: Path) -> None:
    """Publish with one atomic rename, tolerating bounded Windows handle lag."""

    for attempt in range(8):
        try:
            staging.replace(final_path)
            return
        except PermissionError:
            if attempt == 7:
                raise
            gc.collect()
            time.sleep(0.05 * (attempt + 1))


def _definition(registry_id: str, dataset_id: str) -> Any:
    if registry_id == "P-EVIDENCE":
        return P_DATASET_BY_ID[dataset_id]
    if registry_id == "Q-ANALYTICS":
        return Q_DATASET_BY_ID[dataset_id]
    raise KeyError(registry_id)


def _storage_key(registry_id: str) -> str:
    return {
        "P-EVIDENCE": "p-evidence-v1",
        "Q-ANALYTICS": "q-analytics-v1",
    }[registry_id]


def _read_json(path: Path, model: type[Any]) -> Any:
    payload = path.read_bytes()
    value = model.model_validate_json(payload)
    if canonical_json_bytes(value.model_dump(mode="json")) != payload:
        raise ValueError(f"{path.name} is not canonical")
    return value


def _source_manifest(root: Path) -> GovernedExportManifest:
    return cast(GovernedExportManifest, _read_json(root / "manifest.json", GovernedExportManifest))


def _selected_coordinates(profile_id: str) -> tuple[DatasetCoordinate, ...]:
    selected = PROFILE_DATASET_IDS[profile_id]  # type: ignore[index]
    return tuple(item for item in ALL_DATASET_COORDINATES if item.dataset_id in selected)


def _selected_projection_map(
    profile_id: str,
) -> dict[tuple[str, str], tuple[Any, ...]]:
    relationship_ids = {item.relationship_id for item in relationship_plan(profile_id)}  # type: ignore[arg-type]
    selected = PROFILE_DATASET_IDS[profile_id]  # type: ignore[index]
    result: dict[tuple[str, str], list[Any]] = {}
    for projection in RELATIONSHIP_KEY_PROJECTIONS:
        if (
            projection.relationship_id not in relationship_ids
            or projection.from_coordinate.dataset_id not in selected
            or projection.to_coordinate.dataset_id not in selected
        ):
            continue
        for coordinate in (projection.from_coordinate, projection.to_coordinate):
            result.setdefault(
                (coordinate.registry_id, coordinate.dataset_id), []
            ).append(projection)
    return {
        key: tuple(sorted(value, key=lambda item: item.relationship_id))
        for key, value in result.items()
    }


def _projection_endpoint(projection: Any, coordinate: DatasetCoordinate) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if coordinate == projection.from_coordinate:
        return projection.from_columns, projection.from_types
    if coordinate == projection.to_coordinate:
        return projection.to_columns, projection.to_types
    raise ValueError("relationship projection does not contain dataset endpoint")


def _project_rows(
    coordinate: DatasetCoordinate,
    rows: tuple[dict[str, object], ...],
    projections: tuple[Any, ...],
) -> tuple[tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    output: list[dict[str, object]] = []
    technical: list[dict[str, object]] = []
    collision_sets: dict[str, list[tuple[str, tuple[object, ...]]]] = {
        item.relationship_id: [] for item in projections
    }
    for source in rows:
        emitted = dict(source)
        technical_row: dict[str, object] = {"row_key": source["row_key"]}
        for projection in projections:
            columns, types = _projection_endpoint(projection, coordinate)
            preimage = tuple(source[column] for column in columns)
            key = relationship_key(projection.relationship_id, types, preimage)
            emitted[projection.technical_column_name] = key
            technical_row[projection.technical_column_name] = key
            collision_sets[projection.relationship_id].append((key, preimage))
        output.append(emitted)
        technical.append(technical_row)
    for values in collision_sets.values():
        assert_no_key_collisions(values)
    return tuple(output), tuple(technical)


def _arrow_type(source_type: str) -> pa.DataType:
    return {
        "text": pa.string(),
        "enum": pa.string(),
        "integer": pa.int64(),
        "boolean": pa.bool_(),
        "date": pa.date32(),
        "timestamp": pa.timestamp("us", tz="UTC"),
        "hash": pa.string(),
    }[source_type]


def _typed_value(source_type: str, value: object) -> object:
    if value is None:
        return None
    if source_type == "date":
        return date.fromisoformat(cast(str, value))
    if source_type == "timestamp":
        parsed = datetime.fromisoformat(cast(str, value).replace("Z", "+00:00"))
        return parsed.astimezone(UTC)
    return value


def _arrow_table(
    coordinate: DatasetCoordinate,
    definition: Any,
    rows: tuple[dict[str, object], ...],
    projections: tuple[Any, ...],
) -> pa.Table:
    fields = [
        pa.field(column.name, _arrow_type(column.type), nullable=column.nullable)
        for column in definition.columns
    ]
    fields.extend(
        pa.field(item.technical_column_name, pa.string(), nullable=False)
        for item in projections
    )
    metadata = {
        b"r_contract_version": R_CONTRACT_VERSION.encode("ascii"),
        b"source_coordinate": (
            f"{coordinate.registry_id}@v1/{coordinate.dataset_id}@v1"
        ).encode("ascii"),
    }
    schema = pa.schema(fields, metadata=metadata)
    arrays = []
    source_types = {item.name: item.type for item in definition.columns}
    for field in schema:
        source_type = source_types.get(field.name, "hash")
        arrays.append(
            pa.array(
                [_typed_value(source_type, row[field.name]) for row in rows],
                type=field.type,
            )
        )
    return pa.Table.from_arrays(arrays, schema=schema)


def _schema_fingerprint(schema: pa.Schema) -> str:
    return canonical_sha256(
        {
            "fields": [
                {
                    "name": field.name,
                    "nullable": field.nullable,
                    "type": str(field.type),
                }
                for field in schema
            ],
            "metadata": {
                key.decode("ascii"): value.decode("ascii")
                for key, value in sorted((schema.metadata or {}).items())
            },
        }
    )


def _canonical_scope(
    coordinates: tuple[DatasetCoordinate, ...], formats: tuple[str, ...]
) -> tuple[str, ...]:
    paths = {
        "README.txt",
        "model-manifest.json",
        "relationships.json",
        "semantic-model.json",
    }
    for coordinate in coordinates:
        storage = _storage_key(coordinate.registry_id)
        paths.add(f"schemas/{storage}/{coordinate.dataset_id}.schema.json")
        if "CSV" in formats:
            paths.add(f"csv/{storage}/{coordinate.dataset_id}.csv")
        if "PARQUET" in formats:
            paths.add(f"parquet/{storage}/{coordinate.dataset_id}.parquet")
    return tuple(sorted(paths))


def _readme(manifest: ModelManifest) -> bytes:
    lines = (
        "Finance & Assurance Platform - Consumer Model",
        f"Model: {manifest.model_ref}",
        f"Contract: {manifest.contract_version}",
        f"Profile: {manifest.profile_id}@v{manifest.profile_version}",
        f"Source package: {manifest.source_package_ref}",
        f"Source digest: {manifest.source_package_digest}",
        "Synthetic data: true",
        f"Notice: {manifest.synthetic_data_notice}",
        "Canonical depth: bounded C-001 and CT-1 reference cases.",
        "This directory is a rebuildable projection and is not runtime authority.",
    )
    return ("\n".join(lines) + "\n").encode("ascii")


def _semantic_catalogue(
    request: BuildConsumerModel,
    coordinates: tuple[DatasetCoordinate, ...],
) -> SemanticCatalogue:
    selected = {(item.registry_id, item.dataset_id) for item in coordinates}
    columns = tuple(
        item
        for item in COLUMN_ROLE_REGISTRY
        if (
            item.source_coordinate.registry_id,
            item.source_coordinate.dataset_id,
        )
        in selected
    )
    measures = tuple(
        item
        for item in MEASURE_REGISTRY
        if (item.source_registry_id, item.source_dataset_id) in selected
    )
    projection_map = _selected_projection_map(request.profile_id)
    tables = tuple(
        SemanticTable(
            source_coordinate=coordinate,
            physical_alias=portable_alias(
                coordinate.registry_id,
                coordinate.dataset_id,
                _definition(coordinate.registry_id, coordinate.dataset_id).name,
            ),
            display_label=_definition(
                coordinate.registry_id, coordinate.dataset_id
            ).name.replace("_", " ").title(),
            primary_consumption_class=PRIMARY_CONSUMPTION_CLASS[
                coordinate.dataset_id
            ],
            included_by_profile=request.profile_id,
            semantic_owners=_definition(
                coordinate.registry_id, coordinate.dataset_id
            ).semantic_owners,
            default_sort=("row_key",),
            column_names=tuple(
                item.name
                for item in _definition(
                    coordinate.registry_id, coordinate.dataset_id
                ).columns
            )
            + tuple(
                item.technical_column_name
                for item in projection_map.get(
                    (coordinate.registry_id, coordinate.dataset_id), ()
                )
            ),
        )
        for coordinate in coordinates
    )
    return SemanticCatalogue(
        catalogue_contract_version=SEMANTIC_CONTRACT,
        model_ref=request.model_ref,
        profile_coordinate=ProfileCoordinate(
            profile_id=request.profile_id, profile_version=1
        ),
        source_package_digest=request.expected_source_package_digest,
        tables=tables,
        columns=columns,
        relationships=relationship_plan(request.profile_id),
        measures=measures,
        format_hints=FORMAT_HINTS,
        consumer_capabilities=CONSUMER_CAPABILITIES,
    )


class ConsumerModelService:
    """Finite R-C01/R-C02/R-C03 service through Phase R3."""

    def build(self, request: BuildConsumerModel) -> BuildConsumerModelResult:
        validate_registry()
        if "PARQUET" in request.formats:
            validate_writer_runtime()
        if "DUCKDB" in request.formats:
            validate_duckdb_runtime()
        final_path = request.output_path.resolve()
        source = request.source_package_path.resolve()
        if final_path == source or final_path.is_relative_to(source):
            raise ConsumerModelError("model output cannot be inside the source package")
        if final_path.exists():
            raise ConsumerModelError("final output path already exists")
        final_path.parent.mkdir(parents=True, exist_ok=True)
        staging = final_path.parent / f".{final_path.name}.staging-{uuid4().hex}"
        try:
            source_verification = verify_governed_export(source)
            if source_verification.status != "VERIFIED":
                raise ConsumerModelError("source package is not VERIFIED by P-C02")
            if source_verification.package_digest != request.expected_source_package_digest:
                raise ConsumerModelError("source package digest differs from request")
            source_manifest = _source_manifest(source)
            if (
                tuple(item.registry_id for item in source_manifest.dataset_registries)
                != ("P-EVIDENCE", "Q-ANALYTICS")
                or source_manifest.relationship_contract_version != 2
                or source_manifest.compatibility_mode != "EXACT_ORIGINAL"
            ):
                raise ConsumerModelError("source package coordinate is unsupported")

            staging.mkdir()
            coordinates = _selected_coordinates(request.profile_id)
            projection_map = _selected_projection_map(request.profile_id)
            source_entries = {
                (item.registry_id, item.dataset_id): item
                for item in source_manifest.dataset_entries
            }
            table_entries: list[ModelTableBinding] = []
            source_row_count = 0
            for coordinate in coordinates:
                definition = _definition(
                    coordinate.registry_id, coordinate.dataset_id
                )
                storage = _storage_key(coordinate.registry_id)
                source_csv = source / "data" / storage / f"{coordinate.dataset_id}.csv"
                source_schema = (
                    source
                    / "schemas"
                    / storage
                    / f"{coordinate.dataset_id}.schema.json"
                )
                csv_bytes = source_csv.read_bytes()
                schema_bytes = source_schema.read_bytes()
                rows = parse_canonical_csv(definition, csv_bytes)
                source_row_count += len(rows)
                projections = projection_map.get(
                    (coordinate.registry_id, coordinate.dataset_id), ()
                )
                projected_rows, technical_rows = _project_rows(
                    coordinate, rows, projections
                )

                schema_relative = (
                    f"schemas/{storage}/{coordinate.dataset_id}.schema.json"
                )
                schema_target = staging / schema_relative
                schema_target.parent.mkdir(parents=True, exist_ok=True)
                schema_target.write_bytes(schema_bytes)

                csv_relative: str | None = None
                if "CSV" in request.formats:
                    csv_relative = f"csv/{storage}/{coordinate.dataset_id}.csv"
                    csv_target = staging / csv_relative
                    csv_target.parent.mkdir(parents=True, exist_ok=True)
                    csv_target.write_bytes(csv_bytes)

                parquet_relative: str | None = None
                parquet_hash: str | None = None
                fingerprint: str | None = None
                if "PARQUET" in request.formats:
                    parquet_relative = (
                        f"parquet/{storage}/{coordinate.dataset_id}.parquet"
                    )
                    parquet_target = staging / parquet_relative
                    parquet_target.parent.mkdir(parents=True, exist_ok=True)
                    table = _arrow_table(
                        coordinate, definition, projected_rows, projections
                    )
                    pq.write_table(
                        table,
                        parquet_target,
                        **PYARROW_WRITE_OPTIONS,
                    )
                    parquet_hash = sha256_bytes(parquet_target.read_bytes())
                    fingerprint = _schema_fingerprint(table.schema)

                source_entry = source_entries[
                    (coordinate.registry_id, coordinate.dataset_id)
                ]
                table_entries.append(
                    ModelTableBinding(
                        source_registry_id=coordinate.registry_id,
                        source_registry_version=1,
                        source_dataset_id=coordinate.dataset_id,
                        source_dataset_version=1,
                        source_dataset_name=definition.name,
                        primary_consumption_class=PRIMARY_CONSUMPTION_CLASS[
                            coordinate.dataset_id
                        ],
                        included_by_profile=request.profile_id,
                        semantic_owners=definition.semantic_owners,
                        source_schema_path=schema_relative,
                        source_schema_hash=source_entry.schema_sha256,
                        source_data_hash=source_entry.data_sha256,
                        row_count=len(rows),
                        primary_key=("row_key",),
                        unique_keys=definition.unique_keys,
                        default_sort=("row_key",),
                        logical_table_digest=sha256_bytes(
                            canonical_json_bytes(list(rows))
                        ),
                        technical_projection_digest=sha256_bytes(
                            canonical_json_bytes(list(technical_rows))
                        ),
                        relationship_key_projections=tuple(
                            item.relationship_id for item in projections
                        ),
                        csv_path=csv_relative,
                        csv_hash=(sha256_bytes(csv_bytes) if csv_relative else None),
                        parquet_path=parquet_relative,
                        parquet_hash=parquet_hash,
                        physical_schema_fingerprint=fingerprint,
                        duckdb_schema=(
                            duckdb_schema(coordinate.registry_id)
                            if "DUCKDB" in request.formats
                            else None
                        ),
                        duckdb_object=(
                            portable_alias(
                                coordinate.registry_id,
                                coordinate.dataset_id,
                                definition.name,
                            )
                            if "DUCKDB" in request.formats
                            else None
                        ),
                    )
                )

            catalogue = _semantic_catalogue(request, coordinates)
            relationship_catalogue = relationship_plan(request.profile_id)
            scope = _canonical_scope(coordinates, request.formats)
            manifest = ModelManifest(
                contract_version=MODEL_CONTRACT,
                model_ref=request.model_ref,
                source_package_ref=source_manifest.export_ref,
                source_package_digest=request.expected_source_package_digest,
                source_export_ref=source_manifest.export_ref,
                source_query_revision=source_manifest.query_revision,
                source_semantic_as_of=source_manifest.semantic_as_of,
                source_scenario_set_digest=source_manifest.scenario_set_digest,
                source_compatibility_mode=source_manifest.compatibility_mode,
                source_registry_coordinates=(
                    {"registry_id": "P-EVIDENCE", "registry_version": 1},
                    {"registry_id": "Q-ANALYTICS", "registry_version": 1},
                ),
                source_relationship_contract_version=2,
                source_verification_status="VERIFIED",
                source_verification_contract=SOURCE_VERIFICATION_CONTRACT,
                profile_id=request.profile_id,
                profile_version=1,
                requested_formats=request.formats,
                producer_release=request.producer_release,
                built_at=request.built_at,
                parquet_writer_profile_ref=(
                    WRITER_PROFILE_REF if "PARQUET" in request.formats else None
                ),
                parquet_writer_profile_hash=(
                    PARQUET_WRITER_PROFILE.profile_hash
                    if "PARQUET" in request.formats
                    else None
                ),
                synthetic_data=True,
                synthetic_data_notice=source_manifest.synthetic_data_notice,
                table_entries=tuple(table_entries),
                semantic_catalogue_path="semantic-model.json",
                relationship_catalogue_path="relationships.json",
                checksum_ledger_path="checksums.json",
                canonical_digest_scope=scope,
                noncanonical_cache_manifest_path=(
                    DUCKDB_CACHE_MANIFEST_PATH
                    if "DUCKDB" in request.formats
                    else None
                ),
            )
            (staging / "semantic-model.json").write_bytes(
                canonical_json_bytes(catalogue.model_dump(mode="json"))
            )
            (staging / "relationships.json").write_bytes(
                canonical_json_bytes(
                    [item.model_dump(mode="json") for item in relationship_catalogue]
                )
            )
            (staging / "model-manifest.json").write_bytes(
                canonical_json_bytes(manifest.model_dump(mode="json"))
            )
            (staging / "README.txt").write_bytes(_readme(manifest))
            if tuple(
                sorted(
                    path.relative_to(staging).as_posix()
                    for path in staging.rglob("*")
                    if path.is_file()
                )
            ) != scope:
                raise ConsumerModelError("canonical output scope differs")
            ledger = ChecksumLedger(
                checksum_contract_version=1,
                files=tuple(
                    ChecksumEntry(
                        relative_path=relative,
                        sha256=sha256_bytes((staging / relative).read_bytes()),
                    )
                    for relative in scope
                ),
            )
            ledger_bytes = canonical_json_bytes(ledger.model_dump(mode="json"))
            (staging / "checksums.json").write_bytes(ledger_bytes)
            model_digest = sha256_bytes(ledger_bytes)
            (staging / "model.digest").write_text(
                model_digest + "\n", encoding="ascii", newline="\n"
            )
            if "DUCKDB" in request.formats:
                build_duckdb_cache(staging, manifest)
            verification = verify_consumer_model(
                VerifyConsumerModel(
                    request_contract_version="verify-consumer-model-request@v1",
                    model_path=staging,
                    source_package_path=source,
                    expected_model_digest=model_digest,
                    expected_source_package_digest=request.expected_source_package_digest,
                    verification_scope="FULL_SOURCE_EQUIVALENCE",
                )
            )
            if verification.status != "VERIFIED":
                raise ConsumerModelError(
                    f"staged consumer model failed R-C02: {verification.message}"
                )
            staging.replace(final_path)
            return BuildConsumerModelResult(
                result_contract_version="build-consumer-model-result@v1",
                model_ref=request.model_ref,
                model_path=final_path,
                model_digest=model_digest,
                source_package_digest=request.expected_source_package_digest,
                profile_id=request.profile_id,
                profile_version=1,
                canonical_file_count=len(scope) + 2,
                noncanonical_cache_file_count=(
                    2 if "DUCKDB" in request.formats else 0
                ),
                table_count=len(coordinates),
                source_row_count=source_row_count,
                technical_projection_count=len(
                    {
                        item.relationship_id
                        for values in projection_map.values()
                        for item in values
                    }
                ),
            )
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            raise

    def reproduce(
        self, request: ReproduceConsumerModel
    ) -> ReproduceConsumerModelResult:
        source_model = request.source_model_path.resolve()
        try:
            manifest = _read_json(
                source_model / "model-manifest.json", ModelManifest
            )
        except (OSError, ValueError, ValidationError):
            return ReproduceConsumerModelResult(
                result_contract_version="reproduce-consumer-model-result@v1",
                status="BUILD_FAILED",
                expected_model_digest=request.expected_model_digest,
                message="source model manifest is unavailable or invalid",
            )
        source_verification = verify_governed_export(request.source_package_path)
        if (
            source_verification.status != "VERIFIED"
            or source_verification.package_digest
            != request.expected_source_package_digest
        ):
            return ReproduceConsumerModelResult(
                result_contract_version="reproduce-consumer-model-result@v1",
                status="SOURCE_PACKAGE_UNAVAILABLE",
                expected_model_digest=request.expected_model_digest,
                message="exact source package is unavailable",
            )
        original_verification = verify_consumer_model(
            VerifyConsumerModel(
                request_contract_version="verify-consumer-model-request@v1",
                model_path=source_model,
                source_package_path=request.source_package_path,
                expected_model_digest=request.expected_model_digest,
                expected_source_package_digest=request.expected_source_package_digest,
                verification_scope="FULL_SOURCE_EQUIVALENCE",
            )
        )
        if original_verification.status != "VERIFIED":
            return ReproduceConsumerModelResult(
                result_contract_version="reproduce-consumer-model-result@v1",
                status="BUILD_FAILED",
                expected_model_digest=request.expected_model_digest,
                source_package_digest=source_verification.package_digest,
                message="source consumer model is not verified",
            )
        if manifest.parquet_writer_profile_ref not in {None, WRITER_PROFILE_REF}:
            return ReproduceConsumerModelResult(
                result_contract_version="reproduce-consumer-model-result@v1",
                status="WRITER_PROFILE_UNAVAILABLE",
                expected_model_digest=request.expected_model_digest,
                source_package_digest=source_verification.package_digest,
                message="exact Parquet writer profile is unavailable",
            )
        duckdb_storage_version = None
        if "DUCKDB" in manifest.requested_formats:
            try:
                cache_manifest = read_duckdb_cache_manifest(
                    source_model / DUCKDB_CACHE_MANIFEST_PATH
                )
                duckdb_storage_version = (
                    cache_manifest.storage_compatibility_version
                )
            except (OSError, ValueError, ValidationError):
                return ReproduceConsumerModelResult(
                    result_contract_version="reproduce-consumer-model-result@v1",
                    status="WRITER_PROFILE_UNAVAILABLE",
                    expected_model_digest=request.expected_model_digest,
                    source_package_digest=source_verification.package_digest,
                    message="exact DuckDB cache profile is unavailable",
                )
        try:
            result = self.build(
                BuildConsumerModel(
                    request_contract_version="build-consumer-model-request@v1",
                    model_ref=manifest.model_ref,
                    source_package_path=request.source_package_path,
                    expected_source_package_digest=request.expected_source_package_digest,
                    profile_id=manifest.profile_id,
                    profile_version=1,
                    formats=manifest.requested_formats,
                    parquet_writer_profile_ref=manifest.parquet_writer_profile_ref,
                    parquet_writer_profile_hash=manifest.parquet_writer_profile_hash,
                    duckdb_storage_compatibility_version=duckdb_storage_version,
                    output_path=request.reproduction_output_path,
                    producer_release=manifest.producer_release,
                    built_at=manifest.built_at,
                )
            )
        except (ConsumerModelError, OSError, ValueError, ValidationError):
            return ReproduceConsumerModelResult(
                result_contract_version="reproduce-consumer-model-result@v1",
                status="BUILD_FAILED",
                expected_model_digest=request.expected_model_digest,
                source_package_digest=source_verification.package_digest,
                message="consumer-model reproduction failed",
            )
        return ReproduceConsumerModelResult(
            result_contract_version="reproduce-consumer-model-result@v1",
            status=(
                "REPRODUCED"
                if result.model_digest == request.expected_model_digest
                else "DIGEST_MISMATCH"
            ),
            expected_model_digest=request.expected_model_digest,
            actual_model_digest=result.model_digest,
            source_package_digest=result.source_package_digest,
            message=(
                (
                    "the canonical consumer model reproduced byte-for-byte and "
                    "the non-canonical DuckDB cache reverified logically"
                    if "DUCKDB" in manifest.requested_formats
                    else "the consumer model reproduced byte-for-byte"
                )
                if result.model_digest == request.expected_model_digest
                else "the reproduced model digest differs"
            ),
        )


def _verification_result(
    status: str,
    message: str,
    *,
    model_digest: str | None = None,
    source_digest: str | None = None,
    files: int = 0,
    tables: int = 0,
    columns: int = 0,
    relationships: int = 0,
) -> VerifyConsumerModelResult:
    return VerifyConsumerModelResult(
        result_contract_version="verify-consumer-model-result@v1",
        status=status,
        model_digest=model_digest,
        source_package_digest=source_digest,
        checked_file_count=files,
        checked_table_count=tables,
        checked_column_count=columns,
        checked_relationship_count=relationships,
        message=message,
    )


def verify_consumer_model(request: VerifyConsumerModel) -> VerifyConsumerModelResult:
    """R-C02 full source-equivalence and non-canonical cache verification."""

    root = request.model_path.resolve()
    source = request.source_package_path.resolve()
    try:
        source_verification = verify_governed_export(source)
        if (
            source_verification.status != "VERIFIED"
            or source_verification.package_digest
            != request.expected_source_package_digest
        ):
            raise _VerificationFailure("source package is not exact and VERIFIED")
        if not root.is_dir():
            raise _VerificationFailure("model directory is missing")
        source_manifest = _source_manifest(source)
        ledger = _read_json(root / "checksums.json", ChecksumLedger)
        ledger_bytes = (root / "checksums.json").read_bytes()
        digest = sha256_bytes(ledger_bytes)
        if (
            digest != request.expected_model_digest
            or (root / "model.digest").read_text(encoding="ascii")
            != digest + "\n"
        ):
            raise _VerificationFailure("detached model digest differs")
        manifest = cast(
            ModelManifest,
            _read_json(root / "model-manifest.json", ModelManifest),
        )
        if (
            manifest.source_package_digest
            != request.expected_source_package_digest
            or manifest.source_verification_status != "VERIFIED"
            or manifest.source_compatibility_mode != "EXACT_ORIGINAL"
            or manifest.source_relationship_contract_version != 2
        ):
            raise _VerificationFailure("model source binding differs")
        if (
            manifest.source_package_ref != source_manifest.export_ref
            or manifest.source_export_ref != source_manifest.export_ref
            or manifest.source_query_revision != source_manifest.query_revision
            or str(manifest.source_semantic_as_of)
            != str(source_manifest.semantic_as_of)
            or manifest.source_scenario_set_digest
            != source_manifest.scenario_set_digest
            or manifest.synthetic_data_notice
            != source_manifest.synthetic_data_notice
        ):
            raise _VerificationFailure("model snapshot coordinate differs")
        ledger_paths = tuple(item.relative_path for item in ledger.files)
        expected_scope = _canonical_scope(
            _selected_coordinates(manifest.profile_id), manifest.requested_formats
        )
        if "PARQUET" in manifest.requested_formats:
            validate_writer_runtime()
        if "DUCKDB" in manifest.requested_formats:
            validate_duckdb_runtime()
        if (
            ledger_paths != tuple(sorted(set(ledger_paths)))
            or ledger_paths != manifest.canonical_digest_scope
            or ledger_paths != expected_scope
        ):
            raise _VerificationFailure("checksum ledger scope differs")
        actual_paths = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        }
        cache_paths = (
            {DUCKDB_CACHE_MANIFEST_PATH, "warehouse/finance-assurance.duckdb"}
            if "DUCKDB" in manifest.requested_formats
            else set()
        )
        if actual_paths != {
            *ledger_paths,
            "checksums.json",
            "model.digest",
            *cache_paths,
        }:
            raise _VerificationFailure("model file inventory differs")
        for entry in ledger.files:
            if sha256_bytes((root / entry.relative_path).read_bytes()) != entry.sha256:
                raise _VerificationFailure("model file hash differs")
        coordinates = _selected_coordinates(manifest.profile_id)
        expected_ids = {
            (item.registry_id, item.dataset_id) for item in coordinates
        }
        entries = {
            (item.source_registry_id, item.source_dataset_id): item
            for item in manifest.table_entries
        }
        if set(entries) != expected_ids or len(entries) != len(manifest.table_entries):
            raise _VerificationFailure("profile table inventory differs")
        catalogue = cast(
            SemanticCatalogue,
            _read_json(root / manifest.semantic_catalogue_path, SemanticCatalogue),
        )
        expected_catalogue = _semantic_catalogue(
            BuildConsumerModel(
                request_contract_version="build-consumer-model-request@v1",
                model_ref=manifest.model_ref,
                source_package_path=source,
                expected_source_package_digest=manifest.source_package_digest,
                profile_id=manifest.profile_id,
                profile_version=1,
                formats=manifest.requested_formats,
                parquet_writer_profile_ref=manifest.parquet_writer_profile_ref,
                parquet_writer_profile_hash=manifest.parquet_writer_profile_hash,
                duckdb_storage_compatibility_version=(
                    DUCKDB_STORAGE_COMPATIBILITY_VERSION
                    if "DUCKDB" in manifest.requested_formats
                    else None
                ),
                output_path=root,
                producer_release=manifest.producer_release,
                built_at=manifest.built_at,
            ),
            coordinates,
        )
        if catalogue != expected_catalogue:
            raise _VerificationFailure("semantic catalogue differs")
        if (root / "README.txt").read_bytes() != _readme(manifest):
            raise _VerificationFailure("model README differs")
        if (root / "README.txt").read_bytes() != _readme(manifest):
            raise _VerificationFailure("model README differs")
        plan = relationship_plan(manifest.profile_id)
        relationships_bytes = (root / manifest.relationship_catalogue_path).read_bytes()
        if relationships_bytes != canonical_json_bytes(
            [item.model_dump(mode="json") for item in plan]
        ):
            raise _VerificationFailure("relationship catalogue differs")
        validate_relationship_graph(plan)
        projection_map = _selected_projection_map(manifest.profile_id)
        source_entries = {
            (item.registry_id, item.dataset_id): item
            for item in source_manifest.dataset_entries
        }
        for coordinate in coordinates:
            definition = _definition(coordinate.registry_id, coordinate.dataset_id)
            storage = _storage_key(coordinate.registry_id)
            source_csv = source / "data" / storage / f"{coordinate.dataset_id}.csv"
            source_schema = (
                source / "schemas" / storage / f"{coordinate.dataset_id}.schema.json"
            )
            rows = parse_canonical_csv(definition, source_csv.read_bytes())
            projections = projection_map.get(
                (coordinate.registry_id, coordinate.dataset_id), ()
            )
            projected_rows, technical_rows = _project_rows(
                coordinate, rows, projections
            )
            entry = entries[(coordinate.registry_id, coordinate.dataset_id)]
            source_entry = source_entries[
                (coordinate.registry_id, coordinate.dataset_id)
            ]
            expected_schema_path = (
                f"schemas/{storage}/{coordinate.dataset_id}.schema.json"
            )
            expected_csv_path = (
                f"csv/{storage}/{coordinate.dataset_id}.csv"
                if "CSV" in manifest.requested_formats
                else None
            )
            expected_duckdb_schema = (
                duckdb_schema(coordinate.registry_id)
                if "DUCKDB" in manifest.requested_formats
                else None
            )
            expected_duckdb_object = (
                portable_alias(
                    coordinate.registry_id, coordinate.dataset_id, definition.name
                )
                if "DUCKDB" in manifest.requested_formats
                else None
            )
            expected_parquet_path = (
                f"parquet/{storage}/{coordinate.dataset_id}.parquet"
                if "PARQUET" in manifest.requested_formats
                else None
            )
            if (
                entry.source_registry_version != 1
                or entry.source_dataset_version != 1
                or entry.source_dataset_name != definition.name
                or entry.primary_consumption_class
                != PRIMARY_CONSUMPTION_CLASS[coordinate.dataset_id]
                or entry.included_by_profile != manifest.profile_id
                or entry.semantic_owners != definition.semantic_owners
                or entry.source_schema_path != expected_schema_path
                or entry.source_schema_hash != source_entry.schema_sha256
                or entry.source_data_hash != source_entry.data_sha256
                or entry.source_schema_hash != sha256_bytes(source_schema.read_bytes())
                or entry.row_count != len(rows)
                or entry.logical_table_digest
                != sha256_bytes(canonical_json_bytes(list(rows)))
                or entry.technical_projection_digest
                != sha256_bytes(canonical_json_bytes(list(technical_rows)))
                or entry.relationship_key_projections
                != tuple(item.relationship_id for item in projections)
                or entry.default_sort != ("row_key",)
                or entry.primary_key != ("row_key",)
                or entry.unique_keys != definition.unique_keys
                or entry.csv_path != expected_csv_path
                or entry.csv_hash
                != (sha256_bytes(source_csv.read_bytes()) if expected_csv_path else None)
                or entry.parquet_path != expected_parquet_path
                or entry.duckdb_schema != expected_duckdb_schema
                or entry.duckdb_object != expected_duckdb_object
            ):
                raise _VerificationFailure("table binding differs")
            if (root / entry.source_schema_path).read_bytes() != source_schema.read_bytes():
                raise _VerificationFailure("source schema copy differs")
            if entry.csv_path is not None and (
                (root / entry.csv_path).read_bytes() != source_csv.read_bytes()
                or entry.csv_hash != sha256_bytes(source_csv.read_bytes())
            ):
                raise _VerificationFailure("canonical CSV copy differs")
            if entry.parquet_path is not None:
                parquet_bytes = (root / entry.parquet_path).read_bytes()
                table = pq.read_table(pa.BufferReader(parquet_bytes))
                expected_table = _arrow_table(
                    coordinate, definition, projected_rows, projections
                )
                if not table.equals(expected_table, check_metadata=True):
                    raise _VerificationFailure("Parquet logical table differs")
                if entry.parquet_hash != sha256_bytes(parquet_bytes):
                    raise _VerificationFailure("Parquet bytes differ from binding")
                if entry.physical_schema_fingerprint != _schema_fingerprint(table.schema):
                    raise _VerificationFailure("physical schema fingerprint differs")
        if "DUCKDB" in manifest.requested_formats:
            verify_duckdb_cache(root, manifest)
        return _verification_result(
            "VERIFIED",
            "consumer model verified with full source equivalence",
            model_digest=digest,
            source_digest=source_verification.package_digest,
            files=len(actual_paths),
            tables=len(coordinates),
            columns=len(catalogue.columns),
            relationships=len(plan),
        )
    except (
        _VerificationFailure,
        OSError,
        ValueError,
        TypeError,
        ValidationError,
        json.JSONDecodeError,
        pa.ArrowException,
        duckdb.Error,
    ) as error:
        return _verification_result("FAILED", str(error) or "verification failed")


def model_registry_binding() -> dict[str, str]:
    """Small diagnostic surface used by Artifact R cohesion audits."""

    return {
        "r_contract_version": R_CONTRACT_VERSION,
        "r_registry_hash": registry_contract_hash(),
        "parquet_profile_ref": WRITER_PROFILE_REF,
        "parquet_profile_hash": PARQUET_WRITER_PROFILE.profile_hash,
        "duckdb_engine_version": DUCKDB_ENGINE_VERSION,
        "duckdb_storage_compatibility_version": DUCKDB_STORAGE_COMPATIBILITY_VERSION,
        "duckdb_cache_contract": "duckdb-cache-manifest@v1",
    }
