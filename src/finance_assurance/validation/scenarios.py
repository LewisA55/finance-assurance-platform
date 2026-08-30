"""Scenario-local C-001 and CT-1 replay drivers for Artifact H H5."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from finance_assurance.validation.contracts.registry import validate_object
from finance_assurance.validation.dispatcher import DispatchOutcome, dispatch
from finance_assurance.validation.index import ValidatedCorpusIndex
from finance_assurance.validation.planner import (
    ApproveProposal,
    ApproveRestatement,
    ConstructCorrectionProposal,
    DeferProposal,
    EvaluatePostingRule,
    FreezeRestatementManifest,
    HardClosePeriod,
    LinkRestatementAdjustment,
    PeriodState,
    PlannerCommand,
    PostProposal,
    ProposeRestatement,
    PublishRestatement,
    StateSnapshot,
    SubmitProposal,
    TransitionPlan,
)
from finance_assurance.validation.proofs import (
    ReportingContentProof,
    resolve_referenced_journal,
    resolve_reporting_content,
)
from finance_assurance.validation.results import Rejection
from finance_assurance.validation.state import HarnessState


@dataclass(frozen=True, slots=True)
class ScenarioReplay:
    name: str
    initial_state: HarnessState
    state: HarnessState
    commands: tuple[PlannerCommand, ...]
    outcomes: tuple[DispatchOutcome, ...]
    evaluator_input_ids: tuple[str, ...]
    correction_constructor_refs: tuple[str, ...]


def _event(index: ValidatedCorpusIndex, event_id: str) -> BaseModel:
    return next(
        item.value for item in index.events if item.value.event_id == event_id
    )


def _object(
    index: ValidatedCorpusIndex,
    contract_key: str,
    field_name: str,
    expected: str,
) -> BaseModel:
    return next(
        item.value
        for item in index.canonical_objects
        if item.contract_key == contract_key
        and getattr(item.value, field_name) == expected
    )


def _evidence(event: BaseModel) -> list[dict[str, object]]:
    return [item.model_dump(mode="json") for item in event.evidence_refs]


def _dimensions(
    *, customer_id: str | None, contract_id: str | None
) -> dict[str, object]:
    return {
        "legal_entity_id": "NEXUS-UK",
        "customer_id": customer_id,
        "contract_id": contract_id,
    }


def _proposal_object(
    proposal_ref: str,
    status: str,
    submit_event: BaseModel,
) -> BaseModel:
    specs: dict[str, dict[str, object]] = {
        "P-551@v1": {
            "proposal_id": "P-551",
            "proposal_version": 1,
            "origin_type": "AUTOMATED_POSTING",
            "origin_basis": {
                "business_event_ref": "BE-C001-RECOG-202606",
                "posting_rule_ref": "PR-O2C-RECOG@v1",
                "input_hashes": ["sha256:" + "a" * 64],
            },
            "target_period_id": "2026-06",
            "effective_date": "2026-06-30",
            "created_at": "2026-07-03T08:56:00Z",
            "lines": (
                ("ACC-DEFERRED-REVENUE", 1_000_000, 0, "CUST-ORION", "CONTRACT-C001"),
                (
                    "ACC-SUBSCRIPTION-REVENUE",
                    0,
                    1_000_000,
                    "CUST-ORION",
                    "CONTRACT-C001",
                ),
            ),
        },
        "P-551@v2": {
            "proposal_id": "P-551",
            "proposal_version": 2,
            "origin_type": "RESTATEMENT_ADJUSTMENT",
            "origin_basis": {
                "restatement_case_id": "RC-001",
                "restatement_policy_ref": {
                    "object_type": "policy",
                    "object_id": "POL-RESTATEMENT-v1",
                },
                "directive_ref": {
                    "object_type": "remediation_directive",
                    "object_id": "DIR-C001-001",
                },
                "predecessor_proposal_ref": "P-551@v1",
                "input_hashes": ["sha256:" + "e" * 64],
            },
            "target_period_id": "2026-07",
            "effective_date": "2026-07-13",
            "created_at": "2026-07-13T08:55:00Z",
            "lines": (
                ("ACC-DEFERRED-REVENUE", 1_000_000, 0, "CUST-ORION", "CONTRACT-C001"),
                (
                    "ACC-SUBSCRIPTION-REVENUE",
                    0,
                    1_000_000,
                    "CUST-ORION",
                    "CONTRACT-C001",
                ),
            ),
        },
        "P-REV-010@v1": {
            "proposal_id": "P-REV-010",
            "proposal_version": 1,
            "origin_type": "REVERSAL",
            "origin_basis": {
                "reverses_journal_id": "J-010",
                "correction_policy_ref": {
                    "object_type": "policy",
                    "object_id": "POL-REVERSAL-v1",
                },
                "directive_ref": {
                    "object_type": "remediation_directive",
                    "object_id": "DIR-CT1-001",
                },
                "input_hashes": ["sha256:" + "6" * 64],
            },
            "target_period_id": "2026-07",
            "effective_date": "2026-07-11",
            "created_at": "2026-07-11T08:55:00Z",
            "lines": (
                ("ACC-AR", 12_000_000, 0, "CUST-VEGA", None),
                ("ACC-UNAPPLIED-CASH", 0, 12_000_000, None, None),
            ),
        },
        "P-REP-010@v1": {
            "proposal_id": "P-REP-010",
            "proposal_version": 1,
            "origin_type": "REPLACEMENT",
            "origin_basis": {
                "corrects_journal_id": "J-010",
                "correction_policy_ref": {
                    "object_type": "policy",
                    "object_id": "POL-CORRECTION-v1",
                },
                "directive_ref": {
                    "object_type": "remediation_directive",
                    "object_id": "DIR-CT1-001",
                },
                "input_hashes": ["sha256:" + "9" * 64],
            },
            "target_period_id": "2026-07",
            "effective_date": "2026-07-11",
            "created_at": "2026-07-11T09:35:00Z",
            "lines": (
                ("ACC-UNAPPLIED-CASH", 12_000_000, 0, None, None),
                ("ACC-AR", 0, 12_000_000, "CUST-ORION", None),
            ),
        },
    }
    spec = specs[proposal_ref]
    lines = [
        {
            "line_no": number,
            "account_id": account,
            "debit_minor": debit,
            "credit_minor": credit,
            "currency": "GBP",
            "dimensions": _dimensions(customer_id=customer, contract_id=contract),
        }
        for number, (account, debit, credit, customer, contract) in enumerate(
            spec["lines"],  # type: ignore[arg-type]
            start=1,
        )
    ]
    payload = {
        "contract_version": 1,
        "proposal_id": spec["proposal_id"],
        "proposal_version": spec["proposal_version"],
        "proposal_ref": proposal_ref,
        "status": status,
        "origin_type": spec["origin_type"],
        "origin_basis": spec["origin_basis"],
        "target_period_id": spec["target_period_id"],
        "effective_date": spec["effective_date"],
        "ledger_currency": "GBP",
        "proposed_lines": lines,
        "total_debit_minor": sum(item[1] for item in spec["lines"]),  # type: ignore[union-attr]
        "total_credit_minor": sum(item[2] for item in spec["lines"]),  # type: ignore[union-attr]
        "prepared_by": submit_event.actor.model_dump(mode="json"),
        "created_at": spec["created_at"],
        "submitted_at": str(submit_event.occurred_at),
        "evidence_refs": _evidence(submit_event),
    }
    return validate_object("journal_proposal", payload)


def _journal_package(
    proposal: BaseModel,
    post_event: BaseModel,
    *,
    correction_basis: dict[str, object],
) -> tuple[BaseModel, ...]:
    journal_id = str(post_event.payload.journal_id)
    lines = tuple(
        validate_object(
            "journal_line",
            {
                "contract_version": 1,
                "journal_line_id": f"{journal_id}-L{line.line_no}",
                "journal_id": journal_id,
                "line_no": line.line_no,
                "account_id": line.account_id,
                "debit_minor": line.debit_minor,
                "credit_minor": line.credit_minor,
                "currency": line.currency,
                "dimensions": line.dimensions.model_dump(mode="json"),
            },
        )
        for line in proposal.proposed_lines
    )
    journal = validate_object(
        "journal_entry",
        {
            "contract_version": 1,
            "journal_id": journal_id,
            "entry_class": post_event.payload.entry_class,
            "source_proposal_ref": proposal.proposal_ref,
            "posted_by_event_id": post_event.event_id,
            "ledger_period_id": post_event.basis.period_id,
            "effective_date": proposal.effective_date,
            "posted_at": post_event.occurred_at,
            "currency": post_event.basis.currency,
            "total_debit_minor": proposal.total_debit_minor,
            "total_credit_minor": proposal.total_credit_minor,
            "line_refs": [line.journal_line_id for line in lines],
            "correction_basis": correction_basis,
            "evidence_refs": _evidence(post_event),
        },
    )
    return (journal, *lines)


def _hard_closed_period(close_event: BaseModel) -> BaseModel:
    return validate_object(
        "accounting_period",
        {
            "contract_version": 1,
            "period_id": "2026-06",
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
            "status": "HARD_CLOSED",
            "ledger_currency": "GBP",
            "evidence_refs": _evidence(close_event),
            "hard_closed_at": close_event.occurred_at,
            "hard_close_event_id": close_event.event_id,
            "close_policy_ref": close_event.basis.close_policy_ref.model_dump(
                mode="json"
            ),
        },
    )


def _manifest(journal_lines: tuple[BaseModel, ...]) -> list[dict[str, object]]:
    return [
        {
            "journal_line_ref": line.journal_line_id,
            "ledger_period_id": "2026-07",
            "presented_period_id": "2026-06",
            "account_id": line.account_id,
            "debit_minor": line.debit_minor,
            "credit_minor": line.credit_minor,
            "currency": line.currency,
            "basis_ref": {
                "object_type": "policy",
                "object_id": "POL-RESTATEMENT-v1",
            },
        }
        for line in journal_lines
    ]


def _restatement_object(
    status: str,
    *,
    event: BaseModel,
    proposal_event: BaseModel,
    approval_event: BaseModel,
    journal_lines: tuple[BaseModel, ...],
) -> BaseModel:
    linked = status != "PROPOSED_EMPTY"
    wire_status = "PROPOSED" if status.startswith("PROPOSED") else status
    ready = wire_status in {"ADJUSTMENTS_READY", "APPROVED", "PUBLISHED"}
    approved = wire_status in {"APPROVED", "PUBLISHED"}
    published = wire_status == "PUBLISHED"
    evidence_event = approval_event if published else event
    return validate_object(
        "restatement_case",
        {
            "contract_version": 1,
            "restatement_case_id": "RC-001",
            "status": wire_status,
            "scope_period_ids": ["2026-06"],
            "trigger_ref": proposal_event.basis.trigger_ref.model_dump(mode="json"),
            "directive_ref": proposal_event.basis.directive_ref.model_dump(mode="json"),
            "owner_ref": proposal_event.actor.model_dump(mode="json"),
            "linked_journal_ids": ["J-560"] if linked else [],
            "adjustment_manifest": _manifest(journal_lines) if ready else [],
            "manifest_hash": "sha256:" + "3" * 64 if ready else None,
            "approver_ref": approval_event.actor.model_dump(mode="json")
            if approved
            else None,
            "approved_at": approval_event.occurred_at if approved else None,
            "published_version_refs": ["RV-2026-06@v2"] if published else [],
            "evidence_refs": _evidence(evidence_event),
        },
    )


def _reporting_version(
    publication_event: BaseModel,
    v2_proof: ReportingContentProof,
) -> BaseModel:
    return validate_object(
        "reporting_version",
        {
            "contract_version": 1,
            "reporting_version_id": "RV-2026-06",
            "period_id": "2026-06",
            "version": 2,
            "reporting_version_ref": publication_event.payload.reporting_version_ref,
            "predecessor_version_ref": publication_event.basis.predecessor_version_ref,
            "restatement_case_id": publication_event.basis.restatement_case_id,
            "content_ref": publication_event.basis.content_ref,
            "content_hash": v2_proof.content_hash,
            "content_schema_version": v2_proof.content_schema_version,
            "adjustment_manifest_hash": publication_event.basis.manifest_hash,
            "published_at": publication_event.occurred_at,
            "published_by_event_id": publication_event.event_id,
            "evidence_refs": _evidence(publication_event),
        },
    )


def _execute(
    name: str,
    initial: HarnessState,
    commands: tuple[PlannerCommand, ...],
) -> ScenarioReplay:
    state = initial
    outcomes: list[DispatchOutcome] = []
    for command in commands:
        outcome = dispatch(state, command)
        if isinstance(outcome.result, Rejection):
            raise AssertionError(
                f"{name} {command.command_id} rejected: {outcome.result.code}"
            )
        if not isinstance(outcome.result, TransitionPlan) or not outcome.committed:
            raise AssertionError(f"{name} {command.command_id} did not commit")
        state = outcome.state
        outcomes.append(outcome)
    return ScenarioReplay(
        name=name,
        initial_state=initial,
        state=state,
        commands=commands,
        outcomes=tuple(outcomes),
        evaluator_input_ids=tuple(
            command.input_id
            for command in commands
            if isinstance(command, EvaluatePostingRule)
        ),
        correction_constructor_refs=tuple(
            command.proposal_ref
            for command in commands
            if isinstance(command, ConstructCorrectionProposal)
        ),
    )


def replay_c001(index: ValidatedCorpusIndex) -> ScenarioReplay:
    """Replay C-001 from declared bootstrap state through ordinary dispatch."""

    events = {str(item.value.event_id): item.value for item in index.c001_events}
    v1_proof, v2_proof = resolve_reporting_content(index)
    business_event = _object(
        index, "business_event", "business_event_id", "BE-C001-RECOG-202606"
    )
    posting_rule = _object(
        index, "posting_rule", "posting_rule_ref", "PR-O2C-RECOG@v1"
    )
    initial = HarnessState(
        snapshot=StateSnapshot(
            periods=(
                PeriodState("2026-06", "SOFT_CLOSED"),
                PeriodState("2026-07", "OPEN"),
            ),
            business_event_ids=frozenset({"BE-C001-RECOG-202606"}),
        ),
        object_versions=(business_event, posting_rule),
        reporting_content_proofs=(v1_proof,),
    )

    p551_v1 = _proposal_object("P-551@v1", "DEFERRED", events["AE-C001-001"])
    p551_v2 = _proposal_object("P-551@v2", "POSTED", events["AE-C001-005"])
    journal_package = _journal_package(
        p551_v2,
        events["AE-C001-007"],
        correction_basis={
            "restatement_case_id": "RC-001",
            "directive_ref": {
                "object_type": "remediation_directive",
                "object_id": "DIR-C001-001",
            },
        },
    )
    lines = tuple(journal_package[1:])
    rc_empty = _restatement_object(
        "PROPOSED_EMPTY",
        event=events["AE-C001-004"],
        proposal_event=events["AE-C001-004"],
        approval_event=events["AE-C001-010"],
        journal_lines=lines,
    )
    rc_linked = _restatement_object(
        "PROPOSED_LINKED",
        event=events["AE-C001-008"],
        proposal_event=events["AE-C001-004"],
        approval_event=events["AE-C001-010"],
        journal_lines=lines,
    )
    rc_ready = _restatement_object(
        "ADJUSTMENTS_READY",
        event=events["AE-C001-009"],
        proposal_event=events["AE-C001-004"],
        approval_event=events["AE-C001-010"],
        journal_lines=lines,
    )
    rc_approved = _restatement_object(
        "APPROVED",
        event=events["AE-C001-010"],
        proposal_event=events["AE-C001-004"],
        approval_event=events["AE-C001-010"],
        journal_lines=lines,
    )
    rc_published = _restatement_object(
        "PUBLISHED",
        event=events["AE-C001-011"],
        proposal_event=events["AE-C001-004"],
        approval_event=events["AE-C001-010"],
        journal_lines=lines,
    )
    rv2 = _reporting_version(events["AE-C001-011"], v2_proof)

    commands: tuple[PlannerCommand, ...] = (
        EvaluatePostingRule(
            command_id="CMD-C001-DERIVE-V1",
            input_id="BE-C001-RECOG-202606",
            proposal_ref="P-551@v1",
            target_period_id="2026-06",
            account_ids=frozenset(
                {"ACC-DEFERRED-REVENUE", "ACC-SUBSCRIPTION-REVENUE"}
            ),
            input_hashes=("sha256:" + "a" * 64,),
        ),
        SubmitProposal(
            command_id="CMD-C001-001",
            accounting_event=events["AE-C001-001"],
            proposal_ref="P-551@v1",
        ),
        DeferProposal(
            command_id="CMD-C001-002",
            accounting_event=events["AE-C001-002"],
            immutable_creations=(p551_v1,),
            proposal_ref="P-551@v1",
        ),
        HardClosePeriod(
            command_id="CMD-C001-003",
            accounting_event=events["AE-C001-003"],
            immutable_creations=(_hard_closed_period(events["AE-C001-003"]),),
            period_id="2026-06",
        ),
        ProposeRestatement(
            command_id="CMD-C001-004",
            accounting_event=events["AE-C001-004"],
            immutable_creations=(rc_empty,),
            case_id="RC-001",
            scope_period_ids=frozenset({"2026-06"}),
        ),
        ConstructCorrectionProposal(
            command_id="CMD-C001-DERIVE-V2",
            proposal_ref="P-551@v2",
            target_period_id="2026-07",
            origin_type="RESTATEMENT_ADJUSTMENT",
            account_ids=frozenset(
                {"ACC-DEFERRED-REVENUE", "ACC-SUBSCRIPTION-REVENUE"}
            ),
            input_hashes=("sha256:" + "e" * 64,),
        ),
        SubmitProposal(
            command_id="CMD-C001-005",
            accounting_event=events["AE-C001-005"],
            proposal_ref="P-551@v2",
        ),
        ApproveProposal(
            command_id="CMD-C001-006",
            accounting_event=events["AE-C001-006"],
            proposal_ref="P-551@v2",
            approver_id="USR-CONTROLLER-01",
            preparer_id="SYS-CORRECTION-ENGINE",
        ),
        PostProposal(
            command_id="CMD-C001-007",
            accounting_event=events["AE-C001-007"],
            immutable_creations=(p551_v2, *journal_package),
            proposal_ref="P-551@v2",
            effect_key="post:P-551@v2",
            entry_class="RESTATEMENT_ADJUSTMENT",
            restatement_case_id="RC-001",
        ),
        LinkRestatementAdjustment(
            command_id="CMD-C001-008",
            accounting_event=events["AE-C001-008"],
            immutable_creations=(rc_linked,),
            case_id="RC-001",
            journal_id="J-560",
            journal_case_id="RC-001",
        ),
        FreezeRestatementManifest(
            command_id="CMD-C001-009",
            accounting_event=events["AE-C001-009"],
            immutable_creations=(rc_ready,),
            case_id="RC-001",
            linked_journal_ids=frozenset({"J-560"}),
            presented_period_ids=frozenset({"2026-06"}),
            manifest_hash="sha256:" + "3" * 64,
        ),
        ApproveRestatement(
            command_id="CMD-C001-010",
            accounting_event=events["AE-C001-010"],
            immutable_creations=(rc_approved,),
            case_id="RC-001",
        ),
        PublishRestatement(
            command_id="CMD-C001-011",
            accounting_event=events["AE-C001-011"],
            immutable_creations=(rv2, rc_published),
            case_id="RC-001",
            predecessor_version_ref="RV-2026-06@v1",
            manifest_hash="sha256:" + "3" * 64,
            content_ref="reporting://2026-06/v2",
            effect_key="publish:RV-2026-06@v2",
        ),
    )
    return _execute("C-001", initial, commands)


def replay_ct1(index: ValidatedCorpusIndex) -> ScenarioReplay:
    """Replay CT-1 while preserving J-010 as non-authored G-13 state."""

    events = {str(item.value.event_id): item.value for item in index.ct1_events}
    projection = resolve_referenced_journal(index)
    initial = HarnessState.from_snapshot(
        StateSnapshot(
            periods=(PeriodState("2026-07", "OPEN"),),
            posted_journal_ids=frozenset({"J-010"}),
            referenced_journals=(projection,),
        )
    )
    reversal = _proposal_object(
        "P-REV-010@v1", "POSTED", events["AE-CT1-001"]
    )
    replacement = _proposal_object(
        "P-REP-010@v1", "POSTED", events["AE-CT1-004"]
    )
    reversal_package = _journal_package(
        reversal,
        events["AE-CT1-003"],
        correction_basis={"reverses_journal_id": "J-010"},
    )
    replacement_package = _journal_package(
        replacement,
        events["AE-CT1-006"],
        correction_basis={
            "corrects_journal_id": "J-010",
            "directive_ref": {
                "object_type": "remediation_directive",
                "object_id": "DIR-CT1-001",
            },
        },
    )
    commands: tuple[PlannerCommand, ...] = (
        ConstructCorrectionProposal(
            command_id="CMD-CT1-DERIVE-REVERSAL",
            proposal_ref="P-REV-010@v1",
            target_period_id="2026-07",
            origin_type="REVERSAL",
            account_ids=frozenset({"ACC-AR", "ACC-UNAPPLIED-CASH"}),
            input_hashes=(projection.source_hash,),
        ),
        ConstructCorrectionProposal(
            command_id="CMD-CT1-DERIVE-REPLACEMENT",
            proposal_ref="P-REP-010@v1",
            target_period_id="2026-07",
            origin_type="REPLACEMENT",
            account_ids=frozenset({"ACC-AR", "ACC-UNAPPLIED-CASH"}),
            input_hashes=("sha256:" + "9" * 64,),
        ),
        SubmitProposal(
            command_id="CMD-CT1-001",
            accounting_event=events["AE-CT1-001"],
            proposal_ref="P-REV-010@v1",
        ),
        ApproveProposal(
            command_id="CMD-CT1-002",
            accounting_event=events["AE-CT1-002"],
            proposal_ref="P-REV-010@v1",
            approver_id="USR-CONTROLLER-01",
            preparer_id="SYS-CORRECTION-ENGINE",
        ),
        PostProposal(
            command_id="CMD-CT1-003",
            accounting_event=events["AE-CT1-003"],
            immutable_creations=(reversal, *reversal_package),
            proposal_ref="P-REV-010@v1",
            effect_key="post:P-REV-010@v1",
            entry_class="REVERSAL",
            reverses_journal_id="J-010",
        ),
        SubmitProposal(
            command_id="CMD-CT1-004",
            accounting_event=events["AE-CT1-004"],
            proposal_ref="P-REP-010@v1",
        ),
        ApproveProposal(
            command_id="CMD-CT1-005",
            accounting_event=events["AE-CT1-005"],
            proposal_ref="P-REP-010@v1",
            approver_id="USR-CONTROLLER-01",
            preparer_id="SYS-CORRECTION-ENGINE",
        ),
        PostProposal(
            command_id="CMD-CT1-006",
            accounting_event=events["AE-CT1-006"],
            immutable_creations=(replacement, *replacement_package),
            proposal_ref="P-REP-010@v1",
            effect_key="post:P-REP-010@v1",
            entry_class="REPLACEMENT",
            corrects_journal_id="J-010",
        ),
    )
    return _execute("CT-1", initial, commands)
