"""Direct proofs for the Phase 5 transactional state boundary."""

from dataclasses import replace

import pytest

from finance_assurance.validation.dispatcher import InjectedCommitFailure, dispatch
from finance_assurance.validation.h2 import run_h2
from finance_assurance.validation.h3_guards import accepted_controls, guard_cases
from finance_assurance.validation.h3_stateful import run_h3
from finance_assurance.validation.h4_stateful import run_h4
from finance_assurance.validation.planner import ApplyRemediationDirective
from finance_assurance.validation.results import Rejection
from finance_assurance.validation.state import HarnessState


def _runtime(snapshot: object, command: object) -> HarnessState:
    event = getattr(command, "accounting_event", None)
    cause = getattr(event, "causation_event_id", None)
    return HarnessState.from_snapshot(
        snapshot,  # type: ignore[arg-type]
        known_predecessor_event_ids=(
            frozenset({str(cause)}) if cause is not None else frozenset()
        ),
    )


def test_every_h3_rejection_preserves_all_six_protected_digests() -> None:
    h2 = run_h2()
    assert h2.index is not None
    for case in guard_cases(h2.index):
        for command in case.commands:
            state = _runtime(case.state, command)
            before = state.protected_digests()
            outcome = dispatch(state, command)
            assert isinstance(outcome.result, Rejection)
            assert str(outcome.result.code) == case.expected_code
            assert outcome.state.protected_digests() == before
            assert len(outcome.state.command_results) == 1
            assert not outcome.state.dispositions


def test_rejected_command_retry_is_control_plane_idempotent() -> None:
    h2 = run_h2()
    assert h2.index is not None
    case = guard_cases(h2.index)[0]
    first = dispatch(_runtime(case.state, case.commands[0]), case.commands[0])
    retry = dispatch(first.state, case.commands[0])
    assert retry.replayed
    assert retry.result == first.result
    assert retry.state == first.state


def test_successful_post_commits_journal_event_result_and_effect_together() -> None:
    h2 = run_h2()
    assert h2.index is not None
    control = next(
        item
        for item in accepted_controls(h2.index)
        if item.name == "restatement posting"
    )
    outcome = dispatch(_runtime(control.state, control.command), control.command)
    assert outcome.committed
    assert len(outcome.state.journal_store) == 3
    assert len(outcome.state.event_log) == 1
    assert len(outcome.state.command_results) == 1
    assert len(outcome.state.effect_registry) == 1
    proposal = outcome.state.snapshot.proposal("P-551@v2")
    assert proposal is not None and proposal.status == "POSTED"


def test_precommit_failure_cannot_publish_partial_state() -> None:
    h2 = run_h2()
    assert h2.index is not None
    control = next(
        item
        for item in accepted_controls(h2.index)
        if item.name == "restatement posting"
    )
    state = _runtime(control.state, control.command)
    before = state.full_digest
    with pytest.raises(InjectedCommitFailure):
        dispatch(state, control.command, inject_failure_before_commit=True)
    assert state.full_digest == before
    assert not state.command_results
    assert not state.event_log
    assert not state.journal_store
    assert not state.effect_registry


def test_consumed_command_id_rejects_changed_content_without_record() -> None:
    h2 = run_h2()
    assert h2.index is not None
    control = next(
        item
        for item in accepted_controls(h2.index)
        if item.name == "restatement posting"
    )
    first = dispatch(_runtime(control.state, control.command), control.command)
    conflict = dispatch(first.state, replace(control.command, approval_valid=False))
    assert isinstance(conflict.result, Rejection)
    assert str(conflict.result.code) == "COMMAND_ID_CONFLICT"
    assert conflict.state == first.state


def test_invalid_directive_has_one_g14_disposition_and_no_subject() -> None:
    command = ApplyRemediationDirective(
        command_id="CMD-G14-TEST",
        request_ref="REQ-G14-TEST",
        directive_valid=False,
    )
    first = dispatch(HarnessState(), command)
    assert len(first.state.command_results) == 1
    assert len(first.state.dispositions) == 1
    assert first.state.dispositions[0].contract_id == "G-14"
    assert not first.state.event_log
    retry = dispatch(first.state, command)
    assert retry.replayed
    assert retry.state == first.state


def test_h3_and_h4_suites_pass() -> None:
    assert run_h3().passed
    assert run_h4().passed
