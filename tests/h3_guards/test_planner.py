"""Phase 4 acceptance tests for the single pure planner."""

from copy import deepcopy

from finance_assurance.validation.h2 import run_h2
from finance_assurance.validation.h3_guards import (
    accepted_controls,
    guard_cases,
    run_h3_guards,
)
from finance_assurance.validation.planner import (
    ReopenPeriod,
    StateSnapshot,
    TransitionPlan,
    plan,
)
from finance_assurance.validation.results import AssertionStatus, Rejection


def test_all_eighteen_guard_decisions_pass_without_reporting_full_h3() -> None:
    run = run_h3_guards()

    assert run.passed
    assert len(run.results) == 18
    assert [result.test_id for result in run.results] == [
        f"H3-{number:02d}" for number in range(1, 19)
    ]
    assert {result.layer for result in run.results} == {"H3_GUARD"}
    assert {result.status for result in run.results} == {AssertionStatus.PASS}


def test_every_accepted_control_produces_a_complete_deterministic_plan() -> None:
    h2 = run_h2()
    assert h2.index is not None
    controls = accepted_controls(h2.index)

    assert len(controls) == 13
    for control in controls:
        first = plan(control.command, control.state)
        second = plan(control.command, control.state)
        assert isinstance(first, TransitionPlan)
        assert first == second
        assert first.transition_id == control.transition_id
        if first.accounting_event is not None:
            assert first.accounting_event.command_id == first.command_id
            assert (
                first.accounting_event.subject_ref.object_ref
                == first.transition.subject_ref
            )
        if first.transition_id == "P4":
            assert len(first.immutable_creations) >= 3
            assert first.effect_key is not None
        if first.transition_id == "RS5":
            assert len(first.immutable_creations) == 1
            assert first.effect_key is not None


def test_planner_calls_do_not_mutate_commands_or_state() -> None:
    h2 = run_h2()
    assert h2.index is not None
    cases = guard_cases(h2.index)
    controls = accepted_controls(h2.index)

    for command, state in (
        *((case.commands[0], case.state) for case in cases),
        *((control.command, control.state) for control in controls),
    ):
        command_before = deepcopy(command)
        state_before = deepcopy(state)
        plan(command, state)
        assert command == command_before
        assert state == state_before


def test_successful_deferred_transition_cannot_expand_artifact_f() -> None:
    command = ReopenPeriod(
        command_id="CMD-DEFERRED-REOPEN",
        period_id="2026-06",
        directive_approved=True,
        scope_bounded=True,
        time_limit_present=True,
        evidence_complete=True,
    )
    state = StateSnapshot(
        periods=(),
    )
    missing_period = plan(command, state)
    assert isinstance(missing_period, Rejection)
    assert str(missing_period.code) == "PERIOD_NOT_HARD_CLOSED"

    from finance_assurance.validation.planner import PeriodState

    bounded_state = StateSnapshot(periods=(PeriodState("2026-06", "HARD_CLOSED"),))
    deferred = plan(command, bounded_state)
    assert isinstance(deferred, Rejection)
    assert str(deferred.code) == "DEFERRED_TRANSITION"


def test_accepted_event_set_does_not_expand_the_ten_type_boundary() -> None:
    h2 = run_h2()
    assert h2.index is not None
    allowed = {record.contract_key for record in h2.index.events}
    controls = accepted_controls(h2.index)

    planned_types = {
        str(control.command.accounting_event.event_type)
        for control in controls
        if control.command.accounting_event is not None
    }
    assert planned_types <= allowed
