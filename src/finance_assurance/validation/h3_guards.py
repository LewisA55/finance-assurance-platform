"""Phase 4 guard-correctness proofs for Artifact E PI-01 through PI-18."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from finance_assurance.validation.h2 import H2Run, run_h2
from finance_assurance.validation.index import ValidatedCorpusIndex
from finance_assurance.validation.planner import (
    ApproveProposal,
    ApproveRestatement,
    DeferProposal,
    DirectReportingOverwrite,
    EvaluatePostingRule,
    FreezeRestatementManifest,
    HardClosePeriod,
    LinkRestatementAdjustment,
    MutateImmutableRecord,
    PeriodState,
    PlannerCommand,
    PostProposal,
    ProposalState,
    ProposeRestatement,
    PublishRestatement,
    ReopenPeriod,
    ReopenScope,
    RestatementState,
    StateSnapshot,
    SubmitProposal,
    TransitionPlan,
    plan,
)
from finance_assurance.validation.proofs import resolve_referenced_journal
from finance_assurance.validation.results import (
    AssertionResult,
    AssertionStatus,
    Rejection,
)


@dataclass(frozen=True, slots=True)
class GuardCase:
    test_id: str
    commands: tuple[PlannerCommand, ...]
    state: StateSnapshot
    expected_code: str


@dataclass(frozen=True, slots=True)
class AcceptedControl:
    name: str
    command: PlannerCommand
    state: StateSnapshot
    transition_id: str


@dataclass(frozen=True, slots=True)
class H3GuardRun:
    results: tuple[AssertionResult, ...]
    accepted_controls: tuple[AcceptedControl, ...]

    @property
    def passed(self) -> bool:
        return all(result.status is AssertionStatus.PASS for result in self.results)


def _event(index: ValidatedCorpusIndex, event_id: str) -> BaseModel:
    return next(record.value for record in index.events if record.value.event_id == event_id)


def _object(
    index: ValidatedCorpusIndex,
    contract_key: str,
    field: str,
    value: str,
) -> BaseModel:
    return next(
        record.value
        for record in index.canonical_objects
        if record.contract_key == contract_key and getattr(record.value, field) == value
    )


def _journal_package(index: ValidatedCorpusIndex, journal_id: str) -> tuple[BaseModel, ...]:
    journal = _object(index, "journal_entry", "journal_id", journal_id)
    lines = tuple(
        record.value
        for record in index.canonical_objects
        if record.contract_key == "journal_line"
        and record.value.journal_id == journal_id
    )
    return (journal, *lines)


def _proposal(
    proposal_ref: str,
    status: str,
    period_id: str,
    origin: str,
    *,
    account_ids: frozenset[str] = frozenset(),
    input_hashes: tuple[str, ...] = (),
) -> ProposalState:
    return ProposalState(
        proposal_ref=proposal_ref,
        status=status,  # type: ignore[arg-type]
        target_period_id=period_id,
        origin_type=origin,  # type: ignore[arg-type]
        account_ids=account_ids,
        input_hashes=input_hashes,
    )


def _restatement(status: str, manifest_hash: str | None = None) -> RestatementState:
    return RestatementState(
        case_id="RC-001",
        status=status,  # type: ignore[arg-type]
        scope_period_ids=frozenset({"2026-06"}),
        linked_journal_ids=frozenset({"J-560"}),
        manifest_hash=manifest_hash,
    )


def _post_command(
    index: ValidatedCorpusIndex,
    *,
    event_id: str,
    proposal_ref: str,
    journal_id: str,
    effect_key: str,
    entry_class: str,
    reverses_journal_id: str | None = None,
    corrects_journal_id: str | None = None,
    restatement_case_id: str | None = None,
    corrupt_reversal: bool = False,
) -> PostProposal:
    event = _event(index, event_id)
    package = _journal_package(index, journal_id)
    if corrupt_reversal:
        journal, first_line, *other_lines = package
        package = (
            journal,
            first_line.model_copy(update={"account_id": "ACC-OTHER"}),
            *other_lines,
        )
    return PostProposal(
        command_id=str(event.command_id),
        accounting_event=event,
        immutable_creations=package,
        proposal_ref=proposal_ref,
        effect_key=effect_key,
        entry_class=entry_class,  # type: ignore[arg-type]
        reverses_journal_id=reverses_journal_id,
        corrects_journal_id=corrects_journal_id,
        restatement_case_id=restatement_case_id,
    )


def _publish_command(index: ValidatedCorpusIndex) -> PublishRestatement:
    event = _event(index, "AE-C001-011")
    version = _object(
        index,
        "reporting_version",
        "reporting_version_ref",
        "RV-2026-06@v2",
    )
    return PublishRestatement(
        command_id=str(event.command_id),
        accounting_event=event,
        immutable_creations=(version,),
        case_id="RC-001",
        predecessor_version_ref="RV-2026-06@v1",
        manifest_hash="sha256:" + "3" * 64,
        content_ref="reporting://2026-06/v2",
        effect_key="publish:RV-2026-06@v2",
    )


def accepted_controls(index: ValidatedCorpusIndex) -> tuple[AcceptedControl, ...]:
    july = PeriodState("2026-07", "OPEN")
    june_soft = PeriodState("2026-06", "SOFT_CLOSED")
    manifest_hash = "sha256:" + "3" * 64

    submit_event = _event(index, "AE-C001-005")
    defer_event = _event(index, "AE-C001-002")
    approve_event = _event(index, "AE-C001-006")
    close_event = _event(index, "AE-C001-003")
    propose_event = _event(index, "AE-C001-004")
    link_event = _event(index, "AE-C001-008")
    freeze_event = _event(index, "AE-C001-009")
    restatement_approve_event = _event(index, "AE-C001-010")

    controls = (
        AcceptedControl(
            "business-event derivation",
            EvaluatePostingRule(
                command_id="CMD-DERIVE-C001",
                input_stream="BUSINESS_EVENT",
                input_id="BE-C001-RECOG-202606",
                proposal_ref="P-551@v1",
            ),
            StateSnapshot(
                business_event_ids=frozenset({"BE-C001-RECOG-202606"}),
            ),
            "DERIVE_AUTOMATED_PROPOSAL",
        ),
        AcceptedControl(
            "proposal submission",
            SubmitProposal(
                command_id=str(submit_event.command_id),
                accounting_event=submit_event,
                proposal_ref="P-551@v2",
            ),
            StateSnapshot(
                proposals=(
                    _proposal("P-551@v2", "DRAFT", "2026-07", "RESTATEMENT_ADJUSTMENT"),
                ),
                periods=(july,),
                restatements=(_restatement("PROPOSED"),),
            ),
            "P2",
        ),
        AcceptedControl(
            "close deferral",
            DeferProposal(
                command_id=str(defer_event.command_id),
                accounting_event=defer_event,
                proposal_ref="P-551@v1",
            ),
            StateSnapshot(
                proposals=(
                    _proposal("P-551@v1", "SUBMITTED", "2026-06", "AUTOMATED_POSTING"),
                ),
                periods=(june_soft,),
            ),
            "P7",
        ),
        AcceptedControl(
            "proposal approval",
            ApproveProposal(
                command_id=str(approve_event.command_id),
                accounting_event=approve_event,
                proposal_ref="P-551@v2",
                approver_id="USR-CONTROLLER-01",
                preparer_id="SYS-CORRECTION-ENGINE",
            ),
            StateSnapshot(
                proposals=(
                    _proposal(
                        "P-551@v2",
                        "SUBMITTED",
                        "2026-07",
                        "RESTATEMENT_ADJUSTMENT",
                        account_ids=frozenset({"ACC-SUBSCRIPTION-REVENUE"}),
                    ),
                ),
                periods=(july,),
            ),
            "P3",
        ),
        AcceptedControl(
            "restatement posting",
            _post_command(
                index,
                event_id="AE-C001-007",
                proposal_ref="P-551@v2",
                journal_id="J-560",
                effect_key="post:P-551@v2",
                entry_class="RESTATEMENT_ADJUSTMENT",
                restatement_case_id="RC-001",
            ),
            StateSnapshot(
                proposals=(
                    _proposal("P-551@v2", "APPROVED", "2026-07", "RESTATEMENT_ADJUSTMENT"),
                ),
                periods=(july,),
                restatements=(_restatement("PROPOSED"),),
            ),
            "P4",
        ),
        AcceptedControl(
            "reversal posting",
            _post_command(
                index,
                event_id="AE-CT1-003",
                proposal_ref="P-REV-010@v1",
                journal_id="J-011",
                effect_key="post:P-REV-010@v1",
                entry_class="REVERSAL",
                reverses_journal_id="J-010",
            ),
            StateSnapshot(
                proposals=(
                    _proposal(
                        "P-REV-010@v1",
                        "APPROVED",
                        "2026-07",
                        "REVERSAL",
                        input_hashes=("sha256:" + "6" * 64,),
                    ),
                ),
                periods=(july,),
                posted_journal_ids=frozenset({"J-010"}),
                referenced_journals=(resolve_referenced_journal(index),),
            ),
            "P4",
        ),
        AcceptedControl(
            "replacement posting",
            _post_command(
                index,
                event_id="AE-CT1-006",
                proposal_ref="P-REP-010@v1",
                journal_id="J-012",
                effect_key="post:P-REP-010@v1",
                entry_class="REPLACEMENT",
                corrects_journal_id="J-010",
            ),
            StateSnapshot(
                proposals=(
                    _proposal("P-REP-010@v1", "APPROVED", "2026-07", "REPLACEMENT"),
                ),
                periods=(july,),
            ),
            "P4",
        ),
        AcceptedControl(
            "hard close",
            HardClosePeriod(
                command_id=str(close_event.command_id),
                accounting_event=close_event,
                period_id="2026-06",
            ),
            StateSnapshot(periods=(june_soft,)),
            "A3",
        ),
        AcceptedControl(
            "restatement proposal",
            ProposeRestatement(
                command_id=str(propose_event.command_id),
                accounting_event=propose_event,
                case_id="RC-001",
                scope_period_ids=frozenset({"2026-06"}),
            ),
            StateSnapshot(),
            "RS1",
        ),
        AcceptedControl(
            "adjustment link",
            LinkRestatementAdjustment(
                command_id=str(link_event.command_id),
                accounting_event=link_event,
                case_id="RC-001",
                journal_id="J-560",
                journal_case_id="RC-001",
            ),
            StateSnapshot(
                restatements=(_restatement("PROPOSED"),),
                posted_journal_ids=frozenset({"J-560"}),
            ),
            "RS2",
        ),
        AcceptedControl(
            "manifest freeze",
            FreezeRestatementManifest(
                command_id=str(freeze_event.command_id),
                accounting_event=freeze_event,
                case_id="RC-001",
                linked_journal_ids=frozenset({"J-560"}),
                presented_period_ids=frozenset({"2026-06"}),
                manifest_hash=manifest_hash,
            ),
            StateSnapshot(
                restatements=(_restatement("PROPOSED"),),
                posted_journal_ids=frozenset({"J-560"}),
            ),
            "RS3",
        ),
        AcceptedControl(
            "restatement approval",
            ApproveRestatement(
                command_id=str(restatement_approve_event.command_id),
                accounting_event=restatement_approve_event,
                case_id="RC-001",
            ),
            StateSnapshot(
                restatements=(_restatement("ADJUSTMENTS_READY", manifest_hash),),
            ),
            "RS4",
        ),
        AcceptedControl(
            "reporting publication",
            _publish_command(index),
            StateSnapshot(
                restatements=(_restatement("APPROVED", manifest_hash),),
            ),
            "RS5",
        ),
    )
    return controls


def guard_cases(index: ValidatedCorpusIndex) -> tuple[GuardCase, ...]:
    july = PeriodState("2026-07", "OPEN")
    june_hard = PeriodState("2026-06", "HARD_CLOSED")
    june_soft = PeriodState("2026-06", "SOFT_CLOSED")
    manifest_hash = "sha256:" + "3" * 64
    post_rest = _post_command(
        index,
        event_id="AE-C001-007",
        proposal_ref="P-551@v2",
        journal_id="J-560",
        effect_key="post:P-551@v2",
        entry_class="RESTATEMENT_ADJUSTMENT",
        restatement_case_id="RC-001",
    )
    publish = _publish_command(index)
    approve_event = _event(index, "AE-C001-006")
    close_event = _event(index, "AE-C001-003")
    defer_event = _event(index, "AE-C001-002")
    freeze_event = _event(index, "AE-C001-009")

    return (
        GuardCase(
            "H3-01",
            (post_rest,),
            StateSnapshot(
                proposals=(
                    _proposal(
                        "P-551@v2",
                        "SUBMITTED",
                        "2026-07",
                        "RESTATEMENT_ADJUSTMENT",
                        account_ids=frozenset({"ACC-DEFERRED-REVENUE"}),
                    ),
                ),
                periods=(july,),
            ),
            "PROPOSAL_NOT_APPROVED",
        ),
        GuardCase(
            "H3-02",
            (
                ApproveProposal(
                    command_id=str(approve_event.command_id),
                    accounting_event=approve_event,
                    proposal_ref="P-551@v2",
                    approver_id="USR-CONTROLLER-01",
                    preparer_id="SYS-CORRECTION-ENGINE",
                ),
            ),
            StateSnapshot(
                proposals=(
                    _proposal("P-551@v2", "POSTED", "2026-07", "RESTATEMENT_ADJUSTMENT"),
                ),
                periods=(july,),
            ),
            "PROPOSAL_TERMINAL",
        ),
        GuardCase(
            "H3-03",
            (MutateImmutableRecord(command_id="CMD-PI03", target_type="journal", target_ref="J-560"),),
            StateSnapshot(immutable_journal_ids=frozenset({"J-560"})),
            "IMMUTABLE_RECORD",
        ),
        GuardCase(
            "H3-04",
            (post_rest,),
            StateSnapshot(
                proposals=(
                    _proposal("P-551@v2", "APPROVED", "2026-06", "RESTATEMENT_ADJUSTMENT"),
                ),
                periods=(june_hard,),
            ),
            "HARD_CLOSED_PERIOD",
        ),
        GuardCase(
            "H3-05",
            (
                HardClosePeriod(
                    command_id=str(close_event.command_id),
                    accounting_event=close_event,
                    period_id="2026-06",
                    unresolved_submitted_count=1,
                ),
                HardClosePeriod(
                    command_id=str(close_event.command_id),
                    accounting_event=close_event,
                    period_id="2026-06",
                    unresolved_approved_count=1,
                ),
            ),
            StateSnapshot(periods=(june_soft,)),
            "UNRESOLVED_PROPOSALS",
        ),
        GuardCase(
            "H3-06",
            (
                DeferProposal(
                    command_id=str(defer_event.command_id),
                    accounting_event=defer_event,
                    proposal_ref="P-551@v1",
                    authority_valid=False,
                ),
            ),
            StateSnapshot(
                proposals=(
                    _proposal("P-551@v1", "SUBMITTED", "2026-06", "AUTOMATED_POSTING"),
                ),
            ),
            "CLOSE_EXCEPTION_INCOMPLETE",
        ),
        GuardCase(
            "H3-07",
            (
                ApproveProposal(
                    command_id=str(approve_event.command_id),
                    accounting_event=approve_event,
                    proposal_ref="P-551@v2",
                    approver_id="USR-CONTROLLER-01",
                    preparer_id="USR-CONTROLLER-01",
                ),
            ),
            StateSnapshot(
                proposals=(
                    _proposal("P-551@v2", "SUBMITTED", "2026-07", "RESTATEMENT_ADJUSTMENT"),
                ),
                periods=(july,),
            ),
            "SEGREGATION_OF_DUTIES",
        ),
        GuardCase(
            "H3-08",
            (
                EvaluatePostingRule(
                    command_id="CMD-PI08",
                    input_stream="ACCOUNTING_EVENT",
                    input_id="AE-C001-001",
                ),
            ),
            StateSnapshot(accounting_event_ids=frozenset({"AE-C001-001"})),
            "EVENT_STREAM_FIREWALL",
        ),
        GuardCase(
            "H3-09",
            (ReopenPeriod(command_id="CMD-PI09", period_id="2026-06"),),
            StateSnapshot(periods=(june_hard,)),
            "REOPEN_DIRECTIVE_INVALID",
        ),
        GuardCase(
            "H3-10",
            (
                ApproveProposal(
                    command_id=str(approve_event.command_id),
                    accounting_event=approve_event,
                    proposal_ref="P-551@v2",
                    approver_id="USR-CONTROLLER-01",
                    preparer_id="SYS-CORRECTION-ENGINE",
                ),
            ),
            StateSnapshot(
                proposals=(
                    _proposal(
                        "P-551@v2",
                        "SUBMITTED",
                        "2026-07",
                        "RESTATEMENT_ADJUSTMENT",
                        account_ids=frozenset({"ACC-DEFERRED-REVENUE"}),
                    ),
                ),
                periods=(PeriodState("2026-07", "REOPENED"),),
                reopen_scopes=(
                    ReopenScope(
                        "2026-07",
                        frozenset({"ACC-OTHER"}),
                        frozenset({"RESTATEMENT_ADJUSTMENT"}),
                    ),
                ),
            ),
            "REOPEN_SCOPE_VIOLATION",
        ),
        GuardCase(
            "H3-11",
            (publish,),
            StateSnapshot(restatements=(_restatement("PROPOSED", manifest_hash),)),
            "RESTATEMENT_NOT_APPROVED",
        ),
        GuardCase(
            "H3-12",
            (
                _post_command(
                    index,
                    event_id="AE-CT1-003",
                    proposal_ref="P-REV-010@v1",
                    journal_id="J-011",
                    effect_key="post:P-REV-010@v1",
                    entry_class="REVERSAL",
                    reverses_journal_id="J-010",
                    corrupt_reversal=True,
                ),
            ),
            StateSnapshot(
                proposals=(
                    _proposal(
                        "P-REV-010@v1",
                        "APPROVED",
                        "2026-07",
                        "REVERSAL",
                        input_hashes=("sha256:" + "6" * 64,),
                    ),
                ),
                periods=(july,),
                posted_journal_ids=frozenset({"J-010"}),
                referenced_journals=(resolve_referenced_journal(index),),
            ),
            "REVERSAL_MISMATCH",
        ),
        GuardCase(
            "H3-13",
            (
                _post_command(
                    index,
                    event_id="AE-CT1-006",
                    proposal_ref="P-REP-010@v1",
                    journal_id="J-012",
                    effect_key="post:P-REP-010@v1",
                    entry_class="REPLACEMENT",
                ),
            ),
            StateSnapshot(
                proposals=(
                    _proposal("P-REP-010@v1", "APPROVED", "2026-07", "REPLACEMENT"),
                ),
                periods=(july,),
            ),
            "REPLACEMENT_BASIS_MISSING",
        ),
        GuardCase(
            "H3-14",
            (
                _post_command(
                    index,
                    event_id="AE-C001-007",
                    proposal_ref="P-551@v2",
                    journal_id="J-560",
                    effect_key="post:P-551@v2",
                    entry_class="RESTATEMENT_ADJUSTMENT",
                ),
            ),
            StateSnapshot(
                proposals=(
                    _proposal("P-551@v2", "APPROVED", "2026-07", "RESTATEMENT_ADJUSTMENT"),
                ),
                periods=(july,),
            ),
            "RESTATEMENT_CASE_MISSING",
        ),
        GuardCase(
            "H3-15",
            (
                FreezeRestatementManifest(
                    command_id=str(freeze_event.command_id),
                    accounting_event=freeze_event,
                    case_id="RC-001",
                    linked_journal_ids=frozenset({"J-560"}),
                    reconciles_to_journal_lines=False,
                    presented_period_ids=frozenset({"2026-06"}),
                    manifest_hash=manifest_hash,
                ),
            ),
            StateSnapshot(
                restatements=(_restatement("PROPOSED"),),
                posted_journal_ids=frozenset({"J-560"}),
            ),
            "MANIFEST_MISMATCH",
        ),
        GuardCase(
            "H3-16",
            (MutateImmutableRecord(command_id="CMD-PI16", target_type="manifest", target_ref="RC-001"),),
            StateSnapshot(frozen_manifest_case_ids=frozenset({"RC-001"})),
            "IMMUTABLE_RECORD",
        ),
        GuardCase(
            "H3-17",
            (
                DirectReportingOverwrite(
                    command_id="CMD-PI17",
                    journal_id="J-560",
                    reporting_version_ref="RV-2026-06@v1",
                ),
            ),
            StateSnapshot(
                immutable_journal_ids=frozenset({"J-560"}),
                published_reporting_refs=frozenset({"RV-2026-06@v1"}),
            ),
            "REPORTING_OVERWRITE_PROHIBITED",
        ),
        GuardCase(
            "H3-18",
            (post_rest, publish),
            StateSnapshot(
                proposals=(
                    _proposal("P-551@v2", "APPROVED", "2026-07", "RESTATEMENT_ADJUSTMENT"),
                ),
                periods=(july,),
                restatements=(_restatement("APPROVED", manifest_hash),),
                consumed_effect_keys=frozenset(
                    {"post:P-551@v2", "publish:RV-2026-06@v2"}
                ),
            ),
            "DUPLICATE_EFFECT",
        ),
    )


def run_h3_guards(
    root: Path | None = None,
    *,
    h2_run: H2Run | None = None,
) -> H3GuardRun:
    """Prove guard decisions only; full H3 no-mutation remains Phase 5."""

    h2 = h2_run or run_h2(root)
    if not h2.passed or h2.index is None:
        results = tuple(
            AssertionResult(
                test_id=f"H3-{number:02d}",
                layer="H3_GUARD",
                source_obligation=f"PI-{number:02d}",
                status=AssertionStatus.BLOCKED,
                expected_outcome="H2 must pass before H3 guard evaluation",
                actual_outcome="Blocked because H2 failed",
            )
            for number in range(1, 19)
        )
        return H3GuardRun(results=results, accepted_controls=())

    controls = accepted_controls(h2.index)
    results: list[AssertionResult] = []
    for case in guard_cases(h2.index):
        outcomes = tuple(plan(command, case.state) for command in case.commands)
        codes = tuple(
            str(outcome.code) if isinstance(outcome, Rejection) else "ACCEPTED"
            for outcome in outcomes
        )
        matched = sum(code == case.expected_code for code in codes)
        passed = matched == len(codes)
        results.append(
            AssertionResult(
                test_id=case.test_id,
                layer="H3_GUARD",
                source_obligation=f"PI-{case.test_id[-2:]}",
                status=AssertionStatus.PASS if passed else AssertionStatus.FAIL,
                expected_outcome=f"all attempts rejected with {case.expected_code}",
                actual_outcome=(
                    f"{matched}/{len(codes)} rejected as expected: {','.join(codes)}"
                ),
            )
        )

    for control in controls:
        outcome = plan(control.command, control.state)
        if not isinstance(outcome, TransitionPlan) or outcome.transition_id != control.transition_id:
            results.append(
                AssertionResult(
                    test_id=f"H3-CONTROL-{control.transition_id}",
                    layer="H3_GUARD",
                    source_obligation="Artifact H section 12 accepted control",
                    status=AssertionStatus.FAIL,
                    expected_outcome=f"accepted {control.transition_id}",
                    actual_outcome=(
                        f"rejected with {outcome.code}"
                        if isinstance(outcome, Rejection)
                        else "wrong transition plan"
                    ),
                )
            )
    return H3GuardRun(results=tuple(results), accepted_controls=controls)
