"""P-C01/P-C02/P-C03 governed export application service."""

from __future__ import annotations

import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import cast
from uuid import uuid4

from pydantic import ValidationError

from finance_assurance.exports.contracts import (
    BuildGovernedExport,
    BuildGovernedExportResult,
    ChecksumEntry,
    ChecksumLedger,
    DatasetManifestEntry,
    DatasetRegistryEntry,
    ExportDiscoveryDescriptor,
    GovernedExportManifest,
    ReproductionResult,
    VerificationResult,
    VerificationStatus,
)
from finance_assurance.exports.discovery import compile_export_discovery
from finance_assurance.exports.registry import (
    DATASETS,
    REGISTRY_ID,
    REGISTRY_VERSION,
    RELATIONSHIPS,
    STORAGE_KEY,
    registry_contract_hash,
)
from finance_assurance.exports.serialization import (
    canonical_csv_bytes,
    canonical_json_bytes,
    parse_canonical_csv,
    sha256_bytes,
)
from finance_assurance.exports.tabularize import (
    ExecutedPublicQuery,
    query_instance_ref,
    tabularize,
)
from finance_assurance.product.contracts import PublicSuccessEnvelope
from finance_assurance.product.demo_scenarios import DemoScenarioSet
from finance_assurance.product.query_service import PublicQueryService
from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.persistence.models import QueryContext
from finance_assurance.runtime.persistence.ports import PersistenceBoundary

PACKAGE_CONTRACT = "governed-export-package@v1"
PRODUCER_RELEASE = "0.1.0"


def _supported_registry_set(
    registry_ids: tuple[str, ...],
) -> tuple[
    tuple[object, ...],
    tuple[dict[str, object], ...],
    dict[str, tuple[str, int, str]],
]:
    """Resolve either closed package registry variant without open discovery."""

    if registry_ids == (REGISTRY_ID,):
        return (
            DATASETS,
            RELATIONSHIPS,
            {
                REGISTRY_ID: (
                    STORAGE_KEY,
                    REGISTRY_VERSION,
                    registry_contract_hash(),
                )
            },
        )
    if registry_ids == (REGISTRY_ID, "Q-ANALYTICS"):
        from finance_assurance.analytics.registry import (
            DATASETS as Q_DATASETS,
        )
        from finance_assurance.analytics.registry import (
            REGISTRY_VERSION as Q_REGISTRY_VERSION,
        )
        from finance_assurance.analytics.registry import (
            RELATIONSHIPS as Q_RELATIONSHIPS,
        )
        from finance_assurance.analytics.registry import (
            STORAGE_KEY as Q_STORAGE_KEY,
        )
        from finance_assurance.analytics.registry import (
            registry_contract_hash as q_registry_contract_hash,
        )

        return (
            (*DATASETS, *Q_DATASETS),
            (*RELATIONSHIPS, *Q_RELATIONSHIPS),
            {
                REGISTRY_ID: (
                    STORAGE_KEY,
                    REGISTRY_VERSION,
                    registry_contract_hash(),
                ),
                "Q-ANALYTICS": (
                    Q_STORAGE_KEY,
                    Q_REGISTRY_VERSION,
                    q_registry_contract_hash(),
                ),
            },
        )
    raise _VerificationFailure("UNSUPPORTED_CONTRACT", "registry set is not closed")


class GovernedExportError(RuntimeError):
    """A closed Artifact P build failure that publishes no package."""


