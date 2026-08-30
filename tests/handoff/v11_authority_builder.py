"""Build bounded Artifact S v0.11 authenticated logical authorities."""

from __future__ import annotations

import copy
import json
from typing import Any

from finance_assurance.digestion.contracts import (
    ModelManifest,
    NoncanonicalCacheManifest,
    RelationshipPlanEntry,
    SemanticCatalogue,
)
from finance_assurance.digestion.service import (
    CONSUMER_CAPABILITIES,
    FORMAT_HINTS,
)
from finance_assurance.digestion.writer import PARQUET_WRITER_PROFILE
from finance_assurance.exports.contracts import ChecksumEntry, ChecksumLedger
from finance_assurance.exports.serialization import (
    canonical_json_bytes,
    sha256_bytes,
)
from finance_assurance.handoff.metadata import MetadataDocument
from finance_assurance.runtime.canonical import canonical_sha256

from .v09_authority_builder import DIGESTS, write_json
from .v10_authority_builder import (
    _provenance,
)
from .v10_authority_builder import (
    build_context as build_v10_context,
)
from .v10_authority_builder import (
    build_documents as build_v10_documents,
)

VECTOR_CONTRACT_VERSION = "handoff-metadata-positive-logical-vectors@v4"
CONTEXT_CONTRACT_VERSION = "handoff-mutation-positive-context@v3"
HANDOFF_REF = "S-V11-POSITIVE"
SOURCE_MODEL_REF = "R-V11-POSITIVE"
SOURCE_PACKAGE_REF = "P-V11-POSITIVE"
SOURCE_PACKAGE_DIGEST = DIGESTS[1]
SYNTHETIC_NOTICE = (
    "Synthetic bounded C-001 and CT-1 data for governed local analysis only."
)


def _canonical_scope(table_entries: list[dict[str, Any]]) -> tuple[str, ...]:
    paths = {
        "README.txt",
        "model-manifest.json",
        "relationships.json",
        "semantic-model.json",
    }
    for item in table_entries:
        paths.add(item["source_schema_path"])
        paths.add(item["csv_path"])
        paths.add(item["parquet_path"])
    return tuple(sorted(paths))


def _readme(manifest: ModelManifest) -> bytes:
    lines = (
        "Finance & Assurance Platform - Consumer Model",
        f"Model: {manifest.model_ref}",
        f"Contract: {manifest.contract_version}",
        f"Profile: {manifest.profile_id}@v{manifest.profile_version}",
        f"Source package: {manifest.source_package_ref}",
        f"Source digest: {manifest.source_package_digest}",
        "Synthetic data: true",
        f"Notice: {manifest.synthetic_data_notice}",
        "Canonical depth: bounded C-001 and CT-1 reference cases.",
        "This directory is a rebuildable projection and is not runtime authority.",
    )
    return ("\n".join(lines) + "\n").encode("ascii")


