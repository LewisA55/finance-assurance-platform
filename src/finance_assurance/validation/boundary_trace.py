"""Artifact G semantic registry, ownership guard, and observational traces."""

from __future__ import annotations

import re
from dataclasses import dataclass

from finance_assurance.validation.boundaries import BoundaryObservation
from finance_assurance.validation.results import Rejection, RejectionCode
from finance_assurance.validation.scenarios import ScenarioReplay

G_CONTRACT_VERSION = "G-v0.2"
PRODUCT_MODULES = frozenset({"Hermes", "Atlas", "Argus", "Aegis", "Pythia"})
SUBSTRATE_BOUNDARY = "SharedSubstrate"

ATLAS_OWNED_ARTIFACT_F_TYPES = frozenset(
    {
        "posting_rule",
        "journal_proposal",
        "accounting_event",
        "journal_entry",
        "journal_line",
        "accounting_period",
        "reporting_version",
        "restatement_case",
    }
)

AUTHORITATIVE_WRITERS = {
    "business_event": "SourceDomain",
    **{object_type: "Atlas" for object_type in ATLAS_OWNED_ARTIFACT_F_TYPES},
    "admission_result": "Hermes",
    "reconciliation_result": "Hermes",
    "exception": "Argus",
    "finding": "Aegis",
    "issue": "Aegis",
    "remediation_directive": "Aegis",
    "readiness_assessment": "Aegis",
    "planning_input_snapshot": "Pythia",
    "forecast": "Pythia",
    "decision": "Pythia",
}

_ALLOWED_EDGES: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "G-01": (
        frozenset({"SourceDomain", SUBSTRATE_BOUNDARY, "ApprovedDecision"}),
        frozenset({SUBSTRATE_BOUNDARY, "Atlas", "Argus"}),
    ),
    "G-02": (
        frozenset({"Hermes"}),
        frozenset({SUBSTRATE_BOUNDARY, "Atlas", "Argus"}),
    ),
    "G-03": (
        frozenset({"Hermes"}),
        frozenset({"Argus", "Aegis", "Atlas"}),
    ),
    "G-04": (
        frozenset({"Atlas"}),
        frozenset({SUBSTRATE_BOUNDARY, "Argus", "Aegis", "Pythia"}),
    ),
    "G-05": (
        frozenset({"Atlas"}),
        frozenset({SUBSTRATE_BOUNDARY, "Argus", "Aegis", "Hermes"}),
    ),
    "G-06": (
        frozenset({"Atlas"}),
        frozenset({"Argus", "Aegis", "Pythia"}),
    ),
    "G-07": (
        frozenset({"Argus"}),
        frozenset({"Aegis", "Atlas"}),
    ),
    "G-08": (
        frozenset({"Aegis"}),
        frozenset({"Argus", "Atlas", "Pythia"}),
    ),
    "G-09": (frozenset({"Aegis"}), frozenset({"Atlas"})),
    "G-10": (frozenset({"Aegis"}), frozenset({"Pythia"})),
    "G-11": (frozenset({"Pythia"}), frozenset({"Argus", "Aegis"})),
    "G-12": (
        frozenset({"Pythia"}),
        frozenset({"Argus", "Aegis", "Atlas", "ApprovedDecision"}),
    ),
    "G-13": (
        frozenset({"AtlasReadBoundary"}),
        frozenset({"Argus", "CorrectionConstructor"}),
    ),
    "G-14": (
        frozenset({"Atlas"}),
        frozenset({"Aegis", "Argus"}),
    ),
}

_VERSION_REQUIRED = frozenset(
    {"G-02", "G-03", "G-04", "G-06", "G-07", "G-08", "G-10", "G-11", "G-12"}
)
_VERSION_PATTERN = re.compile(r".+@v[1-9][0-9]*$")


def boundary_contract_inventory() -> dict[str, object]:
    """Return deterministic Artifact G registry metadata for the H7 digest."""

    return {
        contract_id: {
            "publishers": sorted(publishers),
            "consumers": sorted(consumers),
            "contract_version": G_CONTRACT_VERSION,
            "object_version_required": contract_id in _VERSION_REQUIRED,
        }
        for contract_id, (publishers, consumers) in sorted(_ALLOWED_EDGES.items())
    }


