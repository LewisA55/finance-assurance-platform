"""Deterministically generate the bounded Artifact S v0.9 logical authorities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from finance_assurance.analytics.registry import DATASET_BY_ID as Q_DATASET_BY_ID
from finance_assurance.digestion.registry import (
    COLUMN_ROLE_REGISTRY,
    PRIMARY_CONSUMPTION_CLASS,
    RELATIONSHIP_KEY_PROJECTIONS,
    datasets_for_profile,
    portable_alias,
    registry_contract_hash,
)
from finance_assurance.exports.registry import DATASET_BY_ID as P_DATASET_BY_ID
from finance_assurance.handoff.metadata import MetadataDocument
from finance_assurance.runtime.canonical import canonical_sha256

ROOT = Path(__file__).parents[2]
AUTHORITY = ROOT / "tests" / "fixtures" / "local-analytical-handoff"
DIGESTS = tuple("sha256:" + character * 64 for character in "123456789abcdef")
DUCKDB_AMOUNT_TARGET = (
    "SOURCE_HANDOFF::source-model/warehouse/finance-assurance.duckdb::"
    "P-D06::SEL-C1-V1-REVENUE::amount_minor"
)
XLSX_AMOUNT_TARGET = (
    "SOURCE_HANDOFF::excel/finance-assurance-data-pack.xlsx::"
    "SEL-C1-V1-REVENUE::amount_minor"
)
XLSX_NULL_TARGET = (
    "SOURCE_HANDOFF::excel/finance-assurance-data-pack.xlsx::"
    "NULL_VECTOR::nullable_text"
)
XLSX_EXTERNAL_LINK_TARGET = (
    "SOURCE_HANDOFF::excel/finance-assurance-data-pack.xlsx::"
    "xl/externalLinks/externalLink1.xml"
)
STAGING_DUCKDB_AMOUNT_TARGET = (
    "STAGING::source-model/warehouse/finance-assurance.duckdb::"
    "P-D06::SEL-C1-V1-REVENUE::amount_minor"
)
XLSX_CORE_TARGET = (
    "SOURCE_HANDOFF::excel/finance-assurance-data-pack.xlsx::docProps/core.xml"
)


def coordinate(dataset_id: str, registry_id: str = "P-EVIDENCE") -> dict[str, Any]:
    return {
        "registry_id": registry_id,
        "registry_version": 1,
        "dataset_id": dataset_id,
        "dataset_version": 1,
    }


def _definition(registry_id: str, dataset_id: str) -> Any:
    if registry_id == "P-EVIDENCE":
        return P_DATASET_BY_ID[dataset_id]
    return Q_DATASET_BY_ID[dataset_id]


def _projection_names(registry_id: str, dataset_id: str) -> list[str]:
    identity = (registry_id, dataset_id)
    return [
        item.technical_column_name
        for item in RELATIONSHIP_KEY_PROJECTIONS
        if identity
        in {
            (item.from_coordinate.registry_id, item.from_coordinate.dataset_id),
            (item.to_coordinate.registry_id, item.to_coordinate.dataset_id),
        }
    ]


def _column_names(registry_id: str, dataset_id: str) -> list[str]:
    definition = _definition(registry_id, dataset_id)
    return [item.name for item in definition.columns] + _projection_names(
        registry_id, dataset_id
    )


def dataset_binding(
    dataset_id: str, index: int, registry_id: str = "P-EVIDENCE"
) -> dict[str, Any]:
    storage = "p-evidence-v1" if registry_id == "P-EVIDENCE" else "q-analytics-v1"
    return {
        "source_coordinate": coordinate(dataset_id, registry_id),
        "parquet_path": f"source-model/parquet/{storage}/{dataset_id}.parquet",
        "parquet_sha256": DIGESTS[(index + 6) % len(DIGESTS)],
        "logical_table_digest": DIGESTS[(index + 3) % len(DIGESTS)],
        "technical_projection_digest": DIGESTS[(index + 4) % len(DIGESTS)],
        "column_names": _column_names(registry_id, dataset_id),
    }


def source_table(registry_id: str, dataset_id: str, index: int) -> dict[str, Any]:
    definition = _definition(registry_id, dataset_id)
    storage = "p-evidence-v1" if registry_id == "P-EVIDENCE" else "q-analytics-v1"
    projection_refs = [
        item.relationship_id
        for item in RELATIONSHIP_KEY_PROJECTIONS
        if (registry_id, dataset_id)
        in {
            (item.from_coordinate.registry_id, item.from_coordinate.dataset_id),
            (item.to_coordinate.registry_id, item.to_coordinate.dataset_id),
        }
    ]
    return {
        "source_registry_id": registry_id,
        "source_registry_version": 1,
        "source_dataset_id": dataset_id,
        "source_dataset_version": 1,
        "source_dataset_name": definition.name,
        "primary_consumption_class": PRIMARY_CONSUMPTION_CLASS[dataset_id],
        "included_by_profile": "LINEAGE",
        "semantic_owners": list(definition.semantic_owners),
        "source_schema_path": f"schemas/{storage}/{dataset_id}.schema.json",
        "source_schema_hash": DIGESTS[(index + 1) % len(DIGESTS)],
        "source_data_hash": DIGESTS[(index + 2) % len(DIGESTS)],
        "row_count": 4 if dataset_id == "P-D06" else 1,
        "primary_key": ["row_key"],
        "unique_keys": [list(item) for item in definition.unique_keys],
        "default_sort": ["row_key"],
        "logical_table_digest": DIGESTS[(index + 3) % len(DIGESTS)],
        "technical_projection_digest": DIGESTS[(index + 4) % len(DIGESTS)],
        "relationship_key_projections": projection_refs,
        "csv_path": f"csv/{storage}/{dataset_id}.csv",
        "csv_hash": DIGESTS[(index + 5) % len(DIGESTS)],
        "parquet_path": f"parquet/{storage}/{dataset_id}.parquet",
        "parquet_hash": DIGESTS[(index + 6) % len(DIGESTS)],
        "physical_schema_fingerprint": DIGESTS[(index + 7) % len(DIGESTS)],
        "duckdb_schema": storage.replace("-", "_"),
        "duckdb_object": portable_alias(registry_id, dataset_id, definition.name),
    }


def dictionary_table(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_coordinate": coordinate(
            entry["source_dataset_id"], entry["source_registry_id"]
        ),
        "physical_alias": entry["duckdb_object"],
        "display_label": entry["source_dataset_name"].replace("_", " ").title(),
        "primary_consumption_class": entry["primary_consumption_class"],
        "included_by_profile": "LINEAGE",
        "semantic_owners": entry["semantic_owners"],
        "default_sort": ["row_key"],
        "column_names": _column_names(
            entry["source_registry_id"], entry["source_dataset_id"]
        ),
        "primary_key": ["row_key"],
        "unique_keys": entry["unique_keys"],
    }


def _xlsx_storage_mode(source_type: str) -> str:
    return {
        "boolean": "BOOLEAN_NATIVE",
        "date": "TEXT_DATE_ISO",
        "integer": "NUMBER_EXACT",
        "timestamp": "TEXT_TIMESTAMP_UTC",
    }.get(source_type, "TEXT_EXACT")


def dictionary_columns(registry_id: str, dataset_id: str) -> list[dict[str, Any]]:
    semantics = [
        item
        for item in COLUMN_ROLE_REGISTRY
        if item.source_coordinate.registry_id == registry_id
        and item.source_coordinate.dataset_id == dataset_id
    ]
    return [
        {
            **item.model_dump(mode="json"),
            "ordinal": ordinal,
            "xlsx_storage_mode": _xlsx_storage_mode(item.source_type),
        }
        for ordinal, item in enumerate(semantics, start=1)
    ]


def relationship(relationship_id: str, terminal_from: str) -> dict[str, Any]:
    return {
        "relationship_id": relationship_id,
        "relationship_type": "STANDARD",
        "enforcement": "INTEGRITY_ONLY",
        "from_registry": "P-EVIDENCE",
        "from_dataset": "P-D17",
        "from_columns": [
            "scenario_ref",
            "reporting_version_ref",
            "statement_field",
            terminal_from,
        ],
        "to_registry": "P-EVIDENCE",
        "to_dataset": "P-D16",
        "to_columns": [
            "scenario_ref",
            "reporting_version_ref",
            "statement_field",
            "node_ref",
        ],
        "allowed_target_coordinates": [],
        "load_disposition": "VALIDATION_ONLY",
        "relationship_role": "VALIDATION_ONLY",
        "projected_key_ref": None,
        "cross_filter_direction": "NONE",
        "consumer_reason": "UPSTREAM_INTEGRITY_OR_POLYMORPHIC_VALIDATION",
    }


def source_documents(paths: list[str]) -> list[dict[str, Any]]:
    versions = {
        "source-model/model-manifest.json": "consumer-model@v1",
        "source-model/semantic-model.json": "semantic-catalogue@v1",
        "source-model/relationships.json": "relationship-catalogue@v1",
        "source-model/checksums.json": "checksum-ledger@v1",
        "source-model/model.digest": "detached-model-digest@v1",
        "source-model/noncanonical-cache.json": "duckdb-cache-manifest@v1",
    }
    return [
        {"path": path, "contract_version": versions[path], "sha256": DIGESTS[index]}
        for index, path in enumerate(paths)
    ]


def escaped(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def covered_paths(value: Any, path: str = "/payload") -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if isinstance(value, list):
        result.append((path, "ARRAY_ORDER"))
        for index, item in enumerate(value):
            result.extend(covered_paths(item, f"{path}/{index}"))
    elif isinstance(value, dict):
        for key, item in value.items():
            result.extend(covered_paths(item, f"{path}/{escaped(key)}"))
    else:
        result.append((path, "VALUE"))
    return result


def _validation_dataset_pointer(payload: dict[str, Any], target: str) -> dict[str, Any]:
    selector_by_id = {item["selector_id"]: item for item in payload["selectors"]}
    segments = target.removeprefix("/payload/").split("/")
    selector: dict[str, Any] | None = None
    assertion: dict[str, Any] | None = None
    if segments[0] == "selectors" and len(segments) > 1:
        selector = payload["selectors"][int(segments[1])]
    elif segments[0] == "checks" and len(segments) > 1:
        check = payload["checks"][int(segments[1])]
        if "assertions" in segments and segments.index("assertions") + 1 < len(segments):
            assertion_index = int(segments[segments.index("assertions") + 1])
            assertion = check["assertions"][assertion_index]
        candidates: list[str] = []

        def collect(value: Any) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    if key.endswith("selector_ref") and isinstance(item, str):
                        candidates.append(item)
                    else:
                        collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)

        collect(assertion if assertion is not None else check)
        if candidates:
            selector = selector_by_id[candidates[0]]
    if selector is None:
        selector = payload["selectors"][0]
    registry, dataset = selector["source_coordinate"].split("/")
    field_name = "row_key"
    if assertion is not None:
        field_name = assertion.get("source_field") or field_name
        if field_name == "row_key":
            for key in ("field_names", "edge_fields"):
                values = assertion.get(key)
                if values:
                    field_name = values[0]
                    break
    return {
        "pointer_kind": "DATASET_CELL",
        "source_coordinate": coordinate(dataset.split("@")[0], registry.split("@")[0]),
        "selector_ref": selector["selector_id"],
        "field_name": field_name,
    }


def _json_source_pointer(path: str, target: str) -> dict[str, Any]:
    relative = target.removeprefix("/payload") or "/"
    document = "source-model/semantic-model.json"
    pointer = relative
    if path == "metadata/source-model.json":
        if relative.startswith("/r_cache_binding"):
            document = "source-model/noncanonical-cache.json"
            pointer = relative.removeprefix("/r_cache_binding") or "/"
        else:
            document = "source-model/model-manifest.json"
            pointer = relative
            pointer = pointer.replace("/source_formats", "/requested_formats", 1)
            pointer = pointer.replace("/table_entries", "/table_entries", 1)
            pointer = pointer.replace("/profile_coordinate/profile_id", "/profile_id", 1)
            pointer = pointer.replace(
                "/profile_coordinate/profile_version", "/profile_version", 1
            )
    elif path == "metadata/data-dictionary.json":
        parts = relative.strip("/").split("/")
        if parts[0] == "tables" and len(parts) >= 3:
            index, field = parts[1], parts[2]
            if field in {"primary_key", "unique_keys"}:
                document = "source-model/model-manifest.json"
                pointer = f"/table_entries/{index}/" + "/".join(parts[2:])
            else:
                pointer = "/" + "/".join(parts)
        elif parts[0] == "columns" and len(parts) >= 3:
            if parts[2] == "ordinal":
                pointer = f"/columns/{parts[1]}"
            else:
                pointer = f"/columns/{parts[1]}/" + "/".join(parts[2:])
    elif path == "metadata/relationships.json":
        document = "source-model/relationships.json"
        pointer = relative.removeprefix("/relationships") or "/0"
    elif path == "metadata/measures.json":
        pointer = relative
    elif path == "metadata/field-roles.json":
        pointer = relative.replace("/fields/0", "/columns/6", 1)
    elif path == "metadata/lineage.json":
        parts = relative.strip("/").split("/")
        if parts[0] == "directed_join_steps" and len(parts) >= 3:
            document = "source-model/relationships.json"
            mapping = {
                "relationship_id": "relationship_id",
                "from_fields": "from_columns",
                "to_fields": "to_columns",
                "projected_key_ref": "projected_key_ref",
            }
            if parts[2] in {
                "step_ordinal",
                "from_coordinate",
                "to_coordinate",
                "direction",
            }:
                pointer = f"/{parts[1]}"
            else:
                pointer = f"/{parts[1]}/{mapping.get(parts[2], parts[2])}"
            if len(parts) > 3 and parts[2] not in {
                "from_coordinate",
                "to_coordinate",
            }:
                pointer += "/" + "/".join(parts[3:])
        elif parts[0] == "dataset_pointers" and len(parts) >= 3:
            table_index = 15 + int(parts[1])
            field = "physical_alias" if parts[2] == "r_table_alias" else parts[2]
            pointer = f"/tables/{table_index}/{field}"
            if len(parts) > 3:
                pointer += "/" + "/".join(parts[3:])
        else:
            pointer = "/columns"
    return {
        "pointer_kind": "JSON_POINTER",
        "source_document_path": document,
        "json_pointer": pointer,
    }


def provenance(payload: dict[str, Any], path: str, source_paths: list[str]) -> list[dict[str, Any]]:
    guidance_document = path == "metadata/consumer-suitability.json"
    guidance_fragments = {
        "metadata/source-model.json": ("/payload/r_paths",),
        "metadata/data-dictionary.json": ("/xlsx_storage_mode",),
        "metadata/field-roles.json": ("/format_hints",),
    }
    algorithm = {
        "metadata/source-model.json": "R-MANIFEST-BINDING@v1",
        "metadata/data-dictionary.json": "R-TABLE-COLUMN-PROJECTION@v1",
        "metadata/relationships.json": "R-RELATIONSHIP-PROJECTION@v1",
        "metadata/measures.json": "R-MEASURE-PROJECTION@v1",
        "metadata/field-roles.json": "R-FIELD-ROLE-PROJECTION@v1",
        "metadata/lineage.json": "R-LINEAGE-POINTERS@v1",
        "metadata/consumer-suitability.json": "S-CONSUMER-SUITABILITY@v1",
        "metadata/validation-checks.json": "S-VALIDATION-REGISTRY@v1",
    }[path]
    result = []
    for target, coverage in covered_paths(payload):
        is_guidance = guidance_document or any(
            fragment in target for fragment in guidance_fragments.get(path, ())
        )
        pointers = []
        if not is_guidance:
            if path == "metadata/validation-checks.json":
                pointers = [_validation_dataset_pointer(payload, target)]
            else:
                pointers = [_json_source_pointer(path, target)]
        result.append(
            {
                "target_json_pointer": target,
                "coverage": coverage,
                "derivation_class": "S_GUIDANCE" if is_guidance else "R_PROJECTION",
                "source_pointers": pointers,
                "algorithm_ref": algorithm,
            }
        )
    return sorted(result, key=lambda item: (item["target_json_pointer"], item["coverage"]))


def consumers() -> dict[str, Any]:
    expansions = [
        "BALANCE_SHEET_DRIVERS",
        "CASH_FLOW_DRIVERS",
        "ENTITY_AND_PERIOD_EXPANSION",
        "FORECAST_ASSUMPTIONS",
        "MARKET_VALUATION_INPUTS",
        "OPENING_BALANCES",
        "PRODUCTION_CONTROL_EVIDENCE",
        "STATISTICAL_SAMPLE_DESIGN",
    ]
    conditional = ["CONTROLLED_KPI_USE"]
    rows = [
        ("REACT", ["LINEAGE_PROTOTYPE", "LOCAL_DUCKDB_READ_ONLY", "PARQUET_QUERY"], ["DCF_MODEL", "ENTERPRISE_FORECAST", "HANDOFF_AS_FINISHED_DASHBOARD", "PRODUCTION_BENCHMARK", "STATISTICAL_CLAIM", "THREE_STATEMENT_MODEL"], ["examples/starter-queries.sql", "metadata/data-dictionary.json", "metadata/relationships.json", "source-model/model-manifest.json", "source-model/noncanonical-cache.json", "source-model/warehouse/finance-assurance.duckdb"]),
        ("EXCEL", ["CONTROL_TOTAL_RECONCILIATION", "SOURCE_TABLE_IMPORT", "XLSX_DATA_PACK_INSPECTION"], ["DCF_MODEL", "ENTERPRISE_FORECAST", "HANDOFF_AS_FINISHED_FINANCIAL_MODEL", "PRODUCTION_BENCHMARK", "STATISTICAL_CLAIM", "THREE_STATEMENT_MODEL"], ["excel/finance-assurance-data-pack.xlsx", "excel/noncanonical-workbook.json", "limitations.json", "metadata/data-dictionary.json", "metadata/measures.json", "metadata/relationships.json", "metadata/validation-checks.json"]),
        ("POWER_BI", ["MEASURE_SPECIFICATION_USE", "PARQUET_IMPORT", "RELATIONSHIP_CATALOGUE_USE"], ["DCF_MODEL", "ENTERPRISE_FORECAST", "HANDOFF_AS_FINISHED_SEMANTIC_MODEL", "PRODUCTION_BENCHMARK", "STATISTICAL_CLAIM", "THREE_STATEMENT_MODEL"], ["limitations.json", "metadata/data-dictionary.json", "metadata/field-roles.json", "metadata/measures.json", "metadata/relationships.json", "source-model/model-manifest.json"]),
        ("SQL", ["READ_ONLY_EXPLORATION", "RECONCILIATION_QUERY_EXECUTION", "STARTER_QUERY_EXECUTION"], ["DCF_MODEL", "ENTERPRISE_FORECAST", "PRODUCTION_BENCHMARK", "STATISTICAL_CLAIM", "THREE_STATEMENT_MODEL", "WRITEBACK"], ["examples/reconciliation-queries.sql", "examples/starter-queries.sql", "source-model/model-manifest.json", "source-model/noncanonical-cache.json", "source-model/warehouse/finance-assurance.duckdb"]),
    ]
    return {
        "consumers": [
            {
                "consumer_id": consumer_id,
                "supported_use_ids": supported,
                "conditional_use_ids": conditional,
                "unsupported_use_ids": unsupported,
                "required_upstream_expansion_ids": expansions,
                "required_source_paths": paths,
            }
            for consumer_id, supported, unsupported, paths in rows
        ],
        "synthetic_depth_notice": "C-001 and CT-1 are synthetic, bounded scenario proofs. They support local lineage, restatement, correction, and controlled-use demonstrations; they do not support DCF, three-statement, enterprise forecasting, statistical, benchmark, or production claims.",
    }


def build_documents() -> list[dict[str, Any]]:
    lineage_coordinates = datasets_for_profile("LINEAGE")
    table_entries = [
        source_table(item.registry_id, item.dataset_id, index)
        for index, item in enumerate(lineage_coordinates)
    ]
    all_bindings = [
        dataset_binding(item.dataset_id, index, item.registry_id)
        for index, item in enumerate(lineage_coordinates)
    ]
    relation_rows = [relationship("P-RL11", "source_ref"), relationship("P-RL12", "target_ref")]
    validation = json.loads((AUTHORITY / "validation-registry-v1.json").read_text(encoding="ascii"))
    selector_coordinates = []
    for selector in validation["selectors"]:
        registry, dataset = selector["source_coordinate"].split("/")[0], selector["source_coordinate"].split("/")[1]
        registry_id = registry.split("@")[0]
        dataset_id = dataset.split("@")[0]
        pair = (registry_id, dataset_id)
        if pair not in selector_coordinates:
            selector_coordinates.append(pair)
    selector_bindings = [dataset_binding(dataset_id, index, registry_id) for index, (registry_id, dataset_id) in enumerate(selector_coordinates)]
    model_paths = [
        "source-model/model-manifest.json",
        "source-model/semantic-model.json",
        "source-model/relationships.json",
        "source-model/checksums.json",
        "source-model/model.digest",
        "source-model/noncanonical-cache.json",
    ]
    payloads: list[tuple[str, str, list[str], list[dict[str, Any]], dict[str, Any]]] = [
        (
            "S-MV09-01",
            "metadata/source-model.json",
            model_paths,
            all_bindings,
            {
                "profile_coordinate": {"profile_id": "LINEAGE", "profile_version": 1},
                "source_formats": ["CSV", "PARQUET", "DUCKDB"],
                "r_paths": [path.removeprefix("source-model/") for path in model_paths],
                "r_cache_binding": {
                    "cache_contract_version": "duckdb-cache-manifest@v1",
                    "model_ref": "R-V09-POSITIVE",
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
                },
                "table_entries": table_entries,
            },
        ),
        (
            "S-MV09-02",
            "metadata/data-dictionary.json",
            model_paths[:2],
            all_bindings,
            {
                "tables": [dictionary_table(entry) for entry in table_entries],
                "columns": [
                    column
                    for entry in table_entries
                    for column in dictionary_columns(
                        entry["source_registry_id"], entry["source_dataset_id"]
                    )
                ],
            },
        ),
        ("S-MV09-03", "metadata/relationships.json", [model_paths[2]], [dataset_binding("P-D16", 0), dataset_binding("P-D17", 1)], {"relationships": relation_rows}),
        (
            "S-MV09-04",
            "metadata/measures.json",
            [model_paths[1]],
            [
                next(
                    item
                    for item in all_bindings
                    if item["source_coordinate"]["dataset_id"] == "P-D06"
                )
            ],
            {"measures": [{"measure_id": "R-M01", "measure_name": "June v2 revenue", "source_registry_id": "P-EVIDENCE", "source_dataset_id": "P-D06", "source_field": "amount_minor", "classification": "EXACT_VALUE", "aggregation": "SELECT_EXACT", "required_grain": ["scenario_ref", "reporting_version_ref", "statement_field"], "required_grouping": [], "currency_policy": "SINGLE_EXACT_CURRENCY", "reporting_version_policy": "EXACT_REPORTING_VERSION", "population_class": "REPORTING_VALUE", "multirow_behavior": "BLANK_OR_ERROR", "non_combinable_with": [], "default_format": "GBP_MINOR"}]},
        ),
        (
            "S-MV09-05",
            "metadata/field-roles.json",
            [model_paths[1]],
            all_bindings,
            {"fields": [{"source_coordinate": coordinate("P-D06"), "source_name": "amount_minor", "source_type": "integer", "physical_type": "INT64", "column_role": "DOMAIN_MEASURE_INPUT", "default_visibility": "VISIBLE", "default_summarization": "NONE", "display_label": "Amount Minor", "display_folder": "Reporting", "format_hints": ["MONEY_INTEGER_MINOR_UNITS", "RAW_INTEGER_SUMMARIZATION_NONE"]}]},
        ),
        (
            "S-MV09-06",
            "metadata/lineage.json",
            [model_paths[1], model_paths[2]],
            [dataset_binding("P-D16", 0), dataset_binding("P-D17", 1)],
            {
                "dataset_pointers": [{"source_coordinate": coordinate("P-D16"), "r_table_alias": "r_trace_nodes"}, {"source_coordinate": coordinate("P-D17"), "r_table_alias": "r_trace_edges"}],
                "directed_join_steps": [
                    {"step_ordinal": index + 1, "relationship_id": row["relationship_id"], "from_coordinate": coordinate("P-D17"), "from_fields": row["from_columns"], "to_coordinate": coordinate("P-D16"), "to_fields": row["to_columns"], "projected_key_ref": None, "direction": "FORWARD"}
                    for index, row in enumerate(relation_rows)
                ],
                "evidence_status_fields": [],
            },
        ),
        ("S-MV09-07", "metadata/consumer-suitability.json", [], [], consumers()),
        ("S-MV09-08", "metadata/validation-checks.json", [model_paths[1], model_paths[2]], selector_bindings, validation),
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
        provenance_mapping = provenance(payload, path, document_paths)
        handoff_binding = {
            "handoff_ref": "S-V09-POSITIVE",
            "source_model_ref": "R-V09-POSITIVE",
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
    validation = json.loads((AUTHORITY / "validation-registry-v1.json").read_text(encoding="ascii"))
    return {
        "contract_version": "handoff-mutation-positive-context@v1",
        "metadata_vector_refs": by_path,
        "json_roots": {
            "SOURCE_MODEL": {
                "model-manifest.json": {"table_entries": manifest_entries},
                "noncanonical-cache.json": {"profile_coordinate": {"profile_id": "LINEAGE", "profile_version": 1}},
            },
            "SOURCE_HANDOFF": {"handoff-manifest.json": {}, **{path: {"metadata_vector_ref": ref} for path, ref in by_path.items()}},
            "STAGING": {"limitations.json": json.loads((AUTHORITY / "limitations-v1.json").read_text(encoding="ascii"))},
        },
        "direct_targets": {
            "SOURCE_PACKAGE::P-EVIDENCE@v1/P-D06@v1::SEL-C1-V1-REVENUE::amount_minor": {"kind": "INTEGER", "value": 0},
            "SOURCE_MODEL::schemas/p-evidence-v1/P-D06.schema.json": {"kind": "REGULAR_FILE_SHA256", "value": DIGESTS[6]},
            DUCKDB_AMOUNT_TARGET: {"kind": "INTEGER", "value": 0},
            XLSX_AMOUNT_TARGET: {"kind": "INTEGER_NUMERIC", "value": 0},
            XLSX_NULL_TARGET: {"kind": "ABSENT_CELL", "value": None},
            XLSX_EXTERNAL_LINK_TARGET: {"kind": "ABSENT", "value": None},
            "SOURCE_HANDOFF::examples/reconciliation-queries.sql::S-QV03": {"kind": "AUTHORITY_QUERY", "value": "S-QV03"},
            "SOURCE_HANDOFF::examples/starter-queries.sql::S-QS01": {"kind": "AUTHORITY_QUERY", "value": "S-QS01"},
            "SOURCE_HANDOFF::unexpected.txt": {"kind": "ABSENT", "value": None},
            "REQUEST::source_model_path": {"kind": "DIRECTORY", "value": "verified-model"},
            "REQUEST::output_path": {"kind": "ABSENT", "value": None},
            "RUNTIME::atomic_rename(staging_path,output_path)": {"kind": "CALLABLE", "value": "normal"},
            "REQUEST::xlsx_writer_profile_ref": {"kind": "TEXT", "value": "XLSXWRITER-3.2.9@v1"},
            "REQUEST::source_package_path": {"kind": "DIRECTORY", "value": "verified-package"},
            STAGING_DUCKDB_AMOUNT_TARGET: {"kind": "INTEGER", "value": 0},
            "RUNTIME::xlsx_writer_profile/XLSXWRITER-3.2.9@v1": {"kind": "AVAILABLE", "value": "XlsxWriter-3.2.9"},
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
            "SOURCE_MODEL::model-manifest.json": {"kind": "REGULAR_FILE_SHA256", "value": DIGESTS[9]},
            XLSX_CORE_TARGET: {"kind": "ZIP_MEMBER_SHA256", "value": DIGESTS[10]},
        },
        "recipe_target_overrides": {
            "RESEALED_UNSAFE_INTEGER_NUMERIC": {
                XLSX_AMOUNT_TARGET: {
                    "kind": "INTEGER_TEXT",
                    "value": 9007199254740992,
                }
            }
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


def write_json(name: str, value: dict[str, Any]) -> None:
    (AUTHORITY / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="ascii", newline="\n")


def main() -> None:
    vectors = build_documents()
    write_json(
        "metadata-positive-logical-vectors-v2.json",
        {
            "contract_version": "handoff-metadata-positive-logical-vectors@v2",
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
    write_json("mutation-positive-context-v1.json", build_context(vectors))


if __name__ == "__main__":
    main()
