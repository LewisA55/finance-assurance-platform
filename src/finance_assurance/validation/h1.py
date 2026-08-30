"""Artifact H H1 strict contract-conformance assertions."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from finance_assurance.validation.canonical import canonical_bytes
from finance_assurance.validation.contracts.registry import (
    ContractViolation,
    validate_accounting_event,
    validate_object,
)
from finance_assurance.validation.corpus import RawCorpusIndex, thaw_json
from finance_assurance.validation.h0 import H0Run, run_h0
from finance_assurance.validation.index import (
    ValidatedCorpusIndex,
    build_validated_index,
)
from finance_assurance.validation.results import AssertionResult, AssertionStatus


@dataclass(frozen=True, slots=True)
class H1Run:
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
        layer="H1",
        source_obligation=obligation,
        status=status,
        expected_outcome=expected,
        actual_outcome=actual,
    )


def _payload(raw: RawCorpusIndex, fixture_id: str) -> tuple[str, dict[str, object]]:
    for name in ("canonical-object-payloads.jsonl", "restatement-case-snapshots.jsonl"):
        for record in raw.records(name):
            if record.value.get("fixture_id") == fixture_id:
                object_type = record.value.get("object_type")
                if not isinstance(object_type, str):
                    raise AssertionError("object_type is not a string")
                value = thaw_json(record.value.get("payload"))
                if not isinstance(value, dict):
                    raise AssertionError("payload is not an object")
                return object_type, value
    raise KeyError(fixture_id)


def _event(raw: RawCorpusIndex, event_id: str) -> dict[str, object]:
    for name in ("c001-accounting-events.jsonl", "ct1-accounting-events.jsonl"):
        for record in raw.records(name):
            if record.value.get("event_id") == event_id:
                value = thaw_json(record.value)
                if not isinstance(value, dict):
                    raise AssertionError("event is not an object")
                return value
    raise KeyError(event_id)


def _object_mutation(
    raw: RawCorpusIndex,
    fixture_id: str,
    mutate: Callable[[dict[str, object]], None],
) -> Callable[[], None]:
    def execute() -> None:
        object_type, source = _payload(raw, fixture_id)
        candidate = deepcopy(source)
        mutate(candidate)
        validate_object(object_type, candidate)

    return execute


def _event_mutation(
    raw: RawCorpusIndex,
    event_id: str,
    mutate: Callable[[dict[str, object]], None],
) -> Callable[[], None]:
    def execute() -> None:
        candidate = deepcopy(_event(raw, event_id))
        mutate(candidate)
        validate_accounting_event(candidate)

    return execute


def _nested(value: dict[str, object], key: str) -> dict[str, object]:
    nested = value[key]
    if not isinstance(nested, dict):
        raise AssertionError(f"{key} is not an object")
    return nested


def _positive_results(index: ValidatedCorpusIndex) -> list[AssertionResult]:
    object_count = len(index.objects)
    results = [
        _result(
            "H1-01",
            "F-P01",
            AssertionStatus.PASS,
            "Every canonical object payload validates under its selected contract",
            f"{object_count} canonical and lifecycle object payloads validated",
        ),
    ]
    for test_id, obligation, records, expected_count in (
        ("H1-02", "F-P02", index.c001_events, 11),
        ("H1-03", "F-P03", index.ct1_events, 6),
    ):
        mismatches = [
            record.raw.line_number
            for record in records
            if record.canonical_bytes != canonical_bytes(record.raw.value)
        ]
        if len(records) == expected_count and not mismatches:
            results.append(
                _result(
                    test_id,
                    obligation,
                    AssertionStatus.PASS,
                    f"{expected_count} events survive a canonical "
                    "byte-equivalent round trip",
                    f"{expected_count}/{expected_count} events byte-equivalent",
                ),
            )
        else:
            results.append(
                _result(
                    test_id,
                    obligation,
                    AssertionStatus.FAIL,
                    f"{expected_count} events survive a canonical "
                    "byte-equivalent round trip",
                    f"count={len(records)} mismatched_lines={mismatches}",
                ),
            )
    return results


def _negative_cases(raw: RawCorpusIndex) -> tuple[tuple[str, str, str, Callable[[], None]], ...]:
    return (
        (
            "H1-04",
            "F-N01",
            "UNKNOWN_FIELD",
            _object_mutation(raw, "OBJ-C001-BE-001", lambda value: value.__setitem__("unexpected", True)),
        ),
        (
            "H1-05",
            "F-N02",
            "NON_INTEGER_MONEY",
            _object_mutation(raw, "OBJ-C001-PROP-001", lambda value: value.__setitem__("total_debit_minor", 1000000.0)),
        ),
        (
            "H1-06",
            "F-N03",
            "INCOMPLETE_VERSION_REFERENCE",
            _object_mutation(raw, "OBJ-C001-PROP-001", lambda value: value.__setitem__("proposal_ref", "P-551")),
        ),
        (
            "H1-07",
            "F-N04",
            "INAPPLICABLE_CONDITIONAL_FIELD",
            _event_mutation(raw, "AE-C001-001", lambda value: value.__setitem__("idempotency_key", "invalid")),
        ),
        (
            "H1-08",
            "F-N05",
            "MISSING_REQUIRED_CONDITIONAL_FIELD",
            _event_mutation(raw, "AE-C001-007", lambda value: value.pop("idempotency_key")),
        ),
        (
            "H1-09",
            "F-N06",
            "UNEXERCISED_VARIANT",
            _object_mutation(raw, "OBJ-C001-JE-001", lambda value: value.__setitem__("entry_class", "AUTOMATED_POSTING")),
        ),
        (
            "H1-10",
            "F-N07",
            "UNKNOWN_DISCRIMINATOR",
            _event_mutation(raw, "AE-C001-001", lambda value: value.__setitem__("event_type", "proposal.voided")),
        ),
        (
            "H1-11",
            "F-N09",
            "CROSS_VARIANT_FIELD_LEAKAGE",
            _object_mutation(raw, "OBJ-CT1-PROP-001", lambda value: _nested(value, "origin_basis").__setitem__("corrects_journal_id", "J-010")),
        ),
        (
            "H1-12",
            "F-N10",
            "CROSS_VARIANT_FIELD_LEAKAGE",
            _object_mutation(raw, "OBJ-C001-PROP-002", lambda value: _nested(value, "origin_basis").__setitem__("reverses_journal_id", "J-010")),
        ),
        (
            "H1-13",
            "F-N12",
            "INCOMPLETE_VERSION_REFERENCE",
            _event_mutation(raw, "AE-C001-011", lambda value: _nested(value, "basis").__setitem__("predecessor_version_ref", "RV-2026-06")),
        ),
        (
            "H1-14",
            "F-N16",
            "OWNERSHIP_BOUNDARY_VIOLATION",
            _event_mutation(raw, "AE-C001-004", lambda value: _nested(_nested(value, "basis"), "trigger_ref").__setitem__("status", "OPEN")),
        ),
    )


def run_h1(root: Path | None = None, *, h0_run: H0Run | None = None) -> H1Run:
    """Execute H1-01 through H1-14 after a successful H0 dependency."""

    h0 = h0_run or run_h0(root)
    if not h0.passed or h0.index is None:
        blocked = tuple(
            _result(
                f"H1-{number:02d}",
                "Artifact F contract boundary",
                AssertionStatus.BLOCKED,
                "H0 must pass before H1",
                "Blocked because H0 failed",
            )
            for number in range(1, 15)
        )
        return H1Run(index=None, results=blocked)

    try:
        index = build_validated_index(h0.index)
    except (ContractViolation, TypeError, ValueError) as error:
        failed = _result(
            "H1-01",
            "F-P01",
            AssertionStatus.FAIL,
            "Every canonical object payload validates under its selected contract",
            str(error),
        )
        blocked = tuple(
            _result(
                f"H1-{number:02d}",
                "Artifact F contract boundary",
                AssertionStatus.BLOCKED,
                "H1-01 must construct the validated index",
                "Blocked because H1-01 failed",
            )
            for number in range(2, 15)
        )
        return H1Run(index=None, results=(failed, *blocked))

    results = _positive_results(index)
    for test_id, obligation, expected_code, execute in _negative_cases(h0.index):
        try:
            execute()
        except ContractViolation as error:
            actual_code = str(error.rejection.code)
            status = AssertionStatus.PASS if actual_code == expected_code else AssertionStatus.FAIL
            actual = f"rejected with {actual_code}"
        else:
            status = AssertionStatus.FAIL
            actual = "mutation was accepted"
        results.append(
            _result(
                test_id,
                obligation,
                status,
                f"rejected with {expected_code}",
                actual,
            ),
        )
    return H1Run(index=index, results=tuple(results))
