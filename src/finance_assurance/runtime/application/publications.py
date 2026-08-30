"""Closed Artifact I publication matrix for Atlas accounting transitions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pydantic import BaseModel

from finance_assurance.runtime.application.models import ProposalTreatmentVersion
from finance_assurance.runtime.contracts.events import (
    AccountingEvent,
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
    AccountingPeriodBase,
    AutomatedPostingProposal,
    JournalEntryBase,
    JournalProposalBase,
    PublishedRestatementCase,
    ReplacementProposal,
    ReportingVersion,
    RestatementAdjustmentProposal,
    RestatementCaseBase,
    ReversalProposal,
)
from finance_assurance.runtime.contracts.primitives import AuthoritativeRef
from finance_assurance.runtime.digests import value_digest


class AtlasPublicationClosureError(ValueError):
    """Raised before persistence when an accounting publication set is not exact."""


@dataclass(frozen=True, slots=True)
class AtlasPublicationRequirement:
    """One required publication identity and exact canonical body."""

    contract_id: str
    body_discriminator: str
    product_ref: str
    product_state_token: str | None
    canonical_payload: dict[str, object]


_PROPOSAL_TYPES = {
    "AUTOMATED_POSTING": AutomatedPostingProposal,
    "REVERSAL": ReversalProposal,
    "REPLACEMENT": ReplacementProposal,
    "RESTATEMENT_ADJUSTMENT": RestatementAdjustmentProposal,
}


def _one(
    values: tuple[BaseModel, ...],
    expected_type: type[BaseModel],
    label: str,
) -> BaseModel:
    matches = tuple(item for item in values if isinstance(item, expected_type))
    if len(matches) != 1:
        raise AtlasPublicationClosureError(
            f"{label} requires exactly one {expected_type.__name__}"
        )
    return matches[0]


def _proposal_view(
    treatment: ProposalTreatmentVersion,
    *,
    status: str,
    submitted_at: str,
) -> JournalProposalBase:
    body = treatment.model_dump(mode="python", exclude={"treatment_hash"})
    body.update(status=status, submitted_at=submitted_at)
    proposal_type = _PROPOSAL_TYPES[treatment.origin_type]
    return proposal_type.model_validate(body)


def _g06_payload(
    report: ReportingVersion,
    event: ReportingVersionPublished,
) -> dict[str, object]:
    return {
        "reporting_version_ref": str(report.reporting_version_ref),
        "period_id": str(report.period_id),
        "content_ref": str(report.content_ref),
        "content_hash": str(report.content_hash),
        "content_schema_version": report.content_schema_version,
        "publication_origin": "RESTATEMENT_PUBLICATION",
        "published_at": str(report.published_at),
        "predecessor_version_ref": str(report.predecessor_version_ref),
        "restatement_case_ref": str(report.restatement_case_id),
        "manifest_hash": str(report.adjustment_manifest_hash),
        "published_by_event_id": str(report.published_by_event_id),
        "publication_effect_ref": str(event.idempotency_key),
    }


def required_atlas_publications(
    event: AccountingEvent,
    *,
    treatment: ProposalTreatmentVersion | None,
    submitted_at: str | None,
    authoritative_creations: tuple[BaseModel, ...],
) -> tuple[AtlasPublicationRequirement, ...]:
    """Return the finite G-04/G-05/G-06 closure ratified for one event."""

    requirements: list[AtlasPublicationRequirement] = []
    subject_ref = str(event.subject_ref.object_ref)

    if isinstance(
        event,
        (ProposalSubmitted, ProposalDeferred, ProposalApproved, JournalPosted),
    ):
        if treatment is None or submitted_at is None:
            raise AtlasPublicationClosureError(
                "proposal publication requires treatment and submission time"
            )
        if str(treatment.proposal_ref) != subject_ref:
            raise AtlasPublicationClosureError(
                "proposal publication treatment does not match event subject"
            )
        status = {
            ProposalSubmitted: "SUBMITTED",
            ProposalDeferred: "DEFERRED",
            ProposalApproved: "APPROVED",
            JournalPosted: "POSTED",
        }[type(event)]
        proposal = _proposal_view(
            treatment,
            status=status,
            submitted_at=submitted_at,
        )
        requirements.append(
            AtlasPublicationRequirement(
                contract_id="G-04",
                body_discriminator="journal_proposal",
                product_ref=str(proposal.proposal_ref),
                product_state_token=str(event.event_id),
                canonical_payload=proposal.model_dump(mode="json"),
            )
        )
        if isinstance(event, JournalPosted):
            journal = _one(
                authoritative_creations,
                JournalEntryBase,
                "journal.posted publication closure",
            )
            assert isinstance(journal, JournalEntryBase)
            if (
                str(journal.source_proposal_ref) != subject_ref
                or str(journal.posted_by_event_id) != str(event.event_id)
                or str(journal.journal_id) != str(event.payload.journal_id)
                or str(journal.posted_at) != str(event.occurred_at)
            ):
                raise AtlasPublicationClosureError(
                    "journal publication does not match its posting event"
                )
            requirements.append(
                AtlasPublicationRequirement(
                    contract_id="G-04",
                    body_discriminator="journal_entry",
                    product_ref=str(journal.journal_id),
                    product_state_token=None,
                    canonical_payload=journal.model_dump(mode="json"),
                )
            )
    elif isinstance(event, PeriodHardClosed):
        period = _one(
            authoritative_creations,
            AccountingPeriodBase,
            "period.hard_closed publication closure",
        )
        assert isinstance(period, AccountingPeriodBase)
        if (
            str(period.period_id) != subject_ref
            or period.status != "HARD_CLOSED"
            or str(period.hard_close_event_id) != str(event.event_id)
            or str(period.hard_closed_at) != str(event.occurred_at)
        ):
            raise AtlasPublicationClosureError(
                "period publication does not match its hard-close event"
            )
        requirements.append(
            AtlasPublicationRequirement(
                contract_id="G-04",
                body_discriminator="accounting_period",
                product_ref=str(period.period_id),
                product_state_token=str(event.event_id),
                canonical_payload=period.model_dump(mode="json"),
            )
        )
    elif isinstance(
        event,
        (
            RestatementProposed,
            RestatementAdjustmentLinked,
            RestatementAdjustmentsReady,
            RestatementApproved,
            ReportingVersionPublished,
        ),
    ):
        case = _one(
            authoritative_creations,
            RestatementCaseBase,
            "restatement publication closure",
        )
        assert isinstance(case, RestatementCaseBase)
        if str(case.restatement_case_id) != subject_ref:
            raise AtlasPublicationClosureError(
                "restatement publication does not match event subject"
            )
        expected_status = {
            RestatementProposed: "PROPOSED",
            RestatementAdjustmentLinked: "PROPOSED",
            RestatementAdjustmentsReady: "ADJUSTMENTS_READY",
            RestatementApproved: "APPROVED",
            ReportingVersionPublished: "PUBLISHED",
        }[type(event)]
        if case.status != expected_status:
            raise AtlasPublicationClosureError(
                "restatement publication status does not match event transition"
            )
        if isinstance(event, RestatementAdjustmentLinked) and str(
            event.payload.journal_id
        ) not in {str(item) for item in case.linked_journal_ids}:
            raise AtlasPublicationClosureError(
                "linked restatement publication omits the governed journal"
            )
        if isinstance(event, RestatementAdjustmentsReady) and str(
            case.manifest_hash
        ) != str(event.basis.manifest_hash):
            raise AtlasPublicationClosureError(
                "restatement publication does not bind the frozen manifest"
            )
        if isinstance(event, RestatementApproved) and str(case.approved_at) != str(
            event.occurred_at
        ):
            raise AtlasPublicationClosureError(
                "approved restatement publication does not bind approval time"
            )
        if isinstance(event, ReportingVersionPublished) and str(
            event.payload.reporting_version_ref
        ) not in {str(item) for item in case.published_version_refs}:
            raise AtlasPublicationClosureError(
                "published restatement case omits the successor reporting version"
            )
        requirements.append(
            AtlasPublicationRequirement(
                contract_id="G-04",
                body_discriminator="restatement_case",
                product_ref=str(case.restatement_case_id),
                product_state_token=str(event.event_id),
                canonical_payload=case.model_dump(mode="json"),
            )
        )
    else:  # pragma: no cover - AccountingWorkflow closes the event union
        raise AtlasPublicationClosureError(
            f"accounting event has no Artifact I publication ruling: {event.event_type}"
        )

    requirements.append(
        AtlasPublicationRequirement(
            contract_id="G-05",
            body_discriminator="accounting_event",
            product_ref=str(event.event_id),
            product_state_token=None,
            canonical_payload=event.model_dump(mode="json"),
        )
    )

    if isinstance(event, ReportingVersionPublished):
        report = _one(
            authoritative_creations,
            ReportingVersion,
            "reporting publication closure",
        )
        assert isinstance(report, ReportingVersion)
        case = _one(
            authoritative_creations,
            PublishedRestatementCase,
            "reporting publication closure",
        )
        assert isinstance(case, PublishedRestatementCase)
        if (
            str(report.reporting_version_ref)
            != str(event.payload.reporting_version_ref)
            or str(report.published_by_event_id) != str(event.event_id)
            or str(report.published_at) != str(event.occurred_at)
            or str(report.restatement_case_id) != str(case.restatement_case_id)
        ):
            raise AtlasPublicationClosureError(
                "G-06 reporting product does not match its publication event"
            )
        requirements.append(
            AtlasPublicationRequirement(
                contract_id="G-06",
                body_discriminator="G06ReportingVersion",
                product_ref=str(report.reporting_version_ref),
                product_state_token=None,
                canonical_payload=_g06_payload(report, event),
            )
        )
    return tuple(requirements)


def materialize_atlas_publications(
    event: AccountingEvent,
    requirements: tuple[AtlasPublicationRequirement, ...],
) -> tuple[ContractPublication, ...]:
    """Materialize the exact command-owned closure as J-AR13 records."""

    evidence_refs = tuple(
        AuthoritativeRef(
            record_family="J-AR12",
            record_identity=str(item.ref_id),
            semantic_hash=value_digest(item),
        )
        for item in event.evidence_refs
    )
    return tuple(
        ContractPublication.command(
            publication_ref=(
                f"PUB-{event.event_id}-{requirement.contract_id}-"
                f"{ordinal:02d}"
            ),
            contract_id=requirement.contract_id,  # type: ignore[arg-type]
            body_discriminator=requirement.body_discriminator,
            publisher="Atlas",
            product_ref=requirement.product_ref,
            product_state_token=requirement.product_state_token,
            payload=requirement.canonical_payload,
            command_owner="Atlas",
            command_id=str(event.command_id),
            evidence_refs=evidence_refs,
            available_from=str(event.recorded_at),
        )
        for ordinal, requirement in enumerate(requirements, start=1)
    )


def validate_atlas_publication_closure(
    requirements: tuple[AtlasPublicationRequirement, ...],
    publications: Iterable[ContractPublication],
) -> tuple[ContractPublication, ...]:
    """Reject missing, extra, reordered, or semantically mismatched publications."""

    actual = tuple(publications)
    expected = tuple(
        (
            item.contract_id,
            item.body_discriminator,
            item.product_ref,
            item.product_state_token,
            item.canonical_payload,
        )
        for item in requirements
    )
    observed = tuple(
        (
            item.contract_id,
            item.body_discriminator,
            str(item.product_ref),
            str(item.product_state_token)
            if item.product_state_token is not None
            else None,
            item.canonical_payload,
        )
        for item in actual
    )
    if observed != expected:
        raise AtlasPublicationClosureError(
            "accounting command publication closure is not exact"
        )
    return actual
