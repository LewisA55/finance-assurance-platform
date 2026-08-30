from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from finance_assurance.exports.contracts import (
    BuildGovernedExport,
    ChecksumEntry,
    ChecksumLedger,
)
from finance_assurance.exports.discovery import (
    ExportSubjectSet,
    build_export_discovery,
    compile_export_discovery,
)
from finance_assurance.exports.registry import (
    DATASET_BY_ID,
    DATASETS,
    RELATIONSHIPS,
)
from finance_assurance.exports.serialization import (
    canonical_csv_bytes,
    canonical_json_bytes,
    parse_canonical_csv,
    sha256_bytes,
)
from finance_assurance.exports.service import (
    GovernedExportError,
    GovernedExportService,
    verify_governed_export,
)
from finance_assurance.product.demo_runtime import materialize_demo
from finance_assurance.product.demo_scenarios import default_demo_scenarios
from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.persistence.sqlite import SqlitePersistenceBoundary


class _CountingBoundary:
    def __init__(self, boundary: SqlitePersistenceBoundary) -> None:
        self.boundary = boundary
        self.query_count = 0

    def open_query(self, context: object) -> object:
        self.query_count += 1
        return self.boundary.open_query(context)  # type: ignore[arg-type]


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


@pytest.fixture(scope="module")
def governed_package(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, GovernedExportService, _CountingBoundary]:
    root = tmp_path_factory.mktemp("governed-export")
    scenarios = default_demo_scenarios()
    database = root / "demo.sqlite3"
    materialize_demo(database, scenarios)
    boundary = SqlitePersistenceBoundary(database)
    counted = _CountingBoundary(boundary)
    descriptor = build_export_discovery(
        scenarios,
        workspace_ref="TEST-DEMO",
        subjects=_subjects(),
    )
    service = GovernedExportService(  # type: ignore[arg-type]
        counted,
        scenarios=scenarios,
        descriptor=descriptor,
    )
    package = root / "P-EVIDENCE-DEMO"
    result = service.build(
        BuildGovernedExport(
            export_ref="P-EVIDENCE-DEMO",
            workspace_ref="TEST-DEMO",
            semantic_as_of=scenarios.semantic_as_of_time,
            exported_at="2026-08-13T12:00:00Z",
            output_path=package,
            discovery_descriptor_ref=descriptor.discovery_descriptor_ref,
            contract_version="governed-export-package@v1",
        )
    )
    assert result.package_path == package
    yield package, service, counted
    boundary.close()


def _reseal(package: Path) -> None:
    files = sorted(
        (
            path
            for path in package.rglob("*")
            if path.is_file()
            and path.name not in {"checksums.json", "package.digest"}
        ),
        key=lambda path: path.relative_to(package).as_posix(),
    )
    ledger = ChecksumLedger(
        checksum_contract_version=1,
        files=tuple(
            ChecksumEntry(
                relative_path=path.relative_to(package).as_posix(),
                sha256=sha256_bytes(path.read_bytes()),
            )
            for path in files
        ),
    )
    ledger_bytes = canonical_json_bytes(ledger.model_dump(mode="json"))
    (package / "checksums.json").write_bytes(ledger_bytes)
    (package / "package.digest").write_text(
        f"{sha256_bytes(ledger_bytes)}\n",
        encoding="ascii",
        newline="\n",
    )


def _rows(package: Path, dataset_id: str) -> tuple[dict[str, object], ...]:
    definition = DATASET_BY_ID[dataset_id]
    return parse_canonical_csv(
        definition,
        (package / "data" / "p-evidence-v1" / f"{dataset_id}.csv").read_bytes(),
    )


def test_p_q00_is_closed_finite_and_hash_bound() -> None:
    scenarios = default_demo_scenarios()
    descriptor = build_export_discovery(
        scenarios,
        workspace_ref="TEST-DEMO",
        subjects=_subjects(),
    )
    view = compile_export_discovery(
        descriptor,
        query_revision=7,
        scenario_set_digest=canonical_sha256(scenarios.model_dump(mode="json")),
    )

    assert len(view.query_requests) == 15
    assert view.query_requests[0].request.query_id == "O-Q01"
    assert view.discovery_descriptor_hash == descriptor.descriptor_hash
    assert [item.canonical_family for item in view.scenarios] == ["C-001", "CT-1"]
    assert len(view.entry_points) == 4

    payload = descriptor.model_dump(mode="json")
    payload["unknown"] = True
    with pytest.raises(ValidationError, match="extra_forbidden"):
        type(descriptor).model_validate(payload)


