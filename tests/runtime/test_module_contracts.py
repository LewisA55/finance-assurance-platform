"""Phase 5 executed module-contract acceptance proofs."""

from __future__ import annotations

from pathlib import Path

import pytest

from finance_assurance.runtime.application.admission import CandidateAdmissionService
from finance_assurance.runtime.application.contracts import (
    InMemoryObservationSink,
    ModuleBoundaryError,
    ModuleCommand,
    ModuleContractService,
)
from finance_assurance.runtime.application.models import CandidateAssessmentCommand
from finance_assurance.runtime.application.queries import RuntimeQueryService
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256
from finance_assurance.runtime.contracts.module import (
    ContractPublication,
    ImportPublicationBasis,
    ReferencedJournalPublicationBasis,
    ValidatedModuleProduct,
)
from finance_assurance.runtime.contracts.objects import BusinessEvent
from finance_assurance.runtime.contracts.primitives import (
    AuthoritativeRef,
    EvidenceRef,
    ExactSemanticRef,
)
from finance_assurance.runtime.digests import value_digest
from finance_assurance.runtime.persistence.codec import durable_hash, encode_durable
from finance_assurance.runtime.persistence.memory import (
    InMemoryPersistenceBoundary,
    InvariantFailure,
)
from finance_assurance.runtime.persistence.models import (
    AdmissionBundle,
    BaselineContext,
    CommandContext,
    CommandDisposition,
    CommandResult,
    ModuleCommandOutcome,
    ProjectionReplacement,
    RebuildContext,
    SealedAdmissionRecord,
    StagedWriteSet,
)
from finance_assurance.runtime.persistence.sqlite import SqlitePersistenceBoundary
from finance_assurance.runtime.persistence.state import InMemoryState
from finance_assurance.runtime.planner import StateSnapshot
from finance_assurance.runtime.rejections import Rejection, RejectionCode
from finance_assurance.validation.h2 import run_h2

NOW = "2026-07-14T12:00:00Z"
EVIDENCE_BODY = EvidenceRef(
    ref_id="EVD-PHASE5",
    description="Phase 5 declared-only evidence",
    content_hash="sha256:" + "e" * 64,
)
EVIDENCE = (
    AuthoritativeRef(
        record_family="J-AR12",
        record_identity="EVD-PHASE5",
        semantic_hash=value_digest(EVIDENCE_BODY),
    ),
)


