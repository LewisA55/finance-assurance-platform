"""Artifact L internal module products and J-AR13 publication contracts."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import (
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256
from finance_assurance.runtime.contracts.events import ACCOUNTING_EVENT_ADAPTER
from finance_assurance.runtime.contracts.objects import OBJECT_ADAPTERS
from finance_assurance.runtime.contracts.primitives import (
    AsciiString,
    AuthoritativeRef,
    ContractPublicationRef,
    ExactSemanticRef,
    FrozenContractModel,
    HashValue,
    ModuleProductRef,
    Timestamp,
)

ContractId = Literal[
    "G-01",
    "G-02",
    "G-03",
    "G-04",
    "G-05",
    "G-06",
    "G-07",
    "G-08",
    "G-09",
    "G-10",
    "G-11",
    "G-12",
    "G-13",
    "G-14",
]
Publisher = Literal[
    "SharedSubstrate",
    "Hermes",
    "Atlas",
    "Argus",
    "Aegis",
    "Pythia",
    "AtlasReadBoundary",
]
Consumer = Literal[
    "SharedSubstrate",
    "Hermes",
    "Atlas",
    "Argus",
    "Aegis",
    "Pythia",
    "ApprovedDecision",
    "CorrectionConstructor",
]

G_REGISTRY: dict[str, tuple[str, frozenset[str], frozenset[str]]] = {
    "G-01": ("SharedSubstrate", frozenset({"business_event"}), frozenset({"Atlas", "Argus"})),
    "G-02": ("Hermes", frozenset({"G02AdmissionResult"}), frozenset({"SharedSubstrate", "Atlas", "Argus"})),
    "G-03": ("Hermes", frozenset({"G03ReconciliationResult"}), frozenset({"Argus", "Aegis", "Atlas"})),
    "G-04": ("Atlas", frozenset({"journal_proposal", "accounting_period", "restatement_case", "journal_entry"}), frozenset({"Argus", "Aegis", "Pythia"})),
    "G-05": ("Atlas", frozenset({"accounting_event"}), frozenset({"Argus", "Aegis", "Hermes"})),
    "G-06": ("Atlas", frozenset({"G06ReportingVersion"}), frozenset({"Argus", "Aegis", "Pythia"})),
    "G-07": ("Argus", frozenset({"G07AssuranceResult"}), frozenset({"Aegis", "Atlas"})),
    "G-08": ("Aegis", frozenset({"G08GovernanceResult"}), frozenset({"Argus", "Atlas", "Pythia"})),
    "G-09": ("Aegis", frozenset({"G09RemediationDirective"}), frozenset({"Atlas"})),
    "G-10": ("Aegis", frozenset({"G10ReadinessAssessment"}), frozenset({"Pythia"})),
    "G-11": ("Pythia", frozenset({"G11PlanningInputSnapshot"}), frozenset({"Argus", "Aegis"})),
    "G-12": ("Pythia", frozenset({"G12GovernedDecision"}), frozenset({"Argus", "Aegis", "Atlas", "ApprovedDecision"})),
    "G-13": ("AtlasReadBoundary", frozenset({"G13ReferencedJournal"}), frozenset({"Argus", "CorrectionConstructor"})),
    "G-14": ("Atlas", frozenset({"G14CommandRejection"}), frozenset({"Aegis", "Argus"})),
}

_BODY_FIELDS: dict[str, tuple[frozenset[str], ...]] = {
    "G02AdmissionResult": (frozenset({"product_ref", "candidate_receipt_ref", "candidate_type", "candidate_payload_hash", "source_domain_ref", "source_record_ref", "outcome", "eligible_for_g01", "assessed_at"}), frozenset({"product_ref", "candidate_receipt_ref", "candidate_type", "candidate_payload_hash", "source_domain_ref", "source_record_ref", "outcome", "reason_code", "eligible_for_g01", "assessed_at"})),
    "G03ReconciliationResult": (frozenset({"product_ref", "reconciliation_type", "scope_ref", "result", "performed_at", "period_id", "recognition_schedule_ref", "expected_item_count", "expected_amount_minor", "posted_item_count", "posted_amount_minor", "submitted_unposted_count", "deferred_count", "difference_minor", "currency"}), frozenset({"product_ref", "reconciliation_type", "scope_ref", "result", "performed_at", "cash_application_ref", "receipt_party_ref", "application_party_ref", "party_mapping_ref", "identity_match"})),
    "G06ReportingVersion": (frozenset({"reporting_version_ref", "period_id", "content_ref", "content_hash", "content_schema_version", "publication_origin", "published_at", "import_attestation_ref", "original_authority_ref", "source_ref"}), frozenset({"reporting_version_ref", "period_id", "content_ref", "content_hash", "content_schema_version", "publication_origin", "published_at", "predecessor_version_ref", "restatement_case_ref", "manifest_hash", "published_by_event_id", "publication_effect_ref"})),
    "G07AssuranceResult": (frozenset({"result_type", "test_run_ref", "exception_ref", "test_outcome", "assertion", "severity"}), frozenset({"result_type", "verification_ref", "verification_outcome"})),
    "G08GovernanceResult": (frozenset({"governance_result_type", "review_ref", "finding_ref", "issue_ref", "source_exception_ref"}), frozenset({"governance_result_type", "issue_ref", "verification_ref", "prior_issue_ref"})),
    "G09RemediationDirective": (frozenset({"product_ref", "issue_ref", "target_module", "requested_outcome", "affected_period_id", "eligible_correction_period_id", "policy_ref", "requested_by", "requested_at"}),),
    "G10ReadinessAssessment": (frozenset({"product_ref", "reporting_version_ref", "reporting_publication_ref", "period_id", "scope_ref", "purpose_ref", "status", "basis_refs", "limitation_codes", "assessed_by", "assessed_at"}),),
    "G11PlanningInputSnapshot": (frozenset({"product_ref", "reporting_version_ref", "reporting_publication_ref", "readiness_ref", "readiness_publication_ref", "purpose_ref", "period_id", "scope_ref", "assumption_refs", "exclusion_refs", "frozen_at"}),),
    "G12GovernedDecision": (frozenset({"product_ref", "decision_type", "planning_snapshot_ref", "planning_publication_ref", "position_ref", "original_start_date", "recommended_start_date", "monthly_cost_minor", "currency", "reason_code", "produced_at"}),),
    "G13ReferencedJournal": (frozenset({"projection_type", "projection_version", "authored_by_f", "source_hash", "journal_id", "ledger_period_id", "currency", "line_tuples"}),),
    "G14CommandRejection": (frozenset({"disposition_ref", "command_owner", "command_id", "command_type", "requesting_module", "target_module", "request_ref", "disposition", "reason_code", "recorded_at", "authority_refs"}),),
}

MODULE_PRODUCT_OWNERS: dict[str, str] = {
    "source.recognition_schedule": "SourceDomain",
    "hermes.party_identity_mapping": "Hermes",
    "hermes.business_event_admission_result": "Hermes",
    "hermes.recognition_population_reconciliation": "Hermes",
    "hermes.cash_application_identity_reconciliation": "Hermes",
    "argus.recognition_completeness_test_run": "Argus",
    "argus.recognition_completeness_exception": "Argus",
    "argus.cash_application_identity_test_run": "Argus",
    "argus.cash_application_identity_exception": "Argus",
    "argus.restatement_verification": "Argus",
    "argus.cash_application_correction_verification": "Argus",
    "aegis.exception_review": "Aegis",
    "aegis.finding": "Aegis",
    "aegis.issue": "Aegis",
    "aegis.remediation_directive": "Aegis",
    "aegis.readiness_assessment": "Aegis",
    "pythia.planning_input_snapshot": "Pythia",
    "pythia.governed_decision": "Pythia",
    "source.operational_decision_approval": "SourceDomain",
    "source.business_event_candidate": "SourceDomain",
}

_MODULE_BODY_FIELDS: dict[str, tuple[frozenset[str], ...]] = {
    "source.recognition_schedule": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "recognition_schedule_ref",
                "contract_ref",
                "legal_entity_id",
                "customer_id",
                "service_period_start",
                "service_period_end",
                "recognition_effective_date",
                "amount_minor",
                "currency",
                "source_record_ref",
            }
        ),
    ),
    "hermes.party_identity_mapping": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "mapping_ref",
                "source_party_ref",
                "canonical_party_ref",
                "mapping_method",
                "effective_from",
                "effective_to",
                "status",
            }
        ),
    ),
    "hermes.business_event_admission_result": _BODY_FIELDS["G02AdmissionResult"],
    "hermes.recognition_population_reconciliation": (
        _BODY_FIELDS["G03ReconciliationResult"][0],
    ),
    "hermes.cash_application_identity_reconciliation": (
        _BODY_FIELDS["G03ReconciliationResult"][1],
    ),
    "argus.recognition_completeness_test_run": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "test_definition_ref",
                "reconciliation_ref",
                "period_id",
                "population_refs",
                "population_hashes",
                "executed_at",
                "outcome",
                "exception_ref",
            }
        ),
    ),
    "argus.recognition_completeness_exception": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "test_run_ref",
                "assertion",
                "severity",
                "subject_refs",
                "expected_amount_minor",
                "actual_amount_minor",
                "difference_minor",
                "currency",
                "period_id",
                "status",
            }
        ),
    ),
    "argus.cash_application_identity_test_run": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "test_definition_ref",
                "reconciliation_ref",
                "referenced_journal_publication_ref",
                "population_refs",
                "population_hashes",
                "executed_at",
                "outcome",
                "exception_ref",
            }
        ),
    ),
    "argus.cash_application_identity_exception": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "test_run_ref",
                "assertion",
                "severity",
                "receipt_party_ref",
                "application_party_ref",
                "journal_id",
                "amount_minor",
                "currency",
                "status",
            }
        ),
    ),
    "argus.restatement_verification": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "verification_type",
                "journal_ref",
                "manifest_ref",
                "predecessor_reporting_ref",
                "successor_reporting_ref",
                "reporting_publication_ref",
                "check_results",
                "outcome",
            }
        ),
    ),
    "argus.cash_application_correction_verification": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "verification_type",
                "source_journal_ref",
                "source_hash",
                "reversal_journal_ref",
                "replacement_journal_ref",
                "check_results",
                "outcome",
            }
        ),
    ),
    "aegis.exception_review": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "exception_ref",
                "review_outcome",
                "reviewed_by",
                "reviewed_at",
                "conclusion_code",
            }
        ),
    ),
    "aegis.finding": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "review_ref",
                "finding_type",
                "assertion",
                "affected_refs",
                "conclusion_code",
            }
        ),
    ),
    "aegis.issue": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "issue_id",
                "issue_version",
                "finding_refs",
                "status",
                "owner_ref",
                "directive_refs",
                "verification_refs",
                "updated_at",
            }
        ),
        frozenset(
            {
                "product_ref",
                "created_at",
                "issue_id",
                "issue_version",
                "prior_issue_ref",
                "finding_refs",
                "status",
                "owner_ref",
                "directive_refs",
                "verification_refs",
                "updated_at",
            }
        ),
    ),
    "aegis.remediation_directive": _BODY_FIELDS["G09RemediationDirective"],
    "aegis.readiness_assessment": _BODY_FIELDS["G10ReadinessAssessment"],
    "pythia.planning_input_snapshot": _BODY_FIELDS["G11PlanningInputSnapshot"],
    "pythia.governed_decision": _BODY_FIELDS["G12GovernedDecision"],
    "source.operational_decision_approval": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "decision_ref",
                "decision_publication_ref",
                "outcome",
                "decided_by",
                "decided_at",
                "approval_policy_ref",
            }
        ),
        frozenset(
            {
                "product_ref",
                "created_at",
                "decision_ref",
                "decision_publication_ref",
                "outcome",
                "decided_by",
                "decided_at",
                "approval_policy_ref",
                "candidate_ref",
            }
        ),
    ),
    "source.business_event_candidate": (
        frozenset(
            {
                "product_ref",
                "created_at",
                "candidate_type",
                "source_domain_ref",
                "decision_ref",
                "approval_ref",
                "correlation_id",
                "occurred_at",
                "recorded_at",
                "effective_date",
                "position_ref",
                "original_start_date",
                "revised_start_date",
                "monthly_cost_minor",
                "currency",
                "reason_code",
            }
        ),
    ),
}


def _no_float(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("floats are prohibited in internal contracts")
    if isinstance(value, dict):
        for item in value.values():
            _no_float(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _no_float(item)


def _exact_fields(discriminator: str, body: dict[str, Any]) -> None:
    variants = _BODY_FIELDS.get(discriminator)
    if variants is not None and frozenset(body) not in variants:
        raise ValueError(f"{discriminator} body fields are not closed")


_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
_TIMESTAMP_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})"
)
_VERSION_REF_PATTERN = re.compile(r".+@v[1-9][0-9]*")


def _validate_scalar_contracts(body: dict[str, Any]) -> None:
    for key, value in body.items():
        if value is None:
            raise ValueError(f"{key} must be absent rather than null")
        if key.endswith("_hash") and (
            not isinstance(value, str) or _HASH_PATTERN.fullmatch(value) is None
        ):
            raise ValueError(f"{key} must be a SHA-256 value")
        if (
            key.endswith("_minor")
            or key.endswith("_count")
            or key.endswith("_version")
        ) and (isinstance(value, bool) or not isinstance(value, int)):
            raise ValueError(f"{key} must be an integer")
        if key.endswith("_count") and value < 0:
            raise ValueError(f"{key} must be non-negative")
        if key.endswith("_date") and (
            not isinstance(value, str) or _DATE_PATTERN.fullmatch(value) is None
        ):
            raise ValueError(f"{key} must be an ISO date")
        if key.endswith("_at") and (
            not isinstance(value, str)
            or _TIMESTAMP_PATTERN.fullmatch(value) is None
        ):
            raise ValueError(f"{key} must be a timezone-qualified timestamp")
        if key == "currency" and (
            not isinstance(value, str)
            or re.fullmatch(r"[A-Z]{3}", value) is None
        ):
            raise ValueError("currency must be ISO-4217 shaped")
        if key == "product_ref" and (
            not isinstance(value, str)
            or _VERSION_REF_PATTERN.fullmatch(value) is None
        ):
            raise ValueError("module product_ref must be fully versioned")
        if key.endswith("_refs") and not isinstance(value, (list, tuple)):
            raise ValueError(f"{key} must be an ordered reference array")


def _validate_body_semantics(discriminator: str, body: dict[str, Any]) -> None:
    _validate_scalar_contracts(body)
    for field in (
        "authority_refs",
        "basis_refs",
        "population_refs",
        "subject_refs",
        "affected_refs",
    ):
        if field not in body:
            continue
        values = body[field]
        if not isinstance(values, list):
            raise ValueError(f"{field} must be an ordered exact-reference array")
        try:
            resolved = tuple(ExactSemanticRef.model_validate(item) for item in values)
        except ValueError as error:
            raise ValueError(f"{field} contains a non-exact reference") from error
        if len({canonical_sha256(item.model_dump(mode="json")) for item in resolved}) != len(
            resolved
        ):
            raise ValueError(f"{field} contains a duplicate exact reference")
    if discriminator == "G02AdmissionResult":
        accepted = body["outcome"] == "ACCEPTED"
        if bool(body["eligible_for_g01"]) != accepted:
            raise ValueError("G-02 eligibility must equal accepted admission")
        if accepted == ("reason_code" in body):
            raise ValueError("G-02 reason-code presence is inconsistent")
    elif discriminator == "G03ReconciliationResult":
        if body["reconciliation_type"] == "RECOGNITION_POPULATION":
            difference = body["expected_amount_minor"] - body["posted_amount_minor"]
            reconciled = difference == 0
            if body["difference_minor"] != difference:
                raise ValueError("G-03 recognition difference is inconsistent")
        else:
            reconciled = bool(body["identity_match"])
        if (body["result"] == "RECONCILED") != reconciled:
            raise ValueError("G-03 result is inconsistent")
    elif discriminator == "G07AssuranceResult":
        if body["result_type"] == "ASSURANCE_EXCEPTION":
            if body["test_outcome"] != "FAILED":
                raise ValueError("G-07 exception must bind a failed test")
        elif body["result_type"] != "ASSURANCE_VERIFICATION":
            raise ValueError("G-07 result type is unsupported")
    elif discriminator == "G08GovernanceResult" and body[
        "governance_result_type"
    ] not in {"EXCEPTION_GOVERNED", "ISSUE_UPDATED"}:
        raise ValueError("G-08 result type is unsupported")
    elif discriminator == "G09RemediationDirective":
        if body["target_module"] != "Atlas":
            raise ValueError("G-09 target must be Atlas")
    elif discriminator == "G10ReadinessAssessment":
        limitations = body["limitation_codes"]
        if (body["status"] == "BLOCKED") != bool(limitations):
            raise ValueError("G-10 readiness limitations are inconsistent")
        if body["status"] not in {"BLOCKED", "APPROVED"}:
            raise ValueError("G-10 readiness status is unsupported")
    elif discriminator in {
        "argus.restatement_verification",
        "argus.cash_application_correction_verification",
    }:
        passed = all(body["check_results"].values())
        if (body["outcome"] == "PASSED") != passed:
            raise ValueError("Argus verification outcome is inconsistent")
    elif discriminator == "source.operational_decision_approval":
        approved = body["outcome"] == "APPROVED"
        if approved != ("candidate_ref" in body):
            raise ValueError("operational approval candidate binding is inconsistent")
    elif discriminator == "G13ReferencedJournal":
        if body["authored_by_f"] is not False:
            raise ValueError("G-13 can never claim Artifact F authorship")
    elif discriminator == "G14CommandRejection":
        if body["disposition"] != "REJECTED":
            raise ValueError("G-14 is rejection-only")
    elif discriminator == "G06ReportingVersion":
        imported = body["publication_origin"] == "PRE_SCOPE_IMPORT"
        if imported != ("import_attestation_ref" in body):
            raise ValueError("G-06 origin and variant fields are inconsistent")


class CommandPublicationBasis(FrozenContractModel):
    basis_type: Literal["COMMAND"]
    command_owner: AsciiString
    command_id: AsciiString
    command_result_ref: AsciiString


class ImportPublicationBasis(FrozenContractModel):
    basis_type: Literal["PRE_SCOPE_IMPORT"]
    import_attestation_ref: AsciiString


class ReferencedJournalPublicationBasis(FrozenContractModel):
    basis_type: Literal["REFERENCED_JOURNAL_ADMISSION"]
    referenced_source_ref: AsciiString
    admission_identity: AsciiString


PublicationBasis = (
    CommandPublicationBasis
    | ImportPublicationBasis
    | ReferencedJournalPublicationBasis
)


class ContractPublication(FrozenContractModel):
    """Exact Artifact L J-AR13 envelope."""

    publication_ref: AsciiString
    contract_id: ContractId
    g_contract_version: Literal["G-v0.2"]
    body_contract_version: Literal[1]
    body_discriminator: AsciiString
    canonicalization_version: Literal["SORTED_KEYS_COMPACT_UTF8_V1"]
    publisher: Publisher
    product_ref: AsciiString
    product_state_token: AsciiString | None
    canonical_payload: dict[str, Any]
    payload_hash: HashValue
    upstream_publication_refs: tuple[ContractPublicationRef, ...]
    upstream_authoritative_refs: tuple[ExactSemanticRef, ...]
    evidence_refs: tuple[AuthoritativeRef, ...] = Field(min_length=1)
    available_from: Timestamp
    publication_basis: PublicationBasis

    @model_validator(mode="before")
    @classmethod
    def restore_logically_absent_token(cls, value: object) -> object:
        if isinstance(value, dict):
            restored = dict(value)
            restored.setdefault("product_state_token", None)
            for field in (
                "upstream_publication_refs",
                "upstream_authoritative_refs",
                "evidence_refs",
            ):
                if isinstance(restored.get(field), list):
                    restored[field] = tuple(restored[field])
            return restored
        return value

    @model_validator(mode="after")
    def validate_closed_contract(self) -> ContractPublication:
        publisher, discriminators, _ = G_REGISTRY[self.contract_id]
        if self.publisher != publisher or self.body_discriminator not in discriminators:
            raise ValueError("publisher or body discriminator is not permitted")
        state_required = (
            self.contract_id == "G-04"
            and self.body_discriminator != "journal_entry"
        )
        if state_required != (self.product_state_token is not None):
            raise ValueError("publication state-token exactness is inconsistent")
        _no_float(self.canonical_payload)
        if self.payload_hash != canonical_sha256(self.canonical_payload):
            raise ValueError("publication payload hash is inconsistent")
        self._validate_payload()
        return self

    @model_serializer(mode="wrap")
    def serialize_without_absent_token(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        value = handler(self)
        assert isinstance(value, dict)
        if self.product_state_token is None:
            value.pop("product_state_token", None)
        return value

    def _validate_payload(self) -> None:
        if self.contract_id == "G-01":
            OBJECT_ADAPTERS["business_event"].validate_json(
                canonical_bytes(self.canonical_payload)
            )
        elif self.contract_id == "G-04":
            OBJECT_ADAPTERS[self.body_discriminator].validate_json(
                canonical_bytes(self.canonical_payload)
            )
        elif self.contract_id == "G-05":
            ACCOUNTING_EVENT_ADAPTER.validate_json(
                canonical_bytes(self.canonical_payload)
            )
        else:
            _exact_fields(self.body_discriminator, self.canonical_payload)
            _validate_body_semantics(
                self.body_discriminator,
                self.canonical_payload,
            )

    def exact_ref(self) -> ContractPublicationRef:
        return ContractPublicationRef(
            publication_authoritative_ref=AuthoritativeRef(
                record_family="J-AR13",
                record_identity=str(self.publication_ref),
                semantic_hash=canonical_sha256(self.model_dump(mode="json")),
            ),
            contract_id=self.contract_id,
            g_contract_version=self.g_contract_version,
            product_ref=str(self.product_ref),
            payload_hash=self.payload_hash,
        )

    @classmethod
    def command(
        cls,
        *,
        publication_ref: str,
        contract_id: ContractId,
        body_discriminator: str,
        publisher: Publisher,
        product_ref: str,
        payload: dict[str, Any],
        command_owner: str,
        command_id: str,
        evidence_refs: tuple[AuthoritativeRef, ...],
        available_from: str,
        product_state_token: str | None = None,
        upstream_publication_refs: tuple[ContractPublicationRef, ...] = (),
        upstream_authoritative_refs: tuple[ExactSemanticRef, ...] = (),
    ) -> ContractPublication:
        return cls(
            publication_ref=publication_ref,
            contract_id=contract_id,
            g_contract_version="G-v0.2",
            body_contract_version=1,
            body_discriminator=body_discriminator,
            canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
            publisher=publisher,
            product_ref=product_ref,
            product_state_token=product_state_token,
            canonical_payload=payload,
            payload_hash=canonical_sha256(payload),
            upstream_publication_refs=upstream_publication_refs,
            upstream_authoritative_refs=upstream_authoritative_refs,
            evidence_refs=evidence_refs,
            available_from=available_from,
            publication_basis=CommandPublicationBasis(
                basis_type="COMMAND",
                command_owner=command_owner,
                command_id=command_id,
                command_result_ref=command_id,
            ),
        )


class ModuleCreationBasis(FrozenContractModel):
    basis_type: Literal["COMMAND"]
    command_owner: AsciiString
    command_id: AsciiString


class BaselineCreationBasis(FrozenContractModel):
    basis_type: Literal["BASELINE"]
    baseline_manifest_ref: AsciiString


class ValidatedModuleProduct(FrozenContractModel):
    """Finite Artifact L J-AR02 command-output product."""

    product_discriminator: AsciiString
    body_contract_version: Literal[1]
    semantic_owner: AsciiString
    canonicalization_version: Literal["SORTED_KEYS_COMPACT_UTF8_V1"]
    canonical_body: dict[str, Any]
    body_hash: HashValue
    upstream_publication_refs: tuple[ContractPublicationRef, ...]
    upstream_authoritative_refs: tuple[ExactSemanticRef, ...]
    evidence_refs: tuple[AuthoritativeRef, ...] = Field(min_length=1)
    creation_basis: ModuleCreationBasis | BaselineCreationBasis
    available_from: Timestamp
    semantic_hash: HashValue

    @model_validator(mode="before")
    @classmethod
    def restore_reference_arrays(cls, value: object) -> object:
        if isinstance(value, dict):
            restored = dict(value)
            for field in (
                "upstream_publication_refs",
                "upstream_authoritative_refs",
                "evidence_refs",
            ):
                if isinstance(restored.get(field), list):
                    restored[field] = tuple(restored[field])
            return restored
        return value

    @model_validator(mode="after")
    def validate_descriptor_and_hashes(self) -> ValidatedModuleProduct:
        owner = MODULE_PRODUCT_OWNERS.get(self.product_discriminator)
        if owner is None or owner != self.semantic_owner:
            raise ValueError("unknown module-product discriminator or owner")
        baseline_product = self.product_discriminator in {
            "source.recognition_schedule",
            "hermes.party_identity_mapping",
        }
        if baseline_product != isinstance(self.creation_basis, BaselineCreationBasis):
            raise ValueError("module-product persistence mode is inconsistent")
        variants = _MODULE_BODY_FIELDS.get(self.product_discriminator)
        if variants is None or frozenset(self.canonical_body) not in variants:
            raise ValueError("module-product body fields are not closed")
        body_discriminator = {
            "hermes.business_event_admission_result": "G02AdmissionResult",
            "hermes.recognition_population_reconciliation": (
                "G03ReconciliationResult"
            ),
            "hermes.cash_application_identity_reconciliation": (
                "G03ReconciliationResult"
            ),
            "aegis.remediation_directive": "G09RemediationDirective",
            "aegis.readiness_assessment": "G10ReadinessAssessment",
            "argus.restatement_verification": "argus.restatement_verification",
            "argus.cash_application_correction_verification": (
                "argus.cash_application_correction_verification"
            ),
            "source.operational_decision_approval": (
                "source.operational_decision_approval"
            ),
        }.get(self.product_discriminator)
        _validate_body_semantics(
            body_discriminator or str(self.product_discriminator),
            self.canonical_body,
        )
        _no_float(self.canonical_body)
        if self.body_hash != canonical_sha256(self.canonical_body):
            raise ValueError("module-product body hash is inconsistent")
        semantic_body = self.model_dump(mode="json", exclude={"semantic_hash"})
        if self.semantic_hash != canonical_sha256(semantic_body):
            raise ValueError("module-product semantic hash is inconsistent")
        if not str(self.canonical_body.get("product_ref", "")):
            raise ValueError("module-product body requires product_ref")
        return self

    def exact_ref(self) -> ModuleProductRef:
        return ModuleProductRef(
            product_authoritative_ref=AuthoritativeRef(
                record_family="J-AR02",
                record_identity=str(self.product_ref),
                semantic_hash=self.semantic_hash,
            ),
            product_discriminator=str(self.product_discriminator),
            product_ref=str(self.product_ref),
            body_contract_version=self.body_contract_version,
            body_hash=self.body_hash,
        )

    @classmethod
    def baseline(
        cls,
        *,
        product_discriminator: str,
        owner: str,
        body: dict[str, Any],
        baseline_manifest_ref: str,
        evidence_refs: tuple[AuthoritativeRef, ...],
        available_from: str,
        upstream_authoritative_refs: tuple[ExactSemanticRef, ...] = (),
    ) -> ValidatedModuleProduct:
        body_hash = canonical_sha256(body)
        values = dict(
            product_discriminator=product_discriminator,
            body_contract_version=1,
            semantic_owner=owner,
            canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
            canonical_body=body,
            body_hash=body_hash,
            upstream_publication_refs=(),
            upstream_authoritative_refs=upstream_authoritative_refs,
            evidence_refs=evidence_refs,
            creation_basis=BaselineCreationBasis(
                basis_type="BASELINE",
                baseline_manifest_ref=baseline_manifest_ref,
            ),
            available_from=available_from,
        )
        values["semantic_hash"] = canonical_sha256(
            {
                key: (
                    value.model_dump(mode="json")
                    if isinstance(value, FrozenContractModel)
                    else value
                )
                for key, value in values.items()
            }
        )
        return cls.model_validate(values)

    @classmethod
    def command(
        cls,
        *,
        product_discriminator: str,
        owner: str,
        body: dict[str, Any],
        command_id: str,
        evidence_refs: tuple[AuthoritativeRef, ...],
        available_from: str,
        upstream_publication_refs: tuple[ContractPublicationRef, ...] = (),
        upstream_authoritative_refs: tuple[ExactSemanticRef, ...] = (),
    ) -> ValidatedModuleProduct:
        body_hash = canonical_sha256(body)
        values = dict(
            product_discriminator=product_discriminator,
            body_contract_version=1,
            semantic_owner=owner,
            canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
            canonical_body=body,
            body_hash=body_hash,
            upstream_publication_refs=upstream_publication_refs,
            upstream_authoritative_refs=upstream_authoritative_refs,
            evidence_refs=evidence_refs,
            creation_basis=ModuleCreationBasis(
                basis_type="COMMAND", command_owner=owner, command_id=command_id
            ),
            available_from=available_from,
        )
        values["semantic_hash"] = canonical_sha256(
            {
                key: (
                    value.model_dump(mode="json")
                    if isinstance(value, FrozenContractModel)
                    else value
                )
                for key, value in values.items()
            }
        )
        return cls.model_validate(values)

    @property
    def product_ref(self) -> str:
        return str(self.canonical_body["product_ref"])


class BoundaryObservation(FrozenContractModel):
    observation_id: AsciiString
    operation: Literal["PUBLISH", "CONSUME"]
    publication_ref: AsciiString
    contract_id: ContractId
    publisher: Publisher
    consumer: Consumer | None
    command_id: AsciiString
    observed_at: Timestamp