def test_package_is_closed_verified_and_uses_one_query_session(
    governed_package: tuple[Path, GovernedExportService, _CountingBoundary],
) -> None:
    package, _, counted = governed_package
    verification = verify_governed_export(package)
    manifest = json.loads((package / "manifest.json").read_bytes())

    assert verification.status == "VERIFIED"
    assert counted.query_count == 1
    assert verification.checked_dataset_count == 21
    assert len(manifest["dataset_entries"]) == 21
    assert manifest["dataset_registries"][0]["dataset_ids"] == [
        item.dataset_id for item in DATASETS
    ]
    assert manifest["compatibility_mode"] == "EXACT_ORIGINAL"
    assert manifest["synthetic_data"] is True


def test_build_and_verify_do_not_mutate_platform_state(
    governed_package: tuple[Path, GovernedExportService, _CountingBoundary],
    tmp_path: Path,
) -> None:
    _, service, counted = governed_package
    before_revision = counted.boundary.revision
    before_digest = counted.boundary.state.full_digest
    scenarios = default_demo_scenarios()
    descriptor = build_export_discovery(
        scenarios,
        workspace_ref="TEST-DEMO",
        subjects=_subjects(),
    )

    output = tmp_path / "non-mutating-export"
    service.build(
        BuildGovernedExport(
            export_ref="P-EVIDENCE-NON-MUTATING",
            workspace_ref="TEST-DEMO",
            semantic_as_of=scenarios.semantic_as_of_time,
            exported_at="2026-08-13T12:00:00Z",
            output_path=output,
            discovery_descriptor_ref=descriptor.discovery_descriptor_ref,
            contract_version="governed-export-package@v1",
        )
    )
    assert verify_governed_export(output).status == "VERIFIED"
    assert counted.boundary.revision == before_revision
    assert counted.boundary.state.full_digest == before_digest


def test_export_preserves_reporting_readiness_decision_and_correction_semantics(
    governed_package: tuple[Path, GovernedExportService, _CountingBoundary],
) -> None:
    package, _, _ = governed_package
    versions = _rows(package, "P-D05")
    values = _rows(package, "P-D06")
    bridges = _rows(package, "P-D07")
    readiness = _rows(package, "P-D10")
    decisions = _rows(package, "P-D11")
    corrections = _rows(package, "P-D13")
    journals = _rows(package, "P-D14")

    assert sorted(
        (row["version"], row["publication_origin"]) for row in versions
    ) == [
        (1, "PRE_SCOPE_IMPORT"),
        (2, "RESTATEMENT_PUBLICATION"),
    ]
    revenue = {
        (row["reporting_version_ref"], row["statement_field"]): row
        for row in values
    }
    assert revenue[("RV-2026-06@v2", "subscription_revenue_minor")][
        "amount_minor"
    ] == 1_000_000
    assert bridges[0]["adjustment_minor"] == 1_000_000
    assert readiness[0]["status"] == "APPROVED"
    assert decisions[0]["readiness_ref"] == readiness[0]["readiness_ref"]
    assert corrections[0]["reversal_binding_status"] == "BOUND_BEFORE_COMPARE"
    assert corrections[0]["control_account_net_movement_minor"] == 0
    assert {row["journal_role"] for row in journals} == {"REVERSAL", "REPLACEMENT"}
    assert all(row["balanced"] is True for row in journals)


def test_trace_and_query_provenance_remain_directed_and_invocation_local(
    governed_package: tuple[Path, GovernedExportService, _CountingBoundary],
) -> None:
    package, _, _ = governed_package
    nodes = _rows(package, "P-D16")
    edges = _rows(package, "P-D17")
    executions = _rows(package, "P-D18")
    sources = _rows(package, "P-D19")

    node_refs = {row["node_ref"] for row in nodes}
    assert all(row["source_ref"] in node_refs for row in edges)
    assert all(row["target_ref"] in node_refs for row in edges)
    assert len(executions) == 16
    p_q00 = next(row for row in executions if row["query_id"] == "P-Q00")
    assert not any(
        row["query_instance_ref"] == p_q00["query_instance_ref"] for row in sources
    )
    assert len({row["query_instance_ref"] for row in executions}) == 16


