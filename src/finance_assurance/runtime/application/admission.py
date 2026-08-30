"""Ordinary I-C01 candidate custody and Hermes admission assessment."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from finance_assurance.runtime.application.contracts import (
    ModuleCommand,
    ModuleContractService,
    ModuleExecution,
)
from finance_assurance.runtime.application.models import (
    CandidateAssessmentCommand,
    CandidateOutcome,
    CandidateReceipt,
)
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256
from finance_assurance.runtime.contracts.module import (
    ContractPublication,
    ValidatedModuleProduct,
)
from finance_assurance.runtime.contracts.objects import BusinessEvent
from finance_assurance.runtime.contracts.primitives import (
    AuthoritativeRef,
    ExactSemanticRef,
)
from finance_assurance.runtime.digests import value_digest
from finance_assurance.runtime.persistence.ports import CommandPersistenceBoundary

_SUPPORTED_CANDIDATE = "accounting.recognition.due"
_SUPPORTED_CONTRACT_VERSION = "1"


@dataclass(frozen=True, slots=True)
class CandidateAssessmentExecution:
    """Exact I-S01 closure returned after one ordinary command commit."""

    receipt: CandidateReceipt
    admission_result: ValidatedModuleProduct
    publication: ContractPublication
    outcome: CandidateOutcome
    execution: ModuleExecution


def _evidence_refs(
    command: CandidateAssessmentCommand,
) -> tuple[AuthoritativeRef, ...]:
    return tuple(
        AuthoritativeRef(
            record_family="J-AR12",
            record_identity=str(item.ref_id),
            semantic_hash=value_digest(item),
        )
        for item in command.evidence_refs
    )


def _assessment(
    command: CandidateAssessmentCommand,
) -> tuple[CandidateOutcome, str | None]:
    if command.candidate_type != _SUPPORTED_CANDIDATE:
        return "UNSUPPORTED", "UNSUPPORTED_CANDIDATE_TYPE"
    if command.candidate_contract_version != _SUPPORTED_CONTRACT_VERSION:
        return "REJECTED", "UNSUPPORTED_CONTRACT_VERSION"
    try:
        event = BusinessEvent.model_validate_json(
            canonical_bytes(command.canonical_candidate_body)
        )
    except ValidationError:
        return "REJECTED", "INVALID_CANDIDATE_CONTRACT"
    if str(event.correlation_id) != str(command.correlation_id):
        return "REJECTED", "CORRELATION_MISMATCH"
    return "ACCEPTED", None


class CandidateAdmissionService:
    """Produce the finite J-AR01/J-AR02/G-02/J-AR14 I-C01 write set."""

    def __init__(
        self,
        boundary: CommandPersistenceBoundary | None = None,
        *,
        contracts: ModuleContractService | None = None,
    ) -> None:
        if contracts is None and boundary is None:
            raise ValueError("candidate admission requires a persistence boundary")
        if contracts is not None:
            self._contracts = contracts
        else:
            assert boundary is not None
            self._contracts = ModuleContractService(boundary)

    def assess(
        self,
        command: CandidateAssessmentCommand,
    ) -> CandidateAssessmentExecution:
        outcome, reason_code = _assessment(command)
        candidate_hash = canonical_sha256(command.canonical_candidate_body)
        evidence = _evidence_refs(command)
        receipt = CandidateReceipt(
            receipt_contract_version=1,
            candidate_receipt_ref=command.candidate_receipt_ref,
            candidate_contract_version=command.candidate_contract_version,
            canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
            candidate_type=command.candidate_type,
            canonical_candidate_body=command.canonical_candidate_body,
            candidate_payload_hash=candidate_hash,
            source_domain_ref=command.source_domain_ref,
            source_record_ref=command.source_record_ref,
            received_at=command.received_at,
            approval_ref=command.approval_ref,
            upstream_authoritative_refs=command.upstream_authoritative_refs,
            evidence_refs=command.evidence_refs,
        )
        body: dict[str, object] = {
            "product_ref": str(command.admission_product_ref),
            "candidate_receipt_ref": str(command.candidate_receipt_ref),
            "candidate_type": str(command.candidate_type),
            "candidate_payload_hash": candidate_hash,
            "source_domain_ref": str(command.source_domain_ref),
            "source_record_ref": str(command.source_record_ref),
            "outcome": outcome,
            "eligible_for_g01": outcome == "ACCEPTED",
            "assessed_at": str(command.assessed_at),
        }
        if reason_code is not None:
            body["reason_code"] = reason_code
        receipt_ref = AuthoritativeRef(
            record_family="J-AR01",
            record_identity=str(command.candidate_receipt_ref),
            semantic_hash=value_digest(receipt),
        )
        upstream_authoritative_refs = (
            ExactSemanticRef(
                ref_kind="AUTHORITATIVE",
                authoritative_ref=receipt_ref,
                publication_ref=None,
                module_product_ref=None,
            ),
        )
        if command.upstream_authoritative_refs:
            raise ValueError(
                "candidate upstream identities require resolved exact references"
            )
        admission = ValidatedModuleProduct.command(
            product_discriminator="hermes.business_event_admission_result",
            owner="Hermes",
            body=body,
            command_id=str(command.command_id),
            evidence_refs=evidence,
            available_from=str(command.semantic_as_of_time),
            upstream_authoritative_refs=upstream_authoritative_refs,
        )
        publication = ContractPublication.command(
            publication_ref=str(command.publication_ref),
            contract_id="G-02",
            body_discriminator="G02AdmissionResult",
            publisher="Hermes",
            product_ref=admission.product_ref,
            payload=admission.canonical_body,
            command_owner="Hermes",
            command_id=str(command.command_id),
            evidence_refs=evidence,
            available_from=str(command.semantic_as_of_time),
            upstream_authoritative_refs=(
                ExactSemanticRef(
                    ref_kind="AUTHORITATIVE",
                    authoritative_ref=receipt_ref,
                    publication_ref=None,
                    module_product_ref=None,
                ),
                ExactSemanticRef(
                    ref_kind="MODULE_PRODUCT",
                    authoritative_ref=None,
                    publication_ref=None,
                    module_product_ref=admission.exact_ref(),
                ),
            ),
        )
        execution = self._contracts.execute(
            ModuleCommand(
                command_id=str(command.command_id),
                command_owner="Hermes",
                command_type="AssessBusinessEventCandidate",
                actor_ref=str(command.actor_ref),
                correlation_id=str(command.correlation_id),
                semantic_as_of_time=str(command.semantic_as_of_time),
                products=(admission,),
                authoritative_creations=(receipt,),
                publications=(publication,),
            )
        )
        return CandidateAssessmentExecution(
            receipt=receipt,
            admission_result=admission,
            publication=publication,
            outcome=outcome,
            execution=execution,
        )
