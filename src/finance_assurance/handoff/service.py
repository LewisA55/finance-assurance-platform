"""Production build and verification service for Artifact S."""

from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

from finance_assurance.digestion.contracts import (
    ModelManifest,
    SemanticCatalogue,
    VerifyConsumerModel,
)
from finance_assurance.digestion.service import verify_consumer_model
from finance_assurance.exports.serialization import sha256_bytes
from finance_assurance.handoff.authorities import (
    AUTHORITY_BY_FILENAME,
    load_json_authority,
    read_authority_bytes,
    split_sql_authority,
    validate_authorities,
)
from finance_assurance.handoff.contracts import (
    BuildLocalAnalyticalHandoff,
    BuildLocalAnalyticalHandoffResult,
    VerifyLocalAnalyticalHandoff,
    VerifyLocalAnalyticalHandoffResult,
)
from finance_assurance.handoff.digests import canonical_json_file_bytes
from finance_assurance.handoff.metadata import (
    HandoffChecksumEntry,
    HandoffChecksumLedger,
    HandoffLimitations,
    HandoffManifest,
    MetadataDocument,
    MetadataManifestEntry,
    NoncanonicalWorkbookManifest,
    SqlManifestEntry,
)
from finance_assurance.handoff.metadata_builder import build_metadata_documents
from finance_assurance.handoff.paths import (
    S_FIXED_CANONICAL_PATHS,
    S_METADATA_PATHS,
    S_NONCANONICAL_PATHS,
)
from finance_assurance.handoff.profiles import (
    XLSX_TYPE_MAP_HASH,
    XLSX_WRITER_PROFILE_HASH,
)
from finance_assurance.handoff.workbook import build_workbook, workbook_sha256
from finance_assurance.runtime.canonical import canonical_sha256


