from __future__ import annotations

import json
import shutil
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from finance_assurance.analytics.contracts import BuildGovernedAnalyticalExport
from finance_assurance.analytics.discovery import build_analytical_discovery
from finance_assurance.analytics.service import GovernedAnalyticalExportService
from finance_assurance.digestion import service as digestion_service
from finance_assurance.digestion.contracts import (
    BuildConsumerModel,
    ModelManifest,
    NoncanonicalCacheManifest,
    ReproduceConsumerModel,
    SemanticCatalogue,
    VerifyConsumerModel,
    VerifyConsumerModelResult,
)
from finance_assurance.digestion.registry import PROFILE_DATASET_IDS
from finance_assurance.digestion.service import (
    ConsumerModelError,
    ConsumerModelService,
    verify_consumer_model,
)
from finance_assurance.digestion.writer import PARQUET_WRITER_PROFILE
from finance_assurance.exports.contracts import ChecksumEntry, ChecksumLedger
from finance_assurance.exports.discovery import ExportSubjectSet, build_export_discovery
from finance_assurance.exports.serialization import (
    canonical_json_bytes,
    sha256_bytes,
)
from finance_assurance.product.demo_runtime import materialize_demo
from finance_assurance.product.demo_scenarios import default_demo_scenarios
from finance_assurance.runtime.persistence.sqlite import SqlitePersistenceBoundary


def _subjects() -> ExportSubjectSet:
    return ExportSubjectSet(
        c001_reconciliation_ref="RECON-C001@v1",
        c001_reporting_predecessor_ref="RV-2026-06@v1",
        c001_reporting_successor_ref="RV-2026-06@v2",
        c001_exception_ref="EXC-C001@v1",
        c001_issue_ref="ISSUE-C001@v1",
        c001_readiness_ref="READY-C001@v1",
        c001_readiness_purpose_ref="HIRING-FORECAST",
        c001_readiness_scope_ref="NEXUS-GROUP",
        c001_decision_ref="DECISION-C001@v1",
        c001_statement_field="subscription_revenue_minor",
        ct1_reconciliation_ref="RECON-CT1@v1",
        ct1_exception_ref="EXC-CT1@v1",
        ct1_issue_ref="ISSUE-CT1@v1",
        ct1_verification_ref="VERIFY-CT1@v1",
    )


def _reseal_model(model: Path) -> str:
    manifest = ModelManifest.model_validate_json(
        (model / "model-manifest.json").read_bytes()
    )
    ledger = ChecksumLedger(
        checksum_contract_version=1,
        files=tuple(
            ChecksumEntry(
                relative_path=relative,
                sha256=sha256_bytes((model / relative).read_bytes()),
            )
            for relative in manifest.canonical_digest_scope
        ),
    )
    ledger_bytes = canonical_json_bytes(ledger.model_dump(mode="json"))
    (model / "checksums.json").write_bytes(ledger_bytes)
    digest = sha256_bytes(ledger_bytes)
    (model / "model.digest").write_text(digest + "\n", encoding="ascii")
    return digest


def _reseal_cache(model: Path) -> None:
    path = model / "noncanonical-cache.json"
    payload = json.loads(path.read_bytes())
    database_path = model / payload["database_path"]
    database_bytes = database_path.read_bytes()
    payload["database_sha256"] = sha256_bytes(database_bytes)
    payload["database_byte_count"] = len(database_bytes)
    path.write_bytes(canonical_json_bytes(payload))


def _verify(
    model: Path, source_package: tuple[Path, str], model_digest: str
) -> VerifyConsumerModelResult:
    package, source_digest = source_package
    return verify_consumer_model(
        VerifyConsumerModel(
            request_contract_version="verify-consumer-model-request@v1",
            model_path=model,
            source_package_path=package,
            expected_model_digest=model_digest,
            expected_source_package_digest=source_digest,
            verification_scope="FULL_SOURCE_EQUIVALENCE",
        )
    )


