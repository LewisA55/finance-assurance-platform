"""Finite O-C01/O-C02/O-C03 lifecycle for the disposable public demo."""

from __future__ import annotations

import hashlib
import os
import shutil
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory, mkstemp
from typing import Literal

from finance_assurance.product.contracts import PublicContractModel
from finance_assurance.product.demo_runtime import (
    DemoMaterialization,
    inspect_demo_boundary,
    materialize_demo,
)
from finance_assurance.product.demo_scenarios import DemoScenarioSet
from finance_assurance.runtime.application.queries import RuntimeQueryService
from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.persistence.models import QueryContext, RebuildContext
from finance_assurance.runtime.persistence.sqlite import SqlitePersistenceBoundary


class DemoLifecycleError(RuntimeError):
    """Base failure for the finite local demo lifecycle."""


class DemoAlreadyExistsError(DemoLifecycleError):
    """O-C01 target is not empty."""


class DemoNotInitialisedError(DemoLifecycleError):
    """O-C02/O-C03 target does not exist."""


class DemoWorkspaceUnrecognisedError(DemoLifecycleError):
    """Workspace does not carry the exact Artifact O baseline identity."""


class DemoVerificationError(DemoLifecycleError):
    """Materialised workspace does not satisfy its exact proof contract."""


class ScenarioVerification(PublicContractModel):
    scenario_ref: str
    canonical_family: Literal["C-001", "CT-1"]
    status: Literal["AVAILABLE", "FAILED"]
    event_count: int


class ViewVerification(PublicContractModel):
    view_contract: Literal[
        "O-V01",
        "O-V02",
        "O-V03",
        "O-V04",
        "O-V05",
        "O-V06",
        "O-V07",
        "O-V08",
        "O-V09",
        "O-V10",
        "O-V11",
    ]
    available: bool
    source_count: int


class DemoVerificationReport(PublicContractModel):
    demo_contract_version: Literal[1]
    workspace_ref: str
    runtime_release: str
    semantic_as_of_time: str
    compatibility_status: Literal["EXACT_ORIGINAL", "FAILED"]
    scenario_set_digest: str
    authoritative_inventory_digest: str
    semantic_state_digest: str
    restart_semantic_digest: str
    rebuilt_semantic_digest: str
    workspace_file_hash: str
    query_revision: int
    projection_generation_ref: str
    scenario_verification: tuple[ScenarioVerification, ...]
    view_verification: tuple[ViewVerification, ...]
    read_only_verified: bool
    passed: bool


class DemoLifecycleResult(PublicContractModel):
    operation: Literal["O-C01", "O-C02"]
    workspace_ref: str
    verification: DemoVerificationReport


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _body(record: object) -> dict[str, object]:
    semantic_body = record.semantic_body()
    if not isinstance(semantic_body, dict):
        raise DemoVerificationError("authoritative record body is not an object")
    return semantic_body


