from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from finance_assurance.product.demo_runtime import materialize_demo
from finance_assurance.product.demo_scenarios import (
    DemoScenarioSet,
    default_demo_scenarios,
)
from finance_assurance.product.query_models import (
    PUBLIC_QUERY_ADAPTER,
    GetAssuranceException,
    GetCorrectionIntegrity,
    GetDemoManifest,
    GetGovernanceCase,
    GetGovernedDecision,
    GetPlatformOverview,
    GetReadinessMatrix,
    GetReportingHistory,
    GetReportingVersion,
    GetSourceReconciliation,
    PublicQuery,
    TraceReportingValue,
)
from finance_assurance.product.query_service import PublicQueryService
from finance_assurance.runtime.persistence.models import RebuildContext
from finance_assurance.runtime.persistence.sqlite import SqlitePersistenceBoundary


def _queries(scenarios: DemoScenarioSet) -> tuple[PublicQuery, ...]:
    common = {
        "view_contract_version": 1,
        "semantic_as_of_time": scenarios.semantic_as_of_time,
    }
    return (
        GetDemoManifest(
            query_id="O-Q01",
            scenario_ref=scenarios.c001.scenario_ref,
            workspace_ref="TEST-DEMO",
            **common,
        ),
        GetPlatformOverview(
            query_id="O-Q02",
            scenario_ref=scenarios.c001.scenario_ref,
            **common,
        ),
        GetSourceReconciliation(
            query_id="O-Q03",
            scenario_ref=scenarios.c001.scenario_ref,
            reconciliation_ref="RECON-C001@v1",
            **common,
        ),
        GetReportingHistory(
            query_id="O-Q04",
            scenario_ref=scenarios.c001.scenario_ref,
            period_id="2026-06",
            **common,
        ),
        GetReportingVersion(
            query_id="O-Q05",
            scenario_ref=scenarios.c001.scenario_ref,
            reporting_version_ref="RV-2026-06@v2",
            **common,
        ),
        GetAssuranceException(
            query_id="O-Q06",
            scenario_ref=scenarios.c001.scenario_ref,
            exception_ref="EXC-C001@v1",
            **common,
        ),
        GetGovernanceCase(
            query_id="O-Q07",
            scenario_ref=scenarios.c001.scenario_ref,
            issue_ref="ISSUE-C001@v1",
            **common,
        ),
        GetReadinessMatrix(
            query_id="O-Q08",
            scenario_ref=scenarios.c001.scenario_ref,
            reporting_version_ref="RV-2026-06@v2",
            period_id="2026-06",
            purpose_ref="HIRING-FORECAST",
            scope_ref="NEXUS-GROUP",
            **common,
        ),
        GetGovernedDecision(
            query_id="O-Q09",
            scenario_ref=scenarios.c001.scenario_ref,
            decision_ref="DECISION-C001@v1",
            **common,
        ),
        TraceReportingValue(
            query_id="O-Q10",
            scenario_ref=scenarios.c001.scenario_ref,
            reporting_version_ref="RV-2026-06@v2",
            statement_field="subscription_revenue_minor",
            **common,
        ),
        GetCorrectionIntegrity(
            query_id="O-Q11",
            scenario_ref=scenarios.ct1.scenario_ref,
            verification_ref="VERIFY-CT1@v1",
            **common,
        ),
    )


