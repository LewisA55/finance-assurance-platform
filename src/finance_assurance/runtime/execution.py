"""Artifact K command execution over the single pure transition planner."""

from __future__ import annotations

from dataclasses import dataclass, replace

from finance_assurance.runtime.contracts.objects import JournalEntryBase
from finance_assurance.runtime.digests import value_digest
from finance_assurance.runtime.persistence.models import (
    CommandContext,
    CommandDisposition,
    CommandIdentityConflict,
    CommandResult,
    CommitReceipt,
    EffectRecord,
    ExactCommandResult,
    ExactConflictSnapshot,
    StagedRejectionSet,
    StagedWriteSet,
    StateExpectation,
    ValidatedAcceptedPlan,
    ValidatedRejectionPlan,
)
from finance_assurance.runtime.persistence.ports import CommandPersistenceBoundary
from finance_assurance.runtime.persistence.semantic_time import latest
from finance_assurance.runtime.persistence.state import InMemoryState, split_creations
from finance_assurance.runtime.planner import (
    ApplyRemediationDirective,
    ConstructCorrectionProposal,
    EvaluatePostingRule,
    FreezeRestatementManifest,
    LinkRestatementAdjustment,
    PlannerCommand,
    ProposalState,
    ProposeRestatement,
    PublishRestatement,
    RestatementState,
    StateSnapshot,
    TransitionPlan,
    plan,
)
from finance_assurance.runtime.rejections import Rejection, RejectionCode


class InjectedCommitFailure(RuntimeError):
    """Raised at the sole fault-injection point immediately before commit."""


@dataclass(frozen=True, slots=True)
class DispatchOutcome:
    state: InMemoryState
    result: TransitionPlan | Rejection
    replayed: bool = False
    committed: bool = False
    receipt: CommitReceipt | None = None


def _reject(code: str, reason: str) -> Rejection:
    return Rejection(code=RejectionCode(code), reason=reason)


def _replace_proposal(
    proposals: tuple[ProposalState, ...], proposal_ref: str, status: str
) -> tuple[ProposalState, ...]:
    return tuple(
        replace(item, status=status) if item.proposal_ref == proposal_ref else item
        for item in proposals
    )


def _replace_restatement(
    restatements: tuple[RestatementState, ...], replacement: RestatementState
) -> tuple[RestatementState, ...]:
    return tuple(
        replacement if item.case_id == replacement.case_id else item
        for item in restatements
    )


def _project_snapshot(
    snapshot: StateSnapshot, command: PlannerCommand, transition: TransitionPlan
) -> StateSnapshot:
    planned = transition.transition
    proposals = snapshot.proposals
    periods = snapshot.periods
    restatements = snapshot.restatements

    if planned.subject_type == "journal_proposal":
        if planned.from_state is None and planned.to_state == "DRAFT":
            if isinstance(command, ConstructCorrectionProposal):
                target_period_id = command.target_period_id
                origin_type = command.origin_type
                account_ids = command.account_ids
                input_hashes = command.input_hashes
            elif isinstance(command, EvaluatePostingRule):
                target_period_id = command.target_period_id
                origin_type = "AUTOMATED_POSTING"
                account_ids = command.account_ids
                input_hashes = command.input_hashes
            else:
                raise TypeError("unsupported proposal constructor")
            proposals = (
                *proposals,
                ProposalState(
                    proposal_ref=planned.subject_ref,
                    status="DRAFT",
                    target_period_id=target_period_id,
                    origin_type=origin_type,
                    account_ids=account_ids,
                    input_hashes=input_hashes,
                ),
            )
        elif planned.to_state is not None:
            proposals = _replace_proposal(
                proposals, planned.subject_ref, planned.to_state
            )
    elif planned.subject_type == "accounting_period" and planned.to_state:
        periods = tuple(
            replace(item, status=planned.to_state)
            if item.period_id == planned.subject_ref
            else item
            for item in periods
        )
    elif planned.subject_type == "restatement_case":
        existing = snapshot.restatement(planned.subject_ref)
        if existing is None and isinstance(command, ProposeRestatement):
            restatements = (
                *restatements,
                RestatementState(
                    case_id=command.case_id,
                    status="PROPOSED",
                    scope_period_ids=command.scope_period_ids,
                ),
            )
        elif existing is not None:
            linked = existing.linked_journal_ids
            manifest_hash = existing.manifest_hash
            if isinstance(command, LinkRestatementAdjustment):
                linked = linked | {command.journal_id}
            if isinstance(command, FreezeRestatementManifest):
                linked = command.linked_journal_ids
                manifest_hash = command.manifest_hash
            restatements = _replace_restatement(
                restatements,
                replace(
                    existing,
                    status=planned.to_state or existing.status,
                    linked_journal_ids=frozenset(linked),
                    manifest_hash=manifest_hash,
                ),
            )

    event = transition.accounting_event
    event_ids = snapshot.accounting_event_ids
    if event is not None:
        event_ids = event_ids | {str(event.event_id)}

    journal_ids = {
        item.journal_id
        for item in transition.immutable_creations
        if isinstance(item, JournalEntryBase)
    }
    reporting_refs = {
        item.reporting_version_ref
        for item in transition.immutable_creations
        if hasattr(item, "reporting_version_ref")
    }
    frozen_cases = snapshot.frozen_manifest_case_ids
    if isinstance(command, FreezeRestatementManifest):
        frozen_cases = frozen_cases | {command.case_id}

    return replace(
        snapshot,
        proposals=proposals,
        periods=periods,
        restatements=restatements,
        posted_journal_ids=snapshot.posted_journal_ids | journal_ids,
        immutable_journal_ids=snapshot.immutable_journal_ids | journal_ids,
        frozen_manifest_case_ids=frozen_cases,
        published_reporting_refs=(
            snapshot.published_reporting_refs | reporting_refs
        ),
        accounting_event_ids=event_ids,
        consumed_effect_keys=(
            snapshot.consumed_effect_keys
            | ({transition.effect_key} if transition.effect_key else set())
        ),
    )