def _view_checks(
    boundary: SqlitePersistenceBoundary,
    scenarios: DemoScenarioSet,
) -> tuple[ViewVerification, ...]:
    session = boundary.open_query(
        QueryContext(semantic_as_of_time=str(scenarios.semantic_as_of_time))
    )
    records = session.authoritative_records()
    by_family: dict[str, tuple[object, ...]] = {
        family: tuple(item for item in records if item.record_family == family)
        for family in {item.record_family for item in records}
    }
    products = tuple(_body(item) for item in by_family.get("J-AR02", ()))
    canonical_products = tuple(
        item["canonical_body"]
        for item in products
        if isinstance(item.get("canonical_body"), dict)
    )
    product_discriminators = {
        str(item.get("product_discriminator")) for item in products
    }
    product_refs = {
        str(item.get("product_ref")) for item in canonical_products
    }
    reporting_refs = {
        item.record_identity for item in by_family.get("J-AR10", ())
    }
    journal_refs = {
        item.record_identity for item in by_family.get("J-AR08", ())
    }
    v1_ref = f"{scenarios.c001.reporting_version_id}@v1"
    v2_ref = f"{scenarios.c001.reporting_version_id}@v2"
    module_owners = {
        str(item.get("semantic_owner")) for item in products
    }
    trace_available = False
    try:
        trace = RuntimeQueryService(
            boundary,
            semantic_as_of_time=str(scenarios.semantic_as_of_time),
        ).trace_reporting_value(v2_ref, "subscription_revenue_minor")
        trace_available = (
            trace.statement_value_minor == scenarios.c001.monthly_revenue_minor
            and trace.content_verification_status == "CONTENT_BYTES_VERIFIED"
            and bool(trace.nodes)
            and bool(trace.edges)
        )
    except ValueError:
        trace_available = False
    checks: dict[str, tuple[bool, int]] = {
        "O-V01": (
            any(
                item.record_identity == "DEMO-BASELINE@v1"
                for item in by_family.get("J-AR04", ())
            ),
            1,
        ),
        "O-V02": (
            {"Hermes", "Argus", "Aegis", "Pythia"}.issubset(module_owners)
            and bool(by_family.get("J-AR08"))
            and bool(by_family.get("J-AR10")),
            len(module_owners | {"Atlas"}),
        ),
        "O-V03": (
            {
                "hermes.recognition_population_reconciliation",
                "hermes.cash_application_identity_reconciliation",
            }.issubset(product_discriminators),
            sum(
                item.startswith("hermes.") and item.endswith("reconciliation")
                for item in product_discriminators
            ),
        ),
        "O-V04": ({v1_ref, v2_ref}.issubset(reporting_refs), len(reporting_refs)),
        "O-V05": ({v1_ref, v2_ref}.issubset(reporting_refs), len(reporting_refs)),
        "O-V06": (
            {
                "argus.recognition_completeness_exception",
                "argus.cash_application_identity_exception",
            }.issubset(product_discriminators),
            sum(item.startswith("EXC-") for item in product_refs),
        ),
        "O-V07": (
            {
                "ISSUE-C001@v1",
                "ISSUE-C001@v2",
                "ISSUE-CT1@v1",
                "ISSUE-CT1@v2",
            }.issubset(product_refs),
            sum(item.startswith("ISSUE-") for item in product_refs),
        ),
        "O-V08": ("READY-C001@v1" in product_refs, 1),
        "O-V09": (
            {
                "PLAN-C001@v1",
                "DECISION-C001@v1",
                "APPROVAL-C001-HIRING@v1",
                "CANDIDATE-C001-HIRING@v1",
                "ADM-CANDIDATE-C001-HIRING@v1",
            }.issubset(product_refs),
            5,
        ),
        "O-V10": (trace_available, 1 if trace_available else 0),
        "O-V11": (
            {
                scenarios.ct1.reversal_journal_id,
                scenarios.ct1.replacement_journal_id,
            }.issubset(journal_refs)
            and "VERIFY-CT1@v1" in product_refs
            and any(
                item.record_identity == scenarios.ct1.source_journal_id
                for item in by_family.get("J-AR17", ())
            ),
            4,
        ),
    }
    return tuple(
        ViewVerification(
            view_contract=f"O-V{index:02d}",  # type: ignore[arg-type]
            available=checks[f"O-V{index:02d}"][0],
            source_count=checks[f"O-V{index:02d}"][1],
        )
        for index in range(1, 12)
    )


def _manifest_matches(
    boundary: SqlitePersistenceBoundary,
    scenarios: DemoScenarioSet,
) -> bool:
    session = boundary.open_query(
        QueryContext(semantic_as_of_time=str(scenarios.semantic_as_of_time))
    )
    record = session.authoritative_record("J-AR04", "DEMO-BASELINE@v1")
    if record is None:
        return False
    body = _body(record)
    return (
        body.get("contract_version") == scenarios.baseline_contract_version
        and body.get("runtime_release") == scenarios.runtime_release
        and body.get("scenario_set_digest")
        == canonical_sha256(scenarios.model_dump(mode="json"))
        and body.get("scenario_refs")
        == [str(scenarios.c001.scenario_ref), str(scenarios.ct1.scenario_ref)]
    )


def _rebuilt_digest(path: Path, scenarios: DemoScenarioSet) -> str:
    with TemporaryDirectory(prefix="finance-assurance-demo-verify-") as directory:
        copy = Path(directory) / "rebuild.sqlite3"
        shutil.copy2(path, copy)
        boundary = SqlitePersistenceBoundary(copy)
        try:
            boundary.delete_projection_checkpoint()
            session = boundary.open_rebuild(
                RebuildContext(
                    semantic_as_of_time=str(scenarios.semantic_as_of_time),
                    requested_projection_families=("J-P02", "J-P04", "J-P06"),
                )
            )
            generation = session.begin_generation()
            session.promote(session.validate(session.rebuild(generation)))
            return boundary.state.full_digest
        finally:
            boundary.close()


