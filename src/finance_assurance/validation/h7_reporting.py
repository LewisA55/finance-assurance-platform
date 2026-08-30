"""Artifact H H7 aggregation, machine report, and reproducibility proof."""

from __future__ import annotations

import subprocess
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path

from finance_assurance.validation.canonical import canonical_sha256
from finance_assurance.validation.contracts.objects import OBJECT_ADAPTERS
from finance_assurance.validation.h0 import H0Run, run_h0
from finance_assurance.validation.h1 import H1Run, run_h1
from finance_assurance.validation.h2 import H2Run, run_h2
from finance_assurance.validation.h3_guards import H3GuardRun, run_h3_guards
from finance_assurance.validation.h3_stateful import H3Run, run_h3
from finance_assurance.validation.h4_stateful import H4Run, run_h4
from finance_assurance.validation.h5_replay import H5Run, run_h5
from finance_assurance.validation.h6_boundaries import H6Run, run_h6
from finance_assurance.validation.report import (
    MemoryReportSink,
    parse_report_bytes,
    report_bytes,
)
from finance_assurance.validation.results import (
    AssertionResult,
    AssertionStatus,
    StatusCount,
    ValidationReport,
)
from finance_assurance.validation.state import stable_value


@dataclass(frozen=True, slots=True)
class LowerLayerRuns:
    h0: H0Run
    h1: H1Run
    h2: H2Run
    h3_guards: H3GuardRun
    h3: H3Run
    h4: H4Run
    h5: H5Run
    h6: H6Run

    @property
    def results(self) -> tuple[AssertionResult, ...]:
        return (
            *self.h0.results,
            *self.h1.results,
            *self.h2.results,
            *self.h3.results,
            *self.h4.results,
            *self.h5.results,
            *self.h6.results,
        )

    @property
    def passed(self) -> bool:
        return all(
            (
                self.h0.passed,
                self.h1.passed,
                self.h2.passed,
                self.h3_guards.passed,
                self.h3.passed,
                self.h4.passed,
                self.h5.passed,
                self.h6.passed,
            )
        )


@dataclass(frozen=True, slots=True)
class H7Run:
    results: tuple[AssertionResult, ...]
    report: ValidationReport
    semantic_bytes: bytes
    lower: LowerLayerRuns

    @property
    def passed(self) -> bool:
        return all(result.status is AssertionStatus.PASS for result in self.results)


def execute_lower_layers(root: Path | None = None) -> LowerLayerRuns:
    """Run H0-H6 once with each layer consuming the prior result."""

    h0 = run_h0(root)
    h1 = run_h1(root, h0_run=h0)
    h2 = run_h2(root, h1_run=h1)
    guards = run_h3_guards(root, h2_run=h2)
    h3 = run_h3(root, h2_run=h2, guard_run=guards)
    h4 = run_h4(root, h2_run=h2)
    h5 = run_h5(root, h2_run=h2, h3_run=h3, h4_run=h4)
    h6 = run_h6(root, h4_run=h4, h5_run=h5)
    return LowerLayerRuns(h0, h1, h2, guards, h3, h4, h5, h6)


def _repository_revision(root: Path | None) -> str | None:
    cwd = root or Path(__file__).resolve().parents[3]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    revision = result.stdout.strip()
    return revision or None


def _fixture_inventory_digest(lower: LowerLayerRuns) -> str:
    if lower.h0.index is None:
        return canonical_sha256({"fixture_inventory": "unavailable"})
    return canonical_sha256(
        {
            fixture_file.name: [record.raw_text for record in fixture_file.records]
            for fixture_file in lower.h0.index.files
        }
    )


def _contract_inventory_digest(lower: LowerLayerRuns) -> str:
    event_types: list[str] = []
    if lower.h2.index is not None:
        event_types = sorted({str(item.value.event_type) for item in lower.h2.index.events})
    return canonical_sha256(
        {
            "object_contracts": sorted(OBJECT_ADAPTERS),
            "accounting_event_contracts": event_types,
            "g_contracts": [f"G-{number:02d}" for number in range(1, 15)],
        }
    )


def _state_digests(lower: LowerLayerRuns) -> tuple[str, str]:
    if lower.h5.c001 is None or lower.h5.ct1 is None:
        missing = canonical_sha256({"state": "unavailable"})
        return missing, missing
    return lower.h5.c001.state.full_digest, lower.h5.ct1.state.full_digest


def _semantic_seed(lower: LowerLayerRuns) -> dict[str, object]:
    c001, ct1 = _state_digests(lower)
    return {
        "fixture_inventory_digest": _fixture_inventory_digest(lower),
        "contract_inventory_digest": _contract_inventory_digest(lower),
        "results": stable_value(lower.results),
        "c001_state_digest": c001,
        "ct1_state_digest": ct1,
        "c001_trace": stable_value(lower.h6.c001_trace),
        "ct1_trace": stable_value(lower.h6.ct1_trace),
        "control_trace": stable_value(lower.h6.control_trace),
    }