def _source_inputs(
    base_vectors: list[dict[str, Any]],
) -> tuple[dict[str, bytes], dict[str, Any], str]:
    base = base_vectors[0]["construction_inputs"]["source_document_payloads"]
    base_manifest = base["source-model/model-manifest.json"]
    base_semantic = base["source-model/semantic-model.json"]
    base_cache = base["source-model/noncanonical-cache.json"]
    table_entries = base_manifest["table_entries"]
    semantic_tables = [
        {
            key: item[key]
            for key in (
                "source_coordinate",
                "physical_alias",
                "display_label",
                "primary_consumption_class",
                "included_by_profile",
                "semantic_owners",
                "default_sort",
                "column_names",
            )
        }
        for item in base_semantic["tables"]
    ]
    relationships = [
        RelationshipPlanEntry.model_validate_json(json.dumps(item)).model_dump(
            mode="json"
        )
        for item in base["source-model/relationships.json"]
    ]
    semantic = SemanticCatalogue.model_validate_json(
        json.dumps(
            {
                "catalogue_contract_version": "semantic-catalogue@v1",
                "model_ref": SOURCE_MODEL_REF,
                "profile_coordinate": {
                    "profile_id": "LINEAGE",
                    "profile_version": 1,
                },
                "source_package_digest": SOURCE_PACKAGE_DIGEST,
                "tables": semantic_tables,
                "columns": base_semantic["columns"],
                "relationships": relationships,
                "measures": base_semantic["measures"],
                "format_hints": FORMAT_HINTS,
                "consumer_capabilities": CONSUMER_CAPABILITIES,
            }
        )
    )
    manifest = ModelManifest.model_validate_json(
        json.dumps(
            {
                "contract_version": "consumer-model@v1",
                "model_ref": SOURCE_MODEL_REF,
                "source_package_ref": SOURCE_PACKAGE_REF,
                "source_package_digest": SOURCE_PACKAGE_DIGEST,
                "source_export_ref": SOURCE_PACKAGE_REF,
                "source_query_revision": 42,
                "source_semantic_as_of": "2026-06-30T23:59:59Z",
                "source_scenario_set_digest": DIGESTS[7],
                "source_compatibility_mode": "EXACT_ORIGINAL",
                "source_registry_coordinates": [
                    {"registry_id": "P-EVIDENCE", "registry_version": 1},
                    {"registry_id": "Q-ANALYTICS", "registry_version": 1},
                ],
                "source_relationship_contract_version": 2,
                "source_verification_status": "VERIFIED",
                "source_verification_contract": "governed-export-verification@v1",
                "profile_id": "LINEAGE",
                "profile_version": 1,
                "requested_formats": ["CSV", "PARQUET", "DUCKDB"],
                "producer_release": "finance-assurance-v11-logical-source@v1",
                "built_at": "2026-08-20T15:00:00Z",
                "parquet_writer_profile_ref": "PYARROW-25@v1",
                "parquet_writer_profile_hash": PARQUET_WRITER_PROFILE.profile_hash,
                "synthetic_data": True,
                "synthetic_data_notice": SYNTHETIC_NOTICE,
                "table_entries": table_entries,
                "semantic_catalogue_path": "semantic-model.json",
                "relationship_catalogue_path": "relationships.json",
                "checksum_ledger_path": "checksums.json",
                "canonical_digest_scope": _canonical_scope(table_entries),
                "noncanonical_cache_manifest_path": "noncanonical-cache.json",
            }
        )
    )
    semantic_payload = semantic.model_dump(mode="json")
    manifest_payload = manifest.model_dump(mode="json")
    relationship_payload = relationships
    document_bytes: dict[str, bytes] = {
        "source-model/model-manifest.json": canonical_json_bytes(manifest_payload),
        "source-model/semantic-model.json": canonical_json_bytes(semantic_payload),
        "source-model/relationships.json": canonical_json_bytes(
            relationship_payload
        ),
    }

    known_hashes = {
        "README.txt": sha256_bytes(_readme(manifest)),
        "model-manifest.json": sha256_bytes(
            document_bytes["source-model/model-manifest.json"]
        ),
        "relationships.json": sha256_bytes(
            document_bytes["source-model/relationships.json"]
        ),
        "semantic-model.json": sha256_bytes(
            document_bytes["source-model/semantic-model.json"]
        ),
    }
    for item in table_entries:
        known_hashes[item["source_schema_path"]] = item["source_schema_hash"]
        known_hashes[item["csv_path"]] = item["csv_hash"]
        known_hashes[item["parquet_path"]] = item["parquet_hash"]
    checksums = ChecksumLedger(
        checksum_contract_version=1,
        files=tuple(
            ChecksumEntry(relative_path=path, sha256=known_hashes[path])
            for path in manifest.canonical_digest_scope
        ),
    )
    checksum_payload = checksums.model_dump(mode="json")
    checksum_bytes = canonical_json_bytes(checksum_payload)
    model_digest = sha256_bytes(checksum_bytes)
    document_bytes["source-model/checksums.json"] = checksum_bytes
    document_bytes["source-model/model.digest"] = (
        model_digest + "\n"
    ).encode("ascii")

    semantic_table_by_coordinate = {
        (
            item["source_coordinate"]["registry_id"],
            item["source_coordinate"]["dataset_id"],
        ): item
        for item in base_semantic["tables"]
    }
    cache = NoncanonicalCacheManifest.model_validate_json(
        json.dumps(
            {
                "cache_contract_version": "duckdb-cache-manifest@v1",
                "model_ref": SOURCE_MODEL_REF,
                "source_package_digest": SOURCE_PACKAGE_DIGEST,
                "profile_coordinate": {
                    "profile_id": "LINEAGE",
                    "profile_version": 1,
                },
                "database_path": "warehouse/finance-assurance.duckdb",
                "database_sha256": base_cache["database_sha256"],
                "database_byte_count": base_cache["database_byte_count"],
                "engine": "DUCKDB",
                "engine_version": "1.5.5",
                "storage_compatibility_version": "v1.5.0",
                "database_storage_version": "v1.5.0+",
                "build_source_format": "PARQUET",
                "schema_names": ["p_evidence_v1", "q_analytics_v1", "model_meta"],
                "metadata_table_names": [
                    "cache_profile",
                    "documents",
                    "table_bindings",
                ],
                "table_entries": [
            {
                "source_coordinate": {
                    "registry_id": item["source_registry_id"],
                    "registry_version": item["source_registry_version"],
                    "dataset_id": item["source_dataset_id"],
                    "dataset_version": item["source_dataset_version"],
                },
                "duckdb_schema": item["duckdb_schema"],
                "duckdb_object": item["duckdb_object"],
                "parquet_path": item["parquet_path"],
                "parquet_hash": item["parquet_hash"],
                "row_count": item["row_count"],
                "column_names": semantic_table_by_coordinate[
                    (item["source_registry_id"], item["source_dataset_id"])
                ]["column_names"],
                "logical_table_digest": item["logical_table_digest"],
                "technical_projection_digest": item[
                    "technical_projection_digest"
                ],
            }
            for item in table_entries
                ],
                "read_only_consumer_required": True,
            }
        )
    )
    cache_payload = cache.model_dump(mode="json")
    document_bytes["source-model/noncanonical-cache.json"] = canonical_json_bytes(
        cache_payload
    )
    payloads: dict[str, Any] = {
        "source-model/model-manifest.json": manifest_payload,
        "source-model/semantic-model.json": semantic_payload,
        "source-model/relationships.json": relationship_payload,
        "source-model/checksums.json": checksum_payload,
        "source-model/model.digest": model_digest + "\n",
        "source-model/noncanonical-cache.json": cache_payload,
    }
    return document_bytes, payloads, model_digest


