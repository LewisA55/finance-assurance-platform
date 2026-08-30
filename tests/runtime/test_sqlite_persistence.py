"""Phase 3 conformance proofs for the transactional SQLite adapter."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from finance_assurance.runtime.application.contracts import (
    InMemoryObservationSink,
    ModuleContractService,
)
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256
from finance_assurance.runtime.contracts.module import (
    ContractPublication,
    ReferencedJournalPublicationBasis,
    ValidatedModuleProduct,
)
from finance_assurance.runtime.contracts.primitives import (
    AuthoritativeRef,
    EvidenceRef,
    ExactSemanticRef,
)
from finance_assurance.runtime.execution import execute
from finance_assurance.runtime.persistence.codec import durable_hash, encode_durable
from finance_assurance.runtime.persistence.memory import InvariantFailure
from finance_assurance.runtime.persistence.migrations import MIGRATIONS
from finance_assurance.runtime.persistence.models import (
    AdmissionBundle,
    BaselineContext,
    ProjectionReplacement,
    QueryContext,
    RebuildContext,
    ReferencedJournalAdmissionBundle,
    ReferencedJournalContext,
    SealedAdmissionRecord,
)
from finance_assurance.runtime.persistence.sqlite import (
    AdmissionConflict,
    DurableStateError,
    SqlitePersistenceBoundary,
)
from finance_assurance.runtime.persistence.state import InMemoryState
from finance_assurance.runtime.planner import (
    ApplyRemediationDirective,
    EvaluatePostingRule,
    StateSnapshot,
)
from finance_assurance.runtime.rejections import Rejection
from finance_assurance.validation.h2 import run_h2
from finance_assurance.validation.h3_guards import accepted_controls


def _posting_control() -> object:
    h2 = run_h2()
    assert h2.index is not None
    return next(
        item
        for item in accepted_controls(h2.index)
        if item.name == "restatement posting"
    )


def _baseline(control: object) -> InMemoryState:
    command = control.command  # type: ignore[attr-defined]
    event = command.accounting_event
    cause = getattr(event, "causation_event_id", None)
    return InMemoryState.from_snapshot(
        control.state,  # type: ignore[attr-defined]
        known_predecessor_event_ids=(
            frozenset({str(cause)}) if cause is not None else frozenset()
        ),
    )


def _admit(
    path: Path,
    state: InMemoryState,
    **kwargs: object,
) -> SqlitePersistenceBoundary:
    boundary = SqlitePersistenceBoundary(path, **kwargs)  # type: ignore[arg-type]
    context, bundle = _baseline_admission(state)
    unit = boundary.begin_runtime_baseline_admission(context)
    unit.stage_bundle(bundle)
    receipt = unit.commit(unit.validate())
    assert not receipt.replayed
    return boundary


def _baseline_admission(
    state: InMemoryState,
) -> tuple[BaselineContext, AdmissionBundle]:
    encoded_snapshot = encode_durable(state.snapshot)
    projection_ref = "BASELINE-PHASE3:J-P04"
    projection_hash = durable_hash(encoded_snapshot)
    manifest_body = {
        "contract_version": 1,
        "manifest_ref": "BASELINE-PHASE3",
        "projection_ref": projection_ref,
        "projection_hash": projection_hash,
        "predecessor_event_refs": sorted(state.known_predecessor_event_ids),
    }
    manifest_payload = canonical_bytes(manifest_body)
    manifest_hash = canonical_sha256(manifest_body)
    context = BaselineContext(
        baseline_manifest_ref="BASELINE-PHASE3",
        baseline_manifest_contract_version="1",
        baseline_manifest_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        baseline_manifest_hash=manifest_hash,
        semantic_as_of_time="2026-07-14T00:00:00Z",
        admitting_actor_ref="PHASE3-TEST",
    )
    projection_payload = encoded_snapshot
    bundle = AdmissionBundle(
        declared_records=(
            SealedAdmissionRecord(
                record_family="J-AR04",
                record_identity=context.baseline_manifest_ref,
                semantic_owner="PLATFORM",
                contract_version="1",
                canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
                semantic_hash=manifest_hash,
                canonical_payload=manifest_payload,
            ),
            *tuple(
                _sealed_record("J-AR12", event_id)
                for event_id in sorted(state.known_predecessor_event_ids)
            ),
        ),
        projection_replacements=(
            ProjectionReplacement(
                projection_family="J-P04",
                projection_token=projection_ref,
                source_hash=projection_hash,
                canonical_payload=projection_payload,
            ),
        ),
    )
    return context, bundle


def test_schema_and_baseline_survive_process_restart(tmp_path: Path) -> None:
    control = _posting_control()
    initial = _baseline(control)
    database = tmp_path / "runtime.sqlite3"
    boundary = _admit(database, initial)

    assert boundary.schema_version == 4
    before_baseline = boundary.open_query(
        QueryContext(semantic_as_of_time="2026-07-13T23:59:59Z")
    )
    assert before_baseline.state().snapshot == StateSnapshot()
    assert before_baseline.authoritative_records() == ()
    assert boundary.state.full_digest == initial.full_digest
    boundary.close()

    restarted = SqlitePersistenceBoundary(database)
    assert restarted.revision == 0
    assert restarted.state.full_digest == initial.full_digest
    context, bundle = _baseline_admission(initial)
    replay_unit = restarted.begin_runtime_baseline_admission(context)
    replay_unit.stage_bundle(bundle)
    replay = replay_unit.commit(replay_unit.validate())
    assert replay.replayed
    restarted.close()


def test_baseline_j_ar02_accepts_only_registered_artifact_l_products(
    tmp_path: Path,
) -> None:
    boundary = SqlitePersistenceBoundary(tmp_path / "baseline-products.sqlite3")
    context, bundle = _baseline_admission(InMemoryState())
    evidence_body = EvidenceRef(
        ref_id="EVD-BASELINE-SCHEDULE",
        description="Declared recognition-schedule evidence",
        content_hash="sha256:" + "e" * 64,
    )
    evidence = AuthoritativeRef(
        record_family="J-AR12",
        record_identity="EVD-BASELINE-SCHEDULE",
        semantic_hash=canonical_sha256(evidence_body.model_dump(mode="json")),
    )
    product = ValidatedModuleProduct.baseline(
        product_discriminator="source.recognition_schedule",
        owner="SourceDomain",
        body={
            "product_ref": "SCHEDULE:C001@v1",
            "created_at": "2026-07-14T00:00:00Z",
            "recognition_schedule_ref": "SCHEDULE:C001",
            "contract_ref": "CONTRACT:C001",
            "legal_entity_id": "NEXUS-UK",
            "customer_id": "ORION",
            "service_period_start": "2026-06-01",
            "service_period_end": "2027-05-31",
            "recognition_effective_date": "2026-06-30",
            "amount_minor": 1000000,
            "currency": "GBP",
            "source_record_ref": "SOURCE:SCHEDULE:C001",
        },
        baseline_manifest_ref=context.baseline_manifest_ref,
        evidence_refs=(evidence,),
        available_from=context.semantic_as_of_time,
    )
    product_payload = canonical_bytes(product.model_dump(mode="json"))
    product_record = SealedAdmissionRecord(
        record_family="J-AR02",
        record_identity=product.product_ref,
        semantic_owner="SourceDomain",
        contract_version="1",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        semantic_hash=product.semantic_hash,
        canonical_payload=product_payload,
    )
    evidence_record = SealedAdmissionRecord(
        record_family="J-AR12",
        record_identity=str(evidence_body.ref_id),
        semantic_owner="PLATFORM",
        contract_version="1",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        semantic_hash=canonical_sha256(evidence_body.model_dump(mode="json")),
        canonical_payload=canonical_bytes(evidence_body.model_dump(mode="json")),
    )
    unit = boundary.begin_runtime_baseline_admission(context)
    unit.stage_bundle(
        AdmissionBundle(
            declared_records=(
                *bundle.declared_records,
                evidence_record,
                product_record,
            ),
            projection_replacements=bundle.projection_replacements,
        )
    )
    unit.commit(unit.validate())

    stored = boundary.open_query(
        QueryContext(semantic_as_of_time=context.semantic_as_of_time)
    ).authoritative_records()
    assert any(
        item.record_family == "J-AR02"
        and item.record_identity == "SCHEDULE:C001@v1"
        for item in stored
    )
    boundary.close()


def test_schema_v3_records_receive_deterministic_availability_on_upgrade(
    tmp_path: Path,
) -> None:
    database = tmp_path / "runtime-v3.sqlite3"
    connection = sqlite3.connect(database, isolation_level=None)
    connection.execute(
        """
        CREATE TABLE schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    for migration in MIGRATIONS[:3]:
        connection.execute("BEGIN IMMEDIATE")
        for statement in migration.sql.split(";"):
            if statement.strip():
                connection.execute(statement)
        connection.execute(
            "INSERT INTO schema_migrations(version, name) VALUES (?, ?)",
            (migration.version, migration.name),
        )
        connection.commit()
    connection.execute(
        """
        INSERT INTO authoritative_records(
            record_family, record_identity, semantic_hash, payload,
            command_id, record_ordinal
        ) VALUES ('J-AR12', 'LEGACY-EVIDENCE', 'sha256:legacy', X'7B7D', NULL, 0)
        """
    )
    connection.close()

    upgraded = SqlitePersistenceBoundary(database)
    row = upgraded._connection.execute(
        """
        SELECT available_from FROM authoritative_records
        WHERE record_family = 'J-AR12' AND record_identity = 'LEGACY-EVIDENCE'
        """
    ).fetchone()
    assert upgraded.schema_version == 4
    assert row == ("0001-01-01T00:00:00Z",)
    upgraded.close()


