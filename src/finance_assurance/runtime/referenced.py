"""Runtime model for admitted non-authored journal projections."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from finance_assurance.runtime.contracts.primitives import (
    AsciiString,
    Currency,
    Dimensions,
    FrozenContractModel,
    HashValue,
    NonNegativeInt,
    PeriodId,
    PositiveInt,
    require_one_sided_line,
)


class ProjectionLine(FrozenContractModel):
    line_no: PositiveInt
    account_id: AsciiString
    debit_minor: NonNegativeInt
    credit_minor: NonNegativeInt
    currency: Currency
    dimensions: Dimensions

    @model_validator(mode="after")
    def is_one_sided(self) -> ProjectionLine:
        require_one_sided_line(self.debit_minor, self.credit_minor)
        return self


class ReferencedJournalProjection(FrozenContractModel):
    fixture_id: AsciiString
    projection_type: Literal["referenced_journal_projection"]
    projection_version: Literal[1]
    authored_by_f: Literal[False]
    source_hash: HashValue
    journal_id: AsciiString
    ledger_period_id: PeriodId
    currency: Currency
    line_tuples: tuple[ProjectionLine, ...] = Field(min_length=2)
