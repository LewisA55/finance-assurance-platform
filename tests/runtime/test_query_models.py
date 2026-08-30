"""Phase 6 exact-read, current-projection, and traceability proofs."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from finance_assurance.runtime.application.admission import CandidateAdmissionService
from finance_assurance.runtime.application.contracts import (
    ModuleCommand,
    ModuleContractService,
)
from finance_assurance.runtime.application.models import (
    AccountingWorkflow,
    CandidateAssessmentCommand,
    ScriptedIdentityGenerator,
)
from finance_assurance.runtime.application.queries import (
    ReadModelError,
    RuntimeQueryService,
)
from finance_assurance.runtime.application.service import AccountingApplicationService
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256
from finance_assurance.runtime.contracts.evidence import ReportingContentRecord
from finance_assurance.runtime.contracts.module import (
    ContractPublication,
    ImportPublicationBasis,
    ValidatedModuleProduct,
)
from finance_assurance.runtime.contracts.objects import (
    BusinessEvent,
    PostingRule,
    ReportingVersion,
)
from finance_assurance.runtime.contracts.primitives import (
    AuthoritativeRef,
    ExactSemanticRef,
)
from finance_assurance.runtime.digests import value_digest
from finance_assurance.runtime.persistence.memory import InMemoryPersistenceBoundary
from finance_assurance.runtime.persistence.models import (
    ExactStoredRecord,
    ImportContext,
    PreScopeReportingImportBundle,
    QueryContext,
    RebuildContext,
)
from finance_assurance.runtime.persistence.sqlite import (
    AdmissionConflict,
    SqlitePersistenceBoundary,
)
from finance_assurance.runtime.persistence.state import InMemoryState
from finance_assurance.validation.h2 import run_h2
from finance_assurance.validation.proofs import resolve_reporting_content

from .support import accounting_workflow, admit_runtime, sealed_record

NOW = "2026-07-14T12:00:00Z"
ORIGINAL_PUBLISHED_AT = "2026-07-10T18:30:00Z"
IMPORTED_AT = "2026-07-11T09:00:00Z"
PREDECESSOR_AVAILABLE_FROM = "2026-07-11T12:00:00Z"
EVIDENCE = (
    AuthoritativeRef(
        record_family="J-AR12",
        record_identity="EVD-PHASE6",
        semantic_hash="sha256:" + "e" * 64,
    ),
)


def _exact_authority(
    record_family: str,
    record_identity: str,
    semantic_hash: str | None = None,
) -> ExactSemanticRef:
    return ExactSemanticRef(
        ref_kind="AUTHORITATIVE",
        authoritative_ref=AuthoritativeRef(
            record_family=record_family,
            record_identity=record_identity,
            semantic_hash=semantic_hash or "sha256:" + "a" * 64,
        ),
        publication_ref=None,
        module_product_ref=None,
    )


def _state_with_workflow_evidence(
    state: InMemoryState,
    workflow: AccountingWorkflow,
) -> InMemoryState:
    values = (
        *workflow.event_templates,
        *(
            (workflow.business_event,)
            if workflow.business_event is not None
            else ()
        ),
    )
    evidence = {
        str(ref.ref_id): ref
        for value in values
        for ref in getattr(value, "evidence_refs", ())
    }
    return replace(state, object_versions=(*state.object_versions, *evidence.values()))


def _state_with_workflow_evidence(
    state: InMemoryState,
    workflow: object,
) -> InMemoryState:
    values = (
        *workflow.event_templates,
        *(
            (workflow.business_event,)
            if workflow.business_event is not None
            else ()
        ),
    )
    evidence = {
        str(ref.ref_id): ref
        for value in values
        for ref in getattr(value, "evidence_refs", ())
    }
    return replace(state, object_versions=(*state.object_versions, *evidence.values()))


def _import_predecessor(
    boundary: SqlitePersistenceBoundary,
    *,
    available_from: str = PREDECESSOR_AVAILABLE_FROM,
    close_view_hash: str | None = None,
) -> None:
    v1_proof, _ = resolve_reporting_content(run_h2().index)
    v1_body = {
        "contract_version": 1,
        "reporting_version_id": "RV-2026-06",
        "period_id": "2026-06",
        "version": 1,
        "reporting_version_ref": "RV-2026-06@v1",
        "content_ref": str(v1_proof.content_ref),
        "content_hash": str(v1_proof.content_hash),
        "content_schema_version": v1_proof.content_schema_version,
        "publication_origin": "PRE_SCOPE_IMPORT",
        "published_at": ORIGINAL_PUBLISHED_AT,
    }
    g06_payload = {
        "reporting_version_ref": "RV-2026-06@v1",
        "period_id": "2026-06",
        "content_ref": str(v1_proof.content_ref),
        "content_hash": str(v1_proof.content_hash),
        "content_schema_version": v1_proof.content_schema_version,
        "publication_origin": "PRE_SCOPE_IMPORT",
        "published_at": ORIGINAL_PUBLISHED_AT,
        "import_attestation_ref": "J-AR11:IMPORT-C001-V1",
        "original_authority_ref": "AUTHORITY:CFO",
        "source_ref": "ARCHIVE:RV-2026-06@v1",
    }
    g06 = ContractPublication(
        publication_ref="PUB-G06-C001-V1",
        contract_id="G-06",
        g_contract_version="G-v0.2",
        body_contract_version=1,
        body_discriminator="G06ReportingVersion",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        publisher="Atlas",
        product_ref="RV-2026-06@v1",
        product_state_token=None,
        canonical_payload=g06_payload,
        payload_hash=canonical_sha256(g06_payload),
        upstream_publication_refs=(),
        upstream_authoritative_refs=(
            _exact_authority("J-AR10", "RV-2026-06@v1"),
        ),
        evidence_refs=EVIDENCE,
        available_from=available_from,
        publication_basis=ImportPublicationBasis(
            basis_type="PRE_SCOPE_IMPORT",
            import_attestation_ref="J-AR11:IMPORT-C001-V1",
        ),
    )
    candidate = canonical_bytes({"candidate_ref": "RV-2026-06@v1"})
    context = ImportContext(
        import_id="IMPORT-C001-V1",
        imported_reporting_version_ref="RV-2026-06@v1",
        sealed_candidate_contract_version="1",
        sealed_candidate_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        sealed_candidate_hash=canonical_sha256({"candidate_ref": "RV-2026-06@v1"}),
        semantic_as_of_time=IMPORTED_AT,
        importer_ref="REPORTING-SERVICE",
    )
    period = boundary.state.snapshot.period("2026-06")
    assert period is not None
    close_view_hash = close_view_hash or value_digest(period)
    core_record = sealed_record(
        "J-AR10", "RV-2026-06@v1", v1_body, owner="ATLAS"
    )
    attestation = {
        "import_id": "IMPORT-C001-V1",
        "imported_object_type": "reporting_version",
        "reporting_version_ref": "RV-2026-06@v1",
        "canonical_core_hash": core_record.semantic_hash,
        "content_ref": str(v1_proof.content_ref),
        "content_hash": str(v1_proof.content_hash),
        "content_schema_version": v1_proof.content_schema_version,
        "prerequisite_period_id": "2026-06",
        "prerequisite_close_event_id": "AE-C001-003",
        "prerequisite_close_view_hash": close_view_hash,
        "original_published_at": ORIGINAL_PUBLISHED_AT,
        "available_from": available_from,
        "original_authority_ref": "AUTHORITY:CFO",
        "source_ref": "ARCHIVE:RV-2026-06@v1",
        "imported_at": IMPORTED_AT,
        "imported_by": "REPORTING-SERVICE",
        "import_command_or_manifest_ref": "IMPORT-C001-V1",
        "evidence_refs": list(EVIDENCE),
    }
    unit = boundary.begin_pre_scope_reporting_import(context)
    unit.stage_bundle(
        PreScopeReportingImportBundle(
            declared_records=(
                core_record,
                sealed_record(
                    "J-AR11",
                    "IMPORT-C001-V1",
                    attestation,
                ),
                sealed_record(
                    "J-AR12",
                    str(v1_proof.content_ref),
                    v1_proof.model_dump(mode="json"),
                ),
                sealed_record(
                    "J-AR13",
                    "PUB-G06-C001-V1",
                    g06.model_dump(mode="json"),
                    owner="ATLAS",
                ),
            ),
            sealed_candidate_body=candidate,
            prerequisite_period_ref="2026-06",
            prerequisite_close_event_ref="AE-C001-003",
            prerequisite_close_view_hash=close_view_hash,
        )
    )
    unit.commit(unit.validate())


def _publish_business_event(
    boundary: SqlitePersistenceBoundary, event: BusinessEvent
) -> None:
    assessment = CandidateAdmissionService(boundary).assess(
        CandidateAssessmentCommand(
            command_contract_version=1,
            command_id="CMD-PHASE6-ASSESS-EVENT",
            actor_ref="ACTOR:HERMES",
            correlation_id=str(event.correlation_id),
            semantic_as_of_time=NOW,
            candidate_receipt_ref=f"J-AR01:{event.business_event_id}",
            admission_product_ref=f"ADM-{event.business_event_id}@v1",
            publication_ref="PUB-G02-C001-PHASE6",
            candidate_contract_version="1",
            candidate_type=str(event.event_type),
            canonical_candidate_body=event.model_dump(mode="json"),
            source_domain_ref=f"SOURCE:{event.source_system}",
            source_record_ref=str(event.payload.recognition_schedule_ref.object_id),
            received_at=str(event.recorded_at),
            assessed_at=NOW,
            evidence_refs=event.evidence_refs,
        )
    )
    publication = ContractPublication.command(
        publication_ref="PUB-G01-C001-PHASE6",
        contract_id="G-01",
        body_discriminator="business_event",
        publisher="SharedSubstrate",
        product_ref=str(event.business_event_id),
        payload=event.model_dump(mode="json"),
        command_owner="SharedSubstrate",
        command_id="CMD-PHASE6-PUBLISH-EVENT",
        evidence_refs=tuple(
            AuthoritativeRef(
                record_family="J-AR12",
                record_identity=str(item.ref_id),
                semantic_hash=value_digest(item),
            )
            for item in event.evidence_refs
        ),
        available_from=str(event.recorded_at),
        upstream_publication_refs=(assessment.publication.exact_ref(),),
        upstream_authoritative_refs=(
            _exact_authority(
                "J-AR01",
                str(assessment.receipt.candidate_receipt_ref),
                value_digest(assessment.receipt),
            ),
            _exact_authority(
                "J-AR03", str(event.business_event_id), value_digest(event)
            ),
        ),
    )
    ModuleContractService(boundary).execute(
        ModuleCommand(
            command_id="CMD-PHASE6-PUBLISH-EVENT",
            command_owner="SharedSubstrate",
            command_type="PublishAdmittedBusinessEvent",
            actor_ref="ACTOR:SUBSTRATE",
            correlation_id=str(event.correlation_id),
            semantic_as_of_time=NOW,
            authoritative_creations=(event,),
            publications=(publication,),
            consumed_publication_refs=(
                str(assessment.publication.publication_ref),
            ),
        )
    )


def test_query_session_is_revision_pinned_across_later_commit(tmp_path: Path) -> None:
    workflow, initial, _ = accounting_workflow("C001")
    assert workflow.business_event is not None
    boundary = admit_runtime(tmp_path / "phase6-pinned.sqlite3", initial)
    pinned = RuntimeQueryService(boundary, semantic_as_of_time=NOW)

    _publish_business_event(boundary, workflow.business_event)

    assert (
        pinned.get_business_event(str(workflow.business_event.business_event_id))
        is None
    )
    fresh = RuntimeQueryService(boundary, semantic_as_of_time=NOW)
    assert fresh.get_business_event(
        str(workflow.business_event.business_event_id)
    ) is not None
    boundary.close()


def test_in_memory_semantic_time_hides_exact_and_current_state() -> None:
    workflow, initial, _ = accounting_workflow("C001")
    boundary = InMemoryPersistenceBoundary(
        _state_with_workflow_evidence(initial, workflow)
    )
    AccountingApplicationService(
        boundary,
        ScriptedIdentityGenerator(
            {"constructor_command": ("CMD-MEMORY-CONSTRUCT-AUTO",)}
        ),
    ).execute_segment(workflow, start=0, stop=3)

    before = RuntimeQueryService(
        boundary, semantic_as_of_time="2026-07-10T18:00:00Z"
    )
    period = before.get_current_accounting_period("2026-06")
    assert period is not None and period.state_label == "SOFT_CLOSED"
    assert period.exactness_token.startswith("BASELINE:")
    assert before.get_exact("J-AR06", "AE-C001-003") is None

    at = RuntimeQueryService(
        boundary, semantic_as_of_time="2026-07-10T18:00:01Z"
    )
    period = at.get_current_accounting_period("2026-06")
    assert period is not None and period.state_label == "HARD_CLOSED"
    assert period.exactness_token == "AE-C001-003"
    exact = at.get_accounting_period_exact("2026-06", "AE-C001-003")
    assert exact is not None and exact.state_label == "HARD_CLOSED"
    assert at.get_exact("J-AR06", "AE-C001-003") is not None


def test_c001_exact_history_content_and_trace_survive_restart_and_rebuild(
    tmp_path: Path,
) -> None:
    workflow, initial, _ = accounting_workflow("C001")
    _, v2_proof = resolve_reporting_content(run_h2().index)
    v2_content = ReportingContentRecord.model_validate(
        v2_proof.model_dump(mode="json")
    )
    final_event_id = str(workflow.event_templates[-1].event_id)
    workflow = replace(
        workflow,
        creations=tuple(
            replace(bundle, values=(*bundle.values, v2_content))
            if bundle.template_event_id == final_event_id
            else bundle
            for bundle in workflow.creations
        ),
    )
    rule = next(
        item for item in initial.object_versions if isinstance(item, PostingRule)
    )
    database = tmp_path / "phase6-c001.sqlite3"
    boundary = admit_runtime(
        database,
        initial,
        additional_records=(
            sealed_record(
                "J-AR04",
                str(rule.posting_rule_ref),
                rule.model_dump(mode="json"),
                owner="ATLAS",
            ),
            sealed_record(
                "J-AR04",
                "DOWNSTREAM-CONSUMER",
                {
                    "consumer_ref": "DOWNSTREAM-CONSUMER",
                    "reporting_version_ref": "RV-2026-06@v2",
                },
                owner="ATLAS",
            ),
        ),
    )
    assert workflow.business_event is not None
    _publish_business_event(boundary, workflow.business_event)
    service = AccountingApplicationService(
        boundary,
        ScriptedIdentityGenerator(
            {
                "constructor_command": (
                    "CMD-PHASE6-CONSTRUCT-AUTO",
                    "CMD-PHASE6-CONSTRUCT-RESTATEMENT",
                )
            }
        ),
    )
    assert RuntimeQueryService(
        boundary, semantic_as_of_time=NOW
    ).get_reporting_version("RV-2026-06@v1") is None
    with pytest.raises(AdmissionConflict, match="hard-close authority"):
        _import_predecessor(boundary)
    assert RuntimeQueryService(
        boundary, semantic_as_of_time=NOW
    ).get_reporting_version("RV-2026-06@v1") is None

    service.execute_segment(workflow, start=0, stop=3)

    before_close = RuntimeQueryService(
        boundary, semantic_as_of_time="2026-07-10T18:00:00Z"
    )
    before_period = before_close.get_current_accounting_period("2026-06")
    assert before_period is not None and before_period.state_label == "SOFT_CLOSED"
    assert before_close.get_exact("J-AR06", "AE-C001-003") is None
    at_close = RuntimeQueryService(
        boundary, semantic_as_of_time="2026-07-10T18:00:01Z"
    )
    closed_period = at_close.get_current_accounting_period("2026-06")
    assert closed_period is not None and closed_period.state_label == "HARD_CLOSED"
    assert closed_period.exactness_token == "AE-C001-003"
    exact_period = at_close.get_accounting_period_exact(
        "2026-06", "AE-C001-003"
    )
    assert exact_period is not None
    assert exact_period.lifecycle_evidence[-1].record.record_identity == "AE-C001-003"
    assert at_close.get_exact("J-AR06", "AE-C001-003") is not None

    with pytest.raises(AdmissionConflict, match="hard-close authority"):
        _import_predecessor(boundary, close_view_hash="sha256:" + "0" * 64)
    with pytest.raises(AdmissionConflict, match="availability precedes"):
        _import_predecessor(boundary, available_from="2026-07-11T08:59:59Z")
    assert RuntimeQueryService(
        boundary, semantic_as_of_time=NOW
    ).get_reporting_version("RV-2026-06@v1") is None
    _import_predecessor(boundary)
    assert RuntimeQueryService(
        boundary, semantic_as_of_time="2026-07-11T11:59:59Z"
    ).get_reporting_version("RV-2026-06@v1") is None
    assert RuntimeQueryService(
        boundary, semantic_as_of_time=PREDECESSOR_AVAILABLE_FROM
    ).get_reporting_version("RV-2026-06@v1") is not None

    service.execute_segment(workflow, start=3, stop=11)

    query = RuntimeQueryService(boundary, semantic_as_of_time=NOW)
    history = query.get_reporting_history("2026-06")
    assert [item.record.record_identity for item in history.versions] == [
        "RV-2026-06@v1",
        "RV-2026-06@v2",
    ]
    assert query.resolve_reporting_content(
        "RV-2026-06@v1"
    ).verification_status == "CONTENT_BYTES_VERIFIED"
    assert query.resolve_reporting_content(
        "RV-2026-06@v2"
    ).verification_status == "CONTENT_BYTES_VERIFIED"
    current_case = query.get_current_restatement_case("RC-001")
    assert current_case is not None
    assert current_case.label == "CURRENT_REBUILDABLE"
    assert current_case.state_label == "PUBLISHED"
    assert current_case.exactness_token == "AE-C001-011"
    proposed_case = query.get_restatement_case_exact("RC-001", "AE-C001-004")
    published_case = query.get_restatement_case_exact("RC-001", "AE-C001-011")
    assert proposed_case is not None and proposed_case.state_label == "PROPOSED"
    assert published_case is not None and published_case.state_label == "PUBLISHED"
    assert proposed_case.artifact_f_view["linked_journal_ids"] == []
    assert published_case.artifact_f_view["published_version_refs"] == [
        "RV-2026-06@v2"
    ]
    submitted = query.get_journal_proposal_exact("P-551@v1", "AE-C001-001")
    deferred = query.get_journal_proposal_exact("P-551@v1", "AE-C001-002")
    assert submitted is not None and submitted.state_label == "SUBMITTED"
    assert deferred is not None and deferred.state_label == "DEFERRED"
    assert submitted.artifact_f_view != deferred.artifact_f_view
    trace = query.trace_reporting_value(
        "RV-2026-06@v2", "subscription_revenue_minor"
    )
    assert trace.statement_value_minor == 1000000
    assert trace.currency == "GBP"
    assert {
        "reporting_version",
        "journal",
        "proposal",
        "posting_rule",
        "business_event",
        "evidence",
        "source_reference",
    }.issubset({item.role for item in trace.nodes})
    assert all(
        item.record_identity != "DOWNSTREAM-CONSUMER" for item in trace.nodes
    )
    directed = {
        node.node_ref: {
            edge.target_ref for edge in trace.edges if edge.source_ref == node.node_ref
        }
        for node in trace.nodes
    }

    def reaches(start: str, target: str) -> bool:
        pending = [start]
        visited = {start}
        while pending:
            current = pending.pop(0)
            if current == target:
                return True
            for neighbor in directed.get(current, set()) - visited:
                visited.add(neighbor)
                pending.append(neighbor)
        return False

    root = "J-AR10:RV-2026-06@v2"
    assert reaches(root, "J-AR08:J-560")
    assert reaches(root, "J-AR05:P-551@v2")
    assert reaches(root, "J-AR05:P-551@v1")
    assert reaches(root, "J-AR04:PR-O2C-RECOG@v1")
    assert reaches(root, "J-AR03:BE-C001-RECOG-202606")
    assert reaches(root, "EXTERNAL:source_reference:REVENUE_SUBLEDGER")
    assert not reaches("J-AR03:BE-C001-RECOG-202606", root)
    before = trace.semantic_digest

    boundary.delete_projection_checkpoint()
    rebuild = boundary.open_rebuild(
        RebuildContext(
            semantic_as_of_time=NOW,
            requested_projection_families=(
                "J-P02",
                "J-P04",
                "J-P06",
                "J-P08",
                "J-P11",
            ),
        )
    )
    generation = rebuild.begin_generation()
    rebuild.promote(rebuild.validate(rebuild.rebuild(generation)))
    assert (
        RuntimeQueryService(boundary, semantic_as_of_time=NOW)
        .trace_reporting_value("RV-2026-06@v2", "subscription_revenue_minor")
        .semantic_digest
        == before
    )
    boundary.close()

    restarted = SqlitePersistenceBoundary(database)
    restarted_query = RuntimeQueryService(restarted, semantic_as_of_time=NOW)
    assert restarted_query.get_reporting_version("RV-2026-06@v1") is not None
    assert restarted_query.get_reporting_version("RV-2026-06@v2") is not None
    assert (
        restarted_query.trace_reporting_value(
            "RV-2026-06@v2", "subscription_revenue_minor"
        ).semantic_digest
        == before
    )
    restarted.close()


@pytest.mark.parametrize(
    ("family", "proposal_ref", "journal_id"),
    [
        ("C001", "P-551@v2", "J-560"),
        ("CT1", "P-REV-010@v1", "J-011"),
    ],
)
def test_c001_and_ct1_exact_and_current_reads_remain_distinct(
    family: str,
    proposal_ref: str,
    journal_id: str,
) -> None:
    workflow, initial, _ = accounting_workflow(family)
    boundary = InMemoryPersistenceBoundary(
        _state_with_workflow_evidence(initial, workflow)
    )
    AccountingApplicationService(
        boundary,
        ScriptedIdentityGenerator(
            {
                "constructor_command": (
                    f"CMD-{family}-QUERY-CONSTRUCT-1",
                    f"CMD-{family}-QUERY-CONSTRUCT-2",
                )
            }
        ),
    ).execute_workflow(workflow)
    query = RuntimeQueryService(
        boundary, semantic_as_of_time=NOW
    )

    posting_event = next(
        item
        for item in workflow.event_templates
        if item.event_type == "journal.posted"
        and str(item.subject_ref.object_ref) == proposal_ref
    )
    state_token = str(posting_event.event_id)
    proposal = query.get_journal_proposal_exact(proposal_ref, state_token)
    assert proposal is not None
    assert proposal.treatment.record.record_identity == proposal_ref
    assert proposal.state_label == "POSTED"
    assert proposal.lifecycle_evidence[-1].record.record_identity == state_token
    current = query.get_current_journal_proposal(proposal_ref)
    assert current is not None and current.label == "CURRENT_REBUILDABLE"
    assert current.state_label == "POSTED"
    assert current.exactness_token == state_token
    if family == "C001":
        exact_period = query.get_accounting_period_exact(
            "2026-06", "AE-C001-003"
        )
        exact_case = query.get_restatement_case_exact("RC-001", "AE-C001-009")
        assert exact_period is not None and exact_period.state_label == "HARD_CLOSED"
        assert exact_case is not None
        assert exact_case.state_label == "ADJUSTMENTS_READY"
        assert exact_case.artifact_f_view["manifest_hash"] is not None
    journal = query.get_journal(journal_id)
    assert journal is not None
    assert [line.body["line_no"] for line in journal.ordered_lines] == [1, 2]  # type: ignore[index]


def test_exact_and_current_lifecycle_queries_have_adapter_parity(
    tmp_path: Path,
) -> None:
    workflow, initial, _ = accounting_workflow("C001")
    memory = InMemoryPersistenceBoundary(
        _state_with_workflow_evidence(initial, workflow)
    )
    sqlite = admit_runtime(tmp_path / "lifecycle-parity.sqlite3", initial)
    for boundary in (memory, sqlite):
        AccountingApplicationService(
            boundary,
            ScriptedIdentityGenerator(
                {
                    "constructor_command": (
                        "CMD-PARITY-CONSTRUCT-1",
                        "CMD-PARITY-CONSTRUCT-2",
                    )
                }
            ),
        ).execute_workflow(workflow)

    def lifecycle_digest(boundary: object) -> str:
        query = RuntimeQueryService(
            boundary,  # type: ignore[arg-type]
            semantic_as_of_time=NOW,
        )
        period = query.get_accounting_period_exact("2026-06", "AE-C001-003")
        current_period = query.get_current_accounting_period("2026-06")
        proposal = query.get_journal_proposal_exact(
            "P-551@v1", "AE-C001-001"
        )
        current_proposal = query.get_current_journal_proposal("P-551@v1")
        case = query.get_restatement_case_exact("RC-001", "AE-C001-009")
        current_case = query.get_current_restatement_case("RC-001")
        assert all(
            item is not None
            for item in (
                period,
                current_period,
                proposal,
                current_proposal,
                case,
                current_case,
            )
        )
        assert period is not None and proposal is not None and case is not None
        assert current_period is not None
        assert current_proposal is not None
        assert current_case is not None
        return value_digest(
            (
                period.state_token,
                period.state_label,
                period.artifact_f_view,
                tuple(
                    item.record.record_identity
                    for item in period.lifecycle_evidence
                ),
                current_period.exactness_token,
                current_period.state_label,
                current_period.projection_hash,
                proposal.state_token,
                proposal.state_label,
                proposal.artifact_f_view,
                tuple(
                    item.record.record_identity
                    for item in proposal.lifecycle_evidence
                ),
                current_proposal.exactness_token,
                current_proposal.state_label,
                current_proposal.projection_hash,
                case.state_token,
                case.state_label,
                case.artifact_f_view,
                tuple(
                    item.record.record_identity for item in case.lifecycle_evidence
                ),
                current_case.exactness_token,
                current_case.state_label,
                current_case.projection_hash,
            )
        )

    assert lifecycle_digest(memory) == lifecycle_digest(sqlite)
    sqlite.close()


def _module_product(
    *, discriminator: str, owner: str, body: dict[str, object]
) -> ValidatedModuleProduct:
    return ValidatedModuleProduct.command(
        product_discriminator=discriminator,
        owner=owner,
        body=body,
        command_id=f"CMD:{body['product_ref']}",
        evidence_refs=EVIDENCE,
        available_from=NOW,
    )


def test_controlled_planning_query_never_infers_readiness_from_predecessor() -> None:
    report = next(
        item
        for item in accounting_workflow("C001")[2].reporting_version_store
        if isinstance(item, ReportingVersion)
    )
    v1_readiness_body = {
        "product_ref": "READY-C001-V1@v1",
        "reporting_version_ref": "RV-2026-06@v1",
        "reporting_publication_ref": "PUB-G06-C001-V1",
        "period_id": "2026-06",
        "scope_ref": "NEXUS-GROUP",
        "purpose_ref": "HIRING-FORECAST",
        "status": "APPROVED",
        "basis_refs": [
            _exact_authority("J-AR13", "PUB-G06-C001-V1").model_dump(mode="json")
        ],
        "limitation_codes": [],
        "assessed_by": "ACTOR:CFO",
        "assessed_at": NOW,
    }
    planning_body = {
        "product_ref": "PLAN-C001@v1",
        "reporting_version_ref": "RV-2026-06@v2",
        "reporting_publication_ref": "PUB-G06-C001-V2",
        "readiness_ref": "READY-C001-V2@v1",
        "readiness_publication_ref": "PUB-G10-C001-V2",
        "purpose_ref": "HIRING-FORECAST",
        "period_id": "2026-06",
        "scope_ref": "NEXUS-GROUP",
        "assumption_refs": [],
        "exclusion_refs": [],
        "frozen_at": NOW,
    }
    predecessor = _module_product(
        discriminator="aegis.readiness_assessment",
        owner="Aegis",
        body=v1_readiness_body,
    )
    planning = _module_product(
        discriminator="pythia.planning_input_snapshot",
        owner="Pythia",
        body=planning_body,
    )
    incomplete = InMemoryState(
        object_versions=(predecessor, planning),
        reporting_version_store=(report,),
    )
    query = RuntimeQueryService(
        InMemoryPersistenceBoundary(incomplete),
        semantic_as_of_time=NOW,
    )
    with pytest.raises(ReadModelError, match="exact approved readiness"):
        query.get_controlled_planning_input("PLAN-C001@v1")

    exact = _module_product(
        discriminator="aegis.readiness_assessment",
        owner="Aegis",
        body={
            **v1_readiness_body,
            "product_ref": "READY-C001-V2@v1",
            "reporting_version_ref": "RV-2026-06@v2",
            "reporting_publication_ref": "PUB-G06-C001-V2",
        },
    )
    complete = replace(
        incomplete,
        object_versions=(predecessor, exact, planning),
    )
    controlled = RuntimeQueryService(
        InMemoryPersistenceBoundary(complete), semantic_as_of_time=NOW
    ).get_controlled_planning_input("PLAN-C001@v1")
    assert controlled.readiness.product.record.record_identity == (
        "READY-C001-V2@v1"
    )
    assert controlled.reporting_version.record.record_identity == "RV-2026-06@v2"


def _exact_record(
    family: str,
    identity: str,
    body: dict[str, object],
) -> ExactStoredRecord:
    return ExactStoredRecord(
        record_family=family,
        record_identity=identity,
        semantic_hash=canonical_sha256(body),
        canonical_payload=canonical_bytes(body),
        available_from=NOW,
    )


class _StaticQuerySession:
    def __init__(self, records: tuple[ExactStoredRecord, ...]) -> None:
        self.revision = 1
        self._records = records

    def state(self) -> InMemoryState:
        return InMemoryState()

    def command_result(self, command_id: str) -> None:
        del command_id
        return None

    def authoritative_record(
        self,
        record_family: str,
        record_identity: str,
    ) -> ExactStoredRecord | None:
        return next(
            (
                item
                for item in self.authoritative_records(record_family)
                if item.record_identity == record_identity
            ),
            None,
        )

    def authoritative_records(
        self,
        record_family: str | None = None,
    ) -> tuple[ExactStoredRecord, ...]:
        if record_family is None:
            return self._records
        return tuple(
            item for item in self._records if item.record_family == record_family
        )


class _StaticBoundary:
    def __init__(self, records: tuple[ExactStoredRecord, ...]) -> None:
        self._query = _StaticQuerySession(records)

    def open_query(self, context: QueryContext) -> _StaticQuerySession:
        del context
        return self._query


@pytest.mark.parametrize(
    ("defect", "message"),
    [
        ("ambiguous", "ambiguous authoritative trace binding"),
        ("broken", "broken internal trace binding"),
    ],
)
def test_directed_trace_fails_instead_of_guessing_internal_bindings(
    defect: str,
    message: str,
) -> None:
    content_body = {"subscription_revenue_minor": 100, "currency": "GBP"}
    content_ref = "reporting://strict/v1"
    records = [
        _exact_record(
            "J-AR10",
            "RV-STRICT@v1",
            {
                "reporting_version_ref": "RV-STRICT@v1",
                "content_ref": content_ref,
                "content_hash": canonical_sha256(content_body),
                "published_by_event_id": "AE-STRICT-1",
            },
        ),
        _exact_record(
            "J-AR12",
            content_ref,
            {"content_ref": content_ref, "canonical_body": content_body},
        ),
        _exact_record(
            "J-AR06",
            "AE-STRICT-1",
            {
                "event_id": "AE-STRICT-1",
                "subject_ref": {
                    "object_type": "journal_proposal",
                    "object_ref": "P-STRICT@v1",
                },
            },
        ),
    ]
    if defect == "ambiguous":
        records.extend(
            (
                _exact_record(
                    "J-AR05",
                    "P-STRICT@v1",
                    {
                        "proposal_ref": "P-STRICT@v1",
                        "origin_basis": {"posting_rule_ref": "RULE-ALIAS@v1"},
                    },
                ),
                _exact_record(
                    "J-AR04",
                    "RULE-A@v1",
                    {"posting_rule_ref": "RULE-ALIAS@v1"},
                ),
                _exact_record(
                    "J-AR04",
                    "RULE-B@v1",
                    {"posting_rule_ref": "RULE-ALIAS@v1"},
                ),
            )
        )

    query = RuntimeQueryService(
        _StaticBoundary(tuple(records)),  # type: ignore[arg-type]
        semantic_as_of_time=NOW,
    )
    with pytest.raises(ReadModelError, match=message):
        query.trace_reporting_value(
            "RV-STRICT@v1", "subscription_revenue_minor"
        )