@pytest.fixture(scope="module")
def source_package(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, str]:
    root = tmp_path_factory.mktemp("r2-source-package")
    scenarios = default_demo_scenarios()
    database = root / "demo.sqlite3"
    materialize_demo(database, scenarios)
    boundary = SqlitePersistenceBoundary(database)
    try:
        p_descriptor = build_export_discovery(
            scenarios,
            workspace_ref="R2-TEST",
            subjects=_subjects(),
        )
        q_descriptor = build_analytical_discovery(scenarios, p_descriptor)
        service = GovernedAnalyticalExportService(
            boundary,
            scenarios=scenarios,
            p_descriptor=p_descriptor,
            q_descriptor=q_descriptor,
        )
        package = root / "R2-PQ-SOURCE"
        result = service.build(
            BuildGovernedAnalyticalExport(
                request_contract_version="governed-analytical-export-request@v1",
                export_ref="R2-PQ-SOURCE",
                workspace_ref="R2-TEST",
                semantic_as_of=scenarios.semantic_as_of_time,
                exported_at="2026-08-13T12:00:00Z",
                output_path=package,
                p_discovery_descriptor_ref=p_descriptor.discovery_descriptor_ref,
                q_discovery_descriptor_ref=q_descriptor.discovery_descriptor_ref,
            )
        )
        yield package, result.package_digest
    finally:
        boundary.close()


def _request(
    package: Path,
    digest: str,
    output: Path,
    *,
    profile: str = "LINEAGE",
    formats: tuple[str, ...] = ("CSV", "PARQUET"),
) -> BuildConsumerModel:
    return BuildConsumerModel(
        request_contract_version="build-consumer-model-request@v1",
        model_ref=f"R2-{profile}",
        source_package_path=package,
        expected_source_package_digest=digest,
        profile_id=profile,
        profile_version=1,
        formats=formats,
        parquet_writer_profile_ref=(
            "PYARROW-25@v1" if "PARQUET" in formats else None
        ),
        parquet_writer_profile_hash=(
            PARQUET_WRITER_PROFILE.profile_hash if "PARQUET" in formats else None
        ),
        duckdb_storage_compatibility_version=(
            "v1.5.0" if "DUCKDB" in formats else None
        ),
        output_path=output,
        producer_release="finance-assurance-r2-test@v1",
        built_at="2026-08-13T15:00:00Z",
    )


@pytest.mark.parametrize(
    ("profile", "formats", "expected_tables"),
    [
        ("CORE", ("PARQUET",), 26),
        ("LINEAGE", ("CSV", "PARQUET"), 31),
        ("DIAGNOSTIC", ("PARQUET",), 37),
    ],
)
def test_r2_builds_and_verifies_every_closed_profile(
    source_package: tuple[Path, str],
    tmp_path: Path,
    profile: str,
    formats: tuple[str, ...],
    expected_tables: int,
) -> None:
    package, digest = source_package
    output = tmp_path / profile.lower()
    result = ConsumerModelService().build(
        _request(package, digest, output, profile=profile, formats=formats)
    )

    assert result.table_count == expected_tables
    assert result.model_path == output.resolve()
    manifest = ModelManifest.model_validate_json(
        (output / "model-manifest.json").read_bytes()
    )
    catalogue = SemanticCatalogue.model_validate_json(
        (output / "semantic-model.json").read_bytes()
    )
    assert len(manifest.table_entries) == expected_tables
    assert len(catalogue.tables) == expected_tables
    assert {
        item.source_coordinate.dataset_id for item in catalogue.tables
    } == PROFILE_DATASET_IDS[profile]
    assert len({item.physical_alias for item in catalogue.tables}) == expected_tables
    assert all(item.physical_alias.startswith("r_") for item in catalogue.tables)
    assert manifest.source_package_digest == digest
    assert manifest.source_query_revision == 42
    assert manifest.source_compatibility_mode == "EXACT_ORIGINAL"
    verification = verify_consumer_model(
        VerifyConsumerModel(
            request_contract_version="verify-consumer-model-request@v1",
            model_path=output,
            source_package_path=package,
            expected_model_digest=result.model_digest,
            expected_source_package_digest=digest,
            verification_scope="FULL_SOURCE_EQUIVALENCE",
        )
    )
    assert verification.status == "VERIFIED", verification.message
    assert verification.checked_table_count == expected_tables
    assert verification.checked_column_count == len(catalogue.columns)