def _memory_boundary(
    *evidence: EvidenceRef,
    objects: tuple[object, ...] = (),
) -> InMemoryPersistenceBoundary:
    declared = {
        str(item.ref_id): item for item in (*_business_event().evidence_refs, *evidence)
    }
    return InMemoryPersistenceBoundary(
        InMemoryState(
            object_versions=(*declared.values(), *objects)  # type: ignore[arg-type]
        )
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


def _exact_publication(publication: ContractPublication) -> ExactSemanticRef:
    return ExactSemanticRef(
        ref_kind="PUBLICATION",
        authoritative_ref=None,
        publication_ref=publication.exact_ref(),
        module_product_ref=None,
    )


def _exact_publications(
    boundary: InMemoryPersistenceBoundary | SqlitePersistenceBoundary,
    refs: tuple[str, ...],
) -> tuple[object, ...]:
    publications = {
        str(item.publication_ref): item
        for item in boundary.state.object_versions
        if isinstance(item, ContractPublication)
    }
    return tuple(publications[item].exact_ref() for item in refs)


def _sqlite_boundary(path: Path) -> SqlitePersistenceBoundary:
    boundary = SqlitePersistenceBoundary(path)
    snapshot_payload = encode_durable(StateSnapshot())
    projection_ref = "BASELINE-PHASE5:J-P04"
    projection_hash = durable_hash(snapshot_payload)
    manifest = {
        "contract_version": 1,
        "manifest_ref": "BASELINE-PHASE5",
        "projection_ref": projection_ref,
        "projection_hash": projection_hash,
        "predecessor_event_refs": [],
    }
    context = BaselineContext(
        baseline_manifest_ref="BASELINE-PHASE5",
        baseline_manifest_contract_version="1",
        baseline_manifest_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        baseline_manifest_hash=canonical_sha256(manifest),
        semantic_as_of_time=NOW,
        admitting_actor_ref="PHASE5-TEST",
    )
    unit = boundary.begin_runtime_baseline_admission(context)
    unit.stage_bundle(
        AdmissionBundle(
            declared_records=(
                SealedAdmissionRecord(
                    record_family="J-AR04",
                    record_identity="BASELINE-PHASE5",
                    semantic_owner="PLATFORM",
                    contract_version="1",
                    canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
                    semantic_hash=context.baseline_manifest_hash,
                    canonical_payload=canonical_bytes(manifest),
                ),
                *tuple(
                    SealedAdmissionRecord(
                        record_family="J-AR12",
                        record_identity=str(item.ref_id),
                        semantic_owner="PLATFORM",
                        contract_version="1",
                        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
                        semantic_hash=value_digest(item),
                        canonical_payload=canonical_bytes(item.model_dump(mode="json")),
                    )
                    for item in {
                        str(value.ref_id): value
                        for value in (
                            EVIDENCE_BODY,
                            *_business_event().evidence_refs,
                        )
                    }.values()
                ),
            ),
            projection_replacements=(
                ProjectionReplacement(
                    projection_family="J-P04",
                    projection_token=projection_ref,
                    source_hash=projection_hash,
                    canonical_payload=snapshot_payload,
                ),
            ),
        )
    )
    unit.commit(unit.validate())
    return boundary


def _business_event() -> BusinessEvent:
    record = next(
        item
        for item in run_h2().index.objects
        if isinstance(item.value, BusinessEvent)
    )
    return record.value


def _assessment_command(
    event: BusinessEvent,
    *,
    suffix: str,
    candidate_type: str | None = None,
    canonical_body: dict[str, object] | None = None,
) -> CandidateAssessmentCommand:
    return CandidateAssessmentCommand(
        command_contract_version=1,
        command_id=f"CMD-HERMES-ASSESS-{suffix}",
        actor_ref="ACTOR:HERMES",
        correlation_id=str(event.correlation_id),
        semantic_as_of_time=NOW,
        candidate_receipt_ref=f"J-AR01:CAND-{suffix}",
        admission_product_ref=f"ADM-{suffix}@v1",
        publication_ref=f"PUB-G02-{suffix}",
        candidate_contract_version="1",
        candidate_type=candidate_type or str(event.event_type),
        canonical_candidate_body=(
            canonical_body or event.model_dump(mode="json")
        ),
        source_domain_ref="SOURCE:REVENUE",
        source_record_ref=f"SOURCE-RECORD:{suffix}",
        received_at=NOW,
        assessed_at=NOW,
        evidence_refs=event.evidence_refs,
    )


def _admission_body() -> dict[str, object]:
    return {
        "product_ref": "ADM-C001@v1",
        "candidate_receipt_ref": "J-AR01:CAND-C001",
        "candidate_type": "accounting.recognition.due",
        "candidate_payload_hash": "sha256:" + "1" * 64,
        "source_domain_ref": "SOURCE:REVENUE",
        "source_record_ref": "SCHEDULE:C001",
        "outcome": "ACCEPTED",
        "eligible_for_g01": True,
        "assessed_at": NOW,
    }


def _admit_event(
    service: ModuleContractService,
) -> tuple[ContractPublication, ContractPublication]:
    event = _business_event()
    assessment = CandidateAdmissionService(contracts=service).assess(
        CandidateAssessmentCommand(
            command_contract_version=1,
            command_id="CMD-HERMES-ADMIT",
            actor_ref="ACTOR:HERMES",
            correlation_id="C-001",
            semantic_as_of_time=NOW,
            candidate_receipt_ref="J-AR01:CAND-C001",
            admission_product_ref="ADM-C001@v1",
            publication_ref="PUB-G02-C001",
            candidate_contract_version="1",
            candidate_type=str(event.event_type),
            canonical_candidate_body=event.model_dump(mode="json"),
            source_domain_ref="SOURCE:REVENUE",
            source_record_ref="SCHEDULE:C001",
            received_at=NOW,
            assessed_at=NOW,
            evidence_refs=event.evidence_refs,
        )
    )
    g02 = assessment.publication
    if not assessment.execution.replayed:
        assert tuple(
            item.record_family
            for item in assessment.execution.receipt.committed_publication_refs
        ) == ("J-AR13",)

    g01 = ContractPublication.command(
        publication_ref="PUB-G01-C001",
        contract_id="G-01",
        body_discriminator="business_event",
        publisher="SharedSubstrate",
        product_ref=str(event.business_event_id),
        payload=event.model_dump(mode="json"),
        command_owner="SharedSubstrate",
        command_id="CMD-SUBSTRATE-PUBLISH",
        evidence_refs=EVIDENCE,
        available_from=NOW,
        upstream_publication_refs=(g02.exact_ref(),),
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
    second = service.execute(
        ModuleCommand(
            command_id="CMD-SUBSTRATE-PUBLISH",
            command_owner="SharedSubstrate",
            command_type="PublishAdmittedBusinessEvent",
            actor_ref="ACTOR:SUBSTRATE",
            correlation_id="C-001",
            semantic_as_of_time=NOW,
            authoritative_creations=(event,),
            publications=(g01,),
            consumed_publication_refs=(str(g02.publication_ref),),
        )
    )
    families = {item.record_family for item in second.receipt.committed_authoritative_refs}
    if not second.replayed:
        assert "J-AR03" in families
    return g02, g01


def test_i_c01_candidate_custody_is_mandatory_and_outcome_is_derived() -> None:
    event = _business_event()
    boundary = _memory_boundary(*event.evidence_refs)
    service = CandidateAdmissionService(boundary)

    accepted = service.assess(_assessment_command(event, suffix="ACCEPTED"))
    invalid_body = event.model_dump(mode="json")
    invalid_body.pop("payload")
    rejected = service.assess(
        _assessment_command(
            event,
            suffix="REJECTED",
            canonical_body=invalid_body,
        )
    )
    unsupported = service.assess(
        _assessment_command(
            event,
            suffix="UNSUPPORTED",
            candidate_type="workforce.hiring.deferred",
            canonical_body={
                "candidate_type": "workforce.hiring.deferred",
                "position_ref": "POSITION:14",
            },
        )
    )

    assert accepted.outcome == "ACCEPTED"
    assert rejected.outcome == "REJECTED"
    assert unsupported.outcome == "UNSUPPORTED"
    assert accepted.admission_result.canonical_body["eligible_for_g01"] is True
    assert rejected.admission_result.canonical_body["reason_code"] == (
        "INVALID_CANDIDATE_CONTRACT"
    )
    assert unsupported.admission_result.canonical_body["reason_code"] == (
        "UNSUPPORTED_CANDIDATE_TYPE"
    )
    families = {
        item.record_family
        for result in (accepted, rejected, unsupported)
        for item in result.execution.receipt.committed_authoritative_refs
    }
    assert {"J-AR01", "J-AR02", "J-AR14"}.issubset(families)
    assert not any(
        isinstance(item, BusinessEvent) for item in boundary.state.object_versions
    )


def test_module_boundary_rejects_unavailable_evidence_declaration() -> None:
    event = _business_event()
    boundary = InMemoryPersistenceBoundary()

    with pytest.raises(ModuleBoundaryError, match="evidence reference is unavailable"):
        CandidateAdmissionService(boundary).assess(
            _assessment_command(event, suffix="MISSING-EVIDENCE")
        )

    assert boundary.state == InMemoryState()


def test_i_c01_cannot_commit_without_candidate_custody() -> None:
    boundary = _memory_boundary(EVIDENCE_BODY)
    service = ModuleContractService(boundary)
    body = _admission_body()
    product = ValidatedModuleProduct.command(
        product_discriminator="hermes.business_event_admission_result",
        owner="Hermes",
        body=body,
        command_id="CMD-HERMES-NO-CUSTODY",
        evidence_refs=EVIDENCE,
        available_from=NOW,
    )
    publication = ContractPublication.command(
        publication_ref="PUB-G02-NO-CUSTODY",
        contract_id="G-02",
        body_discriminator="G02AdmissionResult",
        publisher="Hermes",
        product_ref=product.product_ref,
        payload=product.canonical_body,
        command_owner="Hermes",
        command_id="CMD-HERMES-NO-CUSTODY",
        evidence_refs=EVIDENCE,
        available_from=NOW,
    )
    before = boundary.state.full_digest

    with pytest.raises(ModuleBoundaryError, match="exactly J-AR01"):
        service.execute(
            ModuleCommand(
                command_id="CMD-HERMES-NO-CUSTODY",
                command_owner="Hermes",
                command_type="AssessBusinessEventCandidate",
                actor_ref="ACTOR:HERMES",
                correlation_id="C-001",
                semantic_as_of_time=NOW,
                    products=(product,),
                publications=(publication,),
            )
        )

    assert boundary.state.full_digest == before


@pytest.mark.parametrize(
    ("outcome", "candidate_ref"),
    (("APPROVED", None), ("REJECTED", "CANDIDATE:HIRING@v1")),
)
def test_operational_approval_variant_is_bound_to_outcome(
    outcome: str,
    candidate_ref: str | None,
) -> None:
    body: dict[str, object] = {
        "product_ref": "APPROVAL:HIRING@v1",
        "created_at": NOW,
        "decision_ref": "DECISION:HIRING@v1",
        "decision_publication_ref": "PUB-G12-HIRING",
        "outcome": outcome,
        "decided_by": "ACTOR:OPERATIONS",
        "decided_at": NOW,
        "approval_policy_ref": "J-AR04:POLICY-HIRING@v1",
    }
    if candidate_ref is not None:
        body["candidate_ref"] = candidate_ref

    with pytest.raises(ValueError, match="candidate binding"):
        ValidatedModuleProduct.command(
            product_discriminator="source.operational_decision_approval",
            owner="SourceDomain",
            body=body,
            command_id="CMD-SOURCE-APPROVAL",
            evidence_refs=EVIDENCE,
            available_from=NOW,
        )


def test_argus_verification_outcome_is_derived_from_every_check() -> None:
    body = {
        "product_ref": "VERIFY:CT1@v1",
        "created_at": NOW,
        "verification_type": "CASH_APPLICATION_CORRECTION",
        "source_journal_ref": "J-AR17:J-010",
        "source_hash": "sha256:" + "1" * 64,
        "reversal_journal_ref": "J-AR08:J-011",
        "replacement_journal_ref": "J-AR08:J-012",
        "check_results": {
            "reversal_source_bound": True,
            "reversal_equal_and_opposite": False,
            "replacement_customer_correct": True,
            "journals_balanced": True,
            "control_account_net_zero": True,
        },
        "outcome": "PASSED",
    }

    with pytest.raises(ValueError, match="verification outcome"):
        ValidatedModuleProduct.command(
            product_discriminator="argus.cash_application_correction_verification",
            owner="Argus",
            body=body,
            command_id="CMD-ARGUS-VERIFY",
            evidence_refs=EVIDENCE,
            available_from=NOW,
        )


def test_persistence_adapters_reject_partial_candidate_closure(
    tmp_path: Path,
) -> None:
    event = _business_event()
    source = CandidateAdmissionService(_memory_boundary(*event.evidence_refs)).assess(
        _assessment_command(event, suffix="ADAPTER-TEMPLATE")
    )
    for boundary in (
        _memory_boundary(*event.evidence_refs),
        _sqlite_boundary(tmp_path / "candidate-partial.sqlite3"),
    ):
        input_digest = value_digest(("partial-candidate", type(boundary).__name__))
        context = CommandContext(
            command_owner="Hermes",
            command_id=f"CMD-PARTIAL-{type(boundary).__name__}",
            command_type="AssessBusinessEventCandidate",
            input_contract_version="ARTIFACT-L-MODULE-COMMAND-V1",
            input_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
            input_digest=input_digest,
            actor_ref="ACTOR:HERMES",
            authority_refs=(),
            semantic_as_of_time=NOW,
            correlation_id=str(event.correlation_id),
        )
        outcome = ModuleCommandOutcome(
            command_id=context.command_id,
            command_owner="Hermes",
            consumed_publication_refs=(),
            immutable_creations=(source.receipt, source.admission_result),
        )
        result = CommandResult(
            command_id=context.command_id,
            command_fingerprint=input_digest,
            status="ACCEPTED",
            outcome=outcome,
        )
        before = boundary.state.full_digest
        revision = boundary.revision
        unit = boundary.begin_command(context)
        unit.stage_accepted(
            StagedWriteSet(
                projection_replacement=unit.records().snapshot(),
                object_appends=outcome.immutable_creations,
                accounting_event_appends=(),
                journal_appends=(),
                reporting_version_appends=(),
                effect_claims=(),
                expected_state_tokens=(),
                resulting_state_tokens=(),
                command_result=result,
            )
        )
        with pytest.raises(InvariantFailure, match="exact receipt and G-02"):
            unit.validate()
        unit.rollback()
        assert boundary.state.full_digest == before
        assert boundary.revision == revision
        if isinstance(boundary, SqlitePersistenceBoundary):
            boundary.close()


def test_rejected_candidate_cannot_cross_the_g01_firewall() -> None:
    event = _business_event()
    invalid_body = event.model_dump(mode="json")
    invalid_body.pop("payload")
    boundary = _memory_boundary(*event.evidence_refs)
    assessed = CandidateAdmissionService(boundary).assess(
        _assessment_command(
            event,
            suffix="FIREWALL",
            canonical_body=invalid_body,
        )
    )
    publication = ContractPublication.command(
        publication_ref="PUB-G01-ILLEGAL",
        contract_id="G-01",
        body_discriminator="business_event",
        publisher="SharedSubstrate",
        product_ref=str(event.business_event_id),
        payload=event.model_dump(mode="json"),
        command_owner="SharedSubstrate",
        command_id="CMD-SUBSTRATE-ILLEGAL",
        evidence_refs=EVIDENCE,
        available_from=NOW,
        upstream_publication_refs=(assessed.publication.exact_ref(),),
        upstream_authoritative_refs=(
            _exact_authority(
                "J-AR01",
                str(assessed.receipt.candidate_receipt_ref),
                value_digest(assessed.receipt),
            ),
            _exact_authority(
                "J-AR03", str(event.business_event_id), value_digest(event)
            ),
        ),
    )
    before = boundary.state.full_digest

    with pytest.raises(ModuleBoundaryError, match="accepted G-02"):
        ModuleContractService(boundary).execute(
            ModuleCommand(
                command_id="CMD-SUBSTRATE-ILLEGAL",
                command_owner="SharedSubstrate",
                command_type="PublishAdmittedBusinessEvent",
                actor_ref="ACTOR:SUBSTRATE",
                correlation_id=str(event.correlation_id),
                semantic_as_of_time=NOW,
                authoritative_creations=(event,),
                publications=(publication,),
                consumed_publication_refs=(
                    str(assessed.publication.publication_ref),
                ),
            )
        )

    assert boundary.state.full_digest == before


def test_candidate_receipt_query_survives_retry_restart_and_rebuild(
    tmp_path: Path,
) -> None:
    event = _business_event()
    database = tmp_path / "candidate-receipt.sqlite3"
    boundary = _sqlite_boundary(database)
    command = _assessment_command(event, suffix="DURABLE")
    first = CandidateAdmissionService(boundary).assess(command)
    digest = boundary.state.full_digest
    revision = boundary.revision
    exact_before = RuntimeQueryService(
        boundary,
        semantic_as_of_time=NOW,
    ).get_candidate_receipt(str(command.candidate_receipt_ref))
    receipt_ref = next(
        item
        for item in first.execution.receipt.committed_authoritative_refs
        if item.record_family == "J-AR01"
    )
    assert exact_before is not None
    assert exact_before.receipt.record.semantic_hash == receipt_ref.semantic_hash
    assert exact_before.outcome == "ACCEPTED"
    assert exact_before.eligible_for_g01
    replay = CandidateAdmissionService(boundary).assess(command)
    assert replay.execution.replayed
    assert boundary.state.full_digest == digest
    assert boundary.revision == revision
    changed_body = event.model_dump(mode="json")
    changed_body["effective_date"] = "2026-07-01"
    with pytest.raises(ModuleBoundaryError, match="different input"):
        CandidateAdmissionService(boundary).assess(
            command.model_copy(update={"canonical_candidate_body": changed_body})
        )
    assert boundary.state.full_digest == digest
    assert boundary.revision == revision
    boundary.close()

    restarted = SqlitePersistenceBoundary(database)
    exact = RuntimeQueryService(
        restarted,
        semantic_as_of_time=NOW,
    ).get_candidate_receipt(str(command.candidate_receipt_ref))
    assert exact is not None
    rebuild = restarted.open_rebuild(
        RebuildContext(
            semantic_as_of_time=NOW,
            requested_projection_families=("J-P01", "J-P11"),
        )
    )
    generation = rebuild.begin_generation()
    candidate = rebuild.rebuild(generation)
    rebuild.promote(rebuild.validate(candidate))
    rebuilt_exact = RuntimeQueryService(
        restarted,
        semantic_as_of_time=NOW,
    ).get_candidate_receipt(str(command.candidate_receipt_ref))
    assert rebuilt_exact is not None
    assert rebuilt_exact.receipt.record.semantic_hash == (
        exact.receipt.record.semantic_hash
    )
    assert rebuilt_exact.outcome == exact.outcome
    assert restarted.state.full_digest == digest
    restarted.close()


def test_candidate_assessment_rolls_back_complete_atomic_set(
    tmp_path: Path,
) -> None:
    database = tmp_path / "candidate-atomicity.sqlite3"
    seeded = _sqlite_boundary(database)
    seeded.close()

    def fail(stage: str) -> None:
        if stage == "command_before_commit":
            raise OSError("injected candidate commit failure")

    boundary = SqlitePersistenceBoundary(database, fault_injector=fail)
    before = boundary.state.full_digest
    revision = boundary.revision
    with pytest.raises(OSError, match="candidate commit failure"):
        CandidateAdmissionService(boundary).assess(
            _assessment_command(_business_event(), suffix="ATOMIC")
        )
    assert boundary.state.full_digest == before
    assert boundary.revision == revision
    assert RuntimeQueryService(
        boundary,
        semantic_as_of_time=NOW,
    ).get_candidate_receipt("J-AR01:CAND-ATOMIC") is None
    boundary.close()


def test_g02_to_g01_commits_and_observes_real_handoffs() -> None:
    boundary = _memory_boundary(EVIDENCE_BODY)
    observations = InMemoryObservationSink()
    service = ModuleContractService(boundary, observations=observations)

    g02, g01 = _admit_event(service)
    atlas = service.execute(
        ModuleCommand(
            command_id="CMD-ATLAS-CONSUME-G01",
            command_owner="Atlas",
            command_type="EvaluatePostingRuleInput",
            actor_ref="ACTOR:ATLAS",
            correlation_id="C-001",
            semantic_as_of_time=NOW,
            consumed_publication_refs=(str(g01.publication_ref),),
        )
    )

    assert atlas.receipt.outcome == "ACCEPTED"
    assert [item.operation for item in observations.observations] == [
        "PUBLISH",
        "PUBLISH",
        "CONSUME",
        "CONSUME",
    ]
    assert {item.contract_id for item in observations.observations} == {
        g02.contract_id,
        g01.contract_id,
    }


def test_registry_availability_and_evidence_are_enforced_before_commit() -> None:
    boundary = _memory_boundary(EVIDENCE_BODY)
    service = ModuleContractService(boundary)
    _, g01 = _admit_event(service)
    before = boundary.state.full_digest

    with pytest.raises(ModuleBoundaryError, match="consumer"):
        service.execute(
            ModuleCommand(
                command_id="CMD-AEGIS-ILLEGAL-CONSUME",
                command_owner="Aegis",
                command_type="IllegalRead",
                actor_ref="ACTOR:AEGIS",
                correlation_id="C-001",
                semantic_as_of_time=NOW,
                consumed_publication_refs=(str(g01.publication_ref),),
            )
        )
    assert boundary.state.full_digest == before

    with pytest.raises(ModuleBoundaryError, match="available"):
        service.execute(
            ModuleCommand(
                command_id="CMD-ATLAS-PREMATURE-CONSUME",
                command_owner="Atlas",
                command_type="PrematureRead",
                actor_ref="ACTOR:ATLAS",
                correlation_id="C-001",
                semantic_as_of_time="2026-07-14T11:59:59Z",
                consumed_publication_refs=(str(g01.publication_ref),),
            )
        )
    assert boundary.state.full_digest == before

    with pytest.raises(ValueError, match="evidence"):
        ContractPublication.command(
            publication_ref="PUB-BAD-EVIDENCE",
            contract_id="G-02",
            body_discriminator="G02AdmissionResult",
            publisher="Hermes",
            product_ref="ADM-C001@v1",
            payload=_admission_body(),
            command_owner="Hermes",
            command_id="CMD-BAD-EVIDENCE",
            evidence_refs=(),
            available_from=NOW,
        )


def test_scalar_types_and_readiness_semantics_are_closed() -> None:
    bad_reconciliation = {
        "product_ref": "RECON-BAD@v1",
        "reconciliation_type": "RECOGNITION_POPULATION",
        "scope_ref": "CONTRACT:BAD",
        "result": "FAILED",
        "performed_at": NOW,
        "period_id": "2026-06",
        "recognition_schedule_ref": "SCHEDULE:BAD@v1",
        "expected_item_count": 1,
        "expected_amount_minor": "1000",
        "posted_item_count": 0,
        "posted_amount_minor": 0,
        "submitted_unposted_count": 1,
        "deferred_count": 0,
        "difference_minor": 1000,
        "currency": "GBP",
    }
    with pytest.raises(ValueError, match="integer"):
        ContractPublication.command(
            publication_ref="PUB-G03-BAD-TYPE",
            contract_id="G-03",
            body_discriminator="G03ReconciliationResult",
            publisher="Hermes",
            product_ref="RECON-BAD@v1",
            payload=bad_reconciliation,
            command_owner="Hermes",
            command_id="CMD-G03-BAD-TYPE",
            evidence_refs=EVIDENCE,
            available_from=NOW,
        )

    bad_readiness = {
        "product_ref": "READY-BAD@v1",
        "reporting_version_ref": "RV-BAD@v1",
        "reporting_publication_ref": "PUB-G06-BAD",
        "period_id": "2026-06",
        "scope_ref": "NEXUS-GROUP",
        "purpose_ref": "HIRING-FORECAST",
        "status": "APPROVED",
        "basis_refs": [
            _exact_authority("J-AR13", "PUB-G06-BAD").model_dump(mode="json")
        ],
        "limitation_codes": ["KNOWN_MISSTATEMENT"],
        "assessed_by": {"actor_type": "PERSON", "actor_id": "CFO"},
        "assessed_at": NOW,
    }
    with pytest.raises(ValueError, match="limitations"):
        ContractPublication.command(
            publication_ref="PUB-G10-BAD-READINESS",
            contract_id="G-10",
            body_discriminator="G10ReadinessAssessment",
            publisher="Aegis",
            product_ref="READY-BAD@v1",
            payload=bad_readiness,
            command_owner="Aegis",
            command_id="CMD-G10-BAD-READINESS",
            evidence_refs=EVIDENCE,
            available_from=NOW,
        )


def test_g14_is_rejection_only_and_atomic() -> None:
    boundary = _memory_boundary(EVIDENCE_BODY)
    observations = InMemoryObservationSink()
    service = ModuleContractService(boundary, observations=observations)
    body = {
        "disposition_ref": "DISP-INVALID-DIRECTIVE@v1",
        "command_owner": "Atlas",
        "command_id": "CMD-ATLAS-REJECT",
        "command_type": "ApplyRemediationDirective",
        "requesting_module": "Aegis",
        "target_module": "Atlas",
        "request_ref": "DIRECTIVE-INVALID@v1",
        "disposition": "REJECTED",
        "reason_code": "DIRECTIVE_INVALID",
        "recorded_at": NOW,
        "authority_refs": [
            _exact_authority(
                "J-AR04", "POLICY-RESTATEMENT@v1"
            ).model_dump(mode="json")
        ],
    }
    publication = ContractPublication.command(
        publication_ref="PUB-G14-REJECT",
        contract_id="G-14",
        body_discriminator="G14CommandRejection",
        publisher="Atlas",
        product_ref="DISP-INVALID-DIRECTIVE@v1",
        payload=body,
        command_owner="Atlas",
        command_id="CMD-ATLAS-REJECT",
        evidence_refs=EVIDENCE,
        available_from=NOW,
    )
    result = service.reject(
        ModuleCommand(
            command_id="CMD-ATLAS-REJECT",
            command_owner="Atlas",
            command_type="ApplyRemediationDirective",
            actor_ref="ACTOR:ATLAS",
            correlation_id="C-001",
            semantic_as_of_time=NOW,
            publications=(publication,),
        ),
        rejection=Rejection(
            code=RejectionCode("DIRECTIVE_INVALID"),
            reason="directive cannot be applied",
        ),
        disposition=CommandDisposition(
            contract_id="G-14",
            command_id="CMD-ATLAS-REJECT",
            request_ref="DIRECTIVE-INVALID@v1",
            status="REJECTED",
            rejection_code="DIRECTIVE_INVALID",
            reason="directive cannot be applied",
        ),
    )

    assert result.receipt.outcome == "REJECTED"
    assert result.receipt.committed_publication_refs[0].record_identity == (
        "PUB-G14-REJECT"
    )
    assert boundary.state.dispositions[0].command_id == "CMD-ATLAS-REJECT"
    assert observations.observations[0].contract_id == "G-14"


def test_observation_failure_cannot_roll_back_authoritative_commit() -> None:
    class BrokenSink:
        def record(self, observation: object) -> None:
            del observation
            raise RuntimeError("telemetry unavailable")

    boundary = _memory_boundary(EVIDENCE_BODY)
    service = ModuleContractService(boundary, observations=BrokenSink())
    _admit_event(service)

    assert len(boundary.state.command_results) == 2
    assert len(
        [
            item
            for item in boundary.state.object_versions
            if isinstance(item, ContractPublication)
        ]
    ) == 2


def test_publications_and_module_outcomes_survive_sqlite_restart(
    tmp_path: Path,
) -> None:
    database = tmp_path / "phase5.sqlite3"
    boundary = _sqlite_boundary(database)
    service = ModuleContractService(boundary)
    _admit_event(service)
    digest = boundary.state.full_digest
    boundary.close()

    restarted = SqlitePersistenceBoundary(database)
    assert restarted.state.full_digest == digest
    assert len(
        [
            item
            for item in restarted.state.object_versions
            if isinstance(item, ContractPublication)
        ]
    ) == 2
    replay_service = ModuleContractService(restarted)
    _admit_event(replay_service)
    assert restarted.state.full_digest == digest
    restarted.close()


def test_c001_governance_planning_contract_chain_is_executed() -> None:
    g06_payload = {
        "reporting_version_ref": "RV-2026-06@v2",
        "period_id": "2026-06",
        "content_ref": "reporting://2026-06/v2",
        "content_hash": "sha256:" + "2" * 64,
        "content_schema_version": 1,
        "publication_origin": "PRE_SCOPE_IMPORT",
        "published_at": NOW,
        "import_attestation_ref": "J-AR11:IMPORT-RV2",
        "original_authority_ref": "AUTHORITY:CFO",
        "source_ref": "ARCHIVE:RV2",
    }
    g06 = ContractPublication(
        publication_ref="PUB-G06-RV2",
        contract_id="G-06",
        g_contract_version="G-v0.2",
        body_contract_version=1,
        body_discriminator="G06ReportingVersion",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        publisher="Atlas",
        product_ref="RV-2026-06@v2",
        product_state_token=None,
        canonical_payload=g06_payload,
        payload_hash=canonical_sha256(g06_payload),
        upstream_publication_refs=(),
        upstream_authoritative_refs=(
            _exact_authority("J-AR10", "RV-2026-06@v2"),
        ),
        evidence_refs=EVIDENCE,
        available_from=NOW,
        publication_basis=ImportPublicationBasis(
            basis_type="PRE_SCOPE_IMPORT",
            import_attestation_ref="J-AR11:IMPORT-RV2",
        ),
    )
    boundary = _memory_boundary(EVIDENCE_BODY, objects=(g06,))
    sink = InMemoryObservationSink()
    service = ModuleContractService(boundary, observations=sink)

    def execute_product(
        *,
        command_id: str,
        owner: str,
        discriminator: str,
        body: dict[str, object],
        contract_id: str,
        body_discriminator: str,
        publication_payload: dict[str, object],
        product_ref: str,
        consumed: tuple[str, ...] = (),
        companion_products: tuple[tuple[str, dict[str, object]], ...] = (),
    ) -> ContractPublication:
        product = ValidatedModuleProduct.command(
            product_discriminator=discriminator,
            owner=owner,
            body=body,
            command_id=command_id,
            evidence_refs=EVIDENCE,
            available_from=NOW,
            upstream_publication_refs=_exact_publications(boundary, consumed),
        )
        publication = ContractPublication.command(
            publication_ref=f"PUB-{contract_id}-{command_id}",
            contract_id=contract_id,  # type: ignore[arg-type]
            body_discriminator=body_discriminator,
            publisher=owner,  # type: ignore[arg-type]
            product_ref=product_ref,
            payload=publication_payload,
            command_owner=owner,
            command_id=command_id,
            evidence_refs=EVIDENCE,
            available_from=NOW,
            upstream_publication_refs=_exact_publications(boundary, consumed),
        )
        companions = tuple(
            ValidatedModuleProduct.command(
                product_discriminator=item_discriminator,
                owner=owner,
                body=item_body,
                command_id=command_id,
                evidence_refs=EVIDENCE,
                available_from=NOW,
                upstream_publication_refs=_exact_publications(boundary, consumed),
            )
            for item_discriminator, item_body in companion_products
        )
        service.execute(
            ModuleCommand(
                command_id=command_id,
                command_owner=owner,
                command_type=discriminator,
                actor_ref=f"ACTOR:{owner.upper()}",
                correlation_id="C-001",
                semantic_as_of_time=NOW,
                products=(*companions, product),
                publications=(publication,),
                consumed_publication_refs=consumed,
            )
        )
        return publication

    g03_body = {
        "product_ref": "RECON-C001@v1",
        "reconciliation_type": "RECOGNITION_POPULATION",
        "scope_ref": "CONTRACT:C001",
        "result": "FAILED",
        "performed_at": NOW,
        "period_id": "2026-06",
        "recognition_schedule_ref": "SCHEDULE:C001@v1",
        "expected_item_count": 12,
        "expected_amount_minor": 12000000,
        "posted_item_count": 11,
        "posted_amount_minor": 11000000,
        "submitted_unposted_count": 1,
        "deferred_count": 1,
        "difference_minor": 1000000,
        "currency": "GBP",
    }
    g03 = execute_product(
        command_id="CMD-HERMES-RECON",
        owner="Hermes",
        discriminator="hermes.recognition_population_reconciliation",
        body=g03_body,
        contract_id="G-03",
        body_discriminator="G03ReconciliationResult",
        publication_payload=g03_body,
        product_ref="RECON-C001@v1",
    )
    exception_body = {
        "product_ref": "EXC-C001@v1",
        "created_at": NOW,
        "test_run_ref": "TEST-C001@v1",
        "assertion": "COMPLETENESS",
        "severity": "BLOCKING",
        "subject_refs": [
            _exact_authority("J-AR02", "RECON-C001@v1").model_dump(mode="json")
        ],
        "expected_amount_minor": 1000000,
        "actual_amount_minor": 0,
        "difference_minor": 1000000,
        "currency": "GBP",
        "period_id": "2026-06",
        "status": "OPEN",
    }
    g07 = execute_product(
        command_id="CMD-ARGUS-TEST",
        owner="Argus",
        discriminator="argus.recognition_completeness_exception",
        body=exception_body,
        contract_id="G-07",
        body_discriminator="G07AssuranceResult",
        publication_payload={
            "result_type": "ASSURANCE_EXCEPTION",
            "test_run_ref": "TEST-C001@v1",
            "exception_ref": "EXC-C001@v1",
            "test_outcome": "FAILED",
            "assertion": "COMPLETENESS",
            "severity": "BLOCKING",
        },
        product_ref="EXC-C001@v1",
        consumed=(str(g03.publication_ref),),
        companion_products=(
            (
                "argus.recognition_completeness_test_run",
                {
                    "product_ref": "TEST-C001@v1",
                    "created_at": NOW,
                    "test_definition_ref": "J-AR04:TEST-REVENUE-COMPLETENESS@v1",
                    "reconciliation_ref": "RECON-C001@v1",
                    "period_id": "2026-06",
                    "population_refs": [
                        _exact_authority(
                            "J-AR02", "RECON-C001@v1"
                        ).model_dump(mode="json")
                    ],
                    "population_hashes": ["sha256:" + "1" * 64],
                    "executed_at": NOW,
                    "outcome": "FAILED",
                    "exception_ref": "EXC-C001@v1",
                },
            ),
        ),
    )
    issue_body = {
        "product_ref": "ISSUE-C001@v1",
        "created_at": NOW,
        "issue_id": "ISSUE-C001",
        "issue_version": 1,
        "finding_refs": ["FINDING-C001@v1"],
        "status": "OPEN",
        "owner_ref": "ACTOR:CONTROLLER",
        "directive_refs": [],
        "verification_refs": [],
        "updated_at": NOW,
    }
    g08 = execute_product(
        command_id="CMD-AEGIS-GOVERN",
        owner="Aegis",
        discriminator="aegis.issue",
        body=issue_body,
        contract_id="G-08",
        body_discriminator="G08GovernanceResult",
        publication_payload={
            "governance_result_type": "EXCEPTION_GOVERNED",
            "review_ref": "REVIEW-C001@v1",
            "finding_ref": "FINDING-C001@v1",
            "issue_ref": "ISSUE-C001@v1",
            "source_exception_ref": "EXC-C001@v1",
        },
        product_ref="ISSUE-C001@v1",
        consumed=(str(g07.publication_ref),),
        companion_products=(
            (
                "aegis.exception_review",
                {
                    "product_ref": "REVIEW-C001@v1",
                    "created_at": NOW,
                    "exception_ref": "EXC-C001@v1",
                    "review_outcome": "CONFIRMED",
                    "reviewed_by": "ACTOR:CONTROLLER",
                    "reviewed_at": NOW,
                    "conclusion_code": "POLICY-CONCLUSION@v1",
                },
            ),
            (
                "aegis.finding",
                {
                    "product_ref": "FINDING-C001@v1",
                    "created_at": NOW,
                    "review_ref": "REVIEW-C001@v1",
                    "finding_type": "RECOGNITION_OMISSION",
                    "assertion": "COMPLETENESS",
                    "affected_refs": [
                        _exact_authority(
                            "J-AR02", "EXC-C001@v1"
                        ).model_dump(mode="json")
                    ],
                    "conclusion_code": "POLICY-CONCLUSION@v1",
                },
            ),
        ),
    )
    directive_body = {
        "product_ref": "DIRECTIVE-C001@v1",
        "issue_ref": "ISSUE-C001@v1",
        "target_module": "Atlas",
        "requested_outcome": "RESTATEMENT",
        "affected_period_id": "2026-06",
        "eligible_correction_period_id": "2026-07",
        "policy_ref": "J-AR04:POL-RESTATEMENT@v1",
        "requested_by": {"actor_type": "PERSON", "actor_id": "CFO"},
        "requested_at": NOW,
    }
    execute_product(
        command_id="CMD-AEGIS-DIRECT",
        owner="Aegis",
        discriminator="aegis.remediation_directive",
        body=directive_body,
        contract_id="G-09",
        body_discriminator="G09RemediationDirective",
        publication_payload=directive_body,
        product_ref="DIRECTIVE-C001@v1",
        consumed=(str(g08.publication_ref),),
    )
    readiness_body = {
        "product_ref": "READY-C001@v1",
        "reporting_version_ref": "RV-2026-06@v2",
        "reporting_publication_ref": str(g06.publication_ref),
        "period_id": "2026-06",
        "scope_ref": "NEXUS-GROUP",
        "purpose_ref": "HIRING-FORECAST",
        "status": "APPROVED",
        "basis_refs": [_exact_publication(g06).model_dump(mode="json")],
        "limitation_codes": [],
        "assessed_by": {"actor_type": "PERSON", "actor_id": "CFO"},
        "assessed_at": NOW,
    }
    g10 = execute_product(
        command_id="CMD-AEGIS-READY",
        owner="Aegis",
        discriminator="aegis.readiness_assessment",
        body=readiness_body,
        contract_id="G-10",
        body_discriminator="G10ReadinessAssessment",
        publication_payload=readiness_body,
        product_ref="READY-C001@v1",
        consumed=(str(g06.publication_ref), str(g08.publication_ref)),
    )
    planning_body = {
        "product_ref": "PLAN-C001@v1",
        "reporting_version_ref": "RV-2026-06@v2",
        "reporting_publication_ref": str(g06.publication_ref),
        "readiness_ref": "READY-C001@v1",
        "readiness_publication_ref": str(g10.publication_ref),
        "purpose_ref": "HIRING-FORECAST",
        "period_id": "2026-06",
        "scope_ref": "NEXUS-GROUP",
        "assumption_refs": ["J-AR04:ASSUMPTIONS@v1"],
        "exclusion_refs": [],
        "frozen_at": NOW,
    }
    g11 = execute_product(
        command_id="CMD-PYTHIA-FREEZE",
        owner="Pythia",
        discriminator="pythia.planning_input_snapshot",
        body=planning_body,
        contract_id="G-11",
        body_discriminator="G11PlanningInputSnapshot",
        publication_payload=planning_body,
        product_ref="PLAN-C001@v1",
        consumed=(str(g06.publication_ref), str(g10.publication_ref)),
    )
    decision_body = {
        "product_ref": "DECISION-C001@v1",
        "decision_type": "HIRING_DEFERRED",
        "planning_snapshot_ref": "PLAN-C001@v1",
        "planning_publication_ref": str(g11.publication_ref),
        "position_ref": "POSITION-CS-014",
        "original_start_date": "2026-08-01",
        "recommended_start_date": "2026-09-01",
        "monthly_cost_minor": 650000,
        "currency": "GBP",
        "reason_code": "ACTUALS_READINESS_DELAY",
        "produced_at": NOW,
    }
    execute_product(
        command_id="CMD-PYTHIA-DECIDE",
        owner="Pythia",
        discriminator="pythia.governed_decision",
        body=decision_body,
        contract_id="G-12",
        body_discriminator="G12GovernedDecision",
        publication_payload=decision_body,
        product_ref="DECISION-C001@v1",
        consumed=(str(g11.publication_ref),),
    )

    assert {item.contract_id for item in sink.observations if item.operation == "PUBLISH"} == {
        "G-03",
        "G-07",
        "G-08",
        "G-09",
        "G-10",
        "G-11",
        "G-12",
    }


def test_ct1_assurance_governance_trace_consumes_non_authored_g13() -> None:
    source_hash = "sha256:" + "3" * 64
    g13_payload = {
        "projection_type": "referenced_journal_projection",
        "projection_version": 1,
        "authored_by_f": False,
        "source_hash": source_hash,
        "journal_id": "J-010",
        "ledger_period_id": "2026-07",
        "currency": "GBP",
        "line_tuples": [],
    }
    g13 = ContractPublication(
        publication_ref="PUB-G13-J010",
        contract_id="G-13",
        g_contract_version="G-v0.2",
        body_contract_version=1,
        body_discriminator="G13ReferencedJournal",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        publisher="AtlasReadBoundary",
        product_ref="J-010@v1",
        product_state_token=None,
        canonical_payload=g13_payload,
        payload_hash=canonical_sha256(g13_payload),
        upstream_publication_refs=(),
        upstream_authoritative_refs=(_exact_authority("J-AR17", "J-010"),),
        evidence_refs=EVIDENCE,
        available_from=NOW,
        publication_basis=ReferencedJournalPublicationBasis(
            basis_type="REFERENCED_JOURNAL_ADMISSION",
            referenced_source_ref="J-010",
            admission_identity="J-010",
        ),
    )
    boundary = _memory_boundary(EVIDENCE_BODY, objects=(g13,))
    sink = InMemoryObservationSink()
    service = ModuleContractService(boundary, observations=sink)

    def execute(
        command_id: str,
        owner: str,
        discriminator: str,
        body: dict[str, object],
        contract_id: str,
        payload: dict[str, object],
        product_ref: str,
        consumed: tuple[str, ...],
        companion_products: tuple[tuple[str, dict[str, object]], ...] = (),
    ) -> ContractPublication:
        product = ValidatedModuleProduct.command(
            product_discriminator=discriminator,
            owner=owner,
            body=body,
            command_id=command_id,
            evidence_refs=EVIDENCE,
            available_from=NOW,
            upstream_publication_refs=_exact_publications(boundary, consumed),
        )
        publication = ContractPublication.command(
            publication_ref=f"PUB-{contract_id}-{command_id}",
            contract_id=contract_id,  # type: ignore[arg-type]
            body_discriminator={
                "G-03": "G03ReconciliationResult",
                "G-07": "G07AssuranceResult",
                "G-08": "G08GovernanceResult",
            }[contract_id],
            publisher=owner,  # type: ignore[arg-type]
            product_ref=product_ref,
            payload=payload,
            command_owner=owner,
            command_id=command_id,
            evidence_refs=EVIDENCE,
            available_from=NOW,
            upstream_publication_refs=_exact_publications(boundary, consumed),
        )
        companions = tuple(
            ValidatedModuleProduct.command(
                product_discriminator=item_discriminator,
                owner=owner,
                body=item_body,
                command_id=command_id,
                evidence_refs=EVIDENCE,
                available_from=NOW,
                upstream_publication_refs=_exact_publications(boundary, consumed),
            )
            for item_discriminator, item_body in companion_products
        )
        service.execute(
            ModuleCommand(
                command_id=command_id,
                command_owner=owner,
                command_type=discriminator,
                actor_ref=f"ACTOR:{owner.upper()}",
                correlation_id="CT-1",
                semantic_as_of_time=NOW,
                products=(*companions, product),
                publications=(publication,),
                consumed_publication_refs=consumed,
            )
        )
        return publication

    reconciliation = {
        "product_ref": "RECON-CT1@v1",
        "reconciliation_type": "CASH_APPLICATION_IDENTITY",
        "scope_ref": "CASH-APPLICATION:CT1",
        "result": "FAILED",
        "performed_at": NOW,
        "cash_application_ref": "CASH-APP-010",
        "receipt_party_ref": "PARTY:ORION",
        "application_party_ref": "PARTY:VEGA",
        "party_mapping_ref": "PARTY-MAP-010@v1",
        "identity_match": False,
    }
    g03 = execute(
        "CMD-HERMES-CT1-RECON",
        "Hermes",
        "hermes.cash_application_identity_reconciliation",
        reconciliation,
        "G-03",
        reconciliation,
        "RECON-CT1@v1",
        (),
    )
    exception = {
        "product_ref": "EXC-CT1@v1",
        "created_at": NOW,
        "test_run_ref": "TEST-CT1@v1",
        "assertion": "ACCURACY",
        "severity": "HIGH",
        "receipt_party_ref": "PARTY:ORION",
        "application_party_ref": "PARTY:VEGA",
        "journal_id": "J-010",
        "amount_minor": 12000000,
        "currency": "GBP",
        "status": "OPEN",
    }
    g07 = execute(
        "CMD-ARGUS-CT1-TEST",
        "Argus",
        "argus.cash_application_identity_exception",
        exception,
        "G-07",
        {
            "result_type": "ASSURANCE_EXCEPTION",
            "test_run_ref": "TEST-CT1@v1",
            "exception_ref": "EXC-CT1@v1",
            "test_outcome": "FAILED",
            "assertion": "ACCURACY",
            "severity": "HIGH",
        },
        "EXC-CT1@v1",
        (str(g03.publication_ref), str(g13.publication_ref)),
        (
            (
                "argus.cash_application_identity_test_run",
                {
                    "product_ref": "TEST-CT1@v1",
                    "created_at": NOW,
                    "test_definition_ref": "J-AR04:TEST-CASH-IDENTITY@v1",
                    "reconciliation_ref": "RECON-CT1@v1",
                    "referenced_journal_publication_ref": "PUB-G13-J010",
                    "population_refs": [
                        _exact_authority(
                            "J-AR17", "J-010", source_hash
                        ).model_dump(mode="json")
                    ],
                    "population_hashes": [source_hash],
                    "executed_at": NOW,
                    "outcome": "FAILED",
                    "exception_ref": "EXC-CT1@v1",
                },
            ),
        ),
    )
    issue = {
        "product_ref": "ISSUE-CT1@v1",
        "created_at": NOW,
        "issue_id": "ISSUE-CT1",
        "issue_version": 1,
        "finding_refs": ["FINDING-CT1@v1"],
        "status": "OPEN",
        "owner_ref": "ACTOR:CONTROLLER",
        "directive_refs": [],
        "verification_refs": [],
        "updated_at": NOW,
    }
    g08 = execute(
        "CMD-AEGIS-CT1-GOVERN",
        "Aegis",
        "aegis.issue",
        issue,
        "G-08",
        {
            "governance_result_type": "EXCEPTION_GOVERNED",
            "review_ref": "REVIEW-CT1@v1",
            "finding_ref": "FINDING-CT1@v1",
            "issue_ref": "ISSUE-CT1@v1",
            "source_exception_ref": "EXC-CT1@v1",
        },
        "ISSUE-CT1@v1",
        (str(g07.publication_ref),),
        (
            (
                "aegis.exception_review",
                {
                    "product_ref": "REVIEW-CT1@v1",
                    "created_at": NOW,
                    "exception_ref": "EXC-CT1@v1",
                    "review_outcome": "CONFIRMED",
                    "reviewed_by": "ACTOR:CONTROLLER",
                    "reviewed_at": NOW,
                    "conclusion_code": "POLICY-CONCLUSION@v1",
                },
            ),
            (
                "aegis.finding",
                {
                    "product_ref": "FINDING-CT1@v1",
                    "created_at": NOW,
                    "review_ref": "REVIEW-CT1@v1",
                    "finding_type": "CASH_APPLICATION_IDENTITY_MISMATCH",
                    "assertion": "ACCURACY",
                    "affected_refs": [
                        _exact_authority(
                            "J-AR02", "EXC-CT1@v1"
                        ).model_dump(mode="json")
                    ],
                    "conclusion_code": "POLICY-CONCLUSION@v1",
                },
            ),
        ),
    )
    verification = {
        "product_ref": "VERIFY-CT1@v1",
        "created_at": NOW,
        "verification_type": "CASH_APPLICATION_CORRECTION",
        "source_journal_ref": "J-AR17:J-010",
        "source_hash": source_hash,
        "reversal_journal_ref": "J-AR08:J-011",
        "replacement_journal_ref": "J-AR08:J-012",
        "check_results": {
            "reversal_source_bound": True,
            "reversal_equal_and_opposite": True,
            "replacement_customer_correct": True,
            "journals_balanced": True,
            "control_account_net_zero": True,
        },
        "outcome": "PASSED",
    }
    g07_verification = execute(
        "CMD-ARGUS-CT1-VERIFY",
        "Argus",
        "argus.cash_application_correction_verification",
        verification,
        "G-07",
        {
            "result_type": "ASSURANCE_VERIFICATION",
            "verification_ref": "VERIFY-CT1@v1",
            "verification_outcome": "PASSED",
        },
        "VERIFY-CT1@v1",
        (str(g08.publication_ref), str(g13.publication_ref)),
    )
    successor_issue = {
        **issue,
        "product_ref": "ISSUE-CT1@v2",
        "issue_version": 2,
        "prior_issue_ref": "ISSUE-CT1@v1",
        "status": "REMEDIATION_VERIFIED",
        "verification_refs": ["VERIFY-CT1@v1"],
    }
    execute(
        "CMD-AEGIS-CT1-UPDATE",
        "Aegis",
        "aegis.issue",
        successor_issue,
        "G-08",
        {
            "governance_result_type": "ISSUE_UPDATED",
            "issue_ref": "ISSUE-CT1@v2",
            "verification_ref": "VERIFY-CT1@v1",
            "prior_issue_ref": "ISSUE-CT1@v1",
        },
        "ISSUE-CT1@v2",
        (str(g07_verification.publication_ref),),
    )

    publishes = [
        item.contract_id for item in sink.observations if item.operation == "PUBLISH"
    ]
    assert publishes == ["G-03", "G-07", "G-08", "G-07", "G-08"]
    assert all(item.canonical_payload["authored_by_f"] is False for item in [g13])
