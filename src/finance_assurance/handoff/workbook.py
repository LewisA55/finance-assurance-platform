"""Create and independently reproduce the data-only Artifact S workbook."""

from __future__ import annotations

import io
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import duckdb
import xlsxwriter

from finance_assurance.digestion.contracts import ModelManifest, SemanticCatalogue
from finance_assurance.exports.serialization import sha256_bytes
from finance_assurance.handoff.authorities import split_sql_authority
from finance_assurance.handoff.digests import logical_workbook_digest, typed_rows_digest
from finance_assurance.handoff.metadata import (
    MetadataDocument,
    OpenXmlPartEntry,
    WorkbookColumnEntry,
    WorkbookNullCount,
    WorkbookSheetEntry,
)
from finance_assurance.handoff.profiles import (
    XLSX_TYPE_MAP_HASH,
    XLSX_WRITER_PROFILE,
)
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256

_SAFE_INTEGER = 999_999_999_999_999
_INVALID_SHEET = re.compile(r"[^A-Za-z0-9_ -]")
_INVALID_TABLE = re.compile(r"[^A-Za-z0-9_]")


@dataclass(frozen=True, slots=True)
class WorkbookBuild:
    payload: bytes
    logical_digest: str
    sheet_entries: tuple[WorkbookSheetEntry, ...]
    openxml_inventory: tuple[OpenXmlPartEntry, ...]
    validation_check_count: int


@dataclass(frozen=True, slots=True)
class _Sheet:
    kind: str
    identity: Any
    name: str
    table_name: str | None
    columns: tuple[WorkbookColumnEntry, ...]
    rows: tuple[tuple[Any, ...], ...]
    projection_ref: str | None = None
    projection_source_digest: str | None = None
    source_logical_table_digest: str | None = None
    source_technical_projection_digest: str | None = None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_text(value: Any) -> str:
    return canonical_bytes(value).decode("ascii")


def _typed_digest(sheet: _Sheet) -> str:
    return typed_rows_digest(
        {
            "contract_version": "xlsx-typed-rows@v1",
            "columns": [
                {
                    "ordinal": item.ordinal,
                    "name": item.name,
                    "source_type": item.source_type,
                }
                for item in sheet.columns
            ],
            "rows": [
                {
                    "row_ordinal": ordinal,
                    "cells": [
                        {
                            "is_null": value is None,
                            "source_type": column.source_type,
                            "value": value,
                        }
                        for column, value in zip(sheet.columns, row, strict=True)
                    ],
                }
                for ordinal, row in enumerate(sheet.rows, start=1)
            ],
        }
    )


def _column(
    ordinal: int,
    name: str,
    source_type: str,
    nullable: bool,
    rows: tuple[tuple[Any, ...], ...],
) -> WorkbookColumnEntry:
    mode = {
        "boolean": "BOOLEAN_NATIVE",
        "date": "TEXT_DATE_ISO",
        "timestamp": "TEXT_TIMESTAMP_UTC",
    }.get(source_type, "TEXT_EXACT")
    if source_type == "integer":
        values = [row[ordinal - 1] for row in rows if row[ordinal - 1] is not None]
        mode = (
            "NUMBER_EXACT"
            if all(abs(int(value)) <= _SAFE_INTEGER for value in values)
            else "TEXT_INT64"
        )
    return WorkbookColumnEntry(
        ordinal=ordinal,
        name=name,
        source_type=source_type,
        nullability=nullable,
        storage_mode=mode,
    )


def _metadata_sheet(
    *,
    sheet_id: str,
    rows: list[dict[str, Any]],
    projection_ref: str,
    projection_source_digest: str,
    declared_types: dict[str, str] | None = None,
) -> _Sheet:
    if not rows:
        raise ValueError(f"metadata sheet {sheet_id} cannot be empty")
    names = tuple(rows[0])
    normalized: list[tuple[Any, ...]] = []
    for row in rows:
        values: list[Any] = []
        if tuple(row) != names:
            raise ValueError(f"metadata sheet {sheet_id} row shape differs")
        for value in row.values():
            if isinstance(value, (dict, list, tuple)):
                values.append(_canonical_text(value))
            else:
                values.append(value)
        normalized.append(tuple(values))
    normalized_rows = tuple(normalized)
    columns = []
    for ordinal, name in enumerate(names, start=1):
        values = [row[ordinal - 1] for row in normalized_rows]
        source_type = (declared_types or {}).get(name)
        if source_type is None:
            present = next((value for value in values if value is not None), "")
            source_type = (
                "boolean"
                if type(present) is bool
                else "integer"
                if type(present) is int
                else "text"
            )
        columns.append(
            _column(ordinal, name, source_type, any(value is None for value in values), normalized_rows)
        )
    return _Sheet(
        kind="METADATA",
        identity=sheet_id,
        name=sheet_id,
        table_name=None,
        columns=tuple(columns),
        rows=normalized_rows,
        projection_ref=projection_ref,
        projection_source_digest=projection_source_digest,
    )


