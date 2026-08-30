"""Deterministic Milestone 3 report assembled from bounded evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from finance_assurance.acceptance.report import SuiteCaseResult
from finance_assurance.product_acceptance.catalog import (
    ACCEPTANCE_CATALOG,
    AcceptanceCriterion,
    validate_catalog,
)
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256
from finance_assurance.runtime.digests import stable_value

Status = Literal["PASS", "FAIL", "BLOCKED"]


@dataclass(frozen=True, slots=True)
class GateResult:
    gate_id: str
    status: Status
    outcome: str


@dataclass(frozen=True, slots=True)
class CriterionResult:
    criterion_id: str
    statement: str
    status: Status
    evidence_test_ids: tuple[str, ...]
    required_gate_ids: tuple[str, ...]
    actual_outcome: str


@dataclass(frozen=True, slots=True)
class Milestone3Report:
    schema_version: str
    repository_revision: str | None
    milestone2_report_digest: str | None
    test_inventory_digest: str
    test_count: int
    application_build_digest: str | None
    manual_evidence_digest: str | None
    quality_gates: tuple[GateResult, ...]
    criteria: tuple[CriterionResult, ...]
    status_counts: dict[str, int]
    overall: Status

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_bytes(stable_value(self))


def _test_evidence(criterion: AcceptanceCriterion, test_cases: tuple[SuiteCaseResult, ...]) -> tuple[Status, tuple[str, ...], str]:
    matched: dict[str, SuiteCaseResult] = {}
    missing: list[str] = []
    for pattern in criterion.evidence_tests:
        found = tuple(item for item in test_cases if pattern in item.test_id)
        if not found:
            missing.append(pattern)
        matched.update((item.test_id, item) for item in found)
    evidence = tuple(sorted(matched))
    if missing:
        return "BLOCKED", evidence, f"missing tests: {', '.join(missing)}"
    failures = tuple(item.test_id for item in matched.values() if item.status != "PASS")
    if failures:
        return "FAIL", evidence, f"non-passing tests: {', '.join(sorted(failures))}"
    return "PASS", evidence, f"{len(evidence)} executable test(s) passed"


def build_report(*, repository_revision: str | None, milestone2_report_digest: str | None, test_cases: tuple[SuiteCaseResult, ...], application_build_digest: str | None, manual_evidence_digest: str | None, quality_gates: tuple[GateResult, ...]) -> Milestone3Report:
    """Build the closed O-A01..O-A33 report without timestamps or host paths."""

    validate_catalog()
    gate_map = {item.gate_id: item for item in quality_gates}
    if len(gate_map) != len(quality_gates):
        raise ValueError("Milestone 3 quality-gate identities must be unique")
    criteria: list[CriterionResult] = []
    for criterion in ACCEPTANCE_CATALOG:
        status, evidence, actual = _test_evidence(criterion, test_cases)
        missing_gates = tuple(gate for gate in criterion.required_gates if gate not in gate_map)
        if missing_gates:
            status, actual = "BLOCKED", f"missing gates: {', '.join(missing_gates)}"
        else:
            required = tuple(gate_map[gate] for gate in criterion.required_gates)
            if any(item.status == "FAIL" for item in required):
                status = "FAIL"
                actual = "required gate failed: " + ", ".join(item.gate_id for item in required if item.status == "FAIL")
            elif status == "PASS" and any(item.status == "BLOCKED" for item in required):
                status = "BLOCKED"
                actual = "required gate blocked: " + ", ".join(item.gate_id for item in required if item.status == "BLOCKED")
        criteria.append(CriterionResult(criterion.criterion_id, criterion.statement, status, evidence, criterion.required_gates, actual))
    frozen = tuple(criteria)
    statuses = {item.status for item in frozen} | {item.status for item in quality_gates}
    overall: Status = "FAIL" if "FAIL" in statuses else "BLOCKED" if "BLOCKED" in statuses else "PASS"
    return Milestone3Report("milestone-3-acceptance-report@v1", repository_revision, milestone2_report_digest, canonical_sha256(stable_value(test_cases)), len(test_cases), application_build_digest, manual_evidence_digest, quality_gates, frozen, {value: sum(item.status == value for item in frozen) for value in ("PASS", "FAIL", "BLOCKED")}, overall)