def _reject(code: str, reason: str) -> Rejection:
    return Rejection(code=RejectionCode(code), reason=reason)


@dataclass(frozen=True, slots=True)
class BoundaryContractRegistry:
    """Validate proof metadata without defining any G domain payload."""

    def validate(self, observation: BoundaryObservation) -> Rejection | None:
        edge = _ALLOWED_EDGES.get(observation.contract_id)
        if edge is None:
            return _reject("UNKNOWN_G_CONTRACT", "G contract is not registered")
        publishers, consumers = edge
        if observation.publisher not in publishers:
            return _reject(
                "UNAUTHORIZED_PUBLISHER",
                "publisher does not own this G contract",
            )
        if observation.consumer not in consumers:
            return _reject(
                "UNAUTHORIZED_CONSUMER",
                "consumer is not registered for this G contract",
            )
        if observation.contract_version != G_CONTRACT_VERSION:
            return _reject(
                "UNKNOWN_CONTRACT_VERSION",
                "boundary trace must pin the ratified G contract version",
            )
        if observation.subject_ref == "J-010" and observation.contract_id in {
            "G-04",
            "G-05",
        }:
            return _reject(
                "REFERENCED_STATE_AUTHORSHIP",
                "J-010 may be consumed only through G-13",
            )
        if observation.contract_id == "G-01" and (
            observation.subject_ref is None
            or not observation.subject_ref.startswith("BE-")
        ):
            return _reject(
                "INVALID_G01_INPUT",
                "only a business-event identity may cross G-01",
            )
        if observation.contract_id in _VERSION_REQUIRED and (
            observation.object_version is None
            or _VERSION_PATTERN.fullmatch(observation.object_version) is None
        ):
            return _reject(
                "UNVERSIONED_REFERENCE",
                "cross-module consumption requires an exact object version",
            )
        return None

    def validate_controlled_use(
        self,
        *,
        reporting_version_ref: str,
        readiness_product_ref: str | None,
        readiness_ref: str | None,
    ) -> Rejection | None:
        if readiness_product_ref is None or readiness_ref is None:
            return _reject(
                "READINESS_REQUIRED",
                "controlled use requires exact purpose-specific readiness",
            )
        if (
            _VERSION_PATTERN.fullmatch(reporting_version_ref) is None
            or _VERSION_PATTERN.fullmatch(readiness_ref) is None
        ):
            return _reject(
                "UNVERSIONED_REFERENCE",
                "controlled use references must be fully versioned",
            )
        if reporting_version_ref != readiness_product_ref:
            return _reject(
                "READINESS_VERSION_MISMATCH",
                "readiness belongs to a different reporting product version",
            )
        return None


class BoundaryViolation(ValueError):
    def __init__(self, rejection: Rejection) -> None:
        self.rejection = rejection
        super().__init__(f"{rejection.code}: {rejection.reason}")


class RecordingBoundaryRecorder:
    """Mutable test observer whose records never participate in transitions."""

    def __init__(self, registry: BoundaryContractRegistry | None = None) -> None:
        self._registry = registry or BoundaryContractRegistry()
        self._observations: list[BoundaryObservation] = []

    @property
    def observations(self) -> tuple[BoundaryObservation, ...]:
        return tuple(self._observations)

    def record(self, observation: BoundaryObservation) -> None:
        if observation.sequence != len(self._observations) + 1:
            raise BoundaryViolation(
                _reject("TRACE_SEQUENCE", "boundary sequence must be contiguous")
            )
        rejection = self._registry.validate(observation)
        if rejection is not None:
            raise BoundaryViolation(rejection)
        self._observations.append(observation)


def _observation(
    sequence: int,
    publisher: str,
    consumer: str,
    contract_id: str,
    subject_ref: str,
    object_version: str | None,
    purpose: str,
    evidence_ref: str,
    *,
    event_id: str | None = None,
    command_id: str | None = None,
    upstream_refs: tuple[str, ...] = (),
    outcome: str = "ACCEPTED",
) -> BoundaryObservation:
    return BoundaryObservation(
        sequence=sequence,
        publisher=publisher,
        consumer=consumer,
        contract_id=contract_id,
        contract_version=G_CONTRACT_VERSION,
        subject_ref=subject_ref,
        object_version=object_version,
        event_id=event_id,
        command_id=command_id,
        purpose=purpose,
        upstream_refs=upstream_refs,
        evidence_refs=(evidence_ref,),
        outcome=outcome,  # type: ignore[arg-type]
    )


