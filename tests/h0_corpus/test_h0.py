"""Artifact H H0 acceptance tests."""

from pathlib import Path

import pytest

from finance_assurance.validation.h0 import run_h0
from finance_assurance.validation.results import AssertionStatus
from finance_assurance.validation.runner import HARNESS_HEADER, main


def test_h0_runner_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    assert main() == 0
    first = capsys.readouterr()

    assert main() == 0
    second = capsys.readouterr()

    assert first.out == second.out
    assert first.out == (
        f"{HARNESS_HEADER}\n"
        "H0 PASS (7/7)\n"
        "H1 PASS (14/14)\n"
        "H2 PASS (11/11)\n"
        "H3 PASS (18/18)\n"
        "H4 PASS (7/7)\n"
        "H5 PASS (2/2)\n"
        "H6 PASS (17/17)\n"
        "H7 PASS (4/4)\n"
        "H3-GUARD PASS (18/18)\n"
        "REPORT build/validation-report.json\n"
        "OVERALL PASS\n"
    )
    assert first.err == second.err == ""


def test_canonical_corpus_passes_all_seven_h0_assertions() -> None:
    run = run_h0()

    assert run.index is not None
    assert run.passed
    assert [result.test_id for result in run.results] == [
        "H0-01",
        "H0-02",
        "H0-03",
        "H0-04",
        "H0-05",
        "H0-06",
        "H0-07",
    ]
    assert {result.status for result in run.results} == {AssertionStatus.PASS}


def test_parse_failure_blocks_dependent_h0_assertions(tmp_path: Path) -> None:
    first_file = tmp_path / "canonical-object-payloads.jsonl"
    first_file.write_text("not-json", encoding="utf-8")

    run = run_h0(tmp_path)

    assert run.index is None
    assert run.results[0].status is AssertionStatus.FAIL
    assert all(
        result.status is AssertionStatus.BLOCKED for result in run.results[1:]
    )