def _document_bindings(
    paths: list[str], document_bytes: dict[str, bytes]
) -> list[dict[str, Any]]:
    versions = {
        "source-model/model-manifest.json": "consumer-model@v1",
        "source-model/semantic-model.json": "semantic-catalogue@v1",
        "source-model/relationships.json": "relationship-catalogue@v1",
        "source-model/checksums.json": "checksum-ledger@v1",
        "source-model/model.digest": "detached-model-digest@v1",
        "source-model/noncanonical-cache.json": "duckdb-cache-manifest@v1",
    }
    return [
        {
            "path": path,
            "contract_version": versions[path],
            "sha256": sha256_bytes(document_bytes[path]),
        }
        for path in paths
    ]


def _v11_provenance(
    path: str, payload: dict[str, Any], source_payloads: dict[str, Any]
) -> list[dict[str, Any]]:
    rows = _provenance(payload, path, source_payloads)
    for row in rows:
        row["algorithm_ref"] = row["algorithm_ref"].replace("@v2", "@v3")
        target = row["target_json_pointer"]
        parts = target.split("/")
        if (
            path == "metadata/data-dictionary.json"
            and len(parts) >= 5
            and parts[2] == "tables"
            and parts[4] in {"primary_key", "unique_keys"}
        ):
            suffix = "/".join(parts[4:])
            row["source_pointers"] = [
                {
                    "pointer_kind": "JSON_POINTER",
                    "source_document_path": "source-model/model-manifest.json",
                    "json_pointer": f"/table_entries/{parts[3]}/{suffix}",
                }
            ]
            row["algorithm_ref"] = "R-MANIFEST-KEY-PROJECTION@v1"
        if target in {
            "/payload/r_cache_binding/table_count",
            "/payload/r_cache_binding/table_bindings_digest",
        }:
            row["source_pointers"] = [
                {
                    "pointer_kind": "JSON_POINTER",
                    "source_document_path": "source-model/noncanonical-cache.json",
                    "json_pointer": "/table_entries",
                }
            ]
            row["algorithm_ref"] = (
                "R-CACHE-TABLE-COUNT@v1"
                if target.endswith("/table_count")
                else "R-CACHE-TABLE-BINDINGS-DIGEST@v1"
            )
        if (
            path == "metadata/lineage.json"
            and target == "/payload/evidence_status_fields"
        ):
            row["source_pointers"] = [
                {
                    "pointer_kind": "JSON_POINTER",
                    "source_document_path": "source-model/semantic-model.json",
                    "json_pointer": "/columns",
                }
            ]
            row["algorithm_ref"] = "R-LINEAGE-EVIDENCE-STATUS-SELECTION@v1"
    return rows


