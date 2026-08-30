"""Full H3 proof: correct rejection plus protected-state immutability."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from finance_assurance.validation.dispatcher import dispatch
from finance_assurance.validation.h2 import H2Run, run_h2
from finance_assurance.validation.h3_guards import (
    H3GuardRun,
    guard_cases,
    run_h3_guards,
)
from finance_assurance.validation.results import (
    AssertionResult,
    AssertionStatus,
    Rejection,
)
from finance_assurance.validation.state import HarnessState


@dataclass(frozen=True, slots=True)
class H3Run:
    results: tuple[AssertionResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.status is AssertionStatus.PASS for result in self.results)


def _runtime_state(case_state: object, command: object) -> HarnessState:
    event = getattr(command, "accounting_event", None)
    cause = getattr(event, "causation_event_id", None)
    known = frozenset({str(cause)}) if cause is not None else frozenset()
    return HarnessState.from_snapshot(
        case_state,  # type: ignore[arg-type]
        known_predecessor_event_ids=known,
    )


def run_h3(
    root: Path | None = None,
    *,
    h2_run: H2Run | None = None,
    guard_run: H3GuardRun | None = None,
) -> H3Run:
    """Execute H3-01..18 against the transactional dispatcher."""

    h2 = h2_run or run_h2(root)
    guards = guard_run or run_h3_guards(root, h2_run=h2)
    if not h2.passed or h2.index is None or not guards.passed:
        return H3Run(
            results=tuple(
                AssertionResult(
                    test_id=f"H3-{number:02d}",
                    layer="H3",
                    source_obligation=f"PI-{number:02d}",
                    status=AssertionStatus.BLOCKED,
                    expected_outcome="H2 and H3 guard correctness must pass",
                    actual_outcome="blocked by a lower validation layer",
                )
                for number in range(1, 19)
            )
        )

    results: list[AssertionResult] = []
    for case in guard_cases(h2.index):
        passed = True
        details: list[str] = []
        before_combined: str | None = None
        after_combined: str | None = None
        for command in case.commands:
            initial = _runtime_state(case.state, command)
            before = initial.protected_digests()
            first = dispatch(initial, command)
            after = first.state.protected_digests()
            retry = dispatch(first.state, command)
            result_is_expected = (
                isinstance(first.result, Rejection)
                and str(first.result.code) == case.expected_code
            )
            attempt_passed = bool(
                result_is_expected
                and before == after
                and len(first.state.command_results) == 1
                and not first.state.dispositions
                and retry.replayed
                and retry.state == first.state
                and retry.result == first.result
            )
            passed = passed and attempt_passed
            before_combined = before.combined
            after_combined = after.combined
            outcome_code = getattr(first.result, "code", "ACCEPTED")
            details.append(
                f"{command.command_id}:code={outcome_code},"
                f"protected={'equal' if before == after else 'changed'},"
                f"results={len(first.state.command_results)},retry={retry.replayed}"
            )
        results.append(
            AssertionResult(
                test_id=case.test_id,
                layer="H3",
                source_obligation=f"PI-{case.test_id[-2:]}",
                status=AssertionStatus.PASS if passed else AssertionStatus.FAIL,
                expected_outcome=(
                    f"{case.expected_code}; six protected digests unchanged; "
                    "one rejection record; idempotent retry"
                ),
                actual_outcome=" | ".join(details),
                before_digest=before_combined,
                after_digest=after_combined,
            )
        )
    return H3Run(results=tuple(results))
