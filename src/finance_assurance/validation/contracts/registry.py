"""Discriminated Artifact F registry and stable harness rejection mapping."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from finance_assurance.validation.canonical import canonical_bytes
from finance_assurance.validation.results import Detail, Rejection, RejectionCode

from .events import ACCOUNTING_EVENT_ADAPTER
from .objects import OBJECT_ADAPTERS


@dataclass(frozen=True, slots=True)
class ContractViolation(ValueError):
    """A stable contract rejection independent of Pydantic wording."""

    rejection: Rejection

    def __str__(self) -> str:
        return f"{self.rejection.code}: {self.rejection.reason}"


def _location(error: dict[str, object]) -> tuple[str, ...]:
    return tuple(str(item) for item in error.get("loc", ()))


def _classify(error: dict[str, object]) -> tuple[str, str]:
    error_type = str(error.get("type", ""))
    location = _location(error)
    leaf = location[-1] if location else ""
    input_value = error.get("input")

    if error_type == "extra_forbidden":
        if leaf == "idempotency_key":
            return "INAPPLICABLE_CONDITIONAL_FIELD", "idempotency is not valid for this event"
        if leaf in {"corrects_journal_id", "reverses_journal_id"}:
            return "CROSS_VARIANT_FIELD_LEAKAGE", "field belongs to another contract variant"
        if any(part in {"trigger_ref", "directive_ref"} for part in location):
            return "OWNERSHIP_BOUNDARY_VIOLATION", "opaque owner reference contains an embedded body"
        return "UNKNOWN_FIELD", "payload contains an undeclared field"
    if error_type == "missing" and leaf == "idempotency_key":
        return "MISSING_REQUIRED_CONDITIONAL_FIELD", "effect event requires idempotency_key"
    if error_type == "int_type" and leaf.endswith("_minor"):
        return "NON_INTEGER_MONEY", "money must be encoded as an integer in minor units"
    if error_type == "union_tag_invalid":
        if (
            input_value == "AUTOMATED_POSTING"
            or "entry_class" in location
            or (
                isinstance(input_value, Mapping)
                and input_value.get("entry_class") == "AUTOMATED_POSTING"
            )
        ):
            return "UNEXERCISED_VARIANT", "posted journal class is outside contract version 1"
        return "UNKNOWN_DISCRIMINATOR", "discriminator is outside contract version 1"
    if error_type == "union_tag_not_found":
        return "UNKNOWN_DISCRIMINATOR", "required contract discriminator is missing"
    if leaf.endswith("_ref") and error_type in {"value_error", "string_pattern_mismatch"}:
        return "INCOMPLETE_VERSION_REFERENCE", "versioned reference must include @v<positive>"
    return "CONTRACT_VIOLATION", "payload does not conform to the selected contract"


def _translate(error: ValidationError) -> ContractViolation:
    first = error.errors(include_url=False, include_context=False, include_input=True)[0]
    code, reason = _classify(first)
    location = ".".join(_location(first)) or "$"
    return ContractViolation(
        Rejection(
            code=RejectionCode(code),
            reason=reason,
            details=(Detail("location", location),),
        ),
    )


def validate_object(object_type: str, payload: object) -> BaseModel:
    """Validate one object selected only by its fixture discriminant."""

    adapter = OBJECT_ADAPTERS.get(object_type)
    if adapter is None:
        raise ContractViolation(
            Rejection(RejectionCode("UNKNOWN_DISCRIMINATOR"), "unknown object type"),
        )
    try:
        model = adapter.validate_json(canonical_bytes(payload))
    except ValidationError as error:
        raise _translate(error) from None
    if not isinstance(model, BaseModel):
        raise AssertionError("object contract did not produce a frozen model")
    return model


def validate_accounting_event(payload: object) -> BaseModel:
    """Validate one of the ten accounting-event contracts."""

    try:
        model = ACCOUNTING_EVENT_ADAPTER.validate_json(canonical_bytes(payload))
    except ValidationError as error:
        raise _translate(error) from None
    if not isinstance(model, BaseModel):
        raise AssertionError("event contract did not produce a frozen model")
    return model


def canonical_model_bytes(model: BaseModel) -> bytes:
    """Serialize a validated model independently of field declaration order."""

    return canonical_bytes(model.model_dump(mode="json", round_trip=True))