def _validation_rows(database_path: Path, validation: dict[str, Any]) -> list[dict[str, Any]]:
    query_by_id = dict(split_sql_authority("reconciliation-queries-v1.sql"))
    connection = duckdb.connect(str(database_path), read_only=True)
    rows: list[dict[str, Any]] = []
    try:
        for check in validation["checks"]:
            query_id = check["sql_query_id"]
            cursor = connection.execute(query_by_id[query_id])
            columns = [item[0] for item in cursor.description]
            result_rows = cursor.fetchall()
            if len(result_rows) != 1:
                raise ValueError(f"{query_id} did not return exactly one row")
            observed = dict(zip(columns, result_rows[0], strict=True))
            if observed.get("check_id") != check["check_id"]:
                raise ValueError(f"{query_id} returned the wrong check ID")
            for assertion in check["assertions"]:
                result_name = assertion["assertion_id"].lower().replace("-", "_") + "_pass"
                assertion_pass = observed.get(result_name)
                if type(assertion_pass) is not bool:
                    raise ValueError(f"{query_id} omitted {result_name}")
                rows.append(
                    {
                        "check_id": check["check_id"],
                        "assertion_id": assertion["assertion_id"],
                        "scenario_ref": check["scenario_ref"],
                        "classification": check["classification"],
                        "assertion_kind": assertion["kind"],
                        "expected_json": _canonical_text(assertion),
                        "observed_json": _canonical_text(
                            {"assertion_pass": assertion_pass, "query_id": query_id}
                        ),
                        "assertion_pass": assertion_pass,
                        "sql_query_id": query_id,
                    }
                )
        if not all(bool(row["assertion_pass"]) for row in rows):
            raise ValueError("one or more governed validation assertions failed")
        return rows
    finally:
        connection.close()


def _sheet_names(aliases: list[tuple[str, str]]) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    used_sheets = {item.casefold() for item in ("README", "DATA_DICTIONARY", "RELATIONSHIPS", "MEASURES", "VALIDATION_RESULTS")}
    used_tables: set[str] = set()
    for identity, alias in aliases:
        base = alias.removeprefix("r_")
        base = re.sub(r"_+", "_", _INVALID_SHEET.sub("_", base)).strip(" '")[:24]
        if not base or base.casefold() == "history":
            base = "data"
        suffix = sha256(identity.encode("ascii")).hexdigest()[:6]
        sheet = base
        if sheet.casefold() in used_sheets:
            sheet = f"{base[:24]}_{suffix}"
        used_sheets.add(sheet.casefold())
        table_base = "t_" + _INVALID_TABLE.sub("_", alias)
        if table_base[2:3].isdigit():
            table_base = "t__" + table_base[2:]
        table = table_base[:64]
        if table.casefold() in used_tables:
            table = f"{table_base[:57]}_{suffix}"
        used_tables.add(table.casefold())
        result[identity] = (sheet, table)
    return result


