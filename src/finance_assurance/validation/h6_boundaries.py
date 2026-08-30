"""Artifact H H6 ownership and module-boundary conformance assertions."""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

from finance_assurance.validation.boundaries import BoundaryObservation
from finance_assurance.validation.boundary_trace import (
    ATLAS_OWNED_ARTIFACT_F_TYPES,
    AUTHORITATIVE_WRITERS,
    G_CONTRACT_VERSION,
    PRODUCT_MODULES,
    SUBSTRATE_BOUNDARY,
    BoundaryContractRegistry,
    record_c001_trace,
    record_ct1_trace,
)
from finance_assurance.validation.contracts.objects import OBJECT_ADAPTERS
from finance_assurance.validation.dispatcher import dispatch
from finance_assurance.validation.h4_stateful import H4Run, run_h4
from finance_assurance.validation.h5_replay import H5Run, run_h5
from finance_assurance.validation.planner import ApplyRemediationDirective
from finance_assurance.validation.results import (
    AssertionResult,
    AssertionStatus,
    Rejection,
)
from finance_assurance.validation.state import HarnessState


@dataclass(frozen=True, slots=True)
class H6Run:
    results: tuple[AssertionResult, ...]
    c001_trace: tuple[BoundaryObservation, ...]
    ct1_trace: tuple[BoundaryObservation, ...]
    control_trace: tuple[BoundaryObservation, ...]

    @property
    def passed(self) -> bool:
        return all(result.status is AssertionStatus.PASS for result in self.results)


def _result(number: int, passed: bool, actual: str) -> AssertionResult:
    test_id = f"H6-{number:02d}"
    return AssertionResult(
        test_id=test_id,
        layer="H6",
        source_obligation=f"G-A{number:02d}",
        status=AssertionStatus.PASS if passed else AssertionStatus.FAIL,
        expected_outcome=f"Artifact G acceptance G-A{number:02d} holds",
        actual_outcome=actual,
        references=(f"G-A{number:02d}",),
    )


def _observation(
    *,
    publisher: str,
    consumer: str,
    contract_id: str,
    subject_ref: str,
    object_version: str | None = None,
) -> BoundaryObservation:
    return BoundaryObservation(
        sequence=1,
        publisher=publisher,
        consumer=consumer,
        contract_id=contract_id,
        contract_version=G_CONTRACT_VERSION,
        subject_ref=subject_ref,
        object_version=object_version,
        purpose="negative boundary probe",
        evidence_refs=("EVD-H6-NEGATIVE",),
    )


def _code(rejection: Rejection | None) -> str:
    return str(rejection.code) if rejection is not None else "ACCEPTED"


def _blocked_results() -> tuple[AssertionResult, ...]:
    return tuple(
        AssertionResult(
            test_id=f"H6-{number:02d}",
            layer="H6",
            source_obligation=f"G-A{number:02d}",
            status=AssertionStatus.BLOCKED,
            expected_outcome="H4 and H5 must pass before boundary conformance",
            actual_outcome="blocked by a lower validation layer",
        )
        for number in range(1, 18)
    )


