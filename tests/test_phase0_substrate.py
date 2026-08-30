"""Phase 0 acceptance tests for the validation-harness substrate."""

from dataclasses import FrozenInstanceError

import pytest

from finance_assurance.validation.boundaries import (
    BoundaryObservation,
    BoundaryRecorder,
)
from finance_assurance.validation.report import ReportSink
from finance_assurance.validation.results import (
    AssertionResult,
    AssertionStatus,
    Detail,
    Rejection,
    RejectionCode,
    ValidationReport,
)


class InMemoryBoundaryRecorder:
    """Minimal structural implementation used only to prove the protocol."""

    def __init__(self) -> None:
        self.observations: list[BoundaryObservation] = []

    def record(self, observation: BoundaryObservation) -> None:
        self.observations.append(observation)


class InMemoryReportSink:
    """Minimal structural implementation used only to prove the protocol."""

    def __init__(self) -> None:
        self.reports: list[ValidationReport] = []

    def write(self, report: ValidationReport) -> None:
        self.reports.append(report)


def test_result_and_rejection_values_are_immutable() -> None:
    result = AssertionResult(
        test_id="PHASE0-PROTOCOL",
        layer="PHASE0",
        source_obligation="Phase 0 protocol",
        status=AssertionStatus.PASS,
        expected_outcome="Value is immutable",
        actual_outcome="Value is immutable",
    )
    rejection = Rejection(
        code=RejectionCode("INVALID_TRANSITION"),
        reason="The transition is not permitted.",
        details=(Detail("state", "HARD_CLOSED"),),
    )

    with pytest.raises(FrozenInstanceError):
        result.actual_outcome = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        rejection.reason = "mutated"  # type: ignore[misc]


@pytest.mark.parametrize(
    "value",
    ["", "lowercase", "HAS-HYPHEN", "1STARTS_WITH_DIGIT"],
)
def test_rejection_code_rejects_unstable_forms(value: str) -> None:
    with pytest.raises(ValueError, match="rejection code"):
        RejectionCode(value)


def test_boundary_observation_requires_a_traceable_subject() -> None:
    with pytest.raises(ValueError, match="object_version, event_id, or command_id"):
        BoundaryObservation(
            sequence=0,
            publisher="Atlas",
            consumer="Argus",
            contract_id="G-05",
            purpose="lineage",
        )


def test_boundary_observation_supports_g14_without_a_domain_subject() -> None:
    observation = BoundaryObservation(
        sequence=0,
        publisher="Atlas",
        consumer="Aegis",
        contract_id="G-14",
        purpose="pre-construction rejection",
        command_id="CMD-INVALID-001",
    )

    assert observation.object_version is None
    assert observation.event_id is None
    assert observation.command_id == "CMD-INVALID-001"


def test_protocols_accept_structural_implementations() -> None:
    recorder: BoundaryRecorder = InMemoryBoundaryRecorder()
    sink: ReportSink = InMemoryReportSink()

    assert isinstance(recorder, BoundaryRecorder)
    assert isinstance(sink, ReportSink)
