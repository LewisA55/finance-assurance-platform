"""Closed Milestone 2 acceptance catalogue and executable evidence map."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AcceptanceCriterion:
    criterion_id: str
    statement: str
    evidence_tests: tuple[str, ...]


ACCEPTANCE_CATALOG = (
    AcceptanceCriterion("M2-A01", "One application boundary and one authoritative persistence boundary.", ("test_command_executes_through_boundary_and_returns_clean_receipt", "test_root_boundary_exposes_no_independent_commit_or_generic_append")),
    AcceptanceCriterion("M2-A02", "Only an admitted business event can invoke posting-rule evaluation.", ("test_g02_to_g01_commits_and_observes_real_handoffs", "test_rejected_candidate_cannot_cross_the_g01_firewall")),
    AcceptanceCriterion("M2-A03", "Non-business semantic classes are rejected from the posting input.", ("test_rejected_candidate_cannot_cross_the_g01_firewall", "test_scalar_types_and_readiness_semantics_are_closed")),
    AcceptanceCriterion("M2-A04", "The pure planner is the only transition-guard implementation.", ("test_runtime_planner_matches_locked_milestone_1_characterization", "test_all_eighteen_guard_decisions_pass_without_reporting_full_h3")),
    AcceptanceCriterion("M2-A05", "Command retry and effect idempotency survive process restart.", ("test_command_retry_and_effect_identity_survive_restart",)),
    AcceptanceCriterion("M2-A06", "Injected failure commits no authoritative or projection state.", ("test_sql_failure_rolls_back_disk_and_memory_atomically", "test_candidate_assessment_rolls_back_complete_atomic_set", "test_invalid_artifact_g_closure_cannot_mutate_the_hard_close")),
    AcceptanceCriterion("M2-A07", "Current projections rebuild only from declared authority.", ("test_projection_can_be_deleted_and_rebuilt_from_declared_inputs", "test_c001_exact_history_content_and_trace_survive_restart_and_rebuild")),
    AcceptanceCriterion("M2-A08", "Clean-start, restart, and rebuilt semantic states are identical.", ("test_canonical_workflows_execute_and_rebuild_through_sqlite", "test_c001_exact_history_content_and_trace_survive_restart_and_rebuild")),
    AcceptanceCriterion("M2-A09", "Parameterised C-001 completes without literal canonical identities or reopen.", ("test_noncanonical_identity_and_dual_time_binding_is_deterministic", "test_c001_exact_history_content_and_trace_survive_restart_and_rebuild")),
    AcceptanceCriterion("M2-A10", "Parameterised CT-1 binds G-13 before reversal comparison.", ("test_noncanonical_identity_and_dual_time_binding_is_deterministic", "test_reversal_source_hash_is_bound_before_constructor")),
    AcceptanceCriterion("M2-A11", "Canonical inputs retain Artifact F bytes and terminal semantics.", ("test_runtime_planner_matches_locked_milestone_1_characterization", "test_canonical_corpus_loads_in_declared_order_without_rewriting")),
    AcceptanceCriterion("M2-A12", "C-001 and CT-1 traces arise from executed application handoffs.", ("test_g02_to_g01_commits_and_observes_real_handoffs", "test_c001_governance_planning_contract_chain_is_executed", "test_ct1_assurance_governance_trace_consumes_non_authored_g13")),
    AcceptanceCriterion("M2-A13", "Controlled use binds exact product and purpose-specific readiness versions.", ("test_controlled_planning_query_never_infers_readiness_from_predecessor",)),
    AcceptanceCriterion("M2-A14", "Evidence distinguishes byte verification from declared-hash consistency.", ("test_proof_boundaries_remain_non_authored_and_hash_verified", "test_c001_exact_history_content_and_trace_survive_restart_and_rebuild")),
    AcceptanceCriterion("M2-A15", "The product runtime has no validation-harness dependency.", ("test_runtime_kernel_has_no_validation_layer_dependency",)),
    AcceptanceCriterion("M2-A16", "The unchanged H0-H7 conformance suite passes without weakened assertions.", ("test_h7_accounts_for_all_eighty_assertions", "test_two_fresh_h7_runs_are_byte_identical")),
    AcceptanceCriterion("M2-A17", "No persistence or query path creates a second Artifact G owner.", ("test_registry_availability_and_evidence_are_enforced_before_commit", "test_root_boundary_exposes_no_independent_commit_or_generic_append")),
    AcceptanceCriterion("M2-A18", "Deferred product surfaces and business processes remain outside Milestone 2.", ("test_milestone2_scope_excludes_deferred_product_surfaces",)),
    AcceptanceCriterion("M2-A19", "One locked command emits complete deterministic Milestone 1 and 2 reports.", ("test_two_fresh_h7_runs_are_byte_identical", "test_milestone2_report_is_canonical_and_catalogue_is_closed")),
)


def validate_catalog() -> None:
    """Reject gaps, duplicates, or empty evidence before execution."""

    expected = tuple(f"M2-A{number:02d}" for number in range(1, 20))
    actual = tuple(item.criterion_id for item in ACCEPTANCE_CATALOG)
    if actual != expected:
        raise ValueError("Milestone 2 acceptance catalogue is not closed")
    if any(not item.evidence_tests for item in ACCEPTANCE_CATALOG):
        raise ValueError("every Milestone 2 criterion requires executable evidence")
