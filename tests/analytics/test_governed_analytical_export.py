from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from finance_assurance.analytics.contracts import BuildGovernedAnalyticalExport
from finance_assurance.analytics.discovery import build_analytical_discovery
from finance_assurance.analytics.registry import DATASET_BY_ID
from finance_assurance.analytics.service import GovernedAnalyticalExportService
from finance_assurance.exports.contracts import ChecksumEntry, ChecksumLedger
from finance_assurance.exports.discovery import ExportSubjectSet, build_export_discovery
from finance_assurance.exports.serialization import (
    canonical_json_bytes,
    parse_canonical_csv,
    sha256_bytes,
)
from finance_assurance.exports.service import (
    GovernedExportError,
    verify_governed_export,
)
from finance_assurance.product.demo_runtime import materialize_demo
from finance_assurance.product.demo_scenarios import default_demo_scenarios
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
    payload = canonical_json_bytes(ledger.model_dump(mode="json"))
    (package / "checksums.json").write_bytes(payload)
    (package / "package.digest").write_text(
        f"{sha256_bytes(payload)}\n",
        encoding="ascii",
        newline="\n",
    )


@pytest.fixture(scope="module")
def analytical_package(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, GovernedAnalyticalExportService, _CountingBoundary]:
    root = tmp_path_factory.mktemp("governed-analytical-export")
    scenarios = default_demo_scenarios()
    database = root / "demo.sqlite3"
    materialize_demo(database, scenarios)
    boundary = SqlitePersistenceBoundary(database)
    counted = _CountingBoundary(boundary)
    p_descriptor = build_export_discovery(
        scenarios,
        workspace_ref="TEST-DEMO",
        subjects=_subjects(),
    )
    q_descriptor = build_analytical_discovery(scenarios, p_descriptor)
    service = GovernedAnalyticalExportService(  # type: ignore[arg-type]
        counted,
        scenarios=scenarios,
        p_descriptor=p_descriptor,
        q_descriptor=q_descriptor,
    )
    package = root / "Q-ANALYTICS-DEMO"
    result = service.build(
        BuildGovernedAnalyticalExport(
            request_contract_version="governed-analytical-export-request@v1",
            export_ref="Q-ANALYTICS-DEMO",
            workspace_ref="TEST-DEMO",
            semantic_as_of=scenarios.semantic_as_of_time,
            exported_at="2026-08-13T12:00:00Z",
            output_path=package,
            p_discovery_descriptor_ref=p_descriptor.discovery_descriptor_ref,
            q_discovery_descriptor_ref=q_descriptor.discovery_descriptor_ref,
        )
    )
    assert result.dataset_count == 37
    yield package, service, counted
    boundary.close()


def _q_rows(package: Path, dataset_id: str) -> tuple[dict[str, object], ...]:
    return parse_canonical_csv(
        DATASET_BY_ID[dataset_id],  # type: ignore[arg-type]
        (package / "data" / "q-analytics-v1" / f"{dataset_id}.csv").read_bytes(),
    )


def test_combined_package_is_verified_and_uses_one_snapshot(
    analytical_package: tuple[
        Path,
        GovernedAnalyticalExportService,
        _CountingBoundary,
    ],
) -> None:
    package, _, counted = analytical_package

    verification = verify_governed_export(package)

    assert verification.status == "VERIFIED"
    assert verification.checked_dataset_count == 37
    assert counted.query_count == 1
    assert len(_q_rows(package, "Q-D13")) == 10
    assert len(_q_rows(package, "Q-D14")) == 38
    q00 = next(row for row in _q_rows(package, "Q-D13") if row["query_id"] == "Q-Q00")
    assert q00["query_instance_ref"] == (
        f"Q00:{str(q00['canonical_request_hash'])[7:31]}"
    )


