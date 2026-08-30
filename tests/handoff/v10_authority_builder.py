"""Deterministically generate bounded Artifact S v0.10 logical authorities."""

from __future__ import annotations

import json
from typing import Any

from finance_assurance.digestion.registry import (
    COLUMN_ROLE_REGISTRY,
    MEASURE_REGISTRY,
    datasets_for_profile,
    registry_contract_hash,
    relationship_plan,
)
from finance_assurance.handoff.metadata import MetadataDocument
from finance_assurance.runtime.canonical import canonical_sha256

from .v09_authority_builder import (
    AUTHORITY,
    DIGESTS,
    DUCKDB_AMOUNT_TARGET,
    STAGING_DUCKDB_AMOUNT_TARGET,
    XLSX_AMOUNT_TARGET,
    XLSX_CORE_TARGET,
    XLSX_EXTERNAL_LINK_TARGET,
    XLSX_NULL_TARGET,
    consumers,
    coordinate,
    dataset_binding,
    dictionary_table,
    source_documents,
    source_table,
    write_json,
)

VECTOR_CONTRACT_VERSION = "handoff-metadata-positive-logical-vectors@v3"
CONTEXT_CONTRACT_VERSION = "handoff-mutation-positive-context@v2"
HANDOFF_REF = "S-V10-POSITIVE"
SOURCE_MODEL_REF = "R-V10-POSITIVE"
SOURCE_PACKAGE_AMOUNT_TARGET = (
    "SOURCE_PACKAGE::P-EVIDENCE@v1/P-D06@v1::"
    "SEL-C1-V1-REVENUE::amount_minor"
)


def _load_json(name: str) -> dict[str, Any]:
    return json.loads((AUTHORITY / name).read_text(encoding="ascii"))