def _command_fingerprint(command: PlannerCommand) -> str:
    return value_digest(command)


def command_context_for(command: PlannerCommand) -> CommandContext:
    """Build the fixed version-1 Artifact K context for one planner command."""
    event = command.accounting_event
    actor_ref = "SYSTEM"
    correlation_id = command.command_id
    semantic_as_of_time = "1970-01-01T00:00:00Z"
    if event is not None:
        actor_ref = str(event.actor.actor_id)
        correlation_id = str(event.correlation_id)
        semantic_as_of_time = str(event.recorded_at)
    else:
        creation_times = [
            str(value)
            for item in command.immutable_creations
            for field in ("available_from", "recorded_at", "created_at", "published_at")
            if (value := getattr(item, field, None)) is not None
        ]
        if creation_times:
            semantic_as_of_time = latest(*creation_times)
    return CommandContext(
        command_owner="ATLAS",
        command_id=command.command_id,
        command_type=type(command).__name__,
        input_contract_version="ARTIFACT-K-COMMAND-V1",
        input_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        input_digest=_command_fingerprint(command),
        actor_ref=actor_ref,
        authority_refs=(),
        semantic_as_of_time=semantic_as_of_time,
        correlation_id=correlation_id,
    )


def _same_command_identity(left: CommandContext, right: CommandContext) -> bool:
    return left.retry_identity == right.retry_identity


def rejection_write_set_for(
    command: PlannerCommand,
    command_result: CommandResult,
) -> StagedRejectionSet:
    dispositions: tuple[CommandDisposition, ...] = ()
    if isinstance(command, ApplyRemediationDirective):
        rejection = command_result.outcome
        if not isinstance(rejection, Rejection):
            raise ValueError("G-14 disposition requires a rejected command")
        dispositions = (
            CommandDisposition(
                contract_id="G-14",
                command_id=command.command_id,
                request_ref=command.request_ref,
                status="REJECTED",
                rejection_code=str(rejection.code),
                reason=rejection.reason,
            ),
        )
    return StagedRejectionSet(
        command_result=command_result,
        dispositions=dispositions,
    )


def write_set_for_transition(
    command: PlannerCommand,
    result: TransitionPlan,
    snapshot: StateSnapshot,
    command_result: CommandResult,
) -> StagedWriteSet:
    objects, journals, reporting = split_creations(result.immutable_creations)
    events = (result.accounting_event,) if result.accounting_event is not None else ()
    effects: tuple[EffectRecord, ...] = ()
    if result.effect_key is not None:
        event = result.accounting_event
        if event is None:
            raise ValueError("financial effect requires an accounting event")
        effects = (
            EffectRecord(
                idempotency_key=result.effect_key,
                effect_type=(
                    "PUBLICATION"
                    if isinstance(command, PublishRestatement)
                    else "POSTING"
                ),
                command_id=command.command_id,
                event_id=str(event.event_id),
                subject_ref=result.transition.subject_ref,
            ),
        )
    expected = StateExpectation(
        subject_type=result.transition.subject_type,
        subject_ref=result.transition.subject_ref,
        expected_state_token=result.transition.from_state or "ABSENT",
    )
    resulting = StateExpectation(
        subject_type=result.transition.subject_type,
        subject_ref=result.transition.subject_ref,
        expected_state_token=(
            result.transition.to_state
            or result.transition.from_state
            or "ABSENT"
        ),
    )
    return StagedWriteSet(
        projection_replacement=_project_snapshot(snapshot, command, result),
        object_appends=objects,
        accounting_event_appends=events,
        journal_appends=journals,
        reporting_version_appends=reporting,
        effect_claims=effects,
        expected_state_tokens=(expected,),
        resulting_state_tokens=(resulting,),
        command_result=command_result,
    )


