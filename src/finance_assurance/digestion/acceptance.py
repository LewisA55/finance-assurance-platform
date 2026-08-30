"""Closed R-A01..R-A48 Artifact R acceptance catalogue."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DigestionAcceptanceCriterion:
    criterion_id: str
    statement: str
    evidence_tests: tuple[str, ...]


_STATEMENTS = (
    "R remains a non-authoritative projection over one verified P+Q package.",
    "The exact source digest and snapshot coordinates bind every model.",
    "P-C02 VERIFIED is mandatory before source CSV parsing.",
    "The source registry set is exactly P v1 plus Q v1.",
    "All source datasets retain registry-qualified identity.",
    "R authors no replacement fact, dimension, aggregate, or source query.",
    "All datasets have one exact primary consumption class.",
    "CORE, LINEAGE, and DIAGNOSTIC profiles are cumulative and exact.",
    "Every selected source schema is copied byte-for-byte.",
    "Selected CSV emission is byte-identical to canonical source bytes.",
    "All declared source physical types and null semantics remain exact.",
    "Enum sets remain exact and text discriminators remain text.",
    "Every source column retains origin, transformation, role, and visibility.",
    "Every R-added field is hidden reserved R_TECHNICAL metadata.",
    "Money remains signed int64 minor units with exact currency columns.",
    "Parquet preserves source order, row order, nulls, and technical-key order.",
    "One dependency-locked Parquet writer profile binds canonical bytes.",
    "DuckDB remains optional, downstream of Parquet, and read-only.",
    "DuckDB is excluded from canonical byte reproduction.",
    "All composite consumer relationships receive exact technical keys.",
    "Incomplete keys, endpoint mismatch, and hash collision fail closed.",
    "Every in-profile relationship has one closed disposition.",
    "Only the finite declared relationship set may be active.",
    "The active filter graph is acyclic and has unique directed paths.",
    "Only the declared role-playing relationship is inactive.",
    "Integrity and polymorphic relationships remain validation-only.",
    "Readiness, limitations, and evidence references remain related.",
    "As-was, as-restated, and bridge datasets remain simultaneous.",
    "Authored and referenced journal populations remain separate.",
    "Trace direction and evidence verification status remain exact.",
    "All raw integer fields default to no summarization.",
    "The measure registry closes grain, currency, version, and population.",
    "Exact-value measures require one exact source row.",
    "Additive journal measures retain grouping and population separation.",
    "Portable aliases are deterministic, source-bound, and unique.",
    "Profiles remain complete and consumers cannot invent subsets.",
    "The first flagship Excel boundary remains LINEAGE rather than CORE.",
    "The baseline requires no paid, hosted, credentialed, or network service.",
    "Synthetic status and bounded C-001/CT-1 depth remain prominent.",
    "Publication is staged, verified, atomic, and non-overwriting.",
    "R-C02 exposes only full source-equivalence verification.",
    "R-C02 re-verifies every source, file, table, field, and relationship.",
    "R-C03 requires the exact source package and writer profile.",
    "DuckDB reproduction is logical rather than byte-level.",
    "Consumer adapters cannot mutate the model or source package.",
    "Consumer calculations cannot be presented as governed values.",
    "C-001 and CT-1 remain consumable offline through LINEAGE.",
    "Existing P/Q verification, reproduction, and acceptance remain green.",
)

_BUILD = "test_r2_builds_and_verifies_every_closed_profile"
_REPRODUCE = "test_r2_reproduces_every_canonical_file_byte_for_byte"
_PARQUET = "test_r2_parquet_retains_source_order_types_and_hidden_keys"
_TAMPER = "test_r2_full_equivalence_rejects_resealed_parquet_domain_tampering"
_ATOMIC = "test_r2_writer_failure_is_atomic"
_CATALOGUE = "test_r2_catalogue_is_canonical_and_separates_metadata_from_domain_rows"
_REGISTRY = "test_registry_closes_exact_source_inventory"
_RELATIONSHIPS = "test_each_profile_has_one_finite_safe_relationship_plan"
_MEASURES = "test_measure_registry_closes_double_counting_guards"

_EVIDENCE = (
    "test_r2_cannot_stage_or_publish_inside_the_governed_source",
    _BUILD,
    "test_r2_requires_verified_exact_source_before_parse_or_publication",
    _BUILD,
    _BUILD,
    "test_r2_cannot_stage_or_publish_inside_the_governed_source",
    _REGISTRY,
    _BUILD,
    _BUILD,
    _BUILD,
    _PARQUET,
    _CATALOGUE,
    _CATALOGUE,
    _PARQUET,
    _PARQUET,
    _PARQUET,
    _REPRODUCE,
    "test_r3_builds_verified_read_only_duckdb_cache",
    "test_r3_reproduces_canonical_bytes_and_revalidates_cache",
    _PARQUET,
    "test_relationship_key_rejects_incomplete_or_mistyped_tuples",
    _RELATIONSHIPS,
    _RELATIONSHIPS,
    _RELATIONSHIPS,
    _RELATIONSHIPS,
    _RELATIONSHIPS,
    _BUILD,
    _BUILD,
    _BUILD,
    _BUILD,
    _REGISTRY,
    _MEASURES,
    _MEASURES,
    _MEASURES,
    "test_portable_aliases_are_unique_and_bounded",
    _BUILD,
    _BUILD,
    _BUILD,
    _BUILD,
    "test_r2_staged_verification_failure_is_atomic",
    _TAMPER,
    _TAMPER,
    _REPRODUCE,
    "test_r2_rejects_duckdb_until_phase_r3",
    _CATALOGUE,
    _CATALOGUE,
    _BUILD,
    "milestone_4_acceptance_command",
)

ACCEPTANCE_CATALOG = tuple(
    DigestionAcceptanceCriterion(
        criterion_id=f"R-A{index:02d}",
        statement=statement,
        evidence_tests=(evidence,),
    )
    for index, (statement, evidence) in enumerate(
        zip(_STATEMENTS, _EVIDENCE, strict=True), start=1
    )
)


def validate_catalog() -> None:
    expected = tuple(f"R-A{number:02d}" for number in range(1, 49))
    actual = tuple(item.criterion_id for item in ACCEPTANCE_CATALOG)
    if actual != expected:
        raise ValueError("Artifact R acceptance catalogue is not closed")
    if any(not item.evidence_tests for item in ACCEPTANCE_CATALOG):
        raise ValueError("every Artifact R criterion requires evidence")
