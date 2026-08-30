"""Artifact H H5 canonical replay assertions for C-001 and CT-1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from finance_assurance.validation.contracts.registry import canonical_model_bytes
from finance_assurance.validation.h2 import H2Run, run_h2
from finance_assurance.validation.h3_stateful import H3Run, run_h3
from finance_assurance.validation.h4_stateful import H4Run, run_h4
from finance_assurance.validation.proofs import resolve_reporting_content
from finance_assurance.validation.results import AssertionResult, AssertionStatus
from finance_assurance.validation.scenarios import (
    ScenarioReplay,
    replay_c001,
    replay_ct1,
)


@dataclass(frozen=True, slots=True)
class H5Run:
    results: tuple[AssertionResult, ...]
    c001: ScenarioReplay | None
    ct1: ScenarioReplay | None

    @property
    def passed(self) -> bool:
        return all(result.status is AssertionStatus.PASS for result in self.results)


def _canonical_equal(
    actual: tuple[BaseModel, ...], expected: tuple[BaseModel, ...]
) -> bool:
    return tuple(canonical_model_bytes(item) for item in actual) == tuple(
        canonical_model_bytes(item) for item in expected
    )


def _canonical_set_equal(
    actual: tuple[BaseModel, ...], expected: tuple[BaseModel, ...]
) -> bool:
    return sorted(canonical_model_bytes(item) for item in actual) == sorted(
        canonical_model_bytes(item) for item in expected
    )


def _objects_with(state: ScenarioReplay, field_name: str) -> tuple[BaseModel, ...]:
    return tuple(
        item
        for item in state.state.object_versions
        if hasattr(item, field_name)
    )


def _journal_models(
    replay: ScenarioReplay, journal_ids: set[str]
) -> tuple[BaseModel, ...]:
    return tuple(
        item
        for item in replay.state.journal_store
        if getattr(item, "journal_id", None) in journal_ids
    )


def _c001_passes(h2: H2Run, replay: ScenarioReplay) -> tuple[bool, str]:
    assert h2.index is not None
    expected_events = tuple(item.value for item in h2.index.c001_events)
    events_equal = _canonical_equal(replay.state.event_log, expected_events)

    proposals = {item.proposal_ref: item for item in replay.state.snapshot.proposals}
    periods = {item.period_id: item for item in replay.state.snapshot.periods}
    case = replay.state.snapshot.restatement("RC-001")
    lifecycle_ok = bool(
        proposals["P-551@v1"].status == "DEFERRED"
        and proposals["P-551@v2"].status == "POSTED"
        and periods["2026-06"].status == "HARD_CLOSED"
        and periods["2026-07"].status == "OPEN"
        and case is not None
        and case.status == "PUBLISHED"
        and case.linked_journal_ids == frozenset({"J-560"})
        and case.manifest_hash == "sha256:" + "3" * 64
    )

    actual_proposals = _objects_with(replay, "proposal_ref")
    expected_proposals = tuple(
        item.value
        for item in h2.index.canonical_objects
        if item.contract_key == "journal_proposal"
        and item.value.proposal_ref in {"P-551@v1", "P-551@v2"}
    )
    proposal_objects_equal = _canonical_equal(actual_proposals, expected_proposals)

    actual_periods = _objects_with(replay, "hard_close_event_id")
    expected_periods = tuple(
        item.value
        for item in h2.index.canonical_objects
        if item.contract_key == "accounting_period"
        and item.value.period_id == "2026-06"
    )
    period_object_equal = _canonical_equal(actual_periods, expected_periods)

    actual_cases = _objects_with(replay, "restatement_case_id")
    terminal_case = next(
        item.value
        for item in h2.index.canonical_objects
        if item.contract_key == "restatement_case"
    )
    expected_cases = (
        *(item.value for item in h2.index.restatement_snapshots),
        terminal_case,
    )
    cases_equal = _canonical_equal(actual_cases, expected_cases)

    actual_journal = _journal_models(replay, {"J-560"})
    expected_journal = tuple(
        item.value
        for item in h2.index.canonical_objects
        if (
            item.contract_key == "journal_entry"
            and item.value.journal_id == "J-560"
        )
        or (
            item.contract_key == "journal_line"
            and item.value.journal_id == "J-560"
        )
    )
    journal_equal = _canonical_set_equal(actual_journal, expected_journal)

    expected_rv2 = tuple(
        item.value
        for item in h2.index.canonical_objects
        if item.contract_key == "reporting_version"
    )
    reporting_equal = _canonical_equal(
        replay.state.reporting_version_store,
        expected_rv2,
    )
    v1, v2 = resolve_reporting_content(h2.index)
    reporting_bridge = bool(
        replay.initial_state.reporting_content_proofs == (v1,)
        and replay.state.reporting_content_proofs == (v1,)
        and v2.canonical_body.subscription_revenue_minor
        - v1.canonical_body.subscription_revenue_minor
        == 1_000_000
        and v1.canonical_body.deferred_revenue_minor
        - v2.canonical_body.deferred_revenue_minor
        == 1_000_000
    )
    routing_ok = bool(
        replay.evaluator_input_ids == ("BE-C001-RECOG-202606",)
        and replay.correction_constructor_refs == ("P-551@v2",)
        and all(
            not input_id.startswith("AE-") for input_id in replay.evaluator_input_ids
        )
    )
    passed = all(
        (
            events_equal,
            lifecycle_ok,
            proposal_objects_equal,
            period_object_equal,
            cases_equal,
            journal_equal,
            reporting_equal,
            reporting_bridge,
            routing_ok,
        )
    )
    actual = (
        f"events={len(replay.state.event_log)}/11 exact={events_equal}; "
        f"terminal={lifecycle_ok}; authored_objects="
        f"{proposal_objects_equal and period_object_equal and cases_equal}; "
        f"journal={journal_equal}; reporting={reporting_equal}; "
        f"bridge={reporting_bridge}; firewall={routing_ok}"
    )
    return passed, actual


def _line_identity(line: BaseModel) -> tuple[object, ...]:
    return (
        line.account_id,
        line.dimensions.legal_entity_id,
        line.dimensions.customer_id,
        line.dimensions.contract_id,
        line.currency,
    )


def _ct1_passes(h2: H2Run, replay: ScenarioReplay) -> tuple[bool, str]:
    assert h2.index is not None
    expected_events = tuple(item.value for item in h2.index.ct1_events)
    events_equal = _canonical_equal(replay.state.event_log, expected_events)
    proposals = {item.proposal_ref: item for item in replay.state.snapshot.proposals}
    lifecycle_ok = bool(
        proposals["P-REV-010@v1"].status == "POSTED"
        and proposals["P-REP-010@v1"].status == "POSTED"
        and replay.state.snapshot.period("2026-07").status == "OPEN"  # type: ignore[union-attr]
    )
    actual_proposals = _objects_with(replay, "proposal_ref")
    expected_proposals = tuple(
        item.value
        for item in h2.index.canonical_objects
        if item.contract_key == "journal_proposal"
        and item.value.proposal_ref in {"P-REV-010@v1", "P-REP-010@v1"}
    )
    proposal_objects_equal = _canonical_equal(actual_proposals, expected_proposals)
    actual_journals = _journal_models(replay, {"J-011", "J-012"})
    expected_journals = tuple(
        item.value
        for item in h2.index.canonical_objects
        if item.contract_key in {"journal_entry", "journal_line"}
        and item.value.journal_id in {"J-011", "J-012"}
    )
    journals_equal = _canonical_set_equal(actual_journals, expected_journals)
    referenced_ok = bool(
        replay.state.referenced_state == replay.initial_state.referenced_state
        and replay.state.snapshot.referenced_journals
        == replay.initial_state.snapshot.referenced_journals
        and all(
            getattr(item, "journal_id", None) != "J-010"
            for item in replay.state.journal_store
        )
    )

    projection = replay.state.referenced_state[0]
    j011_lines = tuple(
        item
        for item in replay.state.journal_store
        if getattr(item, "journal_id", None) == "J-011"
        and hasattr(item, "journal_line_id")
    )
    reversal_by_identity = {_line_identity(line): line for line in j011_lines}
    reversal_ok = all(
        (reverse := reversal_by_identity.get(_line_identity(source))) is not None
        and source.debit_minor == reverse.credit_minor
        and source.credit_minor == reverse.debit_minor
        for source in projection.line_tuples
    )
    j012_lines = tuple(
        item
        for item in replay.state.journal_store
        if getattr(item, "journal_id", None) == "J-012"
        and hasattr(item, "journal_line_id")
    )
    orion_ok = any(
        line.account_id == "ACC-AR"
        and line.credit_minor == 12_000_000
        and line.dimensions.customer_id == "CUST-ORION"
        for line in j012_lines
    ) and all(line.dimensions.customer_id != "CUST-VEGA" for line in j012_lines)
    account_net: dict[str, int] = {}
    for line in (*j011_lines, *j012_lines):
        account_net[line.account_id] = account_net.get(line.account_id, 0) + (
            line.debit_minor - line.credit_minor
        )
    net_zero = account_net == {"ACC-AR": 0, "ACC-UNAPPLIED-CASH": 0}
    routing_ok = bool(
        not replay.evaluator_input_ids
        and replay.correction_constructor_refs
        == ("P-REV-010@v1", "P-REP-010@v1")
    )
    passed = all(
        (
            events_equal,
            lifecycle_ok,
            proposal_objects_equal,
            journals_equal,
            referenced_ok,
            reversal_ok,
            orion_ok,
            net_zero,
            routing_ok,
        )
    )
    actual = (
        f"events={len(replay.state.event_log)}/6 exact={events_equal}; "
        f"terminal={lifecycle_ok}; proposals={proposal_objects_equal}; "
        f"journals={journals_equal}; G13={referenced_ok}; "
        f"reversal={reversal_ok}; Orion={orion_ok}; net_zero={net_zero}; "
        f"firewall={routing_ok}"
    )
    return passed, actual


def run_h5(
    root: Path | None = None,
    *,
    h2_run: H2Run | None = None,
    h3_run: H3Run | None = None,
    h4_run: H4Run | None = None,
) -> H5Run:
    """Replay both canonical scenarios only after lower stateful layers pass."""

    h2 = h2_run or run_h2(root)
    h3 = h3_run or run_h3(root, h2_run=h2)
    h4 = h4_run or run_h4(root, h2_run=h2)
    if not h2.passed or h2.index is None or not h3.passed or not h4.passed:
        results = tuple(
            AssertionResult(
                test_id=test_id,
                layer="H5",
                source_obligation=source,
                status=AssertionStatus.BLOCKED,
                expected_outcome="H2, H3, and H4 must pass before scenario replay",
                actual_outcome="blocked by a lower validation layer",
            )
            for test_id, source in (("H5-01", "C-001"), ("H5-02", "CT-1"))
        )
        return H5Run(results=results, c001=None, ct1=None)

    c001 = replay_c001(h2.index)
    ct1 = replay_ct1(h2.index)
    c001_passed, c001_actual = _c001_passes(h2, c001)
    ct1_passed, ct1_actual = _ct1_passes(h2, ct1)
    results = (
        AssertionResult(
            test_id="H5-01",
            layer="H5",
            source_obligation="Artifact H section 14.1 / C-001",
            status=AssertionStatus.PASS if c001_passed else AssertionStatus.FAIL,
            expected_outcome="C-001 reproduces 13 ordered replay obligations",
            actual_outcome=c001_actual,
            after_digest=c001.state.full_digest,
        ),
        AssertionResult(
            test_id="H5-02",
            layer="H5",
            source_obligation="Artifact H section 14.2 / CT-1",
            status=AssertionStatus.PASS if ct1_passed else AssertionStatus.FAIL,
            expected_outcome="CT-1 reproduces 9 ordered replay obligations",
            actual_outcome=ct1_actual,
            after_digest=ct1.state.full_digest,
        ),
    )
    return H5Run(results=results, c001=c001, ct1=ct1)
