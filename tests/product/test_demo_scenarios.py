from __future__ import annotations

from pathlib import Path

from finance_assurance.product.demo_scenarios import (
    C001ScenarioDescriptor,
    build_c001_scenario,
    build_ct1_scenario,
    default_demo_scenarios,
)


def test_product_demo_builders_are_fixture_independent_and_exact() -> None:
    scenarios = default_demo_scenarios()
    c001 = build_c001_scenario(scenarios.c001)
    ct1 = build_ct1_scenario(scenarios.ct1)

    assert tuple(str(item.event_type) for item in c001.workflow.event_templates) == (
        "proposal.submitted",
        "proposal.deferred",
        "period.hard_closed",
        "restatement.proposed",
        "proposal.submitted",
        "proposal.approved",
        "journal.posted",
        "restatement.adjustment_linked",
        "restatement.adjustments_ready",
        "restatement.approved",
        "reporting_version.published",
    )
    assert tuple(str(item.event_type) for item in ct1.workflow.event_templates) == (
        "proposal.submitted",
        "proposal.approved",
        "journal.posted",
        "proposal.submitted",
        "proposal.approved",
        "journal.posted",
    )
    assert len(c001.evidence) == 13
    assert len(ct1.evidence) == 6

    product_root = Path(__file__).parents[2] / "src" / "finance_assurance" / "product"
    demo_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(product_root.glob("demo_*.py"))
    )
    assert "finance_assurance.validation" not in demo_sources
    assert "finance_assurance.acceptance" not in demo_sources


def test_c001_builder_uses_typed_parameters_not_canonical_literal_branches() -> None:
    baseline = default_demo_scenarios().c001
    payload = baseline.model_dump(mode="json")
    payload.update(customer_id="CUST-ALTERNATE", monthly_revenue_minor=1250000)
    descriptor = C001ScenarioDescriptor.model_validate(payload)

    built = build_c001_scenario(descriptor)
    created_values = tuple(
        value
        for creation in built.workflow.creations
        for value in creation.values
    )
    journal_lines = tuple(
        value for value in created_values if hasattr(value, "journal_line_id")
    )

    assert any(
        item.dimensions.customer_id == "CUST-ALTERNATE" for item in journal_lines
    )
    assert sum(int(item.credit_minor) for item in journal_lines) >= 1250000