def record_c001_trace(replay: ScenarioReplay) -> tuple[BoundaryObservation, ...]:
    """Observe the ratified C-001 G-01..G-12 semantic handoffs."""

    if len(replay.state.event_log) != 11:
        raise ValueError("C-001 boundary trace requires a passing scenario replay")
    recorder = RecordingBoundaryRecorder()
    rows = (
        ("SourceDomain", "SharedSubstrate", "G-01", "BE-C001-RECOG-202606", None, "candidate source event", "EVD-C001-BE-001", None, ()),
        ("Hermes", "SharedSubstrate", "G-02", "ADM-C001", "ADM-C001@v1", "identity and provenance admission", "EVD-C001-BE-001", None, ("BE-C001-RECOG-202606",)),
        ("SharedSubstrate", "Atlas", "G-01", "BE-C001-RECOG-202606", None, "admitted posting input", "EVD-C001-BE-001", None, ("ADM-C001@v1",)),
        ("Atlas", "Argus", "G-04", "P-551", "P-551@v1", "read submitted and deferred proposal", "EVD-C001-002", None, ("BE-C001-RECOG-202606",)),
        ("Atlas", "Hermes", "G-05", "AE-C001-002", None, "source-to-accounting lineage", "EVD-C001-002", "AE-C001-002", ("P-551@v1",)),
        ("Hermes", "Argus", "G-03", "REC-C001-RECOG", "REC-C001-RECOG@v1", "recognition completeness reconciliation", "EVD-C001-004", None, ("P-551@v1",)),
        ("Atlas", "Argus", "G-06", "RV-2026-06", "RV-2026-06@v1", "freeze original reporting population", "RPT-C001-2026-06-V1", None, ("REC-C001-RECOG@v1",)),
        ("Argus", "Aegis", "G-07", "EXC-C001-RECOG", "EXC-C001-RECOG@v1", "publish completeness exception", "EVD-C001-004", None, ("RV-2026-06@v1",)),
        ("Aegis", "Atlas", "G-08", "ISS-C001-001", "ISS-C001-001@v1", "governed finding and issue", "EVD-C001-004", None, ("EXC-C001-RECOG@v1",)),
        ("Aegis", "Atlas", "G-09", "DIR-C001-001", None, "authorise restatement treatment", "EVD-C001-004", None, ("ISS-C001-001@v1",)),
        ("Aegis", "Pythia", "G-10", "READY-C001-V1", "READY-C001-V1@v1", "block unreliable revenue actuals", "EVD-C001-004", None, ("RV-2026-06@v1",)),
        ("Atlas", "Argus", "G-04", "RC-001", "RC-001@v5", "read published restatement objects", "EVD-C001-010", None, ("DIR-C001-001",)),
        ("Atlas", "Aegis", "G-05", "AE-C001-011", None, "prove accounting publication", "EVD-C001-011", "AE-C001-011", ("RC-001@v5",)),
        ("Atlas", "Pythia", "G-06", "RV-2026-06", "RV-2026-06@v2", "exact governed forecast actual", "RPT-C001-2026-06-V2", None, ("AE-C001-011",)),
        ("Argus", "Aegis", "G-07", "VERIFY-C001", "VERIFY-C001@v1", "verify correction and lineage", "EVD-C001-011", None, ("RV-2026-06@v2",)),
        ("Aegis", "Pythia", "G-10", "READY-C001-V2", "READY-C001-V2@v1", "approve exact forecast use", "EVD-C001-011", None, ("RV-2026-06@v2", "VERIFY-C001@v1")),
        ("Atlas", "Pythia", "G-06", "RV-2026-06", "RV-2026-06@v2", "pair reporting value with readiness", "RPT-C001-2026-06-V2", None, ("READY-C001-V2@v1",)),
        ("Pythia", "Argus", "G-11", "PLANINPUT-C001", "PLANINPUT-C001@v1", "freeze model inputs", "EVD-PYTHIA-C001-INPUT", None, ("RV-2026-06@v2", "READY-C001-V2@v1")),
        ("Pythia", "Aegis", "G-12", "DECISION-C001", "DECISION-C001@v1", "publish governed hiring decision", "EVD-PYTHIA-C001-DECISION", None, ("PLANINPUT-C001@v1",)),
        ("Pythia", "ApprovedDecision", "G-12", "DECISION-C001", "DECISION-C001@v1", "request operational approval", "EVD-PYTHIA-C001-DECISION", None, ("PLANINPUT-C001@v1",)),
        ("ApprovedDecision", "SharedSubstrate", "G-01", "BE-HIRING-DEFERRED-CANDIDATE", None, "return through normal admission", "EVD-PYTHIA-C001-DECISION", None, ("DECISION-C001@v1",)),
    )
    for row in rows:
        publisher, consumer, contract_id, subject, version, purpose, evidence, event, upstream = row
        recorder.record(
            _observation(
                len(recorder.observations) + 1,
                publisher,
                consumer,
                contract_id,
                subject,
                version,
                purpose,
                evidence,
                event_id=event,
                upstream_refs=upstream,
            )
        )
    return recorder.observations


