"""Build, verify, reproduce, or accept local Artifact P and Q packages."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from finance_assurance.analytics.acceptance import (
    ACCEPTANCE_CATALOG as Q_ACCEPTANCE_CATALOG,
)
from finance_assurance.analytics.acceptance import (
    validate_catalog as validate_q_catalog,
)
from finance_assurance.analytics.contracts import BuildGovernedAnalyticalExport
from finance_assurance.analytics.discovery import build_analytical_discovery
from finance_assurance.analytics.service import GovernedAnalyticalExportService
from finance_assurance.digestion.acceptance import (
    ACCEPTANCE_CATALOG as R_ACCEPTANCE_CATALOG,
)
from finance_assurance.digestion.acceptance import (
    validate_catalog as validate_r_catalog,
)
from finance_assurance.digestion.contracts import (
    BuildConsumerModel,
    ModelManifest,
    ReproduceConsumerModel,
    VerifyConsumerModel,
)
from finance_assurance.digestion.service import (
    ConsumerModelService,
    verify_consumer_model,
)
from finance_assurance.digestion.writer import PARQUET_WRITER_PROFILE
from finance_assurance.exports.acceptance import ACCEPTANCE_CATALOG, validate_catalog
from finance_assurance.exports.contracts import BuildGovernedExport
from finance_assurance.exports.discovery import (
    ExportSubjectSet,
    build_export_discovery,
)
from finance_assurance.exports.serialization import canonical_json_bytes
from finance_assurance.exports.service import (
    GovernedExportService,
    verify_governed_export,
)
from finance_assurance.product.demo_runtime import materialize_demo
from finance_assurance.product.demo_scenarios import default_demo_scenarios
from finance_assurance.runtime.persistence.sqlite import SqlitePersistenceBoundary

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONSUMER_MODEL = (
    PROJECT_ROOT / "build" / "model-digestion" / "R-LINEAGE-DEMO"
)
DEFAULT_REPRODUCED_MODEL = (
    PROJECT_ROOT / "build" / "model-digestion" / "R-LINEAGE-DEMO-REPRODUCED"
)
DEFAULT_EXPORT = PROJECT_ROOT / "build" / "governed-outputs" / "P-EVIDENCE-DEMO"
DEFAULT_ANALYTICAL_EXPORT = (
    PROJECT_ROOT / "build" / "governed-outputs" / "Q-ANALYTICS-DEMO"
)
DEFAULT_DATABASE = PROJECT_ROOT / "build" / "governed-outputs" / "demo.sqlite3"
DEFAULT_REPORT = PROJECT_ROOT / "build" / "milestone-4-report.json"
EXPORTED_AT = "2026-08-13T12:00:00Z"


def _default_subjects() -> ExportSubjectSet:
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


def _analytical_service(
    database: Path,
) -> tuple[GovernedAnalyticalExportService, SqlitePersistenceBoundary]:
    scenarios = default_demo_scenarios()
    if not database.exists():
        database.parent.mkdir(parents=True, exist_ok=True)
        materialize_demo(database, scenarios)
    boundary = SqlitePersistenceBoundary(database)
    p_descriptor = build_export_discovery(
        scenarios,
        workspace_ref="FINANCE-ASSURANCE-DEMO",
        subjects=_default_subjects(),
    )
    q_descriptor = build_analytical_discovery(scenarios, p_descriptor)
    return (
        GovernedAnalyticalExportService(
            boundary,
            scenarios=scenarios,
            p_descriptor=p_descriptor,
            q_descriptor=q_descriptor,
        ),
        boundary,
    )


def _service(database: Path) -> tuple[GovernedExportService, SqlitePersistenceBoundary]:
    scenarios = default_demo_scenarios()
    if not database.exists():
        database.parent.mkdir(parents=True, exist_ok=True)
        materialize_demo(database, scenarios)
    boundary = SqlitePersistenceBoundary(database)
    descriptor = build_export_discovery(
        scenarios,
        workspace_ref="FINANCE-ASSURANCE-DEMO",
        subjects=_default_subjects(),
    )
    return (
        GovernedExportService(
            boundary,
            scenarios=scenarios,
            descriptor=descriptor,
        ),
        boundary,
    )


def build(output: Path, database: Path) -> int:
    scenarios = default_demo_scenarios()
    service, boundary = _service(database)
    try:
        result = service.build(
            BuildGovernedExport(
                export_ref=output.name,
                workspace_ref="FINANCE-ASSURANCE-DEMO",
                semantic_as_of=scenarios.semantic_as_of_time,
                exported_at=EXPORTED_AT,
                output_path=output,
                discovery_descriptor_ref="EXPORT-DISCOVERY-DEMO@v1",
                contract_version="governed-export-package@v1",
            )
        )
    finally:
        boundary.close()
    print(result.model_dump_json(indent=2))
    return 0


def verify(output: Path) -> int:
    result = verify_governed_export(output)
    print(result.model_dump_json(indent=2))
    return 0 if result.status == "VERIFIED" else 1


def build_analytics(output: Path, database: Path) -> int:
    scenarios = default_demo_scenarios()
    service, boundary = _analytical_service(database)
    try:
        result = service.build(
            BuildGovernedAnalyticalExport(
                request_contract_version="governed-analytical-export-request@v1",
                export_ref=output.name,
                workspace_ref="FINANCE-ASSURANCE-DEMO",
                semantic_as_of=scenarios.semantic_as_of_time,
                exported_at=EXPORTED_AT,
                output_path=output,
                p_discovery_descriptor_ref="EXPORT-DISCOVERY-DEMO@v1",
                q_discovery_descriptor_ref="ANALYTICAL-DISCOVERY-DEMO@v1",
            )
        )
    finally:
        boundary.close()
    print(result.model_dump_json(indent=2))
    return 0


def reproduce_analytics(output: Path, database: Path) -> int:
    service, boundary = _analytical_service(database)
    try:
        result = service.reproduce(output)
    finally:
        boundary.close()
    print(result.model_dump_json(indent=2))
    return 0 if result.status == "REPRODUCED" else 1


def build_model(output: Path, source: Path, profile: str) -> int:
    verification = verify_governed_export(source)
    if verification.status != "VERIFIED" or verification.package_digest is None:
        print(verification.model_dump_json(indent=2))
        return 1
    result = ConsumerModelService().build(
        BuildConsumerModel(
            request_contract_version="build-consumer-model-request@v1",
            model_ref=output.name,
            source_package_path=source,
            expected_source_package_digest=verification.package_digest,
            profile_id=profile,
            profile_version=1,
            formats=("CSV", "PARQUET"),
            parquet_writer_profile_ref="PYARROW-25@v1",
            parquet_writer_profile_hash=PARQUET_WRITER_PROFILE.profile_hash,
            output_path=output,
            producer_release="finance-assurance-r2-local@v1",
            built_at="2026-08-13T15:00:00Z",
        )
    )
    print(result.model_dump_json(indent=2))
    return 0


def verify_model(output: Path, source: Path) -> int:
    manifest = ModelManifest.model_validate_json(
        (output / "model-manifest.json").read_bytes()
    )
    digest = (output / "model.digest").read_text(encoding="ascii").strip()
    result = verify_consumer_model(
        VerifyConsumerModel(
            request_contract_version="verify-consumer-model-request@v1",
            model_path=output,
            source_package_path=source,
            expected_model_digest=digest,
            expected_source_package_digest=manifest.source_package_digest,
            verification_scope="FULL_SOURCE_EQUIVALENCE",
        )
    )
    print(result.model_dump_json(indent=2))
    return 0 if result.status == "VERIFIED" else 1


def reproduce_model(output: Path, source: Path, reproduction_output: Path) -> int:
    manifest = ModelManifest.model_validate_json(
        (output / "model-manifest.json").read_bytes()
    )
    digest = (output / "model.digest").read_text(encoding="ascii").strip()
    result = ConsumerModelService().reproduce(
        ReproduceConsumerModel(
            request_contract_version="reproduce-consumer-model-request@v1",
            source_model_path=output,
            source_package_path=source,
            reproduction_output_path=reproduction_output,
            expected_model_digest=digest,
            expected_source_package_digest=manifest.source_package_digest,
        )
    )
    print(result.model_dump_json(indent=2))
    return 0 if result.status == "REPRODUCED" else 1


def reproduce(output: Path, database: Path) -> int:
    service, boundary = _service(database)
    try:
        result = service.reproduce(output)
    finally:
        boundary.close()
    print(result.model_dump_json(indent=2))
    return 0 if result.status == "REPRODUCED" else 1


def _run(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
        text=True,
        timeout=900,
    )


def acceptance(report_path: Path) -> int:
    validate_catalog()
    validate_q_catalog()
    validate_r_catalog()
    ruff = shutil.which("ruff") or str(PROJECT_ROOT / ".venv" / "Scripts" / "ruff.exe")
    pytest = shutil.which("pytest") or str(
        PROJECT_ROOT / ".venv" / "Scripts" / "pytest.exe"
    )
    gates = {
        "ruff": _run((ruff, "check", ".")),
        "pytest": _run((pytest, "-q")),
    }
    with tempfile.TemporaryDirectory(prefix="finance-assurance-m4-") as directory:
        root = Path(directory)
        database = root / "demo.sqlite3"
        package = root / "P-EVIDENCE-ACCEPTANCE"
        analytical_package = root / "Q-ANALYTICS-ACCEPTANCE"
        consumer_model = root / "R-LINEAGE-ACCEPTANCE"
        reproduced_model = root / "R-LINEAGE-REPRODUCED"
        scenarios = default_demo_scenarios()
        materialize_demo(database, scenarios)
        boundary = SqlitePersistenceBoundary(database)
        p_descriptor = build_export_discovery(
            scenarios,
            workspace_ref="FINANCE-ASSURANCE-DEMO",
            subjects=_default_subjects(),
        )
        service = GovernedExportService(
            boundary,
            scenarios=scenarios,
            descriptor=p_descriptor,
        )
        q_descriptor = build_analytical_discovery(scenarios, p_descriptor)
        analytical_service = GovernedAnalyticalExportService(
            boundary,
            scenarios=scenarios,
            p_descriptor=p_descriptor,
            q_descriptor=q_descriptor,
        )
        try:
            built = service.build(
                BuildGovernedExport(
                    export_ref=package.name,
                    workspace_ref="FINANCE-ASSURANCE-DEMO",
                    semantic_as_of=scenarios.semantic_as_of_time,
                    exported_at=EXPORTED_AT,
                    output_path=package,
                    discovery_descriptor_ref="EXPORT-DISCOVERY-DEMO@v1",
                    contract_version="governed-export-package@v1",
                )
            )
            verified = verify_governed_export(package)
            reproduced = service.reproduce(package)
            analytical_built = analytical_service.build(
                BuildGovernedAnalyticalExport(
                    request_contract_version=(
                        "governed-analytical-export-request@v1"
                    ),
                    export_ref=analytical_package.name,
                    workspace_ref="FINANCE-ASSURANCE-DEMO",
                    semantic_as_of=scenarios.semantic_as_of_time,
                    exported_at=EXPORTED_AT,
                    output_path=analytical_package,
                    p_discovery_descriptor_ref=(
                        p_descriptor.discovery_descriptor_ref
                    ),
                    q_discovery_descriptor_ref=(
                        q_descriptor.discovery_descriptor_ref
                    ),
                )
            )
            analytical_verified = verify_governed_export(analytical_package)
            analytical_reproduced = analytical_service.reproduce(
                analytical_package
            )
            assert analytical_built.package_digest is not None
            model_built = ConsumerModelService().build(
                BuildConsumerModel(
                    request_contract_version="build-consumer-model-request@v1",
                    model_ref=consumer_model.name,
                    source_package_path=analytical_package,
                    expected_source_package_digest=analytical_built.package_digest,
                    profile_id="LINEAGE",
                    profile_version=1,
                    formats=("CSV", "PARQUET"),
                    parquet_writer_profile_ref="PYARROW-25@v1",
                    parquet_writer_profile_hash=PARQUET_WRITER_PROFILE.profile_hash,
                    output_path=consumer_model,
                    producer_release="finance-assurance-r2-local@v1",
                    built_at="2026-08-13T15:00:00Z",
                )
            )
            model_verified = verify_consumer_model(
                VerifyConsumerModel(
                    request_contract_version="verify-consumer-model-request@v1",
                    model_path=consumer_model,
                    source_package_path=analytical_package,
                    expected_model_digest=model_built.model_digest,
                    expected_source_package_digest=model_built.source_package_digest,
                    verification_scope="FULL_SOURCE_EQUIVALENCE",
                )
            )
            model_reproduced = ConsumerModelService().reproduce(
                ReproduceConsumerModel(
                    request_contract_version="reproduce-consumer-model-request@v1",
                    source_model_path=consumer_model,
                    source_package_path=analytical_package,
                    reproduction_output_path=reproduced_model,
                    expected_model_digest=model_built.model_digest,
                    expected_source_package_digest=model_built.source_package_digest,
                )
            )
        finally:
            boundary.close()
    passed = all(item.returncode == 0 for item in gates.values()) and (
        verified.status == "VERIFIED"
        and reproduced.status == "REPRODUCED"
        and analytical_verified.status == "VERIFIED"
        and analytical_reproduced.status == "REPRODUCED"
        and model_verified.status == "VERIFIED"
        and model_reproduced.status == "REPRODUCED"
    )
    report = {
        "acceptance_contract": "milestone-4-governed-outputs-acceptance@v3",
        "artifact": "P+Q+R",
        "artifact_version": "P-v0.2+Q-v0.2+R-v0.2",
        "criteria": [
            {
                "criterion_id": item.criterion_id,
                "evidence_tests": list(item.evidence_tests),
                "statement": item.statement,
                "status": "PASS" if passed else "FAIL",
            }
            for item in (
                *ACCEPTANCE_CATALOG,
                *Q_ACCEPTANCE_CATALOG,
                *R_ACCEPTANCE_CATALOG,
            )
        ],
        "gates": {
            name: {
                "returncode": result.returncode,
                "status": "PASS" if result.returncode == 0 else "FAIL",
            }
            for name, result in gates.items()
        }
        | {
            "package_build": {"status": "PASS", "digest": built.package_digest},
            "offline_verification": {"status": verified.status},
            "reproduction": {"status": reproduced.status},
            "analytical_package_build": {
                "status": "PASS",
                "digest": analytical_built.package_digest,
            },
            "analytical_offline_verification": {
                "status": analytical_verified.status
            },
            "analytical_reproduction": {
                "status": analytical_reproduced.status
            },
            "consumer_model_build": {
                "status": "PASS",
                "digest": model_built.model_digest,
            },
            "consumer_model_verification": {"status": model_verified.status},
            "consumer_model_reproduction": {"status": model_reproduced.status},
        },
        "overall_status": "PASS" if passed else "FAIL",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(canonical_json_bytes(report))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=(
            "build",
            "build-analytics",
            "build-model",
            "verify",
            "verify-model",
            "reproduce",
            "reproduce-analytics",
            "reproduce-model",
            "acceptance",
        ),
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--source", type=Path, default=DEFAULT_ANALYTICAL_EXPORT)
    parser.add_argument(
        "--reproduction-output", type=Path, default=DEFAULT_REPRODUCED_MODEL
    )
    parser.add_argument(
        "--profile", choices=("CORE", "LINEAGE", "DIAGNOSTIC"), default="LINEAGE"
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.action == "build":
        return build(args.output, args.database)
    if args.action == "build-analytics":
        output = (
            DEFAULT_ANALYTICAL_EXPORT
            if args.output == DEFAULT_EXPORT
            else args.output
        )
        return build_analytics(output, args.database)
    if args.action == "verify":
        return verify(args.output)
    if args.action == "reproduce":
        return reproduce(args.output, args.database)
    if args.action == "reproduce-analytics":
        output = (
            DEFAULT_ANALYTICAL_EXPORT
            if args.output == DEFAULT_EXPORT
            else args.output
        )
        return reproduce_analytics(output, args.database)
    if args.action == "build-model":
        output = DEFAULT_CONSUMER_MODEL if args.output == DEFAULT_EXPORT else args.output
        return build_model(output, args.source, args.profile)
    if args.action == "verify-model":
        output = DEFAULT_CONSUMER_MODEL if args.output == DEFAULT_EXPORT else args.output
        return verify_model(output, args.source)
    if args.action == "reproduce-model":
        output = DEFAULT_CONSUMER_MODEL if args.output == DEFAULT_EXPORT else args.output
        return reproduce_model(output, args.source, args.reproduction_output)
    return acceptance(args.report)


if __name__ == "__main__":
    raise SystemExit(main())