def _status_counts(results: tuple[AssertionResult, ...]) -> tuple[StatusCount, ...]:
    counts = Counter(item.status for item in results)
    return tuple(StatusCount(status, counts[status]) for status in AssertionStatus)


def _report(
    lower: LowerLayerRuns,
    h7_results: tuple[AssertionResult, ...],
    root: Path | None,
) -> ValidationReport:
    results = (*lower.results, *h7_results)
    c001, ct1 = _state_digests(lower)
    statuses = {item.status for item in results}
    if AssertionStatus.FAIL in statuses:
        overall = AssertionStatus.FAIL
    elif AssertionStatus.BLOCKED in statuses:
        overall = AssertionStatus.BLOCKED
    else:
        overall = AssertionStatus.PASS
    return ValidationReport(
        schema_version="artifact-h-report@v1",
        repository_revision=_repository_revision(root),
        fixture_inventory_digest=_fixture_inventory_digest(lower),
        contract_inventory_digest=_contract_inventory_digest(lower),
        status_counts=_status_counts(results),
        results=results,
        c001_state_digest=c001,
        ct1_state_digest=ct1,
        overall=overall,
    )


def exit_code_for(report: ValidationReport) -> int:
    return 0 if report.overall is AssertionStatus.PASS else 1


def _assertion(number: int, passed: bool, actual: str) -> AssertionResult:
    return AssertionResult(
        test_id=f"H7-{number:02d}",
        layer="H7",
        source_obligation="Artifact H section 16",
        status=AssertionStatus.PASS if passed else AssertionStatus.FAIL,
        expected_outcome="deterministic complete assertion reporting",
        actual_outcome=actual,
        references=("Artifact H section 16",),
    )


def run_h7(
    root: Path | None = None,
    *,
    lower_run: LowerLayerRuns | None = None,
) -> H7Run:
    """Build the complete H0-H7 report and prove two-run semantic equality."""

    lower_a = lower_run or execute_lower_layers(root)
    lower_b = execute_lower_layers(root)
    expected_counts = {
        "H0": 7,
        "H1": 14,
        "H2": 11,
        "H3": 18,
        "H4": 7,
        "H5": 2,
        "H6": 17,
    }
    layer_counts = Counter(item.layer for item in lower_a.results)
    unique_ids = len({item.test_id for item in lower_a.results}) == len(
        lower_a.results
    )
    complete = bool(
        layer_counts == expected_counts
        and unique_ids
        and all(
            item.test_id
            and item.source_obligation
            and item.expected_outcome
            and item.actual_outcome
            for item in lower_a.results
        )
    )
    metadata = bool(
        _fixture_inventory_digest(lower_a).startswith("sha256:")
        and _contract_inventory_digest(lower_a).startswith("sha256:")
        and all(value.startswith("sha256:") for value in _state_digests(lower_a))
    )
    reproducible = _semantic_seed(lower_a) == _semantic_seed(lower_b)

    h7_results = (
        _assertion(1, complete, f"{len(lower_a.results)} unique H0-H6 assertions"),
        _assertion(2, metadata, "inventory and terminal-state digests populated"),
        _assertion(3, reproducible, "fresh H0-H6 runs are semantically identical"),
        _assertion(4, True, "canonical JSON and exit semantics verified"),
    )
    if not lower_a.passed:
        h7_results = tuple(
            replace(
                item,
                status=AssertionStatus.BLOCKED,
                actual_outcome="blocked because a required lower layer did not pass",
            )
            for item in h7_results
        )

    report = _report(lower_a, h7_results, root)
    sink = MemoryReportSink()
    sink.write(report)
    sink_content = sink.content or b""
    parsed = parse_report_bytes(sink_content)
    exit_semantics_ok = exit_code_for(report) == (
        0 if report.overall is AssertionStatus.PASS else 1
    )
    if report.overall is AssertionStatus.PASS:
        final = report.results[-1]
        failed_results = (
            *report.results[:-1],
            replace(final, status=AssertionStatus.FAIL),
        )
        blocked_results = (
            *report.results[:-1],
            replace(final, status=AssertionStatus.BLOCKED),
        )
        failed_report = replace(
            report,
            status_counts=_status_counts(failed_results),
            results=failed_results,
            overall=AssertionStatus.FAIL,
        )
        blocked_report = replace(
            report,
            status_counts=_status_counts(blocked_results),
            results=blocked_results,
            overall=AssertionStatus.BLOCKED,
        )
        exit_semantics_ok = bool(
            exit_semantics_ok
            and exit_code_for(failed_report) == 1
            and exit_code_for(blocked_report) == 1
        )
    sink_ok = bool(
        sink_content == report_bytes(report)
        and parsed.get("schema_version") == "artifact-h-report@v1"
        and parsed.get("overall") == report.overall.value
        and exit_semantics_ok
    )
    if not sink_ok and lower_a.passed:
        h7_results = (
            *h7_results[:3],
            _assertion(4, False, "machine report round-trip or exit semantics failed"),
        )
        report = _report(lower_a, h7_results, root)
        sink_content = report_bytes(report)

    return H7Run(h7_results, report, sink_content, lower_a)
