"""Closed runtime evidence values required by the ratified reporting proof."""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.contracts.primitives import (
    AsciiString,
    Currency,
    FrozenContractModel,
    HashValue,
    NonNegativeInt,
    PeriodId,
    VersionRef,
)


class ReportingContentBody(FrozenContractModel):
    currency: Currency
    deferred_revenue_minor: NonNegativeInt
    presented_period_id: PeriodId
    reporting_version_ref: VersionRef
    subscription_revenue_minor: NonNegativeInt


class ReportingContentRecord(FrozenContractModel):
    """J-AR12 content whose committed bytes support a reporting value claim."""

    fixture_id: AsciiString
    fixture_type: Literal["reporting_content_proof"]
    content_ref: AsciiString
    content_hash: HashValue
    content_schema_version: Literal[1]
    canonicalization: Literal["SORTED_KEYS_COMPACT_UTF8_V1"]
    canonical_body: ReportingContentBody

    @model_validator(mode="after")
    def declared_hash_matches_body(self) -> ReportingContentRecord:
        if self.content_hash != canonical_sha256(
            self.canonical_body.model_dump(mode="json")
        ):
            raise ValueError("reporting content bytes do not match the declared hash")
        return self
