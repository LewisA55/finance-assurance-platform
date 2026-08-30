"""Runtime-owned cross-cutting primitives from Artifact F section 2."""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)


class FrozenContractModel(BaseModel):
    """Strict immutable wire model; undeclared fields are contract failures."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


def _ascii(value: str) -> str:
    if not value or not value.isascii():
        raise ValueError("must be a non-empty ASCII string")
    return value


def _version_ref(value: str) -> str:
    if re.fullmatch(r".+@v[1-9][0-9]*", value) is None:
        raise ValueError("must be a fully qualified version reference")
    return value


def _date(value: str) -> str:
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise ValueError("must use YYYY-MM-DD")
    return value


def _period(value: str) -> str:
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}", value) is None:
        raise ValueError("must use YYYY-MM")
    return value


def _timestamp(value: str) -> str:
    pattern = r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z"
    if re.fullmatch(pattern, value) is None:
        raise ValueError("must be an RFC 3339 UTC timestamp ending in Z")
    return value


def _hash(value: str) -> str:
    if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise ValueError("must be a lowercase SHA-256 reference")
    return value


AsciiString = Annotated[str, AfterValidator(_ascii)]
VersionRef = Annotated[str, AfterValidator(_ascii), AfterValidator(_version_ref)]
DateString = Annotated[str, AfterValidator(_date)]
PeriodId = Annotated[str, AfterValidator(_period)]
Timestamp = Annotated[str, AfterValidator(_timestamp)]
HashValue = Annotated[str, AfterValidator(_hash)]
PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]
Currency = Literal["GBP"]


class EvidenceRef(FrozenContractModel):
    ref_id: AsciiString
    description: AsciiString
    content_hash: HashValue


class AuthoritativeRef(FrozenContractModel):
    record_family: AsciiString
    record_identity: AsciiString
    semantic_hash: HashValue

    @model_validator(mode="after")
    def validate_family(self) -> AuthoritativeRef:
        if re.fullmatch(r"J-AR(?:0[1-9]|1[0-7])", self.record_family) is None:
            raise ValueError("authoritative reference family is unsupported")
        return self

    def __str__(self) -> str:
        return self.record_identity


class ContractPublicationRef(FrozenContractModel):
    publication_authoritative_ref: AuthoritativeRef
    contract_id: AsciiString
    g_contract_version: Literal["G-v0.2"]
    product_ref: AsciiString
    payload_hash: HashValue

    @model_validator(mode="after")
    def validate_publication(self) -> ContractPublicationRef:
        if self.publication_authoritative_ref.record_family != "J-AR13":
            raise ValueError("publication reference must resolve to J-AR13")
        if re.fullmatch(r"G-(?:0[1-9]|1[0-4])", self.contract_id) is None:
            raise ValueError("publication contract is unsupported")
        return self

    def __str__(self) -> str:
        return self.publication_authoritative_ref.record_identity


class ModuleProductRef(FrozenContractModel):
    product_authoritative_ref: AuthoritativeRef
    product_discriminator: AsciiString
    product_ref: AsciiString
    body_contract_version: Literal[1]
    body_hash: HashValue

    @model_validator(mode="after")
    def validate_product(self) -> ModuleProductRef:
        if self.product_authoritative_ref.record_family != "J-AR02":
            raise ValueError("module-product reference must resolve to J-AR02")
        return self

    def __str__(self) -> str:
        return self.product_ref


class ExactSemanticRef(FrozenContractModel):
    ref_kind: Literal["AUTHORITATIVE", "PUBLICATION", "MODULE_PRODUCT"]
    authoritative_ref: AuthoritativeRef | None
    publication_ref: ContractPublicationRef | None
    module_product_ref: ModuleProductRef | None

    @model_validator(mode="before")
    @classmethod
    def restore_absent_variant_fields(cls, value: object) -> object:
        if isinstance(value, dict):
            return {
                "authoritative_ref": None,
                "publication_ref": None,
                "module_product_ref": None,
                **value,
            }
        return value

    @model_validator(mode="after")
    def validate_variant(self) -> ExactSemanticRef:
        selected = {
            "AUTHORITATIVE": self.authoritative_ref,
            "PUBLICATION": self.publication_ref,
            "MODULE_PRODUCT": self.module_product_ref,
        }
        if selected[self.ref_kind] is None or sum(
            item is not None for item in selected.values()
        ) != 1:
            raise ValueError("exact semantic reference variant is inconsistent")
        return self

    def __str__(self) -> str:
        selected = {
            "AUTHORITATIVE": self.authoritative_ref,
            "PUBLICATION": self.publication_ref,
            "MODULE_PRODUCT": self.module_product_ref,
        }[self.ref_kind]
        assert selected is not None
        return str(selected)

    @model_serializer(mode="wrap")
    def serialize_without_nulls(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        value = handler(self)
        assert isinstance(value, dict)
        return {key: item for key, item in value.items() if item is not None}


class OpaqueRef(FrozenContractModel):
    object_type: Literal[
        "contract",
        "recognition_schedule",
        "issue",
        "remediation_directive",
        "policy",
        "checklist",
        "reconciliation",
        "materiality_assessment",
        "disclosure_basis",
    ]
    object_id: AsciiString


class ContractRef(OpaqueRef):
    object_type: Literal["contract"]


class RecognitionScheduleRef(OpaqueRef):
    object_type: Literal["recognition_schedule"]


class IssueRef(OpaqueRef):
    object_type: Literal["issue"]


class RemediationDirectiveRef(OpaqueRef):
    object_type: Literal["remediation_directive"]


class PolicyRef(OpaqueRef):
    object_type: Literal["policy"]


class ChecklistRef(OpaqueRef):
    object_type: Literal["checklist"]


class ReconciliationRef(OpaqueRef):
    object_type: Literal["reconciliation"]


class MaterialityRef(OpaqueRef):
    object_type: Literal["materiality_assessment"]


class DisclosureBasisRef(OpaqueRef):
    object_type: Literal["disclosure_basis"]


class ActorRef(FrozenContractModel):
    actor_type: Literal["PERSON", "SYSTEM_POLICY"]
    actor_id: AsciiString
    role: Literal[
        "RULE_ENGINE",
        "CORRECTION_ENGINE",
        "CONTROLLER",
        "CFO",
        "POSTING_SERVICE",
        "REPORTING_SERVICE",
    ]


class Authorization(FrozenContractModel):
    authority_mode: Literal["HUMAN", "SYSTEM_POLICY"]
    policy_ref: PolicyRef


class DerivationAuthority(FrozenContractModel):
    authority_kind: Literal["POSTING_RULE", "POLICY"]
    authority_ref: AsciiString

    @model_validator(mode="after")
    def posting_rule_is_versioned(self) -> DerivationAuthority:
        if self.authority_kind == "POSTING_RULE":
            _version_ref(self.authority_ref)
        return self


class Dimensions(FrozenContractModel):
    legal_entity_id: AsciiString
    customer_id: AsciiString | None
    contract_id: AsciiString | None


def require_one_sided_line(debit_minor: int, credit_minor: int) -> None:
    if (debit_minor > 0) == (credit_minor > 0):
        raise ValueError("exactly one of debit_minor and credit_minor must be positive")