def _escaped(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _covered_paths(value: Any, path: str = "/payload") -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if isinstance(value, list):
        result.append((path, "ARRAY_ORDER"))
        for index, item in enumerate(value):
            result.extend(_covered_paths(item, f"{path}/{index}"))
    elif isinstance(value, dict):
        for key, item in value.items():
            result.extend(_covered_paths(item, f"{path}/{_escaped(key)}"))
    else:
        result.append((path, "VALUE"))
    return result


def _field_role_format_hints(item: dict[str, Any]) -> list[str]:
    hints: list[str] = []
    if item["source_type"] == "timestamp":
        hints.append("TIMESTAMP_UTC_MICROSECOND")
    if item["source_type"] == "integer":
        if item["column_role"] == "DOMAIN_MEASURE_INPUT":
            hints.append("MONEY_INTEGER_MINOR_UNITS")
        hints.append("RAW_INTEGER_SUMMARIZATION_NONE")
    return hints


def _field_role_projection(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: item[key]
        for key in (
            "source_coordinate",
            "source_name",
            "source_type",
            "physical_type",
            "column_role",
            "default_visibility",
            "default_summarization",
            "display_label",
            "display_folder",
        )
    } | {"format_hints": _field_role_format_hints(item)}


def _dictionary_column_projection(item: dict[str, Any], ordinal: int) -> dict[str, Any]:
    return {
        **item,
        "ordinal": ordinal,
        "xlsx_storage_mode": {
            "boolean": "BOOLEAN_NATIVE",
            "date": "TEXT_DATE_ISO",
            "integer": "NUMBER_EXACT",
            "timestamp": "TEXT_TIMESTAMP_UTC",
        }.get(item["source_type"], "TEXT_EXACT"),
    }


def _source_documents_payloads(
    table_entries: list[dict[str, Any]],
    semantic_tables: list[dict[str, Any]],
    semantic_columns: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    measures: list[dict[str, Any]],
    cache_binding: dict[str, Any],
    model_paths: list[str],
) -> dict[str, Any]:
    return {
        "source-model/model-manifest.json": {
            "profile_id": "LINEAGE",
            "profile_version": 1,
            "requested_formats": ["CSV", "PARQUET", "DUCKDB"],
            "r_paths": [path.removeprefix("source-model/") for path in model_paths],
            "table_entries": table_entries,
        },
        "source-model/semantic-model.json": {
            "tables": semantic_tables,
            "columns": semantic_columns,
            "measures": measures,
            "lineage_evidence_status_fields": [],
        },
        "source-model/relationships.json": relationships,
        "source-model/checksums.json": {"checksum_contract_version": "checksum-ledger@v1"},
        "source-model/model.digest": {"model_digest": DIGESTS[0]},
        "source-model/noncanonical-cache.json": cache_binding,
    }


def _semantic_column_index(columns: list[dict[str, Any]]) -> dict[tuple[str, str, str], int]:
    return {
        (
            item["source_coordinate"]["registry_id"],
            item["source_coordinate"]["dataset_id"],
            item["source_name"],
        ): index
        for index, item in enumerate(columns)
    }


def _relationship_index(
    relationships: list[dict[str, Any]],
) -> dict[str, int]:
    return {
        str(item["relationship_id"]): index for index, item in enumerate(relationships)
    }


def _guidance(path: str, target: str) -> bool:
    if path == "metadata/consumer-suitability.json":
        return True
    if path == "metadata/validation-checks.json":
        return True
    if path == "metadata/source-model.json" and target.startswith("/payload/r_paths"):
        return True
    if path == "metadata/data-dictionary.json" and (
        target.endswith("/ordinal") or target.endswith("/xlsx_storage_mode")
    ):
        return True
    if path == "metadata/field-roles.json" and "/format_hints" in target:
        return True
    return path == "metadata/lineage.json" and (
        target.endswith("/step_ordinal") or target.endswith("/direction")
    )


def _json_pointer(document: str, pointer: str) -> dict[str, Any]:
    return {
        "pointer_kind": "JSON_POINTER",
        "source_document_path": document,
        "json_pointer": pointer,
    }


def _validation_dataset_pointer(payload: dict[str, Any], target: str) -> dict[str, Any]:
    parts = target.removeprefix("/payload/checks/").split("/")
    check = payload["checks"][int(parts[0])]
    selector_ref = check["selector_refs"][0]
    selector = next(item for item in payload["selectors"] if item["selector_ref"] == selector_ref)
    registry_ref, dataset_ref = selector["source_coordinate"].split("/")
    field_name = "row_key"
    if "/result_columns/" in target:
        field_name = check["result_columns"][int(parts[2])]["name"]
    return {
        "pointer_kind": "DATASET_CELL",
        "source_coordinate": coordinate(
            dataset_ref.split("@")[0], registry_ref.split("@")[0]
        ),
        "selector_ref": selector_ref,
        "field_name": field_name,
    }


def _source_pointer(
    path: str,
    target: str,
    payload: dict[str, Any],
    source_payloads: dict[str, Any],
) -> list[dict[str, Any]]:
    relative = target.removeprefix("/payload")
    parts = relative.strip("/").split("/") if relative != "" else []
    relationships = source_payloads["source-model/relationships.json"]
    relationship_indices = _relationship_index(relationships)
    semantic_columns = source_payloads["source-model/semantic-model.json"]["columns"]
    column_indices = _semantic_column_index(semantic_columns)

    if path == "metadata/validation-checks.json":
        return [_validation_dataset_pointer(payload, target)]
    if path == "metadata/source-model.json":
        if relative.startswith("/r_cache_binding"):
            return [
                _json_pointer(
                    "source-model/noncanonical-cache.json",
                    relative.removeprefix("/r_cache_binding") or "/",
                )
            ]
        pointer = relative
        pointer = pointer.replace("/source_formats", "/requested_formats", 1)
        pointer = pointer.replace("/profile_coordinate/profile_id", "/profile_id", 1)
        pointer = pointer.replace(
            "/profile_coordinate/profile_version", "/profile_version", 1
        )
        return [_json_pointer("source-model/model-manifest.json", pointer)]
    if path == "metadata/data-dictionary.json":
        if parts[0] == "tables":
            return [
                _json_pointer(
                    "source-model/semantic-model.json",
                    "/tables"
                    if len(parts) == 1
                    else "/tables/" + "/".join(parts[1:]),
                )
            ]
        if parts[0] == "columns":
            if len(parts) == 1:
                return [_json_pointer("source-model/semantic-model.json", "/columns")]
            target_column = payload["columns"][int(parts[1])]
            source_index = column_indices[
                (
                    target_column["source_coordinate"]["registry_id"],
                    target_column["source_coordinate"]["dataset_id"],
                    target_column["source_name"],
                )
            ]
            if len(parts) == 2:
                return [_json_pointer("source-model/semantic-model.json", f"/columns/{source_index}")]
            return [
                _json_pointer(
                    "source-model/semantic-model.json",
                    f"/columns/{source_index}/" + "/".join(parts[2:]),
                )
            ]
    if path == "metadata/relationships.json":
        if len(parts) == 1:
            return [_json_pointer("source-model/relationships.json", "/")]
        return [
            _json_pointer(
                "source-model/relationships.json",
                "/" + "/".join(parts[1:]),
            )
        ]
    if path == "metadata/measures.json":
        if len(parts) == 1:
            return [_json_pointer("source-model/semantic-model.json", "/measures")]
        return [
            _json_pointer(
                "source-model/semantic-model.json",
                "/measures/" + "/".join(parts[1:]),
            )
        ]
    if path == "metadata/field-roles.json":
        if len(parts) == 1:
            return [_json_pointer("source-model/semantic-model.json", "/columns")]
        target_field = payload["fields"][int(parts[1])]
        source_index = column_indices[
            (
                target_field["source_coordinate"]["registry_id"],
                target_field["source_coordinate"]["dataset_id"],
                target_field["source_name"],
            )
        ]
        if len(parts) == 2:
            return [_json_pointer("source-model/semantic-model.json", f"/columns/{source_index}")]
        return [
            _json_pointer(
                "source-model/semantic-model.json",
                f"/columns/{source_index}/" + "/".join(parts[2:]),
            )
        ]
    if path == "metadata/lineage.json":
        if parts[0] == "dataset_pointers":
            if len(parts) == 1:
                table_by_coordinate = {
                    (
                        item["source_coordinate"]["registry_id"],
                        item["source_coordinate"]["dataset_id"],
                    ): index
                    for index, item in enumerate(
                        source_payloads["source-model/semantic-model.json"]["tables"]
                    )
                }
                return [
                    _json_pointer(
                        "source-model/semantic-model.json",
                        "/tables/"
                        + str(
                            table_by_coordinate[
                                (
                                    item["source_coordinate"]["registry_id"],
                                    item["source_coordinate"]["dataset_id"],
                                )
                            ]
                        ),
                    )
                    for item in payload["dataset_pointers"]
                ]
            dataset = payload["dataset_pointers"][int(parts[1])]
            table_index = next(
                index
                for index, item in enumerate(
                    source_payloads["source-model/semantic-model.json"]["tables"]
                )
                if item["source_coordinate"] == dataset["source_coordinate"]
            )
            field = "physical_alias" if parts[2] == "r_table_alias" else parts[2]
            suffix = "" if len(parts) == 3 else "/" + "/".join(parts[3:])
            return [
                _json_pointer(
                    "source-model/semantic-model.json",
                    f"/tables/{table_index}/{field}{suffix}",
                )
            ]
        if parts[0] == "directed_join_steps":
            if len(parts) == 1:
                return [
                    _json_pointer(
                        "source-model/relationships.json",
                        f"/{relationship_indices[item['relationship_id']]}",
                    )
                    for item in payload["directed_join_steps"]
                ]
            step = payload["directed_join_steps"][int(parts[1])]
            source_index = relationship_indices[step["relationship_id"]]
            mapping = {
                "relationship_id": "relationship_id",
                "from_fields": "from_columns",
                "to_fields": "to_columns",
                "projected_key_ref": "projected_key_ref",
            }
            if parts[2] in mapping:
                return [
                    _json_pointer(
                        "source-model/relationships.json",
                        f"/{source_index}/{mapping[parts[2]]}"
                        + ("/" + "/".join(parts[3:]) if len(parts) > 3 else ""),
                    )
                ]
            if parts[2] == "from_coordinate":
                if len(parts) > 3 and parts[3] in {"registry_version", "dataset_version"}:
                    table_index = next(
                        index
                        for index, item in enumerate(
                            source_payloads["source-model/semantic-model.json"][
                                "tables"
                            ]
                        )
                        if item["source_coordinate"]["registry_id"]
                        == relationships[source_index]["from_registry"]
                        and item["source_coordinate"]["dataset_id"]
                        == relationships[source_index]["from_dataset"]
                    )
                    return [
                        _json_pointer(
                            "source-model/semantic-model.json",
                            f"/tables/{table_index}/source_coordinate/{parts[3]}",
                        )
                    ]
                if len(parts) > 3 and parts[3] in {"registry_id", "dataset_id"}:
                    field = "from_registry" if parts[3] == "registry_id" else "from_dataset"
                    return [
                        _json_pointer("source-model/relationships.json", f"/{source_index}/{field}")
                    ]
                return [
                    _json_pointer("source-model/relationships.json", f"/{source_index}/from_registry"),
                    _json_pointer("source-model/relationships.json", f"/{source_index}/from_dataset"),
                ]
            if parts[2] == "to_coordinate":
                if len(parts) > 3 and parts[3] in {"registry_version", "dataset_version"}:
                    table_index = next(
                        index
                        for index, item in enumerate(
                            source_payloads["source-model/semantic-model.json"][
                                "tables"
                            ]
                        )
                        if item["source_coordinate"]["registry_id"]
                        == relationships[source_index]["to_registry"]
                        and item["source_coordinate"]["dataset_id"]
                        == relationships[source_index]["to_dataset"]
                    )
                    return [
                        _json_pointer(
                            "source-model/semantic-model.json",
                            f"/tables/{table_index}/source_coordinate/{parts[3]}",
                        )
                    ]
                if len(parts) > 3 and parts[3] in {"registry_id", "dataset_id"}:
                    field = "to_registry" if parts[3] == "registry_id" else "to_dataset"
                    return [
                        _json_pointer("source-model/relationships.json", f"/{source_index}/{field}")
                    ]
                return [
                    _json_pointer("source-model/relationships.json", f"/{source_index}/to_registry"),
                    _json_pointer("source-model/relationships.json", f"/{source_index}/to_dataset"),
                ]
        if parts[0] == "evidence_status_fields":
            return [
                _json_pointer(
                    "source-model/semantic-model.json",
                    "/lineage_evidence_status_fields",
                )
            ]
    raise AssertionError(f"unmapped provenance target: {path} {target}")


def _provenance(
    payload: dict[str, Any],
    path: str,
    source_payloads: dict[str, Any],
) -> list[dict[str, Any]]:
    algorithms = {
        "metadata/source-model.json": "R-MANIFEST-BINDING@v2",
        "metadata/data-dictionary.json": "R-TABLE-COLUMN-PROJECTION@v2",
        "metadata/relationships.json": "R-RELATIONSHIP-PROJECTION@v2",
        "metadata/measures.json": "R-MEASURE-PROJECTION@v2",
        "metadata/field-roles.json": "R-FIELD-ROLE-PROJECTION@v2",
        "metadata/lineage.json": "R-LINEAGE-POINTERS@v2",
        "metadata/consumer-suitability.json": "S-CONSUMER-SUITABILITY@v1",
        "metadata/validation-checks.json": "S-VALIDATION-REGISTRY@v1",
    }
    rows = []
    for target, coverage in _covered_paths(payload):
        guidance = _guidance(path, target)
        rows.append(
            {
                "target_json_pointer": target,
                "coverage": coverage,
                "derivation_class": "S_GUIDANCE" if guidance else "R_PROJECTION",
                "source_pointers": []
                if guidance
                else _source_pointer(path, target, payload, source_payloads),
                "algorithm_ref": algorithms[path],
            }
        )
    return sorted(rows, key=lambda item: (item["target_json_pointer"], item["coverage"]))


def build_documents() -> list[dict[str, Any]]:
    lineage_coordinates = datasets_for_profile("LINEAGE")
    selected = {(item.registry_id, item.dataset_id) for item in lineage_coordinates}
    table_entries = [
        source_table(item.registry_id, item.dataset_id, index)
        for index, item in enumerate(lineage_coordinates)
    ]
    all_bindings = [
        dataset_binding(item.dataset_id, index, item.registry_id)
        for index, item in enumerate(lineage_coordinates)
    ]
    semantic_tables = [dictionary_table(entry) for entry in table_entries]
    semantic_columns = [
        item.model_dump(mode="json")
        for item in COLUMN_ROLE_REGISTRY
        if (
            item.source_coordinate.registry_id,
            item.source_coordinate.dataset_id,
        )
        in selected
    ]
    relationship_rows = [
        item.model_dump(mode="json") for item in relationship_plan("LINEAGE")
    ]
    measure_rows = [item.model_dump(mode="json") for item in MEASURE_REGISTRY]
    field_role_rows = [_field_role_projection(item) for item in semantic_columns]
    trace_relationships = [
        item
        for item in relationship_rows
        if item["relationship_id"] in {"P-RL11", "P-RL12"}
    ]
    validation = _load_json("validation-registry-v1.json")
    selector_coordinates: list[tuple[str, str]] = []
    for selector in validation["selectors"]:
        registry, dataset = selector["source_coordinate"].split("/")
        pair = (registry.split("@")[0], dataset.split("@")[0])
        if pair not in selector_coordinates:
            selector_coordinates.append(pair)
    model_paths = [
        "source-model/model-manifest.json",
        "source-model/semantic-model.json",
        "source-model/relationships.json",
        "source-model/checksums.json",
        "source-model/model.digest",
        "source-model/noncanonical-cache.json",
    ]
    cache_binding = {
        "cache_contract_version": "duckdb-cache-manifest@v1",
        "model_ref": SOURCE_MODEL_REF,
        "source_package_digest": DIGESTS[1],
        "profile_coordinate": {"profile_id": "LINEAGE", "profile_version": 1},
        "database_path": "source-model/warehouse/finance-assurance.duckdb",
        "database_sha256": DIGESTS[2],
        "database_byte_count": 1,
        "engine": "DUCKDB",
        "engine_version": "1.5.5",
        "storage_compatibility_version": "v1.5.0",
        "database_storage_version": "v1.5.0+",
        "build_source_format": "PARQUET",
        "schema_names": ["p_evidence_v1", "q_analytics_v1", "model_meta"],
        "metadata_table_names": ["cache_profile", "documents", "table_bindings"],
        "table_count": len(table_entries),
        "table_bindings_digest": DIGESTS[3],
        "read_only_consumer_required": True,
    }
    source_payloads = _source_documents_payloads(
        table_entries,
        semantic_tables,
        semantic_columns,
        relationship_rows,
        measure_rows,
        cache_binding,
        model_paths,
    )
    payloads: list[tuple[str, str, list[str], list[dict[str, Any]], dict[str, Any]]] = [
        (
            "S-MV10-01",
            "metadata/source-model.json",
            model_paths,
            all_bindings,
            {
                "profile_coordinate": {"profile_id": "LINEAGE", "profile_version": 1},
                "source_formats": ["CSV", "PARQUET", "DUCKDB"],
                "r_paths": [path.removeprefix("source-model/") for path in model_paths],
                "r_cache_binding": cache_binding,
                "table_entries": table_entries,
            },
        ),
        (
            "S-MV10-02",
            "metadata/data-dictionary.json",
            model_paths[:2],
            all_bindings,
            {
                "tables": semantic_tables,
                "columns": [
                    _dictionary_column_projection(column, ordinal)
                    for ordinal, column in enumerate(semantic_columns, start=1)
                ],
            },
        ),
        (
            "S-MV10-03",
            "metadata/relationships.json",
            [model_paths[2]],
            all_bindings,
            {"relationships": relationship_rows},
        ),
        (
            "S-MV10-04",
            "metadata/measures.json",
            [model_paths[1]],
            all_bindings,
            {"measures": measure_rows},
        ),
        (
            "S-MV10-05",
            "metadata/field-roles.json",
            [model_paths[1]],
            all_bindings,
            {"fields": field_role_rows},
        ),
        (
            "S-MV10-06",
            "metadata/lineage.json",
            [model_paths[1], model_paths[2]],
            [dataset_binding("P-D16", 0), dataset_binding("P-D17", 1)],
            {
                "dataset_pointers": [
                    {"source_coordinate": coordinate("P-D16"), "r_table_alias": "r_trace_nodes"},
                    {"source_coordinate": coordinate("P-D17"), "r_table_alias": "r_trace_edges"},
                ],
                "directed_join_steps": [
                    {
                        "step_ordinal": index + 1,
                        "relationship_id": row["relationship_id"],
                        "from_coordinate": coordinate(row["from_dataset"], row["from_registry"]),
                        "from_fields": row["from_columns"],
                        "to_coordinate": coordinate(row["to_dataset"], row["to_registry"]),
                        "to_fields": row["to_columns"],
                        "projected_key_ref": row["projected_key_ref"],
                        "direction": "FORWARD",
                    }
                    for index, row in enumerate(trace_relationships)
                ],
                "evidence_status_fields": [],
            },
        ),
        ("S-MV10-07", "metadata/consumer-suitability.json", [], [], consumers()),
        (
            "S-MV10-08",
            "metadata/validation-checks.json",
            [model_paths[1], model_paths[2]],
            [
                dataset_binding(dataset_id, index, registry_id)
                for index, (registry_id, dataset_id) in enumerate(selector_coordinates)
            ],
            validation,
        ),
    ]
    contracts = {
        "metadata/source-model.json": "handoff-source-binding@v1",
        "metadata/data-dictionary.json": "handoff-data-dictionary@v1",
        "metadata/relationships.json": "handoff-relationships@v1",
        "metadata/measures.json": "handoff-measures@v1",
        "metadata/field-roles.json": "handoff-field-roles@v1",
        "metadata/lineage.json": "handoff-lineage-guide@v1",
        "metadata/consumer-suitability.json": "consumer-suitability@v1",
        "metadata/validation-checks.json": "validation-check-registry@v1",
    }
    vectors = []
    for vector_ref, path, document_paths, bindings, payload in payloads:
        document_bindings = source_documents(document_paths)
        provenance_mapping = _provenance(payload, path, source_payloads)
        handoff_binding = {
            "handoff_ref": HANDOFF_REF,
            "source_model_ref": SOURCE_MODEL_REF,
            "source_model_digest": DIGESTS[0],
            "source_package_digest": DIGESTS[1],
        }
        body = {
            "contract_version": contracts[path],
            "handoff_binding": handoff_binding,
            "source_documents": document_bindings,
            "source_datasets": bindings,
            "field_provenance": provenance_mapping,
            "payload": payload,
        }
        document = MetadataDocument.model_validate_json(
            json.dumps(body, ensure_ascii=True)
        ).model_dump(mode="json")
        construction_inputs = {
            "source_registry_contract_hash": registry_contract_hash(),
            "contract_version": contracts[path],
            "handoff_binding": handoff_binding,
            "source_documents": document_bindings,
            "source_datasets": bindings,
            "source_document_payloads": {
                key: source_payloads[key] for key in document_paths
            },
            "payload_projection": payload,
            "provenance_mapping": provenance_mapping,
        }
        vector = {
            "vector_ref": vector_ref,
            "metadata_path": path,
            "construction_inputs": construction_inputs,
            "document": document,
            "expected_object_digest": canonical_sha256(document),
        }
        vector["expected_vector_digest"] = canonical_sha256(vector)
        vectors.append(vector)
    return vectors


def build_context(vectors: list[dict[str, Any]]) -> dict[str, Any]:
    by_path = {item["metadata_path"]: item["vector_ref"] for item in vectors}
    source_model = next(
        item["document"]["payload"]
        for item in vectors
        if item["metadata_path"] == "metadata/source-model.json"
    )
    manifest_entries = [
        {
            "row_count": item["row_count"],
            "logical_table_digest": item["logical_table_digest"],
        }
        for item in source_model["table_entries"]
    ]
    validation = _load_json("validation-registry-v1.json")
    direct_targets = {
        SOURCE_PACKAGE_AMOUNT_TARGET: {
            "kind": "INTEGER",
            "value": 0,
        },
        "SOURCE_MODEL::schemas/p-evidence-v1/P-D06.schema.json": {
            "kind": "REGULAR_FILE_SHA256",
            "value": DIGESTS[6],
        },
        DUCKDB_AMOUNT_TARGET: {
            "kind": "INTEGER",
            "value": 0,
        },
        XLSX_AMOUNT_TARGET: {
            "kind": "INTEGER_NUMERIC",
            "value": 0,
        },
        XLSX_NULL_TARGET: {
            "kind": "ABSENT_CELL",
            "value": None,
        },
        XLSX_EXTERNAL_LINK_TARGET: {
            "kind": "ABSENT",
            "value": None,
        },
        "SOURCE_HANDOFF::examples/reconciliation-queries.sql::S-QV03": {
            "kind": "AUTHORITY_QUERY",
            "value": "S-QV03",
        },
        "SOURCE_HANDOFF::examples/starter-queries.sql::S-QS01": {
            "kind": "AUTHORITY_QUERY",
            "value": "S-QS01",
        },
        "SOURCE_HANDOFF::unexpected.txt": {"kind": "ABSENT", "value": None},
        "REQUEST::source_model_path": {"kind": "DIRECTORY", "value": "verified-model"},
        "REQUEST::output_path": {"kind": "ABSENT", "value": None},
        "RUNTIME::atomic_rename(staging_path,output_path)": {
            "kind": "CALLABLE",
            "value": "normal",
        },
        "REQUEST::xlsx_writer_profile_ref": {
            "kind": "TEXT",
            "value": "XLSXWRITER-3.2.9@v1",
        },
        "REQUEST::source_package_path": {
            "kind": "DIRECTORY",
            "value": "verified-package",
        },
        STAGING_DUCKDB_AMOUNT_TARGET: {
            "kind": "INTEGER",
            "value": 0,
        },
        "RUNTIME::xlsx_writer_profile/XLSXWRITER-3.2.9@v1": {
            "kind": "AVAILABLE",
            "value": "XlsxWriter-3.2.9",
        },
        "REQUEST::reproduction_output_path": {"kind": "ABSENT", "value": None},
        "RUNTIME::create_staging_directory": {"kind": "CALLABLE", "value": "normal"},
        "RUNTIME::copy_source_model": {"kind": "CALLABLE", "value": "normal"},
        "RUNTIME::derive_metadata_and_sql": {"kind": "CALLABLE", "value": "normal"},
        "RUNTIME::write_xlsx_projection": {"kind": "CALLABLE", "value": "normal"},
        "RUNTIME::seal_staged_handoff": {"kind": "CALLABLE", "value": "normal"},
        "RUNTIME::verify_staged_handoff": {"kind": "CALLABLE", "value": "normal"},
        "RUNTIME::verify_source_handoff": {"kind": "CALLABLE", "value": "normal"},
        "RUNTIME::reproduce_handoff": {"kind": "CALLABLE", "value": "normal"},
        "REQUEST::expected_model_digest": {"kind": "TEXT", "value": DIGESTS[0]},
        "SOURCE_MODEL::model-manifest.json": {
            "kind": "REGULAR_FILE_SHA256",
            "value": DIGESTS[9],
        },
        XLSX_CORE_TARGET: {
            "kind": "ZIP_MEMBER_SHA256",
            "value": DIGESTS[10],
        },
    }
    return {
        "contract_version": CONTEXT_CONTRACT_VERSION,
        "metadata_vector_refs": by_path,
        "json_roots": {
            "SOURCE_MODEL": {
                "model-manifest.json": {"table_entries": manifest_entries},
                "noncanonical-cache.json": {
                    "profile_coordinate": {"profile_id": "LINEAGE", "profile_version": 1}
                },
            },
            "SOURCE_HANDOFF": {
                "handoff-manifest.json": {},
                **{path: {"metadata_vector_ref": ref} for path, ref in by_path.items()},
            },
            "STAGING": {"limitations.json": _load_json("limitations-v1.json")},
        },
        "direct_targets": direct_targets,
        "recipe_target_overrides": {
            "RESEALED_UNSAFE_INTEGER_NUMERIC": {
                XLSX_AMOUNT_TARGET: {
                    "kind": "INTEGER_TEXT",
                    "value": 9007199254740992,
                }
            }
        },
        "reseal_contracts": {
            "RESEAL_R_CACHE_AND_S_NONCANONICAL_MANIFEST": ["SOURCE_MODEL_MANIFEST", "R_CACHE", "S_CANONICAL"],
            "RESEAL_S_CANONICAL": ["S_CANONICAL"],
            "RESEAL_S_XLSX_BINARY_MANIFEST_AND_HANDOFF": ["XLSX_BINARY", "S_CANONICAL"],
            "RESEAL_R_MODEL": ["SOURCE_MODEL_MANIFEST"],
            "RESEAL_R_CACHE_ONLY": ["R_CACHE"],
            "RESEAL_STAGED_CANONICAL_TO_DIFFERENT_DIGEST": ["STAGED_CANONICAL"],
        },
        "request_mutations": {
            "USE_RESEALED_MUTANT_HANDOFF_DIGEST": {
                "target_ref": "REQUEST::expected_handoff_digest",
                "operator": "SET_REQUEST_FIELD",
                "mutation": "TEXT:sha256:mutant-handoff-digest",
            },
            "SET_UNSUPPORTED_WRITER_COORDINATE": {
                "target_ref": "REQUEST::xlsx_writer_profile_ref",
                "operator": "SET_REQUEST_FIELD",
                "mutation": "TEXT:XLSXWRITER-UNSUPPORTED@v99",
            },
        },
        "derived_values": {
            "SOURCE_MODEL_SCHEMA_P-D06_SHA256": DIGESTS[6],
            "SOURCE_MODEL_P-D06_ROW_COUNT": 4,
            "SOURCE_MODEL_P-D06_LOGICAL_TABLE_DIGEST": DIGESTS[8],
            "SOURCE_MODEL_MANIFEST_SHA256": DIGESTS[9],
            "XLSX_MEMBER_docProps/core.xml_SHA256": DIGESTS[10],
        },
        "validation_payload_digest": canonical_sha256(validation),
    }


def main() -> None:
    vectors = build_documents()
    write_json(
        "metadata-positive-logical-vectors-v3.json",
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
    write_json("mutation-positive-context-v2.json", build_context(vectors))


if __name__ == "__main__":
    main()