class DemoLifecycleService:
    """Expose only the three finite local Artifact O lifecycle operations."""

    def __init__(
        self,
        *,
        fault_injector: Callable[[str], None] | None = None,
    ) -> None:
        self._fault_injector = fault_injector

    def _inject(self, stage: str) -> None:
        if self._fault_injector is not None:
            self._fault_injector(stage)

    def initialise(
        self,
        target: Path,
        *,
        workspace_ref: str,
        scenarios: DemoScenarioSet,
    ) -> DemoLifecycleResult:
        """O-C01: materialise one new workspace, rejecting any existing target."""

        if target.exists():
            raise DemoAlreadyExistsError("O-C01 requires an empty workspace target")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._temporary_path(target)
        try:
            materialize_demo(temporary, scenarios)
            self._inject("after_materialize")
            verification = self.verify(
                temporary,
                workspace_ref=workspace_ref,
                scenarios=scenarios,
            )
            self._inject("before_replace")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return DemoLifecycleResult(
            operation="O-C01",
            workspace_ref=workspace_ref,
            verification=verification.model_copy(
                update={"workspace_file_hash": _file_hash(target)}
            ),
        )

    def recreate(
        self,
        target: Path,
        *,
        workspace_ref: str,
        scenarios: DemoScenarioSet,
    ) -> DemoLifecycleResult:
        """O-C02: replace only a recognised demo after complete candidate proof."""

        if not target.exists():
            raise DemoNotInitialisedError("O-C02 requires an existing demo workspace")
        prior = self.verify(
            target,
            workspace_ref=workspace_ref,
            scenarios=scenarios,
        )
        temporary = self._temporary_path(target)
        try:
            materialize_demo(temporary, scenarios)
            self._inject("after_materialize")
            candidate = self.verify(
                temporary,
                workspace_ref=workspace_ref,
                scenarios=scenarios,
            )
            if (
                candidate.authoritative_inventory_digest
                != prior.authoritative_inventory_digest
                or candidate.semantic_state_digest != prior.semantic_state_digest
            ):
                raise DemoVerificationError(
                    "O-C02 candidate is not semantically equal to the prior workspace"
                )
            self._inject("before_replace")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return DemoLifecycleResult(
            operation="O-C02",
            workspace_ref=workspace_ref,
            verification=candidate.model_copy(
                update={"workspace_file_hash": _file_hash(target)}
            ),
        )

    def verify(
        self,
        target: Path,
        *,
        workspace_ref: str,
        scenarios: DemoScenarioSet,
    ) -> DemoVerificationReport:
        """O-C03: prove compatibility, availability, and parity without mutation."""

        if not target.exists():
            raise DemoNotInitialisedError("O-C03 requires an existing demo workspace")
        before_hash = _file_hash(target)
        if target.read_bytes()[:16] != b"SQLite format 3\x00":
            raise DemoWorkspaceUnrecognisedError(
                "workspace is not a SQLite database"
            )
        with TemporaryDirectory(prefix="finance-assurance-demo-read-") as directory:
            verification_copy = Path(directory) / "workspace.sqlite3"
            shutil.copy2(target, verification_copy)
            try:
                boundary = SqlitePersistenceBoundary(verification_copy)
            except (ValueError, RuntimeError) as error:
                raise DemoWorkspaceUnrecognisedError(
                    "workspace cannot be opened under the current runtime contracts"
                ) from error
            try:
                if not _manifest_matches(boundary, scenarios):
                    raise DemoWorkspaceUnrecognisedError(
                        "workspace baseline or scenario coordinates are not recognised"
                    )
                materialization: DemoMaterialization = inspect_demo_boundary(
                    boundary, scenarios
                )
                views = _view_checks(boundary, scenarios)
                correlations = {
                    str(item.correlation_id) for item in boundary.state.event_log
                }
                scenario_verification = (
                    ScenarioVerification(
                        scenario_ref=str(scenarios.c001.scenario_ref),
                        canonical_family="C-001",
                        status=(
                            "AVAILABLE" if "C-001" in correlations else "FAILED"
                        ),
                        event_count=sum(
                            str(item.correlation_id) == "C-001"
                            for item in boundary.state.event_log
                        ),
                    ),
                    ScenarioVerification(
                        scenario_ref=str(scenarios.ct1.scenario_ref),
                        canonical_family="CT-1",
                        status=(
                            "AVAILABLE" if "CT-1" in correlations else "FAILED"
                        ),
                        event_count=sum(
                            str(item.correlation_id) == "CT-1"
                            for item in boundary.state.event_log
                        ),
                    ),
                )
                restart_digest = boundary.state.full_digest
            finally:
                boundary.close()
        rebuilt_digest = _rebuilt_digest(target, scenarios)
        after_hash = _file_hash(target)
        read_only = before_hash == after_hash
        passed = (
            read_only
            and materialization.event_count == 17
            and all(item.status == "AVAILABLE" for item in scenario_verification)
            and all(item.available for item in views)
            and materialization.semantic_state_digest
            == restart_digest
            == rebuilt_digest
        )
        report = DemoVerificationReport(
            demo_contract_version=1,
            workspace_ref=workspace_ref,
            runtime_release=str(scenarios.runtime_release),
            semantic_as_of_time=str(scenarios.semantic_as_of_time),
            compatibility_status="EXACT_ORIGINAL",
            scenario_set_digest=materialization.scenario_set_digest,
            authoritative_inventory_digest=(
                materialization.authoritative_inventory_digest
            ),
            semantic_state_digest=materialization.semantic_state_digest,
            restart_semantic_digest=restart_digest,
            rebuilt_semantic_digest=rebuilt_digest,
            workspace_file_hash=after_hash,
            query_revision=materialization.query_revision,
            projection_generation_ref=materialization.projection_generation_ref,
            scenario_verification=scenario_verification,
            view_verification=views,
            read_only_verified=read_only,
            passed=passed,
        )
        if not report.passed:
            raise DemoVerificationError("O-C03 demo verification failed")
        return report

    @staticmethod
    def _temporary_path(target: Path) -> Path:
        descriptor, name = mkstemp(
            prefix=f".{target.name}.",
            suffix=".building",
            dir=target.parent,
        )
        os.close(descriptor)
        temporary = Path(name)
        temporary.unlink()
        return temporary