class LocalAnalyticalHandoffError(RuntimeError):
    """Raised when Artifact S cannot make a verified publication."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LocalAnalyticalHandoffError(f"invalid JSON authority: {path}") from error


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_file_bytes(value))


def _is_reparse_point(path: Path) -> bool:
    try:
        attributes = path.lstat().st_file_attributes
    except AttributeError:
        return path.is_symlink()
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _reject_links(root: Path) -> None:
    if _is_reparse_point(root):
        raise LocalAnalyticalHandoffError(f"path firewall rejected reparse point: {root}")
    for path in root.rglob("*"):
        if _is_reparse_point(path):
            raise LocalAnalyticalHandoffError(
                f"path firewall rejected reparse point below source: {path}"
            )


def _preflight_paths(request: BuildLocalAnalyticalHandoff) -> tuple[Path, Path, Path]:
    source_model = request.source_model_path.resolve(strict=True)
    source_package = request.source_package_path.resolve(strict=True)
    output = request.output_path.resolve()
    if not source_model.is_dir() or not source_package.is_dir():
        raise LocalAnalyticalHandoffError("both Artifact R and source package paths must be directories")
    if output.exists():
        raise LocalAnalyticalHandoffError("final output path already exists")
    for source in (source_model, source_package):
        if output == source or output.is_relative_to(source) or source.is_relative_to(output):
            raise LocalAnalyticalHandoffError("output and source directory trees must be disjoint")
        _reject_links(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    return source_model, source_package, output


def _verify_r_model(
    *, model: Path, source: Path, model_digest: str, source_digest: str
) -> None:
    result = verify_consumer_model(
        VerifyConsumerModel(
            request_contract_version="verify-consumer-model-request@v1",
            model_path=model,
            source_package_path=source,
            expected_model_digest=model_digest,
            expected_source_package_digest=source_digest,
            verification_scope="FULL_SOURCE_EQUIVALENCE",
        )
    )
    if result.status != "VERIFIED":
        raise LocalAnalyticalHandoffError(f"Artifact R verification failed: {result.message}")


def _model_manifest(root: Path) -> ModelManifest:
    return ModelManifest.model_validate_json(
        (root / "source-model/model-manifest.json").read_bytes()
    )


def _semantic(root: Path) -> SemanticCatalogue:
    return SemanticCatalogue.model_validate_json(
        (root / "source-model/semantic-model.json").read_bytes()
    )


def _metadata_entries(documents: dict[str, MetadataDocument]) -> tuple[MetadataManifestEntry, ...]:
    result = []
    for path in S_METADATA_PATHS:
        document = documents[path]
        result.append(
            MetadataManifestEntry(
                path=path,
                contract_version=document.contract_version,
                payload_sha256=canonical_sha256(document.payload.model_dump(mode="json")),
                source_document_bindings=document.source_documents,
                source_dataset_bindings=document.source_datasets,
                algorithm_refs=tuple(sorted({item.algorithm_ref for item in document.field_provenance})),
            )
        )
    return tuple(result)


def _sql_entries() -> tuple[SqlManifestEntry, ...]:
    starter = AUTHORITY_BY_FILENAME["starter-queries-v1.sql"]
    reconciliation = AUTHORITY_BY_FILENAME["reconciliation-queries-v1.sql"]
    return (
        SqlManifestEntry(
            path="examples/starter-queries.sql",
            query_ids=tuple(item[0] for item in split_sql_authority("starter-queries-v1.sql")),
            authority_ref="S-SQL-FIXTURES@v1",
            authority_file_sha256=starter.file_sha256,
            validation_registry_hash=None,
        ),
        SqlManifestEntry(
            path="examples/reconciliation-queries.sql",
            query_ids=tuple(item[0] for item in split_sql_authority("reconciliation-queries-v1.sql")),
            authority_ref="S-SQL-FIXTURES@v1",
            authority_file_sha256=reconciliation.file_sha256,
            validation_registry_hash=(
                "sha256:36255992b12b0176f290ec2fa033e5655d8ca4b3a2e4cbd3a522a1de295f7cb8"
            ),
        ),
    )


def _canonical_scope(manifest: ModelManifest) -> tuple[str, ...]:
    embedded = [f"source-model/{path}" for path in manifest.canonical_digest_scope]
    return tuple(
        sorted(
            {
                *S_FIXED_CANONICAL_PATHS,
                *embedded,
                "source-model/checksums.json",
                "source-model/model.digest",
            }
        )
    )


def _write_fixed_authorities(root: Path) -> None:
    mappings = {
        "README.md": "readme-v1.md",
        "limitations.json": "limitations-v1.json",
        "examples/starter-queries.sql": "starter-queries-v1.sql",
        "examples/reconciliation-queries.sql": "reconciliation-queries-v1.sql",
    }
    for target, authority in mappings.items():
        path = root / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(read_authority_bytes(authority))


def _seal(root: Path, scope: tuple[str, ...]) -> tuple[str, HandoffChecksumLedger]:
    ledger = HandoffChecksumLedger(
        contract_version="handoff-checksum-ledger@v1",
        files=tuple(
            HandoffChecksumEntry(
                path=path,
                sha256=sha256_bytes((root / path).read_bytes()),
                byte_count=(root / path).stat().st_size,
            )
            for path in scope
        ),
    )
    ledger_bytes = canonical_json_file_bytes(ledger.model_dump(mode="json"))
    (root / "checksums.json").write_bytes(ledger_bytes)
    digest = sha256_bytes(ledger_bytes)
    (root / "handoff.digest").write_text(digest + "\n", encoding="ascii", newline="\n")
    return digest, ledger


def _actual_file_inventory(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def _verify_metadata_sources(root: Path, document: MetadataDocument) -> None:
    declared = {item.path: item.sha256 for item in document.source_documents}
    for path, expected in declared.items():
        if sha256_bytes((root / path).read_bytes()) != expected:
            raise LocalAnalyticalHandoffError(f"metadata source binding differs: {path}")
    for row in document.field_provenance:
        for pointer in row.source_pointers:
            if pointer.pointer_kind == "JSON_POINTER":
                if pointer.source_document_path not in declared:
                    raise LocalAnalyticalHandoffError("provenance pointer lacks an authenticated source binding")
                if pointer.json_pointer != "/":
                    raise LocalAnalyticalHandoffError("production v1 only admits authenticated root projections")


class LocalAnalyticalHandoffService:
    """Build S-C01 and verify S-C02 against real filesystem artifacts."""

    def build(self, request: BuildLocalAnalyticalHandoff) -> BuildLocalAnalyticalHandoffResult:
        validate_authorities()
        if request.xlsx_type_map_hash != XLSX_TYPE_MAP_HASH or request.xlsx_writer_profile_hash != XLSX_WRITER_PROFILE_HASH:
            raise LocalAnalyticalHandoffError("unsupported XLSX authority coordinate")
        source_model, source_package, output = _preflight_paths(request)
        _verify_r_model(
            model=source_model,
            source=source_package,
            model_digest=request.expected_model_digest,
            source_digest=request.expected_source_package_digest,
        )
        source_manifest = ModelManifest.model_validate_json(
            (source_model / "model-manifest.json").read_bytes()
        )
        if (
            source_manifest.profile_id != "LINEAGE"
            or source_manifest.profile_version != 1
            or source_manifest.requested_formats != ("CSV", "PARQUET", "DUCKDB")
        ):
            raise LocalAnalyticalHandoffError("Artifact S requires exact R LINEAGE@1 CSV/Parquet/DuckDB")

        staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
        try:
            shutil.copytree(source_model, staging / "source-model")
            _verify_r_model(
                model=staging / "source-model",
                source=source_package,
                model_digest=request.expected_model_digest,
                source_digest=request.expected_source_package_digest,
            )
            _verify_r_model(
                model=source_model,
                source=source_package,
                model_digest=request.expected_model_digest,
                source_digest=request.expected_source_package_digest,
            )
            _write_fixed_authorities(staging)
            HandoffLimitations.model_validate_json(
                canonical_json_file_bytes(load_json_authority("limitations-v1.json"))
            )
            documents = build_metadata_documents(
                root=staging,
                handoff_ref=request.handoff_ref,
                source_model_digest=request.expected_model_digest,
            )
            for path, document in documents.items():
                _write_json(staging / path, document.model_dump(mode="json"))
            workbook = build_workbook(
                root=staging,
                handoff_ref=request.handoff_ref,
                source_model_digest=request.expected_model_digest,
                built_at=request.built_at,
                documents=documents,
            )
            workbook_path = staging / "excel/finance-assurance-data-pack.xlsx"
            workbook_path.parent.mkdir(parents=True, exist_ok=True)
            workbook_path.write_bytes(workbook.payload)
            workbook_manifest = NoncanonicalWorkbookManifest(
                contract_version="handoff-manifest@v1",
                handoff_ref=request.handoff_ref,
                source_model_ref=source_manifest.model_ref,
                source_model_digest=request.expected_model_digest,
                source_package_digest=request.expected_source_package_digest,
                workbook_path="excel/finance-assurance-data-pack.xlsx",
                workbook_sha256=workbook_sha256(workbook.payload),
                workbook_byte_count=len(workbook.payload),
                writer_profile_ref="XLSXWRITER-3.2.9@v1",
                writer_profile_hash=XLSX_WRITER_PROFILE_HASH,
                logical_workbook_digest=workbook.logical_digest,
                sheet_entries=workbook.sheet_entries,
                openxml_part_inventory=workbook.openxml_inventory,
            )
            _write_json(
                staging / "excel/noncanonical-workbook.json",
                workbook_manifest.model_dump(mode="json"),
            )
            semantic = _semantic(staging)
            canonical_scope = _canonical_scope(source_manifest)
            handoff_manifest = HandoffManifest(
                contract_version="handoff-manifest@v1",
                handoff_ref=request.handoff_ref,
                source_model_ref=source_manifest.model_ref,
                source_model_path="source-model",
                source_model_digest=request.expected_model_digest,
                source_package_ref=source_manifest.source_package_ref,
                source_package_digest=request.expected_source_package_digest,
                source_export_ref=source_manifest.source_export_ref,
                source_query_revision=source_manifest.source_query_revision,
                source_semantic_as_of=source_manifest.source_semantic_as_of,
                source_scenario_set_digest=source_manifest.source_scenario_set_digest,
                source_compatibility_mode="EXACT_ORIGINAL",
                source_verification_status="VERIFIED",
                profile_id="LINEAGE",
                profile_version=1,
                source_formats=("CSV", "PARQUET", "DUCKDB"),
                synthetic_data=True,
                synthetic_data_notice=source_manifest.synthetic_data_notice,
                table_count=len(source_manifest.table_entries),
                source_row_count=sum(item.row_count for item in source_manifest.table_entries),
                catalogue_column_count=len(semantic.columns),
                relationship_count=len(semantic.relationships),
                measure_count=len(semantic.measures),
                validation_check_count=workbook.validation_check_count,
                validation_registry_ref="S-VALIDATION-C001-CT1@v1",
                validation_registry_hash=request.validation_registry_hash,
                canonical_digest_scope=canonical_scope,
                noncanonical_path_scope=S_NONCANONICAL_PATHS,
                metadata_entries=_metadata_entries(documents),
                sql_entries=_sql_entries(),
                r_noncanonical_cache_manifest_path="source-model/noncanonical-cache.json",
                r_duckdb_path="source-model/warehouse/finance-assurance.duckdb",
                xlsx_noncanonical_manifest_path="excel/noncanonical-workbook.json",
                xlsx_type_map_ref="XLSX-TYPE-MAP@v1",
                xlsx_type_map_hash=XLSX_TYPE_MAP_HASH,
                xlsx_writer_profile_ref="XLSXWRITER-3.2.9@v1",
                xlsx_writer_profile_hash=XLSX_WRITER_PROFILE_HASH,
                xlsx_logical_workbook_digest=workbook.logical_digest,
                consumer_suitability_path="metadata/consumer-suitability.json",
                producer_release=request.producer_release,
                built_at=request.built_at,
            )
            _write_json(staging / "handoff-manifest.json", handoff_manifest.model_dump(mode="json"))
            handoff_digest, ledger = _seal(staging, canonical_scope)
            verification = verify_local_analytical_handoff(
                VerifyLocalAnalyticalHandoff(
                    request_contract_version="verify-local-analytical-handoff-request@v1",
                    handoff_path=staging,
                    source_package_path=source_package,
                    expected_handoff_digest=handoff_digest,
                    expected_model_digest=request.expected_model_digest,
                    expected_source_package_digest=request.expected_source_package_digest,
                    verification_scope="FULL_HANDOFF_EQUIVALENCE",
                )
            )
            if verification.status != "VERIFIED":
                raise LocalAnalyticalHandoffError("staged handoff did not verify")
            if output.exists():
                raise LocalAnalyticalHandoffError("output became occupied before publication")
            os.replace(staging, output)
            return BuildLocalAnalyticalHandoffResult(
                result_contract_version="build-local-analytical-handoff-result@v1",
                status="PUBLISHED",
                handoff_ref=request.handoff_ref,
                handoff_path=output,
                handoff_digest=handoff_digest,
                source_model_ref=source_manifest.model_ref,
                source_model_digest=request.expected_model_digest,
                source_package_digest=request.expected_source_package_digest,
                canonical_file_count=len(ledger.files),
                noncanonical_file_count=len(S_NONCANONICAL_PATHS),
                table_count=len(source_manifest.table_entries),
                source_row_count=sum(item.row_count for item in source_manifest.table_entries),
                catalogue_column_count=len(semantic.columns),
                relationship_count=len(semantic.relationships),
                measure_count=len(semantic.measures),
                validation_check_count=workbook.validation_check_count,
                workbook_logical_digest=workbook.logical_digest,
                checked_sheet_count=len(workbook.sheet_entries),
            )
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            raise

    def verify(self, request: VerifyLocalAnalyticalHandoff) -> VerifyLocalAnalyticalHandoffResult:
        return verify_local_analytical_handoff(request)


def verify_local_analytical_handoff(
    request: VerifyLocalAnalyticalHandoff,
) -> VerifyLocalAnalyticalHandoffResult:
    """Verify canonical bytes, embedded R, and noncanonical binary equivalence."""

    validate_authorities()
    root = request.handoff_path.resolve(strict=True)
    source = request.source_package_path.resolve(strict=True)
    if not root.is_dir() or not source.is_dir():
        raise LocalAnalyticalHandoffError("handoff and source paths must be directories")
    _reject_links(root)
    _reject_links(source)
    manifest = HandoffManifest.model_validate_json(
        (root / "handoff-manifest.json").read_bytes()
    )
    if (
        manifest.source_model_digest != request.expected_model_digest
        or manifest.source_package_digest != request.expected_source_package_digest
        or manifest.xlsx_type_map_hash != XLSX_TYPE_MAP_HASH
        or manifest.xlsx_writer_profile_hash != XLSX_WRITER_PROFILE_HASH
    ):
        raise LocalAnalyticalHandoffError("handoff manifest request binding differs")
    _verify_r_model(
        model=root / "source-model",
        source=source,
        model_digest=request.expected_model_digest,
        source_digest=request.expected_source_package_digest,
    )
    source_manifest = _model_manifest(root)
    expected_scope = _canonical_scope(source_manifest)
    if manifest.canonical_digest_scope != expected_scope or manifest.noncanonical_path_scope != S_NONCANONICAL_PATHS:
        raise LocalAnalyticalHandoffError("handoff path scopes differ")
    ledger = HandoffChecksumLedger.model_validate_json(
        (root / "checksums.json").read_bytes()
    )
    if tuple(item.path for item in ledger.files) != expected_scope:
        raise LocalAnalyticalHandoffError("handoff checksum ledger scope differs")
    ledger_bytes = (root / "checksums.json").read_bytes()
    if ledger_bytes != canonical_json_file_bytes(ledger.model_dump(mode="json")):
        raise LocalAnalyticalHandoffError("handoff checksum ledger bytes are noncanonical")
    digest = sha256_bytes(ledger_bytes)
    if (
        digest != request.expected_handoff_digest
        or (root / "handoff.digest").read_bytes() != (digest + "\n").encode("ascii")
    ):
        raise LocalAnalyticalHandoffError("detached handoff digest differs")
    for entry in ledger.files:
        payload = (root / entry.path).read_bytes()
        if len(payload) != entry.byte_count or sha256_bytes(payload) != entry.sha256:
            raise LocalAnalyticalHandoffError(f"canonical handoff file differs: {entry.path}")
    expected_inventory = {*expected_scope, "checksums.json", "handoff.digest", *S_NONCANONICAL_PATHS}
    if _actual_file_inventory(root) != expected_inventory:
        raise LocalAnalyticalHandoffError("handoff file inventory differs")
    fixed = {
        "README.md": "readme-v1.md",
        "limitations.json": "limitations-v1.json",
        "examples/starter-queries.sql": "starter-queries-v1.sql",
        "examples/reconciliation-queries.sql": "reconciliation-queries-v1.sql",
    }
    for path, authority in fixed.items():
        if (root / path).read_bytes() != read_authority_bytes(authority):
            raise LocalAnalyticalHandoffError(f"fixed authority differs: {path}")
    documents: dict[str, MetadataDocument] = {}
    for path in S_METADATA_PATHS:
        document = MetadataDocument.model_validate_json((root / path).read_bytes())
        _verify_metadata_sources(root, document)
        documents[path] = document
    rebuilt_documents = build_metadata_documents(
        root=root,
        handoff_ref=manifest.handoff_ref,
        source_model_digest=request.expected_model_digest,
    )
    for path, rebuilt in rebuilt_documents.items():
        if (root / path).read_bytes() != canonical_json_file_bytes(rebuilt.model_dump(mode="json")):
            raise LocalAnalyticalHandoffError(f"metadata derivation differs: {path}")
    rebuilt_workbook = build_workbook(
        root=root,
        handoff_ref=manifest.handoff_ref,
        source_model_digest=request.expected_model_digest,
        built_at=manifest.built_at,
        documents=rebuilt_documents,
    )
    workbook_path = root / "excel/finance-assurance-data-pack.xlsx"
    workbook_payload = workbook_path.read_bytes()
    workbook_manifest = NoncanonicalWorkbookManifest.model_validate_json(
        (root / "excel/noncanonical-workbook.json").read_bytes()
    )
    if (
        workbook_payload != rebuilt_workbook.payload
        or workbook_manifest.workbook_sha256 != workbook_sha256(workbook_payload)
        or workbook_manifest.workbook_byte_count != len(workbook_payload)
        or workbook_manifest.logical_workbook_digest != rebuilt_workbook.logical_digest
        or workbook_manifest.sheet_entries != rebuilt_workbook.sheet_entries
        or workbook_manifest.openxml_part_inventory != rebuilt_workbook.openxml_inventory
        or manifest.xlsx_logical_workbook_digest != rebuilt_workbook.logical_digest
    ):
        raise LocalAnalyticalHandoffError("XLSX binary or logical equivalence differs")
    semantic = _semantic(root)
    if (
        manifest.table_count != len(source_manifest.table_entries)
        or manifest.source_row_count != sum(item.row_count for item in source_manifest.table_entries)
        or manifest.catalogue_column_count != len(semantic.columns)
        or manifest.relationship_count != len(semantic.relationships)
        or manifest.measure_count != len(semantic.measures)
        or manifest.validation_check_count != rebuilt_workbook.validation_check_count
        or manifest.metadata_entries != _metadata_entries(rebuilt_documents)
        or manifest.sql_entries != _sql_entries()
    ):
        raise LocalAnalyticalHandoffError("handoff manifest derived counts or bindings differ")
    return VerifyLocalAnalyticalHandoffResult(
        result_contract_version="verify-local-analytical-handoff-result@v1",
        status="VERIFIED",
        handoff_digest=digest,
        source_model_digest=request.expected_model_digest,
        source_package_digest=request.expected_source_package_digest,
        checked_canonical_file_count=len(ledger.files),
        checked_noncanonical_file_count=len(S_NONCANONICAL_PATHS),
        checked_table_count=len(source_manifest.table_entries),
        checked_column_count=len(semantic.columns),
        checked_relationship_count=len(semantic.relationships),
        checked_measure_count=len(semantic.measures),
        checked_validation_count=rebuilt_workbook.validation_check_count,
        checked_sheet_count=len(rebuilt_workbook.sheet_entries),
        canonical_byte_status="VERIFIED",
        same_build_binary_status="VERIFIED",
        logical_equivalence_status="VERIFIED",
    )