class _VerificationFailure(RuntimeError):
    def __init__(self, status: VerificationStatus, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def _json_file(path: Path, model: type[GovernedExportManifest]) -> GovernedExportManifest:
    try:
        payload = path.read_bytes()
        parsed = model.model_validate_json(payload)
    except (OSError, ValueError, ValidationError) as error:
        raise _VerificationFailure("SCHEMA_INVALID", "manifest is invalid") from error
    if canonical_json_bytes(parsed.model_dump(mode="json")) != payload:
        raise _VerificationFailure("SCHEMA_INVALID", "manifest is not canonical")
    return parsed


def _readme(manifest: GovernedExportManifest) -> bytes:
    lines = (
        "Finance & Assurance Platform - Governed Evidence Package",
        "",
        f"Export: {manifest.export_ref}",
        f"Contract: {manifest.contract_version}",
        f"Registry: {REGISTRY_ID}@v{REGISTRY_VERSION}",
        f"Snapshot revision: {manifest.query_revision}",
        f"Semantic as-of: {manifest.semantic_as_of}",
        "Synthetic data: true",
        f"Notice: {manifest.synthetic_data_notice}",
        "",
        "Verify this directory before use. The evidence registry is not an",
        "analytical registry and does not authorise Excel or Power BI modelling.",
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _remove_staging(path: Path, parent: Path) -> None:
    resolved = path.resolve()
    if resolved.parent != parent.resolve() or not resolved.name.startswith("."):
        raise GovernedExportError("refusing to remove an unsafe staging path")
    if resolved.exists():
        shutil.rmtree(resolved)


class GovernedExportService:
    """Build and reproduce Artifact P packages without reading stores directly."""

    def __init__(
        self,
        boundary: PersistenceBoundary,
        *,
        scenarios: DemoScenarioSet,
        descriptor: ExportDiscoveryDescriptor,
        producer_release: str = PRODUCER_RELEASE,
    ) -> None:
        self._boundary = boundary
        self._scenarios = scenarios
        self._descriptor = descriptor
        self._producer_release = producer_release
        self._public = PublicQueryService(
            boundary,
            scenarios=scenarios,
            workspace_ref=descriptor.workspace_ref,
        )

    def build(
        self,
        request: BuildGovernedExport,
        *,
        required_query_revision: int | None = None,
    ) -> BuildGovernedExportResult:
        if request.workspace_ref != self._descriptor.workspace_ref:
            raise GovernedExportError("workspace_ref does not match P-Q00")
        if request.discovery_descriptor_ref != self._descriptor.discovery_descriptor_ref:
            raise GovernedExportError("discovery descriptor reference does not match")
        if str(request.semantic_as_of) != str(self._descriptor.semantic_as_of):
            raise GovernedExportError("semantic_as_of does not match P-Q00")
        final_path = request.output_path.resolve()
        if final_path.exists():
            raise GovernedExportError("final output path already exists")
        final_path.parent.mkdir(parents=True, exist_ok=True)
        staging = final_path.parent / f".{final_path.name}.staging-{uuid4().hex}"
        session = self._boundary.open_query(
            QueryContext(semantic_as_of_time=str(request.semantic_as_of))
        )
        if required_query_revision is not None and session.revision != required_query_revision:
            raise GovernedExportError("source revision is unavailable")
        discovery = compile_export_discovery(
            self._descriptor,
            query_revision=session.revision,
            scenario_set_digest=canonical_sha256(
                self._scenarios.model_dump(mode="json")
            ),
        )
        executed: list[ExecutedPublicQuery] = []
        try:
            staging.mkdir()
            for owned in discovery.query_requests:
                result = self._public.execute_in_session(owned.request, session)
                if not hasattr(result, "view_contract"):
                    code = getattr(result, "error_code", "INTERNAL_FAILURE")
                    raise GovernedExportError(
                        f"Artifact O query {owned.request.query_id} failed: {code}"
                    )
                envelope = cast(PublicSuccessEnvelope, result)
                if (
                    envelope.query_revision != session.revision
                    or str(envelope.semantic_as_of_time) != str(discovery.semantic_as_of)
                    or envelope.compatibility_read_mode != "EXACT_ORIGINAL"
                    or str(envelope.scenario_ref)
                    not in {item.scenario_ref for item in discovery.scenarios}
                ):
                    raise GovernedExportError("Artifact O snapshot mismatch")
                body = owned.request.model_dump(mode="json")
                request_hash = canonical_sha256(body)
                executed.append(
                    ExecutedPublicQuery(
                        request=owned.request,
                        envelope=envelope,
                        canonical_request_hash=request_hash,
                        query_instance_ref=query_instance_ref(body),
                    )
                )
            self._validate_manifest_membership(discovery, tuple(executed))
            rows = tabularize(
                discovery=discovery,
                executed=tuple(executed),
                export_ref=request.export_ref,
                exported_at=str(request.exported_at),
                producer_release=self._producer_release,
            )
            manifest = self._write_package_content(
                staging,
                request=request,
                discovery=discovery,
                executed=tuple(executed),
                rows=rows,
            )
            result = verify_governed_export(staging)
            if result.status != "VERIFIED" or result.package_digest is None:
                raise GovernedExportError(
                    "staging package verification failed: "
                    f"{result.status}: {result.message}"
                )
            staging.replace(final_path)
            return BuildGovernedExportResult(
                export_ref=request.export_ref,
                package_path=final_path,
                package_digest=result.package_digest,
                query_revision=manifest.query_revision,
                semantic_as_of=request.semantic_as_of,
                dataset_count=len(DATASETS),
                row_count=sum(item.row_count for item in manifest.dataset_entries),
            )
        except Exception:
            _remove_staging(staging, final_path.parent)
            raise

    def reproduce(
        self,
        package_path: Path,
    ) -> ReproductionResult:
        verification = verify_governed_export(package_path)
        if verification.status != "VERIFIED" or verification.package_digest is None:
            return ReproductionResult(
                status="BUILD_FAILED",
                expected_digest="sha256:" + "0" * 64,
                actual_digest=None,
                query_revision=None,
                message="the source package is not verified",
            )
        manifest = _json_file(package_path / "manifest.json", GovernedExportManifest)
        with tempfile.TemporaryDirectory(
            prefix="finance-assurance-reproduce-",
            dir=package_path.parent,
        ) as directory:
            output = Path(directory) / manifest.export_ref
            request = BuildGovernedExport(
                export_ref=manifest.export_ref,
                workspace_ref=manifest.workspace_ref,
                semantic_as_of=manifest.semantic_as_of,
                exported_at=manifest.exported_at,
                output_path=output,
                discovery_descriptor_ref=manifest.discovery_descriptor_ref,
                contract_version=manifest.contract_version,
            )
            try:
                rebuilt = self.build(
                    request,
                    required_query_revision=manifest.query_revision,
                )
            except GovernedExportError as error:
                status = (
                    "SOURCE_REVISION_UNAVAILABLE"
                    if "source revision" in str(error)
                    else "BUILD_FAILED"
                )
                return ReproductionResult(
                    status=status,
                    expected_digest=verification.package_digest,
                    actual_digest=None,
                    query_revision=None,
                    message=str(error),
                )
            return ReproductionResult(
                status=(
                    "REPRODUCED"
                    if rebuilt.package_digest == verification.package_digest
                    else "DIGEST_MISMATCH"
                ),
                expected_digest=verification.package_digest,
                actual_digest=rebuilt.package_digest,
                query_revision=rebuilt.query_revision,
                message=(
                    "the package reproduced byte-for-byte"
                    if rebuilt.package_digest == verification.package_digest
                    else "the reproduced digest differs"
                ),
            )

    def _validate_manifest_membership(
        self,
        discovery: object,
        executed: tuple[ExecutedPublicQuery, ...],
    ) -> None:
        first = executed[0]
        if first.request.query_id != "O-Q01":
            raise GovernedExportError("O-Q01 was not executed first")
        data = first.envelope.data.model_dump(mode="json")
        expected_scenarios = [
            {
                "canonical_family": item.canonical_family,
                "entry_point_count": sum(
                    entry.scenario_ref == item.scenario_ref
                    for entry in discovery.entry_points  # type: ignore[attr-defined]
                ),
                "public_role": item.public_role,
                "scenario_ref": item.scenario_ref,
                "status": "AVAILABLE",
            }
            for item in discovery.scenarios  # type: ignore[attr-defined]
        ]
        if data["scenario_summaries"] != expected_scenarios:
            raise GovernedExportError("P-Q00 and O-V01 scenario sets differ")

    def _write_package_content(
        self,
        root: Path,
        *,
        request: BuildGovernedExport,
        discovery: object,
        executed: tuple[ExecutedPublicQuery, ...],
        rows: dict[str, list[dict[str, object]]],
    ) -> GovernedExportManifest:
        schema_root = root / "schemas" / STORAGE_KEY
        data_root = root / "data" / STORAGE_KEY
        schema_root.mkdir(parents=True)
        data_root.mkdir(parents=True)
        manifest_entries: list[DatasetManifestEntry] = []
        for definition in DATASETS:
            schema_relative = f"schemas/{STORAGE_KEY}/{definition.dataset_id}.schema.json"
            data_relative = f"data/{STORAGE_KEY}/{definition.dataset_id}.csv"
            schema_bytes = canonical_json_bytes(definition.schema_document())
            data_bytes = canonical_csv_bytes(definition, rows[definition.dataset_id])
            (root / schema_relative).write_bytes(schema_bytes)
            (root / data_relative).write_bytes(data_bytes)
            sources = tuple(
                sorted(
                    {
                        source
                        for item in executed
                        if item.request.query_id in definition.source_query_ids
                        for source in item.envelope.source_refs
                    }
                )
            )
            manifest_entries.append(
                DatasetManifestEntry(
                    dataset_id=definition.dataset_id,
                    dataset_version=1,
                    registry_id=REGISTRY_ID,
                    export_steward=definition.export_steward,
                    semantic_owners=definition.semantic_owners,
                    relative_path=data_relative,
                    schema_path=schema_relative,
                    row_count=len(rows[definition.dataset_id]),
                    data_sha256=sha256_bytes(data_bytes),
                    schema_sha256=sha256_bytes(schema_bytes),
                    source_query_ids=definition.source_query_ids,
                    source_view_ids=definition.source_view_ids,
                    semantic_source_refs=sources,
                )
            )
        first = executed[0].envelope.data.model_dump(mode="json")
        manifest = GovernedExportManifest(
            contract_version=PACKAGE_CONTRACT,
            export_ref=request.export_ref,
            workspace_ref=request.workspace_ref,
            discovery_descriptor_ref=discovery.discovery_descriptor_ref,
            discovery_descriptor_hash=discovery.discovery_descriptor_hash,
            runtime_release=first["runtime_release"],
            query_revision=discovery.query_revision,
            semantic_as_of=discovery.semantic_as_of,
            exported_at=request.exported_at,
            compatibility_mode="EXACT_ORIGINAL",
            synthetic_data=True,
            synthetic_data_notice=first["synthetic_data_notice"],
            scenario_refs=tuple(sorted(item.scenario_ref for item in discovery.scenarios)),
            scenario_set_digest=discovery.scenario_set_digest,
            authoritative_inventory_digest=first["authoritative_inventory_digest"],
            projection_generation_ref=first["projection_generation_ref"],
            dataset_entries=tuple(manifest_entries),
            dataset_registries=(
                DatasetRegistryEntry(
                    registry_id=REGISTRY_ID,
                    registry_version=REGISTRY_VERSION,
                    storage_key=STORAGE_KEY,
                    dataset_ids=tuple(item.dataset_id for item in DATASETS),
                    registry_contract_hash=registry_contract_hash(),
                ),
            ),
            relationship_contract_version=1,
            producer_release=self._producer_release,
        )
        (root / "relationships.json").write_bytes(
            canonical_json_bytes(list(RELATIONSHIPS))
        )
        (root / "README.txt").write_bytes(_readme(manifest))
        (root / "manifest.json").write_bytes(
            canonical_json_bytes(manifest.model_dump(mode="json"))
        )
        included = sorted(
            (
                path
                for path in root.rglob("*")
                if path.is_file()
                and path.name not in {"checksums.json", "package.digest"}
            ),
            key=lambda path: path.relative_to(root).as_posix(),
        )
        ledger = ChecksumLedger(
            checksum_contract_version=1,
            files=tuple(
                ChecksumEntry(
                    relative_path=path.relative_to(root).as_posix(),
                    sha256=sha256_bytes(path.read_bytes()),
                )
                for path in included
            ),
        )
        ledger_bytes = canonical_json_bytes(ledger.model_dump(mode="json"))
        (root / "checksums.json").write_bytes(ledger_bytes)
        (root / "package.digest").write_text(
            f"{sha256_bytes(ledger_bytes)}\n",
            encoding="ascii",
            newline="\n",
        )
        return manifest


def _verification_result(
    status: VerificationStatus,
    package_path: Path,
    message: str,
    *,
    digest: str | None = None,
    files: int = 0,
    datasets: int = 0,
) -> VerificationResult:
    return VerificationResult(
        status=status,
        package_path=package_path,
        package_digest=digest,
        checked_file_count=files,
        checked_dataset_count=datasets,
        message=message,
    )


def verify_governed_export(package_path: Path) -> VerificationResult:
    """Verify one package offline without consulting platform state."""

    root = package_path.resolve()
    try:
        if not root.is_dir():
            raise _VerificationFailure("MISSING_FILE", "package directory is missing")
        digest_path = root / "package.digest"
        ledger_path = root / "checksums.json"
        if not digest_path.is_file() or not ledger_path.is_file():
            raise _VerificationFailure("MISSING_FILE", "package digest or ledger is missing")
        ledger_bytes = ledger_path.read_bytes()
        expected_digest = digest_path.read_text(encoding="ascii")
        if expected_digest != f"{sha256_bytes(ledger_bytes)}\n":
            raise _VerificationFailure(
                "PACKAGE_DIGEST_MISMATCH", "package digest does not bind the ledger"
            )
        try:
            ledger = ChecksumLedger.model_validate_json(ledger_bytes)
        except (ValueError, ValidationError) as error:
            raise _VerificationFailure("SCHEMA_INVALID", "checksum ledger is invalid") from error
        if canonical_json_bytes(ledger.model_dump(mode="json")) != ledger_bytes:
            raise _VerificationFailure("SCHEMA_INVALID", "checksum ledger is not canonical")
        ledger_paths = tuple(item.relative_path for item in ledger.files)
        if ledger_paths != tuple(sorted(set(ledger_paths))):
            raise _VerificationFailure("SCHEMA_INVALID", "checksum paths are not sorted unique")
        actual_paths = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        }
        declared_paths = {*ledger_paths, "checksums.json", "package.digest"}
        missing = declared_paths - actual_paths
        extra = actual_paths - declared_paths
        if missing:
            raise _VerificationFailure("MISSING_FILE", "a declared package file is missing")
        if extra:
            raise _VerificationFailure("UNREGISTERED_FILE", "an unregistered file is present")
        for entry in ledger.files:
            if sha256_bytes((root / entry.relative_path).read_bytes()) != entry.sha256:
                raise _VerificationFailure("HASH_MISMATCH", "a file hash does not match")
        manifest = _json_file(root / "manifest.json", GovernedExportManifest)
        if manifest.contract_version != PACKAGE_CONTRACT:
            raise _VerificationFailure("UNSUPPORTED_CONTRACT", "package contract is unsupported")
        if manifest.compatibility_mode != "EXACT_ORIGINAL":
            raise _VerificationFailure(
                "UNSUPPORTED_COMPATIBILITY_MODE", "compatibility mode is unsupported"
            )
        registry_ids = tuple(item.registry_id for item in manifest.dataset_registries)
        if registry_ids != tuple(sorted(set(registry_ids))):
            raise _VerificationFailure(
                "UNSUPPORTED_CONTRACT", "registry entries are not sorted unique"
            )
        definitions, relationships, registry_specs = _supported_registry_set(
            registry_ids
        )
        if manifest.relationship_contract_version != len(registry_ids):
            raise _VerificationFailure(
                "UNSUPPORTED_CONTRACT", "relationship version differs"
            )
        definitions_by_registry: dict[str, list[object]] = {
            registry_id: [] for registry_id in registry_specs
        }
        for definition in definitions:
            definition_registry = (
                REGISTRY_ID
                if str(definition.dataset_id).startswith("P-")
                else "Q-ANALYTICS"
            )
            definitions_by_registry[definition_registry].append(definition)
        for registry in manifest.dataset_registries:
            storage_key, version, contract_hash = registry_specs[registry.registry_id]
            expected_ids = tuple(
                item.dataset_id
                for item in definitions_by_registry[registry.registry_id]
            )
            if (
                registry.registry_version != version
                or registry.storage_key != storage_key
                or registry.dataset_ids != expected_ids
                or registry.registry_contract_hash != contract_hash
            ):
                raise _VerificationFailure(
                    "UNSUPPORTED_CONTRACT", "registry contract differs"
                )
        if len(manifest.dataset_entries) != len(definitions):
            raise _VerificationFailure("UNSUPPORTED_CONTRACT", "dataset inventory differs")
        relationships_bytes = (root / "relationships.json").read_bytes()
        if relationships_bytes != canonical_json_bytes(list(relationships)):
            raise _VerificationFailure(
                "SCHEMA_INVALID", "relationship registry is not canonical or closed"
            )
        parsed_rows: dict[
            tuple[str, str], tuple[dict[str, object], ...]
        ] = {}
        entries = {
            (item.registry_id, item.dataset_id): item
            for item in manifest.dataset_entries
        }
        if len(entries) != len(manifest.dataset_entries):
            raise _VerificationFailure(
                "UNSUPPORTED_CONTRACT", "dataset identities are not unique"
            )
        for definition in definitions:
            definition_registry = (
                REGISTRY_ID
                if str(definition.dataset_id).startswith("P-")
                else "Q-ANALYTICS"
            )
            storage_key = registry_specs[definition_registry][0]
            identity = (definition_registry, definition.dataset_id)
            if identity not in entries:
                raise _VerificationFailure(
                    "UNSUPPORTED_CONTRACT", "dataset identity is not registered"
                )
            entry = entries[identity]
            expected_data = f"data/{storage_key}/{definition.dataset_id}.csv"
            expected_schema = (
                f"schemas/{storage_key}/{definition.dataset_id}.schema.json"
            )
            if (
                entry.relative_path != expected_data
                or entry.schema_path != expected_schema
                or entry.registry_id != definition_registry
                or entry.dataset_version != 1
                or entry.export_steward != definition.export_steward
                or entry.semantic_owners != definition.semantic_owners
                or entry.source_query_ids != definition.source_query_ids
                or entry.source_view_ids != definition.source_view_ids
            ):
                raise _VerificationFailure("SCHEMA_INVALID", "dataset manifest entry differs")
            schema_bytes = (root / expected_schema).read_bytes()
            if schema_bytes != canonical_json_bytes(definition.schema_document()):
                raise _VerificationFailure("SCHEMA_INVALID", "dataset schema differs")
            data_bytes = (root / expected_data).read_bytes()
            if (
                sha256_bytes(schema_bytes) != entry.schema_sha256
                or sha256_bytes(data_bytes) != entry.data_sha256
            ):
                raise _VerificationFailure("HASH_MISMATCH", "dataset hash differs")
            try:
                rows = parse_canonical_csv(definition, data_bytes)
            except (TypeError, ValueError, UnicodeError) as error:
                raise _VerificationFailure("ROW_INVALID", "dataset row is invalid") from error
            if len(rows) != entry.row_count:
                raise _VerificationFailure("ROW_INVALID", "dataset row count differs")
            _validate_keys(definition.dataset_id, definition.unique_keys, rows)
            parsed_rows[identity] = rows
        flat_rows = {
            dataset_id: values
            for (_, dataset_id), values in parsed_rows.items()
        }
        _validate_snapshot(manifest, flat_rows)
        _validate_relationships(parsed_rows, relationships)
        return _verification_result(
            "VERIFIED",
            root,
            "package verified offline",
            digest=expected_digest.strip(),
            files=len(actual_paths),
            datasets=len(definitions),
        )
    except _VerificationFailure as error:
        return _verification_result(error.status, root, error.message)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return _verification_result("SCHEMA_INVALID", root, "package could not be parsed")


def _validate_keys(
    dataset_id: str,
    unique_keys: tuple[tuple[str, ...], ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    row_keys = tuple(str(row["row_key"]) for row in rows)
    if row_keys != tuple(sorted(row_keys)):
        raise _VerificationFailure("KEY_VIOLATION", f"{dataset_id} rows are not sorted")
    for key in unique_keys:
        values = tuple(tuple(row[column] for column in key) for row in rows)
        if len(values) != len(set(values)):
            raise _VerificationFailure("KEY_VIOLATION", f"{dataset_id} key is not unique")


def _validate_snapshot(
    manifest: GovernedExportManifest,
    rows: dict[str, tuple[dict[str, object], ...]],
) -> None:
    executions = rows["P-D18"]
    counts = Counter(str(row["query_id"]) for row in executions)
    expected = {
        "P-Q00": 1,
        "O-Q01": 1,
        "O-Q02": 1,
        "O-Q03": 2,
        "O-Q04": 1,
        "O-Q05": 2,
        "O-Q06": 2,
        "O-Q07": 2,
        "O-Q08": 1,
        "O-Q09": 1,
        "O-Q10": 1,
        "O-Q11": 1,
    }
    if len(executions) != 16 or counts != expected:
        raise _VerificationFailure("SNAPSHOT_MISMATCH", "query inventory differs")
    if any(
        row["query_revision"] != manifest.query_revision
        or row["semantic_as_of"] != str(manifest.semantic_as_of)
        or row["compatibility_mode"] != "EXACT_ORIGINAL"
        for row in executions
    ):
        raise _VerificationFailure("SNAPSHOT_MISMATCH", "query snapshot differs")
    p_instances = {
        row["query_instance_ref"]
        for row in executions
        if row["query_id"] == "P-Q00"
    }
    if any(row["query_instance_ref"] in p_instances for row in rows["P-D19"]):
        raise _VerificationFailure("SNAPSHOT_MISMATCH", "P-Q00 claims semantic sources")

    if "Q-D13" not in rows:
        return
    q_executions = rows["Q-D13"]
    q_counts = Counter(str(row["query_id"]) for row in q_executions)
    expected_q = {
        "Q-Q00": 1,
        "Q-Q01": 1,
        "Q-Q02": 3,
        "Q-Q03": 1,
        "Q-Q04": 1,
        "Q-Q05": 2,
        "Q-Q06": 1,
    }
    if len(q_executions) != 10 or q_counts != expected_q:
        raise _VerificationFailure(
            "SNAPSHOT_MISMATCH", "analytical query inventory differs"
        )
    if any(
        row["query_revision"] != manifest.query_revision
        or row["semantic_as_of"] != str(manifest.semantic_as_of)
        or row["compatibility_mode"] != "EXACT_ORIGINAL"
        for row in q_executions
    ):
        raise _VerificationFailure(
            "SNAPSHOT_MISMATCH", "analytical query snapshot differs"
        )
    q00_instances = {
        row["query_instance_ref"]
        for row in q_executions
        if row["query_id"] == "Q-Q00"
    }
    if any(row["query_instance_ref"] in q00_instances for row in rows["Q-D14"]):
        raise _VerificationFailure(
            "SNAPSHOT_MISMATCH", "Q-Q00 claims semantic sources"
        )
    canonical_counts = {
        "Q-D01": 4,
        "Q-D02": 4,
        "Q-D03": 4,
        "Q-D04": 3,
        "Q-D05": 6,
        "Q-D06": 3,
        "Q-D07": 1,
        "Q-D08": 1,
        "Q-D09": 2,
        "Q-D10": 2,
        "Q-D11": 1,
        "Q-D12": 14,
        "Q-D13": 10,
        "Q-D14": 38,
        "Q-D15": 1,
        "Q-D16": 1,
    }
    if any(len(rows[dataset_id]) != count for dataset_id, count in canonical_counts.items()):
        raise _VerificationFailure(
            "SNAPSHOT_MISMATCH", "analytical dataset inventory differs"
        )
    context = rows["Q-D16"][0]
    package = rows["P-D01"][0]
    shared = (
        ("query_revision", "query_revision"),
        ("semantic_as_of", "semantic_as_of"),
        ("compatibility_mode", "compatibility_mode"),
        ("scenario_set_digest", "scenario_set_digest"),
    )
    if any(context[q_name] != package[p_name] for q_name, p_name in shared):
        raise _VerificationFailure(
            "SNAPSHOT_MISMATCH", "P and Q package contexts differ"
        )
    _validate_analytical_semantics(rows)


def _validate_analytical_semantics(
    rows: dict[str, tuple[dict[str, object], ...]],
) -> None:
    accounts = {row["account_id"] for row in rows["Q-D01"]}
    statements = {row["statement_field"] for row in rows["Q-D02"]}
    mappings = rows["Q-D03"]
    if (
        {row["account_id"] for row in mappings} != accounts
        or {row["statement_field"] for row in mappings} != statements
        or any(row["mapping_role"] != "PRIMARY" for row in mappings)
    ):
        raise _VerificationFailure(
            "RELATIONSHIP_VIOLATION", "ledger semantics mapping is not closed"
        )
    mapping = {row["account_id"]: row["statement_field"] for row in mappings}
    lines_by_journal: dict[tuple[object, object], list[dict[str, object]]] = {}
    for line in rows["Q-D05"]:
        if mapping.get(line["account_id"]) != line["statement_field"]:
            raise _VerificationFailure(
                "RELATIONSHIP_VIOLATION", "journal account mapping differs"
            )
        key = (line["scenario_ref"], line["journal_id"])
        lines_by_journal.setdefault(key, []).append(line)
    nullable_origin_fields = (
        "source_business_event_ref",
        "source_posting_rule_ref",
        "source_projection_ref",
        "reverses_journal_id",
        "corrects_journal_id",
        "restatement_case_ref",
        "directive_ref",
        "restatement_policy_ref",
        "correction_policy_ref",
        "predecessor_proposal_ref",
        "predecessor_proposal_semantic_hash",
    )
    required_by_origin = {
        "RESTATEMENT_ADJUSTMENT": {
            "source_business_event_ref",
            "source_posting_rule_ref",
            "restatement_case_ref",
            "directive_ref",
            "restatement_policy_ref",
            "predecessor_proposal_ref",
            "predecessor_proposal_semantic_hash",
        },
        "REVERSAL": {
            "source_projection_ref",
            "reverses_journal_id",
            "directive_ref",
            "correction_policy_ref",
        },
        "REPLACEMENT": {
            "source_projection_ref",
            "corrects_journal_id",
            "directive_ref",
            "correction_policy_ref",
        },
    }
    lineage_by_origin = {
        "RESTATEMENT_ADJUSTMENT": "PREDECESSOR_ORIGIN",
        "REVERSAL": "DIRECT_ORIGIN",
        "REPLACEMENT": "DIRECT_ORIGIN",
    }
    for header in rows["Q-D04"]:
        key = (header["scenario_ref"], header["journal_id"])
        lines = lines_by_journal.get(key, [])
        debits = sum(int(line["debit_minor"]) for line in lines)
        credits = sum(int(line["credit_minor"]) for line in lines)
        if (
            len(lines) != 2
            or debits != header["total_debit_minor"]
            or credits != header["total_credit_minor"]
            or debits != credits
        ):
            raise _VerificationFailure(
                "RELATIONSHIP_VIOLATION", "authored journal does not reconcile"
            )
        origin = str(header["origin_type"])
        required = required_by_origin.get(origin)
        if required is None or header["source_lineage_mode"] != lineage_by_origin[origin]:
            raise _VerificationFailure(
                "ROW_INVALID", "journal origin discriminator is invalid"
            )
        if any(
            (header[field] is not None) != (field in required)
            for field in nullable_origin_fields
        ):
            raise _VerificationFailure(
                "ROW_INVALID", "journal origin union contains cross-variant leakage"
            )
    exact_sources = {str(row["source_ref"]) for row in rows["Q-D14"]}
    if any(
        row["source_family"] != str(row["source_ref"]).split(":", 1)[0]
        for row in rows["Q-D14"]
    ):
        raise _VerificationFailure(
            "ROW_INVALID", "analytical query source is not family qualified"
        )
    for item in rows["Q-D06"]:
        verified = item["verification_status"] == "CONTENT_BYTES_VERIFIED"
        proof = item["verification_proof_ref"]
        if verified != (proof is not None) or (verified and proof not in exact_sources):
            raise _VerificationFailure(
                "RELATIONSHIP_VIOLATION", "journal input verification is not exact"
            )
    for source in rows["Q-D08"]:
        source_lines = sorted(
            (
                line
                for line in rows["Q-D09"]
                if line["source_projection_ref"] == source["source_projection_ref"]
            ),
            key=lambda line: int(line["line_no"]),
        )
        for line in source_lines:
            if mapping.get(line["account_id"]) != line["statement_field"]:
                raise _VerificationFailure(
                    "RELATIONSHIP_VIOLATION",
                    "referenced-journal account mapping differs",
                )
        payload = {
            "projection_type": source["projection_type"],
            "projection_version": source["projection_version"],
            "authored_by_f": source["authored_by_f"],
            "source_hash": source["source_hash"],
            "journal_id": source["journal_id"],
            "ledger_period_id": source["ledger_period_id"],
            "currency": source["currency"],
            "line_tuples": [
                {
                    "line_no": line["line_no"],
                    "account_id": line["account_id"],
                    "debit_minor": line["debit_minor"],
                    "credit_minor": line["credit_minor"],
                    "currency": line["currency"],
                    "dimensions": {
                        "legal_entity_id": line["legal_entity_id"],
                        "customer_id": line["customer_id"],
                        "contract_id": line["contract_id"],
                    },
                }
                for line in source_lines
            ],
        }
        if (
            len(source_lines) != 2
            or
            source["authored_by_f"] is not False
            or source["source_hash"] != source["j_ar17_semantic_hash"]
            or source["source_hash"] != source["g13_source_record_semantic_hash"]
            or source["source_projection_ref"]
            != source["g13_upstream_authoritative_ref"]
            or canonical_sha256(payload) != source["g13_payload_hash"]
        ):
            raise _VerificationFailure(
                "RELATIONSHIP_VIOLATION", "referenced journal binding differs"
            )
    for period in rows["Q-D10"]:
        if period["state_basis_type"] == "BASE_FACT":
            valid = period["status"] == "OPEN" and period["state_token"] is None
        else:
            valid = (
                period["state_basis_type"] == "TRANSITION_PUBLICATION"
                and period["status"] == "HARD_CLOSED"
                and period["state_token"] is not None
                and period["transition_event_ref"] is not None
            )
        if not valid:
            raise _VerificationFailure(
                "ROW_INVALID", "accounting period basis is inconsistent"
            )


def _validate_relationships(
    rows: dict[tuple[str, str], tuple[dict[str, object], ...]],
    relationships: tuple[dict[str, object], ...],
) -> None:
    for relationship in relationships:
        from_coordinate = (
            str(relationship["from_registry"]),
            str(relationship["from_dataset"]),
        )
        if relationship["relationship_type"] == "POLYMORPHIC_PARENT":
            allowed = {
                (str(item["registry_id"]), str(item["dataset_id"])): tuple(
                    item["target_key_columns"]
                )
                for item in relationship["allowed_targets"]  # type: ignore[union-attr]
            }
            for row in rows[from_coordinate]:
                selected_dataset = str(
                    row[str(relationship["dataset_selector_column"])]
                )
                target_coordinates = tuple(
                    coordinate
                    for coordinate in allowed
                    if coordinate[1] == selected_dataset
                )
                if len(target_coordinates) != 1:
                    raise _VerificationFailure(
                        "RELATIONSHIP_VIOLATION", "polymorphic target is not registered"
                    )
                target_coordinate = target_coordinates[0]
                target_counts = Counter(
                    tuple(target[column] for column in allowed[target_coordinate])
                    for target in rows[target_coordinate]
                )
                if target_counts[(row[str(relationship["key_column"])],)] != 1:
                    raise _VerificationFailure(
                        "RELATIONSHIP_VIOLATION", "polymorphic parent is missing"
                    )
            continue
        condition = relationship.get("condition")
        source_rows = rows[from_coordinate]
        if isinstance(condition, dict):
            source_rows = tuple(
                row
                for row in source_rows
                if row[str(condition["column"])] == condition["equals"]
            )
        from_columns = tuple(str(item) for item in relationship["from_columns"])
        to_columns = tuple(str(item) for item in relationship["to_columns"])
        to_coordinate = (
            str(relationship["to_registry"]),
            str(relationship["to_dataset"]),
        )
        targets = Counter(
            tuple(row[column] for column in to_columns)
            for row in rows[to_coordinate]
        )
        for row in source_rows:
            if targets[tuple(row[column] for column in from_columns)] != 1:
                raise _VerificationFailure(
                    "RELATIONSHIP_VIOLATION",
                    f"relationship {relationship['relationship_id']} is broken",
                )
    role_parent = {
        "RECONCILIATION_SOURCE": "P-D04",
        "EXCEPTION_SUBJECT": "P-D08",
        "EXCEPTION_EVIDENCE": "P-D08",
        "GOVERNANCE_CORRECTION": "P-D09",
        "GOVERNANCE_PRIOR_ISSUE": "P-D09",
        "GOVERNANCE_READINESS": "P-D09",
        "READINESS_BASIS": "P-D10",
    }
    if any(
        role_parent[str(row["reference_role"])] != row["parent_dataset_id"]
        for row in rows[(REGISTRY_ID, "P-D15")]
    ):
        raise _VerificationFailure(
            "RELATIONSHIP_VIOLATION", "reference role has an invalid parent"
        )