def test_reversal_hash_is_verified_against_exact_j_ar17(
    analytical_package: tuple[
        Path,
        GovernedAnalyticalExportService,
        _CountingBoundary,
    ],
) -> None:
    package, _, _ = analytical_package

    verified = [
        row
        for row in _q_rows(package, "Q-D06")
        if row["verification_status"] == "CONTENT_BYTES_VERIFIED"
    ]

    assert len(verified) == 1
    assert str(verified[0]["verification_proof_ref"]).startswith("J-AR17:")


def test_combined_package_reproduces_byte_for_byte(
    analytical_package: tuple[
        Path,
        GovernedAnalyticalExportService,
        _CountingBoundary,
    ],
) -> None:
    package, service, counted = analytical_package

    result = service.reproduce(package)

    assert result.status == "REPRODUCED"
    assert counted.query_count == 2


def test_q_file_tamper_is_detected(
    analytical_package: tuple[
        Path,
        GovernedAnalyticalExportService,
        _CountingBoundary,
    ],
    tmp_path: Path,
) -> None:
    source, _, _ = analytical_package
    package = tmp_path / "tampered"
    shutil.copytree(source, package)
    path = package / "data" / "q-analytics-v1" / "Q-D01.csv"
    path.write_bytes(path.read_bytes() + b"x")

    assert verify_governed_export(package).status == "HASH_MISMATCH"


def test_q_registry_without_p_is_rejected(
    analytical_package: tuple[
        Path,
        GovernedAnalyticalExportService,
        _CountingBoundary,
    ],
    tmp_path: Path,
) -> None:
    source, _, _ = analytical_package
    package = tmp_path / "q-without-p"
    shutil.copytree(source, package)
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["dataset_registries"] = [
        item
        for item in manifest["dataset_registries"]
        if item["registry_id"] == "Q-ANALYTICS"
    ]
    manifest["dataset_entries"] = [
        item
        for item in manifest["dataset_entries"]
        if item["registry_id"] == "Q-ANALYTICS"
    ]
    manifest["relationship_contract_version"] = 1
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    relationships_path = package / "relationships.json"
    relationships = json.loads(relationships_path.read_text(encoding="utf-8"))
    relationships_path.write_bytes(
        canonical_json_bytes(
            [
                item
                for item in relationships
                if item["relationship_id"].startswith("Q-")
            ]
        )
    )
    shutil.rmtree(package / "data" / "p-evidence-v1")
    shutil.rmtree(package / "schemas" / "p-evidence-v1")
    _reseal(package)

    assert verify_governed_export(package).status == "UNSUPPORTED_CONTRACT"


def test_q_subjects_must_reconcile_to_executed_public_views(
    analytical_package: tuple[
        Path,
        GovernedAnalyticalExportService,
        _CountingBoundary,
    ],
    tmp_path: Path,
) -> None:
    _, service, _ = analytical_package
    bad_subjects = service._q_descriptor.subjects.model_copy(
        update={"c001_journal_id": "J-NOT-IN-PUBLIC-TRACE"}
    )
    bad_descriptor = service._q_descriptor.model_copy(
        update={"subjects": bad_subjects}
    )
    bad_service = GovernedAnalyticalExportService(
        service._boundary,  # type: ignore[arg-type]
        scenarios=service._scenarios,
        p_descriptor=service._p_descriptor,
        q_descriptor=bad_descriptor,
    )
    output = tmp_path / "subject-mismatch"

    with pytest.raises(GovernedExportError, match="subject set differs"):
        bad_service.build(
            BuildGovernedAnalyticalExport(
                request_contract_version="governed-analytical-export-request@v1",
                export_ref="Q-ANALYTICS-SUBJECT-MISMATCH",
                workspace_ref="TEST-DEMO",
                semantic_as_of=service._scenarios.semantic_as_of_time,
                exported_at="2026-08-13T12:00:00Z",
                output_path=output,
                p_discovery_descriptor_ref=(
                    service._p_descriptor.discovery_descriptor_ref
                ),
                q_discovery_descriptor_ref=bad_descriptor.discovery_descriptor_ref,
            )
        )
    assert not output.exists()
    assert not tuple(tmp_path.glob(".subject-mismatch.staging-*"))
