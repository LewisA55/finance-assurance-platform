"""Closed package-path validation and Phase S1 path registries."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

S_METADATA_PATHS = (
    "metadata/source-model.json",
    "metadata/data-dictionary.json",
    "metadata/relationships.json",
    "metadata/measures.json",
    "metadata/field-roles.json",
    "metadata/lineage.json",
    "metadata/consumer-suitability.json",
    "metadata/validation-checks.json",
)
S_SQL_PATHS = (
    "examples/starter-queries.sql",
    "examples/reconciliation-queries.sql",
)
S_FIXED_CANONICAL_PATHS = (
    "README.md",
    "handoff-manifest.json",
    "limitations.json",
    *S_METADATA_PATHS,
    *S_SQL_PATHS,
)
S_DETACHED_INTEGRITY_PATHS = ("checksums.json", "handoff.digest")
S_NONCANONICAL_PATHS = (
    "source-model/noncanonical-cache.json",
    "source-model/warehouse/finance-assurance.duckdb",
    "excel/finance-assurance-data-pack.xlsx",
    "excel/noncanonical-workbook.json",
)


def validate_package_path(value: str) -> str:
    if not value or not value.isascii() or "\\" in value:
        raise ValueError("package path must be non-empty ASCII POSIX text")
    if re.match(r"^[A-Za-z]:", value) or value.startswith("/"):
        raise ValueError("package path must be relative")
    if "//" in value or value.endswith("/"):
        raise ValueError("package path contains an empty segment")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("package path is not normalized")
    if path.as_posix() != value:
        raise ValueError("package path is not canonical POSIX text")
    return value


def validate_static_path_registries() -> None:
    all_paths = (
        *S_FIXED_CANONICAL_PATHS,
        *S_DETACHED_INTEGRITY_PATHS,
        *S_NONCANONICAL_PATHS,
    )
    if len(all_paths) != len(set(all_paths)):
        raise ValueError("Artifact S static path registries overlap")
    for path in all_paths:
        validate_package_path(path)


validate_static_path_registries()
