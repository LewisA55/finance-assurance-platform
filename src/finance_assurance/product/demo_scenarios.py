"""Typed, parameterised Artifact O demo scenarios without fixture dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import ConfigDict

from finance_assurance.product.contracts import PublicContractModel
from finance_assurance.runtime.application.models import (
    AccountingWorkflow,
    EventCreations,
    ProposalTreatmentVersion,
)
from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.contracts import (
    ACCOUNTING_EVENT_ADAPTER,
    OBJECT_ADAPTERS,
)
from finance_assurance.runtime.contracts.events import AccountingEvent
from finance_assurance.runtime.contracts.evidence import (
    ReportingContentBody,
    ReportingContentRecord,
)
from finance_assurance.runtime.contracts.objects import (
    BusinessEvent,
    JournalEntryBase,
    JournalLine,
    JournalProposalBase,
    PostingRule,
)
from finance_assurance.runtime.contracts.primitives import (
    AsciiString,
    Currency,
    DateString,
    EvidenceRef,
    PeriodId,
    PositiveInt,
    Timestamp,
)
from finance_assurance.runtime.planner import PeriodState, StateSnapshot
from finance_assurance.runtime.referenced import ReferencedJournalProjection


class _Descriptor(PublicContractModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class C001ScenarioDescriptor(_Descriptor):
    scenario_contract_version: Literal[1]
    scenario_ref: Literal["DEMO-C001-RESTATEMENT@v1"]
    canonical_family: Literal["C-001"]
    correlation_id: AsciiString
    legal_entity_id: AsciiString
    customer_id: AsciiString
    contract_id: AsciiString
    recognition_schedule_id: AsciiString
    business_event_id: AsciiString
    proposal_id: AsciiString
    restatement_case_id: AsciiString
    correction_journal_id: AsciiString
    reporting_version_id: AsciiString
    reporting_period_id: PeriodId
    correction_period_id: PeriodId
    service_period_start: DateString
    service_period_end: DateString
    recognition_effective_date: DateString
    correction_effective_date: DateString
    monthly_revenue_minor: PositiveInt
    annual_invoice_minor: PositiveInt
    currency: Currency
    semantic_as_of_time: Timestamp


class CT1ScenarioDescriptor(_Descriptor):
    scenario_contract_version: Literal[1]
    scenario_ref: Literal["DEMO-CT1-CORRECTION@v1"]
    canonical_family: Literal["CT-1"]
    correlation_id: AsciiString
    legal_entity_id: AsciiString
    receipt_party_ref: AsciiString
    incorrect_customer_id: AsciiString
    correct_customer_id: AsciiString
    source_journal_id: AsciiString
    reversal_proposal_id: AsciiString
    replacement_proposal_id: AsciiString
    reversal_journal_id: AsciiString
    replacement_journal_id: AsciiString
    correction_period_id: PeriodId
    correction_effective_date: DateString
    amount_minor: PositiveInt
    currency: Currency
    semantic_as_of_time: Timestamp


class DemoScenarioSet(_Descriptor):
    demo_contract_version: Literal[1]
    baseline_contract_version: Literal[1]
    runtime_release: AsciiString
    semantic_as_of_time: Timestamp
    synthetic_data_notice: AsciiString
    c001: C001ScenarioDescriptor
    ct1: CT1ScenarioDescriptor


@dataclass(frozen=True, slots=True)
class BuiltScenario:
    scenario_ref: str
    canonical_family: Literal["C-001", "CT-1"]
    workflow: AccountingWorkflow
    initial_snapshot: StateSnapshot
    evidence: tuple[EvidenceRef, ...]
    reporting_content: tuple[ReportingContentRecord, ...] = ()
    posting_rule: PostingRule | None = None
    referenced_journal: ReferencedJournalProjection | None = None
    referenced_source_body: dict[str, object] | None = None


def default_demo_scenarios() -> DemoScenarioSet:
    """Return the exact, versioned synthetic input set for Artifact O v1."""

    return DemoScenarioSet(
        demo_contract_version=1,
        baseline_contract_version=1,
        runtime_release="0.1.0",
        semantic_as_of_time="2026-07-14T12:00:00Z",
        synthetic_data_notice=(
            "Synthetic demonstration data only; no client or employer data."
        ),
        c001=C001ScenarioDescriptor(
            scenario_contract_version=1,
            scenario_ref="DEMO-C001-RESTATEMENT@v1",
            canonical_family="C-001",
            correlation_id="C-001",
            legal_entity_id="NEXUS-UK",
            customer_id="CUST-ORION",
            contract_id="CONTRACT-C001",
            recognition_schedule_id="RECSCHED-C001",
            business_event_id="BE-C001-RECOG-202606",
            proposal_id="P-551",
            restatement_case_id="RC-001",
            correction_journal_id="J-560",
            reporting_version_id="RV-2026-06",
            reporting_period_id="2026-06",
            correction_period_id="2026-07",
            service_period_start="2026-06-01",
            service_period_end="2026-06-30",
            recognition_effective_date="2026-06-30",
            correction_effective_date="2026-07-13",
            monthly_revenue_minor=1_000_000,
            annual_invoice_minor=12_000_000,
            currency="GBP",
            semantic_as_of_time="2026-07-14T12:00:00Z",
        ),
        ct1=CT1ScenarioDescriptor(
            scenario_contract_version=1,
            scenario_ref="DEMO-CT1-CORRECTION@v1",
            canonical_family="CT-1",
            correlation_id="CT-1",
            legal_entity_id="NEXUS-UK",
            receipt_party_ref="PARTY:ORION",
            incorrect_customer_id="CUST-VEGA",
            correct_customer_id="CUST-ORION",
            source_journal_id="J-010",
            reversal_proposal_id="P-REV-010",
            replacement_proposal_id="P-REP-010",
            reversal_journal_id="J-011",
            replacement_journal_id="J-012",
            correction_period_id="2026-07",
            correction_effective_date="2026-07-11",
            amount_minor=12_000_000,
            currency="GBP",
            semantic_as_of_time="2026-07-14T12:00:00Z",
        ),
    )


def _hash(character: str) -> str:
    return "sha256:" + character * 64


def _evidence(ref_id: str, description: str, content_hash: str) -> EvidenceRef:
    return EvidenceRef(
        ref_id=ref_id,
        description=description,
        content_hash=content_hash,
    )


def _actor(actor_type: str, actor_id: str, role: str) -> dict[str, str]:
    return {"actor_type": actor_type, "actor_id": actor_id, "role": role}


RULE_ENGINE = _actor("SYSTEM_POLICY", "SYS-RULE-ENGINE", "RULE_ENGINE")
CORRECTION_ENGINE = _actor(
    "SYSTEM_POLICY", "SYS-CORRECTION-ENGINE", "CORRECTION_ENGINE"
)
CONTROLLER = _actor("PERSON", "USR-CONTROLLER-01", "CONTROLLER")
CFO = _actor("PERSON", "USR-CFO-01", "CFO")
POSTING_SERVICE = _actor("SYSTEM_POLICY", "SYS-POSTING", "POSTING_SERVICE")
REPORTING_SERVICE = _actor(
    "SYSTEM_POLICY", "SYS-REPORTING", "REPORTING_SERVICE"
)


def _authorization(mode: str, policy_id: str) -> dict[str, object]:
    return {
        "authority_mode": mode,
        "policy_ref": {"object_type": "policy", "object_id": policy_id},
    }


def _event(
    *,
    event_id: str,
    event_type: str,
    subject_type: str,
    subject_ref: str,
    command_id: str,
    correlation_id: str,
    causation_event_id: str | None,
    occurred_at: str,
    actor: dict[str, str],
    authorization: dict[str, object],
    basis: dict[str, object],
    payload: dict[str, object],
    evidence: EvidenceRef,
    idempotency_key: str | None = None,
) -> AccountingEvent:
    body: dict[str, object] = {
        "contract_version": 1,
        "event_id": event_id,
        "event_type": event_type,
        "subject_ref": {"object_type": subject_type, "object_ref": subject_ref},
        "command_id": command_id,
        "correlation_id": correlation_id,
        "causation_event_id": causation_event_id,
        "occurred_at": occurred_at,
        "recorded_at": occurred_at.replace("00Z", "01Z"),
        "actor": actor,
        "authorization": authorization,
        "basis": basis,
        "payload": payload,
        "evidence_refs": (evidence.model_dump(mode="python"),),
    }
    if idempotency_key is not None:
        body["idempotency_key"] = idempotency_key
    return ACCOUNTING_EVENT_ADAPTER.validate_python(body)


def _object(kind: str, body: dict[str, Any]) -> Any:
    return OBJECT_ADAPTERS[kind].validate_python(body)


def _dimensions(
    legal_entity_id: str,
    *,
    customer_id: str | None,
    contract_id: str | None,
) -> dict[str, object]:
    return {
        "legal_entity_id": legal_entity_id,
        "customer_id": customer_id,
        "contract_id": contract_id,
    }


def _proposal(
    *,
    proposal_id: str,
    proposal_version: int,
    status: str,
    origin_type: str,
    origin_basis: dict[str, object],
    target_period_id: str,
    effective_date: str,
    amount_minor: int,
    debit_account: str,
    credit_account: str,
    debit_customer: str | None,
    credit_customer: str | None,
    contract_id: str | None,
    legal_entity_id: str,
    prepared_by: dict[str, str],
    created_at: str,
    submitted_at: str,
    evidence: EvidenceRef,
) -> JournalProposalBase:
    proposal_ref = f"{proposal_id}@v{proposal_version}"
    return _object(
        "journal_proposal",
        {
            "contract_version": 1,
            "proposal_id": proposal_id,
            "proposal_version": proposal_version,
            "proposal_ref": proposal_ref,
            "status": status,
            "origin_type": origin_type,
            "origin_basis": origin_basis,
            "target_period_id": target_period_id,
            "effective_date": effective_date,
            "ledger_currency": "GBP",
            "proposed_lines": (
                {
                    "line_no": 1,
                    "account_id": debit_account,
                    "debit_minor": amount_minor,
                    "credit_minor": 0,
                    "currency": "GBP",
                    "dimensions": _dimensions(
                        legal_entity_id,
                        customer_id=debit_customer,
                        contract_id=contract_id,
                    ),
                },
                {
                    "line_no": 2,
                    "account_id": credit_account,
                    "debit_minor": 0,
                    "credit_minor": amount_minor,
                    "currency": "GBP",
                    "dimensions": _dimensions(
                        legal_entity_id,
                        customer_id=credit_customer,
                        contract_id=contract_id,
                    ),
                },
            ),
            "total_debit_minor": amount_minor,
            "total_credit_minor": amount_minor,
            "prepared_by": prepared_by,
            "created_at": created_at,
            "submitted_at": submitted_at,
            "evidence_refs": (evidence.model_dump(mode="python"),),
        },
    )


def _journal_package(
    proposal: JournalProposalBase,
    event: AccountingEvent,
    *,
    journal_id: str,
    correction_basis: dict[str, object],
) -> tuple[JournalEntryBase | JournalLine, ...]:
    lines = tuple(
        _object(
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
                "dimensions": line.dimensions.model_dump(mode="python"),
            },
        )
        for line in proposal.proposed_lines
    )
    journal = _object(
        "journal_entry",
        {
            "contract_version": 1,
            "journal_id": journal_id,
            "entry_class": event.payload.entry_class,
            "source_proposal_ref": proposal.proposal_ref,
            "posted_by_event_id": event.event_id,
            "ledger_period_id": event.basis.period_id,
            "effective_date": proposal.effective_date,
            "posted_at": event.occurred_at,
            "currency": event.basis.currency,
            "total_debit_minor": proposal.total_debit_minor,
            "total_credit_minor": proposal.total_credit_minor,
            "line_refs": tuple(line.journal_line_id for line in lines),
            "correction_basis": correction_basis,
            "evidence_refs": tuple(
                item.model_dump(mode="python") for item in event.evidence_refs
            ),
        },
    )
    return (journal, *lines)


def _reporting_content(
    *,
    fixture_id: str,
    content_ref: str,
    reporting_version_ref: str,
    period_id: str,
    revenue_minor: int,
    deferred_minor: int,
) -> ReportingContentRecord:
    body = ReportingContentBody(
        currency="GBP",
        deferred_revenue_minor=deferred_minor,
        presented_period_id=period_id,
        reporting_version_ref=reporting_version_ref,
        subscription_revenue_minor=revenue_minor,
    )
    return ReportingContentRecord(
        fixture_id=fixture_id,
        fixture_type="reporting_content_proof",
        content_ref=content_ref,
        content_hash=canonical_sha256(body.model_dump(mode="json")),
        content_schema_version=1,
        canonicalization="SORTED_KEYS_COMPACT_UTF8_V1",
        canonical_body=body,
    )


def _unique_evidence(*values: object) -> tuple[EvidenceRef, ...]:
    by_ref: dict[str, EvidenceRef] = {}
    for value in values:
        for item in getattr(value, "evidence_refs", ()):
            by_ref[str(item.ref_id)] = item
    return tuple(by_ref[key] for key in sorted(by_ref))


def _manifest(
    lines: tuple[JournalEntryBase | JournalLine, ...],
    *,
    ledger_period_id: str,
    presented_period_id: str,
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "journal_line_ref": line.journal_line_id,
            "ledger_period_id": ledger_period_id,
            "presented_period_id": presented_period_id,
            "account_id": line.account_id,
            "debit_minor": line.debit_minor,
            "credit_minor": line.credit_minor,
            "currency": line.currency,
            "basis_ref": {
                "object_type": "policy",
                "object_id": "POL-RESTATEMENT-v1",
            },
        }
        for line in lines
        if isinstance(line, JournalLine)
    )


def _restatement_case(
    *,
    status: str,
    descriptor: C001ScenarioDescriptor,
    event: AccountingEvent,
    proposal_event: AccountingEvent,
    approval_event: AccountingEvent,
    journal_package: tuple[JournalEntryBase | JournalLine, ...],
) -> Any:
    linked = status != "PROPOSED_EMPTY"
    wire_status = "PROPOSED" if status.startswith("PROPOSED") else status
    ready = wire_status in {"ADJUSTMENTS_READY", "APPROVED", "PUBLISHED"}
    approved = wire_status in {"APPROVED", "PUBLISHED"}
    published = wire_status == "PUBLISHED"
    evidence_event = approval_event if published else event
    return _object(
        "restatement_case",
        {
            "contract_version": 1,
            "restatement_case_id": descriptor.restatement_case_id,
            "status": wire_status,
            "scope_period_ids": (descriptor.reporting_period_id,),
            "trigger_ref": proposal_event.basis.trigger_ref.model_dump(mode="python"),
            "directive_ref": proposal_event.basis.directive_ref.model_dump(
                mode="python"
            ),
            "owner_ref": proposal_event.actor.model_dump(mode="python"),
            "linked_journal_ids": (
                (descriptor.correction_journal_id,) if linked else ()
            ),
            "adjustment_manifest": (
                _manifest(
                    journal_package,
                    ledger_period_id=descriptor.correction_period_id,
                    presented_period_id=descriptor.reporting_period_id,
                )
                if ready
                else ()
            ),
            "manifest_hash": _hash("3") if ready else None,
            "approver_ref": (
                approval_event.actor.model_dump(mode="python") if approved else None
            ),
            "approved_at": str(approval_event.occurred_at) if approved else None,
            "published_version_refs": (
                (f"{descriptor.reporting_version_id}@v2",) if published else ()
            ),
            "evidence_refs": tuple(
                item.model_dump(mode="python")
                for item in evidence_event.evidence_refs
            ),
        },
    )


def build_c001_scenario(descriptor: C001ScenarioDescriptor) -> BuiltScenario:
    """Construct C-001 from typed business parameters, never fixture rows."""

    v1_ref = f"{descriptor.reporting_version_id}@v1"
    v2_ref = f"{descriptor.reporting_version_id}@v2"
    proposal_v1 = f"{descriptor.proposal_id}@v1"
    proposal_v2 = f"{descriptor.proposal_id}@v2"
    v1_content = _reporting_content(
        fixture_id="DEMO-RPT-C001-V1",
        content_ref=f"reporting://{descriptor.reporting_period_id}/v1",
        reporting_version_ref=v1_ref,
        period_id=descriptor.reporting_period_id,
        revenue_minor=0,
        deferred_minor=descriptor.annual_invoice_minor,
    )
    v2_content = _reporting_content(
        fixture_id="DEMO-RPT-C001-V2",
        content_ref=f"reporting://{descriptor.reporting_period_id}/v2",
        reporting_version_ref=v2_ref,
        period_id=descriptor.reporting_period_id,
        revenue_minor=descriptor.monthly_revenue_minor,
        deferred_minor=(
            descriptor.annual_invoice_minor - descriptor.monthly_revenue_minor
        ),
    )
    evidence = {
        1: _evidence(
            "EVD-C001-001", "June recognition due input snapshot", _hash("a")
        ),
        2: _evidence("EVD-C001-002", "Approved June close exception", _hash("b")),
        3: _evidence("EVD-C001-003", "June hard-close evidence package", _hash("c")),
        4: _evidence(
            "EVD-C001-004", "Confirmed recognition completeness issue", _hash("d")
        ),
        5: _evidence(
            "EVD-C001-005", "Restatement adjustment proposal inputs", _hash("e")
        ),
        6: _evidence(
            "EVD-C001-006",
            "Controller approval for restatement adjustment",
            _hash("f"),
        ),
        7: _evidence("EVD-C001-007", "Validated J-560 posting package", _hash("1")),
        8: _evidence(
            "EVD-C001-008", "J-560 restatement-case linkage", _hash("2")
        ),
        9: _evidence(
            "EVD-C001-009",
            "Frozen June presentation-adjustment manifest",
            _hash("3"),
        ),
        10: _evidence("EVD-C001-010", "CFO restatement approval", _hash("4")),
        11: _evidence(
            "EVD-C001-011",
            "Published June 2026 restated snapshot",
            str(v2_content.content_hash),
        ),
    }
    event_ids = tuple(f"AE-C001-{index:03d}" for index in range(1, 12))
    command_ids = tuple(f"CMD-C001-{index:03d}" for index in range(1, 12))

    def prior(index: int) -> str | None:
        return None if index == 1 else event_ids[index - 2]

    events = (
        _event(
            event_id=event_ids[0],
            event_type="proposal.submitted",
            subject_type="journal_proposal",
            subject_ref=proposal_v1,
            command_id=command_ids[0],
            correlation_id=descriptor.correlation_id,
            causation_event_id=prior(1),
            occurred_at="2026-07-03T09:00:00Z",
            actor=RULE_ENGINE,
            authorization=_authorization("SYSTEM_POLICY", "POL-POSTING-v1"),
            basis={
                "basis_type": "PROPOSAL_SUBMISSION",
                "derivation_authority": {
                    "authority_kind": "POSTING_RULE",
                    "authority_ref": "PR-O2C-RECOG@v1",
                },
                "input_hashes": (_hash("a"),),
                "total_debit_minor": descriptor.monthly_revenue_minor,
                "total_credit_minor": descriptor.monthly_revenue_minor,
                "currency": descriptor.currency,
                "dimensions_resolved": True,
            },
            payload={
                "proposal_ref": proposal_v1,
                "from_status": "DRAFT",
                "to_status": "SUBMITTED",
            },
            evidence=evidence[1],
        ),
        _event(
            event_id=event_ids[1],
            event_type="proposal.deferred",
            subject_type="journal_proposal",
            subject_ref=proposal_v1,
            command_id=command_ids[1],
            correlation_id=descriptor.correlation_id,
            causation_event_id=prior(2),
            occurred_at="2026-07-09T16:00:00Z",
            actor=CONTROLLER,
            authorization=_authorization("HUMAN", "POL-CLOSE-v1"),
            basis={
                "basis_type": "CLOSE_EXCEPTION",
                "close_policy_ref": {
                    "object_type": "policy",
                    "object_id": "POL-CLOSE-v1",
                },
                "reason_code": "RECOGNITION_NOT_POSTED_BEFORE_CLOSE",
                "owner_ref": CONTROLLER,
                "target_treatment": "RESTATEMENT_REVIEW",
                "expires_on": "2026-07-31",
            },
            payload={
                "proposal_ref": proposal_v1,
                "from_status": "SUBMITTED",
                "to_status": "DEFERRED",
            },
            evidence=evidence[2],
        ),
        _event(
            event_id=event_ids[2],
            event_type="period.hard_closed",
            subject_type="accounting_period",
            subject_ref=descriptor.reporting_period_id,
            command_id=command_ids[2],
            correlation_id=descriptor.correlation_id,
            causation_event_id=prior(3),
            occurred_at="2026-07-10T18:00:00Z",
            actor=CONTROLLER,
            authorization=_authorization("HUMAN", "POL-CLOSE-v1"),
            basis={
                "basis_type": "PERIOD_CLOSE",
                "close_policy_ref": {
                    "object_type": "policy",
                    "object_id": "POL-CLOSE-v1",
                },
                "checklist_ref": {
                    "object_type": "checklist",
                    "object_id": "CHK-2026-06-HARD-CLOSE",
                },
                "trial_balance_hash": _hash("c"),
                "reconciliation_refs": (
                    {
                        "object_type": "reconciliation",
                        "object_id": "REC-2026-06-TB",
                    },
                ),
                "unresolved_submitted_count": 0,
                "unresolved_approved_count": 0,
                "deferred_proposal_refs": (proposal_v1,),
            },
            payload={
                "period_id": descriptor.reporting_period_id,
                "from_status": "SOFT_CLOSED",
                "to_status": "HARD_CLOSED",
            },
            evidence=evidence[3],
        ),
        _event(
            event_id=event_ids[3],
            event_type="restatement.proposed",
            subject_type="restatement_case",
            subject_ref=descriptor.restatement_case_id,
            command_id=command_ids[3],
            correlation_id=descriptor.correlation_id,
            causation_event_id=prior(4),
            occurred_at="2026-07-12T09:00:00Z",
            actor=CONTROLLER,
            authorization=_authorization("HUMAN", "POL-RESTATEMENT-v1"),
            basis={
                "basis_type": "RESTATEMENT_INITIATION",
                "trigger_ref": {
                    "object_type": "issue",
                    "object_id": "ISS-C001-001",
                },
                "directive_ref": {
                    "object_type": "remediation_directive",
                    "object_id": "DIR-C001-001",
                },
                "materiality_ref": {
                    "object_type": "materiality_assessment",
                    "object_id": "MAT-C001-001",
                },
                "scope_period_ids": (descriptor.reporting_period_id,),
            },
            payload={
                "restatement_case_id": descriptor.restatement_case_id,
                "to_status": "PROPOSED",
            },
            evidence=evidence[4],
        ),
        _event(
            event_id=event_ids[4],
            event_type="proposal.submitted",
            subject_type="journal_proposal",
            subject_ref=proposal_v2,
            command_id=command_ids[4],
            correlation_id=descriptor.correlation_id,
            causation_event_id=prior(5),
            occurred_at="2026-07-13T09:00:00Z",
            actor=CORRECTION_ENGINE,
            authorization=_authorization("SYSTEM_POLICY", "POL-RESTATEMENT-v1"),
            basis={
                "basis_type": "PROPOSAL_SUBMISSION",
                "derivation_authority": {
                    "authority_kind": "POLICY",
                    "authority_ref": "POL-RESTATEMENT-v1",
                },
                "input_hashes": (_hash("e"),),
                "total_debit_minor": descriptor.monthly_revenue_minor,
                "total_credit_minor": descriptor.monthly_revenue_minor,
                "currency": descriptor.currency,
                "dimensions_resolved": True,
            },
            payload={
                "proposal_ref": proposal_v2,
                "from_status": "DRAFT",
                "to_status": "SUBMITTED",
            },
            evidence=evidence[5],
        ),
        _event(
            event_id=event_ids[5],
            event_type="proposal.approved",
            subject_type="journal_proposal",
            subject_ref=proposal_v2,
            command_id=command_ids[5],
            correlation_id=descriptor.correlation_id,
            causation_event_id=prior(6),
            occurred_at="2026-07-13T10:00:00Z",
            actor=CONTROLLER,
            authorization=_authorization("HUMAN", "POL-APPROVAL-v1"),
            basis={
                "basis_type": "PROPOSAL_APPROVAL",
                "decision_maker": CONTROLLER,
                "sod_check_passed": True,
                "period_guard_state": "OPEN",
                "period_guard_passed": True,
            },
            payload={
                "proposal_ref": proposal_v2,
                "from_status": "SUBMITTED",
                "to_status": "APPROVED",
            },
            evidence=evidence[6],
        ),
        _event(
            event_id=event_ids[6],
            event_type="journal.posted",
            subject_type="journal_proposal",
            subject_ref=proposal_v2,
            command_id=command_ids[6],
            correlation_id=descriptor.correlation_id,
            causation_event_id=prior(7),
            occurred_at="2026-07-13T10:05:00Z",
            actor=POSTING_SERVICE,
            authorization=_authorization("SYSTEM_POLICY", "POL-POSTING-v1"),
            basis={
                "basis_type": "JOURNAL_POSTING",
                "proposal_ref": proposal_v2,
                "balance_debit_minor": descriptor.monthly_revenue_minor,
                "balance_credit_minor": descriptor.monthly_revenue_minor,
                "currency": descriptor.currency,
                "period_id": descriptor.correction_period_id,
                "period_state": "OPEN",
                "period_guard_passed": True,
            },
            payload={
                "proposal_ref": proposal_v2,
                "journal_id": descriptor.correction_journal_id,
                "entry_class": "RESTATEMENT_ADJUSTMENT",
                "from_status": "APPROVED",
                "to_status": "POSTED",
            },
            evidence=evidence[7],
            idempotency_key=f"post:{proposal_v2}",
        ),
        _event(
            event_id=event_ids[7],
            event_type="restatement.adjustment_linked",
            subject_type="restatement_case",
            subject_ref=descriptor.restatement_case_id,
            command_id=command_ids[7],
            correlation_id=descriptor.correlation_id,
            causation_event_id=prior(8),
            occurred_at="2026-07-13T10:15:00Z",
            actor=CONTROLLER,
            authorization=_authorization("HUMAN", "POL-RESTATEMENT-v1"),
            basis={
                "basis_type": "RESTATEMENT_LINK",
                "restatement_case_id": descriptor.restatement_case_id,
                "journal_id": descriptor.correction_journal_id,
                "entry_class": "RESTATEMENT_ADJUSTMENT",
                "class_check_passed": True,
            },
            payload={
                "restatement_case_id": descriptor.restatement_case_id,
                "journal_id": descriptor.correction_journal_id,
                "status": "PROPOSED",
            },
            evidence=evidence[8],
        ),
        _event(
            event_id=event_ids[8],
            event_type="restatement.adjustments_ready",
            subject_type="restatement_case",
            subject_ref=descriptor.restatement_case_id,
            command_id=command_ids[8],
            correlation_id=descriptor.correlation_id,
            causation_event_id=prior(9),
            occurred_at="2026-07-13T11:00:00Z",
            actor=CONTROLLER,
            authorization=_authorization("HUMAN", "POL-RESTATEMENT-v1"),
            basis={
                "basis_type": "RESTATEMENT_MANIFEST",
                "restatement_case_id": descriptor.restatement_case_id,
                "linked_journal_ids": (descriptor.correction_journal_id,),
                "manifest_hash": _hash("3"),
                "manifest_debit_minor": descriptor.monthly_revenue_minor,
                "manifest_credit_minor": descriptor.monthly_revenue_minor,
                "currency": descriptor.currency,
                "reconciles_to_journal_lines": True,
            },
            payload={
                "restatement_case_id": descriptor.restatement_case_id,
                "from_status": "PROPOSED",
                "to_status": "ADJUSTMENTS_READY",
            },
            evidence=evidence[9],
        ),
        _event(
            event_id=event_ids[9],
            event_type="restatement.approved",
            subject_type="restatement_case",
            subject_ref=descriptor.restatement_case_id,
            command_id=command_ids[9],
            correlation_id=descriptor.correlation_id,
            causation_event_id=prior(10),
            occurred_at="2026-07-13T14:00:00Z",
            actor=CFO,
            authorization=_authorization("HUMAN", "POL-RESTATEMENT-v1"),
            basis={
                "basis_type": "RESTATEMENT_APPROVAL",
                "restatement_case_id": descriptor.restatement_case_id,
                "manifest_hash": _hash("3"),
                "materiality_ref": {
                    "object_type": "materiality_assessment",
                    "object_id": "MAT-C001-001",
                },
                "disclosure_basis_ref": {
                    "object_type": "disclosure_basis",
                    "object_id": "DISC-C001-001",
                },
            },
            payload={
                "restatement_case_id": descriptor.restatement_case_id,
                "from_status": "ADJUSTMENTS_READY",
                "to_status": "APPROVED",
            },
            evidence=evidence[10],
        ),
        _event(
            event_id=event_ids[10],
            event_type="reporting_version.published",
            subject_type="restatement_case",
            subject_ref=descriptor.restatement_case_id,
            command_id=command_ids[10],
            correlation_id=descriptor.correlation_id,
            causation_event_id=prior(11),
            occurred_at="2026-07-14T09:00:00Z",
            actor=REPORTING_SERVICE,
            authorization=_authorization("SYSTEM_POLICY", "POL-PUBLICATION-v1"),
            basis={
                "basis_type": "REPORTING_PUBLICATION",
                "restatement_case_id": descriptor.restatement_case_id,
                "predecessor_version_ref": v1_ref,
                "manifest_hash": _hash("3"),
                "content_ref": str(v2_content.content_ref),
                "content_hash": str(v2_content.content_hash),
                "content_schema_version": 1,
                "publication_policy_ref": {
                    "object_type": "policy",
                    "object_id": "POL-PUBLICATION-v1",
                },
            },
            payload={
                "reporting_version_ref": v2_ref,
                "restatement_case_id": descriptor.restatement_case_id,
                "restatement_from_status": "APPROVED",
                "restatement_to_status": "PUBLISHED",
            },
            evidence=evidence[11],
            idempotency_key=f"publish:{v2_ref}",
        ),
    )
    business_evidence = _evidence(
        "EVD-C001-BE-001", "June recognition schedule source", _hash("a")
    )
    business_event = BusinessEvent.model_validate(
        {
            "contract_version": 1,
            "business_event_id": descriptor.business_event_id,
            "event_type": "accounting.recognition.due",
            "correlation_id": descriptor.correlation_id,
            "occurred_at": "2026-06-30T23:59:00Z",
            "recorded_at": "2026-07-03T08:55:00Z",
            "effective_date": descriptor.recognition_effective_date,
            "source_system": "REVENUE_SUBLEDGER",
            "legal_entity_id": descriptor.legal_entity_id,
            "payload": {
                "contract_ref": {
                    "object_type": "contract",
                    "object_id": descriptor.contract_id,
                },
                "recognition_schedule_ref": {
                    "object_type": "recognition_schedule",
                    "object_id": descriptor.recognition_schedule_id,
                },
                "service_period_start": descriptor.service_period_start,
                "service_period_end": descriptor.service_period_end,
                "amount_minor": descriptor.monthly_revenue_minor,
                "currency": descriptor.currency,
            },
            "evidence_refs": (business_evidence.model_dump(mode="python"),),
        }
    )
    rule_evidence = _evidence(
        "EVD-C001-RULE-001", "Approved recognition posting rule", _hash("1")
    )
    posting_rule = PostingRule(
        contract_version=1,
        posting_rule_id="PR-O2C-RECOG",
        rule_version=1,
        posting_rule_ref="PR-O2C-RECOG@v1",
        trigger_event_type="accounting.recognition.due",
        effective_from="2026-01-01",
        effective_to=None,
        status="ACTIVE",
        content_ref="rules://o2c/recognition/v1",
        content_hash=_hash("1"),
        content_schema_version=1,
        evidence_refs=(rule_evidence,),
    )
    deferred = _proposal(
        proposal_id=descriptor.proposal_id,
        proposal_version=1,
        status="DEFERRED",
        origin_type="AUTOMATED_POSTING",
        origin_basis={
            "business_event_ref": descriptor.business_event_id,
            "posting_rule_ref": "PR-O2C-RECOG@v1",
            "input_hashes": (_hash("a"),),
        },
        target_period_id=descriptor.reporting_period_id,
        effective_date=descriptor.recognition_effective_date,
        amount_minor=descriptor.monthly_revenue_minor,
        debit_account="ACC-DEFERRED-REVENUE",
        credit_account="ACC-SUBSCRIPTION-REVENUE",
        debit_customer=descriptor.customer_id,
        credit_customer=descriptor.customer_id,
        contract_id=descriptor.contract_id,
        legal_entity_id=descriptor.legal_entity_id,
        prepared_by=RULE_ENGINE,
        created_at="2026-07-03T08:56:00Z",
        submitted_at=str(events[0].occurred_at),
        evidence=evidence[1],
    )
    correction = _proposal(
        proposal_id=descriptor.proposal_id,
        proposal_version=2,
        status="POSTED",
        origin_type="RESTATEMENT_ADJUSTMENT",
        origin_basis={
            "restatement_case_id": descriptor.restatement_case_id,
            "restatement_policy_ref": {
                "object_type": "policy",
                "object_id": "POL-RESTATEMENT-v1",
            },
            "directive_ref": {
                "object_type": "remediation_directive",
                "object_id": "DIR-C001-001",
            },
            "predecessor_proposal_ref": proposal_v1,
            "input_hashes": (_hash("e"),),
        },
        target_period_id=descriptor.correction_period_id,
        effective_date=descriptor.correction_effective_date,
        amount_minor=descriptor.monthly_revenue_minor,
        debit_account="ACC-DEFERRED-REVENUE",
        credit_account="ACC-SUBSCRIPTION-REVENUE",
        debit_customer=descriptor.customer_id,
        credit_customer=descriptor.customer_id,
        contract_id=descriptor.contract_id,
        legal_entity_id=descriptor.legal_entity_id,
        prepared_by=CORRECTION_ENGINE,
        created_at="2026-07-13T08:55:00Z",
        submitted_at=str(events[4].occurred_at),
        evidence=evidence[5],
    )
    journal_package = _journal_package(
        correction,
        events[6],
        journal_id=descriptor.correction_journal_id,
        correction_basis={
            "restatement_case_id": descriptor.restatement_case_id,
            "directive_ref": {
                "object_type": "remediation_directive",
                "object_id": "DIR-C001-001",
            },
        },
    )
    restatements = tuple(
        _restatement_case(
            status=status,
            descriptor=descriptor,
            event=events[event_index],
            proposal_event=events[3],
            approval_event=events[9],
            journal_package=journal_package,
        )
        for status, event_index in (
            ("PROPOSED_EMPTY", 3),
            ("PROPOSED_LINKED", 7),
            ("ADJUSTMENTS_READY", 8),
            ("APPROVED", 9),
            ("PUBLISHED", 10),
        )
    )
    hard_period = _object(
        "accounting_period",
        {
            "contract_version": 1,
            "period_id": descriptor.reporting_period_id,
            "start_date": descriptor.service_period_start,
            "end_date": descriptor.service_period_end,
            "status": "HARD_CLOSED",
            "ledger_currency": descriptor.currency,
            "evidence_refs": tuple(
                item.model_dump(mode="python") for item in events[2].evidence_refs
            ),
            "hard_closed_at": events[2].occurred_at,
            "hard_close_event_id": events[2].event_id,
            "close_policy_ref": {
                "object_type": "policy",
                "object_id": "POL-CLOSE-v1",
            },
        },
    )
    reporting = _object(
        "reporting_version",
        {
            "contract_version": 1,
            "reporting_version_id": descriptor.reporting_version_id,
            "period_id": descriptor.reporting_period_id,
            "version": 2,
            "reporting_version_ref": v2_ref,
            "predecessor_version_ref": v1_ref,
            "restatement_case_id": descriptor.restatement_case_id,
            "content_ref": v2_content.content_ref,
            "content_hash": v2_content.content_hash,
            "content_schema_version": 1,
            "adjustment_manifest_hash": _hash("3"),
            "published_at": events[10].occurred_at,
            "published_by_event_id": events[10].event_id,
            "evidence_refs": tuple(
                item.model_dump(mode="python") for item in events[10].evidence_refs
            ),
        },
    )
    workflow = AccountingWorkflow(
        family="C001",
        correlation_id=descriptor.correlation_id,
        treatments=(
            ProposalTreatmentVersion.from_proposal(deferred),
            ProposalTreatmentVersion.from_proposal(correction),
        ),
        event_templates=events,
        creations=(
            EventCreations(str(events[2].event_id), (hard_period,)),
            EventCreations(
                str(events[3].event_id),
                (restatements[0],),
                ("PUB-G09-C001",),
            ),
            EventCreations(str(events[6].event_id), journal_package),
            EventCreations(str(events[7].event_id), (restatements[1],)),
            EventCreations(str(events[8].event_id), (restatements[2],)),
            EventCreations(str(events[9].event_id), (restatements[3],)),
            EventCreations(
                str(events[10].event_id), (reporting, restatements[4])
            ),
        ),
        business_event=business_event,
    )
    return BuiltScenario(
        scenario_ref=str(descriptor.scenario_ref),
        canonical_family="C-001",
        workflow=workflow,
        initial_snapshot=StateSnapshot(
            periods=(
                PeriodState(descriptor.reporting_period_id, "SOFT_CLOSED"),
                PeriodState(descriptor.correction_period_id, "OPEN"),
            ),
            business_event_ids=frozenset({descriptor.business_event_id}),
        ),
        evidence=_unique_evidence(business_event, posting_rule, *events),
        reporting_content=(v1_content, v2_content),
        posting_rule=posting_rule,
    )


def build_ct1_scenario(descriptor: CT1ScenarioDescriptor) -> BuiltScenario:
    """Construct CT-1 from typed correction parameters, never fixture rows."""

    reversal_ref = f"{descriptor.reversal_proposal_id}@v1"
    replacement_ref = f"{descriptor.replacement_proposal_id}@v1"
    referenced_source_body: dict[str, object] = {
        "contract_version": 1,
        "journal_id": descriptor.source_journal_id,
        "ledger_period_id": descriptor.correction_period_id,
        "currency": descriptor.currency,
        "line_tuples": (
            {
                "line_no": 1,
                "account_id": "ACC-UNAPPLIED-CASH",
                "debit_minor": descriptor.amount_minor,
                "credit_minor": 0,
                "currency": descriptor.currency,
                "dimensions": _dimensions(
                    descriptor.legal_entity_id,
                    customer_id=None,
                    contract_id=None,
                ),
            },
            {
                "line_no": 2,
                "account_id": "ACC-AR",
                "debit_minor": 0,
                "credit_minor": descriptor.amount_minor,
                "currency": descriptor.currency,
                "dimensions": _dimensions(
                    descriptor.legal_entity_id,
                    customer_id=descriptor.incorrect_customer_id,
                    contract_id=None,
                ),
            },
        ),
    }
    source_hash = canonical_sha256(referenced_source_body)
    evidence = {
        1: _evidence(
            "EVD-CT1-001", "Immutable J-010 reversal input snapshot", source_hash
        ),
        2: _evidence(
            "EVD-CT1-002", "Controller approval for J-010 reversal", _hash("7")
        ),
        3: _evidence(
            "EVD-CT1-003", "Validated J-011 posting package", _hash("8")
        ),
        4: _evidence(
            "EVD-CT1-004", "Correct Orion replacement proposal inputs", _hash("9")
        ),
        5: _evidence(
            "EVD-CT1-005", "Controller approval for Orion replacement", _hash("0")
        ),
        6: _evidence(
            "EVD-CT1-006", "Validated J-012 posting package", _hash("a")
        ),
    }
    event_ids = tuple(f"AE-CT1-{index:03d}" for index in range(1, 7))
    command_ids = tuple(f"CMD-CT1-{index:03d}" for index in range(1, 7))
    times = (
        "2026-07-11T09:00:00Z",
        "2026-07-11T09:30:00Z",
        "2026-07-11T09:31:00Z",
        "2026-07-11T09:40:00Z",
        "2026-07-11T10:00:00Z",
        "2026-07-11T10:01:00Z",
    )

    def submission(
        index: int,
        proposal_ref: str,
        policy: str,
        input_hash: str,
    ) -> AccountingEvent:
        return _event(
            event_id=event_ids[index],
            event_type="proposal.submitted",
            subject_type="journal_proposal",
            subject_ref=proposal_ref,
            command_id=command_ids[index],
            correlation_id=descriptor.correlation_id,
            causation_event_id=None if index == 0 else event_ids[index - 1],
            occurred_at=times[index],
            actor=CORRECTION_ENGINE,
            authorization=_authorization("SYSTEM_POLICY", policy),
            basis={
                "basis_type": "PROPOSAL_SUBMISSION",
                "derivation_authority": {
                    "authority_kind": "POLICY",
                    "authority_ref": policy,
                },
                "input_hashes": (input_hash,),
                "total_debit_minor": descriptor.amount_minor,
                "total_credit_minor": descriptor.amount_minor,
                "currency": descriptor.currency,
                "dimensions_resolved": True,
            },
            payload={
                "proposal_ref": proposal_ref,
                "from_status": "DRAFT",
                "to_status": "SUBMITTED",
            },
            evidence=evidence[index + 1],
        )

    def approval(index: int, proposal_ref: str) -> AccountingEvent:
        return _event(
            event_id=event_ids[index],
            event_type="proposal.approved",
            subject_type="journal_proposal",
            subject_ref=proposal_ref,
            command_id=command_ids[index],
            correlation_id=descriptor.correlation_id,
            causation_event_id=event_ids[index - 1],
            occurred_at=times[index],
            actor=CONTROLLER,
            authorization=_authorization("HUMAN", "POL-APPROVAL-v1"),
            basis={
                "basis_type": "PROPOSAL_APPROVAL",
                "decision_maker": CONTROLLER,
                "sod_check_passed": True,
                "period_guard_state": "OPEN",
                "period_guard_passed": True,
            },
            payload={
                "proposal_ref": proposal_ref,
                "from_status": "SUBMITTED",
                "to_status": "APPROVED",
            },
            evidence=evidence[index + 1],
        )

    def posting(
        index: int,
        proposal_ref: str,
        journal_id: str,
        entry_class: str,
    ) -> AccountingEvent:
        return _event(
            event_id=event_ids[index],
            event_type="journal.posted",
            subject_type="journal_proposal",
            subject_ref=proposal_ref,
            command_id=command_ids[index],
            correlation_id=descriptor.correlation_id,
            causation_event_id=event_ids[index - 1],
            occurred_at=times[index],
            actor=POSTING_SERVICE,
            authorization=_authorization("SYSTEM_POLICY", "POL-POSTING-v1"),
            basis={
                "basis_type": "JOURNAL_POSTING",
                "proposal_ref": proposal_ref,
                "balance_debit_minor": descriptor.amount_minor,
                "balance_credit_minor": descriptor.amount_minor,
                "currency": descriptor.currency,
                "period_id": descriptor.correction_period_id,
                "period_state": "OPEN",
                "period_guard_passed": True,
            },
            payload={
                "proposal_ref": proposal_ref,
                "journal_id": journal_id,
                "entry_class": entry_class,
                "from_status": "APPROVED",
                "to_status": "POSTED",
            },
            evidence=evidence[index + 1],
            idempotency_key=f"post:{proposal_ref}",
        )

    events = (
        submission(0, reversal_ref, "POL-REVERSAL-v1", source_hash),
        approval(1, reversal_ref),
        posting(2, reversal_ref, descriptor.reversal_journal_id, "REVERSAL"),
        submission(3, replacement_ref, "POL-CORRECTION-v1", _hash("9")),
        approval(4, replacement_ref),
        posting(5, replacement_ref, descriptor.replacement_journal_id, "REPLACEMENT"),
    )
    reversal = _proposal(
        proposal_id=descriptor.reversal_proposal_id,
        proposal_version=1,
        status="POSTED",
        origin_type="REVERSAL",
        origin_basis={
            "reverses_journal_id": descriptor.source_journal_id,
            "correction_policy_ref": {
                "object_type": "policy",
                "object_id": "POL-REVERSAL-v1",
            },
            "directive_ref": {
                "object_type": "remediation_directive",
                "object_id": "DIR-CT1-001",
            },
            "input_hashes": (source_hash,),
        },
        target_period_id=descriptor.correction_period_id,
        effective_date=descriptor.correction_effective_date,
        amount_minor=descriptor.amount_minor,
        debit_account="ACC-AR",
        credit_account="ACC-UNAPPLIED-CASH",
        debit_customer=descriptor.incorrect_customer_id,
        credit_customer=None,
        contract_id=None,
        legal_entity_id=descriptor.legal_entity_id,
        prepared_by=CORRECTION_ENGINE,
        created_at="2026-07-11T08:55:00Z",
        submitted_at=str(events[0].occurred_at),
        evidence=evidence[1],
    )
    replacement = _proposal(
        proposal_id=descriptor.replacement_proposal_id,
        proposal_version=1,
        status="POSTED",
        origin_type="REPLACEMENT",
        origin_basis={
            "corrects_journal_id": descriptor.source_journal_id,
            "correction_policy_ref": {
                "object_type": "policy",
                "object_id": "POL-CORRECTION-v1",
            },
            "directive_ref": {
                "object_type": "remediation_directive",
                "object_id": "DIR-CT1-001",
            },
            "input_hashes": (_hash("9"),),
        },
        target_period_id=descriptor.correction_period_id,
        effective_date=descriptor.correction_effective_date,
        amount_minor=descriptor.amount_minor,
        debit_account="ACC-UNAPPLIED-CASH",
        credit_account="ACC-AR",
        debit_customer=None,
        credit_customer=descriptor.correct_customer_id,
        contract_id=None,
        legal_entity_id=descriptor.legal_entity_id,
        prepared_by=CORRECTION_ENGINE,
        created_at="2026-07-11T09:35:00Z",
        submitted_at=str(events[3].occurred_at),
        evidence=evidence[4],
    )
    reversal_package = _journal_package(
        reversal,
        events[2],
        journal_id=descriptor.reversal_journal_id,
        correction_basis={"reverses_journal_id": descriptor.source_journal_id},
    )
    replacement_package = _journal_package(
        replacement,
        events[5],
        journal_id=descriptor.replacement_journal_id,
        correction_basis={
            "corrects_journal_id": descriptor.source_journal_id,
            "directive_ref": {
                "object_type": "remediation_directive",
                "object_id": "DIR-CT1-001",
            },
        },
    )
    referenced = ReferencedJournalProjection(
        fixture_id="DEMO-REF-CT1-J010",
        projection_type="referenced_journal_projection",
        projection_version=1,
        authored_by_f=False,
        source_hash=source_hash,
        journal_id=descriptor.source_journal_id,
        ledger_period_id=descriptor.correction_period_id,
        currency=descriptor.currency,
        line_tuples=referenced_source_body["line_tuples"],
    )
    workflow = AccountingWorkflow(
        family="CT1",
        correlation_id=descriptor.correlation_id,
        treatments=(
            ProposalTreatmentVersion.from_proposal(reversal),
            ProposalTreatmentVersion.from_proposal(replacement),
        ),
        event_templates=events,
        creations=(
            EventCreations(
                str(events[2].event_id),
                reversal_package,
                ("PUB-G09-CT1",),
            ),
            EventCreations(
                str(events[5].event_id),
                replacement_package,
                ("PUB-G09-CT1",),
            ),
        ),
    )
    return BuiltScenario(
        scenario_ref=str(descriptor.scenario_ref),
        canonical_family="CT-1",
        workflow=workflow,
        initial_snapshot=StateSnapshot(
            periods=(PeriodState(descriptor.correction_period_id, "OPEN"),),
            posted_journal_ids=frozenset({descriptor.source_journal_id}),
            referenced_journals=(referenced,),
        ),
        evidence=_unique_evidence(*events),
        referenced_journal=referenced,
        referenced_source_body=referenced_source_body,
    )
