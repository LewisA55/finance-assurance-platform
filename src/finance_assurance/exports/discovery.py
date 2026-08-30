"""Finite parameterised P-Q00 export discovery for Artifact P."""

from __future__ import annotations

from collections import Counter

from pydantic import ConfigDict

from finance_assurance.exports.contracts import (
    DiscoveryScenario,
    ExpectedEntryPoint,
    ExportContractModel,
    ExportDiscoveryDescriptor,
    ExportDiscoveryView,
    ExportScenarioDescriptor,
    OwnedQueryRequest,
)
from finance_assurance.product.demo_scenarios import DemoScenarioSet
from finance_assurance.product.query_models import (
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
    TraceReportingValue,
)
from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.contracts.primitives import AsciiString


class ExportSubjectSet(ExportContractModel):
    """Exact Artifact O subjects supplied by the product composition root."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    c001_reconciliation_ref: AsciiString
    c001_reporting_predecessor_ref: AsciiString
    c001_reporting_successor_ref: AsciiString
    c001_exception_ref: AsciiString
    c001_issue_ref: AsciiString
    c001_readiness_ref: AsciiString
    c001_readiness_purpose_ref: AsciiString
    c001_readiness_scope_ref: AsciiString
    c001_decision_ref: AsciiString
    c001_statement_field: AsciiString
    ct1_reconciliation_ref: AsciiString
    ct1_exception_ref: AsciiString
    ct1_issue_ref: AsciiString
    ct1_verification_ref: AsciiString


def build_export_discovery(
    scenarios: DemoScenarioSet,
    *,
    workspace_ref: str,
    subjects: ExportSubjectSet,
    descriptor_ref: str = "EXPORT-DISCOVERY-DEMO@v1",
) -> ExportDiscoveryDescriptor:
    """Build the closed descriptor from composition-root supplied subjects."""
    common = {
        "view_contract_version": 1,
        "semantic_as_of_time": scenarios.semantic_as_of_time,
    }
    c001_ref = scenarios.c001.scenario_ref
    ct1_ref = scenarios.ct1.scenario_ref
    c001_queries = (
        GetDemoManifest(
            query_id="O-Q01",
            scenario_ref=c001_ref,
            workspace_ref=workspace_ref,
            **common,
        ),
        GetPlatformOverview(query_id="O-Q02", scenario_ref=c001_ref, **common),
        GetSourceReconciliation(
            query_id="O-Q03",
            scenario_ref=c001_ref,
            reconciliation_ref=subjects.c001_reconciliation_ref,
            **common,
        ),
        GetReportingHistory(
            query_id="O-Q04",
            scenario_ref=c001_ref,
            period_id=scenarios.c001.reporting_period_id,
            **common,
        ),
        GetReportingVersion(
            query_id="O-Q05",
            scenario_ref=c001_ref,
            reporting_version_ref=subjects.c001_reporting_predecessor_ref,
            **common,
        ),
        GetReportingVersion(
            query_id="O-Q05",
            scenario_ref=c001_ref,
            reporting_version_ref=subjects.c001_reporting_successor_ref,
            **common,
        ),
        GetAssuranceException(
            query_id="O-Q06",
            scenario_ref=c001_ref,
            exception_ref=subjects.c001_exception_ref,
            **common,
        ),
        GetGovernanceCase(
            query_id="O-Q07",
            scenario_ref=c001_ref,
            issue_ref=subjects.c001_issue_ref,
            **common,
        ),
        GetReadinessMatrix(
            query_id="O-Q08",
            scenario_ref=c001_ref,
            reporting_version_ref=subjects.c001_reporting_successor_ref,
            period_id=scenarios.c001.reporting_period_id,
            purpose_ref=subjects.c001_readiness_purpose_ref,
            scope_ref=subjects.c001_readiness_scope_ref,
            **common,
        ),
        GetGovernedDecision(
            query_id="O-Q09",
            scenario_ref=c001_ref,
            decision_ref=subjects.c001_decision_ref,
            **common,
        ),
        TraceReportingValue(
            query_id="O-Q10",
            scenario_ref=c001_ref,
            reporting_version_ref=subjects.c001_reporting_successor_ref,
            statement_field=subjects.c001_statement_field,
            **common,
        ),
    )
    ct1_queries = (
        GetSourceReconciliation(
            query_id="O-Q03",
            scenario_ref=ct1_ref,
            reconciliation_ref=subjects.ct1_reconciliation_ref,
            **common,
        ),
        GetAssuranceException(
            query_id="O-Q06",
            scenario_ref=ct1_ref,
            exception_ref=subjects.ct1_exception_ref,
            **common,
        ),
        GetGovernanceCase(
            query_id="O-Q07",
            scenario_ref=ct1_ref,
            issue_ref=subjects.ct1_issue_ref,
            **common,
        ),
        GetCorrectionIntegrity(
            query_id="O-Q11",
            scenario_ref=ct1_ref,
            verification_ref=subjects.ct1_verification_ref,
            **common,
        ),
    )
    return ExportDiscoveryDescriptor(
        discovery_contract_version=1,
        discovery_descriptor_ref=descriptor_ref,
        workspace_ref=workspace_ref,
        semantic_as_of=scenarios.semantic_as_of_time,
        scenario_descriptors=(
            ExportScenarioDescriptor(
                scenario_ref=c001_ref,
                canonical_family="C-001",
                public_role="FLAGSHIP",
                query_requests=c001_queries,
                expected_entry_points=(
                    ExpectedEntryPoint(
                        scenario_ref=c001_ref,
                        journey_id="O-J01",
                        semantic_role="reporting_value_trace",
                        exact_ref=subjects.c001_reporting_successor_ref,
                        source_kind="AUTHORITATIVE_RECORD",
                        availability="AVAILABLE",
                    ),
                    ExpectedEntryPoint(
                        scenario_ref=c001_ref,
                        journey_id="O-J02",
                        semantic_role="recognition_reconciliation",
                        exact_ref=subjects.c001_reconciliation_ref,
                        source_kind="AUTHORITATIVE_RECORD",
                        availability="AVAILABLE",
                    ),
                    ExpectedEntryPoint(
                        scenario_ref=c001_ref,
                        journey_id="O-J03",
                        semantic_role="governed_decision",
                        exact_ref=subjects.c001_decision_ref,
                        source_kind="AUTHORITATIVE_RECORD",
                        availability="AVAILABLE",
                    ),
                ),
            ),
            ExportScenarioDescriptor(
                scenario_ref=ct1_ref,
                canonical_family="CT-1",
                public_role="SUPPORTING",
                query_requests=ct1_queries,
                expected_entry_points=(
                    ExpectedEntryPoint(
                        scenario_ref=ct1_ref,
                        journey_id="O-SJ01",
                        semantic_role="correction_verification",
                        exact_ref=subjects.ct1_verification_ref,
                        source_kind="AUTHORITATIVE_RECORD",
                        availability="AVAILABLE",
                    ),
                ),
            ),
        ),
    )


def compile_export_discovery(
    descriptor: ExportDiscoveryDescriptor,
    *,
    query_revision: int,
    scenario_set_digest: str,
) -> ExportDiscoveryView:
    """Validate and compile the closed P-Q00 plan without reading persistence."""

    requests = tuple(
        OwnedQueryRequest(scenario_ref=scenario.scenario_ref, request=request)
        for scenario in descriptor.scenario_descriptors
        for request in scenario.query_requests
    )
    counts = Counter(item.request.query_id for item in requests)
    expected = {
        "O-Q01": 1,
        "O-Q02": 1,
        "O-Q03": 2,
        "O-Q04": 1,
        "O-Q05": 2,
        "O-Q06": 2,
        "O-Q07": 2,
        "O-Q08": 1,
        "O-Q09": 1,
        "O-Q10": 1,
        "O-Q11": 1,
    }
    if len(requests) != 15 or counts != expected:
        raise ValueError("P-Q00 requires the exact fifteen-query Artifact O plan")
    if requests[0].request.query_id != "O-Q01":
        raise ValueError("O-Q01 must be the first Artifact O invocation")
    request_hashes = tuple(
        canonical_sha256(item.request.model_dump(mode="json")) for item in requests
    )
    if len(request_hashes) != len(set(request_hashes)):
        raise ValueError("P-Q00 rejects duplicate query requests")
    return ExportDiscoveryView(
        view_contract="P-V00",
        view_contract_version=1,
        workspace_ref=descriptor.workspace_ref,
        discovery_descriptor_ref=descriptor.discovery_descriptor_ref,
        discovery_descriptor_hash=descriptor.descriptor_hash,
        query_revision=query_revision,
        semantic_as_of=descriptor.semantic_as_of,
        compatibility_mode="EXACT_ORIGINAL",
        scenario_set_digest=scenario_set_digest,
        scenarios=tuple(
            DiscoveryScenario(
                scenario_ref=item.scenario_ref,
                canonical_family=item.canonical_family,
                public_role=item.public_role,
            )
            for item in descriptor.scenario_descriptors
        ),
        query_requests=requests,
        entry_points=tuple(
            entry
            for scenario in descriptor.scenario_descriptors
            for entry in scenario.expected_entry_points
        ),
    )
