"""Pure projection replay shared by persistence and semantic query sessions."""

from __future__ import annotations

from dataclasses import replace

from finance_assurance.runtime.application.models import ProposalTreatmentVersion
from finance_assurance.runtime.contracts.events import (
    RestatementAdjustmentLinked,
    RestatementAdjustmentsReady,
    RestatementProposed,
)
from finance_assurance.runtime.contracts.objects import JournalEntryBase
from finance_assurance.runtime.planner import (
    ProposalState,
    RestatementState,
    StateSnapshot,
    TransitionPlan,
)


class ProjectionReplayError(RuntimeError):
    """Raised when immutable authority cannot reproduce a projection."""


def replay_transition(
    snapshot: StateSnapshot,
    outcome: TransitionPlan,
) -> StateSnapshot:
    """Fold one committed transition closure into a rebuildable projection."""

    transition = outcome.transition
    proposals = snapshot.proposals
    periods = snapshot.periods
    restatements = snapshot.restatements
    if transition.subject_type == "journal_proposal":
        existing = snapshot.proposal(transition.subject_ref)
        if transition.from_state is None:
            treatments = [
                item
                for item in outcome.immutable_creations
                if isinstance(item, ProposalTreatmentVersion)
                and item.proposal_ref == transition.subject_ref
            ]
            if len(treatments) != 1 or existing is not None:
                raise ProjectionReplayError(
                    "proposal constructor requires one exact J-AR05 treatment"
                )
            treatment = treatments[0]
            proposals = (
                *proposals,
                ProposalState(
                    proposal_ref=treatment.proposal_ref,
                    status="DRAFT",
                    target_period_id=treatment.target_period_id,
                    origin_type=treatment.origin_type,
                    account_ids=treatment.account_ids,
                    input_hashes=treatment.input_hashes,
                ),
            )
        else:
            if existing is None:
                raise ProjectionReplayError(
                    "proposal transition has no J-AR05 treatment"
                )
            proposals = tuple(
                replace(item, status=transition.to_state)
                if item.proposal_ref == transition.subject_ref
                else item
                for item in proposals
            )
    elif transition.subject_type == "accounting_period":
        if snapshot.period(transition.subject_ref) is None:
            raise ProjectionReplayError("period transition has no baseline object")
        periods = tuple(
            replace(item, status=transition.to_state)
            if item.period_id == transition.subject_ref
            else item
            for item in periods
        )
    elif transition.subject_type == "restatement_case":
        existing = snapshot.restatement(transition.subject_ref)
        event = outcome.accounting_event
        if transition.from_state is None:
            if not isinstance(event, RestatementProposed) or existing is not None:
                raise ProjectionReplayError(
                    "restatement constructor requires its proposed event"
                )
            restatements = (
                *restatements,
                RestatementState(
                    case_id=transition.subject_ref,
                    status="PROPOSED",
                    scope_period_ids=frozenset(event.basis.scope_period_ids),
                ),
            )
        else:
            if existing is None:
                raise ProjectionReplayError(
                    "restatement transition has no proposed case"
                )
            linked = existing.linked_journal_ids
            manifest_hash = existing.manifest_hash
            if isinstance(event, RestatementAdjustmentLinked):
                linked = linked | {str(event.payload.journal_id)}
            if isinstance(event, RestatementAdjustmentsReady):
                linked = frozenset(str(item) for item in event.basis.linked_journal_ids)
                manifest_hash = str(event.basis.manifest_hash)
            replacement = replace(
                existing,
                status=transition.to_state,
                linked_journal_ids=linked,
                manifest_hash=manifest_hash,
            )
            restatements = tuple(
                replacement if item.case_id == transition.subject_ref else item
                for item in restatements
            )
    event_ids = snapshot.accounting_event_ids
    if outcome.accounting_event is not None:
        event_ids = event_ids | {str(outcome.accounting_event.event_id)}
    journal_ids = {
        item.journal_id
        for item in outcome.immutable_creations
        if isinstance(item, JournalEntryBase)
    }
    reporting_refs = {
        str(item.reporting_version_ref)
        for item in outcome.immutable_creations
        if hasattr(item, "reporting_version_ref")
    }
    frozen_cases = snapshot.frozen_manifest_case_ids
    if isinstance(outcome.accounting_event, RestatementAdjustmentsReady):
        frozen_cases = frozen_cases | {transition.subject_ref}
    return replace(
        snapshot,
        proposals=proposals,
        periods=periods,
        restatements=restatements,
        posted_journal_ids=snapshot.posted_journal_ids | journal_ids,
        immutable_journal_ids=snapshot.immutable_journal_ids | journal_ids,
        frozen_manifest_case_ids=frozen_cases,
        published_reporting_refs=snapshot.published_reporting_refs | reporting_refs,
        accounting_event_ids=event_ids,
        consumed_effect_keys=(
            snapshot.consumed_effect_keys
            | ({outcome.effect_key} if outcome.effect_key else set())
        ),
    )