def test_command_retry_and_effect_identity_survive_restart(tmp_path: Path) -> None:
    control = _posting_control()
    database = tmp_path / "runtime.sqlite3"
    boundary = _admit(database, _baseline(control))
    first = execute(boundary, control.command)  # type: ignore[attr-defined]
    terminal_digest = boundary.state.full_digest
    boundary.close()

    restarted = SqlitePersistenceBoundary(database)
    retry = execute(restarted, control.command)  # type: ignore[attr-defined]

    assert first.committed
    assert retry.replayed
    assert restarted.revision == 1
    assert restarted.state.full_digest == terminal_digest
    assert len(restarted.state.effect_registry) == 1
    restarted.close()


def test_sql_failure_rolls_back_disk_and_memory_atomically(tmp_path: Path) -> None:
    control = _posting_control()
    database = tmp_path / "runtime.sqlite3"

    def fail(stage: str) -> None:
        if stage == "command_before_commit":
            raise OSError("injected durable write failure")

    boundary = _admit(database, _baseline(control), fault_injector=fail)
    before = boundary.state.full_digest

    with pytest.raises(OSError, match="injected durable write failure"):
        execute(boundary, control.command)  # type: ignore[attr-defined]

    assert boundary.revision == 0
    assert boundary.state.full_digest == before
    boundary.close()

    restarted = SqlitePersistenceBoundary(database)
    assert restarted.revision == 0
    assert restarted.state.full_digest == before
    assert not restarted.state.command_results
    assert not restarted.state.effect_registry
    restarted.close()


