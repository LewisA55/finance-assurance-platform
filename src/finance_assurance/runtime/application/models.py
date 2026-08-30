"""Closed Phase 4 application inputs and deterministic infrastructure ports."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, model_validator

from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.contracts.events import AccountingEvent
from finance_assurance.runtime.contracts.objects import (
    AutomatedPostingBasis,
    BusinessEvent,
    JournalProposalBase,
    ProposalLine,
    ReplacementOriginBasis,
    RestatementAdjustmentOriginBasis,
    ReversalOriginBasis,
)
from finance_assurance.runtime.contracts.primitives import (
    ActorRef,
    AsciiString,
    Currency,
    DateString,
    EvidenceRef,
    FrozenContractModel,
    HashValue,
    PeriodId,
    PositiveInt,
    Timestamp,
    VersionRef,
)

WorkflowFamily = Literal["C001", "CT1"]
CandidateOutcome = Literal["ACCEPTED", "REJECTED", "UNSUPPORTED"]
OriginType = Literal[
    "AUTOMATED_POSTING",
    "REVERSAL",
    "REPLACEMENT",
    "RESTATEMENT_ADJUSTMENT",
]
OriginBasis = (
    AutomatedPostingBasis
    | ReversalOriginBasis
    | ReplacementOriginBasis
    | RestatementAdjustmentOriginBasis
)

C001_EVENT_SEQUENCE = (
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
CT1_EVENT_SEQUENCE = (
    "proposal.submitted",
    "proposal.approved",
    "journal.posted",
    "proposal.submitted",
    "proposal.approved",
    "journal.posted",
)


class ClockPort(Protocol):
    """Supply one deterministic occurred/recorded pair per accounting action."""

    def next_timestamp(self, purpose: str) -> tuple[str, str]: ...


class IdentityGeneratorPort(Protocol):
    """Supply globally unique identities without domain-literal branching."""

    def next_identity(self, namespace: str) -> str: ...


class ScriptedClock:
    """Deterministic clock used by tests, demos, and reproducible replays."""

    def __init__(self, values: tuple[tuple[str, str], ...]) -> None:
        self._values = deque(values)

    def next_timestamp(self, purpose: str) -> tuple[str, str]:
        del purpose
        if not self._values:
            raise ValueError("deterministic clock is exhausted")
        return self._values.popleft()


class ScriptedIdentityGenerator:
    """Finite deterministic identity source keyed by semantic namespace."""

    def __init__(self, values: dict[str, tuple[str, ...]]) -> None:
        self._values = {key: deque(items) for key, items in values.items()}

    def next_identity(self, namespace: str) -> str:
        values = self._values.get(namespace)
        if values is None or not values:
            raise ValueError(f"deterministic identity namespace exhausted: {namespace}")
        return values.popleft()


def _reject_float(value: object) -> None:
    if isinstance(value, float):
        raise ValueError("candidate canonical body cannot contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _reject_float(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_float(item)


class CandidateReceipt(FrozenContractModel):
    """Artifact J J-AR01 replayable source-candidate custody record."""

    receipt_contract_version: Literal[1]
    candidate_receipt_ref: AsciiString
    candidate_contract_version: AsciiString
    canonicalization_version: Literal["SORTED_KEYS_COMPACT_UTF8_V1"]
    candidate_type: AsciiString
    canonical_candidate_body: dict[str, Any]
    candidate_payload_hash: HashValue
    source_domain_ref: AsciiString
    source_record_ref: AsciiString
    received_at: Timestamp
    approval_ref: AsciiString | None
    upstream_authoritative_refs: tuple[AsciiString, ...]
    evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def candidate_content_is_replayable(self) -> CandidateReceipt:
        _reject_float(self.canonical_candidate_body)
        if self.candidate_payload_hash != canonical_sha256(
            self.canonical_candidate_body
        ):
            raise ValueError("candidate payload hash does not match canonical body")
        if len(self.upstream_authoritative_refs) != len(
            set(self.upstream_authoritative_refs)
        ):
            raise ValueError("candidate upstream references must be unique")
        return self


class CandidateAssessmentCommand(FrozenContractModel):
    """Typed I-C01 input; assessment outcome is derived, never caller supplied."""

    command_contract_version: Literal[1]
    command_id: AsciiString
    actor_ref: AsciiString
    correlation_id: AsciiString
    semantic_as_of_time: Timestamp
    candidate_receipt_ref: AsciiString
    admission_product_ref: VersionRef
    publication_ref: AsciiString
    candidate_contract_version: AsciiString
    candidate_type: AsciiString
    canonical_candidate_body: dict[str, Any]
    source_domain_ref: AsciiString
    source_record_ref: AsciiString
    received_at: Timestamp
    assessed_at: Timestamp
    approval_ref: AsciiString | None = None
    upstream_authoritative_refs: tuple[AsciiString, ...] = ()
    evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def candidate_input_is_canonical(self) -> CandidateAssessmentCommand:
        _reject_float(self.canonical_candidate_body)
        if len(self.upstream_authoritative_refs) != len(
            set(self.upstream_authoritative_refs)
        ):
            raise ValueError("candidate upstream references must be unique")
        return self


class ProposalTreatmentVersion(FrozenContractModel):
    """Artifact J J-AR05: proposal content without lifecycle status."""

    contract_version: Literal[1]
    proposal_id: AsciiString
    proposal_version: PositiveInt
    proposal_ref: VersionRef
    origin_type: OriginType
    origin_basis: OriginBasis
    target_period_id: PeriodId
    effective_date: DateString
    ledger_currency: Currency
    proposed_lines: tuple[ProposalLine, ...] = Field(min_length=2)
    total_debit_minor: PositiveInt
    total_credit_minor: PositiveInt
    prepared_by: ActorRef
    created_at: Timestamp
    evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)
    treatment_hash: HashValue

    @model_validator(mode="after")
    def identity_basis_and_totals_match(self) -> ProposalTreatmentVersion:
        if self.proposal_ref != f"{self.proposal_id}@v{self.proposal_version}":
            raise ValueError("proposal treatment identity is inconsistent")
        expected_basis = {
            "AUTOMATED_POSTING": AutomatedPostingBasis,
            "REVERSAL": ReversalOriginBasis,
            "REPLACEMENT": ReplacementOriginBasis,
            "RESTATEMENT_ADJUSTMENT": RestatementAdjustmentOriginBasis,
        }[self.origin_type]
        if not isinstance(self.origin_basis, expected_basis):
            raise ValueError("proposal treatment origin basis is inconsistent")
        debit = sum(line.debit_minor for line in self.proposed_lines)
        credit = sum(line.credit_minor for line in self.proposed_lines)
        if debit != credit or debit != self.total_debit_minor:
            raise ValueError("proposal treatment lines do not balance")
        if credit != self.total_credit_minor:
            raise ValueError("proposal treatment credit total is inconsistent")
        unhashed = self.model_dump(mode="json", exclude={"treatment_hash"})
        if self.treatment_hash != canonical_sha256(unhashed):
            raise ValueError("proposal treatment hash is inconsistent")
        return self

    @classmethod
    def from_proposal(
        cls,
        proposal: JournalProposalBase,
    ) -> ProposalTreatmentVersion:
        body = proposal.model_dump(mode="python")
        body.pop("status")
        body.pop("submitted_at")
        hash_body = proposal.model_dump(mode="json")
        hash_body.pop("status")
        hash_body.pop("submitted_at")
        body["treatment_hash"] = canonical_sha256(hash_body)
        return cls.model_validate(body)

    @property
    def account_ids(self) -> frozenset[str]:
        return frozenset(line.account_id for line in self.proposed_lines)

    @property
    def input_hashes(self) -> tuple[str, ...]:
        return tuple(self.origin_basis.input_hashes)


@dataclass(frozen=True, slots=True)
class EventCreations:
    """Immutable Artifact F outputs committed by one accounting event."""

    template_event_id: str
    values: tuple[BaseModel, ...]
    consumed_publication_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AccountingWorkflow:
    """One finite C-001 or CT-1 accounting workflow before ID/time binding."""

    family: WorkflowFamily
    correlation_id: str
    treatments: tuple[ProposalTreatmentVersion, ...]
    event_templates: tuple[AccountingEvent, ...]
    creations: tuple[EventCreations, ...] = ()
    business_event: BusinessEvent | None = None

    def __post_init__(self) -> None:
        expected = C001_EVENT_SEQUENCE if self.family == "C001" else CT1_EVENT_SEQUENCE
        actual = tuple(str(item.event_type) for item in self.event_templates)
        if actual != expected:
            raise ValueError(
                f"{self.family} requires its exact declared accounting-event sequence"
            )
        event_ids = tuple(str(item.event_id) for item in self.event_templates)
        command_ids = tuple(str(item.command_id) for item in self.event_templates)
        if len(set(event_ids)) != len(event_ids) or len(set(command_ids)) != len(
            command_ids
        ):
            raise ValueError("workflow event and command identities must be unique")
        if any(
            str(item.correlation_id) != self.correlation_id
            for item in self.event_templates
        ):
            raise ValueError("workflow events must share the declared correlation")
        expected_causes: tuple[str | None, ...] = (None, *event_ids[:-1])
        actual_causes = tuple(
            str(item.causation_event_id)
            if item.causation_event_id is not None
            else None
            for item in self.event_templates
        )
        if actual_causes != expected_causes:
            raise ValueError("workflow events must form one exact causal chain")
        proposal_refs = tuple(item.proposal_ref for item in self.treatments)
        if len(set(proposal_refs)) != len(proposal_refs):
            raise ValueError("proposal treatment identities must be unique")
        if self.family == "C001":
            if self.business_event is None:
                raise ValueError(
                    "C001 requires one admitted recognition business event"
                )
            origins = tuple(item.origin_type for item in self.treatments)
            if origins != ("AUTOMATED_POSTING", "RESTATEMENT_ADJUSTMENT"):
                raise ValueError("C001 requires automated and restatement treatments")
            if self.business_event.correlation_id != self.correlation_id:
                raise ValueError("business event must share workflow correlation")
            automated = self.treatments[0].origin_basis
            if automated.business_event_ref != self.business_event.business_event_id:
                raise ValueError("automated treatment must bind the business event")
        else:
            if self.business_event is not None:
                raise ValueError(
                    "CT1 correction constructors cannot consume a business event"
                )
            origins = tuple(item.origin_type for item in self.treatments)
            if origins != ("REVERSAL", "REPLACEMENT"):
                raise ValueError("CT1 requires reversal and replacement treatments")
        event_id_set = set(event_ids)
        creation_ids = tuple(item.template_event_id for item in self.creations)
        if len(set(creation_ids)) != len(creation_ids):
            raise ValueError("one creation bundle is permitted per event")
        if any(item.template_event_id not in event_id_set for item in self.creations):
            raise ValueError("event creation is attached to an unknown event")
        if any(
            len(item.consumed_publication_refs)
            != len(set(item.consumed_publication_refs))
            for item in self.creations
        ):
            raise ValueError("event publication consumption must be unique")

    def instantiate(
        self,
        *,
        clock: ClockPort,
        identities: IdentityGeneratorPort,
        correlation_id: str,
    ) -> AccountingWorkflow:
        """Bind event/command identity and dual time without changing semantics."""

        event_id_map: dict[str, str] = {}
        command_id_map: dict[str, str] = {}
        time_map: dict[str, tuple[str, str]] = {}
        for template in self.event_templates:
            old_event_id = str(template.event_id)
            event_id_map[old_event_id] = identities.next_identity("accounting_event")
            command_id_map[old_event_id] = identities.next_identity("command")
            time_map[old_event_id] = clock.next_timestamp(str(template.event_type))

        events: list[AccountingEvent] = []
        for template in self.event_templates:
            old_event_id = str(template.event_id)
            body = template.model_dump(mode="python")
            body.update(
                event_id=event_id_map[old_event_id],
                command_id=command_id_map[old_event_id],
                correlation_id=correlation_id,
                occurred_at=time_map[old_event_id][0],
                recorded_at=time_map[old_event_id][1],
            )
            cause = template.causation_event_id
            body["causation_event_id"] = (
                event_id_map[str(cause)] if cause is not None else None
            )
            events.append(type(template).model_validate(body))

        creations_by_event: dict[str, list[BaseModel]] = defaultdict(list)
        occurred_at_map = {
            str(template.occurred_at): time_map[str(template.event_id)][0]
            for template in self.event_templates
        }
        for bundle in self.creations:
            new_event_id = event_id_map[bundle.template_event_id]
            creations_by_event[new_event_id]
            for value in bundle.values:
                body = value.model_dump(mode="python")
                for field in (
                    "hard_close_event_id",
                    "posted_by_event_id",
                    "published_by_event_id",
                ):
                    prior_event_id = body.get(field)
                    if prior_event_id in event_id_map:
                        body[field] = event_id_map[prior_event_id]
                for field in (
                    "approved_at",
                    "hard_closed_at",
                    "posted_at",
                    "published_at",
                ):
                    prior_time = body.get(field)
                    if prior_time in occurred_at_map:
                        body[field] = occurred_at_map[prior_time]
                creations_by_event[new_event_id].append(type(value).model_validate(body))

        return AccountingWorkflow(
            family=self.family,
            correlation_id=correlation_id,
            treatments=self.treatments,
            event_templates=tuple(events),
            creations=tuple(
                EventCreations(
                    event_id_map[bundle.template_event_id],
                    tuple(creations_by_event[event_id_map[bundle.template_event_id]]),
                    bundle.consumed_publication_refs,
                )
                for bundle in self.creations
            ),
            business_event=(
                self.business_event.model_copy(
                    update={"correlation_id": correlation_id}
                )
                if self.business_event is not None
                else None
            ),
        )
