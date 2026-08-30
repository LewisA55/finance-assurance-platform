"""Closed Artifact O acceptance catalogue and executable evidence map."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AcceptanceCriterion:
    criterion_id: str
    statement: str
    evidence_tests: tuple[str, ...]
    required_gates: tuple[str, ...] = ()


ACCEPTANCE_CATALOG = (
    AcceptanceCriterion("O-A01", "One shell presents five lenses over one substrate.", ("test_demo_lifecycle_is_deterministic_read_only_and_complete",), ("web_test",)),
    AcceptanceCriterion("O-A02", "No public view or client state becomes authoritative input.", ("test_public_transport_is_read_only",)),
    AcceptanceCriterion("O-A03", "The baseline browser surface is read-only.", ("test_public_transport_is_read_only",), ("web_test",)),
    AcceptanceCriterion("O-A04", "O-C01 through O-C03 are the only bounded demo operations.", ("test_demo_lifecycle_is_deterministic_read_only_and_complete",)),
    AcceptanceCriterion("O-A05", "Demo state uses ordinary runtime and persistence ports.", ("test_product_demo_builders_are_fixture_independent_and_exact",)),
    AcceptanceCriterion("O-A06", "Journeys need no paid or external runtime dependencies.", ("test_http_adapter_imports_no_persistence_fixture_or_command_layer",), ("web_test", "public_verify")),
    AcceptanceCriterion("O-A07", "Displayed business data is explicitly synthetic.", ("test_all_eleven_queries_return_exact_pinned_envelopes",), ("web_test",)),
    AcceptanceCriterion("O-A08", "Query and transport cannot access stores or fixtures.", ("test_http_adapter_imports_no_persistence_fixture_or_command_layer",)),
    AcceptanceCriterion("O-A09", "Each response uses one as-of time and pinned revision.", ("test_each_public_response_opens_exactly_one_query_session",)),
    AcceptanceCriterion("O-A10", "The baseline is exactly O-Q01..O-Q11 and O-V01..O-V11.", ("test_query_registry_is_exactly_one_to_one", "test_http_registry_is_exactly_one_to_one_with_artifact_o")),
    AcceptanceCriterion("O-A11", "June v1 and v2 remain distinct and retrievable.", ("test_c001_views_prove_the_three_flagship_journeys",)),
    AcceptanceCriterion("O-A12", "Readiness is bound to product, purpose, period, and scope.", ("test_readiness_route_requires_exact_period_purpose_and_scope",)),
    AcceptanceCriterion("O-A13", "Planning requires exact approved readiness.", ("test_c001_views_prove_the_three_flagship_journeys",)),
    AcceptanceCriterion("O-A14", "Statement trace requires verified content and J-P11.", ("test_trace_view_rejects_unverified_reporting_content",)),
    AcceptanceCriterion("O-A15", "Declared evidence is never labelled content-verified.", ("test_proof_boundaries_remain_non_authored_and_hash_verified",)),
    AcceptanceCriterion("O-A16", "The client formats but performs no domain calculation.", ("test_all_eleven_queries_return_exact_pinned_envelopes",), ("web_test",)),
    AcceptanceCriterion("O-A17", "Ownership and upstream products remain visible.", ("test_all_eleven_queries_return_exact_pinned_envelopes",)),
    AcceptanceCriterion("O-A18", "Narrative is deterministic, versioned, and non-generative.", ("test_public_views_match_after_restart_and_projection_rebuild",), ("web_test",)),
    AcceptanceCriterion("O-A19", "No surface infers an unspecified latest version.", ("test_query_inputs_are_closed_and_discriminated",)),
    AcceptanceCriterion("O-A20", "Closed failures have distinct non-success forms.", ("test_failure_shapes_distinguish_startup_from_opened_query_session",)),
    AcceptanceCriterion("O-A21", "Money preserves integer minor units and currency.", ("test_money_is_strict_integer_minor_units",)),
    AcceptanceCriterion("O-A22", "O-J01 proves the verified GBP 10,000 June v2 trace.", ("test_c001_views_prove_the_three_flagship_journeys",), ("web_test",)),
    AcceptanceCriterion("O-A23", "O-J02 proves failure, governance, immutable v1, and v2.", ("test_c001_views_prove_the_three_flagship_journeys",), ("web_test",)),
    AcceptanceCriterion("O-A24", "O-J03 proves readiness and the governed hiring decision.", ("test_c001_views_prove_the_three_flagship_journeys",), ("web_test",)),
    AcceptanceCriterion("O-A25", "O-SJ01 proves non-authoring and correction integrity.", ("test_ct1_variants_and_integrity_remain_bounded",), ("web_test",)),
    AcceptanceCriterion("O-A26", "Initialisation, restart, and rebuild preserve semantics.", ("test_public_views_match_after_restart_and_projection_rebuild",), ("public_verify",)),
    AcceptanceCriterion("O-A27", "Navigation and failures never present false data.", ("test_public_failures_do_not_cross_scenario_or_infer_readiness",), ("web_test",)),
    AcceptanceCriterion("O-A28", "Journeys pass automated and recorded manual accessibility review.", ("test_each_closed_public_view_contract_accepts_its_exact_shape",), ("web_lint", "web_test", "manual_browser")),
    AcceptanceCriterion("O-A29", "Desktop, tablet, and mobile preserve governed context.", ("test_all_eleven_queries_return_exact_pinned_envelopes",), ("web_test", "manual_browser")),
    AcceptanceCriterion("O-A30", "The baseline needs no secret or external-network call.", ("test_http_adapter_imports_no_persistence_fixture_or_command_layer",), ("web_test", "public_verify")),
    AcceptanceCriterion("O-A31", "Milestone 1 and 2 acceptance remains unchanged and passing.", ("test_milestone2_report_is_canonical_and_catalogue_is_closed",), ("milestone2",)),
    AcceptanceCriterion("O-A32", "One clean-checkout command produces deterministic M3 evidence.", ("test_milestone3_report_is_canonical_and_catalogue_is_closed",), ("clean_checkout", "milestone2", "python_quality", "web_typecheck", "web_lint", "web_test", "public_verify", "report_reproducibility")),
    AcceptanceCriterion("O-A33", "O v1 is EXACT_ORIGINAL; adapted reads require revision.", ("test_all_eleven_queries_return_exact_pinned_envelopes",)),
)


def validate_catalog() -> None:
    """Reject gaps, duplicates, or criteria without executable evidence."""

    expected = tuple(f"O-A{number:02d}" for number in range(1, 34))
    actual = tuple(item.criterion_id for item in ACCEPTANCE_CATALOG)
    if actual != expected:
        raise ValueError("Milestone 3 acceptance catalogue is not closed")
    if any(not item.evidence_tests and not item.required_gates for item in ACCEPTANCE_CATALOG):
        raise ValueError("every Milestone 3 criterion requires evidence")
