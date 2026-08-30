"""Artifact I exact reads, labelled projections, and authority-derived trace graph."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Literal

from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.digests import value_digest
from finance_assurance.runtime.persistence.models import (
    ExactStoredRecord,
    QueryContext,
)
from finance_assurance.runtime.persistence.ports import (
    PersistenceBoundary,
    QuerySession,
)


class ReadModelError(ValueError):
    """Raised when an exact read cannot satisfy the ratified semantic contract."""


@dataclass(frozen=True, slots=True)
class ExactVersionRead:
    """One immutable authoritative version from a pinned query revision."""

    record: ExactStoredRecord
    revision: int

    @property
    def body(self) -> object:
        return self.record.semantic_body()


@dataclass(frozen=True, slots=True)
class LabelledCurrentProjection:
    """Disposable current state that cannot be mistaken for an exact version."""

    projection_family: Literal["J-P02", "J-P04", "J-P06"]
    subject_type: Literal["journal_proposal", "accounting_period", "restatement_case"]
    subject_ref: str
    exactness_token: str
    state_label: str
    projection_hash: str
    value: object
    label: Literal["CURRENT_REBUILDABLE"] = "CURRENT_REBUILDABLE"


@dataclass(frozen=True, slots=True)
class ExactProposalRead:
    treatment: ExactVersionRead
    state_publication: ExactVersionRead
    lifecycle_evidence: tuple[ExactVersionRead, ...]
    state_token: str
    state_label: str
    artifact_f_view: dict[str, object]


@dataclass(frozen=True, slots=True)
class ExactAccountingPeriodRead:
    state_publication: ExactVersionRead
    lifecycle_evidence: tuple[ExactVersionRead, ...]
    state_token: str
    state_label: str
    artifact_f_view: dict[str, object]


@dataclass(frozen=True, slots=True)
class ExactRestatementCaseRead:
    state_publication: ExactVersionRead
    lifecycle_evidence: tuple[ExactVersionRead, ...]
    state_token: str
    state_label: str
    artifact_f_view: dict[str, object]


@dataclass(frozen=True, slots=True)
class ExactJournalRead:
    header: ExactVersionRead
    ordered_lines: tuple[ExactVersionRead, ...]


@dataclass(frozen=True, slots=True)
class ReportingHistoryRead:
    period_id: str
    versions: tuple[ExactVersionRead, ...]


VerificationStatus = Literal["CONTENT_BYTES_VERIFIED", "DECLARED_HASH_ONLY"]


@dataclass(frozen=True, slots=True)
class ResolvedReportingContent:
    content_ref: str
    declared_content_hash: str
    verification_status: VerificationStatus
    proof: ExactVersionRead | None
    canonical_body: object | None


@dataclass(frozen=True, slots=True)
class ReadinessRead:
    product: ExactVersionRead
    reporting_version_ref: str
    purpose_ref: str
    period_id: str
    scope_ref: str
    status: str


@dataclass(frozen=True, slots=True)
class ControlledPlanningInputRead:
    planning_input: ExactVersionRead
    readiness: ReadinessRead
    reporting_version: ExactVersionRead


TraceRole = Literal[
    "reporting_version",
    "reporting_content",
    "restatement_case",
    "accounting_event",
    "journal",
    "proposal",
    "posting_rule",
    "business_event",
    "evidence",
    "source_reference",
    "authority",
]


@dataclass(frozen=True, slots=True)
class TraceNode:
    node_ref: str
    role: TraceRole
    record_family: str
    record_identity: str
    semantic_hash: str | None


@dataclass(frozen=True, slots=True)
class TraceEdge:
    source_ref: str
    target_ref: str
    relationship: str


@dataclass(frozen=True, slots=True)
class ReportingValueTrace:
    reporting_version_ref: str
    statement_field: str
    statement_value_minor: int
    currency: str
    content_verification_status: VerificationStatus
    query_revision: int
    nodes: tuple[TraceNode, ...]
    edges: tuple[TraceEdge, ...]

    @property
    def semantic_digest(self) -> str:
        return value_digest(
            (
                self.reporting_version_ref,
                self.statement_field,
                self.statement_value_minor,
                self.currency,
                self.content_verification_status,
                self.nodes,
                self.edges,
            )
        )


@dataclass(frozen=True, slots=True)
class CandidateReceiptRead:
    receipt: ExactVersionRead
    admission_result: ExactVersionRead
    publication: ExactVersionRead
    outcome: str
    eligible_for_g01: bool


def _body(record: ExactStoredRecord) -> dict[str, object]:
    value = record.semantic_body()
    return value if isinstance(value, dict) else {}


def _product_body(record: ExactStoredRecord) -> dict[str, object]:
    outer = _body(record)
    nested = outer.get("canonical_body")
    return nested if isinstance(nested, dict) else outer


def _record_role(record: ExactStoredRecord) -> TraceRole:
    body = _body(record)
    if record.record_family == "J-AR10" or "reporting_version_ref" in body:
        return "reporting_version"
    if record.record_family == "J-AR12" and "content_ref" in body:
        return "reporting_content"
    if record.record_family == "J-AR02" and "restatement_case_id" in body:
        return "restatement_case"
    if record.record_family == "J-AR06":
        return "accounting_event"
    if record.record_family == "J-AR08":
        return "journal"
    if record.record_family == "J-AR05":
        return "proposal"
    if record.record_family == "J-AR04" and "posting_rule_ref" in body:
        return "posting_rule"
    if record.record_family == "J-AR03" or "business_event_id" in body:
        return "business_event"
    if record.record_family == "J-AR12":
        return "evidence"
    return "authority"


@dataclass(frozen=True, slots=True)
class _ReferenceSpec:
    relationship: str
    target: str
    expected_families: frozenset[str]
    unresolved_role: TraceRole | None = None


def _evidence_ids(value: object) -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, dict):
        evidence = value.get("evidence_refs")
        if isinstance(evidence, (list, tuple)):
            for item in evidence:
                if isinstance(item, dict) and isinstance(item.get("ref_id"), str):
                    found.append(str(item["ref_id"]))
        for item in value.values():
            if isinstance(item, (dict, list, tuple)):
                found.extend(_evidence_ids(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            if isinstance(item, (dict, list, tuple)):
                found.extend(_evidence_ids(item))
    return tuple(dict.fromkeys(found))


def _opaque_id(value: object) -> str | None:
    return str(value["object_id"]) if isinstance(value, dict) and isinstance(
        value.get("object_id"), str
    ) else None


def _record_references(record: ExactStoredRecord) -> tuple[_ReferenceSpec, ...]:
    """Return only ratified upstream relationships for one authority record."""

    body = _body(record)
    specs: list[_ReferenceSpec] = []

    def required(relationship: str, target: object, family: str) -> None:
        if isinstance(target, str) and target:
            specs.append(
                _ReferenceSpec(relationship, target, frozenset({family}))
            )

    def external(
        relationship: str,
        target: object,
        role: TraceRole,
        *families: str,
    ) -> None:
        if isinstance(target, str) and target:
            specs.append(
                _ReferenceSpec(
                    relationship,
                    target,
                    frozenset(families),
                    role,
                )
            )

    if record.record_family == "J-AR10":
        required("published_by_event_id", body.get("published_by_event_id"), "J-AR06")
        required("content_ref", body.get("content_ref"), "J-AR12")
        required(
            "predecessor_version_ref",
            body.get("predecessor_version_ref"),
            "J-AR10",
        )
    elif record.record_family == "J-AR06":
        required("causation_event_id", body.get("causation_event_id"), "J-AR06")
        subject = body.get("subject_ref")
        if (
            isinstance(subject, dict)
            and subject.get("object_type") == "journal_proposal"
        ):
            required("subject_ref.object_ref", subject.get("object_ref"), "J-AR05")
        payload = body.get("payload")
        if isinstance(payload, dict):
            required("payload.journal_id", payload.get("journal_id"), "J-AR08")
        basis = body.get("basis")
        if isinstance(basis, dict):
            authority = basis.get("derivation_authority")
            if isinstance(authority, dict) and authority.get("authority_kind") == (
                "POSTING_RULE"
            ):
                required(
                    "basis.derivation_authority.authority_ref",
                    authority.get("authority_ref"),
                    "J-AR04",
                )
    elif record.record_family == "J-AR08":
        required("source_proposal_ref", body.get("source_proposal_ref"), "J-AR05")
        for index, line_ref in enumerate(body.get("line_refs", ())):
            required(f"line_refs[{index}]", line_ref, "J-AR08")
        correction = body.get("correction_basis")
        if isinstance(correction, dict):
            required(
                "correction_basis.reverses_journal_id",
                correction.get("reverses_journal_id"),
                "J-AR08",
            )
            required(
                "correction_basis.corrects_journal_id",
                correction.get("corrects_journal_id"),
                "J-AR08",
            )
    elif record.record_family == "J-AR05":
        origin = body.get("origin_basis")
        if isinstance(origin, dict):
            required(
                "origin_basis.business_event_ref",
                origin.get("business_event_ref"),
                "J-AR03",
            )
            required(
                "origin_basis.posting_rule_ref",
                origin.get("posting_rule_ref"),
                "J-AR04",
            )
            required(
                "origin_basis.predecessor_proposal_ref",
                origin.get("predecessor_proposal_ref"),
                "J-AR05",
            )
            required(
                "origin_basis.reverses_journal_id",
                origin.get("reverses_journal_id"),
                "J-AR08",
            )
            required(
                "origin_basis.corrects_journal_id",
                origin.get("corrects_journal_id"),
                "J-AR08",
            )
            for key in (
                "correction_policy_ref",
                "restatement_policy_ref",
                "directive_ref",
            ):
                external(
                    f"origin_basis.{key}",
                    _opaque_id(origin.get(key)),
                    "authority",
                    "J-AR02",
                    "J-AR04",
                )
    elif record.record_family == "J-AR04":
        external(
            "content_ref",
            body.get("content_ref"),
            "source_reference",
            "J-AR12",
        )
    elif record.record_family == "J-AR03":
        external("source_system", body.get("source_system"), "source_reference")
        payload = body.get("payload")
        if isinstance(payload, dict):
            for key in ("contract_ref", "recognition_schedule_ref"):
                external(
                    f"payload.{key}",
                    _opaque_id(payload.get(key)),
                    "source_reference",
                    "J-AR01",
                    "J-AR02",
                )
    elif record.record_family == "J-AR02" and "restatement_case_id" in body:
        for index, journal_id in enumerate(body.get("linked_journal_ids", ())):
            required(f"linked_journal_ids[{index}]", journal_id, "J-AR08")
        for index, entry in enumerate(body.get("adjustment_manifest", ())):
            if isinstance(entry, dict):
                required(
                    f"adjustment_manifest[{index}].journal_line_ref",
                    entry.get("journal_line_ref"),
                    "J-AR08",
                )
                external(
                    f"adjustment_manifest[{index}].basis_ref",
                    _opaque_id(entry.get("basis_ref")),
                    "authority",
                    "J-AR04",
                )

    for index, evidence_ref in enumerate(_evidence_ids(body)):
        external(
            f"evidence_refs[{index}]",
            evidence_ref,
            "evidence",
            "J-AR12",
        )
    return tuple(specs)


def _aliases(record: ExactStoredRecord) -> frozenset[str]:
    body = _body(record)
    values = {
        record.record_identity,
        f"{record.record_family}:{record.record_identity}",
    }
    for key in (
        "business_event_id",
        "event_id",
        "journal_id",
        "journal_line_id",
        "proposal_ref",
        "posting_rule_ref",
        "reporting_version_ref",
        "product_ref",
        "publication_ref",
        "case_id",
        "restatement_case_id",
    ):
        candidate = body.get(key)
        if isinstance(candidate, str):
            values.add(candidate)
    nested = body.get("canonical_body")
    if isinstance(nested, dict) and isinstance(nested.get("product_ref"), str):
        values.add(str(nested["product_ref"]))
    return frozenset(values)


class RuntimeQueryService:
    """Programmatic Phase 6 read boundary over one pinned semantic time."""

    def __init__(
        self,
        boundary: PersistenceBoundary,
        *,
        semantic_as_of_time: str,
    ) -> None:
        if not semantic_as_of_time:
            raise ValueError("semantic_as_of_time is required")
        self._query = boundary.open_query(
            QueryContext(semantic_as_of_time=semantic_as_of_time)
        )

    @classmethod
    def from_session(cls, session: QuerySession) -> RuntimeQueryService:
        """Bind all semantic reads to one already-pinned query revision."""

        instance = cls.__new__(cls)
        instance._query = session
        return instance

    @property
    def query_revision(self) -> int:
        return self._query.revision

    def _session(self) -> QuerySession:
        return self._query

    def get_exact(
        self, record_family: str, record_identity: str
    ) -> ExactVersionRead | None:
        session = self._session()
        record = session.authoritative_record(record_family, record_identity)
        return None if record is None else ExactVersionRead(record, session.revision)

    def get_command_result(self, command_id: str) -> ExactVersionRead | None:
        return self.get_exact("J-AR14", command_id)

    def get_command_disposition(self, command_id: str) -> ExactVersionRead | None:
        return self.get_exact("J-AR16", command_id)

    def get_candidate_receipt(self, candidate_ref: str) -> CandidateReceiptRead | None:
        session = self._session()
        receipt = session.authoritative_record("J-AR01", candidate_ref)
        if receipt is None:
            return None
        products = tuple(
            item
            for item in session.authoritative_records("J-AR02")
            if _body(item).get("product_discriminator")
            == "hermes.business_event_admission_result"
            and _product_body(item).get("candidate_receipt_ref") == candidate_ref
        )
        if len(products) != 1:
            raise ReadModelError(
                "candidate receipt does not resolve one exact admission result"
            )
        product = products[0]
        product_body = _product_body(product)
        publications = tuple(
            item
            for item in session.authoritative_records("J-AR13")
            if _body(item).get("contract_id") == "G-02"
            and _body(item).get("product_ref") == product_body.get("product_ref")
            and _body(item).get("canonical_payload") == product_body
        )
        if len(publications) != 1:
            raise ReadModelError(
                "candidate receipt does not resolve one exact G-02 publication"
            )
        return CandidateReceiptRead(
            receipt=ExactVersionRead(receipt, session.revision),
            admission_result=ExactVersionRead(product, session.revision),
            publication=ExactVersionRead(publications[0], session.revision),
            outcome=str(product_body["outcome"]),
            eligible_for_g01=bool(product_body["eligible_for_g01"]),
        )

    def get_business_event(self, event_id: str) -> ExactVersionRead | None:
        return self.get_exact("J-AR03", event_id)

    def get_posting_rule(self, rule_ref: str) -> ExactVersionRead | None:
        return self.get_exact("J-AR04", rule_ref)

    def _get_module_product(
        self,
        product_ref: str,
        permitted_discriminators: frozenset[str],
    ) -> ExactVersionRead | None:
        exact = self.get_exact("J-AR02", product_ref)
        if exact is None or not isinstance(exact.body, dict):
            return None
        if exact.body.get("product_discriminator") not in permitted_discriminators:
            return None
        return exact

    def get_admission_result(self, product_ref: str) -> ExactVersionRead | None:
        return self._get_module_product(
            product_ref,
            frozenset({"hermes.business_event_admission_result"}),
        )

    def get_recognition_reconciliation(
        self, product_ref: str
    ) -> ExactVersionRead | None:
        return self._get_module_product(
            product_ref,
            frozenset(
                {
                    "hermes.recognition_population_reconciliation",
                    "hermes.cash_application_identity_reconciliation",
                }
            ),
        )

    def get_assurance_result(self, product_ref: str) -> ExactVersionRead | None:
        return self._get_module_product(
            product_ref,
            frozenset(
                {
                    "argus.recognition_completeness_test_run",
                    "argus.recognition_completeness_exception",
                    "argus.cash_application_identity_test_run",
                    "argus.cash_application_identity_exception",
                    "argus.restatement_verification",
                    "argus.cash_application_correction_verification",
                }
            ),
        )

    def get_governance_issue(self, product_ref: str) -> ExactVersionRead | None:
        return self._get_module_product(
            product_ref,
            frozenset(
                {
                    "aegis.exception_review",
                    "aegis.finding",
                    "aegis.issue",
                }
            ),
        )

    def get_remediation_directive(
        self, product_ref: str
    ) -> ExactVersionRead | None:
        return self._get_module_product(
            product_ref,
            frozenset({"aegis.remediation_directive"}),
        )

    def get_planning_input_snapshot(
        self, product_ref: str
    ) -> ExactVersionRead | None:
        return self._get_module_product(
            product_ref,
            frozenset({"pythia.planning_input_snapshot"}),
        )

    def get_governed_decision(self, product_ref: str) -> ExactVersionRead | None:
        return self._get_module_product(
            product_ref,
            frozenset({"pythia.governed_decision"}),
        )

    def _current(
        self,
        subject_type: Literal[
            "journal_proposal", "accounting_period", "restatement_case"
        ],
        subject_ref: str,
    ) -> LabelledCurrentProjection | None:
        state = self._session().state().snapshot
        family: Literal["J-P02", "J-P04", "J-P06"]
        if subject_type == "journal_proposal":
            value = state.proposal(subject_ref)
            family = "J-P02"
        elif subject_type == "accounting_period":
            value = state.period(subject_ref)
            family = "J-P04"
        else:
            value = state.restatement(subject_ref)
            family = "J-P06"
        if value is None:
            return None
        events = self._lifecycle_events(subject_type, subject_ref)
        token = (
            events[-1].record.record_identity
            if events
            else f"BASELINE:{value_digest(value)}"
        )
        return LabelledCurrentProjection(
            projection_family=family,
            subject_type=subject_type,
            subject_ref=subject_ref,
            exactness_token=token,
            state_label=str(value.status),
            projection_hash=value_digest(value),
            value=value,
        )

    def get_current_journal_proposal(
        self, proposal_ref: str
    ) -> LabelledCurrentProjection | None:
        return self._current("journal_proposal", proposal_ref)

    def get_current_accounting_period(
        self, period_id: str
    ) -> LabelledCurrentProjection | None:
        return self._current("accounting_period", period_id)

    def get_current_restatement_case(
        self, case_id: str
    ) -> LabelledCurrentProjection | None:
        return self._current("restatement_case", case_id)

    def _lifecycle_events(
        self,
        subject_type: Literal[
            "journal_proposal", "accounting_period", "restatement_case"
        ],
        subject_ref: str,
        *,
        through_token: str | None = None,
    ) -> tuple[ExactVersionRead, ...]:
        session = self._session()
        matches: list[ExactStoredRecord] = []
        for record in session.authoritative_records("J-AR06"):
            body = _body(record)
            subject = body.get("subject_ref")
            if not isinstance(subject, dict):
                continue
            if (
                subject.get("object_type") == subject_type
                and subject.get("object_ref") == subject_ref
            ):
                matches.append(record)
        matches.sort(
            key=lambda item: (
                str(_body(item).get("recorded_at", "")),
                item.record_identity,
            )
        )
        if through_token is not None:
            positions = [
                index
                for index, item in enumerate(matches)
                if item.record_identity == through_token
            ]
            if len(positions) != 1:
                raise ReadModelError(
                    "named lifecycle state token is absent or ambiguous"
                )
            matches = matches[: positions[0] + 1]
        return tuple(ExactVersionRead(item, session.revision) for item in matches)

    def _exact_g04_view(
        self,
        *,
        body_discriminator: str,
        product_ref: str,
        state_token: str,
    ) -> tuple[ExactVersionRead, dict[str, object]] | None:
        session = self._session()
        matches: list[ExactStoredRecord] = []
        for record in session.authoritative_records("J-AR13"):
            body = _body(record)
            if (
                body.get("contract_id") == "G-04"
                and body.get("body_discriminator") == body_discriminator
                and body.get("product_ref") == product_ref
                and body.get("product_state_token") == state_token
            ):
                matches.append(record)
        if not matches:
            return None
        if len(matches) != 1:
            raise ReadModelError("exact G-04 lifecycle view is ambiguous")
        payload = _body(matches[0]).get("canonical_payload")
        if not isinstance(payload, dict):
            raise ReadModelError("exact G-04 lifecycle payload is unavailable")
        return ExactVersionRead(matches[0], session.revision), payload

    def get_journal_proposal_exact(
        self,
        proposal_ref: str,
        state_token: str,
    ) -> ExactProposalRead | None:
        treatment = self.get_exact("J-AR05", proposal_ref)
        if treatment is None:
            return None
        exact = self._exact_g04_view(
            body_discriminator="journal_proposal",
            product_ref=proposal_ref,
            state_token=state_token,
        )
        if exact is None:
            return None
        publication, payload = exact
        evidence = self._lifecycle_events(
            "journal_proposal",
            proposal_ref,
            through_token=state_token,
        )
        return ExactProposalRead(
            treatment=treatment,
            state_publication=publication,
            lifecycle_evidence=evidence,
            state_token=state_token,
            state_label=str(payload["status"]),
            artifact_f_view=payload,
        )

    def get_accounting_period_exact(
        self,
        period_id: str,
        state_token: str,
    ) -> ExactAccountingPeriodRead | None:
        exact = self._exact_g04_view(
            body_discriminator="accounting_period",
            product_ref=period_id,
            state_token=state_token,
        )
        if exact is None:
            return None
        publication, payload = exact
        evidence = self._lifecycle_events(
            "accounting_period",
            period_id,
            through_token=state_token,
        )
        return ExactAccountingPeriodRead(
            state_publication=publication,
            lifecycle_evidence=evidence,
            state_token=state_token,
            state_label=str(payload["status"]),
            artifact_f_view=payload,
        )

    def get_restatement_case_exact(
        self,
        case_id: str,
        state_token: str,
    ) -> ExactRestatementCaseRead | None:
        exact = self._exact_g04_view(
            body_discriminator="restatement_case",
            product_ref=case_id,
            state_token=state_token,
        )
        if exact is None:
            return None
        publication, payload = exact
        evidence = self._lifecycle_events(
            "restatement_case",
            case_id,
            through_token=state_token,
        )
        return ExactRestatementCaseRead(
            state_publication=publication,
            lifecycle_evidence=evidence,
            state_token=state_token,
            state_label=str(payload["status"]),
            artifact_f_view=payload,
        )

    def get_journal(self, journal_id: str) -> ExactJournalRead | None:
        session = self._session()
        records = session.authoritative_records("J-AR08")
        header = next(
            (
                item
                for item in records
                if item.record_identity == journal_id
                and "journal_line_id" not in _body(item)
            ),
            None,
        )
        if header is None:
            return None
        header_body = _body(header)
        line_refs = header_body.get("line_refs", [])
        if not isinstance(line_refs, list):
            line_refs = []
        by_id = {item.record_identity: item for item in records}
        lines = tuple(
            ExactVersionRead(by_id[str(ref)], session.revision)
            for ref in line_refs
            if str(ref) in by_id
        )
        if len(lines) != len(line_refs):
            raise ReadModelError("journal header does not resolve all ordered lines")
        return ExactJournalRead(ExactVersionRead(header, session.revision), lines)

    def get_reporting_version(
        self, reporting_version_ref: str
    ) -> ExactVersionRead | None:
        return self.get_exact("J-AR10", reporting_version_ref)

    def get_reporting_history(self, period_id: str) -> ReportingHistoryRead:
        session = self._session()
        versions = [
            item
            for item in session.authoritative_records("J-AR10")
            if _body(item).get("period_id") == period_id
        ]
        versions.sort(
            key=lambda item: (
                int(_body(item).get("version", 0)),
                item.record_identity,
            )
        )
        return ReportingHistoryRead(
            period_id=period_id,
            versions=tuple(
                ExactVersionRead(item, session.revision) for item in versions
            ),
        )

    def resolve_reporting_content(
        self, reporting_version_ref: str
    ) -> ResolvedReportingContent:
        version = self.get_reporting_version(reporting_version_ref)
        if version is None or not isinstance(version.body, dict):
            raise ReadModelError("reporting version does not exist")
        content_ref = str(version.body["content_ref"])
        content_hash = str(version.body["content_hash"])
        session = self._session()
        proof = next(
            (
                item
                for item in session.authoritative_records("J-AR12")
                if item.record_identity == content_ref
                or _body(item).get("content_ref") == content_ref
            ),
            None,
        )
        if proof is None:
            return ResolvedReportingContent(
                content_ref=content_ref,
                declared_content_hash=content_hash,
                verification_status="DECLARED_HASH_ONLY",
                proof=None,
                canonical_body=None,
            )
        proof_body = _body(proof)
        canonical_body = proof_body.get("canonical_body")
        if canonical_body is None or canonical_sha256(canonical_body) != content_hash:
            raise ReadModelError("committed reporting content hash does not verify")
        return ResolvedReportingContent(
            content_ref=content_ref,
            declared_content_hash=content_hash,
            verification_status="CONTENT_BYTES_VERIFIED",
            proof=ExactVersionRead(proof, session.revision),
            canonical_body=canonical_body,
        )

    def get_readiness_assessment(
        self,
        *,
        product_ref: str,
        reporting_version_ref: str,
        purpose_ref: str,
        period_id: str,
        scope_ref: str,
    ) -> ReadinessRead | None:
        session = self._session()
        record = session.authoritative_record("J-AR02", product_ref)
        if record is None:
            return None
        outer = _body(record)
        body = _product_body(record)
        if outer.get("product_discriminator") != "aegis.readiness_assessment":
            return None
        exact = (
            body.get("product_ref") == product_ref
            and body.get("reporting_version_ref") == reporting_version_ref
            and body.get("purpose_ref") == purpose_ref
            and body.get("period_id") == period_id
            and body.get("scope_ref") == scope_ref
        )
        if not exact:
            return None
        return ReadinessRead(
            product=ExactVersionRead(record, session.revision),
            reporting_version_ref=reporting_version_ref,
            purpose_ref=purpose_ref,
            period_id=period_id,
            scope_ref=scope_ref,
            status=str(body["status"]),
        )

    def get_controlled_planning_input(
        self, product_ref: str
    ) -> ControlledPlanningInputRead:
        session = self._session()
        record = session.authoritative_record("J-AR02", product_ref)
        if record is None:
            raise ReadModelError("exact planning input does not exist")
        outer = _body(record)
        body = _product_body(record)
        if outer.get("product_discriminator") != "pythia.planning_input_snapshot":
            raise ReadModelError("record is not a planning input snapshot")
        readiness = self.get_readiness_assessment(
            product_ref=str(body["readiness_ref"]),
            reporting_version_ref=str(body["reporting_version_ref"]),
            purpose_ref=str(body["purpose_ref"]),
            period_id=str(body["period_id"]),
            scope_ref=str(body["scope_ref"]),
        )
        if readiness is None or readiness.status != "APPROVED":
            raise ReadModelError(
                "controlled use requires its exact approved readiness version"
            )
        reporting = session.authoritative_record(
            "J-AR10", str(body["reporting_version_ref"])
        )
        if reporting is None:
            raise ReadModelError("planning input reporting version does not exist")
        return ControlledPlanningInputRead(
            planning_input=ExactVersionRead(record, session.revision),
            readiness=readiness,
            reporting_version=ExactVersionRead(reporting, session.revision),
        )

    def trace_reporting_value(
        self, reporting_version_ref: str, statement_field: str
    ) -> ReportingValueTrace:
        content = self.resolve_reporting_content(reporting_version_ref)
        if (
            content.verification_status != "CONTENT_BYTES_VERIFIED"
            or not isinstance(content.canonical_body, dict)
        ):
            raise ReadModelError(
                "statement-value trace requires verified reporting content bytes"
            )
        statement_value = content.canonical_body.get(statement_field)
        currency = content.canonical_body.get("currency")
        if isinstance(statement_value, bool) or not isinstance(statement_value, int):
            raise ReadModelError("statement field is not an integer-minor value")
        if not isinstance(currency, str):
            raise ReadModelError("reporting content does not declare its currency")
        session = self._session()
        records = session.authoritative_records()
        keys = {
            (item.record_family, item.record_identity): (
                f"{item.record_family}:{item.record_identity}"
            )
            for item in records
        }
        by_key = {
            keys[(item.record_family, item.record_identity)]: item for item in records
        }
        alias_keys: dict[str, set[str]] = defaultdict(set)
        for key, record in by_key.items():
            for alias in _aliases(record):
                alias_keys[alias].add(key)

        external: dict[str, TraceNode] = {}
        edges: set[TraceEdge] = set()
        starts = alias_keys.get(reporting_version_ref, set())
        starts = {
            key for key in starts if by_key[key].record_family == "J-AR10"
        }
        if len(starts) != 1:
            raise ReadModelError("exact reporting-version trace root is unavailable")
        start = next(iter(starts))
        included = {start}
        pending = deque([start])

        def resolve(source_key: str, spec: _ReferenceSpec) -> str:
            exact_matches = {
                key
                for key, candidate in by_key.items()
                if candidate.record_family in spec.expected_families
                and candidate.record_identity == spec.target
            }
            if len(exact_matches) == 1:
                return next(iter(exact_matches))
            if len(exact_matches) > 1:
                raise ReadModelError(
                    "ambiguous exact authoritative trace identity: "
                    f"{source_key} -> {spec.relationship} -> {spec.target}"
                )
            alias_matches = {
                key
                for key in alias_keys.get(spec.target, set())
                if by_key[key].record_family in spec.expected_families
            }
            if len(alias_matches) > 1:
                raise ReadModelError(
                    "ambiguous authoritative trace binding: "
                    f"{source_key} -> {spec.relationship} -> {spec.target}"
                )
            if len(alias_matches) == 1:
                return next(iter(alias_matches))
            if spec.unresolved_role is None:
                raise ReadModelError(
                    "broken internal trace binding: "
                    f"{source_key} -> {spec.relationship} -> {spec.target}"
                )
            target_key = f"EXTERNAL:{spec.unresolved_role}:{spec.target}"
            external.setdefault(
                target_key,
                TraceNode(
                    node_ref=target_key,
                    role=spec.unresolved_role,
                    record_family="EXTERNAL",
                    record_identity=spec.target,
                    semantic_hash=None,
                ),
            )
            return target_key

        def exact_published_case(
            source_key: str,
            record: ExactStoredRecord,
        ) -> str | None:
            body = _body(record)
            case_id = body.get("restatement_case_id")
            manifest_hash = body.get("adjustment_manifest_hash")
            if record.record_family != "J-AR10" or not isinstance(case_id, str):
                return None
            matches = {
                key
                for key, candidate in by_key.items()
                if candidate.record_family == "J-AR02"
                and _body(candidate).get("restatement_case_id") == case_id
                and _body(candidate).get("status") == "PUBLISHED"
                and _body(candidate).get("manifest_hash") == manifest_hash
            }
            if len(matches) != 1:
                qualifier = "ambiguous" if matches else "broken"
                raise ReadModelError(
                    f"{qualifier} authoritative restatement-case binding: {source_key}"
                )
            return next(iter(matches))

        while pending:
            current = pending.popleft()
            record = by_key[current]
            links = list(_record_references(record))
            case_key = exact_published_case(current, record)
            if case_key is not None:
                edges.add(
                    TraceEdge(
                        current,
                        case_key,
                        "restatement_case_manifest",
                    )
                )
                if case_key not in included:
                    included.add(case_key)
                    pending.append(case_key)
            for spec in sorted(
                links,
                key=lambda item: (item.relationship, item.target),
            ):
                target_key = resolve(current, spec)
                if current == target_key:
                    continue
                edges.add(
                    TraceEdge(current, target_key, spec.relationship)
                )
                if target_key not in included:
                    included.add(target_key)
                    if target_key in by_key:
                        pending.append(target_key)

        nodes = [
            TraceNode(
                node_ref=key,
                role=_record_role(record),
                record_family=record.record_family,
                record_identity=record.record_identity,
                semantic_hash=record.semantic_hash,
            )
            for key, record in by_key.items()
            if key in included
        ]
        nodes.extend(node for key, node in external.items() if key in included)
        selected_edges = tuple(
            sorted(
                edges,
                key=lambda item: (
                    item.source_ref,
                    item.target_ref,
                    item.relationship,
                ),
            )
        )
        return ReportingValueTrace(
            reporting_version_ref=reporting_version_ref,
            statement_field=statement_field,
            statement_value_minor=statement_value,
            currency=currency,
            content_verification_status=content.verification_status,
            query_revision=session.revision,
            nodes=tuple(sorted(nodes, key=lambda item: item.node_ref)),
            edges=selected_edges,
        )
