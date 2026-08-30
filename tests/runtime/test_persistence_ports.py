"""Phase 2 conformance proofs for the Artifact K in-memory adapter."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from finance_assurance.runtime.execution import (
    InjectedCommitFailure,
    command_context_for,
    construct_conflict_rejection,
    execute,
    rejection_write_set_for,
    write_set_for_transition,
)
from finance_assurance.runtime.persistence.memory import InMemoryPersistenceBoundary
from finance_assurance.runtime.persistence.models import (
    AcceptedCommitPlan,
    CommandResult,
    CommitReceipt,
    ExactConflictSnapshot,
)
from finance_assurance.runtime.persistence.state import HarnessState
from finance_assurance.runtime.planner import (
    ApplyRemediationDirective,
    ProposalState,
    TransitionPlan,
    plan,
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


def _runtime(snapshot: object, command: object) -> HarnessState:
    event = getattr(command, "accounting_event", None)
    cause = getattr(event, "causation_event_id", None)
    return HarnessState.from_snapshot(
        snapshot,  # type: ignore[arg-type]
        known_predecessor_event_ids=(
            frozenset({str(cause)}) if cause is not None else frozenset()
        ),
    )


def test_command_executes_through_boundary_and_returns_clean_receipt() -> None:
    control = _posting_control()
    boundary = InMemoryPersistenceBoundary(
        _runtime(control.state, control.command)  # type: ignore[attr-defined]
    )

    outcome = execute(boundary, control.command)  # type: ignore[attr-defined]

    assert outcome.committed
    assert outcome.state is boundary.state
    assert outcome.receipt is not None
    assert outcome.receipt.outcome == "ACCEPTED"
    assert outcome.receipt.command_result_ref == control.command.command_id  # type: ignore[attr-defined]
    assert outcome.receipt.claimed_effect_refs == ("post:P-551@v2",)
    assert {item.record_family for item in outcome.receipt.committed_authoritative_refs} == {
        "J-AR06",
        "J-AR08",
        "J-AR14",
    }
    assert "transaction_id" not in {item.name for item in fields(CommitReceipt)}


def test_same_command_retry_returns_prior_result_before_new_execution() -> None:
    control = _posting_control()
    boundary = InMemoryPersistenceBoundary(
        _runtime(control.state, control.command)  # type: ignore[attr-defined]
    )
    first = execute(boundary, control.command)  # type: ignore[attr-defined]
    digest = boundary.state.full_digest
    revision = boundary.revision

    retry = execute(boundary, control.command)  # type: ignore[attr-defined]

    assert retry.replayed
    assert retry.result == first.result
    assert retry.receipt is None
    assert boundary.revision == revision
    assert boundary.state.full_digest == digest


def test_command_contract_version_is_part_of_retry_identity() -> None:
    control = _posting_control()
    boundary = InMemoryPersistenceBoundary(
        _runtime(control.state, control.command)  # type: ignore[attr-defined]
    )
    execute(boundary, control.command)  # type: ignore[attr-defined]
    before = boundary.state.full_digest
    revision = boundary.revision
    changed_context = replace(
        command_context_for(control.command),  # type: ignore[attr-defined]
        input_contract_version="ARTIFACT-K-COMMAND-V2",
    )

    conflict = execute(
        boundary,
        control.command,  # type: ignore[attr-defined]
        context=changed_context,
    )

    assert isinstance(conflict.result, Rejection)
    assert str(conflict.result.code) == "COMMAND_ID_CONFLICT"
    assert boundary.revision == revision
    assert boundary.state.full_digest == before


def test_injected_precommit_failure_rolls_back_open_unit() -> None:
    control = _posting_control()
    initial = _runtime(control.state, control.command)  # type: ignore[attr-defined]
    boundary = InMemoryPersistenceBoundary(initial)

    with pytest.raises(InjectedCommitFailure):
        execute(
            boundary,
            control.command,  # type: ignore[attr-defined]
            inject_failure_before_commit=True,
        )

    assert boundary.revision == 0
    assert boundary.state is initial
    assert boundary.state.full_digest == initial.full_digest


def test_effect_key_is_unique_across_distinct_command_identities() -> None:
    control = _posting_control()
    second_proposal = ProposalState(
        proposal_ref="P-EFFECT-SECOND@v1",
        status="APPROVED",
        target_period_id="2026-07",
        origin_type="RESTATEMENT_ADJUSTMENT",
        account_ids=frozenset({"ACC-DEFREV", "ACC-REVENUE"}),
    )
    initial_snapshot = replace(
        control.state,  # type: ignore[attr-defined]
        proposals=(*control.state.proposals, second_proposal),  # type: ignore[attr-defined]
    )
    boundary = InMemoryPersistenceBoundary(
        _runtime(initial_snapshot, control.command)  # type: ignore[attr-defined]
    )
    first = execute(boundary, control.command)  # type: ignore[attr-defined]
    second_command = replace(
        control.command,  # type: ignore[attr-defined]
        command_id="CMD-EFFECT-SECOND",
        proposal_ref=second_proposal.proposal_ref,
    )

    second = execute(boundary, second_command)

    assert first.committed
    assert isinstance(second.result, Rejection)
    assert str(second.result.code) == "DUPLICATE_EFFECT"
    assert second.receipt is not None and second.receipt.outcome == "REJECTED"
    assert len(boundary.state.event_log) == 1
    assert len(boundary.state.journal_store) == 3
    assert len(boundary.state.effect_registry) == 1
    assert len(boundary.state.command_results) == 2


def test_final_arbitration_turns_effect_race_into_rejection_only_commit() -> None:
    control = _posting_control()
    original = control.command  # type: ignore[attr-defined]
    proposal = control.state.proposal(original.proposal_ref)  # type: ignore[attr-defined]
    assert proposal is not None
    second_proposal = replace(proposal, proposal_ref="P-EFFECT-RACE@v1")
    initial_snapshot = replace(
        control.state,  # type: ignore[attr-defined]
        proposals=(*control.state.proposals, second_proposal),  # type: ignore[attr-defined]
    )
    original_event = original.accounting_event
    assert original_event is not None
    second_event_id = "AE-EFFECT-RACE"
    second_command_id = "CMD-EFFECT-RACE"
    second_journal_id = "J-EFFECT-RACE"
    second_event = original_event.model_copy(
        update={
            "event_id": second_event_id,
            "command_id": second_command_id,
            "subject_ref": original_event.subject_ref.model_copy(
                update={"object_ref": second_proposal.proposal_ref}
            ),
            "basis": original_event.basis.model_copy(
                update={"proposal_ref": second_proposal.proposal_ref}
            ),
            "payload": original_event.payload.model_copy(
                update={
                    "proposal_ref": second_proposal.proposal_ref,
                    "journal_id": second_journal_id,
                }
            ),
        }
    )
    original_journal, *original_lines = original.immutable_creations
    second_line_ids = tuple(
        f"{second_journal_id}-L{index}"
        for index in range(1, len(original_lines) + 1)
    )
    second_journal = original_journal.model_copy(
        update={
            "journal_id": second_journal_id,
            "source_proposal_ref": second_proposal.proposal_ref,
            "posted_by_event_id": second_event_id,
            "line_refs": second_line_ids,
        }
    )
    second_lines = tuple(
        line.model_copy(
            update={
                "journal_line_id": line_id,
                "journal_id": second_journal_id,
            }
        )
        for line, line_id in zip(original_lines, second_line_ids, strict=True)
    )
    second_command = replace(
        original,
        command_id=second_command_id,
        accounting_event=second_event,
        immutable_creations=(second_journal, *second_lines),
        proposal_ref=second_proposal.proposal_ref,
    )
    boundary = InMemoryPersistenceBoundary(_runtime(initial_snapshot, original))
    first_unit = boundary.begin_command(command_context_for(original))
    second_unit = boundary.begin_command(command_context_for(second_command))

    def prepare(unit: object, command: object) -> object:
        snapshot = unit.records().snapshot()  # type: ignore[attr-defined]
        result = plan(command, snapshot)  # type: ignore[arg-type]
        assert isinstance(result, TransitionPlan)
        closure = CommandResult(
            command_id=command.command_id,  # type: ignore[attr-defined]
            command_fingerprint=command_context_for(command).input_digest,  # type: ignore[arg-type]
            status="ACCEPTED",
            outcome=result,
        )
        unit.stage_accepted(  # type: ignore[attr-defined]
            write_set_for_transition(command, result, snapshot, closure)  # type: ignore[arg-type]
        )
        return unit.validate()  # type: ignore[attr-defined]

    first_validated = prepare(first_unit, original)
    second_validated = prepare(second_unit, second_command)
    first_plan = first_unit.arbitrate(first_validated)  # type: ignore[arg-type]
    assert isinstance(first_plan, AcceptedCommitPlan)
    first_unit.commit(first_plan)

    conflict = second_unit.arbitrate(second_validated)  # type: ignore[arg-type]
    assert isinstance(conflict, ExactConflictSnapshot)
    assert conflict.conflict_class == "EFFECT_CONSUMED"
    rejection = construct_conflict_rejection(conflict)
    rejection_closure = CommandResult(
        command_id=second_command.command_id,
        command_fingerprint=command_context_for(second_command).input_digest,
        status="REJECTED",
        outcome=rejection,
    )
    second_unit.replace_with_conflict_rejection(
        conflict,
        rejection_write_set_for(second_command, rejection_closure),
    )
    second_unit.commit(second_unit.validate())  # type: ignore[arg-type]

    assert len(boundary.state.event_log) == 1
    assert len(boundary.state.journal_store) == 3
    assert len(boundary.state.effect_registry) == 1
    assert len(boundary.state.command_results) == 2
    assert boundary.state.command_results[-1].status == "REJECTED"


def test_g14_rejection_and_disposition_commit_atomically_once() -> None:
    boundary = InMemoryPersistenceBoundary()
    command = ApplyRemediationDirective(
        command_id="CMD-PHASE2-G14",
        request_ref="REQ-PHASE2-G14",
        directive_valid=False,
    )

    first = execute(boundary, command)
    retry = execute(boundary, command)

    assert first.receipt is not None and first.receipt.outcome == "REJECTED"
    assert {item.record_family for item in first.receipt.committed_authoritative_refs} == {
        "J-AR14",
        "J-AR16",
    }
    assert retry.replayed
    assert boundary.revision == 1
    assert len(boundary.state.command_results) == 1
    assert len(boundary.state.dispositions) == 1


def test_root_boundary_exposes_no_independent_commit_or_generic_append() -> None:
    boundary = InMemoryPersistenceBoundary()
    assert not hasattr(boundary, "commit")
    assert not hasattr(boundary, "append")
