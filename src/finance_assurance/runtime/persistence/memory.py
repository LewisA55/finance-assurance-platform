"""Transactional in-memory adapter conforming to the Artifact K command port."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock

from pydantic import BaseModel

from finance_assurance.runtime.application.models import (
    CandidateReceipt,
    ProposalTreatmentVersion,
)
from finance_assurance.runtime.contracts.events import AccountingEventBase
from finance_assurance.runtime.contracts.evidence import ReportingContentRecord
from finance_assurance.runtime.contracts.module import (
    ContractPublication,
    ValidatedModuleProduct,
)
from finance_assurance.runtime.contracts.objects import (
    AccountingPeriodBase,
    BusinessEvent,
    JournalEntryBase,
    PostingRule,
)
from finance_assurance.runtime.contracts.primitives import EvidenceRef
from finance_assurance.runtime.digests import value_digest
from finance_assurance.runtime.persistence.codec import encode_durable
from finance_assurance.runtime.persistence.models import (
    AcceptedCommitPlan,
    AuthoritativeRef,
    CommandContext,
    CommandIdentityConflict,
    CommandResult,
    CommitReceipt,
    ExactCommandResult,
    ExactConflictSnapshot,
    ExactStoredRecord,
    ModuleCommandOutcome,
    QueryContext,
    StagedRejectionSet,
    StagedWriteSet,
    StateExpectation,
    ValidatedAcceptedPlan,
    ValidatedRejectionPlan,
)
from finance_assurance.runtime.persistence.projection import replay_transition
from finance_assurance.runtime.persistence.semantic_time import (
    BASELINE_AVAILABLE_FROM,
    is_available,
)
from finance_assurance.runtime.persistence.state import InMemoryState, split_creations
from finance_assurance.runtime.planner import StateSnapshot, TransitionPlan
from finance_assurance.runtime.rejections import Rejection


class InvariantFailure(RuntimeError):
    """Raised when staged records violate an Artifact K commit invariant."""


class UnitOfWorkClosed(RuntimeError):
    """Raised when a closed unit of work is reused."""


class InMemoryReadFacets:
    """Stable read view captured when a command unit opens."""

    def __init__(self, state: InMemoryState) -> None:
        self._state = state

    def snapshot(self) -> StateSnapshot:
        return self._state.snapshot


def _explicit_available_from(value: object, fallback: str) -> str:
    candidate = getattr(value, "available_from", None)
    return str(candidate) if candidate is not None else fallback


def _record_availability(
    state: InMemoryState,
    contexts: dict[str, CommandContext],
) -> dict[tuple[str, str], str]:
    availability: dict[tuple[str, str], str] = {}
    for result in state.command_results:
        context = contexts.get(result.command_id)
        if context is None:
            continue
        fallback = context.semantic_as_of_time
        availability[("J-AR14", result.command_id)] = fallback
        outcome = result.outcome
        if isinstance(outcome, TransitionPlan):
            if outcome.accounting_event is not None:
                event = outcome.accounting_event
                availability[("J-AR06", _record_identity(event))] = (
                    _explicit_available_from(event, fallback)
                )
            creations = outcome.immutable_creations
        elif isinstance(outcome, ModuleCommandOutcome):
            creations = outcome.immutable_creations
        else:
            creations = ()
        for value in creations:
            family = authoritative_family(value)
            identity = _record_identity(value)
            availability[(family, identity)] = _explicit_available_from(
                value, fallback
            )
    for disposition in state.dispositions:
        context = contexts.get(disposition.command_id)
        if context is not None:
            availability[("J-AR16", disposition.command_id)] = (
                context.semantic_as_of_time
            )
    for effect in state.effect_registry:
        context = contexts.get(effect.command_id)
        if context is not None:
            availability[("J-AR15", effect.idempotency_key)] = (
                context.semantic_as_of_time
            )
    return availability


def _state_exact_records(
    state: InMemoryState,
    contexts: dict[str, CommandContext] | None = None,
) -> tuple[ExactStoredRecord, ...]:
    values: list[tuple[str, str, object]] = []
    for collection in (
        state.object_versions,
        state.event_log,
        state.journal_store,
        state.reporting_version_store,
    ):
        values.extend(
            (authoritative_family(value), _record_identity(value), value)
            for value in collection
        )
    values.extend(("J-AR14", item.command_id, item) for item in state.command_results)
    values.extend(("J-AR16", item.command_id, item) for item in state.dispositions)
    values.extend(
        ("J-AR15", item.idempotency_key, item) for item in state.effect_registry
    )

    availability = _record_availability(state, contexts or {})
    records: dict[tuple[str, str], ExactStoredRecord] = {}
    for family, identity, value in values:
        key = (family, identity)
        candidate = ExactStoredRecord(
            record_family=family,
            record_identity=identity,
            semantic_hash=value_digest(value),
            canonical_payload=encode_durable(value),
            available_from=_explicit_available_from(
                value,
                availability.get(key, BASELINE_AVAILABLE_FROM),
            ),
        )
        prior = records.get(key)
        if prior is not None and prior.semantic_hash != candidate.semantic_hash:
            raise InvariantFailure("authoritative identity resolves to multiple hashes")
        records[key] = candidate
    return tuple(records[key] for key in sorted(records))


def _visible_state(
    state: InMemoryState,
    records: tuple[ExactStoredRecord, ...],
    *,
    baseline_snapshot: StateSnapshot,
    baseline_command_ids: frozenset[str],
) -> InMemoryState:
    visible = {(item.record_family, item.record_identity) for item in records}

    def visible_values(values: tuple[BaseModel, ...]) -> tuple[BaseModel, ...]:
        return tuple(
            value
            for value in values
            if (authoritative_family(value), _record_identity(value)) in visible
        )

    command_results = tuple(
        item
        for item in state.command_results
        if ("J-AR14", item.command_id) in visible
    )
    snapshot = baseline_snapshot
    for result in command_results:
        if result.command_id in baseline_command_ids or result.status != "ACCEPTED":
            continue
        if isinstance(result.outcome, TransitionPlan):
            snapshot = replay_transition(snapshot, result.outcome)
    return replace(
        state,
        snapshot=snapshot,
        object_versions=visible_values(state.object_versions),
        event_log=visible_values(state.event_log),
        journal_store=visible_values(state.journal_store),
        reporting_version_store=tuple(
            value
            for value in state.reporting_version_store
            if (authoritative_family(value), _record_identity(value)) in visible
        ),
        effect_registry=tuple(
            item
            for item in state.effect_registry
            if ("J-AR15", item.idempotency_key) in visible
        ),
        command_results=command_results,
        dispositions=tuple(
            item
            for item in state.dispositions
            if ("J-AR16", item.command_id) in visible
        ),
    )


class InMemoryQuerySession:
    """Pinned, read-only Artifact K query session for the memory adapter."""

    def __init__(
        self,
        state: InMemoryState,
        revision: int,
        context: QueryContext,
        contexts: dict[str, CommandContext],
        baseline_snapshot: StateSnapshot,
        baseline_available_from: str,
        baseline_command_ids: frozenset[str],
    ) -> None:
        self._revision = revision
        self._records = tuple(
            item
            for item in _state_exact_records(state, contexts)
            if is_available(item.available_from, context.semantic_as_of_time)
        )
        self._state = _visible_state(
            state,
            self._records,
            baseline_snapshot=(
                baseline_snapshot
                if is_available(
                    baseline_available_from, context.semantic_as_of_time
                )
                else StateSnapshot()
            ),
            baseline_command_ids=baseline_command_ids,
        )

    @property
    def revision(self) -> int:
        return self._revision

    def state(self) -> InMemoryState:
        return self._state

    def command_result(self, command_id: str) -> CommandResult | None:
        return self._state.command_result(command_id)

    def authoritative_record(
        self, record_family: str, record_identity: str
    ) -> ExactStoredRecord | None:
        return next(
            (
                item
                for item in self.authoritative_records(record_family)
                if item.record_identity == record_identity
            ),
            None,
        )

    def authoritative_records(
        self, record_family: str | None = None
    ) -> tuple[ExactStoredRecord, ...]:
        records = self._records
        if record_family is None:
            return records
        return tuple(item for item in records if item.record_family == record_family)


def _state_token(snapshot: StateSnapshot, expectation: StateExpectation) -> str:
    if expectation.subject_type == "journal_proposal":
        value = snapshot.proposal(expectation.subject_ref)
        return value.status if value is not None else "ABSENT"
    if expectation.subject_type == "accounting_period":
        value = snapshot.period(expectation.subject_ref)
        return value.status if value is not None else "ABSENT"
    if expectation.subject_type == "restatement_case":
        value = snapshot.restatement(expectation.subject_ref)
        return value.status if value is not None else "ABSENT"
    if expectation.subject_type == "posting_rule":
        return (
            "CONSUMED"
            if expectation.subject_ref in snapshot.business_event_ids
            else "ABSENT"
        )
    raise InvariantFailure(
        f"unknown state-expectation subject: {expectation.subject_type}"
    )


def _record_identity(value: BaseModel) -> str:
    if isinstance(value, EvidenceRef):
        return str(value.ref_id)
    if isinstance(value, ReportingContentRecord):
        return str(value.content_ref)
    for field in (
        "publication_ref",
        "candidate_receipt_ref",
        "product_ref",
        "business_event_id",
        "posting_rule_ref",
        "event_id",
        "journal_line_id",
        "journal_id",
        "reporting_version_ref",
        "proposal_ref",
        "case_id",
        "period_id",
    ):
        candidate = getattr(value, field, None)
        if candidate is not None:
            return str(candidate)
    return value_digest(value)


def authoritative_family(value: BaseModel) -> str:
    """Return the ratified Artifact J family for one ordinary command output."""

    if isinstance(value, CandidateReceipt):
        return "J-AR01"
    if isinstance(value, ProposalTreatmentVersion):
        return "J-AR05"
    if isinstance(value, ContractPublication):
        return "J-AR13"
    if isinstance(value, ValidatedModuleProduct):
        return "J-AR02"
    if isinstance(value, BusinessEvent):
        return "J-AR03"
    if isinstance(value, PostingRule):
        return "J-AR04"
    if isinstance(value, AccountingEventBase):
        return "J-AR06"
    if isinstance(value, AccountingPeriodBase):
        return "J-AR07"
    if isinstance(value, ReportingContentRecord):
        return "J-AR12"
    if isinstance(value, EvidenceRef):
        return "J-AR12"
    if isinstance(value, EvidenceRef):
        return "J-AR12"
    if isinstance(value, JournalEntryBase) or hasattr(value, "journal_line_id"):
        return "J-AR08"
    if hasattr(value, "reporting_version_ref"):
        return "J-AR10"
    return "J-AR02"


def _authoritative_ref(family: str, identity: str, value: object) -> AuthoritativeRef:
    return AuthoritativeRef(
        record_family=family,
        record_identity=identity,
        semantic_hash=value_digest(value),
    )


def _materialize_accepted(
    state: InMemoryState,
    write_set: StagedWriteSet,
) -> InMemoryState:
    return replace(
        state,
        snapshot=write_set.projection_replacement,
        object_versions=(*state.object_versions, *write_set.object_appends),
        event_log=(*state.event_log, *write_set.accounting_event_appends),
        journal_store=(*state.journal_store, *write_set.journal_appends),
        reporting_version_store=(
            *state.reporting_version_store,
            *write_set.reporting_version_appends,
        ),
        effect_registry=(*state.effect_registry, *write_set.effect_claims),
        command_results=(*state.command_results, write_set.command_result),
        dispositions=(*state.dispositions, *write_set.dispositions),
    )


def _materialize_rejection(
    state: InMemoryState,
    write_set: StagedRejectionSet,
) -> InMemoryState:
    return replace(
        state,
        object_versions=(*state.object_versions, *write_set.object_appends),
        command_results=(*state.command_results, write_set.command_result),
        dispositions=(*state.dispositions, *write_set.dispositions),
    )


def _validate_prepared(previous: InMemoryState, prepared: InMemoryState) -> None:
    event_ids = [str(event.event_id) for event in prepared.event_log]
    if len(event_ids) != len(set(event_ids)):
        raise InvariantFailure("accounting-event IDs must be unique")
    event_commands = [str(event.command_id) for event in prepared.event_log]
    if len(event_commands) != len(set(event_commands)):
        raise InvariantFailure("one accounting event is permitted per command")
    command_ids = [item.command_id for item in prepared.command_results]
    if len(command_ids) != len(set(command_ids)):
        raise InvariantFailure("command-result registry must be unique by command_id")
    effect_keys = [item.idempotency_key for item in prepared.effect_registry]
    if len(effect_keys) != len(set(effect_keys)):
        raise InvariantFailure("effect registry must be unique by idempotency_key")
    if set(effect_keys) != set(prepared.snapshot.consumed_effect_keys):
        raise InvariantFailure("effect registry and planner effect index must agree")
    disposition_commands = [item.command_id for item in prepared.dispositions]
    if len(disposition_commands) != len(set(disposition_commands)):
        raise InvariantFailure("G-14 disposition must be unique by command_id")
    if prepared.referenced_state != prepared.snapshot.referenced_journals:
        raise InvariantFailure("non-authored referenced state must remain synchronized")

    journal_ids = [
        item.journal_id
        for item in prepared.journal_store
        if isinstance(item, JournalEntryBase)
    ]
    if len(journal_ids) != len(set(journal_ids)):
        raise InvariantFailure("posted journals are immutable and unique by journal_id")
    line_ids = [
        item.journal_line_id
        for item in prepared.journal_store
        if hasattr(item, "journal_line_id")
    ]
    if len(line_ids) != len(set(line_ids)):
        raise InvariantFailure("journal lines are immutable and unique by identity")
    reporting_refs = [
        item.reporting_version_ref for item in prepared.reporting_version_store
    ]
    if len(reporting_refs) != len(set(reporting_refs)):
        raise InvariantFailure("reporting versions are immutable and unique by ref")
    publication_refs = [
        str(item.publication_ref)
        for item in prepared.object_versions
        if isinstance(item, ContractPublication)
    ]
    if len(publication_refs) != len(set(publication_refs)):
        raise InvariantFailure("contract publications are immutable and unique")
    product_refs = [
        item.product_ref
        for item in prepared.object_versions
        if isinstance(item, ValidatedModuleProduct)
    ]
    if len(product_refs) != len(set(product_refs)):
        raise InvariantFailure("module-product versions are immutable and unique")
    publication_refs = [
        str(item.publication_ref)
        for item in prepared.object_versions
        if isinstance(item, ContractPublication)
    ]
    if len(publication_refs) != len(set(publication_refs)):
        raise InvariantFailure("contract publications are immutable and unique")
    product_refs = [
        item.product_ref
        for item in prepared.object_versions
        if isinstance(item, ValidatedModuleProduct)
    ]
    if len(product_refs) != len(set(product_refs)):
        raise InvariantFailure("module-product versions are immutable and unique")
    receipt_refs = [
        str(item.candidate_receipt_ref)
        for item in prepared.object_versions
        if isinstance(item, CandidateReceipt)
    ]
    if len(receipt_refs) != len(set(receipt_refs)):
        raise InvariantFailure("candidate receipts are immutable and unique")
    receipts = {
        str(item.candidate_receipt_ref): item
        for item in prepared.object_versions
        if isinstance(item, CandidateReceipt)
    }
    admission_products = {
        item.product_ref: item
        for item in prepared.object_versions
        if isinstance(item, ValidatedModuleProduct)
        and item.product_discriminator
        == "hermes.business_event_admission_result"
    }
    g02_values = tuple(
        item
        for item in prepared.object_versions
        if isinstance(item, ContractPublication) and item.contract_id == "G-02"
    )
    g02_publications = {
        item.product_ref: item
        for item in g02_values
    }
    if len(g02_publications) != len(g02_values):
        raise InvariantFailure("one G-02 publication is permitted per admission")
    for product_ref, product in admission_products.items():
        body = product.canonical_body
        receipt = receipts.get(str(body.get("candidate_receipt_ref", "")))
        publication = g02_publications.get(product_ref)
        if receipt is None or publication is None:
            raise InvariantFailure(
                "candidate admission requires exact receipt and G-02 publication"
            )
        if (
            body.get("candidate_type") != receipt.candidate_type
            or body.get("candidate_payload_hash") != receipt.candidate_payload_hash
            or body.get("source_domain_ref") != receipt.source_domain_ref
            or body.get("source_record_ref") != receipt.source_record_ref
            or publication.canonical_payload != body
        ):
            raise InvariantFailure("candidate admission binding is inconsistent")
    if set(receipts) != {
        str(item.canonical_body["candidate_receipt_ref"])
        for item in admission_products.values()
    }:
        raise InvariantFailure("candidate custody lacks one exact admission result")

    events = {
        str(item.business_event_id): item
        for item in prepared.object_versions
        if isinstance(item, BusinessEvent)
    }
    publications = {
        str(item.publication_ref): item
        for item in prepared.object_versions
        if isinstance(item, ContractPublication)
    }
    for publication in publications.values():
        if publication.contract_id != "G-01":
            continue
        if len(publication.upstream_publication_refs) != 1:
            raise InvariantFailure("G-01 requires one exact G-02 publication")
        admission = publications.get(str(publication.upstream_publication_refs[0]))
        event = events.get(str(publication.product_ref))
        if (
            admission is None
            or admission.contract_id != "G-02"
            or admission.canonical_payload.get("outcome") != "ACCEPTED"
            or event is None
        ):
            raise InvariantFailure("G-01 crossed an unaccepted admission boundary")
        receipt = receipts.get(
            str(admission.canonical_payload.get("candidate_receipt_ref", ""))
        )
        if (
            receipt is None
            or receipt.candidate_payload_hash
            != value_digest(event.model_dump(mode="json"))
            or publication.canonical_payload != event.model_dump(mode="json")
        ):
            raise InvariantFailure("G-01 bytes do not bind exact candidate custody")

    prior_event_ids = {
        str(event.event_id) for event in previous.event_log
    } | previous.known_predecessor_event_ids
    for event in prepared.event_log[len(previous.event_log) :]:
        cause = event.causation_event_id
        if cause is not None and str(cause) not in prior_event_ids:
            raise InvariantFailure("accounting-event causation must reference prior state")
        prior_event_ids.add(str(event.event_id))


class InMemoryCommandUnitOfWork:
    """One state-isolated command attempt against an in-memory boundary."""

    def __init__(
        self,
        boundary: InMemoryPersistenceBoundary,
        context: CommandContext,
        state: InMemoryState,
        revision: int,
    ) -> None:
        self._boundary = boundary
        self._context = context
        self._base_state = state
        self._base_revision = revision
        self._reads = InMemoryReadFacets(state)
        self._token = object()
        self._staged: StagedWriteSet | StagedRejectionSet | None = None
        self._validated: ValidatedAcceptedPlan | ValidatedRejectionPlan | None = None
        self._arbitrated_revision: int | None = None
        self._conflict: ExactConflictSnapshot | None = None
        self._arbitration_lock_held = False
        self._closed = False

    def _ensure_open(self) -> None:
        if self._closed:
            raise UnitOfWorkClosed("unit of work is closed")

    def context(self) -> CommandContext:
        return self._context

    def prior_result(self) -> ExactCommandResult | None:
        self._ensure_open()
        result = self._base_state.command_result(self._context.command_id)
        if result is None:
            return None
        stored = self._boundary._contexts.get(self._context.command_id)
        if stored is None:
            stored = replace(self._context, input_digest=result.command_fingerprint)
        return ExactCommandResult(context=stored, result=result)

    def records(self) -> InMemoryReadFacets:
        self._ensure_open()
        return self._reads

    def stage_accepted(self, write_set: StagedWriteSet) -> None:
        self._ensure_open()
        if self._staged is not None:
            raise InvariantFailure("a unit of work permits one initial staged set")
        self._staged = write_set

    def stage_rejection(self, write_set: StagedRejectionSet) -> None:
        self._ensure_open()
        if self._staged is not None:
            raise InvariantFailure("a unit of work permits one initial staged set")
        self._staged = write_set

    def validate(self) -> ValidatedAcceptedPlan | ValidatedRejectionPlan:
        self._ensure_open()
        if self._staged is None:
            raise InvariantFailure("nothing is staged")
        if self._staged.command_result.command_id != self._context.command_id:
            raise InvariantFailure("command closure identity does not match context")
        if self._staged.command_result.command_fingerprint != self._context.input_digest:
            raise InvariantFailure("command closure digest does not match context")
        if isinstance(self._staged, StagedWriteSet):
            if self._staged.command_result.status != "ACCEPTED":
                raise InvariantFailure("accepted write set requires accepted closure")
            outcome = self._staged.command_result.outcome
            if not isinstance(outcome, (TransitionPlan, ModuleCommandOutcome)):
                raise InvariantFailure(
                    "accepted closure requires a transition or module outcome"
                )
            objects, journals, reporting = split_creations(
                outcome.immutable_creations
            )

            events = (
                (outcome.accounting_event,)
                if isinstance(outcome, TransitionPlan)
                and outcome.accounting_event is not None
                else ()
            )
            if (
                self._staged.object_appends != objects
                or self._staged.journal_appends != journals
                or self._staged.reporting_version_appends != reporting
                or self._staged.accounting_event_appends != events
            ):
                raise InvariantFailure(
                    "accepted command closure does not match transition outputs"
                )
            effect_keys = tuple(
                item.idempotency_key for item in self._staged.effect_claims
            )
            expected_effect_keys = (
                (outcome.effect_key,)
                if isinstance(outcome, TransitionPlan)
                and outcome.effect_key is not None
                else ()
            )
            if effect_keys != expected_effect_keys:
                raise InvariantFailure(
                    "accepted command closure does not match transition effect"
                )
            prepared = _materialize_accepted(self._base_state, self._staged)
            _validate_prepared(self._base_state, prepared)
            plan: ValidatedAcceptedPlan | ValidatedRejectionPlan = (
                ValidatedAcceptedPlan(self._token, self._staged)
            )
        else:
            if self._staged.command_result.status != "REJECTED":
                raise InvariantFailure("rejection write set requires rejected closure")
            if not isinstance(self._staged.command_result.outcome, Rejection):
                raise InvariantFailure("rejection closure requires a rejection")
            if self._staged.object_appends:
                if (
                    len(self._staged.object_appends) != 1
                    or len(self._staged.dispositions) != 1
                    or not isinstance(
                        self._staged.object_appends[0],
                        ContractPublication,
                    )
                ):
                    raise InvariantFailure(
                        "rejection object closure permits one G-14 publication"
                    )
                publication = self._staged.object_appends[0]
                disposition = self._staged.dispositions[0]
                if (
                    publication.contract_id != "G-14"
                    or publication.canonical_payload.get("command_id")
                    != self._context.command_id
                    or disposition.command_id != self._context.command_id
                ):
                    raise InvariantFailure(
                        "G-14 publication does not bind its rejected command"
                    )
            prepared = _materialize_rejection(self._base_state, self._staged)
            _validate_prepared(self._base_state, prepared)
            plan = ValidatedRejectionPlan(self._token, self._staged)
        self._validated = plan
        return plan

    def arbitrate(
        self,
        plan: ValidatedAcceptedPlan,
    ) -> AcceptedCommitPlan | ExactConflictSnapshot | ExactCommandResult | CommandIdentityConflict:
        self._ensure_open()
        if plan is not self._validated or plan.unit_token is not self._token:
            raise InvariantFailure("accepted plan was not validated by this unit")
        self._boundary._lock.acquire()
        self._arbitration_lock_held = True
        try:
            current = self._boundary._state
            prior = current.command_result(self._context.command_id)
            if prior is not None:
                stored = self._boundary._contexts.get(self._context.command_id)
                if stored is None:
                    stored = replace(self._context, input_digest=prior.command_fingerprint)
                exact = ExactCommandResult(stored, prior)
                if stored.retry_identity == self._context.retry_identity:
                    return exact
                return CommandIdentityConflict(
                    command_id=self._context.command_id,
                    expected_input_digest=stored.input_digest,
                    supplied_input_digest=self._context.input_digest,
                )
            for expectation in plan.write_set.expected_state_tokens:
                observed = _state_token(current.snapshot, expectation)
                if observed != expectation.expected_state_token:
                    snapshot = ExactConflictSnapshot(
                        conflict_class="STALE_STATE",
                        subject_or_effect_key=expectation.subject_ref,
                        expected_authoritative_ref=expectation.expected_state_token,
                        observed_authoritative_ref=observed,
                        observed_semantic_hash=value_digest(observed),
                    )
                    self._conflict = snapshot
                    return snapshot
            for effect in plan.write_set.effect_claims:
                observed = current.effect(effect.idempotency_key)
                if observed is not None:
                    snapshot = ExactConflictSnapshot(
                        conflict_class="EFFECT_CONSUMED",
                        subject_or_effect_key=effect.idempotency_key,
                        expected_authoritative_ref=None,
                        observed_authoritative_ref=observed.event_id,
                        observed_semantic_hash=value_digest(observed),
                    )
                    self._conflict = snapshot
                    return snapshot
            self._arbitrated_revision = self._boundary._revision
            return AcceptedCommitPlan(
                unit_token=self._token,
                write_set=plan.write_set,
                revision=self._boundary._revision,
            )
        except BaseException:
            self._boundary._lock.release()
            self._arbitration_lock_held = False
            raise

    def replace_with_conflict_rejection(
        self,
        snapshot: ExactConflictSnapshot,
        write_set: StagedRejectionSet,
    ) -> None:
        self._ensure_open()
        if snapshot is not self._conflict:
            raise InvariantFailure("conflict snapshot was not issued by this unit")
        self._staged = write_set
        self._validated = None

    def commit(
        self,
        plan: AcceptedCommitPlan | ValidatedRejectionPlan,
    ) -> CommitReceipt:
        self._ensure_open()
        if plan.unit_token is not self._token:
            raise InvariantFailure("commit plan belongs to another unit")
        acquired_for_commit = False
        if not self._arbitration_lock_held:
            self._boundary._lock.acquire()
            acquired_for_commit = True
        try:
            if isinstance(plan, AcceptedCommitPlan):
                if plan.revision != self._boundary._revision:
                    raise InvariantFailure("accepted plan lost its arbitrated revision")
                prepared = _materialize_accepted(self._boundary._state, plan.write_set)
                write_set = plan.write_set
                outcome = "ACCEPTED"
            else:
                if plan is not self._validated:
                    raise InvariantFailure("rejection plan was not validated by this unit")
                prepared = _materialize_rejection(
                    self._boundary._state,
                    plan.write_set,
                )
                write_set = plan.write_set
                outcome = "REJECTED"
            _validate_prepared(self._boundary._state, prepared)
            self._boundary._commit_prepared(
                previous=self._boundary._state,
                prepared=prepared,
                context=self._context,
            )
            self._closed = True
        finally:
            if self._arbitration_lock_held or acquired_for_commit:
                self._boundary._lock.release()
            self._arbitration_lock_held = False
        if isinstance(write_set, StagedWriteSet):
            outputs = (
                *write_set.object_appends,
                *write_set.accounting_event_appends,
                *write_set.journal_appends,
                *write_set.reporting_version_appends,
            )
            refs = tuple(
                _authoritative_ref(
                    authoritative_family(value), _record_identity(value), value
                )
                for value in outputs
            )
            effects = tuple(item.idempotency_key for item in write_set.effect_claims)
            tokens = write_set.resulting_state_tokens
        else:
            refs = tuple(
                _authoritative_ref(
                    authoritative_family(value), _record_identity(value), value
                )
                for value in write_set.object_appends
            )
            effects = ()
            tokens = ()
        publication_refs = tuple(
            item for item in refs if item.record_family == "J-AR13"
        )
        authoritative_refs = tuple(
            item for item in refs if item.record_family != "J-AR13"
        )
        result_ref = _authoritative_ref(
            "J-AR14",
            write_set.command_result.command_id,
            write_set.command_result,
        )
        disposition_refs = tuple(
            _authoritative_ref("J-AR16", item.command_id, item)
            for item in write_set.dispositions
        )
        return CommitReceipt(
            outcome=outcome,
            command_result_ref=result_ref.record_identity,
            command_result_hash=result_ref.semantic_hash,
            committed_authoritative_refs=(
                *authoritative_refs,
                result_ref,
                *disposition_refs,
            ),
            committed_publication_refs=publication_refs,
            claimed_effect_refs=effects,
            resulting_state_tokens=tokens,
        )

    def rollback(self) -> None:
        self._staged = None
        self._validated = None
        self._closed = True
        if self._arbitration_lock_held:
            self._boundary._lock.release()
            self._arbitration_lock_held = False


class InMemoryPersistenceBoundary:
    """One shared, serializable, in-process Artifact K persistence boundary."""

    def __init__(self, state: InMemoryState | None = None) -> None:
        self._state = state or InMemoryState()
        self._contexts: dict[str, CommandContext] = {}
        self._baseline_snapshot = self._state.snapshot
        self._baseline_available_from = BASELINE_AVAILABLE_FROM
        self._baseline_command_ids = frozenset(
            item.command_id for item in self._state.command_results
        )
        self._revision = 0
        self._lock = RLock()

    @property
    def state(self) -> InMemoryState:
        with self._lock:
            return self._state

    @property
    def revision(self) -> int:
        with self._lock:
            return self._revision

    def begin_command(self, context: CommandContext) -> InMemoryCommandUnitOfWork:
        with self._lock:
            return InMemoryCommandUnitOfWork(
                self,
                context,
                self._state,
                self._revision,
            )

    def open_query(self, context: QueryContext) -> InMemoryQuerySession:
        if not context.semantic_as_of_time:
            raise ValueError("query context requires semantic_as_of_time")
        with self._lock:
            return InMemoryQuerySession(
                self._state,
                self._revision,
                context,
                dict(self._contexts),
                self._baseline_snapshot,
                self._baseline_available_from,
                self._baseline_command_ids,
            )

    def _commit_prepared(
        self,
        *,
        previous: InMemoryState,
        prepared: InMemoryState,
        context: CommandContext,
    ) -> None:
        """Publish one validated state while the boundary lock is held.

        Persistent adapters override this single hook and must make durable
        commit succeed before publishing the new in-process state.
        """

        if previous is not self._state:
            raise InvariantFailure("prepared state no longer has its exact base")
        self._state = prepared
        self._contexts[context.command_id] = context
        self._revision += 1