def run_h6(
    root: Path | None = None,
    *,
    h4_run: H4Run | None = None,
    h5_run: H5Run | None = None,
) -> H6Run:
    """Execute H6-01..17 over observational traces and ownership guards."""

    h4 = h4_run or run_h4(root)
    h5 = h5_run or run_h5(root, h4_run=h4)
    if not h4.passed or not h5.passed or h5.c001 is None or h5.ct1 is None:
        return H6Run(_blocked_results(), (), (), ())

    c001 = record_c001_trace(h5.c001)
    ct1 = record_ct1_trace(h5.ct1)
    registry = BoundaryContractRegistry()

    directive = ApplyRemediationDirective(
        command_id="CMD-H6-G14",
        request_ref="REQ-H6-G14",
        directive_valid=False,
    )
    disposition_outcome = dispatch(HarnessState(), directive)
    disposition = disposition_outcome.state.dispositions[0]
    g14 = BoundaryObservation(
        sequence=1,
        publisher="Atlas",
        consumer="Aegis",
        contract_id="G-14",
        contract_version=G_CONTRACT_VERSION,
        command_id=disposition.command_id,
        purpose="publish pre-construction rejection",
        outcome="REJECTED",
        upstream_refs=(disposition.request_ref,),
        evidence_refs=("EVD-H6-G14",),
    )
    g14_valid = registry.validate(g14) is None
    control_trace = (g14,)

    results: list[AssertionResult] = []

    unique_writers = len(AUTHORITATIVE_WRITERS) == len(
        set(AUTHORITATIVE_WRITERS)
    ) and all(AUTHORITATIVE_WRITERS.values())
    results.append(
        _result(
            1,
            bool(unique_writers),
            f"{len(AUTHORITATIVE_WRITERS)} object families have one writer",
        )
    )

    observed_modules = {
        value
        for observation in (*c001, *ct1)
        for value in (observation.publisher, observation.consumer)
        if value in PRODUCT_MODULES
    }
    substrate_ok = observed_modules == PRODUCT_MODULES and (
        SUBSTRATE_BOUNDARY not in PRODUCT_MODULES
    )
    results.append(
        _result(
            2,
            substrate_ok,
            f"modules={','.join(sorted(observed_modules))}; substrate is non-module",
        )
    )

    g02 = next(item for item in c001 if item.contract_id == "G-02")
    initial_business = next(
        item
        for item in h5.c001.initial_state.object_versions
        if hasattr(item, "business_event_id")
    )
    final_business = next(
        item
        for item in h5.c001.state.object_versions
        if hasattr(item, "business_event_id")
    )
    hermes_ok = bool(
        g02.publisher == "Hermes"
        and initial_business.business_event_id in g02.upstream_refs
        and initial_business == final_business
        and "accounting treatment" not in g02.purpose
    )
    results.append(_result(3, hermes_ok, "Hermes admission preserved source meaning"))

    atlas_publications = tuple(
        item for item in (*c001, *ct1) if item.contract_id in {"G-04", "G-05"}
    )
    atlas_ok = bool(
        len(ATLAS_OWNED_ARTIFACT_F_TYPES) == 8
        and all(item.publisher == "Atlas" for item in atlas_publications)
    )
    results.append(
        _result(4, atlas_ok, "eight Artifact F accounting types resolve to Atlas")
    )

    aegis_directive = any(
        item.contract_id == "G-09" and item.publisher == "Aegis" for item in c001
    )
    atlas_case = any(
        item.contract_id == "G-04"
        and item.publisher == "Atlas"
        and item.subject_ref == "RC-001"
        for item in c001
    )
    results.append(
        _result(5, aegis_directive and atlas_case, "Aegis directs; Atlas owns RC-001")
    )

    g07_refs = {item.object_version for item in (*c001, *ct1) if item.contract_id == "G-07"}
    g08_refs = {item.object_version for item in (*c001, *ct1) if item.contract_id == "G-08"}
    distinction_ok = bool(g07_refs and g08_refs and g07_refs.isdisjoint(g08_refs))
    results.append(
        _result(6, distinction_ok, "Argus exception and Aegis issue identities are distinct")
    )

    controlled = registry.validate_controlled_use(
        reporting_version_ref="RV-2026-06@v2",
        readiness_product_ref="RV-2026-06@v2",
        readiness_ref="READY-C001-V2@v1",
    )
    g11 = next(item for item in c001 if item.contract_id == "G-11")
    g06_position = max(
        item.sequence
        for item in c001
        if item.contract_id == "G-06" and item.object_version == "RV-2026-06@v2"
    )
    g10_position = next(
        item.sequence
        for item in c001
        if item.contract_id == "G-10" and item.object_version == "READY-C001-V2@v1"
    )
    controlled_ok = bool(
        controlled is None
        and g06_position < g11.sequence
        and g10_position < g11.sequence
        and g11.upstream_refs
        == ("RV-2026-06@v2", "READY-C001-V2@v1")
    )
    results.append(
        _result(7, controlled_ok, "G-06 and exact G-10 precede controlled G-11")
    )

    unversioned = registry.validate(
        _observation(
            publisher="Atlas",
            consumer="Argus",
            contract_id="G-04",
            subject_ref="P-551",
        )
    )
    results.append(
        _result(8, _code(unversioned) == "UNVERSIONED_REFERENCE", _code(unversioned))
    )

    c001_contracts = {item.contract_id for item in c001}
    expected_c001 = {f"G-{number:02d}" for number in range(1, 13)}
    g11_consumers = {
        item.consumer for item in c001 if item.contract_id == "G-11"
    }
    g12_consumers = {
        item.consumer for item in c001 if item.contract_id == "G-12"
    }
    decision_return = any(
        item.contract_id == "G-01"
        and item.publisher == "ApprovedDecision"
        and item.consumer == SUBSTRATE_BOUNDARY
        for item in c001
    )
    results.append(
        _result(
            9,
            c001_contracts == expected_c001
            and "Argus" in g11_consumers
            and {"Aegis", "ApprovedDecision"}.issubset(g12_consumers)
            and decision_return,
            f"C-001 contracts={','.join(sorted(c001_contracts))}",
        )
    )

    correction_refs = {"J-011", "J-012"}
    correction_observations = tuple(
        item for item in ct1 if item.subject_ref in correction_refs
    )
    ct1_writer_ok = bool(
        {item.subject_ref for item in correction_observations} == correction_refs
        and all(item.publisher == "Atlas" for item in correction_observations)
    )
    results.append(_result(10, ct1_writer_ok, "Atlas alone publishes J-011/J-012"))

    invalid_inputs = tuple(
        registry.validate(
            _observation(
                publisher="SharedSubstrate",
                consumer="Atlas",
                contract_id="G-01",
                subject_ref=subject,
            )
        )
        for subject in ("AE-C001-001", "GOV-ISSUE-001", "FORECAST-001")
    )
    firewall_ok = all(_code(item) == "INVALID_G01_INPUT" for item in invalid_inputs)
    results.append(_result(11, firewall_ok, "accounting/governance/forecast G-01 blocked"))

    evidence_ok = all(
        item.evidence_refs
        and all(ref and "latest" not in ref.lower() for ref in item.upstream_refs)
        for item in (*c001, *ct1, *control_trace)
    )
    results.append(_result(12, evidence_ok, "all handoffs retain evidence and exact refs"))

    h4_status = {item.test_id: item.status for item in h4.results}
    deferred_visible = any(item.event_id == "AE-C001-002" for item in c001)
    stale = registry.validate_controlled_use(
        reporting_version_ref="RV-2026-06@v2",
        readiness_product_ref="RV-2026-06@v1",
        readiness_ref="READY-C001-V1@v1",
    )
    outcomes_ok = bool(
        deferred_visible
        and h4_status.get("H4-01") is AssertionStatus.PASS
        and h4_status.get("H4-05") is AssertionStatus.PASS
        and h4_status.get("H4-07") is AssertionStatus.PASS
        and _code(stale) == "READINESS_VERSION_MISMATCH"
    )
    results.append(_result(13, outcomes_ok, "retry/reject/defer/stale outcomes observed"))

    proof_fields = {field.name for field in fields(BoundaryObservation)}
    required_proof_fields = {
        "sequence",
        "publisher",
        "consumer",
        "contract_id",
        "contract_version",
        "subject_ref",
        "purpose",
        "outcome",
        "upstream_refs",
        "evidence_refs",
    }
    no_payload_schema = bool(
        required_proof_fields.issubset(proof_fields)
        and len(OBJECT_ADAPTERS) == 8
        and not any(name.endswith("Payload") for name in globals())
    )
    results.append(_result(14, no_payload_schema, "trace contains proof metadata only"))

    j010_observations = tuple(item for item in ct1 if item.subject_ref == "J-010")
    j010_ok = bool(
        len(j010_observations) == 1
        and j010_observations[0].contract_id == "G-13"
        and all(
            getattr(item, "journal_id", None) != "J-010"
            for item in h5.ct1.state.journal_store
        )
    )
    results.append(_result(15, j010_ok, "J-010 appears once through G-13 only"))

    actor_roles = {
        str(event.actor.role)
        for event in (*h5.c001.state.event_log, *h5.ct1.state.event_log)
    }
    expected_roles = {
        "RULE_ENGINE",
        "CORRECTION_ENGINE",
        "CONTROLLER",
        "CFO",
        "POSTING_SERVICE",
        "REPORTING_SERVICE",
    }
    role_ok = actor_roles == expected_roles and all(
        item.publisher == "Atlas"
        for item in (*c001, *ct1)
        if item.contract_id == "G-05"
    )
    results.append(_result(16, role_ok, "all six Artifact F roles act inside Atlas"))

    disposition_ok = bool(
        g14_valid
        and len(disposition_outcome.state.dispositions) == 1
        and not disposition_outcome.state.event_log
        and g14.event_id is None
        and g14.object_version is None
        and g14.subject_ref is None
        and g14.command_id == disposition.command_id
    )
    results.append(_result(17, disposition_ok, "G-14 rejection has no F subject/event"))

    return H6Run(tuple(results), c001, ct1, control_trace)
