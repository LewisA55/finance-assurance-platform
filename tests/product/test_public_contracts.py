"""Executable closure of the Artifact O version-1 public contract boundary."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from finance_assurance.product.contracts import (
    PUBLIC_FAILURE_ADAPTER,
    PUBLIC_SUCCESS_ADAPTER,
)
from finance_assurance.product.registry import (
    PUBLIC_QUERY_REGISTRY,
    resolve_public_query,
)

HASH_A = "sha256:" + "a" * 64
NOW = "2026-08-10T12:00:00Z"


def _statement_value() -> dict[str, Any]:
    return {
        "field": "subscription_revenue",
        "label": "Subscription revenue",
        "amount_minor": 1_000_000,
        "currency": "GBP",
        "reporting_version_ref": "RV-JUN-2026@v2",
        "content_verification_status": "CONTENT_BYTES_VERIFIED",
        "trace_available": True,
    }


def _view_data() -> dict[str, dict[str, Any]]:
    statement = _statement_value()
    return {
        "O-V01": {
            "workspace_ref": "DEMO-WORKSPACE-01",
            "runtime_release": "0.1.0",
            "synthetic_data_notice": "Synthetic demonstration data only.",
            "scenario_summaries": [],
            "scenario_entry_points": [],
            "authoritative_inventory_digest": HASH_A,
            "projection_generation_ref": "projection-generation-01",
            "verification_status": "VERIFIED",
        },
        "O-V02": {
            "company_label": "Nexus Group",
            "reporting_period": "2026-06",
            "headline_reporting_version_ref": "RV-JUN-2026@v2",
            "headline_values": [statement],
            "module_summaries": [],
            "machine_exception_count": 1,
            "governance_issue_states": [],
            "readiness_summary": [],
            "governed_decision_ref": "DECISION-001@v1",
            "journey_links": [],
        },
        "O-V03": {
            "reconciliation_ref": "REC-RECOG-001@v1",
            "reconciliation_type": "RECOGNITION_POPULATION",
            "scope_ref": "C-001",
            "performed_at": NOW,
            "source_refs": ["P-551@v1", "SCHEDULE-C001@v1"],
            "reconciliation_status": "FAILED",
            "downstream_exception_ref": "EXC-0001@v1",
            "period_id": "2026-06",
            "expected_item_count": 12,
            "posted_item_count": 11,
            "submitted_unposted_count": 1,
            "deferred_count": 1,
            "expected_amount_minor": 12_000_000,
            "posted_amount_minor": 11_000_000,
            "difference_minor": 1_000_000,
            "currency": "GBP",
        },
        "O-V04": {
            "period_id": "2026-06",
            "versions": [],
            "restatement_bridge": [],
        },
        "O-V05": {
            "reporting_version_ref": "RV-JUN-2026@v2",
            "period_id": "2026-06",
            "version": 2,
            "publication_origin": "RESTATEMENT_PUBLICATION",
            "published_at": NOW,
            "statement_values": [statement],
            "currency": "GBP",
            "content_ref": "REPORT-CONTENT-JUN-V2",
            "content_verification_status": "CONTENT_BYTES_VERIFIED",
            "traceable_fields": ["subscription_revenue"],
            "predecessor_version_ref": "RV-JUN-2026@v1",
            "restatement_case_ref": "RESTATEMENT-C001@v1",
            "manifest_hash": HASH_A,
            "published_by_event_id": "AE-C001-011",
        },
        "O-V06": {
            "test_run_ref": "TEST-RUN-001@v1",
            "test_definition_ref": "ARG-O2C-002@v1",
            "exception_ref": "EXC-0001@v1",
            "exception_type": "RECOGNITION_COMPLETENESS",
            "assertion": "completeness",
            "severity": "blocking",
            "evidence_refs": ["EVD-RECOG-001"],
            "related_governance_case_ref": "ISSUE-001@v1",
            "subject_refs": ["C-001", "P-551@v1"],
            "period_id": "2026-06",
            "expected_amount_minor": 1_000_000,
            "actual_amount_minor": 0,
            "difference_minor": 1_000_000,
            "currency": "GBP",
        },
        "O-V07": {
            "exception_ref": "EXC-0001@v1",
            "review_ref": "REVIEW-001@v1",
            "review_disposition": "CONFIRMED",
            "finding_ref": "FINDING-001@v1",
            "initial_issue_ref": "ISSUE-001@v1",
            "initial_issue_status": "OPEN",
            "owner_ref": "controller-01",
            "remediation_directive_ref": "DIRECTIVE-001@v1",
            "correction_refs": ["J-560@v1"],
            "verification_ref": "VERIFY-001@v1",
            "prior_issue_refs": ["ISSUE-001@v1"],
            "final_issue_ref": "ISSUE-001@v2",
            "final_issue_status": "REMEDIATION_VERIFIED",
            "readiness_refs": ["READY-MGMT@v1"],
        },
        "O-V08": {
            "reporting_version_ref": "RV-JUN-2026@v2",
            "period_id": "2026-06",
            "rows": [],
        },
        "O-V09": {
            "planning_input_ref": "PLAN-INPUT-001@v1",
            "reporting_version_ref": "RV-JUN-2026@v2",
            "readiness_ref": "READY-MGMT@v1",
            "purpose_ref": "management-reporting",
            "scope_ref": "NEXUS-UK",
            "frozen_input_refs": ["READY-MGMT@v1", "RV-JUN-2026@v2"],
            "decision_ref": "DECISION-001@v1",
            "decision_type": "HIRING_DEFERRAL",
            "position_ref": "POS-CS-014",
            "original_start_date": "2026-08-01",
            "recommended_start_date": "2026-09-01",
            "monthly_cost_minor": 650_000,
            "currency": "GBP",
            "reason_code": "ACTUALS_READINESS_DELAY",
            "approval_ref": "APPROVAL-001@v1",
            "approval_outcome": "APPROVED",
            "candidate_ref": "CANDIDATE-001@v1",
            "candidate_admission_outcome": "ACCEPTED",
        },
        "O-V10": {
            "reporting_version_ref": "RV-JUN-2026@v2",
            "statement_field": "subscription_revenue",
            "statement_value_minor": 1_000_000,
            "currency": "GBP",
            "content_verification_status": "CONTENT_BYTES_VERIFIED",
            "nodes": [],
            "edges": [],
        },
        "O-V11": {
            "source_projection_ref": "J-010",
            "source_projection_hash": HASH_A,
            "reversal_proposal_ref": "P-011@v1",
            "reversal_journal_ref": "J-011",
            "replacement_proposal_ref": "P-012@v1",
            "replacement_journal_ref": "J-012",
            "identity_before": "VEGA",
            "identity_after": "ORION",
            "reversal_binding_status": "BOUND_BEFORE_COMPARE",
            "journal_balance_results": [],
            "control_account_net_movement_minor": 0,
            "currency": "GBP",
            "verification_ref": "VERIFY-CT1@v1",
            "issue_update_ref": "ISSUE-CT1@v2",
        },
    }


def _freeze_arrays(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_freeze_arrays(item) for item in value)
    if isinstance(value, dict):
        return {key: _freeze_arrays(item) for key, item in value.items()}
    return value


def _envelope(view_contract: str) -> dict[str, Any]:
    return _freeze_arrays({
        "view_contract": view_contract,
        "view_contract_version": 1,
        "scenario_ref": "DEMO-C001",
        "semantic_as_of_time": NOW,
        "query_revision": 7,
        "compatibility_read_mode": "EXACT_ORIGINAL",
        "data": _view_data()[view_contract],
        "source_refs": ["J-AR02:C001", "J-AR13:G-06:C001"],
    })


@pytest.mark.parametrize("view_contract", [f"O-V{index:02}" for index in range(1, 12)])
def test_each_closed_public_view_contract_accepts_its_exact_shape(
    view_contract: str,
) -> None:
    validated = PUBLIC_SUCCESS_ADAPTER.validate_python(_envelope(view_contract))

    assert validated.view_contract == view_contract
    assert validated.compatibility_read_mode == "EXACT_ORIGINAL"


def test_query_registry_is_exactly_one_to_one() -> None:
    assert tuple(PUBLIC_QUERY_REGISTRY) == tuple(
        f"O-Q{index:02}" for index in range(1, 12)
    )
    assert len({item.operation for item in PUBLIC_QUERY_REGISTRY.values()}) == 11
    assert len({item.view_id for item in PUBLIC_QUERY_REGISTRY.values()}) == 11
    assert resolve_public_query("O-Q10").view_id == "O-V10"

    with pytest.raises(ValueError, match="unsupported public query"):
        resolve_public_query("O-Q12")


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("unknown", "field", "extra_forbidden"),
        ("compatibility_read_mode", "TYPED_TARGET", "literal_error"),
        (
            "source_refs",
            ("J-AR13:G-06:C001", "J-AR02:C001"),
            "source_refs must be sorted and unique",
        ),
        (
            "source_refs",
            ("J-AR02:C001", "J-AR02:C001"),
            "source_refs must be sorted and unique",
        ),
    ],
)
def test_public_success_envelope_rejects_boundary_violations(
    field: str,
    value: object,
    match: str,
) -> None:
    candidate = _envelope("O-V01")
    candidate[field] = value

    with pytest.raises(ValidationError, match=match):
        PUBLIC_SUCCESS_ADAPTER.validate_python(candidate)


@pytest.mark.parametrize("invalid_amount", [1.5, "1000000", True])
def test_money_is_strict_integer_minor_units(invalid_amount: object) -> None:
    candidate = _envelope("O-V05")
    candidate["data"]["statement_values"][0]["amount_minor"] = invalid_amount

    with pytest.raises(ValidationError):
        PUBLIC_SUCCESS_ADAPTER.validate_python(candidate)


@pytest.mark.parametrize(
    ("view_contract", "forbidden_field", "forbidden_value"),
    [
        ("O-V03", "cash_application_ref", "CASH-001"),
        ("O-V05", "import_attestation_ref", "IMPORT-001@v1"),
        ("O-V06", "receipt_party_ref", "ORION"),
    ],
)
def test_variant_fields_cannot_leak_across_discriminated_contracts(
    view_contract: str,
    forbidden_field: str,
    forbidden_value: str,
) -> None:
    candidate = _envelope(view_contract)
    candidate["data"][forbidden_field] = forbidden_value

    with pytest.raises(ValidationError, match="extra_forbidden"):
        PUBLIC_SUCCESS_ADAPTER.validate_python(candidate)


def test_failure_shapes_distinguish_startup_from_opened_query_session() -> None:
    startup = {
        "error_code": "DEMO_NOT_INITIALISED",
        "message": "The deterministic demo workspace has not been initialised.",
        "scenario_ref": "DEMO-C001",
        "subject_ref": "DEMO-WORKSPACE-01",
    }
    runtime = {
        "error_code": "NOT_FOUND",
        "message": "The requested public subject was not found.",
        "scenario_ref": "DEMO-C001",
        "subject_ref": "MISSING-REF",
        "query_revision": 7,
    }

    assert PUBLIC_FAILURE_ADAPTER.validate_python(startup).error_code == (
        "DEMO_NOT_INITIALISED"
    )
    assert PUBLIC_FAILURE_ADAPTER.validate_python(runtime).query_revision == 7

    invalid_startup = deepcopy(startup)
    invalid_startup["query_revision"] = 0
    with pytest.raises(ValidationError, match="extra_forbidden"):
        PUBLIC_FAILURE_ADAPTER.validate_python(invalid_startup)

    invalid_runtime = deepcopy(runtime)
    del invalid_runtime["query_revision"]
    with pytest.raises(ValidationError, match="missing"):
        PUBLIC_FAILURE_ADAPTER.validate_python(invalid_runtime)


def test_trace_view_rejects_unverified_reporting_content() -> None:
    candidate = _envelope("O-V10")
    candidate["data"]["content_verification_status"] = "DECLARED_HASH_ONLY"

    with pytest.raises(ValidationError, match="literal_error"):
        PUBLIC_SUCCESS_ADAPTER.validate_python(candidate)
