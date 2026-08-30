"""Q-C01 bounded P-EVIDENCE plus Q-ANALYTICS package service."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import cast
from uuid import uuid4

from finance_assurance.analytics.contracts import (
    AnalyticalDiscoveryDescriptor,
    BuildGovernedAnalyticalExport,
)
from finance_assurance.analytics.discovery import compile_analytical_discovery
from finance_assurance.analytics.query_service import AnalyticalQueryService
from finance_assurance.analytics.registry import (
    DATASETS as Q_DATASETS,
)
from finance_assurance.analytics.registry import (
    REGISTRY_ID as Q_REGISTRY_ID,
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
from finance_assurance.analytics.tabularize import (
    ExecutedAnalyticalQuery,
    tabularize_analytics,
)
from finance_assurance.exports.contracts import (
    BuildGovernedExportResult,
    ChecksumEntry,
    ChecksumLedger,
    DatasetManifestEntry,
    DatasetRegistryEntry,
    ExportDiscoveryDescriptor,
    GovernedExportManifest,
    ReproductionResult,
)
from finance_assurance.exports.discovery import compile_export_discovery
from finance_assurance.exports.registry import (
    DATASETS as P_DATASETS,
)
from finance_assurance.exports.registry import (
    REGISTRY_ID as P_REGISTRY_ID,
)
from finance_assurance.exports.registry import (
    REGISTRY_VERSION as P_REGISTRY_VERSION,
)
from finance_assurance.exports.registry import (
    RELATIONSHIPS as P_RELATIONSHIPS,
)
from finance_assurance.exports.registry import (
    STORAGE_KEY as P_STORAGE_KEY,
)
from finance_assurance.exports.registry import (
    registry_contract_hash as p_registry_contract_hash,
)
from finance_assurance.exports.serialization import (
    canonical_csv_bytes,
    canonical_json_bytes,
    sha256_bytes,
)
from finance_assurance.exports.service import (
    PACKAGE_CONTRACT,
    PRODUCER_RELEASE,
    GovernedExportError,
    verify_governed_export,
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


def _readme(manifest: GovernedExportManifest) -> bytes:
    lines = (
        "Finance & Assurance Platform - Governed Analytical Package",
        "",
        f"Export: {manifest.export_ref}",
        f"Contract: {manifest.contract_version}",
        "Registries: P-EVIDENCE@v1, Q-ANALYTICS@v1",
        f"Snapshot revision: {manifest.query_revision}",
        f"Semantic as-of: {manifest.semantic_as_of}",
        "Synthetic data: true",
        f"Notice: {manifest.synthetic_data_notice}",
        "",
        "Verify this directory before use. Q-ANALYTICS is the governed",
        "local-consumer boundary for Excel, Power BI, and equivalent tools.",
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


class GovernedAnalyticalExportService:
    """Build and reproduce the finite two-registry Artifact Q package."""

    def __init__(
        self,
        boundary: PersistenceBoundary,
        *,
        scenarios: DemoScenarioSet,
        p_descriptor: ExportDiscoveryDescriptor,
        q_descriptor: AnalyticalDiscoveryDescriptor,
        producer_release: str = PRODUCER_RELEASE,
    ) -> None:
        self._boundary = boundary
        self._scenarios = scenarios
        self._p_descriptor = p_descriptor
        self._q_descriptor = q_descriptor
        self._producer_release = producer_release
        self._public = PublicQueryService(
            boundary,
            scenarios=scenarios,
            workspace_ref=p_descriptor.workspace_ref,
        )
        self._analytical = AnalyticalQueryService()

    def build(
        self,
        request: BuildGovernedAnalyticalExport,
        *,
        required_query_revision: int | None = None,
    ) -> BuildGovernedExportResult:
        self._validate_request(request)
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
        scenario_digest = canonical_sha256(self._scenarios.model_dump(mode="json"))
        p_discovery = compile_export_discovery(
            self._p_descriptor,
            query_revision=session.revision,
            scenario_set_digest=scenario_digest,
        )
        q_discovery = compile_analytical_discovery(
            self._q_descriptor,
            query_revision=session.revision,
            scenario_set_digest=scenario_digest,
        )
        public_executed: list[ExecutedPublicQuery] = []
        analytical_executed: list[ExecutedAnalyticalQuery] = []
        try:
            staging.mkdir()
            for owned in p_discovery.query_requests:
                result = self._public.execute_in_session(owned.request, session)
                if not hasattr(result, "view_contract"):
                    code = getattr(result, "error_code", "INTERNAL_FAILURE")
                    raise GovernedExportError(
                        f"Artifact O query {owned.request.query_id} failed: {code}"
                    )
                envelope = cast(PublicSuccessEnvelope, result)
                if (
                    envelope.query_revision != session.revision
                    or str(envelope.semantic_as_of_time)
                    != str(p_discovery.semantic_as_of)
                    or envelope.compatibility_read_mode != "EXACT_ORIGINAL"
                ):
                    raise GovernedExportError("Artifact O snapshot mismatch")
                body = owned.request.model_dump(mode="json")
                public_executed.append(
                    ExecutedPublicQuery(
                        request=owned.request,
                        envelope=envelope,
                        canonical_request_hash=canonical_sha256(body),
                        query_instance_ref=query_instance_ref(body),
                    )
                )
            self._validate_public_membership(p_discovery, tuple(public_executed))
            self._validate_analytical_subjects(tuple(public_executed))
            for query in q_discovery.query_plan:
                view = self._analytical.execute_in_session(query, session)
                if (
                    view.query_revision != session.revision
                    or str(view.semantic_as_of_time) != str(q_discovery.semantic_as_of)
                    or view.compatibility_mode != "EXACT_ORIGINAL"
                ):
                    raise GovernedExportError("Artifact Q snapshot mismatch")
                analytical_executed.append(
                    ExecutedAnalyticalQuery(request=query, view=view)
                )
            p_rows = tabularize(
                discovery=p_discovery,
                executed=tuple(public_executed),
                export_ref=request.export_ref,
                exported_at=str(request.exported_at),
                producer_release=self._producer_release,
            )
            q_rows = tabularize_analytics(
                descriptor=self._q_descriptor,
                discovery=q_discovery,
                executed=tuple(analytical_executed),
                p_package_context=p_rows["P-D01"][0],
                export_ref=request.export_ref,
            )
            manifest = self._write_package(
                staging,
                request=request,
                p_discovery=p_discovery,
                q_discovery=q_discovery,
                public_executed=tuple(public_executed),
                analytical_executed=tuple(analytical_executed),
                p_rows=p_rows,
                q_rows=q_rows,
            )
            verification = verify_governed_export(staging)
            if verification.status != "VERIFIED" or verification.package_digest is None:
                raise GovernedExportError(
                    "staging package verification failed: "
                    f"{verification.status}: {verification.message}"
                )
            staging.replace(final_path)
            return BuildGovernedExportResult(
                export_ref=request.export_ref,
                package_path=final_path,
                package_digest=verification.package_digest,
                query_revision=manifest.query_revision,
                semantic_as_of=request.semantic_as_of,
                dataset_count=len(P_DATASETS) + len(Q_DATASETS),
                row_count=sum(item.row_count for item in manifest.dataset_entries),
            )
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            raise

    def reproduce(self, package_path: Path) -> ReproductionResult:
        verification = verify_governed_export(package_path)
        if verification.status != "VERIFIED" or verification.package_digest is None:
            return ReproductionResult(
                status="BUILD_FAILED",
                expected_digest="sha256:" + "0" * 64,
                actual_digest=None,
                query_revision=None,
                message="the source package is not verified",
            )
        manifest = GovernedExportManifest.model_validate_json(
            (package_path / "manifest.json").read_bytes()
        )
        with tempfile.TemporaryDirectory(
            prefix="finance-assurance-analytical-reproduce-",
            dir=package_path.parent,
        ) as directory:
            output = Path(directory) / manifest.export_ref
            request = BuildGovernedAnalyticalExport(
                request_contract_version="governed-analytical-export-request@v1",
                export_ref=manifest.export_ref,
                workspace_ref=manifest.workspace_ref,
                semantic_as_of=manifest.semantic_as_of,
                exported_at=manifest.exported_at,
                output_path=output,
                p_discovery_descriptor_ref=self._p_descriptor.discovery_descriptor_ref,
                q_discovery_descriptor_ref=self._q_descriptor.discovery_descriptor_ref,
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
            matches = rebuilt.package_digest == verification.package_digest
            return ReproductionResult(
                status="REPRODUCED" if matches else "DIGEST_MISMATCH",
                expected_digest=verification.package_digest,
                actual_digest=rebuilt.package_digest,
                query_revision=rebuilt.query_revision,
                message=(
                    "the analytical package reproduced byte-for-byte"
                    if matches
                    else "the reproduced analytical digest differs"
                ),
            )

    def _validate_request(self, request: BuildGovernedAnalyticalExport) -> None:
        if request.workspace_ref != self._p_descriptor.workspace_ref:
            raise GovernedExportError("workspace_ref does not match P-Q00")
        if request.workspace_ref != self._q_descriptor.workspace_ref:
            raise GovernedExportError("workspace_ref does not match Q-Q00")
        if request.p_discovery_descriptor_ref != self._p_descriptor.discovery_descriptor_ref:
            raise GovernedExportError("P discovery descriptor reference differs")
        if request.q_discovery_descriptor_ref != self._q_descriptor.discovery_descriptor_ref:
            raise GovernedExportError("Q discovery descriptor reference differs")
        if self._q_descriptor.p_discovery_descriptor_ref != request.p_discovery_descriptor_ref:
            raise GovernedExportError("Q-Q00 is not bound to P-Q00")
        if str(request.semantic_as_of) != str(self._p_descriptor.semantic_as_of):
            raise GovernedExportError("semantic_as_of does not match P-Q00")
        if str(request.semantic_as_of) != str(self._q_descriptor.semantic_as_of):
            raise GovernedExportError("semantic_as_of does not match Q-Q00")

    @staticmethod
    def _validate_public_membership(
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

    def _validate_analytical_subjects(
        self,
        executed: tuple[ExecutedPublicQuery, ...],
    ) -> None:
        """Reconcile Q-Q00 subjects to already-executed P/O evidence views."""

        by_query = {
            item.request.query_id: item
            for item in executed
            if item.request.query_id in {"O-Q10", "O-Q11"}
        }
        if set(by_query) != {"O-Q10", "O-Q11"}:
            raise GovernedExportError("required subject-reconciliation views are absent")
        trace = by_query["O-Q10"].envelope.data.model_dump(mode="json")
        correction = by_query["O-Q11"].envelope.data.model_dump(mode="json")
        trace_identities: dict[str, set[str]] = {}
        for node in trace["nodes"]:
            family = node.get("record_family")
            identity = node.get("record_identity")
            if isinstance(family, str) and isinstance(identity, str):
                trace_identities.setdefault(family, set()).add(identity)
        subjects = self._q_descriptor.subjects
        expected = {
            "c001_journal_id": (
                subjects.c001_journal_id,
                trace_identities.get("J-AR08", set()),
            ),
            "c001_business_event_ref": (
                subjects.c001_business_event_ref,
                trace_identities.get("J-AR03", set()),
            ),
            "c001_posting_rule_ref": (
                subjects.c001_posting_rule_ref,
                trace_identities.get("J-AR04", set()),
            ),
            "ct1_source_journal_id": (
                f"J-AR17:{subjects.ct1_source_journal_id}",
                {correction["source_projection_ref"]},
            ),
            "ct1_reversal_journal_id": (
                subjects.ct1_reversal_journal_id,
                {item["journal_ref"] for item in correction["journal_balance_results"]},
            ),
            "ct1_replacement_journal_id": (
                subjects.ct1_replacement_journal_id,
                {item["journal_ref"] for item in correction["journal_balance_results"]},
            ),
        }
        if any(value not in allowed for value, allowed in expected.values()):
            raise GovernedExportError("Q-Q00 subject set differs from P/O evidence")
        scenario_refs = {
            str(self._scenarios.c001.scenario_ref),
            str(self._scenarios.ct1.scenario_ref),
        }
        if {
            str(subjects.c001_scenario_ref),
            str(subjects.ct1_scenario_ref),
        } != scenario_refs:
            raise GovernedExportError("Q-Q00 scenario set differs from P-Q00")
        if (
            subjects.c001_reporting_period_id
            != self._scenarios.c001.reporting_period_id
            or subjects.correction_period_id
            != self._scenarios.c001.correction_period_id
        ):
            raise GovernedExportError("Q-Q00 period set differs from scenario outputs")

    def _write_package(
        self,
        root: Path,
        *,
        request: BuildGovernedAnalyticalExport,
        p_discovery: object,
        q_discovery: object,
        public_executed: tuple[ExecutedPublicQuery, ...],
        analytical_executed: tuple[ExecutedAnalyticalQuery, ...],
        p_rows: dict[str, list[dict[str, object]]],
        q_rows: dict[str, list[dict[str, object]]],
    ) -> GovernedExportManifest:
        entries: list[DatasetManifestEntry] = []
        registry_sets = (
            (P_REGISTRY_ID, P_STORAGE_KEY, P_DATASETS, p_rows),
            (Q_REGISTRY_ID, Q_STORAGE_KEY, Q_DATASETS, q_rows),
        )
        for registry_id, storage_key, definitions, rows in registry_sets:
            (root / "schemas" / storage_key).mkdir(parents=True)
            (root / "data" / storage_key).mkdir(parents=True)
            for definition in definitions:
                schema_relative = f"schemas/{storage_key}/{definition.dataset_id}.schema.json"
                data_relative = f"data/{storage_key}/{definition.dataset_id}.csv"
                schema_bytes = canonical_json_bytes(definition.schema_document())
                data_bytes = canonical_csv_bytes(
                    definition, rows[definition.dataset_id]  # type: ignore[arg-type]
                )
                (root / schema_relative).write_bytes(schema_bytes)
                (root / data_relative).write_bytes(data_bytes)
                if registry_id == P_REGISTRY_ID:
                    sources = {
                        source
                        for item in public_executed
                        if item.request.query_id in definition.source_query_ids
                        for source in item.envelope.source_refs
                    }
                else:
                    sources = {
                        source
                        for item in analytical_executed
                        if item.request.query_id in definition.source_query_ids
                        for source in item.view.source_refs
                    }
                entries.append(
                    DatasetManifestEntry(
                        dataset_id=definition.dataset_id,
                        dataset_version=1,
                        registry_id=registry_id,
                        export_steward=definition.export_steward,
                        semantic_owners=definition.semantic_owners,
                        relative_path=data_relative,
                        schema_path=schema_relative,
                        row_count=len(rows[definition.dataset_id]),
                        data_sha256=sha256_bytes(data_bytes),
                        schema_sha256=sha256_bytes(schema_bytes),
                        source_query_ids=definition.source_query_ids,
                        source_view_ids=definition.source_view_ids,
                        semantic_source_refs=tuple(sorted(sources)),
                    )
                )
        first = public_executed[0].envelope.data.model_dump(mode="json")
        manifest = GovernedExportManifest(
            contract_version=PACKAGE_CONTRACT,
            export_ref=request.export_ref,
            workspace_ref=request.workspace_ref,
            discovery_descriptor_ref=p_discovery.discovery_descriptor_ref,
            discovery_descriptor_hash=p_discovery.discovery_descriptor_hash,
            runtime_release=first["runtime_release"],
            query_revision=p_discovery.query_revision,
            semantic_as_of=p_discovery.semantic_as_of,
            exported_at=request.exported_at,
            compatibility_mode="EXACT_ORIGINAL",
            synthetic_data=True,
            synthetic_data_notice=first["synthetic_data_notice"],
            scenario_refs=tuple(sorted(item.scenario_ref for item in p_discovery.scenarios)),
            scenario_set_digest=p_discovery.scenario_set_digest,
            authoritative_inventory_digest=first["authoritative_inventory_digest"],
            projection_generation_ref=first["projection_generation_ref"],
            dataset_entries=tuple(entries),
            dataset_registries=(
                DatasetRegistryEntry(
                    registry_id=P_REGISTRY_ID,
                    registry_version=P_REGISTRY_VERSION,
                    storage_key=P_STORAGE_KEY,
                    dataset_ids=tuple(item.dataset_id for item in P_DATASETS),
                    registry_contract_hash=p_registry_contract_hash(),
                ),
                DatasetRegistryEntry(
                    registry_id=Q_REGISTRY_ID,
                    registry_version=Q_REGISTRY_VERSION,
                    storage_key=Q_STORAGE_KEY,
                    dataset_ids=tuple(item.dataset_id for item in Q_DATASETS),
                    registry_contract_hash=q_registry_contract_hash(),
                ),
            ),
            relationship_contract_version=2,
            producer_release=self._producer_release,
        )
        (root / "relationships.json").write_bytes(
            canonical_json_bytes([*P_RELATIONSHIPS, *Q_RELATIONSHIPS])
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
