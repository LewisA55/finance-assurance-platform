"""Strict, test-only resolvers for the two non-domain H2 proof boundaries."""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from finance_assurance.runtime.referenced import ReferencedJournalProjection
from finance_assurance.validation.canonical import canonical_bytes, canonical_sha256
from finance_assurance.validation.contracts.primitives import (
    AsciiString,
    Currency,
    FrozenContractModel,
    HashValue,
    NonNegativeInt,
    PeriodId,
    VersionRef,
)
from finance_assurance.validation.corpus import thaw_json
from finance_assurance.validation.index import ValidatedCorpusIndex


class ReportingContentBody(FrozenContractModel):
    currency: Currency
    deferred_revenue_minor: NonNegativeInt
    presented_period_id: PeriodId
    reporting_version_ref: VersionRef
    subscription_revenue_minor: NonNegativeInt


class ReportingContentProof(FrozenContractModel):
    fixture_id: AsciiString
    fixture_type: Literal["reporting_content_proof"]
    content_ref: AsciiString
    content_hash: HashValue
    content_schema_version: Literal[1]
    canonicalization: Literal["SORTED_KEYS_COMPACT_UTF8_V1"]
    canonical_body: ReportingContentBody

    @model_validator(mode="after")
    def declared_hash_matches_body(self) -> ReportingContentProof:
        actual = canonical_sha256(self.canonical_body.model_dump(mode="json"))
        if actual != self.content_hash:
            raise ValueError("reporting proof body does not match its declared hash")
        return self


def resolve_referenced_journal(
    index: ValidatedCorpusIndex,
) -> ReferencedJournalProjection:
    """Resolve the sole G-13 projection without authoring a domain object."""

    records = index.raw.records("referenced-state-projections.jsonl")
    if len(records) != 1:
        raise ValueError("expected exactly one referenced journal projection")
    return ReferencedJournalProjection.model_validate_json(
        canonical_bytes(thaw_json(records[0].value)),
    )


def resolve_reporting_content(
    index: ValidatedCorpusIndex,
) -> tuple[ReportingContentProof, ReportingContentProof]:
    """Resolve and hash-verify the immutable June v1 and v2 proof bodies."""

    proofs = tuple(
        ReportingContentProof.model_validate_json(
            canonical_bytes(thaw_json(record.value)),
        )
        for record in index.raw.records("reporting-content-proof-bodies.jsonl")
    )
    if len(proofs) != 2:
        raise ValueError("expected exactly two reporting proof bodies")
    by_ref = {proof.canonical_body.reporting_version_ref: proof for proof in proofs}
    expected = {"RV-2026-06@v1", "RV-2026-06@v2"}
    if set(by_ref) != expected:
        raise ValueError("reporting proof bodies do not cover June v1 and v2")
    return by_ref["RV-2026-06@v1"], by_ref["RV-2026-06@v2"]
