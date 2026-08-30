"""Build bounded Artifact S v0.12 executable logical authority state."""

from __future__ import annotations

import copy
from typing import Any

from finance_assurance.runtime.canonical import canonical_sha256

from .v09_authority_builder import write_json
from .v11_authority_builder import build_context as build_v11_context
from .v11_authority_builder import build_documents

CONTEXT_CONTRACT_VERSION = "handoff-mutation-positive-context@v4"

SEAL_LOCATIONS = {
    "r_model_canonical_digest": (
        "SOURCE_MODEL",
        "checksums.json",
        "canonical_payload_digest",
    ),
    "r_model_checksums_digest": (
        "SOURCE_MODEL",
        "checksums.json",
        "checksum_ledger_digest",
    ),
    "r_model_digest": ("SOURCE_MODEL", "model.digest", "value"),
    "r_cache_logical_digest": (
        "SOURCE_HANDOFF",
        "source-model/noncanonical-cache.json",
        "cache_logical_digest",
    ),
    "r_cache_manifest_digest": (
        "SOURCE_HANDOFF",
        "source-model/noncanonical-cache.json",
        "manifest_digest",
    ),
    "staged_r_cache_logical_digest": (
        "STAGING",
        "source-model/noncanonical-cache.json",
        "cache_logical_digest",
    ),
    "staged_r_cache_manifest_digest": (
        "STAGING",
        "source-model/noncanonical-cache.json",
        "manifest_digest",
    ),
    "s_canonical_digest": (
        "SOURCE_HANDOFF",
        "checksums.json",
        "canonical_payload_digest",
    ),
    "s_checksums_digest": (
        "SOURCE_HANDOFF",
        "checksums.json",
        "checksum_ledger_digest",
    ),
    "handoff_digest": ("SOURCE_HANDOFF", "handoff.digest", "value"),
    "xlsx_binary_digest": (
        "SOURCE_HANDOFF",
        "excel/noncanonical-workbook.json",
        "xlsx_binary_digest",
    ),
    "xlsx_logical_digest": (
        "SOURCE_HANDOFF",
        "excel/noncanonical-workbook.json",
        "xlsx_logical_digest",
    ),
    "s_noncanonical_manifest_digest": (
        "SOURCE_HANDOFF",
        "excel/noncanonical-workbook.json",
        "manifest_digest",
    ),
    "staged_canonical_digest": (
        "STAGING",
        "checksums.json",
        "canonical_payload_digest",
    ),
    "staged_checksums_digest": (
        "STAGING",
        "checksums.json",
        "checksum_ledger_digest",
    ),
    "staged_handoff_digest": ("STAGING", "handoff.digest", "value"),
}


def seal_target_ref(key: str) -> str:
    """Return the logical authority coordinate for one seal value."""

    realm, document, field = SEAL_LOCATIONS[key]
    return f"{realm}::{document}#/{field}"


def read_seal(context: dict[str, Any], key: str) -> str:
    realm, document, field = SEAL_LOCATIONS[key]
    return context["json_roots"][realm][document][field]


def _r_model_preimage(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest": context["json_roots"]["SOURCE_MODEL"]["model-manifest.json"],
        "files": {
            key.removeprefix("SOURCE_MODEL::"): value
            for key, value in context["direct_targets"].items()
            if key.startswith("SOURCE_MODEL::")
            and "warehouse/finance-assurance.duckdb" not in key
        },
    }


def _s_canonical_preimage(context: dict[str, Any]) -> dict[str, Any]:
    excluded = {
        "checksums.json",
        "handoff.digest",
        "excel/noncanonical-workbook.json",
        "source-model/noncanonical-cache.json",
    }
    return {
        "root": {
            key: value
            for key, value in context["json_roots"]["SOURCE_HANDOFF"].items()
            if key not in excluded
        },
        "examples": {
            key.removeprefix("SOURCE_HANDOFF::"): value
            for key, value in context["direct_targets"].items()
            if key.startswith("SOURCE_HANDOFF::examples/")
        },
    }


def _xlsx_preimage(context: dict[str, Any]) -> dict[str, Any]:
    return {
        key.removeprefix("SOURCE_HANDOFF::"): value
        for key, value in context["direct_targets"].items()
        if "excel/finance-assurance-data-pack.xlsx" in key
    }


def _staged_preimage(context: dict[str, Any]) -> dict[str, Any]:
    excluded = {
        "checksums.json",
        "handoff.digest",
        "source-model/noncanonical-cache.json",
    }
    return {
        key: value
        for key, value in context["json_roots"]["STAGING"].items()
        if key not in excluded
    }


