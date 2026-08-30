"""Phase 6 integration proofs for canonical C-001 and CT-1 replay."""

from finance_assurance.validation.dispatcher import dispatch
from finance_assurance.validation.h2 import run_h2
from finance_assurance.validation.h5_replay import run_h5
from finance_assurance.validation.planner import (
    ConstructCorrectionProposal,
    PeriodState,
    StateSnapshot,
    TransitionPlan,
)
from finance_assurance.validation.results import AssertionStatus, Rejection
from finance_assurance.validation.scenarios import replay_c001, replay_ct1
from finance_assurance.validation.state import HarnessState


def test_h5_replays_both_canonical_transactions() -> None:
    run = run_h5()
    assert run.passed
    assert [result.test_id for result in run.results] == ["H5-01", "H5-02"]
    assert {result.status for result in run.results} == {AssertionStatus.PASS}
    assert run.c001 is not None
    assert run.ct1 is not None


def test_c001_uses_only_dispatcher_commits_after_bootstrap() -> None:
    h2 = run_h2()
    assert h2.index is not None
    replay = replay_c001(h2.index)
    assert len(replay.commands) == len(replay.outcomes) == 13
    assert len(replay.state.command_results) == 13
    assert len(replay.state.event_log) == 11
    assert all(outcome.committed for outcome in replay.outcomes)
    assert all(
        len(outcome.state.command_results) == sequence
        for sequence, outcome in enumerate(replay.outcomes, start=1)
    )
    assert replay.evaluator_input_ids == ("BE-C001-RECOG-202606",)
    assert replay.correction_constructor_refs == ("P-551@v2",)
    assert replay.state.reporting_content_proofs == (
        replay.initial_state.reporting_content_proofs
    )
    assert not replay.state.dispositions


def test_ct1_preserves_j010_as_non_authored_referenced_state() -> None:
    h2 = run_h2()
    assert h2.index is not None
    replay = replay_ct1(h2.index)
    assert len(replay.commands) == len(replay.outcomes) == 8
    assert len(replay.state.command_results) == 8
    assert len(replay.state.event_log) == 6
    assert not replay.evaluator_input_ids
    assert replay.correction_constructor_refs == (
        "P-REV-010@v1",
        "P-REP-010@v1",
    )
    assert replay.state.referenced_state == replay.initial_state.referenced_state
    assert all(
        getattr(item, "journal_id", None) != "J-010"
        for item in replay.state.journal_store
    )


def test_replay_terminal_digests_are_deterministic() -> None:
    first = run_h5()
    second = run_h5()
    assert first.c001 is not None and second.c001 is not None
    assert first.ct1 is not None and second.ct1 is not None
    assert first.c001.state.full_digest == second.c001.state.full_digest
    assert first.ct1.state.full_digest == second.ct1.state.full_digest


def test_correction_constructor_is_eventless_and_rejects_incomplete_basis() -> None:
    state = HarnessState.from_snapshot(
        StateSnapshot(periods=(PeriodState("2026-07", "OPEN"),))
    )
    valid = ConstructCorrectionProposal(
        command_id="CMD-CONSTRUCT-VALID",
        proposal_ref="P-TEST@v1",
        target_period_id="2026-07",
        origin_type="REPLACEMENT",
        account_ids=frozenset({"ACC-AR"}),
        input_hashes=("sha256:" + "1" * 64,),
    )
    accepted = dispatch(state, valid)
    assert isinstance(accepted.result, TransitionPlan)
    assert not accepted.state.event_log
    proposal = accepted.state.snapshot.proposal("P-TEST@v1")
    assert proposal is not None and proposal.status == "DRAFT"

    invalid = ConstructCorrectionProposal(
        command_id="CMD-CONSTRUCT-INVALID",
        proposal_ref="P-BAD@v1",
        target_period_id="2026-07",
        origin_type="REPLACEMENT",
    )
    rejected = dispatch(state, invalid)
    assert isinstance(rejected.result, Rejection)
    assert str(rejected.result.code) == "CORRECTION_BASIS_INCOMPLETE"
    assert rejected.state.protected_digests() == state.protected_digests()
