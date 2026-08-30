"""Phase 4 parameterised application-service acceptance proofs."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from finance_assurance.acceptance.runtime_proof import admit_runtime
from finance_assurance.runtime.application.contracts import (
    InMemoryObservationSink,
    ModuleContractService,
)
from finance_assurance.runtime.application.models import (
    AccountingWorkflow,
    EventCreations,
    ProposalTreatmentVersion,
    ScriptedClock,
    ScriptedIdentityGenerator,
)
from finance_assurance.runtime.application.publications import (
    AtlasPublicationClosureError,
)
from finance_assurance.runtime.application.service import AccountingApplicationService
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256
from finance_assurance.runtime.contracts.module import ContractPublication
from finance_assurance.runtime.contracts.objects import (
    AccountingPeriodBase,
    BusinessEvent,
    JournalEntryBase,
    JournalLine,
    JournalProposalBase,
    ReportingVersion,
    RestatementCaseBase,
)
from finance_assurance.runtime.persistence.codec import durable_hash, encode_durable
from finance_assurance.runtime.persistence.models import (
    AdmissionBundle,
    BaselineContext,
    ProjectionReplacement,
    RebuildContext,
    SealedAdmissionRecord,
)
from finance_assurance.runtime.persistence.sqlite import SqlitePersistenceBoundary
from finance_assurance.runtime.persistence.state import InMemoryState
from finance_assurance.validation.h2 import run_h2
from finance_assurance.validation.scenarios import replay_c001, replay_ct1


def _sealed(family: str, identity: str) -> SealedAdmissionRecord:
    payload = canonical_bytes({"identity": identity})
    return SealedAdmissionRecord(
        record_family=family,
        record_identity=identity,
        semantic_owner="PLATFORM",
        contract_version="1",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        semantic_hash=durable_hash(payload),
        canonical_payload=payload,
    )


def _admit(path: Path, state: InMemoryState) -> SqlitePersistenceBoundary:
    return admit_runtime(path, state)

    boundary = SqlitePersistenceBoundary(path)
    encoded_snapshot = encode_durable(state.snapshot)
    projection_ref = "BASELINE-PHASE4:J-P04"
    projection_hash = durable_hash(encoded_snapshot)
    manifest = {
        "contract_version": 1,
        "manifest_ref": "BASELINE-PHASE4",
        "projection_ref": projection_ref,
        "projection_hash": projection_hash,
        "predecessor_event_refs": sorted(state.known_predecessor_event_ids),
    }
    context = BaselineContext(
        baseline_manifest_ref="BASELINE-PHASE4",
        baseline_manifest_contract_version="1",
        baseline_manifest_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        baseline_manifest_hash=canonical_sha256(manifest),
        semantic_as_of_time="2026-06-01T00:00:00Z",
        admitting_actor_ref="PHASE4-TEST",
    )
    projection = encoded_snapshot
    index = run_h2().index
    evidence = {
        str(ref.ref_id): ref
        for validated in (*index.canonical_objects, *index.events)
        for ref in getattr(validated.value, "evidence_refs", ())
    }
    bundle = AdmissionBundle(
        declared_records=(
            SealedAdmissionRecord(
                record_family="J-AR04",
                record_identity=context.baseline_manifest_ref,
                semantic_owner="PLATFORM",
                contract_version="1",
                canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
                semantic_hash=context.baseline_manifest_hash,
                canonical_payload=canonical_bytes(manifest),
            ),
            *tuple(
                _sealed("J-AR12", event_id)
                for event_id in sorted(state.known_predecessor_event_ids)
            ),
            *tuple(
                SealedAdmissionRecord(
                    record_family="J-AR12",
                    record_identity=str(item.ref_id),
                    semantic_owner="PLATFORM",
                    contract_version="1",
                    canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
                    semantic_hash=canonical_sha256(item.model_dump(mode="json")),
                    canonical_payload=canonical_bytes(item.model_dump(mode="json")),
                )
                for item in evidence.values()
            ),
        ),
        projection_replacements=(
            ProjectionReplacement(
                projection_family="J-P04",
                projection_token=projection_ref,
                source_hash=projection_hash,
                canonical_payload=projection,
            ),
        ),
    )
    unit = boundary.begin_runtime_baseline_admission(context)
    unit.stage_bundle(bundle)
    unit.commit(unit.validate())
    return boundary


def _workflow(name: str) -> tuple[AccountingWorkflow, InMemoryState, InMemoryState]:
    index = run_h2().index
    replay = replay_c001(index) if name == "C001" else replay_ct1(index)
    commands = replay.commands
    events = tuple(
        command.accounting_event
        for command in commands
        if command.accounting_event is not None
    )
    proposal_objects = {
        item.proposal_ref: item
        for command in commands
        for item in command.immutable_creations
        if isinstance(item, JournalProposalBase)
    }
    refs = (
        ("P-551@v1", "P-551@v2")
        if name == "C001"
        else ("P-REV-010@v1", "P-REP-010@v1")
    )
    treatments = tuple(
        ProposalTreatmentVersion.from_proposal(
            proposal_objects[ref]
        )
        for ref in refs
    )
    creation_bundles = []
    for command in commands:
        event = command.accounting_event
        values = tuple(
            item
            for item in command.immutable_creations
            if isinstance(
                item,
                (
                    AccountingPeriodBase,
                    JournalEntryBase,
                    JournalLine,
                    ReportingVersion,
                    RestatementCaseBase,
                ),
            )
        )
        if event is not None and values:
            creation_bundles.append(EventCreations(str(event.event_id), values))
    business_event = next(
        (
            item
            for item in replay.initial_state.object_versions
            if isinstance(item, BusinessEvent)
        ),
        None,
    )
    workflow = AccountingWorkflow(
        family=name,  # type: ignore[arg-type]
        correlation_id=name.replace("001", "-001").replace("CT1", "CT-1"),
        treatments=treatments,
        event_templates=events,
        creations=tuple(creation_bundles),
        business_event=business_event,
    )
    return workflow, replay.initial_state, replay.state


def test_mandatory_artifact_g_publication_closure_is_atomic(
    tmp_path: Path,
) -> None:
    workflow, initial, _ = _workflow("C001")
    database = tmp_path / "atomic-g05.sqlite3"
    boundary = _admit(database, initial)
    sink = InMemoryObservationSink()
    contracts = ModuleContractService(boundary, observations=sink)
    service = AccountingApplicationService(
        boundary,
        ScriptedIdentityGenerator(
            {
                "constructor_command": (
                    "CMD-C001-CONSTRUCT-AUTO",
                    "CMD-C001-CONSTRUCT-RESTATEMENT",
                )
            }
        ),
        contracts,
    )
    execution = service.execute_workflow(workflow)
    transitions = tuple(
        item
        for item in execution.outcomes
        if getattr(item.result, "accounting_event", None) is not None
    )
    assert len(transitions) == 11
    for transition in transitions:
        assert transition.receipt is not None
        event = transition.result.accounting_event
        expected_count = 3 if event.event_type in {
            "journal.posted",
            "reporting_version.published",
        } else 2
        assert len(transition.receipt.committed_publication_refs) == expected_count
        assert any(
            item.record_family == "J-AR06"
            for item in transition.receipt.committed_authoritative_refs
        )
    assert {item.contract_id for item in sink.observations} == {
        "G-04",
        "G-05",
        "G-06",
    }
    digest = boundary.state.full_digest
    boundary.close()

    restarted = SqlitePersistenceBoundary(database)
    assert restarted.state.full_digest == digest
    assert any(
        isinstance(item, ContractPublication)
        and item.contract_id == "G-06"
        for item in restarted.state.object_versions
    )
    restarted.close()


@pytest.mark.parametrize("defect", ["missing", "extra", "mismatch"])
def test_invalid_artifact_g_closure_cannot_mutate_the_hard_close(
    tmp_path: Path,
    defect: str,
) -> None:
    workflow, initial, _ = _workflow("C001")
    boundary = _admit(tmp_path / f"closure-{defect}.sqlite3", initial)
    service = AccountingApplicationService(
        boundary,
        ScriptedIdentityGenerator(
            {
                "constructor_command": (
                    "CMD-C001-CONSTRUCT-AUTO",
                    "CMD-C001-CONSTRUCT-RESTATEMENT",
                )
            }
        ),
    )
    service.execute_segment(workflow, start=0, stop=2)
    digest_before = boundary.state.full_digest
    revision_before = boundary.revision
    target_event_id = str(workflow.event_templates[2].event_id)
    prior_publication = next(
        item
        for item in boundary.state.object_versions
        if isinstance(item, ContractPublication)
    )

    def corrupt(bundle: EventCreations) -> EventCreations:
        if bundle.template_event_id != target_event_id:
            return bundle
        if defect == "missing":
            values = tuple(
                item
                for item in bundle.values
                if not isinstance(item, AccountingPeriodBase)
            )
        elif defect == "extra":
            values = (*bundle.values, prior_publication)
        else:
            values = tuple(
                item.model_copy(update={"period_id": "2026-07"})
                if isinstance(item, AccountingPeriodBase)
                else item
                for item in bundle.values
            )
        return replace(bundle, values=values)

    defective = replace(workflow, creations=tuple(map(corrupt, workflow.creations)))

    with pytest.raises(AtlasPublicationClosureError):
        service.execute_segment(defective, start=2, stop=3)
    assert boundary.state.full_digest == digest_before
    assert boundary.revision == revision_before
    boundary.close()


@pytest.mark.parametrize("family", ["C001", "CT1"])
def test_canonical_workflows_execute_and_rebuild_through_sqlite(
    tmp_path: Path,
    family: str,
) -> None:
    workflow, initial, expected = _workflow(family)
    boundary = _admit(tmp_path / f"{family}.sqlite3", initial)
    service = AccountingApplicationService(
        boundary,
        ScriptedIdentityGenerator(
            {"constructor_command": tuple(f"CONSTRUCT-{family}-{i}" for i in (1, 2))}
        ),
    )

    result = service.execute_workflow(workflow)

    actual_event_ids = tuple(
        str(item.event_id) for item in result.terminal_state.event_log
    )
    expected_event_ids = tuple(
        str(item.event_id) for item in workflow.event_templates
    )
    assert actual_event_ids == expected_event_ids
    assert result.terminal_state.snapshot == expected.snapshot
    publication_refs = {
        str(item.publication_ref)
        for item in result.terminal_state.object_versions
        if isinstance(item, ContractPublication)
    }
    assert len(publication_refs) == (24 if family == "C001" else 14)
    for treatment in workflow.treatments:
        exact = service.get_exact_proposal(
            treatment.proposal_ref,
            semantic_as_of_time="2026-07-14T12:00:00Z",
        )
        assert exact is not None
        assert exact.treatment == treatment
        assert exact.status in {"DEFERRED", "POSTED"}

    boundary.delete_projection_checkpoint()
    rebuild = boundary.open_rebuild(
        RebuildContext(
            semantic_as_of_time="2026-07-14T12:00:00Z",
            requested_projection_families=("J-P02", "J-P04", "J-P06"),
        )
    )
    generation = rebuild.begin_generation()
    candidate = rebuild.rebuild(generation)
    rebuild.promote(rebuild.validate(candidate))
    assert boundary.state.snapshot == expected.snapshot
    boundary.close()

    restarted = SqlitePersistenceBoundary(tmp_path / f"{family}.sqlite3")
    assert restarted.state.snapshot == expected.snapshot
    assert {
        str(item.publication_ref)
        for item in restarted.state.object_versions
        if isinstance(item, ContractPublication)
    } == publication_refs
    restarted.close()


@pytest.mark.parametrize(("family", "event_count"), [("C001", 11), ("CT1", 6)])
def test_noncanonical_identity_and_dual_time_binding_is_deterministic(
    tmp_path: Path,
    family: str,
    event_count: int,
) -> None:
    template, initial, _ = _workflow(family)
    event_ids = tuple(
        f"AE-{family}-NONCANON-{number:03d}"
        for number in range(1, event_count + 1)
    )
    command_ids = tuple(
        f"CMD-{family}-NONCANON-{number:03d}"
        for number in range(1, event_count + 1)
    )
    times = tuple(
        (f"2027-01-02T10:{number:02d}:00Z", f"2027-01-02T10:{number:02d}:01Z")
        for number in range(1, event_count + 1)
    )
    correlation_id = f"{family}-ACME-42"
    workflow = template.instantiate(
        clock=ScriptedClock(times),
        identities=ScriptedIdentityGenerator(
            {"accounting_event": event_ids, "command": command_ids}
        ),
        correlation_id=correlation_id,
    )
    boundary = _admit(tmp_path / f"{family}-noncanonical.sqlite3", initial)
    service = AccountingApplicationService(
        boundary,
        ScriptedIdentityGenerator(
            {
                "constructor_command": (
                    f"CMD-{family}-CONSTRUCT-1",
                    f"CMD-{family}-CONSTRUCT-2",
                )
            }
        ),
    )

    result = service.execute_workflow(workflow)

    actual_event_ids = tuple(
        str(item.event_id) for item in result.terminal_state.event_log
    )
    assert actual_event_ids == event_ids
    assert {str(item.correlation_id) for item in result.terminal_state.event_log} == {
        correlation_id
    }
    occurred_at = tuple(
        str(item.occurred_at) for item in result.terminal_state.event_log
    )
    assert occurred_at == tuple(item[0] for item in times)
    boundary.close()


def test_workflow_rejects_undeclared_lifecycle_shape() -> None:
    template, _, _ = _workflow("CT1")

    with pytest.raises(ValueError, match="exact declared accounting-event sequence"):
        AccountingWorkflow(
            family="CT1",
            correlation_id="BROKEN",
            treatments=template.treatments,
            event_templates=template.event_templates[:-1],
            creations=template.creations,
        )


def test_reversal_source_hash_is_bound_before_constructor(tmp_path: Path) -> None:
    workflow, initial, _ = _workflow("CT1")
    bad_basis = workflow.treatments[0].origin_basis.model_copy(
        update={"input_hashes": ("sha256:" + "f" * 64,)}
    )
    bad = workflow.treatments[0].model_copy(
        update={"origin_basis": bad_basis}
    )
    workflow = AccountingWorkflow(
        family="CT1",
        correlation_id=workflow.correlation_id,
        treatments=(bad, workflow.treatments[1]),
        event_templates=workflow.event_templates,
        creations=workflow.creations,
    )
    boundary = _admit(tmp_path / "bad-source.sqlite3", initial)
    service = AccountingApplicationService(
        boundary,
        ScriptedIdentityGenerator(
            {"constructor_command": ("BAD-REV", "BAD-REP")}
        ),
    )

    with pytest.raises(ValueError, match="source hash must bind"):
        service.execute_workflow(workflow)
    assert boundary.revision == 0
    boundary.close()