def _data_sheets(root: Path, manifest: ModelManifest, semantic: SemanticCatalogue) -> list[_Sheet]:
    table_by_identity = {
        (item.source_coordinate.registry_id, item.source_coordinate.dataset_id): item
        for item in semantic.tables
    }
    columns_by_identity: dict[tuple[str, str], dict[str, Any]] = {}
    for item in semantic.columns:
        identity = (item.source_coordinate.registry_id, item.source_coordinate.dataset_id)
        columns_by_identity.setdefault(identity, {})[item.source_name] = item
    identities = [
        f"{item.source_registry_id}@v{item.source_registry_version}/{item.source_dataset_id}@v{item.source_dataset_version}"
        for item in manifest.table_entries
    ]
    aliases = [
        (identity, table_by_identity[(entry.source_registry_id, entry.source_dataset_id)].physical_alias)
        for identity, entry in zip(identities, manifest.table_entries, strict=True)
    ]
    names = _sheet_names(aliases)
    sheets: list[_Sheet] = []
    for identity_text, entry in zip(identities, manifest.table_entries, strict=True):
        if entry.parquet_path is None:
            raise ValueError("Artifact S requires an R Parquet binding for every table")
        identity = (entry.source_registry_id, entry.source_dataset_id)
        table = table_by_identity[identity]
        parquet_path = root / "source-model" / entry.parquet_path
        semantic_columns = columns_by_identity[identity]
        projections = []
        for name in table.column_names:
            quoted = '"' + name.replace('"', '""') + '"'
            source_type = semantic_columns[name].source_type
            if source_type == "timestamp":
                projections.append(
                    f"strftime({quoted}, '%Y-%m-%dT%H:%M:%S.%fZ') AS {quoted}"
                )
            elif source_type == "date":
                projections.append(f"CAST({quoted} AS VARCHAR) AS {quoted}")
            else:
                projections.append(quoted)
        connection = duckdb.connect()
        try:
            cursor = connection.execute(
                f"SELECT {', '.join(projections)} FROM read_parquet(?) "
                "ORDER BY row_key",
                [str(parquet_path)],
            )
            parquet_columns = tuple(item[0] for item in cursor.description)
            parquet_rows = cursor.fetchall()
        finally:
            connection.close()
        if parquet_columns != table.column_names:
            raise ValueError(f"CSV header differs for {identity_text}")
        parsed: list[tuple[Any, ...]] = []
        for raw in parquet_rows:
            values: list[Any] = []
            for name, raw_value in zip(table.column_names, raw, strict=True):
                value: Any = raw_value
                column = semantic_columns[name]
                if value is None:
                    pass
                elif column.source_type == "integer":
                    value = int(value)
                elif column.source_type == "boolean":
                    if type(value) is not bool:
                        raise ValueError(f"noncanonical Boolean in {identity_text}.{name}")
                elif column.source_type == "date" and isinstance(value, date):
                    value = value.isoformat()
                elif column.source_type == "timestamp" and isinstance(value, datetime):
                    value = value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                values.append(value)
            parsed.append(tuple(values))
        parsed.sort(key=lambda row: str(row[0]))
        rows = tuple(parsed)
        columns = tuple(
            _column(
                ordinal,
                name,
                semantic_columns[name].source_type,
                any(row[ordinal - 1] is None for row in rows),
                rows,
            )
            for ordinal, name in enumerate(table.column_names, start=1)
        )
        sheet_name, table_name = names[identity_text]
        sheets.append(
            _Sheet(
                kind="DATA",
                identity=table.source_coordinate,
                name=sheet_name,
                table_name=table_name if rows else None,
                columns=columns,
                rows=rows,
                source_logical_table_digest=entry.logical_table_digest,
                source_technical_projection_digest=entry.technical_projection_digest,
            )
        )
    return sheets


def _metadata_sheets(
    *,
    root: Path,
    handoff_ref: str,
    model_digest: str,
    manifest: ModelManifest,
    documents: dict[str, MetadataDocument],
    built_at: str,
) -> tuple[list[_Sheet], int]:
    payloads = {path: document.payload.model_dump(mode="json") for path, document in documents.items()}
    readme_rows = [
        {"key": key, "value": value}
        for key, value in (
            ("synthetic_data", "true"),
            ("synthetic_data_notice", manifest.synthetic_data_notice),
            ("handoff_ref", handoff_ref),
            ("source_model_ref", manifest.model_ref),
            ("source_model_digest", model_digest),
            ("source_package_digest", manifest.source_package_digest),
            ("profile", "LINEAGE@v1"),
            ("formats", "CSV,PARQUET,DUCKDB"),
            ("limitations_path", "limitations.json"),
            ("consumer_suitability_path", "metadata/consumer-suitability.json"),
            ("validation_registry_digest", canonical_sha256(payloads["metadata/validation-checks.json"])),
            ("built_at", built_at),
        )
    ]
    validation_rows = _validation_rows(
        root / "source-model/warehouse/finance-assurance.duckdb",
        payloads["metadata/validation-checks.json"],
    )
    specs = [
        (
            "README",
            readme_rows,
            "S-README-PROJECTION@v1",
            canonical_sha256(readme_rows),
            None,
        ),
        (
            "DATA_DICTIONARY",
            payloads["metadata/data-dictionary.json"]["columns"],
            "S-DATA-DICTIONARY-SHEET@v1",
            canonical_sha256(payloads["metadata/data-dictionary.json"]),
            None,
        ),
        (
            "RELATIONSHIPS",
            payloads["metadata/relationships.json"]["relationships"],
            "S-RELATIONSHIPS-SHEET@v1",
            canonical_sha256(payloads["metadata/relationships.json"]),
            None,
        ),
        (
            "MEASURES",
            sorted(payloads["metadata/measures.json"]["measures"], key=lambda item: item["measure_id"]),
            "S-MEASURES-SHEET@v1",
            canonical_sha256(payloads["metadata/measures.json"]),
            None,
        ),
        (
            "VALIDATION_RESULTS",
            validation_rows,
            "S-VALIDATION-RESULTS@v1",
            canonical_sha256(payloads["metadata/validation-checks.json"]),
            {"assertion_pass": "boolean"},
        ),
    ]
    sheets = [
        _metadata_sheet(
            sheet_id=sheet_id,
            rows=rows,
            projection_ref=projection,
            projection_source_digest=digest,
            declared_types=types,
        )
        for sheet_id, rows, projection, digest, types in specs
    ]
    return sheets, len(payloads["metadata/validation-checks.json"]["checks"])