def test_schema_registry_closes_provenance_ownership_and_relationships(
    governed_package: tuple[Path, GovernedExportService, _CountingBoundary],
) -> None:
    package, _, _ = governed_package
    for definition in DATASETS:
        schema = json.loads(
            (
                package
                / "schemas"
                / "p-evidence-v1"
                / f"{definition.dataset_id}.schema.json"
            ).read_bytes()
        )
        assert schema["semantic_owners"]
        assert schema["export_steward"] == "shared substrate"
        assert all(column["value_origin"] for column in schema["columns"])
        assert all(
            "source_path" in column
            for column in schema["columns"]
            if column["value_origin"]
            in {
                "O_VIEW_FIELD",
                "O_ENVELOPE_FIELD",
                "O_QUERY_FIELD",
                "P_DISCOVERY_FIELD",
            }
        )
    assert not any(
        "*" in str(value.get("from_dataset", ""))
        or "*" in str(value.get("to_dataset", ""))
        for value in RELATIONSHIPS
    )
    assert any(
        value["relationship_type"] == "POLYMORPHIC_PARENT"
        and value["enforcement"] == "INTEGRITY_ONLY"
        for value in RELATIONSHIPS
    )


def test_reproduction_is_byte_identical_and_never_overwrites(
    governed_package: tuple[Path, GovernedExportService, _CountingBoundary],
) -> None:
    package, service, _ = governed_package
    reproduction = service.reproduce(package)

    assert reproduction.status == "REPRODUCED"
    assert reproduction.actual_digest == reproduction.expected_digest

    manifest = json.loads((package / "manifest.json").read_bytes())
    with pytest.raises(GovernedExportError, match="already exists"):
        service.build(
            BuildGovernedExport(
                export_ref=manifest["export_ref"],
                workspace_ref=manifest["workspace_ref"],
                semantic_as_of=manifest["semantic_as_of"],
                exported_at=manifest["exported_at"],
                output_path=package,
                discovery_descriptor_ref=manifest["discovery_descriptor_ref"],
                contract_version=manifest["contract_version"],
            )
        )


def test_offline_verifier_detects_tamper_missing_and_extra_files(
    governed_package: tuple[Path, GovernedExportService, _CountingBoundary],
    tmp_path: Path,
) -> None:
    package, _, _ = governed_package

    tampered = tmp_path / "tampered"
    shutil.copytree(package, tampered)
    target = tampered / "data" / "p-evidence-v1" / "P-D06.csv"
    target.write_bytes(target.read_bytes().replace(b"1000000", b"1000001", 1))
    assert verify_governed_export(tampered).status == "HASH_MISMATCH"

    missing = tmp_path / "missing"
    shutil.copytree(package, missing)
    (missing / "README.txt").unlink()
    assert verify_governed_export(missing).status == "MISSING_FILE"

    extra = tmp_path / "extra"
    shutil.copytree(package, extra)
    (extra / "unregistered.txt").write_text("not governed", encoding="utf-8")
    assert verify_governed_export(extra).status == "UNREGISTERED_FILE"