def record_ct1_trace(replay: ScenarioReplay) -> tuple[BoundaryObservation, ...]:
    """Observe CT-1 without turning J-010 into authored Artifact F state."""

    if len(replay.state.event_log) != 6:
        raise ValueError("CT-1 boundary trace requires a passing scenario replay")
    recorder = RecordingBoundaryRecorder()
    source_hash = str(replay.state.referenced_state[0].source_hash)
    rows = (
        ("Hermes", "Argus", "G-03", "REC-CT1-CUSTOMER", "REC-CT1-CUSTOMER@v1", "customer identity reconciliation", "EVD-CT1-001", None, ()),
        ("AtlasReadBoundary", "Argus", "G-13", "J-010", source_hash, "read hash-bound pre-scope journal", "EVD-CT1-001", None, ("REC-CT1-CUSTOMER@v1",)),
        ("Argus", "Aegis", "G-07", "EXC-CT1-CASH", "EXC-CT1-CASH@v1", "publish cash application exception", "EVD-CT1-001", None, (source_hash,)),
        ("Aegis", "Atlas", "G-08", "ISS-CT1-001", "ISS-CT1-001@v1", "confirm wrong-customer issue", "EVD-CT1-001", None, ("EXC-CT1-CASH@v1",)),
        ("Aegis", "Atlas", "G-09", "DIR-CT1-001", None, "direct open-period correction", "EVD-CT1-001", None, ("ISS-CT1-001@v1",)),
        ("Atlas", "Argus", "G-04", "P-REV-010", "P-REV-010@v1", "read reversal proposal and J-011", "EVD-CT1-003", None, (source_hash, "DIR-CT1-001")),
        ("Atlas", "Aegis", "G-05", "AE-CT1-003", None, "publish reversal posting", "EVD-CT1-003", "AE-CT1-003", ("P-REV-010@v1",)),
        ("Atlas", "Argus", "G-04", "J-011", "J-011@v1", "verify immutable reversal", "EVD-CT1-003", None, (source_hash,)),
        ("Atlas", "Aegis", "G-05", "AE-CT1-006", None, "publish replacement posting", "EVD-CT1-006", "AE-CT1-006", ("P-REP-010@v1",)),
        ("Atlas", "Argus", "G-04", "J-012", "J-012@v1", "verify Orion replacement", "EVD-CT1-006", None, ("DIR-CT1-001",)),
        ("Argus", "Aegis", "G-07", "VERIFY-CT1", "VERIFY-CT1@v1", "verify reversal and replacement", "EVD-CT1-006", None, ("J-011@v1", "J-012@v1")),
        ("Aegis", "Argus", "G-08", "ISS-CT1-001", "ISS-CT1-001@v2", "verify remediation outcome", "EVD-CT1-006", None, ("VERIFY-CT1@v1",)),
    )
    for row in rows:
        publisher, consumer, contract_id, subject, version, purpose, evidence, event, upstream = row
        recorder.record(
            _observation(
                len(recorder.observations) + 1,
                publisher,
                consumer,
                contract_id,
                subject,
                version,
                purpose,
                evidence,
                event_id=event,
                upstream_refs=upstream,
            )
        )
    return recorder.observations
