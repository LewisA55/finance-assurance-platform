"""Artifact H H4 stateful command and financial-effect proofs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from finance_assurance.validation.dispatcher import (
    InjectedCommitFailure,
    dispatch,
)
from finance_assurance.validation.h2 import H2Run, run_h2
from finance_assurance.validation.h3_guards import accepted_controls
from finance_assurance.validation.planner import (
    ApplyRemediationDirective,
    ProposalState,
    RestatementState,
)
from finance_assurance.validation.results import (
    AssertionResult,
    AssertionStatus,
    Rejection,
)
from finance_assurance.validation.state import HarnessState


@dataclass(frozen=True, slots=True)
class H4Run:
    results: tuple[AssertionResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.status is AssertionStatus.PASS for result in self.results)


def _state(snapshot: object, command: object) -> HarnessState:
    event = getattr(command, "accounting_event", None)
    cause = getattr(event, "causation_event_id", None)
    known = frozenset({str(cause)}) if cause is not None else frozenset()
    return HarnessState.from_snapshot(
        snapshot,  # type: ignore[arg-type]
        known_predecessor_event_ids=known,
    )


def _is_code(result: object, code: str) -> bool:
    return isinstance(result, Rejection) and str(result.code) == code


def _assertion(test_id: str, passed: bool, actual: str) -> AssertionResult:
    return AssertionResult(
        test_id=test_id,
        layer="H4",
        source_obligation="Artifact H section 13 / F-EXE-002",
        status=AssertionStatus.PASS if passed else AssertionStatus.FAIL,
        expected_outcome="stateful command/effect invariant holds",
        actual_outcome=actual,
    )


def run_h4(root: Path | None = None, *, h2_run: H2Run | None = None) -> H4Run:
    """Execute H4-01..07 sequentially over immutable transactional state."""

    h2 = h2_run or run_h2(root)
    if not h2.passed or h2.index is None:
        return H4Run(
            results=tuple(
                AssertionResult(
                    test_id=f"H4-{number:02d}",
                    layer="H4",
                    source_obligation="Artifact H section 13 / F-EXE-002",
                    status=AssertionStatus.BLOCKED,
                    expected_outcome="H2 must pass before H4",
                    actual_outcome="blocked because H2 failed",
                )
                for number in range(1, 8)
            )
        )

    controls = {item.name: item for item in accepted_controls(h2.index)}
    post = controls["restatement posting"]
    publish = controls["reporting publication"]
    results: list[AssertionResult] = []

    # H4-01: a byte-identical retry returns the original result and changes nothing.
    initial = _state(post.state, post.command)
    first = dispatch(initial, post.command)
    retry = dispatch(first.state, post.command)
    passed = bool(
        retry.replayed
        and retry.result == first.result
        and retry.state == first.state
    )
    results.append(_assertion("H4-01", passed, "same command replayed without append"))

    # H4-02: command identity is bound to its first logical content.
    conflicting = replace(post.command, approval_valid=False)
    conflict = dispatch(first.state, conflicting)
    passed = _is_code(conflict.result, "COMMAND_ID_CONFLICT") and (
        conflict.state == first.state
    )
    results.append(
        _assertion("H4-02", passed, "different payload rejected by command ID")
    )

    # H4-03: a fresh command cannot reuse an already-consumed posting effect.
    extra = ProposalState(
        proposal_ref="P-DUPLICATE@v1",
        status="APPROVED",
        target_period_id="2026-07",
        origin_type="RESTATEMENT_ADJUSTMENT",
    )
    seeded_snapshot = replace(post.state, proposals=(*post.state.proposals, extra))
    seeded = _state(seeded_snapshot, post.command)
    posted = dispatch(seeded, post.command)
    duplicate_event = post.command.accounting_event.model_copy(
        update={"command_id": "CMD-H4-03", "event_id": "AE-H4-03"}
    )
    duplicate_post = replace(
        post.command,
        command_id="CMD-H4-03",
        accounting_event=duplicate_event,
        proposal_ref="P-DUPLICATE@v1",
    )
    duplicate = dispatch(posted.state, duplicate_post)
    passed = _is_code(duplicate.result, "DUPLICATE_EFFECT") and (
        duplicate.state.protected_digests() == posted.state.protected_digests()
    )
    results.append(_assertion("H4-03", passed, "posting effect key consumed once"))

    # H4-04: publication idempotency is independent of command identity.
    second_case = RestatementState(
        case_id="RC-DUPLICATE",
        status="APPROVED",
        scope_period_ids=frozenset({"2026-06"}),
        manifest_hash=publish.command.manifest_hash,
    )
    publication_snapshot = replace(
        publish.state,
        restatements=(*publish.state.restatements, second_case),
    )
    published = dispatch(_state(publication_snapshot, publish.command), publish.command)
    pub_event = publish.command.accounting_event.model_copy(
        update={
            "command_id": "CMD-H4-04",
            "event_id": "AE-H4-04",
            "subject_ref": publish.command.accounting_event.subject_ref.model_copy(
                update={"object_ref": "RC-DUPLICATE"}
            ),
        }
    )
    duplicate_publish = replace(
        publish.command,
        command_id="CMD-H4-04",
        accounting_event=pub_event,
        case_id="RC-DUPLICATE",
    )
    pub_duplicate = dispatch(published.state, duplicate_publish)
    passed = _is_code(pub_duplicate.result, "DUPLICATE_EFFECT") and (
        pub_duplicate.state.protected_digests()
        == published.state.protected_digests()
    )
    results.append(_assertion("H4-04", passed, "publication effect key consumed once"))

    # H4-05: invalid cross-module input terminates outside Artifact F state.
    directive = ApplyRemediationDirective(
        command_id="CMD-H4-05",
        request_ref="REQ-AEGIS-INVALID-001",
        directive_valid=False,
    )
    directive_initial = HarnessState()
    directive_first = dispatch(directive_initial, directive)
    passed = bool(
        _is_code(directive_first.result, "INVALID_REMEDIATION_DIRECTIVE")
        and directive_first.state.protected_digests()
        == directive_initial.protected_digests()
        and len(directive_first.state.command_results) == 1
        and len(directive_first.state.dispositions) == 1
        and not directive_first.state.event_log
    )
    results.append(_assertion("H4-05", passed, "one subject-free G-14 disposition"))

    # H4-06: validated writes remain invisible when the pre-commit fault fires.
    atomic_initial = _state(post.state, post.command)
    failed = False
    try:
        dispatch(
            atomic_initial,
            post.command,
            inject_failure_before_commit=True,
        )
    except InjectedCommitFailure:
        failed = True
    passed = failed and atomic_initial == _state(post.state, post.command)
    results.append(_assertion("H4-06", passed, "fault left original state intact"))

    # H4-07: rejected cross-module delivery is itself idempotent.
    directive_retry = dispatch(directive_first.state, directive)
    passed = bool(
        directive_retry.replayed
        and directive_retry.result == directive_first.result
        and directive_retry.state == directive_first.state
        and len(directive_retry.state.command_results) == 1
        and len(directive_retry.state.dispositions) == 1
    )
    results.append(
        _assertion("H4-07", passed, "rejection and G-14 disposition replayed")
    )

    return H4Run(results=tuple(results))
