"""Artifact H H7 deterministic reporting acceptance tests."""

from dataclasses import replace

import pytest

from finance_assurance.validation.h7_reporting import exit_code_for, run_h7
from finance_assurance.validation.report import (
    JsonFileReportSink,
    parse_report_bytes,
)
from finance_assurance.validation.results import AssertionStatus, StatusCount


def test_h7_accounts_for_all_eighty_assertions() -> None:
    run = run_h7()

    assert run.passed
    assert run.report.overall is AssertionStatus.PASS
    assert len(run.report.results) == 80
    assert len({result.test_id for result in run.report.results}) == 80
    assert [result.test_id for result in run.results] == [
        "H7-01",
        "H7-02",
        "H7-03",
        "H7-04",
    ]
    assert [(item.status, item.count) for item in run.report.status_counts] == [
        (AssertionStatus.PASS, 80),
        (AssertionStatus.FAIL, 0),
        (AssertionStatus.BLOCKED, 0),
    ]


def test_two_fresh_h7_runs_are_byte_identical() -> None:
    first = run_h7()
    second = run_h7()

    assert first.semantic_bytes == second.semantic_bytes
    assert first.report == second.report


def test_machine_report_round_trips_and_file_sink_preserves_bytes(tmp_path) -> None:
    run = run_h7()
    path = tmp_path / "validation-report.json"

    JsonFileReportSink(path).write(run.report)
    content = path.read_bytes()
    parsed = parse_report_bytes(content)

    assert content == run.semantic_bytes
    assert parsed["schema_version"] == "artifact-h-report@v1"
    assert parsed["overall"] == "PASS"
    assert parsed["fixture_inventory_digest"] == run.report.fixture_inventory_digest
    assert parsed["contract_inventory_digest"] == run.report.contract_inventory_digest
    assert parsed["c001_state_digest"] == run.report.c001_state_digest
    assert parsed["ct1_state_digest"] == run.report.ct1_state_digest
    assert all(
        {
            "test_id",
            "layer",
            "source_obligation",
            "status",
            "expected_outcome",
            "actual_outcome",
            "references",
            "before_digest",
            "after_digest",
            "failure_details",
        }.issubset(result)
        for result in parsed["results"]
    )


def test_failure_and_blocked_reports_return_nonzero() -> None:
    report = run_h7().report
    final = report.results[-1]
    failed_results = (*report.results[:-1], replace(final, status=AssertionStatus.FAIL))
    blocked_results = (
        *report.results[:-1],
        replace(final, status=AssertionStatus.BLOCKED),
    )
    failed = replace(
        report,
        status_counts=(
            StatusCount(AssertionStatus.PASS, 79),
            StatusCount(AssertionStatus.FAIL, 1),
            StatusCount(AssertionStatus.BLOCKED, 0),
        ),
        results=failed_results,
        overall=AssertionStatus.FAIL,
    )
    blocked = replace(
        report,
        status_counts=(
            StatusCount(AssertionStatus.PASS, 79),
            StatusCount(AssertionStatus.FAIL, 0),
            StatusCount(AssertionStatus.BLOCKED, 1),
        ),
        results=blocked_results,
        overall=AssertionStatus.BLOCKED,
    )

    assert exit_code_for(report) == 0
    assert exit_code_for(failed) == 1
    assert exit_code_for(blocked) == 1

    with pytest.raises(ValueError, match="overall status"):
        replace(report, overall=AssertionStatus.FAIL)
    with pytest.raises(ValueError, match="status counts"):
        replace(
            report,
            status_counts=(
                StatusCount(AssertionStatus.PASS, 79),
                StatusCount(AssertionStatus.FAIL, 1),
                StatusCount(AssertionStatus.BLOCKED, 0),
            ),
        )
