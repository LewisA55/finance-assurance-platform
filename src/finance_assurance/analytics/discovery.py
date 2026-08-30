"""Finite parameterised Q-Q00 analytical discovery."""

from __future__ import annotations

from finance_assurance.analytics.catalog import CATALOG_REF
from finance_assurance.analytics.contracts import (
    AnalyticalDiscoveryDescriptor,
    AnalyticalDiscoveryView,
    AnalyticalQuery,
    AnalyticalSubjectSet,
)
from finance_assurance.exports.contracts import ExportDiscoveryDescriptor
from finance_assurance.product.demo_scenarios import DemoScenarioSet


def default_analytical_subjects(scenarios: DemoScenarioSet) -> AnalyticalSubjectSet:
    c001 = scenarios.c001
    ct1 = scenarios.ct1
    return AnalyticalSubjectSet(
        c001_scenario_ref=c001.scenario_ref,
        c001_journal_id=c001.correction_journal_id,
        c001_business_event_ref=c001.business_event_id,
        c001_posting_rule_ref="PR-O2C-RECOG@v1",
        c001_reporting_period_id=c001.reporting_period_id,
        c001_reporting_period_token="AE-C001-003",
        ct1_scenario_ref=ct1.scenario_ref,
        ct1_source_journal_id=ct1.source_journal_id,
        ct1_reversal_journal_id=ct1.reversal_journal_id,
        ct1_replacement_journal_id=ct1.replacement_journal_id,
        correction_period_id=c001.correction_period_id,
        ledger_semantics_catalog_ref=CATALOG_REF,
    )


def build_analytical_discovery(
    scenarios: DemoScenarioSet,
    p_descriptor: ExportDiscoveryDescriptor,
    *,
    subjects: AnalyticalSubjectSet | None = None,
    descriptor_ref: str = "ANALYTICAL-DISCOVERY-DEMO@v1",
) -> AnalyticalDiscoveryDescriptor:
    return AnalyticalDiscoveryDescriptor(
        discovery_contract_version=1,
        discovery_descriptor_ref=descriptor_ref,
        p_discovery_descriptor_ref=p_descriptor.discovery_descriptor_ref,
        workspace_ref=p_descriptor.workspace_ref,
        semantic_as_of=scenarios.semantic_as_of_time,
        subjects=subjects or default_analytical_subjects(scenarios),
    )


def compile_analytical_discovery(
    descriptor: AnalyticalDiscoveryDescriptor,
    *,
    query_revision: int,
    scenario_set_digest: str,
) -> AnalyticalDiscoveryView:
    s = descriptor.subjects
    common = {
        "query_contract_version": 1,
        "semantic_as_of_time": descriptor.semantic_as_of,
    }
    plan = (
        AnalyticalQuery(query_id="Q-Q01", scenario_ref=s.c001_scenario_ref, subject_ref=s.ledger_semantics_catalog_ref, **common),
        AnalyticalQuery(query_id="Q-Q02", scenario_ref=s.c001_scenario_ref, subject_ref=s.c001_journal_id, **common),
        AnalyticalQuery(query_id="Q-Q02", scenario_ref=s.ct1_scenario_ref, subject_ref=s.ct1_reversal_journal_id, **common),
        AnalyticalQuery(query_id="Q-Q02", scenario_ref=s.ct1_scenario_ref, subject_ref=s.ct1_replacement_journal_id, **common),
        AnalyticalQuery(query_id="Q-Q03", scenario_ref=s.c001_scenario_ref, subject_ref=s.c001_business_event_ref, **common),
        AnalyticalQuery(query_id="Q-Q04", scenario_ref=s.ct1_scenario_ref, subject_ref=s.ct1_source_journal_id, **common),
        AnalyticalQuery(query_id="Q-Q05", scenario_ref=s.c001_scenario_ref, subject_ref=s.c001_reporting_period_id, state_basis_type="TRANSITION_PUBLICATION", state_token=s.c001_reporting_period_token, **common),
        AnalyticalQuery(query_id="Q-Q05", scenario_ref=s.c001_scenario_ref, subject_ref=s.correction_period_id, state_basis_type="BASE_FACT", **common),
        AnalyticalQuery(query_id="Q-Q06", scenario_ref=s.c001_scenario_ref, subject_ref=s.c001_posting_rule_ref, **common),
    )
    return AnalyticalDiscoveryView(
        view_contract="Q-V00",
        view_contract_version=1,
        workspace_ref=descriptor.workspace_ref,
        discovery_descriptor_ref=descriptor.discovery_descriptor_ref,
        discovery_descriptor_hash=descriptor.descriptor_hash,
        p_discovery_descriptor_ref=descriptor.p_discovery_descriptor_ref,
        query_revision=query_revision,
        semantic_as_of=descriptor.semantic_as_of,
        compatibility_mode="EXACT_ORIGINAL",
        scenario_set_digest=scenario_set_digest,
        ledger_semantics_catalog_ref=s.ledger_semantics_catalog_ref,
        query_plan=plan,
    )
