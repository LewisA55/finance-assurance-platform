"""Closed P-A01..P-A45 acceptance catalogue and deterministic report."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AcceptanceCriterion:
    criterion_id: str
    statement: str
    evidence_tests: tuple[str, ...]


_STATEMENTS = (
    "One canonical package format carries governed registries.",
    "The package never becomes authoritative platform input.",
    "The assembler consumes only P-Q00 and in-process Artifact O.",
    "Every row belongs to one coherent export snapshot.",
    "Every public input is EXACT_ORIGINAL.",
    "No unspecified latest lookup or substitution occurs.",
    "Tabularization is lossless and non-inferential.",
    "Finance values remain integer minor units plus currency.",
    "June reporting versions one and two remain simultaneous.",
    "Restatement bridges are copied rather than recalculated.",
    "Readiness remains purpose, product, period, and scope specific.",
    "Pythia use retains its exact readiness binding.",
    "Evidence claims are not strengthened.",
    "Directed trace nodes, hashes, and edges remain unchanged.",
    "Export stewardship and semantic ownership remain visible.",
    "Synthetic status remains machine-readable and visible.",
    "The canonical directory is the governed representation.",
    "Schemas close types, keys, provenance, and ownership.",
    "Canonical JSON and CSV are implementation-order independent.",
    "Null, empty, absent, and inapplicable remain distinct.",
    "Offline verification detects malformed or tampered content.",
    "Build, verification, and reproduction do not mutate authority.",
    "Filesystem publication is atomic and never overwrites.",
    "The boundary requires no paid service or runtime network.",
    "Registry growth follows the separately ratified extension rule.",
    "P-EVIDENCE contains exactly P-D01 through P-D21.",
    "Every column has machine-readable source classification.",
    "O-Q04 version refs resolve one-to-one through O-Q05.",
    "Relationships are explicit, directed, and wildcard free.",
    "C-001 preserves the source-to-decision and reporting trace proof.",
    "CT-1 preserves referenced-state and correction-integrity proof.",
    "CT-1 does not receive invented readiness or Pythia rows.",
    "An exact source revision reproduces the same package digest.",
    "One-byte tampering changes verification outcome.",
    "A failed build leaves no apparently valid final package.",
    "Excel and Power BI remain gated by an analytical registry.",
    "Excluded Artifact O fields have an explicit disposition.",
    "Milestones 1 through 3 remain unchanged and passing.",
    "One command verifies the full Milestone 4 boundary.",
    "P-Q00 returns the exact fifteen-invocation plan.",
    "Discovery and assembly are parameterized without subject branching.",
    "One session and fresh readers preserve local source closure.",
    "P-Q00 and O-V01 scenario and entry-point equality is exact.",
    "Query execution and source provenance remain invocation-local.",
    "The evidence registry alone cannot enable Excel or Power BI.",
)

_EVIDENCE = (
    "test_package_is_closed_verified_and_uses_one_query_session",
    "test_build_and_verify_do_not_mutate_platform_state",
    "test_package_is_closed_verified_and_uses_one_query_session",
    "test_trace_and_query_provenance_remain_directed_and_invocation_local",
    "test_package_is_closed_verified_and_uses_one_query_session",
    "test_p_q00_is_closed_finite_and_hash_bound",
    "test_export_preserves_reporting_readiness_decision_and_correction_semantics",
    "test_export_preserves_reporting_readiness_decision_and_correction_semantics",
    "test_export_preserves_reporting_readiness_decision_and_correction_semantics",
    "test_export_preserves_reporting_readiness_decision_and_correction_semantics",
    "test_export_preserves_reporting_readiness_decision_and_correction_semantics",
    "test_export_preserves_reporting_readiness_decision_and_correction_semantics",
    "test_schema_registry_closes_provenance_ownership_and_relationships",
    "test_trace_and_query_provenance_remain_directed_and_invocation_local",
    "test_schema_registry_closes_provenance_ownership_and_relationships",
    "test_package_is_closed_verified_and_uses_one_query_session",
    "test_package_is_closed_verified_and_uses_one_query_session",
    "test_schema_registry_closes_provenance_ownership_and_relationships",
    "test_package_is_closed_verified_and_uses_one_query_session",
    "test_offline_verifier_detects_tamper_missing_and_extra_files",
    "test_offline_verifier_detects_tamper_missing_and_extra_files",
    "test_build_and_verify_do_not_mutate_platform_state",
    "test_reproduction_is_byte_identical_and_never_overwrites",
    "test_package_is_closed_verified_and_uses_one_query_session",
    "test_schema_registry_closes_provenance_ownership_and_relationships",
    "test_package_is_closed_verified_and_uses_one_query_session",
    "test_schema_registry_closes_provenance_ownership_and_relationships",
    "test_export_preserves_reporting_readiness_decision_and_correction_semantics",
    "test_schema_registry_closes_provenance_ownership_and_relationships",
    "test_export_preserves_reporting_readiness_decision_and_correction_semantics",
    "test_export_preserves_reporting_readiness_decision_and_correction_semantics",
    "test_export_preserves_reporting_readiness_decision_and_correction_semantics",
    "test_reproduction_is_byte_identical_and_never_overwrites",
    "test_offline_verifier_detects_tamper_missing_and_extra_files",
    "test_failed_build_is_atomic_and_leaves_no_final_or_staging_path",
    "test_schema_registry_closes_provenance_ownership_and_relationships",
    "test_schema_registry_closes_provenance_ownership_and_relationships",
    "full_pytest_suite",
    "milestone_4_acceptance_command",
    "test_p_q00_is_closed_finite_and_hash_bound",
    "test_descriptor_subjects_are_parameterised_outside_the_exporter",
    "test_package_is_closed_verified_and_uses_one_query_session",
    "test_failed_build_is_atomic_and_leaves_no_final_or_staging_path",
    "test_trace_and_query_provenance_remain_directed_and_invocation_local",
    "test_schema_registry_closes_provenance_ownership_and_relationships",
)

ACCEPTANCE_CATALOG = tuple(
    AcceptanceCriterion(
        criterion_id=f"P-A{index:02d}",
        statement=statement,
        evidence_tests=(evidence,),
    )
    for index, (statement, evidence) in enumerate(
        zip(_STATEMENTS, _EVIDENCE, strict=True),
        start=1,
    )
)


def validate_catalog() -> None:
    expected = tuple(f"P-A{number:02d}" for number in range(1, 46))
    actual = tuple(item.criterion_id for item in ACCEPTANCE_CATALOG)
    if actual != expected:
        raise ValueError("Milestone 4 acceptance catalogue is not closed")
    if any(not item.evidence_tests for item in ACCEPTANCE_CATALOG):
        raise ValueError("every Artifact P criterion requires evidence")
