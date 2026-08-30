"""Milestone 3 acceptance-catalogue and evidence-contract proofs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from finance_assurance.acceptance.report import SuiteCaseResult
from finance_assurance.product_acceptance.catalog import (
    ACCEPTANCE_CATALOG,
    validate_catalog,
)
from finance_assurance.product_acceptance.manual import evaluate_manual_evidence
from finance_assurance.product_acceptance.report import GateResult, build_report


def _passing_cases() -> tuple[SuiteCaseResult, ...]:
    patterns = sorted({pattern for criterion in ACCEPTANCE_CATALOG for pattern in criterion.evidence_tests})
    return tuple(SuiteCaseResult(f"tests.product::{item}", "PASS") for item in patterns)


def _passing_gates() -> tuple[GateResult, ...]:
    names = sorted({gate for criterion in ACCEPTANCE_CATALOG for gate in criterion.required_gates})
    return tuple(GateResult(item, "PASS", "passed") for item in names)


def test_milestone3_report_is_canonical_and_catalogue_is_closed() -> None:
    validate_catalog()
    assert len(ACCEPTANCE_CATALOG) == 33
    arguments = {
        "repository_revision": "a" * 40,
        "milestone2_report_digest": "sha256:" + "b" * 64,
        "test_cases": _passing_cases(),
        "application_build_digest": "c" * 64,
        "manual_evidence_digest": "sha256:" + "d" * 64,
        "quality_gates": _passing_gates(),
    }
    first = build_report(**arguments)  # type: ignore[arg-type]
    second = build_report(**arguments)  # type: ignore[arg-type]
    assert first.canonical_bytes == second.canonical_bytes
    assert first.overall == "PASS"
    assert first.status_counts == {"PASS": 33, "FAIL": 0, "BLOCKED": 0}


def test_manual_browser_evidence_is_revision_bound_and_complete(tmp_path: Path) -> None:
    revision = "a" * 40
    path = tmp_path / "manual.json"
    screenshot_hashes: dict[str, str] = {}
    for viewport in ("desktop", "tablet", "mobile"):
        screenshot = tmp_path / f"{viewport}.png"
        screenshot.write_bytes(f"{viewport}-proof".encode())
        screenshot_hashes[viewport] = (
            f"sha256:{hashlib.sha256(screenshot.read_bytes()).hexdigest()}"
        )
    path.write_text(
        json.dumps(
            {
                "schema_version": "milestone-3-manual-browser-evidence@v1",
                "repository_revision": revision,
                "reviewer": "Portfolio reviewer",
                "reviewed_at": "2026-08-11T12:00:00Z",
                "journeys": ["overview", "O-J01", "O-J02", "O-J03", "O-SJ01"],
                "viewports": [
                    {"name": "desktop", "width": 1440, "height": 900},
                    {"name": "tablet", "width": 768, "height": 1024},
                    {"name": "mobile", "width": 320, "height": 800},
                ],
                "checks": {
                    "keyboard_traversal": True,
                    "visible_focus": True,
                    "skip_and_bottom_navigation": True,
                    "screen_reader_names_and_order": True,
                    "no_horizontal_overflow": True,
                    "exact_context_preserved": True,
                    "screenshots_recorded": True,
                },
                "screenshots": [
                    {
                        "viewport": viewport,
                        "path": f"{viewport}.png",
                        "content_hash": screenshot_hashes[viewport],
                    }
                    for viewport in ("desktop", "tablet", "mobile")
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    result = evaluate_manual_evidence(path, repository_revision=revision)
    assert result.status == "PASS"
    assert result.evidence_digest is not None
    assert evaluate_manual_evidence(path, repository_revision="b" * 40).status == "FAIL"


def test_missing_manual_evidence_blocks_only_manual_acceptance(tmp_path: Path) -> None:
    manual = evaluate_manual_evidence(tmp_path / "missing.json", repository_revision="a" * 40)
    assert manual.status == "BLOCKED"
    gates = tuple(
        GateResult(item.gate_id, manual.status, manual.outcome)
        if item.gate_id == "manual_browser"
        else item
        for item in _passing_gates()
    )
    report = build_report(
        repository_revision="a" * 40,
        milestone2_report_digest="sha256:" + "b" * 64,
        test_cases=_passing_cases(),
        application_build_digest="c" * 64,
        manual_evidence_digest=None,
        quality_gates=gates,
    )
    assert report.overall == "BLOCKED"
    blocked = tuple(item.criterion_id for item in report.criteria if item.status == "BLOCKED")
    assert blocked == ("O-A28", "O-A29")