def test_projection_can_be_deleted_and_rebuilt_from_declared_inputs(
    tmp_path: Path,
) -> None:
    control = _posting_control()
    database = tmp_path / "runtime.sqlite3"
    boundary = _admit(database, _baseline(control))
    execute(boundary, control.command)  # type: ignore[attr-defined]
    terminal_digest = boundary.state.full_digest
    terminal_projection = boundary.state.snapshot

    boundary.delete_projection_checkpoint()
    session = boundary.open_rebuild(
        RebuildContext(
            semantic_as_of_time="2026-07-14T00:00:00Z",
            requested_projection_families=("J-P04", "J-P05"),
        )
    )
    generation = session.begin_generation()
    rebuilt = session.rebuild(generation)
    receipt = session.promote(session.validate(rebuilt))

    assert receipt.prior_projection_hash == receipt.rebuilt_projection_hash
    assert receipt.command_count == 1
    assert boundary.state.snapshot == terminal_projection
    boundary.close()

    restarted = SqlitePersistenceBoundary(database)
    assert restarted.state.full_digest == terminal_digest
    restarted.close()


def test_query_session_is_read_only_and_revision_pinned(tmp_path: Path) -> None:
    control = _posting_control()
    boundary = _admit(tmp_path / "runtime.sqlite3", _baseline(control))
    execute(boundary, control.command)  # type: ignore[attr-defined]

    query = boundary.open_query(
        QueryContext(semantic_as_of_time="2026-07-14T12:00:00Z")
    )

    assert query.revision == 1
    assert query.state().full_digest == boundary.state.full_digest
    assert query.command_result(control.command.command_id) is not None  # type: ignore[attr-defined]
    assert not hasattr(query, "commit")
    boundary.close()