@pytest.fixture(scope="module")
def public_demo(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[PublicQueryService, DemoScenarioSet, SqlitePersistenceBoundary]:
    scenarios = default_demo_scenarios()
    database = tmp_path_factory.mktemp("public-query-demo") / "demo.sqlite3"
    materialize_demo(database, scenarios)
    boundary = SqlitePersistenceBoundary(database)
    service = PublicQueryService(
        boundary,
        scenarios=scenarios,
        workspace_ref="TEST-DEMO",
    )
    yield service, scenarios, boundary
    boundary.close()


def test_query_inputs_are_closed_and_discriminated() -> None:
    scenarios = default_demo_scenarios()
    payload = _queries(scenarios)[4].model_dump(mode="json")

    assert PUBLIC_QUERY_ADAPTER.validate_python(payload).query_id == "O-Q05"

    payload["unknown"] = "forbidden"
    with pytest.raises(ValidationError, match="extra_forbidden"):
        PUBLIC_QUERY_ADAPTER.validate_python(payload)

    payload.pop("unknown")
    payload["view_contract_version"] = 2
    with pytest.raises(ValidationError, match="literal_error"):
        PUBLIC_QUERY_ADAPTER.validate_python(payload)

    payload["view_contract_version"] = 1
    payload["query_id"] = "O-Q12"
    with pytest.raises(ValidationError, match="union_tag_invalid"):
        PUBLIC_QUERY_ADAPTER.validate_python(payload)


def test_all_eleven_queries_return_exact_pinned_envelopes(
    public_demo: tuple[PublicQueryService, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    service, scenarios, boundary = public_demo
    results = tuple(service.execute(query) for query in _queries(scenarios))

    assert tuple(result.view_contract for result in results) == tuple(
        f"O-V{index:02d}" for index in range(1, 12)
    )
    assert {result.query_revision for result in results} == {boundary.revision}
    assert {result.compatibility_read_mode for result in results} == {
        "EXACT_ORIGINAL"
    }
    assert all(result.source_refs == tuple(sorted(set(result.source_refs))) for result in results)


def test_c001_views_prove_the_three_flagship_journeys(
    public_demo: tuple[PublicQueryService, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    service, scenarios, _ = public_demo
    results = {query.query_id: service.execute(query) for query in _queries(scenarios)}

    manifest = results["O-Q01"].data
    overview = results["O-Q02"].data
    reconciliation = results["O-Q03"].data
    history = results["O-Q04"].data
    version = results["O-Q05"].data
    exception = results["O-Q06"].data
    case = results["O-Q07"].data
    readiness = results["O-Q08"].data
    decision = results["O-Q09"].data
    trace = results["O-Q10"].data

    assert [item.entry_point_count for item in manifest.scenario_summaries] == [3, 1]
    assert {item.journey_id for item in manifest.scenario_entry_points} == {
        "O-J01",
        "O-J02",
        "O-J03",
        "O-SJ01",
    }
    revenue = next(
        item
        for item in overview.headline_values
        if item.field == "subscription_revenue_minor"
    )
    assert revenue.amount_minor == 1_000_000
    assert revenue.currency == "GBP"
    assert revenue.content_verification_status == "CONTENT_BYTES_VERIFIED"
    assert reconciliation.difference_minor == 1_000_000
    assert reconciliation.posted_item_count == 11
    assert [item.version for item in history.versions] == [1, 2]
    assert history.restatement_bridge[0].adjustment_minor == 1_000_000
    assert version.publication_origin == "RESTATEMENT_PUBLICATION"
    assert exception.exception_type == "RECOGNITION_COMPLETENESS"
    assert case.initial_issue_status == "OPEN"
    assert case.final_issue_status == "REMEDIATION_VERIFIED"
    assert case.final_issue_status != "CLOSED"
    assert readiness.rows[0].status == "APPROVED"
    assert decision.reporting_version_ref == readiness.reporting_version_ref
    assert decision.readiness_ref == readiness.rows[0].readiness_ref
    assert decision.monthly_cost_minor == 650_000
    assert decision.candidate_admission_outcome == "UNSUPPORTED"
    assert trace.statement_value_minor == 1_000_000
    assert {
        "reporting_version",
        "accounting_event",
        "journal",
        "proposal",
        "posting_rule",
        "business_event",
        "source_reference",
        "evidence",
    }.issubset({item.role for item in trace.nodes})


def test_governance_case_resolves_from_either_exact_issue_version(
    public_demo: tuple[PublicQueryService, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    service, scenarios, _ = public_demo
    common = {
        "query_id": "O-Q07",
        "scenario_ref": scenarios.c001.scenario_ref,
        "semantic_as_of_time": scenarios.semantic_as_of_time,
        "view_contract_version": 1,
    }

    from_initial = service.execute(
        GetGovernanceCase(issue_ref="ISSUE-C001@v1", **common)
    )
    from_successor = service.execute(
        GetGovernanceCase(issue_ref="ISSUE-C001@v2", **common)
    )

    assert from_initial.data == from_successor.data
    assert from_initial.source_refs == from_successor.source_refs
    assert from_successor.data.initial_issue_ref == "ISSUE-C001@v1"
    assert from_successor.data.final_issue_ref == "ISSUE-C001@v2"


def test_ct1_variants_and_integrity_remain_bounded(
    public_demo: tuple[PublicQueryService, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    service, scenarios, _ = public_demo
    common = {
        "view_contract_version": 1,
        "scenario_ref": scenarios.ct1.scenario_ref,
        "semantic_as_of_time": scenarios.semantic_as_of_time,
    }
    reconciliation = service.execute(
        GetSourceReconciliation(
            query_id="O-Q03",
            reconciliation_ref="RECON-CT1@v1",
            **common,
        )
    ).data
    exception = service.execute(
        GetAssuranceException(
            query_id="O-Q06",
            exception_ref="EXC-CT1@v1",
            **common,
        )
    ).data
    case = service.execute(
        GetGovernanceCase(
            query_id="O-Q07",
            issue_ref="ISSUE-CT1@v1",
            **common,
        )
    ).data
    integrity = service.execute(
        GetCorrectionIntegrity(
            query_id="O-Q11",
            verification_ref="VERIFY-CT1@v1",
            **common,
        )
    ).data

    assert reconciliation.reconciliation_type == "CASH_APPLICATION_IDENTITY"
    assert not reconciliation.identity_match
    assert exception.exception_type == "CASH_APPLICATION_IDENTITY"
    assert case.final_issue_status == "REMEDIATION_VERIFIED"
    assert integrity.reversal_binding_status == "BOUND_BEFORE_COMPARE"
    assert integrity.identity_before == "CUST-VEGA"
    assert integrity.identity_after == "CUST-ORION"
    assert integrity.control_account_net_movement_minor == 0
    assert all(item.balanced for item in integrity.journal_balance_results)


class _CountingBoundary:
    def __init__(self, boundary: SqlitePersistenceBoundary) -> None:
        self.boundary = boundary
        self.query_count = 0

    def open_query(self, context: object) -> object:
        self.query_count += 1
        return self.boundary.open_query(context)  # type: ignore[arg-type]


def test_each_public_response_opens_exactly_one_query_session(
    public_demo: tuple[PublicQueryService, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    _, scenarios, boundary = public_demo
    counted = _CountingBoundary(boundary)
    service = PublicQueryService(  # type: ignore[arg-type]
        counted,
        scenarios=scenarios,
        workspace_ref="TEST-DEMO",
    )

    for query in _queries(scenarios):
        before = counted.query_count
        result = service.execute(query)
        assert not hasattr(result, "error_code")
        assert counted.query_count == before + 1


def test_public_failures_do_not_cross_scenario_or_infer_readiness(
    public_demo: tuple[PublicQueryService, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    service, scenarios, _ = public_demo
    wrong_scenario = GetCorrectionIntegrity(
        query_id="O-Q11",
        view_contract_version=1,
        scenario_ref=scenarios.c001.scenario_ref,
        semantic_as_of_time=scenarios.semantic_as_of_time,
        verification_ref="VERIFY-CT1@v1",
    )
    wrong_purpose = GetReadinessMatrix(
        query_id="O-Q08",
        view_contract_version=1,
        scenario_ref=scenarios.c001.scenario_ref,
        semantic_as_of_time=scenarios.semantic_as_of_time,
        reporting_version_ref="RV-2026-06@v2",
        period_id="2026-06",
        purpose_ref="STATUTORY-SIGNOFF",
        scope_ref="NEXUS-GROUP",
    )
    wrong_time_payload = _queries(scenarios)[1].model_dump(mode="json")
    wrong_time_payload["semantic_as_of_time"] = "2026-07-14T11:59:59Z"
    wrong_time = GetPlatformOverview.model_validate(wrong_time_payload)

    assert service.execute(wrong_scenario).error_code == "NOT_FOUND"
    assert service.execute(wrong_purpose).error_code == "NOT_FOUND"
    unsupported = service.execute(wrong_time)
    assert unsupported.error_code == "UNSUPPORTED_CONTRACT"
    assert not hasattr(unsupported, "query_revision")


def test_unexpected_assembler_fault_is_a_safe_internal_failure(
    public_demo: tuple[PublicQueryService, DemoScenarioSet, SqlitePersistenceBoundary],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, scenarios, _ = public_demo

    def fail(*_args: object) -> object:
        raise RuntimeError("private implementation detail")

    monkeypatch.setattr(service, "_overview", fail)
    result = service.execute(_queries(scenarios)[1])

    assert result.error_code == "INTERNAL_FAILURE"
    assert "private implementation detail" not in result.message


def test_public_views_match_after_restart_and_projection_rebuild(
    tmp_path: Path,
) -> None:
    scenarios = default_demo_scenarios()
    database = tmp_path / "parity.sqlite3"
    materialize_demo(database, scenarios)

    before_boundary = SqlitePersistenceBoundary(database)
    before_service = PublicQueryService(
        before_boundary,
        scenarios=scenarios,
        workspace_ref="TEST-DEMO",
    )
    before = tuple(
        before_service.execute(query).model_dump(mode="json")
        for query in _queries(scenarios)
    )
    before_boundary.close()

    after_boundary = SqlitePersistenceBoundary(database)
    rebuild = after_boundary.open_rebuild(
        RebuildContext(
            semantic_as_of_time=str(scenarios.semantic_as_of_time),
            requested_projection_families=("J-P02", "J-P04", "J-P06"),
        )
    )
    generation = rebuild.begin_generation()
    rebuild.promote(rebuild.validate(rebuild.rebuild(generation)))
    after_service = PublicQueryService(
        after_boundary,
        scenarios=scenarios,
        workspace_ref="TEST-DEMO",
    )
    after = tuple(
        after_service.execute(query).model_dump(mode="json")
        for query in _queries(scenarios)
    )
    after_boundary.close()

    assert after == before
