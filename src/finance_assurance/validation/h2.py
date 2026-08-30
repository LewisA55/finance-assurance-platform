"""Artifact H H2 pure referential and accounting-integrity assertions."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from finance_assurance.validation.h1 import H1Run, run_h1
from finance_assurance.validation.index import ValidatedCorpusIndex
from finance_assurance.validation.integrity import (
    IntegrityViolation,
    assert_balances,
    assert_causal_order,
    assert_hard_close_counts,
    assert_manifest_integrity,
    assert_manifest_scope,
    assert_open_ledger_period,
    assert_posting_firewall,
    assert_reporting_bridge,
    assert_restatement_state_guards,
    assert_reversal_integrity,
    assert_sod,
    model_by,
)
from finance_assurance.validation.proofs import (
    ReferencedJournalProjection,
    resolve_referenced_journal,
    resolve_reporting_content,
)
from finance_assurance.validation.results import AssertionResult, AssertionStatus


@dataclass(frozen=True, slots=True)
class H2Run:
    index: ValidatedCorpusIndex | None
    results: tuple[AssertionResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.status is AssertionStatus.PASS for result in self.results)


def _result(
    test_id: str,
    obligation: str,
    status: AssertionStatus,
    expected: str,
    actual: str,
) -> AssertionResult:
    return AssertionResult(
        test_id=test_id,
        layer="H2",
        source_obligation=obligation,
        status=status,
        expected_outcome=expected,
        actual_outcome=actual,
    )


def _pass(test_id: str, obligation: str, expected: str, actual: str) -> AssertionResult:
    return _result(test_id, obligation, AssertionStatus.PASS, expected, actual)


def _fail(test_id: str, obligation: str, expected: str, error: Exception) -> AssertionResult:
    return _result(test_id, obligation, AssertionStatus.FAIL, expected, str(error))


def _expect_violation(action: Callable[[], object], code: str) -> None:
    try:
        action()
    except IntegrityViolation as error:
        if error.code != code:
            raise IntegrityViolation(
                "WRONG_REJECTION",
                f"expected {code}, received {error.code}",
            ) from error
    else:
        raise IntegrityViolation("MUTATION_ACCEPTED", f"expected rejection {code}")


def _h2_01(index: ValidatedCorpusIndex) -> str:
    count = assert_causal_order(index)
    return f"{count} events preserve immediate causal order in two correlations"


def _h2_02(index: ValidatedCorpusIndex) -> str:
    proposals, journals, posted = assert_balances(index)
    return (
        f"{proposals} proposals; {journals} journals; "
        f"{posted} posted events balanced in GBP"
    )


def _h2_03(index: ValidatedCorpusIndex) -> str:
    eligible, rejected = assert_posting_firewall(index)
    return f"{eligible} business event eligible; {rejected} accounting events ineligible"


def _h2_04(index: ValidatedCorpusIndex) -> str:
    count = assert_manifest_integrity(index)
    rc = model_by(index, "restatement_case", "restatement_case_id", "RC-001")
    mutation = rc.model_dump(mode="python", round_trip=True)
    mutation["adjustment_manifest"][0]["debit_minor"] += 1
    _expect_violation(lambda: assert_manifest_integrity(index, mutation), "MANIFEST_INTEGRITY")
    return f"{count} manifest lines reconcile to J-560; changed amount rejected"


def _h2_05(index: ValidatedCorpusIndex, projection: ReferencedJournalProjection) -> str:
    count = assert_reversal_integrity(index, projection)
    unbound = projection.model_copy(
        update={"source_hash": "sha256:" + "0" * 64},
    )
    _expect_violation(lambda: assert_reversal_integrity(index, unbound), "REVERSAL_BINDING")
    changed_line = projection.line_tuples[0].model_copy(update={"account_id": "ACC-OTHER"})
    changed = projection.model_copy(
        update={"line_tuples": (changed_line, *projection.line_tuples[1:])},
    )
    _expect_violation(lambda: assert_reversal_integrity(index, changed), "REVERSAL_INTEGRITY")
    return (
        f"source hash bound first; {count} J-011 lines equal and opposite; "
        "mutations rejected"
    )


def _h2_06(index: ValidatedCorpusIndex) -> str:
    count = assert_restatement_state_guards(index)
    return f"{count} exercised RC-001 snapshots satisfy state guards"


def _h2_07(index: ValidatedCorpusIndex) -> str:
    period = assert_open_ledger_period(index)
    journal = model_by(index, "journal_entry", "journal_id", "J-560")
    mutation = journal.model_dump(mode="python", round_trip=True)
    mutation["ledger_period_id"] = "2026-06"
    _expect_violation(lambda: assert_open_ledger_period(index, mutation), "HARD_CLOSED_PERIOD")
    return f"J-560 posts to open {period}; hard-closed June mutation rejected"


def _h2_08(index: ValidatedCorpusIndex) -> str:
    count = assert_manifest_scope(index)
    rc = model_by(index, "restatement_case", "restatement_case_id", "RC-001")
    mutation = rc.model_dump(mode="python", round_trip=True)
    mutation["adjustment_manifest"][0]["presented_period_id"] = "2026-07"
    _expect_violation(lambda: assert_manifest_scope(index, mutation), "RESTATEMENT_SCOPE")
    return f"{count} manifest lines present within RC-001 scope; outside period rejected"


def _h2_09(index: ValidatedCorpusIndex) -> str:
    event = next(record.value for record in index.c001_events if record.contract_key == "period.hard_closed")
    body = event.model_dump(mode="python", round_trip=True)
    assert_hard_close_counts(body)
    for field, code in (
        ("unresolved_submitted_count", "UNRESOLVED_SUBMITTED_CLOSE"),
        ("unresolved_approved_count", "UNRESOLVED_APPROVED_CLOSE"),
    ):
        mutation = deepcopy(body)
        mutation["basis"][field] = 1
        _expect_violation(lambda candidate=mutation: assert_hard_close_counts(candidate), code)
    return (
        "zero unresolved proposal counts confirmed; "
        "submitted and approved mutations rejected"
    )


def _h2_10(index: ValidatedCorpusIndex) -> str:
    event = next(record.value for record in index.c001_events if record.contract_key == "proposal.approved")
    body = event.model_dump(mode="python", round_trip=True)
    assert_sod(body)
    body["basis"]["sod_check_passed"] = False
    _expect_violation(lambda: assert_sod(body), "SOD_VIOLATION")
    return "segregation-of-duties pass confirmed; failed result rejected"


def _h2_11(index: ValidatedCorpusIndex) -> str:
    v1, v2 = resolve_reporting_content(index)
    adjustment = assert_reporting_bridge(index, v1, v2)
    return f"June v1 and v2 hash-resolved; GBP {adjustment // 100:,.2f} bridge preserved"


_CHECKS = (
    ("H2-01", "F-P04", "Immediate causal order resolves", _h2_01),
    ("H2-02", "F-P05", "Money and balance reconcile", _h2_02),
    ("H2-03", "F-P06; F-N08", "Posting event-stream firewall holds", _h2_03),
    ("H2-04", "F-P07; F-N11", "Manifest reconciles and mutation fails", _h2_04),
    ("H2-06", "F-P09", "Restatement snapshots satisfy state guards", _h2_06),
    ("H2-07", "F-N13", "J-560 cannot post to hard-closed June", _h2_07),
    ("H2-08", "F-N14", "Manifest presentation remains in scope", _h2_08),
    ("H2-09", "F-N17; F-N18", "Hard close requires zero unresolved proposals", _h2_09),
    ("H2-10", "F-N19", "Approval requires segregation of duties", _h2_10),
    ("H2-11", "Artifact F 9.1; ADR-016", "Reporting content bridge resolves", _h2_11),
)


def run_h2(root: Path | None = None, *, h1_run: H1Run | None = None) -> H2Run:
    """Execute H2-01 through H2-11 over immutable conformance state."""

    h1 = h1_run or run_h1(root)
    if not h1.passed or h1.index is None:
        return H2Run(
            index=None,
            results=tuple(
                _result(
                    f"H2-{number:02d}",
                    "Artifact H H2",
                    AssertionStatus.BLOCKED,
                    "H1 must pass before H2",
                    "Blocked because H1 failed",
                )
                for number in range(1, 12)
            ),
        )

    index = h1.index
    projection: ReferencedJournalProjection | None = None
    try:
        projection = resolve_referenced_journal(index)
    except (TypeError, ValueError) as error:
        projection_error = error
    else:
        projection_error = None

    results: list[AssertionResult] = []
    for number in range(1, 12):
        test_id = f"H2-{number:02d}"
        if test_id == "H2-05":
            obligation = "F-P08; F-N20; F-EXE-001"
            expected = "Bind J-010 projection before equal-and-opposite proof"
            if projection_error is not None or projection is None:
                results.append(_fail(test_id, obligation, expected, projection_error or ValueError("missing projection")))
                continue
            def check(current: ValidatedCorpusIndex) -> str:
                if projection is None:
                    raise ValueError("missing projection")
                return _h2_05(current, projection)
        else:
            _, obligation, expected, check = next(item for item in _CHECKS if item[0] == test_id)
        try:
            actual = check(index)
        except (IntegrityViolation, KeyError, TypeError, ValueError) as error:
            results.append(_fail(test_id, obligation, expected, error))
        else:
            results.append(_pass(test_id, obligation, expected, actual))
    return H2Run(index=index, results=tuple(results))
