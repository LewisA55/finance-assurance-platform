"""Runtime-owned parameterised C-001 and CT-1 accounting application service."""

from __future__ import annotations

from dataclasses import dataclass, replace

from pydantic import BaseModel

from finance_assurance.runtime.application.contracts import ModuleContractService
from finance_assurance.runtime.application.models import (
    AccountingWorkflow,
    IdentityGeneratorPort,
    ProposalTreatmentVersion,
)
from finance_assurance.runtime.application.publications import (
    AtlasPublicationClosureError,
    materialize_atlas_publications,
    required_atlas_publications,
    validate_atlas_publication_closure,
)
from finance_assurance.runtime.contracts.events import (
    JournalPosted,
    PeriodHardClosed,
    ProposalApproved,
    ProposalDeferred,
    ProposalSubmitted,
    ReportingVersionPublished,
    RestatementAdjustmentLinked,
    RestatementAdjustmentsReady,
    RestatementApproved,
    RestatementProposed,
)
from finance_assurance.runtime.contracts.module import ContractPublication
from finance_assurance.runtime.contracts.objects import (
    JournalEntryBase,
    JournalLine,
    ReportingVersion,
)
from finance_assurance.runtime.execution import DispatchOutcome, execute
from finance_assurance.runtime.persistence.models import QueryContext
from finance_assurance.runtime.persistence.ports import PersistenceBoundary
from finance_assurance.runtime.persistence.state import InMemoryState
from finance_assurance.runtime.planner import (
    ApproveProposal,
    ApproveRestatement,
    ConstructCorrectionProposal,
    DeferProposal,
    EvaluatePostingRule,
    FreezeRestatementManifest,
    HardClosePeriod,
    LinkRestatementAdjustment,
    PostProposal,
    ProposeRestatement,
    PublishRestatement,
    SubmitProposal,
    TransitionPlan,
)


@dataclass(frozen=True, slots=True)
class WorkflowExecution:
    family: str
    correlation_id: str
    outcomes: tuple[DispatchOutcome, ...]
    constructor_command_ids: tuple[str, ...]
    terminal_state: InMemoryState


@dataclass(frozen=True, slots=True)
class ExactProposalResult:
    treatment: ProposalTreatmentVersion
    status: str


