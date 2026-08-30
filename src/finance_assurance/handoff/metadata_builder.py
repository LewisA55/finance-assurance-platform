"""Derive Artifact S metadata from one verified Artifact R model."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from finance_assurance.digestion.contracts import (
    ModelManifest,
    NoncanonicalCacheManifest,
    SemanticCatalogue,
)
from finance_assurance.exports.serialization import sha256_bytes
from finance_assurance.handoff.authorities import load_json_authority
from finance_assurance.handoff.metadata import MetadataDocument
from finance_assurance.runtime.canonical import canonical_sha256

SOURCE_DOCUMENT_VERSIONS = {
    "source-model/model-manifest.json": "consumer-model@v1",
    "source-model/semantic-model.json": "semantic-catalogue@v1",
    "source-model/relationships.json": "relationship-catalogue@v1",
    "source-model/checksums.json": "checksum-ledger@v1",
    "source-model/model.digest": "detached-model-digest@v1",
    "source-model/noncanonical-cache.json": "duckdb-cache-manifest@v1",
}

METADATA_CONTRACTS = {
    "metadata/source-model.json": "handoff-source-binding@v1",
    "metadata/data-dictionary.json": "handoff-data-dictionary@v1",
    "metadata/relationships.json": "handoff-relationships@v1",
    "metadata/measures.json": "handoff-measures@v1",
    "metadata/field-roles.json": "handoff-field-roles@v1",
    "metadata/lineage.json": "handoff-lineage-guide@v1",
    "metadata/consumer-suitability.json": "consumer-suitability@v1",
    "metadata/validation-checks.json": "validation-check-registry@v1",
}

_MODEL_PATHS = tuple(SOURCE_DOCUMENT_VERSIONS)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _covered_paths(value: Any, path: str = "/payload") -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if isinstance(value, list):
        result.append((path, "ARRAY_ORDER"))
        for index, item in enumerate(value):
            result.extend(_covered_paths(item, f"{path}/{index}"))
    elif isinstance(value, dict):
        for key, item in value.items():
            result.extend(_covered_paths(item, f"{path}/{_escape(key)}"))
    else:
        result.append((path, "VALUE"))
    return result


def _coordinate(registry_id: str, dataset_id: str) -> dict[str, object]:
    return {
        "registry_id": registry_id,
        "registry_version": 1,
        "dataset_id": dataset_id,
        "dataset_version": 1,
    }


def _dataset_bindings(
    manifest: ModelManifest,
    semantic: SemanticCatalogue,
) -> dict[tuple[str, str], dict[str, object]]:
    tables = {
        (item.source_coordinate.registry_id, item.source_coordinate.dataset_id): item
        for item in semantic.tables
    }
    result: dict[tuple[str, str], dict[str, object]] = {}
    for entry in manifest.table_entries:
        identity = (entry.source_registry_id, entry.source_dataset_id)
        table = tables[identity]
        if entry.parquet_path is None or entry.parquet_hash is None:
            raise ValueError("Artifact S requires an R Parquet binding for every table")
        result[identity] = {
            "source_coordinate": _coordinate(*identity),
            "parquet_path": f"source-model/{entry.parquet_path}",
            "parquet_sha256": entry.parquet_hash,
            "logical_table_digest": entry.logical_table_digest,
            "technical_projection_digest": entry.technical_projection_digest,
            "column_names": list(table.column_names),
        }
    return result


def _source_documents(root: Path, paths: Sequence[str]) -> list[dict[str, object]]:
    return [
        {
            "path": path,
            "contract_version": SOURCE_DOCUMENT_VERSIONS[path],
            "sha256": sha256_bytes((root / path).read_bytes()),
        }
        for path in paths
    ]


def _storage_mode(source_type: str) -> str:
    return {
        "boolean": "BOOLEAN_NATIVE",
        "date": "TEXT_DATE_ISO",
        "integer": "NUMBER_EXACT",
        "timestamp": "TEXT_TIMESTAMP_UTC",
    }.get(source_type, "TEXT_EXACT")


def _format_hints(column: Mapping[str, Any]) -> list[str]:
    result: list[str] = []
    if column["source_type"] == "timestamp":
        result.append("TIMESTAMP_UTC_MICROSECOND")
    if column["source_type"] == "integer":
        if column["column_role"] == "DOMAIN_MEASURE_INPUT":
            result.append("MONEY_INTEGER_MINOR_UNITS")
        result.append("RAW_INTEGER_SUMMARIZATION_NONE")
    return result


def _consumer_suitability() -> dict[str, object]:
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
    definitions = (
        (
            "REACT",
            ["LINEAGE_PROTOTYPE", "LOCAL_DUCKDB_READ_ONLY", "PARQUET_QUERY"],
            ["HANDOFF_AS_FINISHED_DASHBOARD"],
            [
                "examples/starter-queries.sql",
                "metadata/data-dictionary.json",
                "metadata/relationships.json",
                "source-model/model-manifest.json",
                "source-model/noncanonical-cache.json",
                "source-model/warehouse/finance-assurance.duckdb",
            ],
        ),
        (
            "EXCEL",
            ["CONTROL_TOTAL_RECONCILIATION", "SOURCE_TABLE_IMPORT", "XLSX_DATA_PACK_INSPECTION"],
            ["HANDOFF_AS_FINISHED_FINANCIAL_MODEL"],
            [
                "excel/finance-assurance-data-pack.xlsx",
                "excel/noncanonical-workbook.json",
                "limitations.json",
                "metadata/data-dictionary.json",
                "metadata/measures.json",
                "metadata/relationships.json",
                "metadata/validation-checks.json",
            ],
        ),
        (
            "POWER_BI",
            ["MEASURE_SPECIFICATION_USE", "PARQUET_IMPORT", "RELATIONSHIP_CATALOGUE_USE"],
            ["HANDOFF_AS_FINISHED_SEMANTIC_MODEL"],
            [
                "limitations.json",
                "metadata/data-dictionary.json",
                "metadata/field-roles.json",
                "metadata/measures.json",
                "metadata/relationships.json",
                "source-model/model-manifest.json",
            ],
        ),
        (
            "SQL",
            ["READ_ONLY_EXPLORATION", "RECONCILIATION_QUERY_EXECUTION", "STARTER_QUERY_EXECUTION"],
            ["WRITEBACK"],
            [
                "examples/reconciliation-queries.sql",
                "examples/starter-queries.sql",
                "source-model/model-manifest.json",
                "source-model/noncanonical-cache.json",
                "source-model/warehouse/finance-assurance.duckdb",
            ],
        ),
    )
    common_unsupported = [
        "DCF_MODEL",
        "ENTERPRISE_FORECAST",
        "PRODUCTION_BENCHMARK",
        "STATISTICAL_CLAIM",
        "THREE_STATEMENT_MODEL",
    ]
    return {
        "consumers": [
            {
                "consumer_id": consumer,
                "supported_use_ids": supported,
                "conditional_use_ids": conditional,
                "unsupported_use_ids": sorted([*common_unsupported, *specific]),
                "required_upstream_expansion_ids": expansions,
                "required_source_paths": paths,
            }
            for consumer, supported, specific, paths in definitions
        ],
        "synthetic_depth_notice": (
            "C-001 and CT-1 are synthetic, bounded scenario proofs. They support "
            "local lineage, restatement, correction, and controlled-use "
            "demonstrations; they do not support DCF, three-statement, enterprise "
            "forecasting, statistical, benchmark, or production claims."
        ),
    }


def _provenance(
    path: str,
    payload: dict[str, Any],
    source_document_paths: Sequence[str],
) -> list[dict[str, object]]:
    guidance_document = path in {
        "metadata/consumer-suitability.json",
        "metadata/validation-checks.json",
    }
    algorithm = {
        "metadata/source-model.json": "R-MANIFEST-BINDING@v3",
        "metadata/data-dictionary.json": "R-TABLE-COLUMN-PROJECTION@v3",
        "metadata/relationships.json": "R-RELATIONSHIP-PROJECTION@v3",
        "metadata/measures.json": "R-MEASURE-PROJECTION@v3",
        "metadata/field-roles.json": "R-FIELD-ROLE-PROJECTION@v3",
        "metadata/lineage.json": "R-LINEAGE-POINTERS@v3",
        "metadata/consumer-suitability.json": "S-CONSUMER-SUITABILITY@v1",
        "metadata/validation-checks.json": "S-VALIDATION-REGISTRY@v1",
    }[path]
    def pointer_path(target: str) -> str | None:
        if path == "metadata/source-model.json":
            if "/r_cache_binding" in target:
                return "source-model/noncanonical-cache.json"
            return "source-model/model-manifest.json"
        if path == "metadata/data-dictionary.json":
            if "/tables/" in target and (
                "/primary_key" in target or "/unique_keys" in target
            ):
                return "source-model/model-manifest.json"
            return "source-model/semantic-model.json"
        if path == "metadata/lineage.json" and "/directed_join_steps" in target:
            return "source-model/relationships.json"
        return source_document_paths[0] if source_document_paths else None

    rows: list[dict[str, object]] = []
    for target, coverage in _covered_paths(payload):
        guidance = guidance_document or target.endswith("/ordinal") or target.endswith(
            "/xlsx_storage_mode"
        ) or "/format_hints" in target or target.endswith("/step_ordinal") or target.endswith(
            "/direction"
        ) or (path == "metadata/source-model.json" and "/r_paths" in target)
        rows.append(
            {
                "target_json_pointer": target,
                "coverage": coverage,
                "derivation_class": "S_GUIDANCE" if guidance else "R_PROJECTION",
                "source_pointers": []
                if guidance
                else [
                    {
                        "pointer_kind": "JSON_POINTER",
                        "source_document_path": pointer_path(target),
                        "json_pointer": "/",
                    }
                ],
                "algorithm_ref": algorithm,
            }
        )
    return sorted(rows, key=lambda item: (str(item["target_json_pointer"]), str(item["coverage"])))


def build_metadata_documents(
    *, root: Path, handoff_ref: str, source_model_digest: str
) -> dict[str, MetadataDocument]:
    """Build all eight closed metadata documents from copied R authorities."""

    manifest = ModelManifest.model_validate_json(
        (root / "source-model/model-manifest.json").read_bytes()
    )
    semantic = SemanticCatalogue.model_validate_json(
        (root / "source-model/semantic-model.json").read_bytes()
    )
    relationships = _load_json(root / "source-model/relationships.json")
    cache = NoncanonicalCacheManifest.model_validate_json(
        (root / "source-model/noncanonical-cache.json").read_bytes()
    )
    bindings = _dataset_bindings(manifest, semantic)
    table_by_identity = {
        (item.source_registry_id, item.source_dataset_id): item
        for item in manifest.table_entries
    }
    semantic_tables = [item.model_dump(mode="json") for item in semantic.tables]
    dictionary_tables = []
    for table in semantic_tables:
        coordinate = table["source_coordinate"]
        entry = table_by_identity[(coordinate["registry_id"], coordinate["dataset_id"])]
        dictionary_tables.append(
            table
            | {
                "primary_key": list(entry.primary_key),
                "unique_keys": [list(item) for item in entry.unique_keys],
            }
        )
    semantic_columns = [item.model_dump(mode="json") for item in semantic.columns]
    dictionary_columns = [
        item | {"ordinal": ordinal, "xlsx_storage_mode": _storage_mode(item["source_type"])}
        for ordinal, item in enumerate(semantic_columns, start=1)
    ]
    field_roles = [
        {
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
        }
        | {"format_hints": _format_hints(item)}
        for item in semantic_columns
    ]
    trace_ids = {"P-RL11", "P-RL12"}
    trace_relationships = [item for item in relationships if item["relationship_id"] in trace_ids]
    table_aliases = {
        (item.source_coordinate.registry_id, item.source_coordinate.dataset_id): item.physical_alias
        for item in semantic.tables
    }
    lineage_coordinates = [("P-EVIDENCE", "P-D16"), ("P-EVIDENCE", "P-D17")]
    cache_body = cache.model_dump(mode="json", exclude={"table_entries"}) | {
        "database_path": f"source-model/{cache.database_path}",
        "table_count": len(cache.table_entries),
        "table_bindings_digest": canonical_sha256(
            [item.model_dump(mode="json") for item in cache.table_entries]
        ),
    }
    validation = load_json_authority("validation-registry-v1.json")
    validation_coordinates: list[tuple[str, str]] = []
    for selector in validation["selectors"]:
        registry, dataset = selector["source_coordinate"].split("/")
        identity = (registry.split("@")[0], dataset.split("@")[0])
        if identity not in validation_coordinates:
            validation_coordinates.append(identity)

    payload_specs: list[tuple[str, tuple[str, ...], list[dict[str, object]], dict[str, Any]]] = [
        (
            "metadata/source-model.json",
            _MODEL_PATHS,
            list(bindings.values()),
            {
                "profile_coordinate": {"profile_id": "LINEAGE", "profile_version": 1},
                "source_formats": ["CSV", "PARQUET", "DUCKDB"],
                "r_paths": [item.removeprefix("source-model/") for item in _MODEL_PATHS],
                "r_cache_binding": cache_body,
                "table_entries": [item.model_dump(mode="json") for item in manifest.table_entries],
            },
        ),
        (
            "metadata/data-dictionary.json",
            _MODEL_PATHS[:2],
            list(bindings.values()),
            {"tables": dictionary_tables, "columns": dictionary_columns},
        ),
        (
            "metadata/relationships.json",
            ("source-model/relationships.json",),
            list(bindings.values()),
            {"relationships": relationships},
        ),
        (
            "metadata/measures.json",
            ("source-model/semantic-model.json",),
            list(bindings.values()),
            {"measures": [item.model_dump(mode="json") for item in semantic.measures]},
        ),
        (
            "metadata/field-roles.json",
            ("source-model/semantic-model.json",),
            list(bindings.values()),
            {"fields": field_roles},
        ),
        (
            "metadata/lineage.json",
            ("source-model/semantic-model.json", "source-model/relationships.json"),
            [bindings[item] for item in lineage_coordinates],
            {
                "dataset_pointers": [
                    {"source_coordinate": _coordinate(*item), "r_table_alias": table_aliases[item]}
                    for item in lineage_coordinates
                ],
                "directed_join_steps": [
                    {
                        "step_ordinal": index,
                        "relationship_id": item["relationship_id"],
                        "from_coordinate": _coordinate(item["from_registry"], item["from_dataset"]),
                        "from_fields": item["from_columns"],
                        "to_coordinate": _coordinate(item["to_registry"], item["to_dataset"]),
                        "to_fields": item["to_columns"],
                        "projected_key_ref": item["projected_key_ref"],
                        "direction": "FORWARD",
                    }
                    for index, item in enumerate(trace_relationships, start=1)
                ],
                "evidence_status_fields": [],
            },
        ),
        ("metadata/consumer-suitability.json", (), [], _consumer_suitability()),
        (
            "metadata/validation-checks.json",
            ("source-model/semantic-model.json", "source-model/relationships.json"),
            [bindings[item] for item in validation_coordinates],
            validation,
        ),
    ]
    handoff_binding = {
        "handoff_ref": handoff_ref,
        "source_model_ref": manifest.model_ref,
        "source_model_digest": source_model_digest,
        "source_package_digest": manifest.source_package_digest,
    }
    documents: dict[str, MetadataDocument] = {}
    for path, document_paths, dataset_rows, payload in payload_specs:
        document = MetadataDocument.model_validate_json(
            json.dumps(
                {
                "contract_version": METADATA_CONTRACTS[path],
                "handoff_binding": handoff_binding,
                "source_documents": _source_documents(root, document_paths),
                "source_datasets": dataset_rows,
                "field_provenance": _provenance(path, payload, document_paths),
                "payload": payload,
                },
                ensure_ascii=True,
            )
        )
        documents[path] = document
    return documents
