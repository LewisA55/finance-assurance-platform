"""Single pure Artifact E transition planner for the reusable runtime kernel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel

from finance_assurance.runtime.contracts.objects import (
    JournalEntryBase,
    JournalLine,
    ReportingVersion,
)
from finance_assurance.runtime.referenced import ReferencedJournalProjection
from finance_assurance.runtime.rejections import Rejection, RejectionCode

ProposalStatus = Literal[
    "DRAFT",
    "SUBMITTED",
    "APPROVED",
    "POSTED",
    "REJECTED",
    "SUPERSEDED",
    "DEFERRED",
    "VOIDED",
    "APPROVAL_REVOKED",
]
PeriodStatus = Literal["OPEN", "SOFT_CLOSED", "HARD_CLOSED", "REOPENED"]
RestatementStatus = Literal[
    "PROPOSED",
    "ADJUSTMENTS_READY",
    "APPROVED",
    "PUBLISHED",
    "WITHDRAWN",
]
EntryClass = Literal[
    "REVERSAL",
    "REPLACEMENT",
    "RESTATEMENT_ADJUSTMENT",
    "AUTOMATED_POSTING",
]


@dataclass(frozen=True, slots=True)
class ProposalState:
    proposal_ref: str
    status: ProposalStatus
    target_period_id: str
    origin_type: EntryClass
    account_ids: frozenset[str] = frozenset()
    input_hashes: tuple[str, ...] = ()
    lines_balanced: bool = True
    dimensions_resolved: bool = True
    origin_basis_complete: bool = True


@dataclass(frozen=True, slots=True)
class PeriodState:
    period_id: str
    status: PeriodStatus


@dataclass(frozen=True, slots=True)
class RestatementState:
    case_id: str
    status: RestatementStatus
    scope_period_ids: frozenset[str]
    linked_journal_ids: frozenset[str] = frozenset()
    manifest_hash: str | None = None


@dataclass(frozen=True, slots=True)
class ReopenScope:
    period_id: str
    permitted_accounts: frozenset[str]
    permitted_origins: frozenset[EntryClass]


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    proposals: tuple[ProposalState, ...] = ()
    periods: tuple[PeriodState, ...] = ()
    restatements: tuple[RestatementState, ...] = ()
    reopen_scopes: tuple[ReopenScope, ...] = ()
    posted_journal_ids: frozenset[str] = frozenset()
    immutable_journal_ids: frozenset[str] = frozenset()
    frozen_manifest_case_ids: frozenset[str] = frozenset()
    published_reporting_refs: frozenset[str] = frozenset()
    business_event_ids: frozenset[str] = frozenset()
    accounting_event_ids: frozenset[str] = frozenset()
    consumed_effect_keys: frozenset[str] = frozenset()
    referenced_journals: tuple[ReferencedJournalProjection, ...] = ()

    def proposal(self, proposal_ref: str) -> ProposalState | None:
        return next(
            (item for item in self.proposals if item.proposal_ref == proposal_ref),
            None,
        )

    def referenced_journal(
        self,
        journal_id: str,
    ) -> ReferencedJournalProjection | None:
        return next(
            (item for item in self.referenced_journals if item.journal_id == journal_id),
            None,
        )

    def period(self, period_id: str) -> PeriodState | None:
        return next((item for item in self.periods if item.period_id == period_id), None)

    def restatement(self, case_id: str) -> RestatementState | None:
        return next(
            (item for item in self.restatements if item.case_id == case_id),
            None,
        )

    def reopen_scope(self, period_id: str) -> ReopenScope | None:
        return next(
            (item for item in self.reopen_scopes if item.period_id == period_id),
            None,
        )


@dataclass(frozen=True, slots=True)
class PlannedTransition:
    subject_type: Literal["journal_proposal", "accounting_period", "restatement_case", "posting_rule"]
    subject_ref: str
    from_state: str | None
    to_state: str | None


@dataclass(frozen=True, slots=True)
class TransitionPlan:
    command_id: str
    transition_id: str
    transition: PlannedTransition
    accounting_event: BaseModel | None
    immutable_creations: tuple[BaseModel, ...] = ()
    effect_key: str | None = None


@dataclass(frozen=True, slots=True)
class CommandBase:
    command_id: str
    accounting_event: BaseModel | None = None
    immutable_creations: tuple[BaseModel, ...] = ()


@dataclass(frozen=True, slots=True)
class EvaluatePostingRule(CommandBase):
    input_stream: Literal["BUSINESS_EVENT", "ACCOUNTING_EVENT"] = "BUSINESS_EVENT"
    input_id: str = ""
    proposal_ref: str = ""
    target_period_id: str = "UNASSIGNED"
    account_ids: frozenset[str] = frozenset()
    input_hashes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConstructCorrectionProposal(CommandBase):
    """Derive a correction draft without entering the posting-rule evaluator."""

    proposal_ref: str = ""
    target_period_id: str = ""
    origin_type: Literal["REVERSAL", "REPLACEMENT", "RESTATEMENT_ADJUSTMENT"] = (
        "RESTATEMENT_ADJUSTMENT"
    )
    account_ids: frozenset[str] = frozenset()
    input_hashes: tuple[str, ...] = ()
    derivation_basis_present: bool = True


@dataclass(frozen=True, slots=True)
class SubmitProposal(CommandBase):
    proposal_ref: str = ""


@dataclass(frozen=True, slots=True)
class ApproveProposal(CommandBase):
    proposal_ref: str = ""
    approver_id: str = ""
    preparer_id: str = ""
    sod_policy_prohibits_self_approval: bool = True
    sod_check_passed: bool = True
    evidence_complete: bool = True


@dataclass(frozen=True, slots=True)
class DeferProposal(CommandBase):
    proposal_ref: str = ""
    authority_valid: bool = True
    reason_present: bool = True
    owner_present: bool = True
    target_treatment_present: bool = True
    expiry_present: bool = True
    evidence_complete: bool = True


@dataclass(frozen=True, slots=True)
class PostProposal(CommandBase):
    proposal_ref: str = ""
    effect_key: str = ""
    approval_valid: bool = True
    entry_class: EntryClass = "RESTATEMENT_ADJUSTMENT"
    reverses_journal_id: str | None = None
    corrects_journal_id: str | None = None
    restatement_case_id: str | None = None


@dataclass(frozen=True, slots=True)
class HardClosePeriod(CommandBase):
    period_id: str = ""
    trial_balance_balanced: bool = True
    reconciliations_ready: bool = True
    unresolved_submitted_count: int = 0
    unresolved_approved_count: int = 0


@dataclass(frozen=True, slots=True)
class ReopenPeriod(CommandBase):
    period_id: str = ""
    directive_approved: bool = False
    scope_bounded: bool = False
    time_limit_present: bool = False
    evidence_complete: bool = False


@dataclass(frozen=True, slots=True)
class ProposeRestatement(CommandBase):
    case_id: str = ""
    trigger_present: bool = True
    directive_valid: bool = True
    scope_period_ids: frozenset[str] = frozenset()
    owner_present: bool = True
    evidence_complete: bool = True


@dataclass(frozen=True, slots=True)
class LinkRestatementAdjustment(CommandBase):
    case_id: str = ""
    journal_id: str = ""
    entry_class: EntryClass = "RESTATEMENT_ADJUSTMENT"
    journal_case_id: str | None = None


@dataclass(frozen=True, slots=True)
class FreezeRestatementManifest(CommandBase):
    case_id: str = ""
    linked_journal_ids: frozenset[str] = frozenset()
    reconciles_to_journal_lines: bool = True
    presented_period_ids: frozenset[str] = frozenset()
    manifest_hash: str | None = None


@dataclass(frozen=True, slots=True)
class ApproveRestatement(CommandBase):
    case_id: str = ""
    materiality_complete: bool = True
    evidence_complete: bool = True
    manifest_unchanged: bool = True
    disclosure_basis_complete: bool = True


@dataclass(frozen=True, slots=True)
class PublishRestatement(CommandBase):
    case_id: str = ""
    predecessor_version_ref: str = ""
    manifest_hash: str = ""
    content_ref: str = ""
    effect_key: str = ""


@dataclass(frozen=True, slots=True)
class MutateImmutableRecord(CommandBase):
    target_type: Literal["journal", "journal_line", "manifest", "reporting_version"] = "journal"
    target_ref: str = ""


@dataclass(frozen=True, slots=True)
class DirectReportingOverwrite(CommandBase):
    journal_id: str = ""
    reporting_version_ref: str = ""


@dataclass(frozen=True, slots=True)
class ApplyRemediationDirective(CommandBase):
    """Cross-module request that may fail before an Artifact F subject exists."""

    request_ref: str = ""
    directive_valid: bool = True


PlannerCommand = (
    EvaluatePostingRule
    | ConstructCorrectionProposal
    | SubmitProposal
    | ApproveProposal
    | DeferProposal
    | PostProposal
    | HardClosePeriod
    | ReopenPeriod
    | ProposeRestatement
    | LinkRestatementAdjustment
    | FreezeRestatementManifest
    | ApproveRestatement
    | PublishRestatement
    | MutateImmutableRecord
    | DirectReportingOverwrite
    | ApplyRemediationDirective
)
PlanResult = TransitionPlan | Rejection

_TERMINAL_PROPOSAL_STATES = {
    "POSTED",
    "REJECTED",
    "SUPERSEDED",
    "DEFERRED",
    "VOIDED",
    "APPROVAL_REVOKED",
}


def _reject(code: str, reason: str) -> Rejection:
    return Rejection(code=RejectionCode(code), reason=reason)


def _event_type(command: CommandBase) -> str | None:
    return (
        str(command.accounting_event.event_type)
        if command.accounting_event is not None
        else None
    )


def _accept(
    command: CommandBase,
    *,
    transition_id: str,
    subject_type: Literal[
        "journal_proposal",
        "accounting_period",
        "restatement_case",
        "posting_rule",
    ],
    subject_ref: str,
    from_state: str | None,
    to_state: str | None,
    expected_event_type: str | None,
    effect_key: str | None = None,
) -> PlanResult:
    if _event_type(command) != expected_event_type:
        return _reject("PLAN_INCOMPLETE", "accepted transition lacks its exact accounting event")
    return TransitionPlan(
        command_id=command.command_id,
        transition_id=transition_id,
        transition=PlannedTransition(
            subject_type=subject_type,
            subject_ref=subject_ref,
            from_state=from_state,
            to_state=to_state,
        ),
        accounting_event=command.accounting_event,
        immutable_creations=command.immutable_creations,
        effect_key=effect_key,
    )


def _posting_package(
    command: PostProposal,
) -> tuple[JournalEntryBase, tuple[JournalLine, ...]] | None:
    if command.accounting_event is None:
        return None
    journals = [
        item
        for item in command.immutable_creations
        if isinstance(item, JournalEntryBase)
    ]
    lines = [
        item for item in command.immutable_creations if isinstance(item, JournalLine)
    ]
    if len(journals) != 1 or len(lines) < 2:
        return None
    journal = journals[0]
    event = command.accounting_event
    debit = sum(line.debit_minor for line in lines)
    credit = sum(line.credit_minor for line in lines)
    valid = bool(
        journal.journal_id == event.payload.journal_id
        and journal.source_proposal_ref == command.proposal_ref
        and journal.posted_by_event_id == event.event_id
        and journal.entry_class == event.payload.entry_class == command.entry_class
        and set(journal.line_refs) == {line.journal_line_id for line in lines}
        and all(line.journal_id == journal.journal_id for line in lines)
        and debit == credit == journal.total_debit_minor == journal.total_credit_minor
        and event.basis.balance_debit_minor == debit
        and event.basis.balance_credit_minor == credit
        and event.idempotency_key == command.effect_key
    )
    return (journal, tuple(lines)) if valid else None


def _reversal_valid(
    command: PostProposal,
    proposal: ProposalState,
    state: StateSnapshot,
    lines: tuple[JournalLine, ...],
) -> bool:
    if command.reverses_journal_id is None:
        return False
    projection = state.referenced_journal(command.reverses_journal_id)
    if projection is None or projection.source_hash not in proposal.input_hashes:
        return False

    def identity(line: Any) -> tuple[object, ...]:
        dimensions = line.dimensions
        return (
            line.account_id,
            dimensions.legal_entity_id,
            dimensions.customer_id,
            dimensions.contract_id,
            line.currency,
        )

    by_identity = {identity(line): line for line in lines}
    if len(by_identity) != len(lines) or len(lines) != len(projection.line_tuples):
        return False
    return all(
        (reversal := by_identity.get(identity(source))) is not None
        and source.debit_minor == reversal.credit_minor
        and source.credit_minor == reversal.debit_minor
        for source in projection.line_tuples
    )


def _publication_creation_valid(command: PublishRestatement) -> bool:
    if command.accounting_event is None:
        return False
    versions = [
        item
        for item in command.immutable_creations
        if isinstance(item, ReportingVersion)
    ]
    if len(versions) != 1:
        return False
    version = versions[0]
    event = command.accounting_event
    return bool(
        version.reporting_version_ref == event.payload.reporting_version_ref
        and version.published_by_event_id == event.event_id
        and version.predecessor_version_ref == command.predecessor_version_ref
        and version.adjustment_manifest_hash == command.manifest_hash
        and version.content_ref == command.content_ref
        and event.basis.predecessor_version_ref == command.predecessor_version_ref
        and event.basis.manifest_hash == command.manifest_hash
        and event.basis.content_ref == command.content_ref
        and event.idempotency_key == command.effect_key
    )


def _posting_creations_valid(command: PostProposal) -> bool:
    if command.accounting_event is None:
        return False
    journals = [
        item for item in command.immutable_creations if isinstance(item, JournalEntryBase)
    ]
    lines = [item for item in command.immutable_creations if isinstance(item, JournalLine)]
    if len(journals) != 1 or len(lines) < 2:
        return False
    journal = journals[0]
    event = command.accounting_event
    return bool(
        journal.journal_id == event.payload.journal_id
        and journal.source_proposal_ref == command.proposal_ref
        and journal.posted_by_event_id == event.event_id
        and set(journal.line_refs) == {line.journal_line_id for line in lines}
        and all(line.journal_id == journal.journal_id for line in lines)
    )


def _publication_creation_valid(command: PublishRestatement) -> bool:
    if command.accounting_event is None:
        return False
    versions = [
        item for item in command.immutable_creations if isinstance(item, ReportingVersion)
    ]
    if len(versions) != 1:
        return False
    version = versions[0]
    event = command.accounting_event
    return bool(
        version.reporting_version_ref == event.payload.reporting_version_ref
        and version.published_by_event_id == event.event_id
    )


def _period_guard(
    state: StateSnapshot,
    period_id: str,
    origin: EntryClass,
    accounts: frozenset[str],
) -> Rejection | None:
    period = state.period(period_id)
    if period is None:
        return _reject("UNKNOWN_PERIOD", "target accounting period is absent")
    if period.status == "HARD_CLOSED":
        return _reject("HARD_CLOSED_PERIOD", "target accounting period is hard-closed")
    if period.status == "REOPENED":
        scope = state.reopen_scope(period_id)
        if (
            scope is None
            or origin not in scope.permitted_origins
            or not accounts.issubset(scope.permitted_accounts)
        ):
            return _reject("REOPEN_SCOPE_VIOLATION", "command falls outside authorised reopen scope")
    return None


def plan(command: PlannerCommand, state: StateSnapshot) -> PlanResult:
    """Return one immutable plan or rejection without I/O or mutation."""

    if isinstance(command, ApplyRemediationDirective):
        if not command.request_ref or not command.directive_valid:
            return _reject(
                "INVALID_REMEDIATION_DIRECTIVE",
                "remediation directive was rejected before target construction",
            )
        return _reject(
            "DEFERRED_TRANSITION",
            "valid cross-module directive construction is outside Milestone 1",
        )
    if isinstance(command, MutateImmutableRecord):
        return _reject("IMMUTABLE_RECORD", f"{command.target_type} cannot be mutated")
    if isinstance(command, DirectReportingOverwrite):
        return _reject(
            "REPORTING_OVERWRITE_PROHIBITED",
            "current-period journals cannot overwrite a prior reporting version",
        )
    if isinstance(command, EvaluatePostingRule):
        if (
            command.input_stream != "BUSINESS_EVENT"
            or command.input_id in state.accounting_event_ids
        ):
            return _reject("EVENT_STREAM_FIREWALL", "accounting events cannot enter the posting engine")
        if command.input_id not in state.business_event_ids:
            return _reject("UNKNOWN_BUSINESS_EVENT", "business event is not admitted")
        if not command.proposal_ref:
            return _reject("PLAN_INCOMPLETE", "derived proposal identity is missing")
        return _accept(
            command,
            transition_id="DERIVE_AUTOMATED_PROPOSAL",
            subject_type="journal_proposal",
            subject_ref=command.proposal_ref,
            from_state=None,
            to_state="DRAFT",
            expected_event_type=None,
        )
    if isinstance(command, ConstructCorrectionProposal):
        if (
            not command.proposal_ref
            or not command.target_period_id
            or not command.account_ids
            or not command.input_hashes
            or not command.derivation_basis_present
        ):
            return _reject(
                "CORRECTION_BASIS_INCOMPLETE",
                "correction proposal derivation basis is incomplete",
            )
        if state.proposal(command.proposal_ref) is not None:
            return _reject(
                "PROPOSAL_ALREADY_EXISTS",
                "correction proposal identity is already present",
            )
        return _accept(
            command,
            transition_id="DERIVE_CORRECTION_PROPOSAL",
            subject_type="journal_proposal",
            subject_ref=command.proposal_ref,
            from_state=None,
            to_state="DRAFT",
            expected_event_type=None,
        )
    if isinstance(command, SubmitProposal):
        proposal = state.proposal(command.proposal_ref)
        if proposal is None or proposal.status != "DRAFT":
            return _reject("PROPOSAL_NOT_DRAFT", "only a draft proposal can be submitted")
        period_rejection = _period_guard(
            state,
            proposal.target_period_id,
            proposal.origin_type,
            proposal.account_ids,
        )
        if period_rejection is not None:
            return period_rejection
        if not (
            proposal.lines_balanced
            and proposal.dimensions_resolved
            and proposal.origin_basis_complete
        ):
            return _reject("SUBMISSION_GUARD_FAILED", "submission basis is incomplete")
        return _accept(
            command,
            transition_id="P2",
            subject_type="journal_proposal",
            subject_ref=proposal.proposal_ref,
            from_state="DRAFT",
            to_state="SUBMITTED",
            expected_event_type="proposal.submitted",
        )
    if isinstance(command, ApproveProposal):
        proposal = state.proposal(command.proposal_ref)
        if proposal is None:
            return _reject("UNKNOWN_PROPOSAL", "proposal is absent")
        if proposal.status in _TERMINAL_PROPOSAL_STATES:
            return _reject("PROPOSAL_TERMINAL", "terminal proposal cannot be approved")
        if proposal.status != "SUBMITTED":
            return _reject("PROPOSAL_NOT_SUBMITTED", "proposal is not submitted")
        period_rejection = _period_guard(
            state,
            proposal.target_period_id,
            proposal.origin_type,
            proposal.account_ids,
        )
        if period_rejection is not None:
            return period_rejection
        self_approval = command.approver_id == command.preparer_id
        if (
            not command.sod_check_passed
            or (self_approval and command.sod_policy_prohibits_self_approval)
        ):
            return _reject("SEGREGATION_OF_DUTIES", "approval violates segregation of duties")
        if not command.evidence_complete:
            return _reject("APPROVAL_EVIDENCE_INCOMPLETE", "approval evidence is incomplete")
        return _accept(
            command,
            transition_id="P3",
            subject_type="journal_proposal",
            subject_ref=proposal.proposal_ref,
            from_state="SUBMITTED",
            to_state="APPROVED",
            expected_event_type="proposal.approved",
        )
    if isinstance(command, DeferProposal):
        proposal = state.proposal(command.proposal_ref)
        if proposal is None or proposal.status != "SUBMITTED":
            return _reject("PROPOSAL_NOT_SUBMITTED", "only a submitted proposal can be deferred")
        if not all(
            (
                command.authority_valid,
                command.reason_present,
                command.owner_present,
                command.target_treatment_present,
                command.expiry_present,
                command.evidence_complete,
            )
        ):
            return _reject("CLOSE_EXCEPTION_INCOMPLETE", "close exception basis is incomplete")
        return _accept(
            command,
            transition_id="P7",
            subject_type="journal_proposal",
            subject_ref=proposal.proposal_ref,
            from_state="SUBMITTED",
            to_state="DEFERRED",
            expected_event_type="proposal.deferred",
        )
    if isinstance(command, PostProposal):
        proposal = state.proposal(command.proposal_ref)
        if proposal is None or proposal.status != "APPROVED":
            return _reject("PROPOSAL_NOT_APPROVED", "only an approved proposal can post")
        period_rejection = _period_guard(
            state,
            proposal.target_period_id,
            proposal.origin_type,
            proposal.account_ids,
        )
        if period_rejection is not None:
            return period_rejection
        if command.effect_key in state.consumed_effect_keys:
            return _reject("DUPLICATE_EFFECT", "posting effect key is already consumed")
        if not command.approval_valid or not proposal.lines_balanced:
            return _reject("POSTING_GUARD_FAILED", "approval or balance guard failed")
        if command.entry_class != proposal.origin_type:
            return _reject("ENTRY_CLASS_MISMATCH", "posting class differs from proposal origin")
        posting_package = _posting_package(command)
        if posting_package is None:
            return _reject(
                "PLAN_INCOMPLETE",
                "posting plan lacks its exact immutable journal package",
            )
        _, posting_lines = posting_package
        if command.entry_class == "REVERSAL" and not _reversal_valid(
            command,
            proposal,
            state,
            posting_lines,
        ):
            return _reject("REVERSAL_MISMATCH", "reversal is not bound and equal-and-opposite")
        if command.entry_class == "REPLACEMENT" and not command.corrects_journal_id:
            return _reject("REPLACEMENT_BASIS_MISSING", "replacement lacks corrects_journal_id")
        if command.entry_class == "RESTATEMENT_ADJUSTMENT" and not command.restatement_case_id:
            return _reject("RESTATEMENT_CASE_MISSING", "restatement adjustment lacks case identity")
        return _accept(
            command,
            transition_id="P4",
            subject_type="journal_proposal",
            subject_ref=proposal.proposal_ref,
            from_state="APPROVED",
            to_state="POSTED",
            expected_event_type="journal.posted",
            effect_key=command.effect_key,
        )
    if isinstance(command, HardClosePeriod):
        period = state.period(command.period_id)
        if period is None or period.status != "SOFT_CLOSED":
            return _reject("PERIOD_NOT_SOFT_CLOSED", "hard close requires soft-closed state")
        if command.unresolved_submitted_count or command.unresolved_approved_count:
            return _reject("UNRESOLVED_PROPOSALS", "unresolved proposals prevent hard close")
        if not command.trial_balance_balanced or not command.reconciliations_ready:
            return _reject("CLOSE_INTEGRITY_FAILED", "close integrity checks failed")
        return _accept(
            command,
            transition_id="A3",
            subject_type="accounting_period",
            subject_ref=period.period_id,
            from_state="SOFT_CLOSED",
            to_state="HARD_CLOSED",
            expected_event_type="period.hard_closed",
        )
    if isinstance(command, ReopenPeriod):
        period = state.period(command.period_id)
        if period is None or period.status != "HARD_CLOSED":
            return _reject("PERIOD_NOT_HARD_CLOSED", "reopen requires hard-closed state")
        if not all(
            (
                command.directive_approved,
                command.scope_bounded,
                command.time_limit_present,
                command.evidence_complete,
            )
        ):
            return _reject("REOPEN_DIRECTIVE_INVALID", "reopen directive is not approved and bounded")
        return _reject("DEFERRED_TRANSITION", "successful reopen is outside Artifact F version 1")
    if isinstance(command, ProposeRestatement):
        if state.restatement(command.case_id) is not None:
            return _reject("RESTATEMENT_ALREADY_EXISTS", "restatement case already exists")
        if not (
            command.trigger_present
            and command.directive_valid
            and command.scope_period_ids
            and command.owner_present
            and command.evidence_complete
        ):
            return _reject("RESTATEMENT_BASIS_INCOMPLETE", "restatement initiation basis is incomplete")
        return _accept(
            command,
            transition_id="RS1",
            subject_type="restatement_case",
            subject_ref=command.case_id,
            from_state=None,
            to_state="PROPOSED",
            expected_event_type="restatement.proposed",
        )
    if isinstance(command, LinkRestatementAdjustment):
        case = state.restatement(command.case_id)
        if case is None or case.status != "PROPOSED":
            return _reject("RESTATEMENT_NOT_PROPOSED", "adjustment linking requires proposed case")
        if (
            command.journal_id not in state.posted_journal_ids
            or command.entry_class != "RESTATEMENT_ADJUSTMENT"
            or command.journal_case_id != command.case_id
        ):
            return _reject("RESTATEMENT_LINK_INVALID", "journal is not a valid case adjustment")
        return _accept(
            command,
            transition_id="RS2",
            subject_type="restatement_case",
            subject_ref=case.case_id,
            from_state="PROPOSED",
            to_state="PROPOSED",
            expected_event_type="restatement.adjustment_linked",
        )
    if isinstance(command, FreezeRestatementManifest):
        case = state.restatement(command.case_id)
        if case is None or case.status != "PROPOSED":
            return _reject("RESTATEMENT_NOT_PROPOSED", "manifest freeze requires proposed case")
        if (
            not command.linked_journal_ids
            or not command.linked_journal_ids.issubset(state.posted_journal_ids)
            or not command.reconciles_to_journal_lines
            or not command.presented_period_ids.issubset(case.scope_period_ids)
            or command.manifest_hash is None
        ):
            return _reject("MANIFEST_MISMATCH", "manifest does not reconcile to linked journals and scope")
        return _accept(
            command,
            transition_id="RS3",
            subject_type="restatement_case",
            subject_ref=case.case_id,
            from_state="PROPOSED",
            to_state="ADJUSTMENTS_READY",
            expected_event_type="restatement.adjustments_ready",
        )
    if isinstance(command, ApproveRestatement):
        case = state.restatement(command.case_id)
        if case is None or case.status != "ADJUSTMENTS_READY":
            return _reject("RESTATEMENT_NOT_READY", "restatement is not ready for approval")
        if not all(
            (
                command.materiality_complete,
                command.evidence_complete,
                command.manifest_unchanged,
                command.disclosure_basis_complete,
            )
        ):
            return _reject("RESTATEMENT_APPROVAL_INCOMPLETE", "restatement approval basis is incomplete")
        return _accept(
            command,
            transition_id="RS4",
            subject_type="restatement_case",
            subject_ref=case.case_id,
            from_state="ADJUSTMENTS_READY",
            to_state="APPROVED",
            expected_event_type="restatement.approved",
        )
    if isinstance(command, PublishRestatement):
        case = state.restatement(command.case_id)
        if case is None or case.status != "APPROVED":
            return _reject("RESTATEMENT_NOT_APPROVED", "only an approved restatement can publish")
        if command.effect_key in state.consumed_effect_keys:
            return _reject("DUPLICATE_EFFECT", "publication effect key is already consumed")
        if (
            not command.predecessor_version_ref
            or command.manifest_hash != case.manifest_hash
            or not command.content_ref
        ):
            return _reject("PUBLICATION_BASIS_INVALID", "publication basis is incomplete or changed")
        return _accept(
            command,
            transition_id="RS5",
            subject_type="restatement_case",
            subject_ref=case.case_id,
            from_state="APPROVED",
            to_state="PUBLISHED",
            expected_event_type="reporting_version.published",
            effect_key=command.effect_key,
        )
    raise TypeError(f"unsupported planner command: {type(command).__name__}")