class AccountingApplicationService:
    """Execute only the finite Artifact I accounting paths through one boundary."""

    def __init__(
        self,
        boundary: PersistenceBoundary,
        identities: IdentityGeneratorPort,
        contracts: ModuleContractService | None = None,
    ) -> None:
        self._boundary = boundary
        self._identities = identities
        self._contracts = contracts or ModuleContractService(boundary)

    def execute_workflow(self, workflow: AccountingWorkflow) -> WorkflowExecution:
        return self.execute_segment(workflow, start=0, stop=None)

    def execute_segment(
        self,
        workflow: AccountingWorkflow,
        *,
        start: int,
        stop: int | None,
    ) -> WorkflowExecution:
        """Execute a contiguous segment of one already validated workflow."""

        event_count = len(workflow.event_templates)
        if (
            start < 0
            or start >= event_count
            or (stop is not None and (stop <= start or stop > event_count))
        ):
            raise ValueError("workflow segment bounds are invalid")
        creations = {
            item.template_event_id: item.values for item in workflow.creations
        }
        treatment_by_ref = {item.proposal_ref: item for item in workflow.treatments}
        submitted_at_by_ref = {
            str(item.subject_ref.object_ref): str(item.occurred_at)
            for item in workflow.event_templates
            if isinstance(item, ProposalSubmitted)
        }
        outcomes: list[DispatchOutcome] = []
        constructors: list[str] = []

        for event in workflow.event_templates[start:stop]:
            event_bundle = next(
                (
                    item
                    for item in workflow.creations
                    if item.template_event_id == str(event.event_id)
                ),
                None,
            )
            proposal_ref = getattr(event.subject_ref, "object_ref", "")
            if isinstance(event, ProposalSubmitted):
                treatment = treatment_by_ref[str(proposal_ref)]
                if self._boundary.state.snapshot.proposal(str(proposal_ref)) is None:
                    command_id = self._identities.next_identity("constructor_command")
                    constructors.append(command_id)
                    if treatment.origin_type == "AUTOMATED_POSTING":
                        if workflow.business_event is None:
                            raise ValueError(
                                "automated posting requires a business event"
                            )
                        command = EvaluatePostingRule(
                            command_id=command_id,
                            input_id=workflow.business_event.business_event_id,
                            proposal_ref=treatment.proposal_ref,
                            target_period_id=treatment.target_period_id,
                            account_ids=treatment.account_ids,
                            input_hashes=treatment.input_hashes,
                            immutable_creations=(treatment,),
                        )
                    else:
                        if treatment.origin_type == "REVERSAL":
                            source_journal_id = str(
                                treatment.origin_basis.reverses_journal_id
                            )
                            source = self._boundary.state.snapshot.referenced_journal(
                                source_journal_id
                            )
                            if (
                                source is None
                                or not treatment.input_hashes
                                or source.source_hash != treatment.input_hashes[0]
                            ):
                                raise ValueError(
                                    "reversal source hash must bind before construction"
                                )
                        command = ConstructCorrectionProposal(
                            command_id=command_id,
                            proposal_ref=treatment.proposal_ref,
                            target_period_id=treatment.target_period_id,
                            origin_type=treatment.origin_type,
                            account_ids=treatment.account_ids,
                            input_hashes=treatment.input_hashes,
                            immutable_creations=(treatment,),
                        )
                    constructor = execute(self._boundary, command)
                    if not isinstance(constructor.result, TransitionPlan):
                        raise RuntimeError(
                            f"workflow constructor rejected: {command_id}"
                        )
                    outcomes.append(constructor)
                command = SubmitProposal(
                    command_id=str(event.command_id),
                    proposal_ref=str(proposal_ref),
                    accounting_event=event,
                )
            elif isinstance(event, ProposalDeferred):
                command = DeferProposal(
                    command_id=str(event.command_id),
                    proposal_ref=str(proposal_ref),
                    accounting_event=event,
                )
            elif isinstance(event, PeriodHardClosed):
                command = HardClosePeriod(
                    command_id=str(event.command_id),
                    period_id=str(proposal_ref),
                    accounting_event=event,
                    unresolved_submitted_count=0,
                    unresolved_approved_count=0,
                )
            elif isinstance(event, RestatementProposed):
                command = ProposeRestatement(
                    command_id=str(event.command_id),
                    case_id=str(proposal_ref),
                    scope_period_ids=frozenset(event.basis.scope_period_ids),
                    accounting_event=event,
                )
            elif isinstance(event, ProposalApproved):
                treatment = treatment_by_ref[str(proposal_ref)]
                command = ApproveProposal(
                    command_id=str(event.command_id),
                    proposal_ref=str(proposal_ref),
                    approver_id=str(event.actor.actor_id),
                    preparer_id=str(treatment.prepared_by.actor_id),
                    accounting_event=event,
                )
            elif isinstance(event, JournalPosted):
                event_creations = creations.get(str(event.event_id), ())
                journals = tuple(
                    item
                    for item in event_creations
                    if isinstance(item, JournalEntryBase)
                )
                if len(journals) != 1 or not any(
                    isinstance(item, JournalLine) for item in event_creations
                ):
                    raise ValueError("journal.posted requires one header and its lines")
                journal = journals[0]
                basis = journal.correction_basis
                command = PostProposal(
                    command_id=str(event.command_id),
                    proposal_ref=str(proposal_ref),
                    effect_key=str(event.idempotency_key),
                    entry_class=event.payload.entry_class,
                    reverses_journal_id=getattr(basis, "reverses_journal_id", None),
                    corrects_journal_id=getattr(basis, "corrects_journal_id", None),
                    restatement_case_id=getattr(basis, "restatement_case_id", None),
                    accounting_event=event,
                    immutable_creations=event_creations,
                )
            elif isinstance(event, RestatementAdjustmentLinked):
                command = LinkRestatementAdjustment(
                    command_id=str(event.command_id),
                    case_id=str(proposal_ref),
                    journal_id=str(event.payload.journal_id),
                    entry_class=event.basis.entry_class,
                    journal_case_id=str(proposal_ref),
                    accounting_event=event,
                )
            elif isinstance(event, RestatementAdjustmentsReady):
                current = self._boundary.state.snapshot.restatement(str(proposal_ref))
                if current is None:
                    raise ValueError("restatement manifest requires an existing case")
                command = FreezeRestatementManifest(
                    command_id=str(event.command_id),
                    case_id=str(proposal_ref),
                    linked_journal_ids=frozenset(event.basis.linked_journal_ids),
                    presented_period_ids=current.scope_period_ids,
                    manifest_hash=str(event.basis.manifest_hash),
                    accounting_event=event,
                    immutable_creations=creations.get(str(event.event_id), ()),
                )
            elif isinstance(event, RestatementApproved):
                command = ApproveRestatement(
                    command_id=str(event.command_id),
                    case_id=str(proposal_ref),
                    accounting_event=event,
                )
            elif isinstance(event, ReportingVersionPublished):
                event_creations = creations.get(str(event.event_id), ())
                if not any(
                    isinstance(item, ReportingVersion) for item in event_creations
                ):
                    raise ValueError("publication requires one reporting version")
                command = PublishRestatement(
                    command_id=str(event.command_id),
                    case_id=str(proposal_ref),
                    predecessor_version_ref=str(event.basis.predecessor_version_ref),
                    manifest_hash=str(event.basis.manifest_hash),
                    content_ref=str(event.basis.content_ref),
                    effect_key=str(event.idempotency_key),
                    accounting_event=event,
                    immutable_creations=event_creations,
                )
            else:  # pragma: no cover - closed union plus workflow sequence guards
                raise TypeError(f"undeclared accounting event: {type(event).__name__}")
            if event_bundle is not None:
                if any(
                    isinstance(item, ContractPublication)
                    for item in event_bundle.values
                ):
                    raise AtlasPublicationClosureError(
                        "accounting publication closure is owned by the command service"
                    )
                additions = tuple(
                    item
                    for item in event_bundle.values
                    if item not in command.immutable_creations
                )
                command = replace(
                    command,
                    immutable_creations=(*command.immutable_creations, *additions),
                )
            event_treatment = treatment_by_ref.get(str(proposal_ref))
            requirements = required_atlas_publications(
                event,
                treatment=event_treatment,
                submitted_at=submitted_at_by_ref.get(str(proposal_ref)),
                authoritative_creations=command.immutable_creations,
            )
            publications = validate_atlas_publication_closure(
                requirements,
                materialize_atlas_publications(event, requirements),
            )
            command = replace(
                command,
                immutable_creations=(*command.immutable_creations, *publications),
            )
            consumed_publication_refs = (
                event_bundle.consumed_publication_refs
                if event_bundle is not None
                else ()
            )
            self._contracts.validate_transition(
                command_id=command.command_id,
                actor_ref=str(event.actor.actor_id),
                correlation_id=str(event.correlation_id),
                semantic_as_of_time=str(event.recorded_at),
                publications=publications,
                consumed_publication_refs=consumed_publication_refs,
            )
            outcome = execute(self._boundary, command)
            if not outcome.committed or not isinstance(outcome.result, TransitionPlan):
                raise RuntimeError(
                    f"workflow command did not commit: {event.command_id}"
                )
            outcomes.append(outcome)
            self._contracts.observe_transition(
                command_id=command.command_id,
                actor_ref=str(event.actor.actor_id),
                correlation_id=str(event.correlation_id),
                semantic_as_of_time=str(event.recorded_at),
                publications=publications,
                consumed_publication_refs=consumed_publication_refs,
            )

        return WorkflowExecution(
            family=workflow.family,
            correlation_id=workflow.correlation_id,
            outcomes=tuple(outcomes),
            constructor_command_ids=tuple(constructors),
            terminal_state=self._boundary.state,
        )

    def get_exact_proposal(
        self,
        proposal_ref: str,
        *,
        semantic_as_of_time: str,
    ) -> ExactProposalResult | None:
        """Return one exact J-AR05 treatment with its labelled current projection."""

        query = self._boundary.open_query(
            QueryContext(semantic_as_of_time=semantic_as_of_time)
        )
        state = query.state()
        treatment = next(
            (
                item
                for item in state.object_versions
                if isinstance(item, ProposalTreatmentVersion)
                and item.proposal_ref == proposal_ref
            ),
            None,
        )
        projection = state.snapshot.proposal(proposal_ref)
        if treatment is None or projection is None:
            return None
        return ExactProposalResult(treatment=treatment, status=projection.status)

    def accounting_event(
        self,
        event_id: str,
        *,
        semantic_as_of_time: str,
    ) -> BaseModel | None:
        query = self._boundary.open_query(
            QueryContext(semantic_as_of_time=semantic_as_of_time)
        )
        return next(
            (
                item
                for item in query.state().event_log
                if str(item.event_id) == event_id
            ),
            None,
        )
