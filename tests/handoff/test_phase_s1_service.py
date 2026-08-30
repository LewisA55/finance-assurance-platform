from __future__ import annotations

import json
from pathlib import Path

import pytest

from finance_assurance.analytics.contracts import BuildGovernedAnalyticalExport
from finance_assurance.analytics.discovery import build_analytical_discovery
from finance_assurance.analytics.service import GovernedAnalyticalExportService
from finance_assurance.digestion.contracts import BuildConsumerModel
from finance_assurance.digestion.service import ConsumerModelService
from finance_assurance.digestion.writer import PARQUET_WRITER_PROFILE
from finance_assurance.exports.discovery import ExportSubjectSet, build_export_discovery
from finance_assurance.handoff.contracts import (
    BuildLocalAnalyticalHandoff,
    VerifyLocalAnalyticalHandoff,
)
from finance_assurance.handoff.profiles import (
    XLSX_TYPE_MAP_HASH,
    XLSX_WRITER_PROFILE_HASH,
)
from finance_assurance.handoff.service import (
    LocalAnalyticalHandoffError,
    LocalAnalyticalHandoffService,
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


@pytest.fixture(scope="module")
def source_package(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, str]:
    root = tmp_path_factory.mktemp("s1-source-package")
    scenarios = default_demo_scenarios()
    database = root / "demo.sqlite3"
    materialize_demo(database, scenarios)
    boundary = SqlitePersistenceBoundary(database)
    try:
        p_descriptor = build_export_discovery(
            scenarios,
            workspace_ref="S1-TEST",
            subjects=_subjects(),
        )
        q_descriptor = build_analytical_discovery(scenarios, p_descriptor)
        service = GovernedAnalyticalExportService(
            boundary,
            scenarios=scenarios,
            p_descriptor=p_descriptor,
            q_descriptor=q_descriptor,
        )
        package = root / "S1-PQ-SOURCE"
        result = service.build(
            BuildGovernedAnalyticalExport(
                request_contract_version="governed-analytical-export-request@v1",
                export_ref="S1-PQ-SOURCE",
                workspace_ref="S1-TEST",
                semantic_as_of=scenarios.semantic_as_of_time,
                exported_at="2026-08-24T10:00:00Z",
                output_path=package,
                p_discovery_descriptor_ref=p_descriptor.discovery_descriptor_ref,
                q_discovery_descriptor_ref=q_descriptor.discovery_descriptor_ref,
            )
        )
        yield package, result.package_digest
    finally:
        boundary.close()


def _request(package: Path, digest: str, output: Path) -> BuildConsumerModel:
    return BuildConsumerModel(
        request_contract_version="build-consumer-model-request@v1",
        model_ref="R-S1-LINEAGE@v1",
        source_package_path=package,
        expected_source_package_digest=digest,
        profile_id="LINEAGE",
        profile_version=1,
        formats=("CSV", "PARQUET", "DUCKDB"),
        parquet_writer_profile_ref="PYARROW-25@v1",
        parquet_writer_profile_hash=PARQUET_WRITER_PROFILE.profile_hash,
        duckdb_storage_compatibility_version="v1.5.0",
        output_path=output,
        producer_release="finance-assurance-r3-s1-integration@v1",
        built_at="2026-08-24T11:00:00Z",
    )


def _handoff_request(
    source_model: Path,
    source_package_path: Path,
    model_digest: str,
    source_digest: str,
    output: Path,
) -> BuildLocalAnalyticalHandoff:
    return BuildLocalAnalyticalHandoff(
        request_contract_version="build-local-analytical-handoff-request@v1",
        handoff_ref="S-INTEGRATION@v1",
        source_model_path=source_model,
        source_package_path=source_package_path,
        expected_model_digest=model_digest,
        expected_source_package_digest=source_digest,
        required_profile_id="LINEAGE",
        required_profile_version=1,
        required_formats=("CSV", "PARQUET", "DUCKDB"),
        output_path=output,
        producer_release="finance-assurance-s1-integration@v1",
        built_at="2026-08-24T12:00:00Z",
        xlsx_type_map_ref="XLSX-TYPE-MAP@v1",
        xlsx_type_map_hash=XLSX_TYPE_MAP_HASH,
        xlsx_writer_profile_ref="XLSXWRITER-3.2.9@v1",
        xlsx_writer_profile_hash=XLSX_WRITER_PROFILE_HASH,
        validation_registry_ref="S-VALIDATION-C001-CT1@v1",
        validation_registry_hash=(
            "sha256:36255992b12b0176f290ec2fa033e5655d8ca4b3a2e4cbd3a522a1de295f7cb8"
        ),
    )


def test_real_handoff_build_verify_and_binary_tamper_rejection(
    source_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, source_digest = source_package
    model_path = tmp_path / "lineage-model"
    model = ConsumerModelService().build(
        _request(package, source_digest, model_path)
    )
    handoff_path = tmp_path / "analytical-handoff"
    service = LocalAnalyticalHandoffService()
    built = service.build(
        _handoff_request(
            model_path,
            package,
            model.model_digest,
            source_digest,
            handoff_path,
        )
    )
    verification_request = VerifyLocalAnalyticalHandoff(
        request_contract_version="verify-local-analytical-handoff-request@v1",
        handoff_path=handoff_path,
        source_package_path=package,
        expected_handoff_digest=built.handoff_digest,
        expected_model_digest=model.model_digest,
        expected_source_package_digest=source_digest,
        verification_scope="FULL_HANDOFF_EQUIVALENCE",
    )
    verified = service.verify(verification_request)
    assert verified.status == "VERIFIED"
    assert verified.checked_table_count == 31
    assert verified.checked_sheet_count == 36
    workbook_manifest = json.loads(
        (handoff_path / "excel/noncanonical-workbook.json").read_bytes()
    )
    assert workbook_manifest["logical_workbook_digest"] == built.workbook_logical_digest
    empty_sheet = next(
        item
        for item in workbook_manifest["sheet_entries"]
        if (item.get("source_dataset_coordinate") or {}).get("dataset_id") == "P-D20"
    )
    assert empty_sheet["row_count"] == 0
    assert empty_sheet["table_name"] is None

    source_metadata = json.loads(
        (handoff_path / "metadata/source-model.json").read_bytes()
    )
    cache_pointer = next(
        item
        for item in source_metadata["field_provenance"]
        if item["target_json_pointer"].endswith("/database_sha256")
    )
    assert cache_pointer["source_pointers"][0]["source_document_path"] == (
        "source-model/noncanonical-cache.json"
    )

    dictionary = json.loads(
        (handoff_path / "metadata/data-dictionary.json").read_bytes()
    )
    semantic_pointer = next(
        item
        for item in dictionary["field_provenance"]
        if item["target_json_pointer"] == "/payload/columns/0/source_name"
    )
    assert semantic_pointer["source_pointers"][0]["source_document_path"] == (
        "source-model/semantic-model.json"
    )

    workbook = handoff_path / "excel/finance-assurance-data-pack.xlsx"
    workbook.write_bytes(workbook.read_bytes() + b"tamper")
    with pytest.raises(LocalAnalyticalHandoffError, match="XLSX binary"):
        service.verify(verification_request)
