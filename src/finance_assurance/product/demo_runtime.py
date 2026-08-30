"""Ordinary-runtime materialisation for the bounded Artifact O demo."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from finance_assurance.analytics.catalog import (
    CATALOG_REF,
    july_open_period,
    ledger_catalog_evidence,
    ledger_semantics_catalog,
)
from finance_assurance.product.demo_scenarios import (
    BuiltScenario,
    DemoScenarioSet,
    build_c001_scenario,
    build_ct1_scenario,
)
from finance_assurance.runtime.application.admission import CandidateAdmissionService
from finance_assurance.runtime.application.contracts import (
    ModuleCommand,
    ModuleContractService,
)
from finance_assurance.runtime.application.models import (
    CandidateAssessmentCommand,
    ScriptedIdentityGenerator,
)
from finance_assurance.runtime.application.service import AccountingApplicationService
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
from finance_assurance.runtime.persistence.models import (
    AdmissionBundle,
    BaselineContext,
    ImportContext,
    PreScopeReportingImportBundle,
    ProjectionReplacement,
    QueryContext,
    ReferencedJournalAdmissionBundle,
    ReferencedJournalContext,
    SealedAdmissionRecord,
)
from finance_assurance.runtime.persistence.sqlite import SqlitePersistenceBoundary
from finance_assurance.runtime.persistence.state import InMemoryState
from finance_assurance.runtime.planner import StateSnapshot

ModuleOwner = Literal[
    "Hermes", "Atlas", "Argus", "Aegis", "Pythia", "SourceDomain"
]


@dataclass(frozen=True, slots=True)
class DemoMaterialization:
    scenario_refs: tuple[str, str]
    scenario_set_digest: str
    authoritative_inventory_digest: str
    semantic_state_digest: str
    query_revision: int
    event_count: int
    publication_count: int
    projection_generation_ref: str


def _sealed_record(
    family: str,
    identity: str,
    body: dict[str, object],
    *,
    owner: str = "PLATFORM",
) -> SealedAdmissionRecord:
    payload = canonical_bytes(body)
    return SealedAdmissionRecord(
        record_family=family,
        record_identity=identity,
        semantic_owner=owner,
        contract_version="1",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        semantic_hash=canonical_sha256(body),
        canonical_payload=payload,
    )


def _product_authority(product: ValidatedModuleProduct) -> dict[str, object]:
    return _exact_authority(
        "J-AR02",
        str(product.product_ref),
        str(product.semantic_hash),
    ).model_dump(mode="json")


def _publication_authority(publication: ContractPublication) -> dict[str, object]:
    return ExactSemanticRef(
        ref_kind="PUBLICATION",
        authoritative_ref=None,
        publication_ref=publication.exact_ref(),
        module_product_ref=None,
    ).model_dump(mode="json")


def _exact_authority(
    record_family: str,
    record_identity: str,
    semantic_hash: str,
) -> ExactSemanticRef:
    return ExactSemanticRef(
        ref_kind="AUTHORITATIVE",
        authoritative_ref=AuthoritativeRef(
            record_family=record_family,
            record_identity=record_identity,
            semantic_hash=semantic_hash,
        ),
        publication_ref=None,
        module_product_ref=None,
    )


def _module_evidence(evidence: EvidenceRef) -> tuple[AuthoritativeRef, ...]:
    return (
        AuthoritativeRef(
            record_family="J-AR12",
            record_identity=str(evidence.ref_id),
            semantic_hash=value_digest(evidence),
        ),
    )


def _combine_snapshot(c001: BuiltScenario, ct1: BuiltScenario) -> StateSnapshot:
    period_by_id = {
        item.period_id: item
        for item in (*c001.initial_snapshot.periods, *ct1.initial_snapshot.periods)
    }
    return StateSnapshot(
        periods=tuple(period_by_id[key] for key in sorted(period_by_id)),
        posted_journal_ids=(
            c001.initial_snapshot.posted_journal_ids
            | ct1.initial_snapshot.posted_journal_ids
        ),
        business_event_ids=(
            c001.initial_snapshot.business_event_ids
            | ct1.initial_snapshot.business_event_ids
        ),
        referenced_journals=ct1.initial_snapshot.referenced_journals,
    )


def _admit_baseline(
    database: Path,
    scenarios: DemoScenarioSet,
    c001: BuiltScenario,
    ct1: BuiltScenario,
    module_evidence: EvidenceRef,
) -> SqlitePersistenceBoundary:
    snapshot = _combine_snapshot(c001, ct1)
    state = InMemoryState.from_snapshot(snapshot)
    encoded_snapshot = encode_durable(state.snapshot)
    projection_ref = "DEMO-BASELINE@v1:J-P04"
    projection_hash = durable_hash(encoded_snapshot)
    scenario_set_digest = canonical_sha256(scenarios.model_dump(mode="json"))
    manifest = {
        "contract_version": 1,
        "manifest_ref": "DEMO-BASELINE@v1",
        "scenario_set_digest": scenario_set_digest,
        "scenario_refs": [
            str(scenarios.c001.scenario_ref),
            str(scenarios.ct1.scenario_ref),
        ],
        "runtime_release": str(scenarios.runtime_release),
        "projection_ref": projection_ref,
        "projection_hash": projection_hash,
        "predecessor_event_refs": [],
    }
    context = BaselineContext(
        baseline_manifest_ref="DEMO-BASELINE@v1",
        baseline_manifest_contract_version="1",
        baseline_manifest_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        baseline_manifest_hash=canonical_sha256(manifest),
        semantic_as_of_time="2026-06-01T00:00:00Z",
        admitting_actor_ref="ARTIFACT-O-DEMO",
    )
    catalogue_evidence = ledger_catalog_evidence()
    evidence = {
        str(item.ref_id): item
        for item in (
            *c001.evidence,
            *ct1.evidence,
            module_evidence,
            catalogue_evidence,
        )
    }
    v2_content = c001.reporting_content[1]
    assert c001.posting_rule is not None
    boundary = SqlitePersistenceBoundary(database)
    unit = boundary.begin_runtime_baseline_admission(context)
    unit.stage_bundle(
        AdmissionBundle(
            declared_records=(
                _sealed_record("J-AR04", "DEMO-BASELINE@v1", manifest),
                _sealed_record(
                    "J-AR04",
                    str(c001.posting_rule.posting_rule_ref),
                    c001.posting_rule.model_dump(mode="json"),
                    owner="ATLAS",
                ),
                _sealed_record(
                    "J-AR04",
                    CATALOG_REF,
                    ledger_semantics_catalog(),
                    owner="ATLAS",
                ),
                _sealed_record(
                    "J-AR07",
                    "2026-07",
                    july_open_period(),
                    owner="ATLAS",
                ),
                *tuple(
                    _sealed_record(
                        "J-AR12",
                        ref,
                        item.model_dump(mode="json"),
                    )
                    for ref, item in sorted(evidence.items())
                ),
                _sealed_record(
                    "J-AR12",
                    str(v2_content.content_ref),
                    v2_content.model_dump(mode="json"),
                ),
            ),
            projection_replacements=(
                ProjectionReplacement(
                    projection_family="J-P04",
                    projection_token=projection_ref,
                    source_hash=projection_hash,
                    canonical_payload=encoded_snapshot,
                ),
            ),
        )
    )
    unit.commit(unit.validate())
    return boundary


def _ct1_pre_correction_chain(
    boundary: SqlitePersistenceBoundary,
    scenarios: DemoScenarioSet,
    module_evidence: EvidenceRef,
    g13: ContractPublication,
) -> tuple[
    _ProductPublication,
    _ProductPublication,
    _ProductPublication,
    _ProductPublication,
]:
    descriptor = scenarios.ct1
    now = "2026-07-11T08:30:00Z"
    reconciliation_body = {
        "product_ref": "RECON-CT1@v1",
        "reconciliation_type": "CASH_APPLICATION_IDENTITY",
        "scope_ref": "CASH-APPLICATION:CT1",
        "result": "FAILED",
        "performed_at": now,
        "cash_application_ref": "CASH-APP-010",
        "receipt_party_ref": descriptor.receipt_party_ref,
        "application_party_ref": f"PARTY:{descriptor.incorrect_customer_id}",
        "party_mapping_ref": "PARTY-MAP-010@v1",
        "identity_match": False,
    }
    g03 = _execute_product(
        boundary,
        command_id="CMD-HERMES-CT1-RECON",
        owner="Hermes",
        correlation_id=descriptor.correlation_id,
        discriminator="hermes.cash_application_identity_reconciliation",
        body=reconciliation_body,
        publication_ref="PUB-G03-CT1",
        contract_id="G-03",
        body_discriminator="G03ReconciliationResult",
        publication_payload=reconciliation_body,
        product_ref="RECON-CT1@v1",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
    )
    source_hash = str(g13.canonical_payload["source_hash"])
    exception_body = {
        "product_ref": "EXC-CT1@v1",
        "created_at": now,
        "test_run_ref": "TEST-CT1@v1",
        "assertion": "ACCURACY",
        "severity": "HIGH",
        "receipt_party_ref": descriptor.receipt_party_ref,
        "application_party_ref": f"PARTY:{descriptor.incorrect_customer_id}",
        "journal_id": descriptor.source_journal_id,
        "amount_minor": descriptor.amount_minor,
        "currency": descriptor.currency,
        "status": "OPEN",
    }
    g07 = _execute_product(
        boundary,
        command_id="CMD-ARGUS-CT1-TEST",
        owner="Argus",
        correlation_id=descriptor.correlation_id,
        discriminator="argus.cash_application_identity_exception",
        body=exception_body,
        publication_ref="PUB-G07-CT1-EXCEPTION",
        contract_id="G-07",
        body_discriminator="G07AssuranceResult",
        publication_payload={
            "result_type": "ASSURANCE_EXCEPTION",
            "test_run_ref": "TEST-CT1@v1",
            "exception_ref": "EXC-CT1@v1",
            "test_outcome": "FAILED",
            "assertion": "ACCURACY",
            "severity": "HIGH",
        },
        product_ref="EXC-CT1@v1",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(str(g03.publication.publication_ref), str(g13.publication_ref)),
        companions=(
            (
                "argus.cash_application_identity_test_run",
                {
                    "product_ref": "TEST-CT1@v1",
                    "created_at": now,
                    "test_definition_ref": "J-AR04:TEST-CASH-IDENTITY@v1",
                    "reconciliation_ref": "RECON-CT1@v1",
                    "referenced_journal_publication_ref": str(g13.publication_ref),
                    "population_refs": [
                        _exact_authority(
                            "J-AR17", descriptor.source_journal_id, source_hash
                        ).model_dump(mode="json")
                    ],
                    "population_hashes": [source_hash],
                    "executed_at": now,
                    "outcome": "FAILED",
                    "exception_ref": "EXC-CT1@v1",
                },
            ),
        ),
    )
    issue_body = {
        "product_ref": "ISSUE-CT1@v1",
        "created_at": now,
        "issue_id": "ISSUE-CT1",
        "issue_version": 1,
        "finding_refs": ["FINDING-CT1@v1"],
        "status": "OPEN",
        "owner_ref": "ACTOR:CONTROLLER",
        "directive_refs": [],
        "verification_refs": [],
        "updated_at": now,
    }
    g08 = _execute_product(
        boundary,
        command_id="CMD-AEGIS-CT1-GOVERN",
        owner="Aegis",
        correlation_id=descriptor.correlation_id,
        discriminator="aegis.issue",
        body=issue_body,
        publication_ref="PUB-G08-CT1-ISSUE-V1",
        contract_id="G-08",
        body_discriminator="G08GovernanceResult",
        publication_payload={
            "governance_result_type": "EXCEPTION_GOVERNED",
            "review_ref": "REVIEW-CT1@v1",
            "finding_ref": "FINDING-CT1@v1",
            "issue_ref": "ISSUE-CT1@v1",
            "source_exception_ref": "EXC-CT1@v1",
        },
        product_ref="ISSUE-CT1@v1",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(str(g07.publication.publication_ref),),
        companions=(
            (
                "aegis.exception_review",
                {
                    "product_ref": "REVIEW-CT1@v1",
                    "created_at": now,
                    "exception_ref": "EXC-CT1@v1",
                    "review_outcome": "CONFIRMED",
                    "reviewed_by": "ACTOR:CONTROLLER",
                    "reviewed_at": now,
                    "conclusion_code": "POLICY-CONCLUSION@v1",
                },
            ),
            (
                "aegis.finding",
                {
                    "product_ref": "FINDING-CT1@v1",
                    "created_at": now,
                    "review_ref": "REVIEW-CT1@v1",
                    "finding_type": "CASH_APPLICATION_IDENTITY_MISMATCH",
                    "assertion": "ACCURACY",
                    "affected_refs": [_product_authority(g07.product)],
                    "conclusion_code": "POLICY-CONCLUSION@v1",
                },
            ),
        ),
    )
    directive_body = {
        "product_ref": "DIRECTIVE-CT1@v1",
        "issue_ref": "ISSUE-CT1@v1",
        "target_module": "Atlas",
        "requested_outcome": "REVERSAL_AND_REPLACEMENT",
        "affected_period_id": descriptor.correction_period_id,
        "eligible_correction_period_id": descriptor.correction_period_id,
        "policy_ref": "J-AR04:POL-CORRECTION@v1",
        "requested_by": {"actor_type": "PERSON", "actor_id": "CONTROLLER"},
        "requested_at": now,
    }
    g09 = _execute_product(
        boundary,
        command_id="CMD-AEGIS-CT1-DIRECT",
        owner="Aegis",
        correlation_id=descriptor.correlation_id,
        discriminator="aegis.remediation_directive",
        body=directive_body,
        publication_ref="PUB-G09-CT1",
        contract_id="G-09",
        body_discriminator="G09RemediationDirective",
        publication_payload=directive_body,
        product_ref="DIRECTIVE-CT1@v1",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(str(g08.publication.publication_ref),),
    )
    return g03, g07, g08, g09


def _ct1_post_correction_chain(
    boundary: SqlitePersistenceBoundary,
    scenarios: DemoScenarioSet,
    module_evidence: EvidenceRef,
    g13: ContractPublication,
) -> None:
    descriptor = scenarios.ct1
    now = str(descriptor.semantic_as_of_time)
    source_hash = str(g13.canonical_payload["source_hash"])
    verification_body = {
        "product_ref": "VERIFY-CT1@v1",
        "created_at": now,
        "verification_type": "CASH_APPLICATION_CORRECTION",
        "source_journal_ref": f"J-AR17:{descriptor.source_journal_id}",
        "source_hash": source_hash,
        "reversal_journal_ref": f"J-AR08:{descriptor.reversal_journal_id}",
        "replacement_journal_ref": f"J-AR08:{descriptor.replacement_journal_id}",
        "check_results": {
            "reversal_source_bound": True,
            "reversal_equal_and_opposite": True,
            "replacement_customer_correct": True,
            "journals_balanced": True,
            "control_account_net_zero": True,
        },
        "outcome": "PASSED",
    }
    verification = _execute_product(
        boundary,
        command_id="CMD-ARGUS-CT1-VERIFY",
        owner="Argus",
        correlation_id=descriptor.correlation_id,
        discriminator="argus.cash_application_correction_verification",
        body=verification_body,
        publication_ref="PUB-G07-CT1-VERIFY",
        contract_id="G-07",
        body_discriminator="G07AssuranceResult",
        publication_payload={
            "result_type": "ASSURANCE_VERIFICATION",
            "verification_ref": "VERIFY-CT1@v1",
            "verification_outcome": "PASSED",
        },
        product_ref="VERIFY-CT1@v1",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=("PUB-G08-CT1-ISSUE-V1", str(g13.publication_ref)),
    )
    issue = {
        "product_ref": "ISSUE-CT1@v2",
        "created_at": now,
        "issue_id": "ISSUE-CT1",
        "issue_version": 2,
        "prior_issue_ref": "ISSUE-CT1@v1",
        "finding_refs": ["FINDING-CT1@v1"],
        "status": "REMEDIATION_VERIFIED",
        "owner_ref": "ACTOR:CONTROLLER",
        "directive_refs": ["DIRECTIVE-CT1@v1"],
        "verification_refs": ["VERIFY-CT1@v1"],
        "updated_at": now,
    }
    _execute_product(
        boundary,
        command_id="CMD-AEGIS-CT1-UPDATE",
        owner="Aegis",
        correlation_id=descriptor.correlation_id,
        discriminator="aegis.issue",
        body=issue,
        publication_ref="PUB-G08-CT1-ISSUE-V2",
        contract_id="G-08",
        body_discriminator="G08GovernanceResult",
        publication_payload={
            "governance_result_type": "ISSUE_UPDATED",
            "issue_ref": "ISSUE-CT1@v2",
            "verification_ref": "VERIFY-CT1@v1",
            "prior_issue_ref": "ISSUE-CT1@v1",
        },
        product_ref="ISSUE-CT1@v2",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(str(verification.publication.publication_ref),),
    )


def _inventory_digest(
    boundary: SqlitePersistenceBoundary, *, semantic_as_of_time: str
) -> str:
    session = boundary.open_query(
        QueryContext(semantic_as_of_time=semantic_as_of_time)
    )
    inventory = tuple(
        sorted(
            (
                item.record_family,
                item.record_identity,
                item.semantic_hash,
            )
            for item in session.authoritative_records()
        )
    )
    return canonical_sha256(inventory)


def inspect_demo_boundary(
    boundary: SqlitePersistenceBoundary,
    scenarios: DemoScenarioSet,
) -> DemoMaterialization:
    """Derive the non-authoritative demo inventory from one loaded boundary."""

    publications = tuple(
        item
        for item in boundary.state.object_versions
        if isinstance(item, ContractPublication)
    )
    admitted_publications = boundary.open_query(
        QueryContext(semantic_as_of_time=str(scenarios.semantic_as_of_time))
    ).authoritative_records("J-AR13")
    publication_refs = {
        str(item.publication_ref) for item in publications
    } | {item.record_identity for item in admitted_publications}
    return DemoMaterialization(
        scenario_refs=(
            str(scenarios.c001.scenario_ref),
            str(scenarios.ct1.scenario_ref),
        ),
        scenario_set_digest=canonical_sha256(scenarios.model_dump(mode="json")),
        authoritative_inventory_digest=_inventory_digest(
            boundary,
            semantic_as_of_time=str(scenarios.semantic_as_of_time),
        ),
        semantic_state_digest=boundary.state.full_digest,
        query_revision=boundary.revision,
        event_count=len(boundary.state.event_log),
        publication_count=len(publication_refs),
        projection_generation_ref=f"J-P04@r{boundary.revision}",
    )


def materialize_demo(
    database: Path,
    scenarios: DemoScenarioSet,
) -> DemoMaterialization:
    """Build the two Artifact O families through ordinary runtime boundaries."""

    c001 = build_c001_scenario(scenarios.c001)
    ct1 = build_ct1_scenario(scenarios.ct1)
    module_evidence = EvidenceRef(
        ref_id="EVD-DEMO-MODULE",
        description="Deterministic synthetic module execution evidence",
        content_hash=canonical_sha256(
            {
                "scenario_set_digest": canonical_sha256(
                    scenarios.model_dump(mode="json")
                ),
                "synthetic": True,
            }
        ),
    )
    boundary = _admit_baseline(database, scenarios, c001, ct1, module_evidence)
    try:
        g13 = _admit_referenced_journal(boundary, ct1, module_evidence)
        assert c001.workflow.business_event is not None
        _publish_business_event(
            boundary,
            c001.workflow.business_event,
            semantic_as_of_time=str(scenarios.semantic_as_of_time),
        )
        c001_service = AccountingApplicationService(
            boundary,
            ScriptedIdentityGenerator(
                {
                    "constructor_command": (
                        "CMD-DEMO-C001-CONSTRUCT-1",
                        "CMD-DEMO-C001-CONSTRUCT-2",
                    )
                }
            ),
        )
        c001_service.execute_segment(c001.workflow, start=0, stop=3)
        _import_predecessor(boundary, c001, scenarios, module_evidence)
        _c001_pre_correction_chain(boundary, scenarios, module_evidence)
        c001_service.execute_segment(c001.workflow, start=3, stop=None)
        _c001_post_correction_chain(boundary, scenarios, module_evidence)

        _ct1_pre_correction_chain(boundary, scenarios, module_evidence, g13)
        AccountingApplicationService(
            boundary,
            ScriptedIdentityGenerator(
                {
                    "constructor_command": (
                        "CMD-DEMO-CT1-CONSTRUCT-1",
                        "CMD-DEMO-CT1-CONSTRUCT-2",
                    )
                }
            ),
        ).execute_workflow(ct1.workflow)
        _ct1_post_correction_chain(boundary, scenarios, module_evidence, g13)

        return inspect_demo_boundary(boundary, scenarios)
    finally:
        boundary.close()


def _publish_business_event(
    boundary: SqlitePersistenceBoundary,
    event: BusinessEvent,
    *,
    semantic_as_of_time: str,
) -> ContractPublication:
    assessment = CandidateAdmissionService(boundary).assess(
        CandidateAssessmentCommand(
            command_contract_version=1,
            command_id="CMD-DEMO-HERMES-ASSESS-C001",
            actor_ref="ACTOR:HERMES",
            correlation_id=str(event.correlation_id),
            semantic_as_of_time=semantic_as_of_time,
            candidate_receipt_ref=f"J-AR01:{event.business_event_id}",
            admission_product_ref=f"ADM-{event.business_event_id}@v1",
            publication_ref="PUB-G02-C001",
            candidate_contract_version="1",
            candidate_type=str(event.event_type),
            canonical_candidate_body=event.model_dump(mode="json"),
            source_domain_ref=f"SOURCE:{event.source_system}",
            source_record_ref=str(event.payload.recognition_schedule_ref.object_id),
            received_at=str(event.recorded_at),
            assessed_at=semantic_as_of_time,
            evidence_refs=event.evidence_refs,
        )
    )
    evidence_refs = tuple(
        AuthoritativeRef(
            record_family="J-AR12",
            record_identity=str(item.ref_id),
            semantic_hash=value_digest(item),
        )
        for item in event.evidence_refs
    )
    publication = ContractPublication.command(
        publication_ref="PUB-G01-C001",
        contract_id="G-01",
        body_discriminator="business_event",
        publisher="SharedSubstrate",
        product_ref=str(event.business_event_id),
        payload=event.model_dump(mode="json"),
        command_owner="SharedSubstrate",
        command_id="CMD-DEMO-SUBSTRATE-PUBLISH-C001",
        evidence_refs=evidence_refs,
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
            command_id="CMD-DEMO-SUBSTRATE-PUBLISH-C001",
            command_owner="SharedSubstrate",
            command_type="PublishAdmittedBusinessEvent",
            actor_ref="ACTOR:SUBSTRATE",
            correlation_id=str(event.correlation_id),
            semantic_as_of_time=semantic_as_of_time,
            authoritative_creations=(event,),
            publications=(publication,),
            consumed_publication_refs=(str(assessment.publication.publication_ref),),
        )
    )
    return publication


def _import_predecessor(
    boundary: SqlitePersistenceBoundary,
    scenario: BuiltScenario,
    scenarios: DemoScenarioSet,
    module_evidence: EvidenceRef,
) -> ContractPublication:
    content = scenario.reporting_content[0]
    descriptor = scenarios.c001
    reporting_ref = f"{descriptor.reporting_version_id}@v1"
    published_at = "2026-07-10T18:30:00Z"
    available_from = "2026-07-11T12:00:00Z"
    body = {
        "contract_version": 1,
        "reporting_version_id": descriptor.reporting_version_id,
        "period_id": descriptor.reporting_period_id,
        "version": 1,
        "reporting_version_ref": reporting_ref,
        "content_ref": str(content.content_ref),
        "content_hash": str(content.content_hash),
        "content_schema_version": 1,
        "publication_origin": "PRE_SCOPE_IMPORT",
        "published_at": published_at,
    }
    evidence_refs = _module_evidence(module_evidence)
    payload = {
        "reporting_version_ref": reporting_ref,
        "period_id": descriptor.reporting_period_id,
        "content_ref": str(content.content_ref),
        "content_hash": str(content.content_hash),
        "content_schema_version": 1,
        "publication_origin": "PRE_SCOPE_IMPORT",
        "published_at": published_at,
        "import_attestation_ref": "J-AR11:IMPORT-C001-V1",
        "original_authority_ref": "AUTHORITY:CFO",
        "source_ref": "ARCHIVE:RV-2026-06@v1",
    }
    publication = ContractPublication(
        publication_ref="PUB-G06-C001-V1",
        contract_id="G-06",
        g_contract_version="G-v0.2",
        body_contract_version=1,
        body_discriminator="G06ReportingVersion",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        publisher="Atlas",
        product_ref=reporting_ref,
        product_state_token=None,
        canonical_payload=payload,
        payload_hash=canonical_sha256(payload),
        upstream_publication_refs=(),
        upstream_authoritative_refs=(
            _exact_authority("J-AR10", reporting_ref, canonical_sha256(body)),
        ),
        evidence_refs=evidence_refs,
        available_from=available_from,
        publication_basis=ImportPublicationBasis(
            basis_type="PRE_SCOPE_IMPORT",
            import_attestation_ref="J-AR11:IMPORT-C001-V1",
        ),
    )
    candidate_body = {"candidate_ref": reporting_ref}
    candidate = canonical_bytes(candidate_body)
    context = ImportContext(
        import_id="IMPORT-C001-V1",
        imported_reporting_version_ref=reporting_ref,
        sealed_candidate_contract_version="1",
        sealed_candidate_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        sealed_candidate_hash=canonical_sha256(candidate_body),
        semantic_as_of_time="2026-07-11T09:00:00Z",
        importer_ref="REPORTING-SERVICE",
    )
    period = boundary.state.snapshot.period(descriptor.reporting_period_id)
    if period is None or period.status != "HARD_CLOSED":
        raise RuntimeError("pre-scope reporting import requires the hard close")
    close_hash = value_digest(period)
    core_record = _sealed_record("J-AR10", reporting_ref, body, owner="ATLAS")
    attestation = {
        "import_id": "IMPORT-C001-V1",
        "imported_object_type": "reporting_version",
        "reporting_version_ref": reporting_ref,
        "canonical_core_hash": core_record.semantic_hash,
        "content_ref": str(content.content_ref),
        "content_hash": str(content.content_hash),
        "content_schema_version": 1,
        "prerequisite_period_id": descriptor.reporting_period_id,
        "prerequisite_close_event_id": "AE-C001-003",
        "prerequisite_close_view_hash": close_hash,
        "original_published_at": published_at,
        "available_from": available_from,
        "original_authority_ref": "AUTHORITY:CFO",
        "source_ref": "ARCHIVE:RV-2026-06@v1",
        "imported_at": "2026-07-11T09:00:00Z",
        "imported_by": "REPORTING-SERVICE",
        "import_command_or_manifest_ref": "IMPORT-C001-V1",
        "evidence_refs": [item.model_dump(mode="json") for item in evidence_refs],
    }
    unit = boundary.begin_pre_scope_reporting_import(context)
    unit.stage_bundle(
        PreScopeReportingImportBundle(
            declared_records=(
                core_record,
                _sealed_record("J-AR11", "IMPORT-C001-V1", attestation),
                _sealed_record(
                    "J-AR12",
                    str(content.content_ref),
                    content.model_dump(mode="json"),
                ),
                _sealed_record(
                    "J-AR13",
                    str(publication.publication_ref),
                    publication.model_dump(mode="json"),
                    owner="ATLAS",
                ),
            ),
            sealed_candidate_body=candidate,
            prerequisite_period_ref=descriptor.reporting_period_id,
            prerequisite_close_event_ref="AE-C001-003",
            prerequisite_close_view_hash=close_hash,
        )
    )
    unit.commit(unit.validate())
    return publication


@dataclass(frozen=True, slots=True)
class _ProductPublication:
    product: ValidatedModuleProduct
    publication: ContractPublication


def _publication(
    boundary: SqlitePersistenceBoundary,
    publication_ref: str,
) -> ContractPublication:
    match = next(
        (
            item
            for item in boundary.state.object_versions
            if isinstance(item, ContractPublication)
            and str(item.publication_ref) == publication_ref
        ),
        None,
    )
    if match is not None:
        return match
    session = boundary.open_query(
        QueryContext(semantic_as_of_time="2026-07-14T12:00:00Z")
    )
    stored = session.authoritative_record("J-AR13", publication_ref)
    if stored is None:
        raise RuntimeError(f"required publication is unavailable: {publication_ref}")
    return ContractPublication.model_validate(stored.semantic_body())


def _find_publication(
    boundary: SqlitePersistenceBoundary,
    *,
    contract_id: str,
    product_ref: str,
) -> ContractPublication:
    matches = tuple(
        item
        for item in boundary.state.object_versions
        if isinstance(item, ContractPublication)
        and item.contract_id == contract_id
        and str(item.product_ref) == product_ref
    )
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one {contract_id} publication for {product_ref}, "
            f"found {len(matches)}"
        )
    return matches[0]


def _execute_product(
    boundary: SqlitePersistenceBoundary,
    *,
    command_id: str,
    owner: ModuleOwner,
    correlation_id: str,
    discriminator: str,
    body: dict[str, object],
    publication_ref: str,
    contract_id: str,
    body_discriminator: str,
    publication_payload: dict[str, object],
    product_ref: str,
    module_evidence: EvidenceRef,
    semantic_as_of_time: str,
    consumed: tuple[str, ...] = (),
    companions: tuple[tuple[str, dict[str, object]], ...] = (),
) -> _ProductPublication:
    evidence_refs = _module_evidence(module_evidence)
    upstream = tuple(_publication(boundary, item).exact_ref() for item in consumed)
    product = ValidatedModuleProduct.command(
        product_discriminator=discriminator,
        owner=owner,
        body=body,
        command_id=command_id,
        evidence_refs=evidence_refs,
        available_from=semantic_as_of_time,
        upstream_publication_refs=upstream,
    )
    publication = ContractPublication.command(
        publication_ref=publication_ref,
        contract_id=contract_id,  # type: ignore[arg-type]
        body_discriminator=body_discriminator,
        publisher=owner,  # type: ignore[arg-type]
        product_ref=product_ref,
        payload=publication_payload,
        command_owner=owner,
        command_id=command_id,
        evidence_refs=evidence_refs,
        available_from=semantic_as_of_time,
        upstream_publication_refs=upstream,
    )
    companion_products = tuple(
        ValidatedModuleProduct.command(
            product_discriminator=companion_discriminator,
            owner=owner,
            body=companion_body,
            command_id=command_id,
            evidence_refs=evidence_refs,
            available_from=semantic_as_of_time,
            upstream_publication_refs=upstream,
        )
        for companion_discriminator, companion_body in companions
    )
    ModuleContractService(boundary).execute(
        ModuleCommand(
            command_id=command_id,
            command_owner=owner,
            command_type=discriminator,
            actor_ref=f"ACTOR:{owner.upper()}",
            correlation_id=correlation_id,
            semantic_as_of_time=semantic_as_of_time,
            products=(*companion_products, product),
            publications=(publication,),
            consumed_publication_refs=consumed,
        )
    )
    return _ProductPublication(product, publication)


def _c001_pre_correction_chain(
    boundary: SqlitePersistenceBoundary,
    scenarios: DemoScenarioSet,
    module_evidence: EvidenceRef,
) -> tuple[
    _ProductPublication,
    _ProductPublication,
    _ProductPublication,
    _ProductPublication,
]:
    descriptor = scenarios.c001
    now = "2026-07-11T18:00:00Z"
    reconciliation_body = {
        "product_ref": "RECON-C001@v1",
        "reconciliation_type": "RECOGNITION_POPULATION",
        "scope_ref": f"CONTRACT:{descriptor.contract_id}",
        "result": "FAILED",
        "performed_at": now,
        "period_id": descriptor.reporting_period_id,
        "recognition_schedule_ref": f"SCHEDULE:{descriptor.recognition_schedule_id}@v1",
        "expected_item_count": 12,
        "expected_amount_minor": descriptor.annual_invoice_minor,
        "posted_item_count": 11,
        "posted_amount_minor": (
            descriptor.annual_invoice_minor - descriptor.monthly_revenue_minor
        ),
        "submitted_unposted_count": 1,
        "deferred_count": 1,
        "difference_minor": descriptor.monthly_revenue_minor,
        "currency": descriptor.currency,
    }
    g03 = _execute_product(
        boundary,
        command_id="CMD-HERMES-C001-RECON",
        owner="Hermes",
        correlation_id=descriptor.correlation_id,
        discriminator="hermes.recognition_population_reconciliation",
        body=reconciliation_body,
        publication_ref="PUB-G03-C001",
        contract_id="G-03",
        body_discriminator="G03ReconciliationResult",
        publication_payload=reconciliation_body,
        product_ref="RECON-C001@v1",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
    )
    exception_body = {
        "product_ref": "EXC-C001@v1",
        "created_at": now,
        "test_run_ref": "TEST-C001@v1",
        "assertion": "COMPLETENESS",
        "severity": "BLOCKING",
        "subject_refs": [_product_authority(g03.product)],
        "expected_amount_minor": descriptor.monthly_revenue_minor,
        "actual_amount_minor": 0,
        "difference_minor": descriptor.monthly_revenue_minor,
        "currency": descriptor.currency,
        "period_id": descriptor.reporting_period_id,
        "status": "OPEN",
    }
    g07 = _execute_product(
        boundary,
        command_id="CMD-ARGUS-C001-TEST",
        owner="Argus",
        correlation_id=descriptor.correlation_id,
        discriminator="argus.recognition_completeness_exception",
        body=exception_body,
        publication_ref="PUB-G07-C001-EXCEPTION",
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
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(str(g03.publication.publication_ref),),
        companions=(
            (
                "argus.recognition_completeness_test_run",
                {
                    "product_ref": "TEST-C001@v1",
                    "created_at": now,
                    "test_definition_ref": "J-AR04:TEST-REVENUE-COMPLETENESS@v1",
                    "reconciliation_ref": "RECON-C001@v1",
                    "period_id": descriptor.reporting_period_id,
                    "population_refs": [_product_authority(g03.product)],
                    "population_hashes": [str(g03.product.semantic_hash)],
                    "executed_at": now,
                    "outcome": "FAILED",
                    "exception_ref": "EXC-C001@v1",
                },
            ),
        ),
    )
    issue_body = {
        "product_ref": "ISSUE-C001@v1",
        "created_at": now,
        "issue_id": "ISSUE-C001",
        "issue_version": 1,
        "finding_refs": ["FINDING-C001@v1"],
        "status": "OPEN",
        "owner_ref": "ACTOR:CONTROLLER",
        "directive_refs": [],
        "verification_refs": [],
        "updated_at": now,
    }
    g08 = _execute_product(
        boundary,
        command_id="CMD-AEGIS-C001-GOVERN",
        owner="Aegis",
        correlation_id=descriptor.correlation_id,
        discriminator="aegis.issue",
        body=issue_body,
        publication_ref="PUB-G08-C001-ISSUE-V1",
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
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(str(g07.publication.publication_ref),),
        companions=(
            (
                "aegis.exception_review",
                {
                    "product_ref": "REVIEW-C001@v1",
                    "created_at": now,
                    "exception_ref": "EXC-C001@v1",
                    "review_outcome": "CONFIRMED",
                    "reviewed_by": "ACTOR:CONTROLLER",
                    "reviewed_at": now,
                    "conclusion_code": "POLICY-CONCLUSION@v1",
                },
            ),
            (
                "aegis.finding",
                {
                    "product_ref": "FINDING-C001@v1",
                    "created_at": now,
                    "review_ref": "REVIEW-C001@v1",
                    "finding_type": "RECOGNITION_OMISSION",
                    "assertion": "COMPLETENESS",
                    "affected_refs": [_product_authority(g07.product)],
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
        "affected_period_id": descriptor.reporting_period_id,
        "eligible_correction_period_id": descriptor.correction_period_id,
        "policy_ref": "J-AR04:POL-RESTATEMENT@v1",
        "requested_by": {"actor_type": "PERSON", "actor_id": "CFO"},
        "requested_at": now,
    }
    g09 = _execute_product(
        boundary,
        command_id="CMD-AEGIS-C001-DIRECT",
        owner="Aegis",
        correlation_id=descriptor.correlation_id,
        discriminator="aegis.remediation_directive",
        body=directive_body,
        publication_ref="PUB-G09-C001",
        contract_id="G-09",
        body_discriminator="G09RemediationDirective",
        publication_payload=directive_body,
        product_ref="DIRECTIVE-C001@v1",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(str(g08.publication.publication_ref),),
    )
    return g03, g07, g08, g09


def _c001_post_correction_chain(
    boundary: SqlitePersistenceBoundary,
    scenarios: DemoScenarioSet,
    module_evidence: EvidenceRef,
) -> None:
    descriptor = scenarios.c001
    now = str(descriptor.semantic_as_of_time)
    v2_ref = f"{descriptor.reporting_version_id}@v2"
    g06 = _find_publication(boundary, contract_id="G-06", product_ref=v2_ref)
    verification_body = {
        "product_ref": "VERIFY-C001@v1",
        "created_at": now,
        "verification_type": "RESTATEMENT_CORRECTION",
        "journal_ref": f"J-AR08:{descriptor.correction_journal_id}",
        "manifest_ref": f"J-AR02:{descriptor.restatement_case_id}:PUBLISHED",
        "predecessor_reporting_ref": f"{descriptor.reporting_version_id}@v1",
        "successor_reporting_ref": v2_ref,
        "reporting_publication_ref": str(g06.publication_ref),
        "check_results": {
            "journal_balanced": True,
            "manifest_reconciled": True,
            "predecessor_preserved": True,
            "successor_content_verified": True,
        },
        "outcome": "PASSED",
    }
    verification = _execute_product(
        boundary,
        command_id="CMD-ARGUS-C001-VERIFY",
        owner="Argus",
        correlation_id=descriptor.correlation_id,
        discriminator="argus.restatement_verification",
        body=verification_body,
        publication_ref="PUB-G07-C001-VERIFY",
        contract_id="G-07",
        body_discriminator="G07AssuranceResult",
        publication_payload={
            "result_type": "ASSURANCE_VERIFICATION",
            "verification_ref": "VERIFY-C001@v1",
            "verification_outcome": "PASSED",
        },
        product_ref="VERIFY-C001@v1",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(str(g06.publication_ref),),
    )
    successor_issue = {
        "product_ref": "ISSUE-C001@v2",
        "created_at": now,
        "issue_id": "ISSUE-C001",
        "issue_version": 2,
        "prior_issue_ref": "ISSUE-C001@v1",
        "finding_refs": ["FINDING-C001@v1"],
        "status": "REMEDIATION_VERIFIED",
        "owner_ref": "ACTOR:CONTROLLER",
        "directive_refs": ["DIRECTIVE-C001@v1"],
        "verification_refs": ["VERIFY-C001@v1"],
        "updated_at": now,
    }
    issue_update = _execute_product(
        boundary,
        command_id="CMD-AEGIS-C001-UPDATE",
        owner="Aegis",
        correlation_id=descriptor.correlation_id,
        discriminator="aegis.issue",
        body=successor_issue,
        publication_ref="PUB-G08-C001-ISSUE-V2",
        contract_id="G-08",
        body_discriminator="G08GovernanceResult",
        publication_payload={
            "governance_result_type": "ISSUE_UPDATED",
            "issue_ref": "ISSUE-C001@v2",
            "verification_ref": "VERIFY-C001@v1",
            "prior_issue_ref": "ISSUE-C001@v1",
        },
        product_ref="ISSUE-C001@v2",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(str(verification.publication.publication_ref),),
    )
    readiness_body = {
        "product_ref": "READY-C001@v1",
        "reporting_version_ref": v2_ref,
        "reporting_publication_ref": str(g06.publication_ref),
        "period_id": descriptor.reporting_period_id,
        "scope_ref": "NEXUS-GROUP",
        "purpose_ref": "HIRING-FORECAST",
        "status": "APPROVED",
        "basis_refs": [_publication_authority(g06)],
        "limitation_codes": [],
        "assessed_by": {"actor_type": "PERSON", "actor_id": "CFO"},
        "assessed_at": now,
    }
    readiness = _execute_product(
        boundary,
        command_id="CMD-AEGIS-C001-READY",
        owner="Aegis",
        correlation_id=descriptor.correlation_id,
        discriminator="aegis.readiness_assessment",
        body=readiness_body,
        publication_ref="PUB-G10-C001",
        contract_id="G-10",
        body_discriminator="G10ReadinessAssessment",
        publication_payload=readiness_body,
        product_ref="READY-C001@v1",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(
            str(g06.publication_ref),
            str(issue_update.publication.publication_ref),
        ),
    )
    planning_body = {
        "product_ref": "PLAN-C001@v1",
        "reporting_version_ref": v2_ref,
        "reporting_publication_ref": str(g06.publication_ref),
        "readiness_ref": "READY-C001@v1",
        "readiness_publication_ref": str(readiness.publication.publication_ref),
        "purpose_ref": "HIRING-FORECAST",
        "period_id": descriptor.reporting_period_id,
        "scope_ref": "NEXUS-GROUP",
        "assumption_refs": ["J-AR04:ASSUMPTIONS@v1"],
        "exclusion_refs": [],
        "frozen_at": now,
    }
    planning = _execute_product(
        boundary,
        command_id="CMD-PYTHIA-C001-FREEZE",
        owner="Pythia",
        correlation_id=descriptor.correlation_id,
        discriminator="pythia.planning_input_snapshot",
        body=planning_body,
        publication_ref="PUB-G11-C001",
        contract_id="G-11",
        body_discriminator="G11PlanningInputSnapshot",
        publication_payload=planning_body,
        product_ref="PLAN-C001@v1",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(str(g06.publication_ref), str(readiness.publication.publication_ref)),
    )
    decision_body = {
        "product_ref": "DECISION-C001@v1",
        "decision_type": "HIRING_DEFERRED",
        "planning_snapshot_ref": "PLAN-C001@v1",
        "planning_publication_ref": str(planning.publication.publication_ref),
        "position_ref": "POSITION-CS-014",
        "original_start_date": "2026-08-01",
        "recommended_start_date": "2026-09-01",
        "monthly_cost_minor": 650_000,
        "currency": descriptor.currency,
        "reason_code": "ACTUALS_READINESS_DELAY",
        "produced_at": now,
    }
    decision = _execute_product(
        boundary,
        command_id="CMD-PYTHIA-C001-DECIDE",
        owner="Pythia",
        correlation_id=descriptor.correlation_id,
        discriminator="pythia.governed_decision",
        body=decision_body,
        publication_ref="PUB-G12-C001",
        contract_id="G-12",
        body_discriminator="G12GovernedDecision",
        publication_payload=decision_body,
        product_ref="DECISION-C001@v1",
        module_evidence=module_evidence,
        semantic_as_of_time=now,
        consumed=(str(planning.publication.publication_ref),),
    )
    approval_body = {
        "product_ref": "APPROVAL-C001-HIRING@v1",
        "created_at": now,
        "decision_ref": "DECISION-C001@v1",
        "decision_publication_ref": str(decision.publication.publication_ref),
        "outcome": "APPROVED",
        "decided_by": "ACTOR:OPERATIONS",
        "decided_at": now,
        "approval_policy_ref": "J-AR04:POLICY-HIRING@v1",
        "candidate_ref": "CANDIDATE-C001-HIRING@v1",
    }
    candidate_body = {
        "product_ref": "CANDIDATE-C001-HIRING@v1",
        "created_at": now,
        "candidate_type": "workforce.hiring.deferred",
        "source_domain_ref": "SOURCE:WORKFORCE",
        "decision_ref": "DECISION-C001@v1",
        "approval_ref": "APPROVAL-C001-HIRING@v1",
        "correlation_id": descriptor.correlation_id,
        "occurred_at": now,
        "recorded_at": now,
        "effective_date": "2026-08-01",
        "position_ref": "POSITION-CS-014",
        "original_start_date": "2026-08-01",
        "revised_start_date": "2026-09-01",
        "monthly_cost_minor": 650_000,
        "currency": descriptor.currency,
        "reason_code": "ACTUALS_READINESS_DELAY",
    }
    evidence_refs = _module_evidence(module_evidence)
    upstream = (decision.publication.exact_ref(),)
    approval = ValidatedModuleProduct.command(
        product_discriminator="source.operational_decision_approval",
        owner="SourceDomain",
        body=approval_body,
        command_id="CMD-SOURCE-C001-APPROVE",
        evidence_refs=evidence_refs,
        available_from=now,
        upstream_publication_refs=upstream,
    )
    candidate = ValidatedModuleProduct.command(
        product_discriminator="source.business_event_candidate",
        owner="SourceDomain",
        body=candidate_body,
        command_id="CMD-SOURCE-C001-APPROVE",
        evidence_refs=evidence_refs,
        available_from=now,
        upstream_publication_refs=upstream,
    )
    ModuleContractService(boundary).execute(
        ModuleCommand(
            command_id="CMD-SOURCE-C001-APPROVE",
            command_owner="SourceDomain",
            command_type="ApproveOperationalDecision",
            actor_ref="ACTOR:OPERATIONS",
            correlation_id=descriptor.correlation_id,
            semantic_as_of_time=now,
            products=(approval, candidate),
            consumed_publication_refs=(str(decision.publication.publication_ref),),
        )
    )
    CandidateAdmissionService(boundary).assess(
        CandidateAssessmentCommand(
            command_contract_version=1,
            command_id="CMD-HERMES-C001-ASSESS-DECISION-CANDIDATE",
            actor_ref="ACTOR:HERMES",
            correlation_id=descriptor.correlation_id,
            semantic_as_of_time=now,
            candidate_receipt_ref="J-AR01:CANDIDATE-C001-HIRING@v1",
            admission_product_ref="ADM-CANDIDATE-C001-HIRING@v1",
            publication_ref="PUB-G02-C001-HIRING-CANDIDATE",
            candidate_contract_version="1",
            candidate_type="workforce.hiring.deferred",
            canonical_candidate_body=candidate_body,
            source_domain_ref="SOURCE:WORKFORCE",
            source_record_ref="CANDIDATE-C001-HIRING@v1",
            received_at=now,
            assessed_at=now,
            approval_ref="APPROVAL-C001-HIRING@v1",
            evidence_refs=(module_evidence,),
        )
    )


def _admit_referenced_journal(
    boundary: SqlitePersistenceBoundary,
    scenario: BuiltScenario,
    module_evidence: EvidenceRef,
) -> ContractPublication:
    projection = scenario.referenced_journal
    source_body = scenario.referenced_source_body
    if projection is None or source_body is None:
        raise ValueError("CT-1 requires one referenced source journal")
    source = _sealed_record(
        "J-AR17", projection.journal_id, source_body, owner="ATLAS"
    )
    if source.semantic_hash != projection.source_hash:
        raise ValueError("referenced source hash and projection are inconsistent")
    payload = projection.model_dump(mode="json", exclude={"fixture_id"})
    evidence_refs = _module_evidence(module_evidence)
    publication = ContractPublication(
        publication_ref="PUB-G13-CT1-J010",
        contract_id="G-13",
        g_contract_version="G-v0.2",
        body_contract_version=1,
        body_discriminator="G13ReferencedJournal",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        publisher="AtlasReadBoundary",
        product_ref=f"{projection.journal_id}@v1",
        product_state_token=None,
        canonical_payload=payload,
        payload_hash=canonical_sha256(payload),
        upstream_publication_refs=(),
        upstream_authoritative_refs=(
            _exact_authority("J-AR17", projection.journal_id, source.semantic_hash),
        ),
        evidence_refs=evidence_refs,
        available_from="2026-07-11T08:00:00Z",
        publication_basis=ReferencedJournalPublicationBasis(
            basis_type="REFERENCED_JOURNAL_ADMISSION",
            referenced_source_ref=projection.journal_id,
            admission_identity=projection.journal_id,
        ),
    )
    context = ReferencedJournalContext(
        source_journal_ref=projection.journal_id,
        source_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        source_hash=source.semantic_hash,
        source_contract_version="1",
        semantic_as_of_time="2026-07-11T08:00:00Z",
        admitting_actor_ref="HERMES",
    )
    unit = boundary.begin_referenced_journal_admission(context)
    unit.stage_bundle(
        ReferencedJournalAdmissionBundle(
            declared_records=(
                source,
                _sealed_record(
                    "J-AR13",
                    str(publication.publication_ref),
                    publication.model_dump(mode="json"),
                    owner="ATLAS",
                ),
            ),
            canonical_source_body=source.canonical_payload,
            provenance_body=canonical_bytes(
                {"source_system": "SYNTHETIC-LEGACY-LEDGER", "verified": True}
            ),
        )
    )
    unit.commit(unit.validate())
    return publication
