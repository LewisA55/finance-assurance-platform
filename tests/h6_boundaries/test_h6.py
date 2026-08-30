"""Artifact H H6 module-boundary acceptance tests."""

from dataclasses import replace

import pytest

from finance_assurance.validation.boundaries import BoundaryObservation
from finance_assurance.validation.boundary_trace import (
    G_CONTRACT_VERSION,
    BoundaryContractRegistry,
    BoundaryViolation,
    RecordingBoundaryRecorder,
)
from finance_assurance.validation.h5_replay import run_h5
from finance_assurance.validation.h6_boundaries import run_h6
from finance_assurance.validation.results import AssertionStatus


def observation(
    *,
    publisher: str = "Atlas",
    consumer: str = "Argus",
    contract_id: str = "G-04",
    subject_ref: str = "J-011",
    object_version: str | None = "J-011@v1",
) -> BoundaryObservation:
    return BoundaryObservation(
        sequence=1,
        publisher=publisher,
        consumer=consumer,
        contract_id=contract_id,
        contract_version=G_CONTRACT_VERSION,
        subject_ref=subject_ref,
        object_version=object_version,
        purpose="test probe",
        evidence_refs=("EVD-H6-TEST",),
    )


def rejection_code(observation: BoundaryObservation) -> str:
    rejection = BoundaryContractRegistry().validate(observation)
    assert rejection is not None
    return str(rejection.code)


def test_h6_passes_all_seventeen_artifact_g_assertions() -> None:
    run = run_h6()

    assert run.passed
    assert [result.test_id for result in run.results] == [
        f"H6-{number:02d}" for number in range(1, 18)
    ]
    assert {result.status for result in run.results} == {AssertionStatus.PASS}
    assert {item.contract_id for item in run.c001_trace} == {
        f"G-{number:02d}" for number in range(1, 13)
    }
    assert {item.contract_id for item in run.ct1_trace} == {
        "G-03",
        "G-04",
        "G-05",
        "G-07",
        "G-08",
        "G-09",
        "G-13",
    }


def test_boundary_recording_is_observational() -> None:
    replay = run_h5()
    assert replay.c001 is not None
    before = replay.c001.state.full_digest

    run = run_h6(h5_run=replay)

    assert run.passed
    assert replay.c001.state.full_digest == before


@pytest.mark.parametrize(
    ("probe", "expected_code"),
    [
        (
            observation(publisher="Argus"),
            "UNAUTHORIZED_PUBLISHER",
        ),
        (
            observation(publisher="Aegis", subject_ref="RC-001"),
            "UNAUTHORIZED_PUBLISHER",
        ),
        (
            observation(publisher="Pythia", contract_id="G-05"),
            "UNAUTHORIZED_PUBLISHER",
        ),
        (
            observation(consumer="Hermes"),
            "UNAUTHORIZED_CONSUMER",
        ),
        (
            observation(subject_ref="J-010"),
            "REFERENCED_STATE_AUTHORSHIP",
        ),
        (
            observation(
                publisher="SharedSubstrate",
                consumer="Atlas",
                contract_id="G-01",
                subject_ref="AE-C001-001",
                object_version=None,
            ),
            "INVALID_G01_INPUT",
        ),
        (
            observation(object_version=None),
            "UNVERSIONED_REFERENCE",
        ),
    ],
)
def test_prohibited_boundary_edges_are_rejected(
    probe: BoundaryObservation,
    expected_code: str,
) -> None:
    assert rejection_code(probe) == expected_code


def test_boundary_recorder_rejects_noncontiguous_or_invalid_observations() -> None:
    recorder = RecordingBoundaryRecorder()
    recorder.record(observation())

    with pytest.raises(BoundaryViolation) as sequence_error:
        recorder.record(observation())
    assert str(sequence_error.value.rejection.code) == "TRACE_SEQUENCE"

    invalid = replace(observation(), publisher="Argus")
    with pytest.raises(BoundaryViolation) as ownership_error:
        RecordingBoundaryRecorder().record(invalid)
    assert str(ownership_error.value.rejection.code) == "UNAUTHORIZED_PUBLISHER"


def test_controlled_use_requires_exact_versioned_readiness() -> None:
    registry = BoundaryContractRegistry()

    missing = registry.validate_controlled_use(
        reporting_version_ref="RV-2026-06@v2",
        readiness_product_ref=None,
        readiness_ref=None,
    )
    stale = registry.validate_controlled_use(
        reporting_version_ref="RV-2026-06@v2",
        readiness_product_ref="RV-2026-06@v1",
        readiness_ref="READY-C001-V1@v1",
    )
    exact = registry.validate_controlled_use(
        reporting_version_ref="RV-2026-06@v2",
        readiness_product_ref="RV-2026-06@v2",
        readiness_ref="READY-C001-V2@v1",
    )

    assert missing is not None and str(missing.code) == "READINESS_REQUIRED"
    assert stale is not None and str(stale.code) == "READINESS_VERSION_MISMATCH"
    assert exact is None