def _manifest_entry(sheet: _Sheet) -> WorkbookSheetEntry:
    null_counts = tuple(
        WorkbookNullCount(
            name=column.name,
            count=sum(row[column.ordinal - 1] is None for row in sheet.rows),
        )
        for column in sheet.columns
    )
    return WorkbookSheetEntry(
        sheet_kind=sheet.kind,
        source_dataset_coordinate=sheet.identity if sheet.kind == "DATA" else None,
        metadata_sheet_id=sheet.identity if sheet.kind == "METADATA" else None,
        sheet_name=sheet.name,
        table_name=sheet.table_name,
        columns=sheet.columns,
        typed_rows_digest=_typed_digest(sheet),
        row_count=len(sheet.rows),
        column_count=len(sheet.columns),
        null_counts=null_counts,
    )


def _logical_entry(sheet: _Sheet, entry: WorkbookSheetEntry) -> dict[str, Any]:
    body: dict[str, Any] = {
        "sheet_kind": sheet.kind,
        "sheet_name": sheet.name,
        "table_name": sheet.table_name,
        "columns": [item.model_dump(mode="json") for item in entry.columns],
        "typed_rows_digest": entry.typed_rows_digest,
        "row_count": entry.row_count,
        "column_count": entry.column_count,
        "null_counts": [item.model_dump(mode="json") for item in entry.null_counts],
    }
    if sheet.kind == "DATA":
        coordinate = sheet.identity
        body |= {
            "source_coordinate": (
                f"{coordinate.registry_id}@v{coordinate.registry_version}/"
                f"{coordinate.dataset_id}@v{coordinate.dataset_version}"
            ),
            "source_logical_table_digest": sheet.source_logical_table_digest,
            "source_technical_projection_digest": (
                sheet.source_technical_projection_digest
            ),
        }
    else:
        body |= {
            "metadata_sheet_id": sheet.identity,
            "projection_ref": sheet.projection_ref,
            "projection_source_digest": sheet.projection_source_digest,
        }
    return body


def _write_workbook(sheets: list[_Sheet], built_at: str) -> bytes:
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(
        output,
        {
            "in_memory": True,
            "constant_memory": False,
            "strings_to_formulas": False,
            "strings_to_urls": False,
            "strings_to_numbers": False,
            "nan_inf_to_errors": False,
            "remove_timezone": False,
        },
    )
    created = datetime.strptime(built_at, "%Y-%m-%dT%H:%M:%SZ")
    properties = dict(XLSX_WRITER_PROFILE.document_properties)
    properties["created"] = created
    workbook.set_properties(properties)
    workbook.set_calc_mode("manual")
    header = workbook.add_format(
        {"font_name": "Arial", "font_size": 10, "bold": True, "font_color": "#FFFFFF", "bg_color": "#1F4E78", "border": 1}
    )
    body = workbook.add_format({"font_name": "Arial", "font_size": 10})
    wrapped = workbook.add_format({"font_name": "Arial", "font_size": 10, "text_wrap": True})
    integer = workbook.add_format({"font_name": "Arial", "font_size": 10, "num_format": "0"})
    for sheet in sheets:
        if len(sheet.rows) + 1 > 1_048_576 or len(sheet.columns) > 16_384:
            raise ValueError(f"worksheet capacity exceeded for {sheet.name}")
        worksheet = workbook.add_worksheet(sheet.name)
        worksheet.freeze_panes(1, 0)
        worksheet.set_row(0, 22)
        for column_index, column in enumerate(sheet.columns):
            if sheet.name == "README" and column.name == "key":
                width = XLSX_WRITER_PROFILE.column_widths["README_KEY"]
            elif sheet.name == "README" and column.name == "value":
                width = XLSX_WRITER_PROFILE.column_widths["README_VALUE"]
            else:
                width = XLSX_WRITER_PROFILE.column_widths[column.storage_mode]
            worksheet.set_column(column_index, column_index, width)
            worksheet.write(0, column_index, column.name, header)
        for row_index, row in enumerate(sheet.rows, start=1):
            worksheet.set_row(row_index, 18)
            for column_index, (column, value) in enumerate(zip(sheet.columns, row, strict=True)):
                if value is None:
                    continue
                if isinstance(value, str) and len(value) > 32_767:
                    raise ValueError(f"cell text exceeds Excel capacity in {sheet.name}")
                cell_format = wrapped if sheet.kind == "METADATA" else body
                if column.storage_mode == "NUMBER_EXACT":
                    worksheet.write_number(row_index, column_index, int(value), integer)
                elif column.storage_mode == "BOOLEAN_NATIVE":
                    worksheet.write_boolean(row_index, column_index, bool(value), cell_format)
                elif column.storage_mode == "TEXT_INT64":
                    worksheet.write_string(row_index, column_index, str(value), cell_format)
                else:
                    worksheet.write_string(row_index, column_index, str(value), cell_format)
        if sheet.kind == "DATA" and sheet.rows:
            worksheet.add_table(
                0,
                0,
                len(sheet.rows),
                len(sheet.columns) - 1,
                {
                    "name": sheet.table_name,
                    "style": "Table Style Medium 2",
                    "columns": [{"header": item.name} for item in sheet.columns],
                },
            )
        else:
            worksheet.autofilter(0, 0, len(sheet.rows), len(sheet.columns) - 1)
    workbook.close()
    return output.getvalue()