def build_documents() -> list[dict[str, Any]]:
    base_vectors = build_v10_documents()
    document_bytes, source_payloads, model_digest = _source_inputs(base_vectors)
    cache_entries = source_payloads["source-model/noncanonical-cache.json"][
        "table_entries"
    ]
    vectors: list[dict[str, Any]] = []
    for index, base in enumerate(base_vectors, start=1):
        path = base["metadata_path"]
        payload = copy.deepcopy(base["document"]["payload"])
        if path == "metadata/source-model.json":
            payload["r_cache_binding"] = {
                key: value
                for key, value in source_payloads[
                    "source-model/noncanonical-cache.json"
                ].items()
                if key != "table_entries"
            } | {
                "table_count": len(cache_entries),
                "table_bindings_digest": canonical_sha256(cache_entries),
            }
        document_paths = [
            item["path"] for item in base["document"]["source_documents"]
        ]
        bindings = _document_bindings(document_paths, document_bytes)
        selected_payloads = {key: source_payloads[key] for key in document_paths}
        provenance = _v11_provenance(path, payload, source_payloads)
        handoff_binding = {
            "handoff_ref": HANDOFF_REF,
            "source_model_ref": SOURCE_MODEL_REF,
            "source_model_digest": model_digest,
            "source_package_digest": SOURCE_PACKAGE_DIGEST,
        }
        body = {
            "contract_version": base["document"]["contract_version"],
            "handoff_binding": handoff_binding,
            "source_documents": bindings,
            "source_datasets": base["document"]["source_datasets"],
            "field_provenance": provenance,
            "payload": payload,
        }
        document = MetadataDocument.model_validate_json(
            json.dumps(body, ensure_ascii=True)
        ).model_dump(mode="json")
        construction_inputs = {
            **base["construction_inputs"],
            "handoff_binding": handoff_binding,
            "source_documents": bindings,
            "source_document_payloads": selected_payloads,
            "source_document_bytes_ascii": {
                key: document_bytes[key].decode("ascii") for key in document_paths
            },
            "payload_projection": payload,
            "provenance_mapping": provenance,
        }
        vector = {
            "vector_ref": f"S-MV11-{index:02d}",
            "metadata_path": path,
            "construction_inputs": construction_inputs,
            "document": document,
            "expected_object_digest": canonical_sha256(document),
        }
        vector["expected_vector_digest"] = canonical_sha256(vector)
        vectors.append(vector)
    return vectors


def _component_preimage(context: dict[str, Any], component: str) -> Any:
    direct = context["direct_targets"]
    if component == "R_MODEL":
        return {
            "root": context["json_roots"]["SOURCE_MODEL"],
            "targets": {
                key: value for key, value in direct.items() if key.startswith("SOURCE_MODEL::")
            },
        }
    if component == "R_CACHE":
        return {
            "manifest": context["json_roots"]["SOURCE_MODEL"][
                "noncanonical-cache.json"
            ],
            "duckdb": {
                key: value
                for key, value in direct.items()
                if "warehouse/finance-assurance.duckdb" in key
            },
        }
    if component == "S_CANONICAL":
        return {
            "root": context["json_roots"]["SOURCE_HANDOFF"],
            "targets": {
                key: value
                for key, value in direct.items()
                if key.startswith("SOURCE_HANDOFF::examples/")
            },
        }
    if component == "XLSX":
        return {
            key: value
            for key, value in direct.items()
            if "excel/finance-assurance-data-pack.xlsx" in key
        }
    if component == "STAGED_CANONICAL":
        return context["json_roots"]["STAGING"]
    raise ValueError(f"unknown v0.11 digest component: {component}")


