"""Phase 7 acceptance-catalogue and report-contract proofs."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from finance_assurance.acceptance.catalog import ACCEPTANCE_CATALOG, validate_catalog
from finance_assurance.acceptance.report import (
    SuiteCaseResult,
    build_report,
    parse_junit,
)
from finance_assurance.acceptance.runner import _run
from finance_assurance.acceptance.runtime_proof import RuntimeEquivalenceProof
from finance_assurance.acceptance.scope import (
    deferred_surface_violations,
    runtime_validation_imports,
)


def test_milestone2_scope_excludes_deferred_product_surfaces() -> None:
    assert deferred_surface_violations() == ()
    assert runtime_validation_imports() == ()


def test_milestone2_report_is_canonical_and_catalogue_is_closed() -> None:
    validate_catalog()
    assert len(ACCEPTANCE_CATALOG) == 19
    patterns = sorted(
        {
            pattern
            for criterion in ACCEPTANCE_CATALOG
            for pattern in criterion.evidence_tests
        }
    )
    cases = tuple(
        SuiteCaseResult(f"tests.acceptance::{item}", "PASS") for item in patterns
    )
    proofs = (
        RuntimeEquivalenceProof("C001", "sha256:a", "sha256:a", "sha256:a", 11, 24),
        RuntimeEquivalenceProof("CT1", "sha256:b", "sha256:b", "sha256:b", 6, 14),
    )
    arguments = {
        "repository_revision": "a" * 40,
        "h0_h7_report": b"{}",
        "h0_h7_passed": True,
        "test_cases": cases,
        "pytest_passed": True,
        "ruff_passed": True,
        "runtime_proofs": proofs,
        "runtime_proofs_reproducible": True,
        "runtime_independent": True,
        "bounded_scope": True,
        "clean_checkout": True,
    }
    first = build_report(**arguments)  # type: ignore[arg-type]
    second = build_report(**arguments)  # type: ignore[arg-type]
    assert first.canonical_bytes == second.canonical_bytes
    assert first.overall == "PASS"
    assert first.status_counts == {"PASS": 19, "FAIL": 0, "BLOCKED": 0}


def test_junit_parser_ignores_time_host_and_timestamp_metadata() -> None:
    first = b'''<testsuites><testsuite time="1" hostname="a">
    <testcase classname="tests.x" name="test_one" time="0.1" />
    </testsuite></testsuites>'''
    second = b'''<testsuites><testsuite time="9" hostname="b">
    <testcase classname="tests.x" name="test_one" time="8.7" />
    </testsuite></testsuites>'''
    assert parse_junit(first) == parse_junit(second)


def test_clean_checkout_is_a_required_m2_a19_gate() -> None:
    patterns = sorted(
        {
            pattern
            for criterion in ACCEPTANCE_CATALOG
            for pattern in criterion.evidence_tests
        }
    )
    cases = tuple(
        SuiteCaseResult(f"tests.acceptance::{item}", "PASS") for item in patterns
    )
    proof = RuntimeEquivalenceProof(
        "C001", "sha256:a", "sha256:a", "sha256:a", 11, 24
    )
    report = build_report(
        repository_revision=None,
        h0_h7_report=b"{}",
        h0_h7_passed=True,
        test_cases=cases,
        pytest_passed=True,
        ruff_passed=True,
        runtime_proofs=(proof,),
        runtime_proofs_reproducible=True,
        runtime_independent=True,
        bounded_scope=True,
        clean_checkout=False,
    )
    criterion = next(item for item in report.criteria if item.criterion_id == "M2-A19")
    assert criterion.status == "BLOCKED"
    assert report.overall == "BLOCKED"


def test_acceptance_timeout_becomes_a_failed_process(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def expire(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(("slow",), 600, output=b"partial")

    monkeypatch.setattr(subprocess, "run", expire)
    result = _run(("slow",), tmp_path)
    assert result.returncode == 124
    assert result.stdout == "partial"
    assert "timed out" in result.stderr