def _openxml_inventory(payload: bytes) -> tuple[OpenXmlPartEntry, ...]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        content_root = ElementTree.fromstring(archive.read("[Content_Types].xml"))
        defaults = {
            item.attrib["Extension"]: item.attrib["ContentType"]
            for item in content_root
            if item.tag.endswith("Default")
        }
        overrides = {
            item.attrib["PartName"].lstrip("/"): item.attrib["ContentType"]
            for item in content_root
            if item.tag.endswith("Override")
        }
        rows = []
        for path in sorted(archive.namelist()):
            if path.endswith("/"):
                continue
            data = archive.read(path)
            relationship_types: tuple[str, ...] = ()
            if path.endswith(".rels"):
                root = ElementTree.fromstring(data)
                relationship_types = tuple(sorted(item.attrib["Type"] for item in root))
            extension = path.rsplit(".", 1)[-1] if "." in path else ""
            rows.append(
                OpenXmlPartEntry(
                    path=path,
                    content_type=overrides.get(path, defaults.get(extension, "application/octet-stream")),
                    sha256=sha256_bytes(data),
                    relationship_type_ids=relationship_types,
                )
            )
        return tuple(rows)


def build_workbook(
    *,
    root: Path,
    handoff_ref: str,
    source_model_digest: str,
    built_at: str,
    documents: dict[str, MetadataDocument],
) -> WorkbookBuild:
    if xlsxwriter.__version__ != "3.2.9":
        raise RuntimeError("Artifact S requires exact XlsxWriter 3.2.9")
    manifest = ModelManifest.model_validate_json(
        (root / "source-model/model-manifest.json").read_bytes()
    )
    semantic = SemanticCatalogue.model_validate_json(
        (root / "source-model/semantic-model.json").read_bytes()
    )
    metadata_sheets, validation_count = _metadata_sheets(
        root=root,
        handoff_ref=handoff_ref,
        model_digest=source_model_digest,
        manifest=manifest,
        documents=documents,
        built_at=built_at,
    )
    sheets = [*metadata_sheets, *_data_sheets(root, manifest, semantic)]
    entries = tuple(_manifest_entry(sheet) for sheet in sheets)
    logical_preimage = {
        "contract_version": "logical-workbook-digest@v1",
        "xlsx_type_map_ref": "XLSX-TYPE-MAP@v1",
        "xlsx_type_map_hash": XLSX_TYPE_MAP_HASH,
        "source_model_digest": source_model_digest,
        "source_package_digest": manifest.source_package_digest,
        "sheet_order": [sheet.name for sheet in sheets],
        "sheet_entries": [
            _logical_entry(sheet, entry)
            for sheet, entry in zip(sheets, entries, strict=True)
        ],
    }
    payload = _write_workbook(sheets, built_at)
    return WorkbookBuild(
        payload=payload,
        logical_digest=logical_workbook_digest(logical_preimage),
        sheet_entries=entries,
        openxml_inventory=_openxml_inventory(payload),
        validation_check_count=validation_count,
    )


def workbook_sha256(value: bytes) -> str:
    return sha256_bytes(value)