def _r_model_values(context: dict[str, Any]) -> dict[str, str]:
    canonical = canonical_sha256(_r_model_preimage(context))
    checksums = canonical_sha256({"r_model": canonical})
    return {
        "r_model_canonical_digest": canonical,
        "r_model_checksums_digest": checksums,
        "r_model_digest": canonical_sha256({"r_checksums": checksums}),
    }


def _cache_preimage(context: dict[str, Any], realm: str) -> dict[str, Any]:
    prefix = f"{realm}::source-model/warehouse/finance-assurance.duckdb::"
    return {
        "manifest": context["json_roots"]["SOURCE_MODEL"][
            "noncanonical-cache.json"
        ],
        "duckdb": {
            key.removeprefix(f"{realm}::"): value
            for key, value in context["direct_targets"].items()
            if key.startswith(prefix)
        },
    }


def _r_cache_values(context: dict[str, Any]) -> dict[str, str]:
    logical = canonical_sha256(_cache_preimage(context, "SOURCE_HANDOFF"))
    return {
        "r_cache_logical_digest": logical,
        "r_cache_manifest_digest": canonical_sha256({"r_cache": logical}),
    }


def _staged_r_cache_values(context: dict[str, Any]) -> dict[str, str]:
    logical = canonical_sha256(_cache_preimage(context, "STAGING"))
    return {
        "staged_r_cache_logical_digest": logical,
        "staged_r_cache_manifest_digest": canonical_sha256(
            {"r_cache": logical}
        ),
    }


def _s_canonical_values(context: dict[str, Any]) -> dict[str, str]:
    canonical = canonical_sha256(_s_canonical_preimage(context))
    checksums = canonical_sha256({"s_canonical": canonical})
    return {
        "s_canonical_digest": canonical,
        "s_checksums_digest": checksums,
        "handoff_digest": canonical_sha256({"checksums": checksums}),
    }


def _xlsx_values(context: dict[str, Any]) -> dict[str, str]:
    binary = canonical_sha256(_xlsx_preimage(context))
    return {
        "xlsx_binary_digest": binary,
        "xlsx_logical_digest": canonical_sha256({"xlsx": binary}),
    }


def _noncanonical_manifest_value(
    r_cache_manifest_digest: str,
    xlsx_binary_digest: str,
    xlsx_logical_digest: str,
) -> str:
    return canonical_sha256(
        {
            "r_cache": r_cache_manifest_digest,
            "xlsx_binary": xlsx_binary_digest,
            "xlsx_logical": xlsx_logical_digest,
        }
    )


def _staged_values(context: dict[str, Any]) -> dict[str, str]:
    canonical = canonical_sha256(_staged_preimage(context))
    checksums = canonical_sha256({"staged": canonical})
    return {
        "staged_canonical_digest": canonical,
        "staged_checksums_digest": checksums,
        "staged_handoff_digest": canonical_sha256({"checksums": checksums}),
    }


def compute_seal_values(context: dict[str, Any]) -> dict[str, str]:
    """Compute the complete positive seal state with the reseal algorithms."""

    values = {
        **_r_model_values(context),
        **_r_cache_values(context),
        **_staged_r_cache_values(context),
        **_s_canonical_values(context),
        **_xlsx_values(context),
        **_staged_values(context),
    }
    values["s_noncanonical_manifest_digest"] = _noncanonical_manifest_value(
        values["r_cache_manifest_digest"],
        values["xlsx_binary_digest"],
        values["xlsx_logical_digest"],
    )
    return values


def _install_seal_documents(
    context: dict[str, Any], values: dict[str, str]
) -> None:
    for key, value in values.items():
        realm, document, field = SEAL_LOCATIONS[key]
        context["json_roots"][realm].setdefault(document, {})[field] = value


def build_context(vectors: list[dict[str, Any]]) -> dict[str, Any]:
    context = copy.deepcopy(build_v11_context(vectors))
    context["contract_version"] = CONTEXT_CONTRACT_VERSION
    context.pop("seal_state", None)
    context["semantic_constraints"] = {
        "excel_max_rows": 1_048_576,
        "excel_header_rows": 1,
        "safe_integer_max": 9_007_199_254_740_991,
        "supported_writer_profile_refs": ["XLSXWRITER-3.2.9@v1"],
        "source_cache_profile_version": 1,
    }
    context["seal_bindings"] = {
        key: seal_target_ref(key) for key in SEAL_LOCATIONS
    }
    values = compute_seal_values(context)
    _install_seal_documents(context, values)
    context["direct_targets"]["REQUEST::expected_model_digest"] = {
        "kind": "TEXT",
        "value": values["r_model_digest"],
    }
    context["direct_targets"]["REQUEST::expected_handoff_digest"] = {
        "kind": "TEXT",
        "value": values["handoff_digest"],
    }
    return context


def main() -> None:
    vectors = build_documents()
    write_json("mutation-positive-context-v4.json", build_context(vectors))


if __name__ == "__main__":
    main()
