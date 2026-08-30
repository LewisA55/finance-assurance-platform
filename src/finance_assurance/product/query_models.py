"""Strict Artifact O query inputs for the in-process public facade."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, TypeAdapter

from finance_assurance.product.contracts import PublicContractModel
from finance_assurance.runtime.contracts.primitives import (
    AsciiString,
    PeriodId,
    Timestamp,
)

ScenarioRef = Literal[
    "DEMO-C001-RESTATEMENT@v1",
    "DEMO-CT1-CORRECTION@v1",
]


class PublicQueryBase(PublicContractModel):
    view_contract_version: Literal[1]
    scenario_ref: ScenarioRef
    semantic_as_of_time: Timestamp


class GetDemoManifest(PublicQueryBase):
    query_id: Literal["O-Q01"]
    workspace_ref: AsciiString


class GetPlatformOverview(PublicQueryBase):
    query_id: Literal["O-Q02"]


class GetSourceReconciliation(PublicQueryBase):
    query_id: Literal["O-Q03"]
    reconciliation_ref: AsciiString


class GetReportingHistory(PublicQueryBase):
    query_id: Literal["O-Q04"]
    period_id: PeriodId


class GetReportingVersion(PublicQueryBase):
    query_id: Literal["O-Q05"]
    reporting_version_ref: AsciiString


class GetAssuranceException(PublicQueryBase):
    query_id: Literal["O-Q06"]
    exception_ref: AsciiString


class GetGovernanceCase(PublicQueryBase):
    query_id: Literal["O-Q07"]
    issue_ref: AsciiString


class GetReadinessMatrix(PublicQueryBase):
    query_id: Literal["O-Q08"]
    reporting_version_ref: AsciiString
    period_id: PeriodId
    purpose_ref: AsciiString
    scope_ref: AsciiString


class GetGovernedDecision(PublicQueryBase):
    query_id: Literal["O-Q09"]
    decision_ref: AsciiString


class TraceReportingValue(PublicQueryBase):
    query_id: Literal["O-Q10"]
    reporting_version_ref: AsciiString
    statement_field: AsciiString


class GetCorrectionIntegrity(PublicQueryBase):
    query_id: Literal["O-Q11"]
    verification_ref: AsciiString


type PublicQuery = Annotated[
    GetDemoManifest
    | GetPlatformOverview
    | GetSourceReconciliation
    | GetReportingHistory
    | GetReportingVersion
    | GetAssuranceException
    | GetGovernanceCase
    | GetReadinessMatrix
    | GetGovernedDecision
    | TraceReportingValue
    | GetCorrectionIntegrity,
    Field(discriminator="query_id"),
]


PUBLIC_QUERY_ADAPTER = TypeAdapter(PublicQuery)
