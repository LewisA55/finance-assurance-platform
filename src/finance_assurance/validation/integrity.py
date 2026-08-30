"""Pure referential and accounting integrity predicates for H2."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from finance_assurance.validation.contracts.objects import BusinessEvent
from finance_assurance.validation.index import ValidatedCorpusIndex, ValidatedRecord
from finance_assurance.validation.proofs import (
    ReferencedJournalProjection,
    ReportingContentProof,
)


@dataclass(frozen=True, slots=True)
class IntegrityViolation(ValueError):
    code: str
    reason: str

    def __str__(self) -> str:
        return f"{self.code}: {self.reason}"


def records_of(index: ValidatedCorpusIndex, contract_key: str) -> tuple[ValidatedRecord, ...]:
    return tuple(record for record in index.objects if record.contract_key == contract_key)


def model_by(index: ValidatedCorpusIndex, contract_key: str, field: str, value: str) -> BaseModel:
    matches = [
        record.value
        for record in index.canonical_objects
        if record.contract_key == contract_key
        if getattr(record.value, field) == value
    ]
    if len(matches) != 1:
        raise IntegrityViolation("REFERENCE_INTEGRITY", f"expected one {contract_key} {value}")
    return matches[0]


def assert_causal_order(index: ValidatedCorpusIndex) -> int:
    checked = 0
    for trace in (index.c001_events, index.ct1_events):
        prior_id: str | None = None
        correlation = str(trace[0].value.correlation_id)
        for record in trace:
            event = record.value
            if event.correlation_id != correlation:
                raise IntegrityViolation("CAUSAL_ORDER", "correlation changed inside trace")
            if event.causation_event_id != prior_id:
                raise IntegrityViolation(
                    "CAUSAL_ORDER",
                    f"{event.event_id} does not name its immediately "
                    "causal predecessor",
                )
            prior_id = str(event.event_id)
            checked += 1
    return checked


def assert_balances(index: ValidatedCorpusIndex) -> tuple[int, int, int]:
    proposals = records_of(index, "journal_proposal")
    journals = records_of(index, "journal_entry")
    lines = records_of(index, "journal_line")
    lines_by_journal: dict[str, list[BaseModel]] = {}
    for record in lines:
        lines_by_journal.setdefault(str(record.value.journal_id), []).append(record.value)

    for record in proposals:
        proposal = record.value
        debit = sum(line.debit_minor for line in proposal.proposed_lines)
        credit = sum(line.credit_minor for line in proposal.proposed_lines)
        if not (
            debit == credit == proposal.total_debit_minor == proposal.total_credit_minor
            and proposal.ledger_currency == "GBP"
            and all(line.currency == "GBP" for line in proposal.proposed_lines)
        ):
            raise IntegrityViolation("BALANCE_INTEGRITY", f"proposal {proposal.proposal_ref} failed")

    for record in journals:
        journal = record.value
        journal_lines = lines_by_journal.get(str(journal.journal_id), [])
        debit = sum(line.debit_minor for line in journal_lines)
        credit = sum(line.credit_minor for line in journal_lines)
        refs = tuple(line.journal_line_id for line in sorted(journal_lines, key=lambda item: item.line_no))
        if not (
            debit == credit == journal.total_debit_minor == journal.total_credit_minor
            and refs == journal.line_refs
            and journal.currency == "GBP"
            and all(line.currency == "GBP" for line in journal_lines)
        ):
            raise IntegrityViolation("BALANCE_INTEGRITY", f"journal {journal.journal_id} failed")

    posted = tuple(record for record in index.events if record.contract_key == "journal.posted")
    for record in posted:
        event = record.value
        if not (
            event.basis.balance_debit_minor == event.basis.balance_credit_minor
            and event.basis.currency == "GBP"
        ):
            raise IntegrityViolation("BALANCE_INTEGRITY", f"posted event {event.event_id} failed")
    return len(proposals), len(journals), len(posted)


def is_posting_rule_input(candidate: object) -> bool:
    """Enforce the two-stream firewall structurally by object class."""

    return isinstance(candidate, BusinessEvent)


def assert_posting_firewall(index: ValidatedCorpusIndex) -> tuple[int, int]:
    business_events = records_of(index, "business_event")
    eligible = [record for record in business_events if is_posting_rule_input(record.value)]
    accounting_events = [record for record in index.events if is_posting_rule_input(record.value)]
    if len(eligible) != 1 or accounting_events:
        raise IntegrityViolation("EVENT_STREAM_FIREWALL", "posting input boundary was crossed")
    return len(eligible), len(index.events)


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="python", round_trip=True)


def assert_manifest_integrity(index: ValidatedCorpusIndex, case: Mapping[str, Any] | None = None) -> int:
    rc = model_by(index, "restatement_case", "restatement_case_id", "RC-001")
    body = dict(case) if case is not None else _dump(rc)
    journal = model_by(index, "journal_entry", "journal_id", "J-560")
    line_models = {
        str(record.value.journal_line_id): record.value
        for record in records_of(index, "journal_line")
        if record.value.journal_id == "J-560"
    }
    manifest = body["adjustment_manifest"]
    if not isinstance(manifest, Sequence):
        raise IntegrityViolation("MANIFEST_INTEGRITY", "manifest is not a sequence")
    for entry in manifest:
        if not isinstance(entry, Mapping):
            raise IntegrityViolation("MANIFEST_INTEGRITY", "manifest entry is not an object")
        line = line_models.get(str(entry.get("journal_line_ref")))
        if line is None:
            raise IntegrityViolation("MANIFEST_INTEGRITY", "manifest line reference is unresolved")
        for field in ("account_id", "debit_minor", "credit_minor", "currency"):
            if entry.get(field) != getattr(line, field):
                raise IntegrityViolation("MANIFEST_INTEGRITY", f"manifest differs from J-560 at {field}")
    ready = next(record.value for record in index.c001_events if record.contract_key == "restatement.adjustments_ready")
    reporting = model_by(index, "reporting_version", "reporting_version_ref", "RV-2026-06@v2")
    hashes = {body.get("manifest_hash"), ready.basis.manifest_hash, reporting.adjustment_manifest_hash}
    if len(hashes) != 1 or None in hashes:
        raise IntegrityViolation("MANIFEST_INTEGRITY", "manifest hash chain diverges")
    debit = sum(int(entry["debit_minor"]) for entry in manifest)
    credit = sum(int(entry["credit_minor"]) for entry in manifest)
    if not (
        debit == credit == journal.total_debit_minor == journal.total_credit_minor
        and debit == ready.basis.manifest_debit_minor
        and credit == ready.basis.manifest_credit_minor
    ):
        raise IntegrityViolation("MANIFEST_INTEGRITY", "manifest totals do not reconcile")
    return len(manifest)


def assert_reversal_integrity(
    index: ValidatedCorpusIndex,
    projection: ReferencedJournalProjection,
) -> int:
    proposal = model_by(index, "journal_proposal", "proposal_ref", "P-REV-010@v1")
    if projection.source_hash != proposal.origin_basis.input_hashes[0]:
        raise IntegrityViolation("REVERSAL_BINDING", "projection hash is not the declared reversal input")

    journal = model_by(index, "journal_entry", "journal_id", "J-011")
    journal_lines = tuple(
        record.value
        for record in records_of(index, "journal_line")
        if record.value.journal_id == journal.journal_id
    )

    def identity(line: Any) -> tuple[object, ...]:
        dimensions = line.dimensions
        return (
            line.account_id,
            dimensions.legal_entity_id,
            dimensions.customer_id,
            dimensions.contract_id,
            line.currency,
        )

    reversal_by_identity = {identity(line): line for line in journal_lines}
    if len(reversal_by_identity) != len(journal_lines):
        raise IntegrityViolation("REVERSAL_INTEGRITY", "reversal identity is duplicated")
    if len(journal_lines) != len(projection.line_tuples):
        raise IntegrityViolation("REVERSAL_INTEGRITY", "reversal line count differs")
    for source in projection.line_tuples:
        reversal = reversal_by_identity.get(identity(source))
        if reversal is None:
            raise IntegrityViolation("REVERSAL_INTEGRITY", "reversal identity differs")
        opposite = (
            source.debit_minor == reversal.credit_minor
            and source.credit_minor == reversal.debit_minor
        )
        if not opposite:
            raise IntegrityViolation("REVERSAL_INTEGRITY", "J-011 is not equal and opposite")
    return len(journal_lines)


def assert_restatement_state_guards(index: ValidatedCorpusIndex) -> int:
    statuses = [str(record.value.status) for record in records_of(index, "restatement_case")]
    expected = ["PUBLISHED", "PROPOSED", "PROPOSED", "ADJUSTMENTS_READY", "APPROVED"]
    if statuses != expected:
        raise IntegrityViolation("RESTATEMENT_STATE", "exercised snapshot states changed")
    return len(statuses)


def assert_open_ledger_period(
    index: ValidatedCorpusIndex,
    journal: Mapping[str, Any] | None = None,
) -> str:
    j560 = model_by(index, "journal_entry", "journal_id", "J-560")
    body = dict(journal) if journal is not None else _dump(j560)
    period_id = str(body["ledger_period_id"])
    period = model_by(index, "accounting_period", "period_id", period_id)
    if period.status != "OPEN":
        raise IntegrityViolation("HARD_CLOSED_PERIOD", "J-560 ledger period is not open")
    return period_id


def assert_manifest_scope(index: ValidatedCorpusIndex, case: Mapping[str, Any] | None = None) -> int:
    rc = model_by(index, "restatement_case", "restatement_case_id", "RC-001")
    body = dict(case) if case is not None else _dump(rc)
    scope = set(body["scope_period_ids"])
    manifest = body["adjustment_manifest"]
    outside = [entry["presented_period_id"] for entry in manifest if entry["presented_period_id"] not in scope]
    if outside:
        raise IntegrityViolation("RESTATEMENT_SCOPE", f"presented periods outside scope: {outside}")
    return len(manifest)


def assert_hard_close_counts(event: Mapping[str, Any]) -> None:
    basis = event["basis"]
    if basis["unresolved_submitted_count"] != 0:
        raise IntegrityViolation("UNRESOLVED_SUBMITTED_CLOSE", "submitted proposals remain")
    if basis["unresolved_approved_count"] != 0:
        raise IntegrityViolation("UNRESOLVED_APPROVED_CLOSE", "approved proposals remain")


def assert_sod(event: Mapping[str, Any]) -> None:
    if event["basis"]["sod_check_passed"] is not True:
        raise IntegrityViolation("SOD_VIOLATION", "segregation-of-duties check failed")


def assert_reporting_bridge(
    index: ValidatedCorpusIndex,
    v1: ReportingContentProof,
    v2: ReportingContentProof,
) -> int:
    old = v1.canonical_body
    new = v2.canonical_body
    adjustment = 1_000_000
    if not (
        old.currency == new.currency == "GBP"
        and old.presented_period_id == new.presented_period_id == "2026-06"
        and new.subscription_revenue_minor == old.subscription_revenue_minor + adjustment
        and new.deferred_revenue_minor == old.deferred_revenue_minor - adjustment
    ):
        raise IntegrityViolation("REPORTING_BRIDGE", "June v1-to-v2 arithmetic failed")

    reporting = model_by(index, "reporting_version", "reporting_version_ref", "RV-2026-06@v2")
    publication = next(
        record.value
        for record in index.c001_events
        if record.contract_key == "reporting_version.published"
    )
    rc = model_by(index, "restatement_case", "restatement_case_id", "RC-001")
    june = model_by(index, "accounting_period", "period_id", "2026-06")
    j560 = model_by(index, "journal_entry", "journal_id", "J-560")
    manifest_by_account = {
        entry.account_id: entry for entry in rc.adjustment_manifest
    }
    deferred = manifest_by_account.get("ACC-DEFERRED-REVENUE")
    revenue = manifest_by_account.get("ACC-SUBSCRIPTION-REVENUE")
    if not (
        reporting.predecessor_version_ref == old.reporting_version_ref
        and reporting.reporting_version_ref == new.reporting_version_ref
        and reporting.content_ref == v2.content_ref
        and reporting.content_hash == v2.content_hash
        and reporting.content_schema_version == v2.content_schema_version
        and reporting.published_by_event_id == publication.event_id
        and publication.basis.predecessor_version_ref
        == old.reporting_version_ref
        and publication.basis.manifest_hash == reporting.adjustment_manifest_hash
        and publication.basis.content_ref == v2.content_ref
        and publication.basis.content_hash == v2.content_hash
        and publication.basis.content_schema_version == v2.content_schema_version
        and publication.payload.reporting_version_ref
        == reporting.reporting_version_ref
        and tuple(rc.published_version_refs) == (new.reporting_version_ref,)
        and june.status == "HARD_CLOSED"
        and j560.ledger_period_id == "2026-07"
        and old.reporting_version_ref != new.reporting_version_ref
        and deferred is not None
        and deferred.debit_minor == adjustment
        and deferred.credit_minor == 0
        and revenue is not None
        and revenue.debit_minor == 0
        and revenue.credit_minor == adjustment
    ):
        raise IntegrityViolation("REPORTING_BRIDGE", "version preservation or lineage failed")
    assert_manifest_integrity(index)
    return adjustment
