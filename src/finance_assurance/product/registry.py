"""Finite Artifact O public query-to-view registry."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, cast

PublicQueryId = Literal[
    "O-Q01",
    "O-Q02",
    "O-Q03",
    "O-Q04",
    "O-Q05",
    "O-Q06",
    "O-Q07",
    "O-Q08",
    "O-Q09",
    "O-Q10",
    "O-Q11",
]
PublicViewId = Literal[
    "O-V01",
    "O-V02",
    "O-V03",
    "O-V04",
    "O-V05",
    "O-V06",
    "O-V07",
    "O-V08",
    "O-V09",
    "O-V10",
    "O-V11",
]


@dataclass(frozen=True, slots=True)
class PublicQueryDescriptor:
    query_id: PublicQueryId
    operation: str
    view_id: PublicViewId


_DESCRIPTORS = (
    PublicQueryDescriptor("O-Q01", "GetDemoManifest", "O-V01"),
    PublicQueryDescriptor("O-Q02", "GetPlatformOverview", "O-V02"),
    PublicQueryDescriptor("O-Q03", "GetSourceReconciliation", "O-V03"),
    PublicQueryDescriptor("O-Q04", "GetReportingHistory", "O-V04"),
    PublicQueryDescriptor("O-Q05", "GetReportingVersion", "O-V05"),
    PublicQueryDescriptor("O-Q06", "GetAssuranceException", "O-V06"),
    PublicQueryDescriptor("O-Q07", "GetGovernanceCase", "O-V07"),
    PublicQueryDescriptor("O-Q08", "GetReadinessMatrix", "O-V08"),
    PublicQueryDescriptor("O-Q09", "GetGovernedDecision", "O-V09"),
    PublicQueryDescriptor("O-Q10", "TraceReportingValue", "O-V10"),
    PublicQueryDescriptor("O-Q11", "GetCorrectionIntegrity", "O-V11"),
)

PUBLIC_QUERY_REGISTRY = MappingProxyType(
    {descriptor.query_id: descriptor for descriptor in _DESCRIPTORS}
)

if len(PUBLIC_QUERY_REGISTRY) != 11 or len(
    {item.view_id for item in PUBLIC_QUERY_REGISTRY.values()}
) != 11:
    raise RuntimeError("Artifact O registry must contain eleven one-to-one entries")


def resolve_public_query(query_id: str) -> PublicQueryDescriptor:
    """Resolve only an exact Artifact O query identifier."""

    try:
        return PUBLIC_QUERY_REGISTRY[cast(PublicQueryId, query_id)]
    except KeyError as error:
        raise ValueError(f"unsupported public query: {query_id}") from error
