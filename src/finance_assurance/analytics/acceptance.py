"""Closed Q-A01..Q-A45 acceptance catalogue."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnalyticalAcceptanceCriterion:
    criterion_id: str
    statement: str
    evidence_tests: tuple[str, ...]


_STATEMENTS = (
    "P and Q share one canonical package format.",
    "P-only compatibility remains intact.",
    "Q-C01 is the sole closed analytical build request.",
    "All Q reads use one revision-pinned snapshot.",
    "All Q domain reads are EXACT_ORIGINAL.",
    "Q-Q00 is finite and parameterised.",
    "Discovery does not create semantic authority.",
    "Ledger semantics resolve exactly once.",
    "Account semantics are never parsed from identifiers.",
    "Exactly three authored journals are selected.",
    "Authored headers and lines reconcile exactly.",
    "Journal origins form a strict closed union.",
    "Input-hash verification status is honest.",
    "Business events preserve all three time concepts.",
    "Referenced state binds J-AR17 and G-13 exactly.",
    "Period states retain their exact authority basis.",
    "The exact posting-rule version is retained.",
    "Evidence hashes are not promoted without proof.",
    "Exactly ten Q query invocations are retained.",
    "Q query sources are invocation-local and family-qualified.",
    "Domain datasets contain no presentation metadata.",
    "Money remains integer minor units plus currency.",
    "P-owned conclusions are related rather than duplicated.",
    "All registry-qualified relationships validate.",
    "P reporting fields resolve to Q statement semantics.",
    "P correction facts resolve to exact Q journals.",
    "Origin-specific sources resolve exactly once.",
    "C-001 preserves June history and July correction posting.",
    "CT-1 preserves all three journal authority classes.",
    "CT-1 receives no invented planning or readiness facts.",
    "Broken semantic closure rejects the build.",
    "Failed builds are atomic and non-overwriting.",
    "Offline verification detects Q package damage.",
    "The exact source revision reproduces both registries.",
    "All earlier milestone gates remain green.",
    "Documentation discloses canonical depth honestly.",
    "Q-D16 binds P and Q discovery and snapshot coordinates.",
    "Q subjects equal already-executed P and O evidence.",
    "Verified hashes resolve an exact proof source.",
    "All Q scenario scopes resolve to P scenarios.",
    "Restatement origin resolves its exact P case.",
    "P-only v1 and P-plus-Q v2 relationship grammars remain closed.",
    "Dataset identity is registry-qualified throughout verification.",
    "All canonical Q dataset counts are exact.",
    "P-only and P-plus-Q packages both verify and reproduce.",
)

_CORE = "test_combined_package_is_verified_and_uses_one_snapshot"
_REVERSAL = "test_reversal_hash_is_verified_against_exact_j_ar17"
_REPRODUCE = "test_combined_package_reproduces_byte_for_byte"
_TAMPER = "test_q_file_tamper_is_detected"
_DEPENDENCY = "test_q_registry_without_p_is_rejected"
_SUBJECTS = "test_q_subjects_must_reconcile_to_executed_public_views"
_EVIDENCE = (
    _CORE,
    "test_package_is_closed_verified_and_uses_one_query_session",
    _CORE,
    _CORE,
    _CORE,
    _SUBJECTS,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _REVERSAL,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _REVERSAL,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _SUBJECTS,
    _SUBJECTS,
    _TAMPER,
    _REPRODUCE,
    "full_pytest_suite",
    "post_q_multi_registry_cohesion_audit",
    _CORE,
    _SUBJECTS,
    _REVERSAL,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _CORE,
    _DEPENDENCY,
)

ACCEPTANCE_CATALOG = tuple(
    AnalyticalAcceptanceCriterion(
        criterion_id=f"Q-A{index:02d}",
        statement=statement,
        evidence_tests=(evidence,),
    )
    for index, (statement, evidence) in enumerate(
        zip(_STATEMENTS, _EVIDENCE, strict=True),
        start=1,
    )
)


def validate_catalog() -> None:
    expected = tuple(f"Q-A{number:02d}" for number in range(1, 46))
    actual = tuple(item.criterion_id for item in ACCEPTANCE_CATALOG)
    if actual != expected:
        raise ValueError("Artifact Q acceptance catalogue is not closed")
    if any(not item.evidence_tests for item in ACCEPTANCE_CATALOG):
        raise ValueError("every Artifact Q criterion requires evidence")
