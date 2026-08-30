"""Strict Artifact Q discovery, query, view, and build contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, model_validator

from finance_assurance.product.contracts import PublicContractModel
from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.contracts.primitives import (
    AsciiString,
    HashValue,
    NonNegativeInt,
    Timestamp,
)


class AnalyticalContractModel(PublicContractModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class AnalyticalSubjectSet(AnalyticalContractModel):
    c001_scenario_ref: AsciiString
    c001_journal_id: AsciiString
    c001_business_event_ref: AsciiString
    c001_posting_rule_ref: AsciiString
    c001_reporting_period_id: AsciiString
    c001_reporting_period_token: AsciiString
    ct1_scenario_ref: AsciiString
    ct1_source_journal_id: AsciiString
    ct1_reversal_journal_id: AsciiString
    ct1_replacement_journal_id: AsciiString
    correction_period_id: AsciiString
    ledger_semantics_catalog_ref: AsciiString


class AnalyticalDiscoveryDescriptor(AnalyticalContractModel):
    discovery_contract_version: Literal[1]
    discovery_descriptor_ref: AsciiString
    p_discovery_descriptor_ref: AsciiString
    workspace_ref: AsciiString
    semantic_as_of: Timestamp
    subjects: AnalyticalSubjectSet

    @property
    def descriptor_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))


QueryId = Literal["Q-Q01", "Q-Q02", "Q-Q03", "Q-Q04", "Q-Q05", "Q-Q06"]
ViewContract = Literal["Q-V01", "Q-V02", "Q-V03", "Q-V04", "Q-V05", "Q-V06"]


class AnalyticalQuery(AnalyticalContractModel):
    query_id: QueryId
    query_contract_version: Literal[1]
    scenario_ref: AsciiString
    subject_ref: AsciiString
    state_basis_type: Literal["BASE_FACT", "TRANSITION_PUBLICATION"] | None = None
    state_token: AsciiString | None = None
    semantic_as_of_time: Timestamp

    @model_validator(mode="after")
    def period_variant_is_closed(self) -> AnalyticalQuery:
        if self.query_id == "Q-Q05":
            if self.state_basis_type is None:
                raise ValueError("Q-Q05 requires a state basis")
            if (
                self.state_basis_type == "TRANSITION_PUBLICATION"
                and self.state_token is None
            ):
                raise ValueError("transition publication requires a state token")
            if self.state_basis_type == "BASE_FACT" and self.state_token is not None:
                raise ValueError("base fact cannot carry a state token")
        elif self.state_basis_type is not None or self.state_token is not None:
            raise ValueError("only Q-Q05 may carry period-state coordinates")
        return self

    @property
    def request_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))


class AnalyticalDiscoveryView(AnalyticalContractModel):
    view_contract: Literal["Q-V00"]
    view_contract_version: Literal[1]
    workspace_ref: AsciiString
    discovery_descriptor_ref: AsciiString
    discovery_descriptor_hash: HashValue
    p_discovery_descriptor_ref: AsciiString
    query_revision: NonNegativeInt
    semantic_as_of: Timestamp
    compatibility_mode: Literal["EXACT_ORIGINAL"]
    scenario_set_digest: HashValue
    ledger_semantics_catalog_ref: AsciiString
    query_plan: tuple[AnalyticalQuery, ...]


class AnalyticalView(AnalyticalContractModel):
    view_contract: ViewContract
    view_contract_version: Literal[1]
    query_id: QueryId
    scenario_ref: AsciiString
    query_revision: NonNegativeInt
    semantic_as_of_time: Timestamp
    compatibility_mode: Literal["EXACT_ORIGINAL"]
    source_refs: tuple[AsciiString, ...]
    data: dict[str, object]


class BuildGovernedAnalyticalExport(AnalyticalContractModel):
    request_contract_version: Literal["governed-analytical-export-request@v1"]
    export_ref: AsciiString
    workspace_ref: AsciiString
    semantic_as_of: Timestamp
    exported_at: Timestamp
    output_path: Path
    p_discovery_descriptor_ref: AsciiString
    q_discovery_descriptor_ref: AsciiString