def build_context(vectors: list[dict[str, Any]]) -> dict[str, Any]:
    context = build_v10_context(vectors)
    context["contract_version"] = CONTEXT_CONTRACT_VERSION
    context["request_mutations"] = {
        "USE_RESEALED_MUTANT_HANDOFF_DIGEST": {
            "target_ref": "REQUEST::expected_handoff_digest",
            "operator": "SET_REQUEST_FIELD",
            "mutation": "TEXT:CURRENT_RESEALED_HANDOFF_DIGEST",
        },
        "SET_UNSUPPORTED_WRITER_COORDINATE": {
            "target_ref": "REQUEST::xlsx_writer_profile_ref",
            "operator": "SET_REQUEST_FIELD",
            "mutation": "TEXT:XLSXWRITER-UNSUPPORTED@v1",
        },
    }
    context["reseal_contracts"] = {
        "RESEAL_R_CACHE_AND_S_NONCANONICAL_MANIFEST": [
            "R01_RECOMPUTE_CACHE_LOGICAL",
            "R02_REWRITE_CACHE_MANIFEST",
            "R03_REWRITE_S_NONCANONICAL_MANIFEST",
            "R04_RETAIN_CANONICAL_HANDOFF_DIGEST",
        ],
        "RESEAL_S_CANONICAL": [
            "S01_CANONICALIZE_CHANGED_AUTHORITIES",
            "S02_RECOMPUTE_CANONICAL_CHECKSUMS",
            "S03_RECOMPUTE_HANDOFF_DIGEST",
        ],
        "RESEAL_S_XLSX_BINARY_MANIFEST_AND_HANDOFF": [
            "X01_RECOMPUTE_XLSX_BINARY_DIGEST",
            "X02_RECOMPUTE_XLSX_LOGICAL_DIGEST",
            "X03_REWRITE_XLSX_NONCANONICAL_MANIFEST",
            "X04_RETAIN_CANONICAL_HANDOFF_DIGEST",
        ],
        "RESEAL_R_MODEL": [
            "M01_CANONICALIZE_R_MANIFEST",
            "M02_RECOMPUTE_R_CHECKSUMS",
            "M03_RECOMPUTE_R_MODEL_DIGEST",
        ],
        "RESEAL_R_CACHE_ONLY": [
            "C01_RECOMPUTE_CACHE_LOGICAL",
            "C02_REWRITE_CACHE_MANIFEST",
        ],
        "RESEAL_STAGED_CANONICAL_TO_DIFFERENT_DIGEST": [
            "T01_CANONICALIZE_STAGED_JSON",
            "T02_RECOMPUTE_STAGED_CHECKSUMS",
            "T03_RECOMPUTE_STAGED_HANDOFF_DIGEST",
        ],
    }
    r_model = canonical_sha256(_component_preimage(context, "R_MODEL"))
    r_cache = canonical_sha256(_component_preimage(context, "R_CACHE"))
    s_canonical = canonical_sha256(_component_preimage(context, "S_CANONICAL"))
    xlsx = canonical_sha256(_component_preimage(context, "XLSX"))
    staged = canonical_sha256(_component_preimage(context, "STAGED_CANONICAL"))
    context["seal_state"] = {
        "r_model_canonical_digest": r_model,
        "r_model_checksums_digest": canonical_sha256({"r_model": r_model}),
        "r_model_digest": canonical_sha256({"r_model_checksums": r_model}),
        "r_cache_logical_digest": r_cache,
        "r_cache_manifest_digest": canonical_sha256({"r_cache": r_cache}),
        "s_canonical_digest": s_canonical,
        "s_checksums_digest": canonical_sha256({"s_canonical": s_canonical}),
        "handoff_digest": canonical_sha256({"s_canonical": s_canonical}),
        "xlsx_binary_digest": xlsx,
        "xlsx_logical_digest": canonical_sha256({"xlsx": xlsx}),
        "s_noncanonical_manifest_digest": canonical_sha256(
            {"r_cache": r_cache, "xlsx": xlsx}
        ),
        "staged_canonical_digest": staged,
        "staged_checksums_digest": canonical_sha256({"staged": staged}),
        "staged_handoff_digest": canonical_sha256({"staged": staged}),
    }
    return context


def main() -> None:
    vectors = build_documents()
    write_json(
        "metadata-positive-logical-vectors-v4.json",
        {
            "contract_version": VECTOR_CONTRACT_VERSION,
            "vector_field_order": [
                "vector_ref",
                "metadata_path",
                "construction_inputs",
                "document",
                "expected_object_digest",
                "expected_vector_digest",
            ],
            "vectors": vectors,
        },
    )
    write_json("mutation-positive-context-v3.json", build_context(vectors))


if __name__ == "__main__":
    main()