def test_r2_reproduces_every_canonical_file_byte_for_byte(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, digest = source_package
    original = tmp_path / "original"
    reproduced = tmp_path / "reproduced"
    service = ConsumerModelService()
    built = service.build(_request(package, digest, original))
    relocated_source = tmp_path / "same-bytes-different-directory"
    shutil.copytree(package, relocated_source)

    result = service.reproduce(
        ReproduceConsumerModel(
            request_contract_version="reproduce-consumer-model-request@v1",
            source_model_path=original,
            source_package_path=package,
            reproduction_output_path=reproduced,
            expected_model_digest=built.model_digest,
            expected_source_package_digest=digest,
        )
    )

    assert result.status == "REPRODUCED", result.message
    original_files = {
        path.relative_to(original).as_posix(): path.read_bytes()
        for path in original.rglob("*")
        if path.is_file()
    }
    reproduced_files = {
        path.relative_to(reproduced).as_posix(): path.read_bytes()
        for path in reproduced.rglob("*")
        if path.is_file()
    }
    assert reproduced_files == original_files


def test_r2_full_equivalence_rejects_resealed_parquet_domain_tampering(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, digest = source_package
    output = tmp_path / "parquet-tamper"
    ConsumerModelService().build(_request(package, digest, output))
    manifest_path = output / "model-manifest.json"
    payload = json.loads(manifest_path.read_bytes())
    entry = next(
        item
        for item in payload["table_entries"]
        if item["source_dataset_id"] == "P-D06"
    )
    parquet_path = output / entry["parquet_path"]
    table = pq.read_table(parquet_path)
    amounts = table["amount_minor"].to_pylist()
    amounts[0] += 1
    column_index = table.column_names.index("amount_minor")
    tampered = table.set_column(
        column_index, "amount_minor", pa.array(amounts, type=pa.int64())
    )
    pq.write_table(tampered, parquet_path)
    entry["parquet_hash"] = sha256_bytes(parquet_path.read_bytes())
    manifest_path.write_bytes(canonical_json_bytes(payload))
    resealed_digest = _reseal_model(output)

    result = verify_consumer_model(
        VerifyConsumerModel(
            request_contract_version="verify-consumer-model-request@v1",
            model_path=output,
            source_package_path=package,
            expected_model_digest=resealed_digest,
            expected_source_package_digest=digest,
            verification_scope="FULL_SOURCE_EQUIVALENCE",
        )
    )

    assert result.status == "FAILED"
    assert "Parquet logical table differs" in result.message


def test_r2_parquet_retains_source_order_types_and_hidden_keys(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, digest = source_package
    output = tmp_path / "parquet-contract"
    ConsumerModelService().build(_request(package, digest, output))
    manifest = ModelManifest.model_validate_json(
        (output / "model-manifest.json").read_bytes()
    )
    entry = next(
        item for item in manifest.table_entries if item.source_dataset_id == "P-D06"
    )
    table = pq.read_table(output / str(entry.parquet_path))

    assert entry.relationship_key_projections == ("P-RL02",)
    assert table.column_names[-1] == "_r_hk_p_rl02"
    assert table.column_names[0] == "row_key"
    assert str(table.schema.field("amount_minor").type) == "int64"
    assert table.schema.field("_r_hk_p_rl02").nullable is False
    assert table["row_key"].to_pylist() == sorted(table["row_key"].to_pylist())


def test_r2_verifier_rejects_tampering_and_unknown_files(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, digest = source_package
    output = tmp_path / "tamper"
    built = ConsumerModelService().build(_request(package, digest, output))
    (output / "unknown.txt").write_text("not registered", encoding="ascii")

    result = verify_consumer_model(
        VerifyConsumerModel(
            request_contract_version="verify-consumer-model-request@v1",
            model_path=output,
            source_package_path=package,
            expected_model_digest=built.model_digest,
            expected_source_package_digest=digest,
            verification_scope="FULL_SOURCE_EQUIVALENCE",
        )
    )

    assert result.status == "FAILED"
    assert "inventory" in result.message


def test_r2_requires_verified_exact_source_before_parse_or_publication(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, digest = source_package
    damaged = tmp_path / "damaged-source"
    shutil.copytree(package, damaged)
    data_file = next((damaged / "data").rglob("*.csv"))
    data_file.write_bytes(data_file.read_bytes() + b"\n")
    output = tmp_path / "must-not-publish"

    with pytest.raises(ConsumerModelError, match="P-C02"):
        ConsumerModelService().build(_request(damaged, digest, output))

    assert not output.exists()
    assert not tuple(tmp_path.glob(".must-not-publish.staging-*"))


def test_r2_cannot_stage_or_publish_inside_the_governed_source(
    source_package: tuple[Path, str],
) -> None:
    package, digest = source_package
    output = package / "consumer-model"

    with pytest.raises(ConsumerModelError, match="inside the source package"):
        ConsumerModelService().build(_request(package, digest, output))

    assert not output.exists()
    assert not tuple(package.glob(".consumer-model.staging-*"))


def test_r2_writer_failure_is_atomic(
    source_package: tuple[Path, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package, digest = source_package
    output = tmp_path / "writer-failure"

    def fail_write(*args: object, **kwargs: object) -> None:
        raise OSError("injected writer failure")

    monkeypatch.setattr("finance_assurance.digestion.service.pq.write_table", fail_write)
    with pytest.raises(OSError, match="injected"):
        ConsumerModelService().build(_request(package, digest, output))

    assert not output.exists()
    assert not tuple(tmp_path.glob(".writer-failure.staging-*"))


def test_r2_staged_verification_failure_is_atomic(
    source_package: tuple[Path, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package, digest = source_package
    output = tmp_path / "verification-failure"
    failed = VerifyConsumerModelResult(
        result_contract_version="verify-consumer-model-result@v1",
        status="FAILED",
        checked_file_count=0,
        checked_table_count=0,
        checked_column_count=0,
        checked_relationship_count=0,
        message="injected staged verification failure",
    )
    monkeypatch.setattr(
        "finance_assurance.digestion.service.verify_consumer_model",
        lambda _: failed,
    )

    with pytest.raises(ConsumerModelError, match="staged consumer model failed"):
        ConsumerModelService().build(_request(package, digest, output))

    assert not output.exists()
    assert not tuple(tmp_path.glob(".verification-failure.staging-*"))


def test_r2_atomic_publication_retries_transient_windows_handle_lag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staging = tmp_path / ".model.staging-test"
    final = tmp_path / "model"
    staging.mkdir()
    (staging / "proof.txt").write_text("closed", encoding="ascii")
    original = Path.replace
    attempts = 0

    def transient_replace(source: Path, target: Path) -> Path:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise PermissionError("transient handle lag")
        return original(source, target)

    monkeypatch.setattr(Path, "replace", transient_replace)
    monkeypatch.setattr(digestion_service.time, "sleep", lambda _: None)

    digestion_service._atomic_publish(staging, final)

    assert attempts == 3
    assert not staging.exists()
    assert (final / "proof.txt").read_text(encoding="ascii") == "closed"


def test_r3_builds_verified_read_only_duckdb_cache(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, digest = source_package
    output = tmp_path / "duckdb"
    result = ConsumerModelService().build(
        _request(
            package,
            digest,
            output,
            formats=("CSV", "PARQUET", "DUCKDB"),
        )
    )
    manifest = ModelManifest.model_validate_json(
        (output / "model-manifest.json").read_bytes()
    )
    cache = NoncanonicalCacheManifest.model_validate_json(
        (output / "noncanonical-cache.json").read_bytes()
    )

    assert result.table_count == 31
    assert result.source_row_count == 189
    assert result.canonical_file_count == 99
    assert result.noncanonical_cache_file_count == 2
    assert manifest.noncanonical_cache_manifest_path == "noncanonical-cache.json"
    assert len(cache.table_entries) == 31
    assert cache.engine_version == "1.5.5"
    assert cache.storage_compatibility_version == "v1.5.0"
    assert cache.database_storage_version == "v1.5.0+"
    assert all(
        item.duckdb_schema and item.duckdb_object for item in manifest.table_entries
    )
    connection = duckdb.connect(str(output / cache.database_path), read_only=True)
    try:
        schemas = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT schema_name FROM duckdb_tables() "
                "WHERE internal = false"
            ).fetchall()
        }
        assert schemas == {"p_evidence_v1", "q_analytics_v1", "model_meta"}
        with pytest.raises(duckdb.Error):
            connection.execute("CREATE TABLE model_meta.forbidden (id INTEGER)")
    finally:
        connection.close()
    verification = _verify(output, source_package, result.model_digest)
    assert verification.status == "VERIFIED"
    assert verification.checked_file_count == 101


def test_r3_rejects_resealed_duckdb_domain_divergence(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, digest = source_package
    output = tmp_path / "duckdb-domain-tamper"
    built = ConsumerModelService().build(
        _request(package, digest, output, formats=("PARQUET", "DUCKDB"))
    )
    manifest = ModelManifest.model_validate_json(
        (output / "model-manifest.json").read_bytes()
    )
    journal_line = next(
        item for item in manifest.table_entries if item.source_dataset_id == "P-D06"
    )
    qualified = f'"{journal_line.duckdb_schema}"."{journal_line.duckdb_object}"'
    connection = duckdb.connect(
        str(output / "warehouse" / "finance-assurance.duckdb")
    )
    try:
        connection.execute(
            f"UPDATE {qualified} SET amount_minor = amount_minor + 1 "
            f"WHERE row_key = (SELECT min(row_key) FROM {qualified})"
        )
        connection.execute("CHECKPOINT")
    finally:
        connection.close()
    _reseal_cache(output)

    result = _verify(output, source_package, built.model_digest)

    assert result.status == "FAILED"
    assert "logical table differs" in result.message


def test_r3_rejects_resealed_unknown_duckdb_object(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, digest = source_package
    output = tmp_path / "duckdb-object-tamper"
    built = ConsumerModelService().build(
        _request(package, digest, output, formats=("PARQUET", "DUCKDB"))
    )
    connection = duckdb.connect(
        str(output / "warehouse" / "finance-assurance.duckdb")
    )
    try:
        connection.execute("CREATE TABLE model_meta.unknown_object (id INTEGER)")
        connection.execute("CHECKPOINT")
    finally:
        connection.close()
    _reseal_cache(output)

    result = _verify(output, source_package, built.model_digest)

    assert result.status == "FAILED"
    assert "object inventory differs" in result.message


def test_r3_rejects_cache_file_and_manifest_tampering(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, digest = source_package
    output = tmp_path / "duckdb-cache-tamper"
    built = ConsumerModelService().build(
        _request(package, digest, output, formats=("PARQUET", "DUCKDB"))
    )
    cache_path = output / "noncanonical-cache.json"
    payload = json.loads(cache_path.read_bytes())
    database_path = output / payload["database_path"]
    original_database = database_path.read_bytes()
    database_path.write_bytes(original_database + b"tamper")

    file_result = _verify(output, source_package, built.model_digest)

    assert file_result.status == "FAILED"
    assert "cache file binding differs" in file_result.message
    database_path.write_bytes(original_database)
    payload["unregistered_field"] = "forbidden"
    cache_path.write_bytes(canonical_json_bytes(payload))

    manifest_result = _verify(output, source_package, built.model_digest)

    assert manifest_result.status == "FAILED"
    assert "Extra inputs are not permitted" in manifest_result.message


def test_r3_duckdb_writer_failure_is_atomic(
    source_package: tuple[Path, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package, digest = source_package
    output = tmp_path / "duckdb-writer-failure"

    def fail_connect(*args: object, **kwargs: object) -> None:
        raise duckdb.IOException("injected DuckDB writer failure")

    monkeypatch.setattr(
        "finance_assurance.digestion.duckdb_cache.duckdb.connect", fail_connect
    )
    with pytest.raises(duckdb.IOException, match="injected"):
        ConsumerModelService().build(
            _request(package, digest, output, formats=("PARQUET", "DUCKDB"))
        )

    assert not output.exists()
    assert not tuple(tmp_path.glob(".duckdb-writer-failure.staging-*"))


def test_r3_reproduces_canonical_bytes_and_revalidates_cache(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, digest = source_package
    original = tmp_path / "duckdb-original"
    reproduced = tmp_path / "duckdb-reproduced"
    service = ConsumerModelService()
    built = service.build(
        _request(
            package,
            digest,
            original,
            formats=("CSV", "PARQUET", "DUCKDB"),
        )
    )

    result = service.reproduce(
        ReproduceConsumerModel(
            request_contract_version="reproduce-consumer-model-request@v1",
            source_model_path=original,
            source_package_path=package,
            reproduction_output_path=reproduced,
            expected_model_digest=built.model_digest,
            expected_source_package_digest=digest,
        )
    )

    assert result.status == "REPRODUCED", result.message
    manifest = ModelManifest.model_validate_json(
        (original / "model-manifest.json").read_bytes()
    )
    for relative in (
        *manifest.canonical_digest_scope,
        "checksums.json",
        "model.digest",
    ):
        assert (original / relative).read_bytes() == (
            reproduced / relative
        ).read_bytes()
    assert _verify(reproduced, source_package, built.model_digest).status == "VERIFIED"


def test_r2_catalogue_is_canonical_and_separates_metadata_from_domain_rows(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, digest = source_package
    output = tmp_path / "catalogue"
    ConsumerModelService().build(_request(package, digest, output))
    catalogue_bytes = (output / "semantic-model.json").read_bytes()
    catalogue = SemanticCatalogue.model_validate_json(catalogue_bytes)

    assert catalogue_bytes == canonical_json_bytes(catalogue.model_dump(mode="json"))
    assert len(catalogue.measures) == 12
    assert all(item.default_summarization == "NONE" for item in catalogue.columns)
    forbidden = {"worksheet", "power_bi", "react_route", "refresh"}
    for entry in ModelManifest.model_validate_json(
        (output / "model-manifest.json").read_bytes()
    ).table_entries:
        table = pq.read_table(output / str(entry.parquet_path))
        assert not forbidden.intersection(table.column_names)
