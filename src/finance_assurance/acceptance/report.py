"""Deterministic Milestone 2 report assembled from executable evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal
from xml.etree import ElementTree

from finance_assurance.acceptance.catalog import (
    ACCEPTANCE_CATALOG,
    AcceptanceCriterion,
    validate_catalog,
)
from finance_assurance.acceptance.runtime_proof import RuntimeEquivalenceProof
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256
from finance_assurance.runtime.digests import stable_value

Status = Literal["PASS", "FAIL", "BLOCKED"]


@dataclass(frozen=True, slots=True)
class SuiteCaseResult:
    test_id: str
    status: Literal["PASS", "FAIL", "ERROR", "SKIP"]


@dataclass(frozen=True, slots=True)
class CriterionResult:
    criterion_id: str
    statement: str
    status: Status
    evidence_test_ids: tuple[str, ...]
    actual_outcome: str


@dataclass(frozen=True, slots=True)
class QualityGates:
    ruff: Status
    pytest: Status
    h0_h7: Status
    runtime_equivalence: Status
    runtime_independence: Status
    bounded_scope: Status
    clean_checkout: Status


@dataclass(frozen=True, slots=True)
class Milestone2Report:
    schema_version: str
    repository_revision: str | None
    h0_h7_report_digest: str
    test_inventory_digest: str
    test_count: int
    runtime_proofs: tuple[RuntimeEquivalenceProof, ...]
    quality_gates: QualityGates
    criteria: tuple[CriterionResult, ...]
    status_counts: dict[str, int]
    overall: Status

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_bytes(stable_value(self))


def parse_junit(payload: bytes) -> tuple[SuiteCaseResult, ...]:
    """Read only deterministic test identity and outcome from pytest JUnit XML."""

    root = ElementTree.fromstring(payload)
    results: list[SuiteCaseResult] = []
    for case in root.iter("testcase"):
        identity = f"{case.attrib['classname']}::{case.attrib['name']}"
        if case.find("failure") is not None:
            status = "FAIL"
        elif case.find("error") is not None:
            status = "ERROR"
        elif case.find("skipped") is not None:
            status = "SKIP"
        else:
            status = "PASS"
        results.append(SuiteCaseResult(identity, status))
    return tuple(sorted(results, key=lambda item: item.test_id))


def _criterion_evidence(
    criterion: AcceptanceCriterion,
    test_cases: tuple[SuiteCaseResult, ...],
) -> tuple[Status, tuple[str, ...], str]:
    matched: list[SuiteCaseResult] = []
    missing: list[str] = []
    for pattern in criterion.evidence_tests:
        found = tuple(item for item in test_cases if pattern in item.test_id)
        if not found:
            missing.append(pattern)
        matched.extend(found)
    unique = {item.test_id: item for item in matched}
    evidence = tuple(sorted(unique))
    if missing:
        return "BLOCKED", evidence, f"missing evidence: {', '.join(missing)}"
    failures = tuple(
        item.test_id for item in unique.values() if item.status != "PASS"
    )
    if failures:
        return "FAIL", evidence, f"non-passing evidence: {', '.join(failures)}"
    return "PASS", evidence, f"{len(evidence)} executable evidence test(s) passed"


def _status_counts(criteria: tuple[CriterionResult, ...]) -> dict[str, int]:
    return {
        status: sum(item.status == status for item in criteria)
        for status in ("PASS", "FAIL", "BLOCKED")
    }


def build_report(
    *,
    repository_revision: str | None,
    h0_h7_report: bytes,
    h0_h7_passed: bool,
    test_cases: tuple[SuiteCaseResult, ...],
    pytest_passed: bool,
    ruff_passed: bool,
    runtime_proofs: tuple[RuntimeEquivalenceProof, ...],
    runtime_proofs_reproducible: bool,
    runtime_independent: bool,
    bounded_scope: bool,
    clean_checkout: bool,
) -> Milestone2Report:
    """Build the closed M2-A01..M2-A19 report without timestamps or paths."""

    validate_catalog()
    proof_passed = bool(
        runtime_proofs
        and all(item.passed for item in runtime_proofs)
        and runtime_proofs_reproducible
    )
    gates = QualityGates(
        ruff="PASS" if ruff_passed else "FAIL",
        pytest="PASS" if pytest_passed else "FAIL",
        h0_h7="PASS" if h0_h7_passed else "FAIL",
        runtime_equivalence="PASS" if proof_passed else "FAIL",
        runtime_independence="PASS" if runtime_independent else "FAIL",
        bounded_scope="PASS" if bounded_scope else "FAIL",
        clean_checkout="PASS" if clean_checkout else "BLOCKED",
    )
    criteria: list[CriterionResult] = []
    for criterion in ACCEPTANCE_CATALOG:
        status, evidence, actual = _criterion_evidence(criterion, test_cases)
        required_gate: Status | None = None
        if criterion.criterion_id == "M2-A08":
            required_gate = gates.runtime_equivalence
        elif criterion.criterion_id == "M2-A15":
            required_gate = gates.runtime_independence
        elif criterion.criterion_id == "M2-A16":
            required_gate = gates.h0_h7
        elif criterion.criterion_id == "M2-A18":
            required_gate = gates.bounded_scope
        elif criterion.criterion_id == "M2-A19":
            required_gate = (
                "PASS"
                if all(
                    gate == "PASS"
                    for gate in (
                        gates.ruff,
                        gates.pytest,
                        gates.h0_h7,
                        gates.runtime_equivalence,
                        gates.clean_checkout,
                    )
                )
                else (
                    "BLOCKED" if gates.clean_checkout == "BLOCKED" else "FAIL"
                )
            )
        if status == "PASS" and required_gate != "PASS" and required_gate is not None:
            status = required_gate
            actual = f"required acceptance gate is {required_gate.lower()}"
        criteria.append(
            CriterionResult(
                criterion_id=criterion.criterion_id,
                statement=criterion.statement,
                status=status,
                evidence_test_ids=evidence,
                actual_outcome=actual,
            )
        )
    frozen = tuple(criteria)
    gate_values = tuple(stable_value(gates).values())
    statuses = {item.status for item in frozen} | set(gate_values)
    if "FAIL" in statuses:
        overall: Status = "FAIL"
    elif "BLOCKED" in statuses:
        overall = "BLOCKED"
    else:
        overall = "PASS"
    return Milestone2Report(
        schema_version="milestone-2-acceptance-report@v1",
        repository_revision=repository_revision,
        h0_h7_report_digest=f"sha256:{hashlib.sha256(h0_h7_report).hexdigest()}",
        test_inventory_digest=canonical_sha256(stable_value(test_cases)),
        test_count=len(test_cases),
        runtime_proofs=runtime_proofs,
        quality_gates=gates,
        criteria=frozen,
        status_counts=_status_counts(frozen),
        overall=overall,
    )