def construct_conflict_rejection(snapshot: ExactConflictSnapshot) -> Rejection:
    if snapshot.conflict_class == "EFFECT_CONSUMED":
        return _reject("DUPLICATE_EFFECT", "financial effect key is already consumed")
    return _reject("STALE_STATE", "expected state token is no longer current")


def execute(
    boundary: CommandPersistenceBoundary,
    command: PlannerCommand,
    *,
    context: CommandContext | None = None,
    inject_failure_before_commit: bool = False,
) -> DispatchOutcome:
    """Execute one command through the complete Artifact K unit-of-work path."""

    supplied_context = context or command_context_for(command)
    if (
        supplied_context.command_id != command.command_id
        or supplied_context.input_digest != _command_fingerprint(command)
    ):
        raise ValueError("command context does not describe the supplied command")
    unit = boundary.begin_command(supplied_context)
    prior = unit.prior_result()
    if prior is not None:
        if _same_command_identity(prior.context, supplied_context):
            unit.rollback()
            return DispatchOutcome(
                state=boundary.state,
                result=prior.result.outcome,
                replayed=True,
            )
        unit.rollback()
        return DispatchOutcome(
            state=boundary.state,
            result=_reject(
                "COMMAND_ID_CONFLICT",
                "command_id is already bound to a different logical command",
            ),
        )

    result = plan(command, unit.records().snapshot())
    command_result = CommandResult(
        command_id=command.command_id,
        command_fingerprint=supplied_context.input_digest,
        status="REJECTED" if isinstance(result, Rejection) else "ACCEPTED",
        outcome=result,
    )

    if isinstance(result, Rejection):
        unit.stage_rejection(rejection_write_set_for(command, command_result))
        rejected_plan = unit.validate()
        if not isinstance(rejected_plan, ValidatedRejectionPlan):
            raise AssertionError("rejection validation returned an accepted plan")
        if inject_failure_before_commit:
            unit.rollback()
            raise InjectedCommitFailure("injected after validation and before commit")
        receipt = unit.commit(rejected_plan)
        return DispatchOutcome(
            state=boundary.state,
            result=result,
            committed=True,
            receipt=receipt,
        )

    unit.stage_accepted(
        write_set_for_transition(
            command,
            result,
            unit.records().snapshot(),
            command_result,
        )
    )
    validated = unit.validate()
    if not isinstance(validated, ValidatedAcceptedPlan):
        raise AssertionError("accepted command did not produce an accepted plan")
    arbitration = unit.arbitrate(validated)
    if isinstance(arbitration, ExactCommandResult):
        unit.rollback()
        return DispatchOutcome(
            state=boundary.state,
            result=arbitration.result.outcome,
            replayed=True,
        )
    if isinstance(arbitration, CommandIdentityConflict):
        unit.rollback()
        return DispatchOutcome(
            state=boundary.state,
            result=_reject(
                "COMMAND_ID_CONFLICT",
                "command_id is already bound to a different logical command",
            ),
        )
    if isinstance(arbitration, ExactConflictSnapshot):
        conflict_result = construct_conflict_rejection(arbitration)
        conflict_closure = CommandResult(
            command_id=command.command_id,
            command_fingerprint=supplied_context.input_digest,
            status="REJECTED",
            outcome=conflict_result,
        )
        unit.replace_with_conflict_rejection(
            arbitration,
            rejection_write_set_for(command, conflict_closure),
        )
        conflict_plan = unit.validate()
        if not isinstance(conflict_plan, ValidatedRejectionPlan):
            raise AssertionError("conflict rejection returned an accepted plan")
        if inject_failure_before_commit:
            unit.rollback()
            raise InjectedCommitFailure("injected after validation and before commit")
        receipt = unit.commit(conflict_plan)
        return DispatchOutcome(
            state=boundary.state,
            result=conflict_result,
            committed=True,
            receipt=receipt,
        )
    if inject_failure_before_commit:
        unit.rollback()
        raise InjectedCommitFailure("injected after validation and before commit")
    receipt = unit.commit(arbitration)
    return DispatchOutcome(
        state=boundary.state,
        result=result,
        committed=True,
        receipt=receipt,
    )


def dispatch(
    state: InMemoryState,
    command: PlannerCommand,
    *,
    inject_failure_before_commit: bool = False,
) -> DispatchOutcome:
    """Compatibility entry point over a fresh in-memory persistence boundary."""

    from finance_assurance.runtime.persistence.memory import InMemoryPersistenceBoundary

    return execute(
        InMemoryPersistenceBoundary(state),
        command,
        inject_failure_before_commit=inject_failure_before_commit,
    )