def test_rejected_g14_closure_survives_restart(tmp_path: Path) -> None:
    empty = InMemoryState()
    database = tmp_path / "runtime.sqlite3"
    boundary = _admit(database, empty)
    command = ApplyRemediationDirective(
        command_id="CMD-PHASE3-G14",
        request_ref="REQ-PHASE3-G14",
        directive_valid=False,
    )
    first = execute(boundary, command)
    boundary.close()

    restarted = SqlitePersistenceBoundary(database)
    retry = execute(restarted, command)

    assert first.committed
    assert retry.replayed
    assert len(restarted.state.command_results) == 1
    assert len(restarted.state.dispositions) == 1
    assert isinstance(restarted.state.command_results[0].outcome, Rejection)
    restarted.close()


def test_database_constraints_reject_duplicate_authoritative_identity(
    tmp_path: Path,
) -> None:
    boundary = _admit(tmp_path / "runtime.sqlite3", InMemoryState())
    connection = boundary._connection
    connection.execute("BEGIN IMMEDIATE")
    connection.execute(
        """
        INSERT INTO authoritative_records(
            record_family, record_identity, semantic_hash, payload,
            command_id, record_ordinal
        ) VALUES ('TEST', 'ONE', 'sha256:a', X'7B7D', NULL, 0)
        """
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO authoritative_records(
                record_family, record_identity, semantic_hash, payload,
                command_id, record_ordinal
            ) VALUES ('TEST', 'ONE', 'sha256:b', X'7B7D', NULL, 1)
            """
        )
    connection.rollback()
    boundary.close()


def test_tampered_checkpoint_is_rejected_on_restart(tmp_path: Path) -> None:
    database = tmp_path / "runtime.sqlite3"
    boundary = _admit(database, InMemoryState())
    boundary._connection.execute(
        "UPDATE projection_checkpoint SET payload_hash = 'sha256:tampered'"
    )
    boundary.close()

    with pytest.raises(DurableStateError, match="projection-checkpoint hash mismatch"):
        SqlitePersistenceBoundary(database)


def test_second_process_view_cannot_commit_a_stale_revision(tmp_path: Path) -> None:
    database = tmp_path / "runtime.sqlite3"
    first = _admit(database, InMemoryState())
    stale = SqlitePersistenceBoundary(database)
    first_command = ApplyRemediationDirective(
        command_id="CMD-PROCESS-ONE",
        request_ref="REQ-PROCESS-ONE",
        directive_valid=False,
    )
    stale_command = ApplyRemediationDirective(
        command_id="CMD-PROCESS-TWO",
        request_ref="REQ-PROCESS-TWO",
        directive_valid=False,
    )
    execute(first, first_command)

    with pytest.raises(InvariantFailure, match="durable revision changed"):
        execute(stale, stale_command)

    assert stale.revision == 0
    assert not stale.state.command_results
    first.close()
    stale.close()

    restarted = SqlitePersistenceBoundary(database)
    assert restarted.revision == 1
    assert [item.command_id for item in restarted.state.command_results] == [
        "CMD-PROCESS-ONE"
    ]
    restarted.close()


def test_baseline_mode_rejects_command_produced_record_family(tmp_path: Path) -> None:
    boundary = SqlitePersistenceBoundary(tmp_path / "runtime.sqlite3")
    context, _ = _baseline_admission(InMemoryState())
    unit = boundary.begin_runtime_baseline_admission(context)
    unit.stage_bundle(AdmissionBundle((_sealed_record("J-AR14", "COMMAND"),)))

    with pytest.raises(AdmissionConflict, match="not permitted"):
        unit.validate()
    assert boundary.revision == 0
    boundary.close()


def test_in_memory_commit_hook_still_rejects_wrong_base() -> None:
    from finance_assurance.runtime.persistence.memory import InMemoryPersistenceBoundary

    boundary = InMemoryPersistenceBoundary()
    with pytest.raises(InvariantFailure):
        boundary._commit_prepared(
            previous=InMemoryState(),
            prepared=InMemoryState(),
            context=next(iter(()), None),  # type: ignore[arg-type]
        )


def _sealed_record(
    family: str,
    identity: str,
    *,
    owner: str = "PLATFORM",
    body: dict[str, object] | None = None,
) -> SealedAdmissionRecord:
    content = body or {"contract_version": 1, "record_id": identity}
    payload = canonical_bytes(content)
    return SealedAdmissionRecord(
        record_family=family,
        record_identity=identity,
        semantic_owner=owner,
        contract_version="1",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        semantic_hash=canonical_sha256(content),
        canonical_payload=payload,
    )


def test_baseline_and_referenced_admission_modes_are_sealed_and_queryable(
    tmp_path: Path,
) -> None:
    database = tmp_path / "runtime.sqlite3"
    boundary = SqlitePersistenceBoundary(database)
    baseline_context, baseline_bundle = _baseline_admission(InMemoryState())
    baseline = boundary.begin_runtime_baseline_admission(baseline_context)
    baseline.stage_bundle(baseline_bundle)
    baseline_receipt = baseline.commit(baseline.validate())
    assert baseline_receipt.revision == 0

    source = _sealed_record("J-AR17", "J-010", owner="ATLAS")
    g13 = ContractPublication(
        publication_ref="G-13:J-010",
        contract_id="G-13",
        g_contract_version="G-v0.2",
        body_contract_version=1,
        body_discriminator="G13ReferencedJournal",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        publisher="AtlasReadBoundary",
        product_ref="J-010@v1",
        product_state_token=None,
        canonical_payload={
            "projection_type": "referenced_journal_projection",
            "projection_version": 1,
            "authored_by_f": False,
            "source_hash": source.semantic_hash,
            "journal_id": source.record_identity,
            "ledger_period_id": "2026-07",
            "currency": "GBP",
            "line_tuples": [],
        },
        payload_hash=canonical_sha256(
            {
                "projection_type": "referenced_journal_projection",
                "projection_version": 1,
                "authored_by_f": False,
                "source_hash": source.semantic_hash,
                "journal_id": source.record_identity,
                "ledger_period_id": "2026-07",
                "currency": "GBP",
                "line_tuples": [],
            }
        ),
        upstream_publication_refs=(),
        upstream_authoritative_refs=(
            ExactSemanticRef(
                ref_kind="AUTHORITATIVE",
                authoritative_ref=AuthoritativeRef(
                    record_family="J-AR17",
                    record_identity="J-010",
                    semantic_hash=source.semantic_hash,
                ),
                publication_ref=None,
                module_product_ref=None,
            ),
        ),
        evidence_refs=(
            AuthoritativeRef(
                record_family="J-AR12",
                record_identity="EVD-J010",
                semantic_hash="sha256:" + "e" * 64,
            ),
        ),
        available_from="2026-07-14T00:00:00Z",
        publication_basis=ReferencedJournalPublicationBasis(
            basis_type="REFERENCED_JOURNAL_ADMISSION",
            referenced_source_ref="J-010",
            admission_identity="J-010",
        ),
    )
    publication = _sealed_record(
        "J-AR13",
        "G-13:J-010",
        owner="ATLAS",
        body=g13.model_dump(mode="json"),
    )
    referenced_context = ReferencedJournalContext(
        source_journal_ref="J-010",
        source_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        source_hash=source.semantic_hash,
        source_contract_version="1",
        semantic_as_of_time="2026-07-14T00:00:00Z",
        admitting_actor_ref="HERMES",
    )
    referenced = boundary.begin_referenced_journal_admission(
        referenced_context
    )
    referenced.stage_bundle(
        ReferencedJournalAdmissionBundle(
            declared_records=(
                source,
                publication,
            ),
            canonical_source_body=source.canonical_payload,
            provenance_body=canonical_bytes(
                {"source_system": "LEGACY-LEDGER", "verified": True}
            ),
        )
    )
    referenced_receipt = referenced.commit(referenced.validate())
    assert referenced_receipt.revision == 1
    sink = InMemoryObservationSink()
    ModuleContractService(boundary, observations=sink).observe_admission(
        g13,
        referenced_receipt,
        observed_at="2026-07-14T00:00:00Z",
    )
    assert sink.observations[0].contract_id == "G-13"

    query = boundary.open_query(
        QueryContext(semantic_as_of_time="2026-07-14T00:00:00Z")
    )
    exact = query.authoritative_record("J-AR17", "J-010")
    assert exact is not None
    assert exact.semantic_hash == source.semantic_hash
    boundary.close()

    restarted = SqlitePersistenceBoundary(database)
    assert restarted.revision == 1
    prior = restarted.begin_referenced_journal_admission(
        referenced_context
    ).prior_receipt()
    assert prior is not None and prior.replayed
    restarted.close()

def test_admission_failure_commits_no_records_or_projection(tmp_path: Path) -> None:
    database = tmp_path / "runtime.sqlite3"

    def fail(stage: str) -> None:
        if stage == "admission_before_commit":
            raise OSError("injected admission failure")

    boundary = SqlitePersistenceBoundary(database, fault_injector=fail)
    context, bundle = _baseline_admission(InMemoryState())
    unit = boundary.begin_runtime_baseline_admission(context)
    unit.stage_bundle(bundle)

    with pytest.raises(OSError, match="injected admission failure"):
        unit.commit(unit.validate())

    assert boundary.revision == 0
    assert not boundary._has_persisted_state()
    assert boundary._connection.execute(
        "SELECT COUNT(*) FROM authoritative_records"
    ).fetchone() == (0,)
    boundary.close()

    restarted = SqlitePersistenceBoundary(database)
    assert restarted.revision == 0
    assert restarted.state == InMemoryState()
    restarted.close()


def test_command_cannot_commit_an_unrebuildable_projection(tmp_path: Path) -> None:
    baseline = InMemoryState.from_snapshot(
        StateSnapshot(business_event_ids=frozenset({"BE-1"}))
    )
    boundary = _admit(tmp_path / "runtime.sqlite3", baseline)
    command = EvaluatePostingRule(
        command_id="CMD-UNREBUILDABLE-CONSTRUCTOR",
        input_id="BE-1",
        proposal_ref="P-NEW@v1",
        target_period_id="2026-07",
        account_ids=frozenset({"ACC-AR", "ACC-DEFREV"}),
        input_hashes=("sha256:input",),
    )

    with pytest.raises(DurableStateError, match="exact J-AR05 treatment"):
        execute(boundary, command)

    assert boundary.revision == 0
    assert not boundary.state.command_results
    boundary.close()