def test_offline_verifier_detects_resealed_relationship_and_snapshot_failures(
    governed_package: tuple[Path, GovernedExportService, _CountingBoundary],
    tmp_path: Path,
) -> None:
    package, _, _ = governed_package

    relationship = tmp_path / "relationship"
    shutil.copytree(package, relationship)
    definition = DATASET_BY_ID["P-D17"]
    rows = [dict(row) for row in _rows(relationship, "P-D17")]
    rows[0]["target_ref"] = "MISSING-TRACE-NODE"
    data_path = relationship / "data" / "p-evidence-v1" / "P-D17.csv"
    data_bytes = canonical_csv_bytes(definition, rows)
    data_path.write_bytes(data_bytes)
    manifest = json.loads((relationship / "manifest.json").read_bytes())
    next(
        item for item in manifest["dataset_entries"] if item["dataset_id"] == "P-D17"
    )["data_sha256"] = sha256_bytes(data_bytes)
    (relationship / "manifest.json").write_bytes(canonical_json_bytes(manifest))
    _reseal(relationship)
    assert verify_governed_export(relationship).status == "RELATIONSHIP_VIOLATION"

    snapshot = tmp_path / "snapshot"
    shutil.copytree(package, snapshot)
    definition = DATASET_BY_ID["P-D18"]
    rows = [dict(row) for row in _rows(snapshot, "P-D18")]
    rows[0]["query_revision"] = int(rows[0]["query_revision"]) + 1
    data_path = snapshot / "data" / "p-evidence-v1" / "P-D18.csv"
    data_bytes = canonical_csv_bytes(definition, rows)
    data_path.write_bytes(data_bytes)
    manifest = json.loads((snapshot / "manifest.json").read_bytes())
    next(
        item for item in manifest["dataset_entries"] if item["dataset_id"] == "P-D18"
    )["data_sha256"] = sha256_bytes(data_bytes)
    (snapshot / "manifest.json").write_bytes(canonical_json_bytes(manifest))
    _reseal(snapshot)
    assert verify_governed_export(snapshot).status == "SNAPSHOT_MISMATCH"


def test_failed_build_is_atomic_and_leaves_no_final_or_staging_path(
    tmp_path: Path,
) -> None:
    scenarios = default_demo_scenarios()
    database = tmp_path / "atomic.sqlite3"
    materialize_demo(database, scenarios)
    boundary = SqlitePersistenceBoundary(database)
    descriptor = build_export_discovery(
        scenarios,
        workspace_ref="TEST-DEMO",
        subjects=_subjects(),
    )
    c001 = descriptor.scenario_descriptors[0]
    broken_c001 = c001.model_copy(
        update={"expected_entry_points": c001.expected_entry_points[:-1]}
    )
    broken = descriptor.model_copy(
        update={
            "scenario_descriptors": (
                broken_c001,
                descriptor.scenario_descriptors[1],
            )
        },
    )
    service = GovernedExportService(
        boundary,
        scenarios=scenarios,
        descriptor=broken,
    )
    output = tmp_path / "failed-export"
    try:
        with pytest.raises(GovernedExportError, match="scenario sets differ"):
            service.build(
                BuildGovernedExport(
                    export_ref="P-EVIDENCE-FAILED",
                    workspace_ref="TEST-DEMO",
                    semantic_as_of=scenarios.semantic_as_of_time,
                    exported_at="2026-08-13T12:00:00Z",
                    output_path=output,
                    discovery_descriptor_ref=broken.discovery_descriptor_ref,
                    contract_version="governed-export-package@v1",
                )
            )
        assert not output.exists()
        assert not tuple(tmp_path.glob(".failed-export.staging-*"))
    finally:
        boundary.close()


def test_descriptor_subjects_are_parameterised_outside_the_exporter() -> None:
    scenarios = default_demo_scenarios()
    baseline = _subjects()
    alternate = ExportSubjectSet.model_validate(
        {
            key: f"ALT-{value}"
            for key, value in baseline.model_dump(mode="json").items()
        }
    )
    baseline_view = compile_export_discovery(
        build_export_discovery(
            scenarios,
            workspace_ref="TEST-DEMO",
            subjects=baseline,
        ),
        query_revision=1,
        scenario_set_digest="sha256:" + "0" * 64,
    )
    alternate_view = compile_export_discovery(
        build_export_discovery(
            scenarios,
            workspace_ref="TEST-DEMO",
            subjects=alternate,
        ),
        query_revision=1,
        scenario_set_digest="sha256:" + "0" * 64,
    )

    assert [item.request.query_id for item in baseline_view.query_requests] == [
        item.request.query_id for item in alternate_view.query_requests
    ]
    service_source = (
        Path(__file__).parents[2]
        / "src"
        / "finance_assurance"
        / "exports"
        / "service.py"
    ).read_text(encoding="utf-8")
    assert "RECON-C001@v1" not in service_source
    assert "VERIFY-CT1@v1" not in service_source
