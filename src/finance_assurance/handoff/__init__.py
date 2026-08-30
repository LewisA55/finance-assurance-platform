"""Artifact S local analytical handoff contracts and Phase S1 registries."""

from finance_assurance.handoff.authorities import (
    AUTHORITY_DIRECTORY,
    AUTHORITY_SPECS,
    load_json_authority,
    read_authority_bytes,
    split_sql_authority,
    validate_authorities,
)
from finance_assurance.handoff.contracts import (
    BuildLocalAnalyticalHandoff,
    BuildLocalAnalyticalHandoffResult,
    HandoffOperationFailure,
    ReproduceLocalAnalyticalHandoff,
    ReproduceLocalAnalyticalHandoffResult,
    VerifyLocalAnalyticalHandoff,
    VerifyLocalAnalyticalHandoffResult,
)
from finance_assurance.handoff.digests import (
    canonical_json_file_bytes,
    logical_workbook_digest,
    typed_rows_digest,
    validate_workbook_vectors,
)
from finance_assurance.handoff.failure_registry import FAILURE_REGISTRY
from finance_assurance.handoff.profiles import (
    AUDIT_RENDERER_PROFILE,
    AUDIT_RENDERER_PROFILE_HASH,
    XLSX_TYPE_MAP,
    XLSX_TYPE_MAP_HASH,
    XLSX_WRITER_PROFILE,
    XLSX_WRITER_PROFILE_HASH,
)
from finance_assurance.handoff.service import (
    LocalAnalyticalHandoffError,
    LocalAnalyticalHandoffService,
    verify_local_analytical_handoff,
)

__all__ = [
    "AUDIT_RENDERER_PROFILE",
    "AUDIT_RENDERER_PROFILE_HASH",
    "AUTHORITY_DIRECTORY",
    "AUTHORITY_SPECS",
    "FAILURE_REGISTRY",
    "XLSX_TYPE_MAP",
    "XLSX_TYPE_MAP_HASH",
    "XLSX_WRITER_PROFILE",
    "XLSX_WRITER_PROFILE_HASH",
    "BuildLocalAnalyticalHandoff",
    "BuildLocalAnalyticalHandoffResult",
    "HandoffOperationFailure",
    "LocalAnalyticalHandoffError",
    "LocalAnalyticalHandoffService",
    "ReproduceLocalAnalyticalHandoff",
    "ReproduceLocalAnalyticalHandoffResult",
    "VerifyLocalAnalyticalHandoff",
    "VerifyLocalAnalyticalHandoffResult",
    "canonical_json_file_bytes",
    "load_json_authority",
    "logical_workbook_digest",
    "read_authority_bytes",
    "split_sql_authority",
    "typed_rows_digest",
    "validate_authorities",
    "validate_workbook_vectors",
    "verify_local_analytical_handoff",
]
