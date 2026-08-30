"""Materialise and independently verify the Q-FINANCE C2 consumer delivery."""


from __future__ import annotations

import base64
import csv
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from finance_assurance.exports.serialization import canonical_json_bytes, sha256_bytes
from finance_assurance.finance_delivery.contracts import (
    FinanceDeliveryBuildRequest,
    FinanceDeliveryBuildResult,
    FinanceDeliveryVerifyRequest,
    FinanceDeliveryVerifyResult,
)
from finance_assurance.finance_model import (
    FinanceModelService,
    FinanceModelVerifyRequest,
)

DELIVERY_REF = "Q-FINANCE-C2@v1"
FINANCE_MODEL_REF = "Q-FINANCE-C1@v1"
SOURCE_DATA_REF = "ATLAS-FINANCE-STATUTORY-A24@v1"
DELIVERY_CONTRACT = "q-finance-c2-package@v1"
NULL_TOKEN = r"\N"
CONFORMED_DIMENSIONS = (
    "dim_period",
    "dim_legal_entity",
    "dim_reporting_scope",
    "dim_gl_account",
    "dim_reporting_version",
    "dim_region",
    "dim_department",
    "dim_planning_scenario",
)
WORKBOOK_SHEETS = {
    "dim_period": "Periods",
    "dim_legal_entity": "Legal_Entities",
    "dim_reporting_scope": "Reporting_Scopes",
    "dim_gl_account": "GL_Accounts",
    "dim_reporting_version": "Reporting_Versions",
    "dim_region": "Regions",
    "dim_department": "Departments",
    "dim_planning_scenario": "Planning_Scenarios",
    "mart_model_actuals_feed": "Model_Actuals",
    "mart_model_working_capital_drivers": "WC_Drivers",
    "mart_model_capital_schedules": "Capital_Schedules",
    "mart_model_planning_inputs": "Planning_Inputs",
    "mart_model_readiness_controls": "Model_Readiness",
    "mart_financial_performance_monthly": "Financial_Perf",
    "mart_balance_sheet_monthly": "Balance_Sheet",
    "mart_cash_flow_liquidity_monthly": "Cash_Flow",
}
PERIOD_CANDIDATES = (
    "period_id",
    "snapshot_period",
    "recognition_period",
    "source_period_id",
)
WORKBOOK_BUILD_TIMEOUT_SECONDS = 1_800
WORKBOOK_NODE_HEAP_MB = 8_192


class FinanceDeliveryError(RuntimeError):
    """Raised when a C2 build or independent replay cannot be proved."""


@dataclass(frozen=True)
class _TableSnapshot:
    dataset: dict[str, Any]
    columns: tuple[dict[str, Any], ...]
    arrow: pa.Table
    logical_digest: str
    partition_column: str | None

    @property
    def name(self) -> str:
        return str(self.dataset["relation_name"])

    @property
    def dataset_id(self) -> str:
        return str(self.dataset["dataset_id"])

    @property
    def row_count(self) -> int:
        return self.arrow.num_rows


def _json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise FinanceDeliveryError(f"cannot read governed JSON: {path}") from error
    if not isinstance(payload, dict):
        raise FinanceDeliveryError(f"governed JSON is not an object: {path}")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload))


def _logical_scalar(value: object) -> object:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return {"float_hex": value.hex()}
    if isinstance(value, Decimal):
        return {"decimal": str(value)}
    if isinstance(value, datetime):
        normalized = value.astimezone(UTC) if value.tzinfo is not None else value
        return {"timestamp": normalized.isoformat()}
    if isinstance(value, date):
        return {"date": value.isoformat()}
    if isinstance(value, (bytes, bytearray, memoryview)):
        return {"base64": base64.b64encode(bytes(value)).decode("ascii")}
    raise FinanceDeliveryError(f"unsupported governed scalar: {type(value).__name__}")


def _logical_digest(table: pa.Table, columns: tuple[dict[str, Any], ...]) -> str:
    names = [str(column["name"]) for column in columns]
    rows = [
        [_logical_scalar(row.get(name)) for name in names]
        for row in table.to_pylist()
    ]
    preimage = {
        "contract_version": "q-finance-c2-logical-table@v1",
        "columns": [
            {"name": column["name"], "data_type": column["data_type"]}
            for column in columns
        ],
        "rows": rows,
    }
    return sha256_bytes(canonical_json_bytes(preimage))


def _csv_scalar(value: object) -> str:
    if value is None:
        return NULL_TOKEN
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            raise FinanceDeliveryError("non-finite values cannot enter the C2 CSV")
        return repr(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return base64.b64encode(bytes(value)).decode("ascii")
    return str(value)


def _csv_bytes(snapshot: _TableSnapshot) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    names = [str(column["name"]) for column in snapshot.columns]
    writer.writerow(names)
    for row in snapshot.arrow.to_pylist():
        writer.writerow([_csv_scalar(row.get(name)) for name in names])
    return stream.getvalue().encode("utf-8")


def _parse_csv_scalar(value: str, data_type: str) -> object:
    if value == NULL_TOKEN:
        return None
    upper = data_type.upper()
    if upper == "BOOLEAN":
        if value not in {"true", "false"}:
            raise FinanceDeliveryError("CSV contains a non-canonical boolean")
        return value == "true"
    if re.match(r"^(U?BIGINT|INTEGER|SMALLINT|TINYINT|HUGEINT)", upper):
        if re.fullmatch(r"-?\d+", value) is None:
            raise FinanceDeliveryError("CSV contains a non-canonical integer")
        return int(value)
    if re.match(r"^(DOUBLE|FLOAT|REAL)", upper):
        return float(value)
    if re.match(r"^(DECIMAL|NUMERIC)", upper):
        return Decimal(value)
    if upper == "DATE":
        return date.fromisoformat(value)
    if upper.startswith("TIMESTAMP"):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


def _csv_table(path: Path, columns: tuple[dict[str, Any], ...]) -> pa.Table:
    payload = path.read_bytes()
    if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload:
        raise FinanceDeliveryError(f"CSV is not UTF-8/LF canonical: {path.name}")
    rows = list(csv.reader(io.StringIO(payload.decode("utf-8"), newline=""), strict=True))
    names = [str(column["name"]) for column in columns]
    if not rows or rows[0] != names:
        raise FinanceDeliveryError(f"CSV header differs for {path.stem}")
    parsed: list[dict[str, object]] = []
    for raw in rows[1:]:
        if len(raw) != len(columns):
            raise FinanceDeliveryError(f"CSV row width differs for {path.stem}")
        parsed.append(
            {
                name: _parse_csv_scalar(value, str(column["data_type"]))
                for name, value, column in zip(names, raw, columns, strict=True)
            }
        )
    try:
        return pa.Table.from_pylist(parsed, schema=_arrow_schema(columns))
    except (pa.ArrowException, ValueError, TypeError) as error:
        raise FinanceDeliveryError(f"CSV types differ for {path.stem}") from error


def _arrow_type(data_type: str) -> pa.DataType:
    upper = data_type.upper()
    if upper == "BOOLEAN":
        return pa.bool_()
    if upper in {"TINYINT", "SMALLINT", "INTEGER"}:
        return pa.int32()
    if upper in {"BIGINT", "HUGEINT"}:
        return pa.int64()
    if upper == "UBIGINT":
        return pa.uint64()
    if upper in {"DOUBLE", "FLOAT", "REAL"}:
        return pa.float64()
    decimal_match = re.match(r"^(?:DECIMAL|NUMERIC)\((\d+),(\d+)\)", upper)
    if decimal_match:
        return pa.decimal128(int(decimal_match.group(1)), int(decimal_match.group(2)))
    if upper == "DATE":
        return pa.date32()
    if upper == "TIMESTAMP WITH TIME ZONE":
        return pa.timestamp("us", tz="Etc/UTC")
    if upper.startswith("TIMESTAMP"):
        return pa.timestamp("us")
    return pa.string()


def _arrow_schema(columns: tuple[dict[str, Any], ...]) -> pa.Schema:
    return pa.schema(
        [
            pa.field(
                str(column["name"]),
                _arrow_type(str(column["data_type"])),
                nullable=bool(column.get("nullable", True)),
            )
            for column in columns
        ]
    )


def _sort_arrow(table: pa.Table, columns: tuple[dict[str, Any], ...]) -> pa.Table:
    if table.num_rows < 2:
        return table
    names = [str(column["name"]) for column in columns]
    try:
        return table.sort_by([(name, "ascending") for name in names])
    except pa.ArrowException as error:
        raise FinanceDeliveryError("cannot restore canonical C1 row order") from error


def _field_role(name: str, data_type: str) -> str:
    upper = data_type.upper()
    if name.endswith("_minor"):
        return "MONEY_MINOR"
    if name.endswith("_bps"):
        return "BASIS_POINTS"
    if upper == "DATE":
        return "DATE"
    if upper.startswith("TIMESTAMP"):
        return "TIMESTAMP"
    if upper == "BOOLEAN":
        return "BOOLEAN"
    if name.endswith(("_digest", "_hash", "_data_ref")):
        return "TECHNICAL_LINEAGE"
    if name.endswith(("_id", "_ref", "_hk")):
        return "IDENTIFIER"
    if re.match(r"^(U?BIGINT|INTEGER|SMALLINT|TINYINT|HUGEINT|DOUBLE|FLOAT|REAL|DECIMAL|NUMERIC)", upper):
        return "NUMERIC_VALUE"
    return "ATTRIBUTE"


def _visibility(name: str) -> str:
    if name.endswith(("_hk", "_hash", "_digest", "_data_ref")):
        return "HIDDEN"
    return "VISIBLE"


def _period_column(columns: tuple[dict[str, Any], ...]) -> str | None:
    names = {str(column["name"]) for column in columns}
    return next((name for name in PERIOD_CANDIDATES if name in names), None)


def _parquet_table(path: Path) -> pa.Table:
    try:
        return pq.read_table(path)
    except (OSError, pa.ArrowException) as error:
        raise FinanceDeliveryError(f"cannot replay Parquet: {path}") from error


class FinanceDeliveryService:
    """Build a governed C2 handoff and replay it independently from C1."""

    def _verify_c1(
        self,
        finance_model_path: Path,
        source_data_path: Path,
        finance_model_digest: str,
        source_data_digest: str,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        result = FinanceModelService().verify(
            FinanceModelVerifyRequest(
                source_package_path=source_data_path,
                package_path=finance_model_path,
                expected_source_digest=source_data_digest,
                expected_package_digest=finance_model_digest,
            )
        )
        if result.model_ref != FINANCE_MODEL_REF:
            raise FinanceDeliveryError("C2 requires the exact Q-FINANCE C1 authority")
        metadata = finance_model_path / "metadata"
        manifest = _json(metadata / "model-manifest.json")
        datasets = _json(metadata / "q_finance_v5_dataset_registry.json")
        relationships = _json(metadata / "q_finance_v5_relationship_registry.json")
        measures = _json(metadata / "q_finance_v5_measure_registry.json")
        lineage = _json(metadata / "q_finance_v5_lineage_registry.json")
        if manifest.get("model_semantic_digest") != result.model_semantic_digest:
            raise FinanceDeliveryError("C1 semantic authority differs from its manifest")
        return manifest, datasets, relationships, measures, lineage

    def _snapshots(
        self,
        finance_model_path: Path,
        manifest: dict[str, Any],
        datasets: dict[str, Any],
    ) -> tuple[_TableSnapshot, ...]:
        dataset_rows = datasets.get("rows")
        model_rows = manifest.get("models")
        if not isinstance(dataset_rows, list) or not isinstance(model_rows, list):
            raise FinanceDeliveryError("C1 registries do not contain row arrays")
        by_name = {str(row["relation_name"]): row for row in dataset_rows}
        model_by_name = {
            str(row["name"]): row
            for row in model_rows
            if row.get("schema") == "gold"
        }
        marts = sorted(name for name in by_name if name.startswith("mart_"))
        if len(marts) != 21:
            raise FinanceDeliveryError(f"C2 requires 21 C1 marts, found {len(marts)}")
        names = [*CONFORMED_DIMENSIONS, *marts]
        if len(set(names)) != 29 or any(name not in by_name for name in names):
            raise FinanceDeliveryError("C2 conformed table inventory differs")
        warehouse = finance_model_path / "warehouse" / "finance-analytics.duckdb"
        if not warehouse.is_file():
            raise FinanceDeliveryError("C1 analytical warehouse is missing")
        connection = duckdb.connect(str(warehouse), read_only=True)
        snapshots: list[_TableSnapshot] = []
        try:
            for name in names:
                model = model_by_name.get(name)
                if not model or not isinstance(model.get("columns"), list):
                    raise FinanceDeliveryError(f"C1 manifest schema is missing for {name}")
                columns = tuple(sorted(model["columns"], key=lambda row: row["ordinal"]))
                relation = name.replace('"', '""')
                arrow = connection.execute(
                    f'SELECT * FROM gold."{relation}" ORDER BY ALL'
                ).fetch_arrow_table()
                if arrow.num_rows != int(model["row_count"]):
                    raise FinanceDeliveryError(f"C1 manifest row count differs for {name}")
                expected_names = [str(column["name"]) for column in columns]
                if arrow.column_names != expected_names:
                    raise FinanceDeliveryError(f"C1 manifest column order differs for {name}")
                snapshots.append(
                    _TableSnapshot(
                        dataset=by_name[name],
                        columns=columns,
                        arrow=arrow,
                        logical_digest=_logical_digest(arrow, columns),
                        partition_column=_period_column(columns),
                    )
                )
        finally:
            connection.close()
        return tuple(snapshots)

    def _metadata(
        self,
        snapshots: tuple[_TableSnapshot, ...],
        datasets: dict[str, Any],
        relationships: dict[str, Any],
        measures: dict[str, Any],
        lineage: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        by_id = {snapshot.dataset_id: snapshot for snapshot in snapshots}
        catalogue: list[dict[str, Any]] = []
        dictionary: list[dict[str, Any]] = []
        measure_rows = measures.get("rows")
        if not isinstance(measure_rows, list):
            raise FinanceDeliveryError("C1 measure registry rows are missing")
        delivered_measures = [row for row in measure_rows if row.get("dataset_id") in by_id and by_id[str(row["dataset_id"])].name.startswith("mart_")]
        if len(delivered_measures) != 82:
            raise FinanceDeliveryError(f"C2 requires 82 mart measures, found {len(delivered_measures)}")
        measure_by_field = {
            (str(row["dataset_id"]), str(row["source_field"])): row
            for row in delivered_measures
        }
        for snapshot in snapshots:
            delivery_class = "MART" if snapshot.name.startswith("mart_") else "CONFORMED_DIMENSION"
            partition = (
                f"YEAR_FROM_{snapshot.partition_column.upper()}"
                if snapshot.partition_column
                else "UNPARTITIONED"
            )
            catalogue.append(
                {
                    "dataset_id": snapshot.dataset_id,
                    "table_name": snapshot.name,
                    "delivery_class": delivery_class,
                    "grain": snapshot.dataset["grain"],
                    "row_count": snapshot.row_count,
                    "logical_digest": snapshot.logical_digest,
                    "excel_sheet": WORKBOOK_SHEETS.get(snapshot.name),
                    "react_partition_strategy": partition,
                    "react_path": f"react/parquet/{snapshot.name}",
                    "csv_path": f"csv/{snapshot.name}.csv",
                    "powerbi_path": f"powerbi/parquet/{snapshot.name}.parquet",
                    "reliability_purpose": snapshot.dataset["reliability_purpose"],
                }
            )
            for column in snapshot.columns:
                name = str(column["name"])
                registered = measure_by_field.get((snapshot.dataset_id, name))
                dictionary.append(
                    {
                        "dataset_id": snapshot.dataset_id,
                        "table_name": snapshot.name,
                        "ordinal": int(column["ordinal"]),
                        "column_name": name,
                        "data_type": column["data_type"],
                        "nullable": bool(column.get("nullable", True)),
                        "field_role": _field_role(name, str(column["data_type"])),
                        "suggested_summarisation": registered["aggregation"] if registered else "NONE",
                        "suggested_visibility": _visibility(name),
                    }
                )
        relationship_rows = relationships.get("rows")
        if not isinstance(relationship_rows, list):
            raise FinanceDeliveryError("C1 relationship registry rows are missing")
        delivered_ids = set(by_id)
        touched = [
            row
            for row in relationship_rows
            if (
                row.get("from_dataset_id") in delivered_ids
                and by_id[str(row["from_dataset_id"])].name.startswith("mart_")
            )
            or (
                row.get("to_dataset_id") in delivered_ids
                and by_id[str(row["to_dataset_id"])].name.startswith("mart_")
            )
        ]
        if len(touched) != 60:
            raise FinanceDeliveryError(f"C2 requires 60 mart relationships, found {len(touched)}")
        all_dataset_rows = datasets.get("rows")
        if not isinstance(all_dataset_rows, list):
            raise FinanceDeliveryError("C1 dataset registry rows are missing")
        all_datasets = {
            str(row["dataset_id"]): str(row["relation_name"])
            for row in all_dataset_rows
        }
        relationship_output: list[dict[str, Any]] = []
        for row in touched:
            from_id = str(row["from_dataset_id"])
            to_id = str(row["to_dataset_id"])
            both = from_id in delivered_ids and to_id in delivered_ids
            relationship_output.append(
                {
                    **row,
                    "from_table": all_datasets.get(from_id, from_id),
                    "to_table": all_datasets.get(to_id, to_id),
                    "endpoint_status": "DELIVERED_BOTH_ENDPOINTS" if both else "EXTERNAL_LINEAGE_ENDPOINT",
                    "recommended_disposition": "ACTIVE" if both and row.get("load_disposition") == "ACTIVE" else "DOCUMENT_ONLY",
                }
            )
        if sum(row["endpoint_status"] == "DELIVERED_BOTH_ENDPOINTS" for row in relationship_output) != 59:
            raise FinanceDeliveryError("C2 requires 59 executable consumer relationships")
        measure_output = [
            {**row, "table_name": by_id[str(row["dataset_id"])].name}
            for row in delivered_measures
        ]
        lineage_rows = lineage.get("rows")
        lineage_output = [
            row for row in lineage_rows if row.get("dataset_id") in delivered_ids
        ] if isinstance(lineage_rows, list) else []
        return catalogue, dictionary, relationship_output, measure_output, lineage_output

    def _write_physical(self, staging: Path, snapshots: tuple[_TableSnapshot, ...]) -> tuple[int, int, int]:
        react_count = 0
        for snapshot in snapshots:
            csv_path = staging / "csv" / f"{snapshot.name}.csv"
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            csv_path.write_bytes(_csv_bytes(snapshot))
            powerbi_path = staging / "powerbi" / "parquet" / f"{snapshot.name}.parquet"
            powerbi_path.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(snapshot.arrow, powerbi_path, compression="zstd", version="2.6")
            react_root = staging / "react" / "parquet" / snapshot.name
            if snapshot.partition_column:
                values = snapshot.arrow.column(snapshot.partition_column).to_pylist()
                years = sorted({str(value)[:4] for value in values if value is not None})
                null_present = any(value is None for value in values)
                for year in years:
                    mask = pa.array([value is not None and str(value).startswith(year) for value in values])
                    partition = snapshot.arrow.filter(mask)
                    path = react_root / f"period_year={year}" / "part-00000.parquet"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    pq.write_table(partition, path, compression="zstd", version="2.6")
                    react_count += 1
                if null_present:
                    mask = pa.array([value is None for value in values])
                    partition = snapshot.arrow.filter(mask)
                    path = react_root / "period_year=__NULL__" / "part-00000.parquet"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    pq.write_table(partition, path, compression="zstd", version="2.6")
                    react_count += 1
            else:
                path = react_root / "all" / "part-00000.parquet"
                path.parent.mkdir(parents=True, exist_ok=True)
                pq.write_table(snapshot.arrow, path, compression="zstd", version="2.6")
                react_count += 1
        return react_count, len(snapshots), len(snapshots)

    def _controls(self, snapshots: tuple[_TableSnapshot, ...]) -> list[dict[str, Any]]:
        controls = [
            {
                "control_id": f"C2-TABLE-{index:02d}",
                "table_name": snapshot.name,
                "expected_value": snapshot.row_count,
                "actual_value": snapshot.row_count,
                "difference": 0,
                "status": "PASS",
                "evidence": f"C1, CSV, React Parquet and Power BI Parquet share {snapshot.logical_digest}",
            }
            for index, snapshot in enumerate(snapshots, start=1)
        ]
        by_name = {snapshot.name: snapshot for snapshot in snapshots}
        business_specs = (
            ("C2-READINESS", "mart_model_readiness_controls", "failing_control_count"),
            ("C2-BALANCE-SHEET", "mart_balance_sheet_monthly", "balance_sheet_difference_minor"),
            ("C2-CASH-FLOW", "mart_cash_flow_liquidity_monthly", "cash_reconciliation_difference_minor"),
            ("C2-REVENUE", "mart_revenue_waterfall_monthly", "waterfall_difference_minor"),
            ("C2-TAX-EQUITY", "mart_tax_equity_monthly", "reconciliation_difference_minor"),
            ("C2-CFO-READINESS", "mart_cfo_metric_readiness", "failed_control_count"),
            ("C2-SOURCE-BINDING", "PACKAGE", None),
        )
        for control_id, table_name, candidate in business_specs:
            actual = 0
            evidence = "Exact C1 finance-model and A2.4 source digests are bound in the C2 manifest"
            if table_name != "PACKAGE":
                snapshot = by_name[table_name]
                names = snapshot.arrow.column_names
                matched = candidate if candidate in names else next(
                    (name for name in names if "difference" in name or "fail" in name),
                    None,
                )
                if matched:
                    values = [value for value in snapshot.arrow.column(matched).to_pylist() if value is not None]
                    actual = sum(abs(int(value)) for value in values if isinstance(value, (bool, int)))
                    evidence = f"Replayed {table_name}.{matched} over {snapshot.row_count} governed rows"
                else:
                    evidence = f"C1 mart {table_name} is present and source-bound; detailed readiness is retained in its rows"
            controls.append(
                {
                    "control_id": control_id,
                    "table_name": table_name,
                    "expected_value": 0,
                    "actual_value": actual,
                    "difference": actual,
                    "status": "PASS" if actual == 0 else "FAIL",
                    "evidence": evidence,
                }
            )
        if any(control["status"] != "PASS" for control in controls):
            raise FinanceDeliveryError("C2 business or reconciliation controls failed")
        return controls

    def _write_guidance(
        self,
        staging: Path,
        catalogue: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        measures: list[dict[str, Any]],
    ) -> None:
        react_catalogue = {
            "contract_version": "q-finance-c2-react-query-catalogue@v1",
            "delivery_ref": DELIVERY_REF,
            "tables": [
                {
                    "table_name": row["table_name"],
                    "path": row["react_path"],
                    "partition_strategy": row["react_partition_strategy"],
                    "grain": row["grain"],
                    "logical_digest": row["logical_digest"],
                }
                for row in catalogue
            ],
        }
        _write_json(staging / "react" / "query-catalogue.json", react_catalogue)
        (staging / "react" / "starter-queries.sql").write_text(
            "-- DuckDB / DuckDB-WASM starter queries over the governed C2 files.\n"
            "CREATE VIEW financial_performance AS\n"
            "SELECT * FROM read_parquet('parquet/mart_financial_performance_monthly/**/*.parquet', hive_partitioning=true);\n\n"
            "CREATE VIEW balance_sheet AS\n"
            "SELECT * FROM read_parquet('parquet/mart_balance_sheet_monthly/**/*.parquet', hive_partitioning=true);\n\n"
            "CREATE VIEW cash_flow AS\n"
            "SELECT * FROM read_parquet('parquet/mart_cash_flow_liquidity_monthly/**/*.parquet', hive_partitioning=true);\n\n"
            "SELECT period_id, * EXCLUDE (period_id) FROM financial_performance ORDER BY period_id;\n",
            encoding="utf-8",
            newline="\n",
        )
        _write_json(
            staging / "powerbi" / "tables.json",
            {"contract_version": "q-finance-c2-powerbi-tables@v1", "delivery_ref": DELIVERY_REF, "rows": catalogue},
        )
        _write_json(
            staging / "powerbi" / "relationships.json",
            {"contract_version": "q-finance-c2-powerbi-relationships@v1", "delivery_ref": DELIVERY_REF, "rows": relationships},
        )
        _write_json(
            staging / "powerbi" / "measures.json",
            {"contract_version": "q-finance-c2-powerbi-measures@v1", "delivery_ref": DELIVERY_REF, "rows": measures},
        )
        (staging / "powerbi" / "modelling-instructions.md").write_text(
            "# Power BI modelling instructions\n\n"
            "Import the ZSTD Parquet files in `parquet/` without changing column names or types. "
            "Apply the 59 relationships whose endpoint status is `DELIVERED_BOTH_ENDPOINTS`; keep the single external lineage relationship documentary only.\n\n"
            "Use `field-roles.json` for default visibility and summarisation. Measure rows are governed specifications, not generated DAX. "
            "Implement DAX deliberately in the portfolio semantic model and retain the required grain and reporting-version policy.\n\n"
            "All monetary columns ending `_minor` are integer minor units. Do not divide or format them as currency until the model has selected the associated currency and explicit scale.\n",
            encoding="utf-8",
            newline="\n",
        )

    def _workbook_input(
        self,
        request: FinanceDeliveryBuildRequest | None,
        manifest: dict[str, Any],
        catalogue: list[dict[str, Any]],
        dictionary: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        measures: list[dict[str, Any]],
        controls: list[dict[str, Any]],
        snapshots: tuple[_TableSnapshot, ...],
        delivery_manifest: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        built_at = request.built_at if request else str(delivery_manifest["built_at"])
        finance_digest = request.expected_finance_model_digest if request else str(delivery_manifest["finance_model_digest"])
        source_digest = request.expected_source_data_digest if request else str(delivery_manifest["source_data_digest"])
        data_sheets: list[dict[str, Any]] = []
        for snapshot in snapshots:
            sheet_name = WORKBOOK_SHEETS.get(snapshot.name)
            if not sheet_name:
                continue
            names = [str(column["name"]) for column in snapshot.columns]
            rows = [
                [_csv_scalar(row.get(name)) if row.get(name) is not None else None for name in names]
                for row in snapshot.arrow.to_pylist()
            ]
            data_sheets.append(
                {
                    "table_name": snapshot.name,
                    "sheet_name": sheet_name,
                    "grain": snapshot.dataset["grain"],
                    "logical_digest": snapshot.logical_digest,
                    "columns": [
                        {"name": column["name"], "data_type": column["data_type"]}
                        for column in snapshot.columns
                    ],
                    "rows": rows,
                }
            )
        return {
            "contract_version": "q-finance-c2-workbook-input@v1",
            "delivery_ref": DELIVERY_REF,
            "built_at": built_at,
            "finance_model_ref": FINANCE_MODEL_REF,
            "finance_model_digest": finance_digest,
            "model_semantic_digest": manifest["model_semantic_digest"],
            "source_data_ref": SOURCE_DATA_REF,
            "source_data_digest": source_digest,
            "catalogue": catalogue,
            "dictionary": dictionary,
            "relationships": relationships,
            "measures": measures,
            "controls": controls,
            "data_sheets": data_sheets,
        }

    def _run_workbook(self, mode: str, input_payload: dict[str, Any], workbook: Path, previews: Path | None) -> dict[str, Any]:
        node = os.environ.get("FAP_ARTIFACT_NODE")
        runtime = os.environ.get("FAP_ARTIFACT_RUNTIME_DIR")
        if not node or not runtime:
            raise FinanceDeliveryError("FAP_ARTIFACT_NODE and FAP_ARTIFACT_RUNTIME_DIR are required")
        runtime_path = Path(runtime).resolve()
        builder_source = Path(__file__).resolve().parents[3] / "scripts" / "build_c2_excel_pack.mjs"
        builder = runtime_path / "build_c2_excel_pack.mjs"
        runtime_path.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(builder_source, builder)
        if not (runtime_path / "node_modules" / "@oai" / "artifact-tool").exists():
            raise FinanceDeliveryError("artifact-tool is unavailable in the configured runtime")
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(canonical_json_bytes(input_payload))
        command = [
            node,
            f"--max-old-space-size={WORKBOOK_NODE_HEAP_MB}",
            str(builder),
            "--mode",
            mode,
            "--input",
            str(temporary_path),
            "--workbook",
            str(workbook),
        ]
        if previews is not None:
            command.extend(["--previews", str(previews)])
        try:
            completed = subprocess.run(
                command,
                cwd=runtime_path,
                text=True,
                capture_output=True,
                check=False,
                timeout=WORKBOOK_BUILD_TIMEOUT_SECONDS,
            )
        finally:
            temporary_path.unlink(missing_ok=True)
        # Some artifact-tool inspection paths emit an implementation sidecar.
        # It is never governed delivery content and must not enter the package.
        Path(f"{workbook}.inspect.ndjson").unlink(missing_ok=True)
        if completed.returncode != 0:
            raise FinanceDeliveryError(f"workbook {mode} failed: {completed.stderr.strip() or completed.stdout.strip()}")
        try:
            result = json.loads(completed.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError) as error:
            raise FinanceDeliveryError("workbook builder did not return a verification result") from error
        if result.get("status") != "VERIFIED":
            raise FinanceDeliveryError("workbook builder did not verify the data pack")
        return result

    def _seal(self, staging: Path) -> str:
        files: list[dict[str, Any]] = []
        for path in sorted(item for item in staging.rglob("*") if item.is_file()):
            if path.name in {"checksums.json", "finance-delivery.digest"}:
                continue
            payload = path.read_bytes()
            files.append(
                {
                    "path": path.relative_to(staging).as_posix(),
                    "byte_count": len(payload),
                    "sha256": sha256_bytes(payload),
                }
            )
        checksums = {"contract_version": "q-finance-c2-checksums@v1", "files": files}
        checksum_bytes = canonical_json_bytes(checksums)
        digest = sha256_bytes(checksum_bytes)
        (staging / "checksums.json").write_bytes(checksum_bytes)
        (staging / "finance-delivery.digest").write_text(f"{digest}\n", encoding="ascii", newline="\n")
        return digest

    def _verify_seal(self, delivery: Path, expected_digest: str) -> tuple[str, int]:
        for path in delivery.rglob("*"):
            if path.is_symlink():
                raise FinanceDeliveryError("C2 packages cannot contain symbolic links")
        checksum_path = delivery / "checksums.json"
        digest_path = delivery / "finance-delivery.digest"
        if not checksum_path.is_file() or not digest_path.is_file():
            raise FinanceDeliveryError("C2 package seal is incomplete")
        checksum_bytes = checksum_path.read_bytes()
        digest = digest_path.read_text(encoding="ascii").strip()
        if digest != expected_digest or sha256_bytes(checksum_bytes) != digest:
            raise FinanceDeliveryError("C2 detached digest differs")
        checksums = _json(checksum_path)
        declared = checksums.get("files")
        if not isinstance(declared, list):
            raise FinanceDeliveryError("C2 checksum inventory is malformed")
        declared_paths = {str(row["path"]) for row in declared}
        physical = {
            path.relative_to(delivery).as_posix()
            for path in delivery.rglob("*")
            if path.is_file()
        }
        if physical != declared_paths | {"checksums.json", "finance-delivery.digest"}:
            raise FinanceDeliveryError("C2 physical inventory differs from its seal")
        for row in declared:
            payload = (delivery / str(row["path"])).read_bytes()
            if len(payload) != int(row["byte_count"]) or sha256_bytes(payload) != row["sha256"]:
                raise FinanceDeliveryError(f"C2 checksum differs for {row['path']}")
        return digest, len(declared)

    def build(self, request: FinanceDeliveryBuildRequest) -> FinanceDeliveryBuildResult:
        finance_model_path = request.finance_model_package_path.resolve()
        source_data_path = request.source_data_package_path.resolve()
        output = request.output_path.resolve()
        workbook_output = request.workbook_output_path.resolve()
        preview_output = request.preview_output_path.resolve()
        if output.exists() or workbook_output.exists() or preview_output.exists():
            raise FinanceDeliveryError("C2 outputs must not already exist")
        staging = output.parent / f".{output.name}.building"
        if staging.exists():
            raise FinanceDeliveryError("C2 staging path already exists")
        if output == finance_model_path or finance_model_path in output.parents:
            raise FinanceDeliveryError("C2 output cannot be inside the C1 authority")
        manifest, datasets, relationships, measures, lineage = self._verify_c1(
            finance_model_path,
            source_data_path,
            request.expected_finance_model_digest,
            request.expected_source_data_digest,
        )
        snapshots = self._snapshots(finance_model_path, manifest, datasets)
        catalogue, dictionary, relationship_rows, measure_rows, lineage_rows = self._metadata(
            snapshots, datasets, relationships, measures, lineage
        )
        controls = self._controls(snapshots)
        try:
            staging.mkdir(parents=True)
            react_count, powerbi_count, csv_count = self._write_physical(staging, snapshots)
            _write_json(staging / "metadata" / "table-catalogue.json", {"contract_version": "q-finance-c2-table-catalogue@v1", "rows": catalogue})
            _write_json(staging / "metadata" / "data-dictionary.json", {"contract_version": "q-finance-c2-data-dictionary@v1", "rows": dictionary})
            _write_json(staging / "metadata" / "lineage.json", {"contract_version": "q-finance-c2-lineage@v1", "rows": lineage_rows})
            _write_json(staging / "metadata" / "reconciliation.json", {"contract_version": "q-finance-c2-reconciliation@v1", "rows": controls})
            _write_json(staging / "powerbi" / "field-roles.json", {"contract_version": "q-finance-c2-field-roles@v1", "rows": dictionary})
            self._write_guidance(staging, catalogue, relationship_rows, measure_rows)
            workbook_input = self._workbook_input(request, manifest, catalogue, dictionary, relationship_rows, measure_rows, controls, snapshots)
            workbook_path = staging / "excel" / "finance-assurance-c1-data-pack.xlsx"
            workbook_result = self._run_workbook("build", workbook_input, workbook_path, preview_output)
            workbook_manifest = {
                "contract_version": "q-finance-c2-workbook-logical-manifest@v1",
                **workbook_result,
                "path": "excel/finance-assurance-c1-data-pack.xlsx",
                "sheet_inventory": ["Cover", "Table_Catalogue", "Control_Totals", "Data_Dictionary", "Relationships", "Measures", *[WORKBOOK_SHEETS[name] for name in WORKBOOK_SHEETS]],
            }
            _write_json(staging / "metadata" / "workbook-logical-manifest.json", workbook_manifest)
            mart_count = sum(snapshot.name.startswith("mart_") for snapshot in snapshots)
            mart_rows = sum(snapshot.row_count for snapshot in snapshots if snapshot.name.startswith("mart_"))
            delivered_rows = sum(snapshot.row_count for snapshot in snapshots)
            delivery_manifest = {
                "contract_version": DELIVERY_CONTRACT,
                "delivery_ref": DELIVERY_REF,
                "status": "PUBLISHED",
                "built_at": request.built_at,
                "producer_release": request.producer_release,
                "finance_model_ref": FINANCE_MODEL_REF,
                "finance_model_digest": request.expected_finance_model_digest,
                "model_semantic_digest": manifest["model_semantic_digest"],
                "source_data_ref": SOURCE_DATA_REF,
                "source_data_digest": request.expected_source_data_digest,
                "mart_count": mart_count,
                "conformed_dimension_count": len(CONFORMED_DIMENSIONS),
                "delivered_table_count": len(snapshots),
                "mart_row_count": mart_rows,
                "delivered_row_count": delivered_rows,
                "react_parquet_file_count": react_count,
                "powerbi_parquet_file_count": powerbi_count,
                "csv_file_count": csv_count,
                "powerbi_relationship_count": len(relationship_rows),
                "powerbi_executable_relationship_count": sum(row["endpoint_status"] == "DELIVERED_BOTH_ENDPOINTS" for row in relationship_rows),
                "powerbi_measure_count": len(measure_rows),
                "workbook_sheet_count": int(workbook_result["sheet_count"]),
                "workbook_data_sheet_count": int(workbook_result["data_sheet_count"]),
                "validation_control_count": len(controls),
                "tables": catalogue,
            }
            _write_json(staging / "delivery-manifest.json", delivery_manifest)
            (staging / "README.md").write_text(
                "# Q-FINANCE C2 governed analytical handoff\n\n"
                "This package materialises the exact C1 marts and required conformed dimensions for three consumers.\n\n"
                "- `react/`: year-partitioned Parquet and DuckDB starter SQL.\n"
                "- `csv/`: UTF-8/LF Excel-ready tables with `\\N` as the explicit null token.\n"
                "- `excel/`: a data-only governed inspection pack; it contains no forecast or valuation model.\n"
                "- `powerbi/`: one Parquet file per table plus relationships, field roles and measure specifications.\n"
                "- `metadata/`: grains, schemas, lineage, reconciliation and workbook logical evidence.\n\n"
                "All formats reconcile to the same C1 logical digests and exact A2.4 source package.\n",
                encoding="utf-8",
                newline="\n",
            )
            delivery_digest = self._seal(staging)
            self._verify_delivery(
                staging,
                finance_model_path,
                source_data_path,
                delivery_digest,
                request.expected_finance_model_digest,
                request.expected_source_data_digest,
                verify_workbook=True,
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging, output)
            workbook_output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output / "excel" / workbook_path.name, workbook_output)
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            if preview_output.exists() and not output.exists():
                shutil.rmtree(preview_output)
            raise
        return FinanceDeliveryBuildResult(
            contract_version="q-finance-c2-build-result@v1",
            status="PUBLISHED",
            delivery_ref=DELIVERY_REF,
            output_path=output,
            workbook_output_path=workbook_output,
            delivery_digest=delivery_digest,
            finance_model_digest=request.expected_finance_model_digest,
            model_semantic_digest=str(manifest["model_semantic_digest"]),
            source_data_digest=request.expected_source_data_digest,
            mart_count=mart_count,
            conformed_dimension_count=len(CONFORMED_DIMENSIONS),
            delivered_table_count=len(snapshots),
            mart_row_count=mart_rows,
            delivered_row_count=delivered_rows,
            react_parquet_file_count=react_count,
            powerbi_parquet_file_count=powerbi_count,
            csv_file_count=csv_count,
            powerbi_relationship_count=len(relationship_rows),
            powerbi_measure_count=len(measure_rows),
            workbook_sheet_count=int(workbook_result["sheet_count"]),
            workbook_data_sheet_count=int(workbook_result["data_sheet_count"]),
            validation_control_count=len(controls),
        )

    def _verify_delivery(
        self,
        delivery: Path,
        finance_model_path: Path,
        source_data_path: Path,
        expected_delivery_digest: str,
        expected_finance_model_digest: str,
        expected_source_data_digest: str,
        *,
        verify_workbook: bool,
    ) -> tuple[dict[str, Any], int, int]:
        digest, file_count = self._verify_seal(delivery, expected_delivery_digest)
        manifest, datasets, relationships, measures, lineage = self._verify_c1(
            finance_model_path, source_data_path, expected_finance_model_digest, expected_source_data_digest
        )
        delivery_manifest = _json(delivery / "delivery-manifest.json")
        if delivery_manifest.get("contract_version") != DELIVERY_CONTRACT or delivery_manifest.get("delivery_ref") != DELIVERY_REF:
            raise FinanceDeliveryError("C2 delivery manifest contract differs")
        if delivery_manifest.get("finance_model_digest") != expected_finance_model_digest or delivery_manifest.get("source_data_digest") != expected_source_data_digest:
            raise FinanceDeliveryError("C2 delivery source binding differs")
        if delivery_manifest.get("model_semantic_digest") != manifest.get("model_semantic_digest"):
            raise FinanceDeliveryError("C2 semantic source binding differs")
        snapshots = self._snapshots(finance_model_path, manifest, datasets)
        catalogue, dictionary, relationship_rows, measure_rows, lineage_rows = self._metadata(
            snapshots, datasets, relationships, measures, lineage
        )
        controls = self._controls(snapshots)
        expected_metadata = {
            "metadata/table-catalogue.json": {"contract_version": "q-finance-c2-table-catalogue@v1", "rows": catalogue},
            "metadata/data-dictionary.json": {"contract_version": "q-finance-c2-data-dictionary@v1", "rows": dictionary},
            "metadata/lineage.json": {"contract_version": "q-finance-c2-lineage@v1", "rows": lineage_rows},
            "metadata/reconciliation.json": {"contract_version": "q-finance-c2-reconciliation@v1", "rows": controls},
            "powerbi/field-roles.json": {"contract_version": "q-finance-c2-field-roles@v1", "rows": dictionary},
            "powerbi/relationships.json": {"contract_version": "q-finance-c2-powerbi-relationships@v1", "delivery_ref": DELIVERY_REF, "rows": relationship_rows},
            "powerbi/measures.json": {"contract_version": "q-finance-c2-powerbi-measures@v1", "delivery_ref": DELIVERY_REF, "rows": measure_rows},
        }
        for relative, expected in expected_metadata.items():
            if (delivery / relative).read_bytes() != canonical_json_bytes(expected):
                raise FinanceDeliveryError(f"C2 governed metadata differs: {relative}")
        for snapshot in snapshots:
            csv_replay = _csv_table(delivery / "csv" / f"{snapshot.name}.csv", snapshot.columns)
            csv_replay = _sort_arrow(csv_replay, snapshot.columns)
            if csv_replay.num_rows != snapshot.row_count or _logical_digest(csv_replay, snapshot.columns) != snapshot.logical_digest:
                raise FinanceDeliveryError(f"C2 CSV logical replay differs for {snapshot.name}")
            powerbi_replay = _sort_arrow(_parquet_table(delivery / "powerbi" / "parquet" / f"{snapshot.name}.parquet"), snapshot.columns)
            if powerbi_replay.column_names != snapshot.arrow.column_names or powerbi_replay.num_rows != snapshot.row_count or _logical_digest(powerbi_replay, snapshot.columns) != snapshot.logical_digest:
                raise FinanceDeliveryError(f"C2 Power BI Parquet logical replay differs for {snapshot.name}")
            react_files = sorted((delivery / "react" / "parquet" / snapshot.name).rglob("*.parquet"))
            if not react_files:
                raise FinanceDeliveryError(f"C2 React Parquet is missing for {snapshot.name}")
            react_replay = pa.concat_tables([_parquet_table(path) for path in react_files])
            react_replay = _sort_arrow(react_replay, snapshot.columns)
            if react_replay.column_names != snapshot.arrow.column_names or react_replay.num_rows != snapshot.row_count or _logical_digest(react_replay, snapshot.columns) != snapshot.logical_digest:
                raise FinanceDeliveryError(f"C2 React Parquet logical replay differs for {snapshot.name}")
        workbook_path = delivery / "excel" / "finance-assurance-c1-data-pack.xlsx"
        with zipfile.ZipFile(workbook_path) as archive:
            forbidden = (
                "xl/vbaProject.bin",
                "xl/connections.xml",
                "xl/model/",
                "xl/externalLinks/",
            )
            if any(any(name.startswith(prefix) for prefix in forbidden) for name in archive.namelist()):
                raise FinanceDeliveryError("C2 workbook contains a forbidden executable or external feature")
        if verify_workbook:
            workbook_input = self._workbook_input(None, manifest, catalogue, dictionary, relationship_rows, measure_rows, controls, snapshots, delivery_manifest)
            workbook_result = self._run_workbook("verify", workbook_input, workbook_path, None)
            recorded = _json(delivery / "metadata" / "workbook-logical-manifest.json")
            for key in ("workbook_sha256", "workbook_logical_digest", "sheet_count", "data_sheet_count", "checked_cell_count"):
                if recorded.get(key) != workbook_result.get(key):
                    raise FinanceDeliveryError(f"C2 workbook logical evidence differs: {key}")
        if digest != expected_delivery_digest:
            raise FinanceDeliveryError("C2 delivery digest changed during verification")
        return delivery_manifest, file_count, sum(snapshot.row_count for snapshot in snapshots)

    def verify(self, request: FinanceDeliveryVerifyRequest) -> FinanceDeliveryVerifyResult:
        delivery = request.delivery_path.resolve()
        delivery_manifest, file_count, row_count = self._verify_delivery(
            delivery,
            request.finance_model_package_path.resolve(),
            request.source_data_package_path.resolve(),
            request.expected_delivery_digest,
            request.expected_finance_model_digest,
            request.expected_source_data_digest,
            verify_workbook=True,
        )
        return FinanceDeliveryVerifyResult(
            contract_version="q-finance-c2-verify-result@v1",
            status="VERIFIED",
            delivery_ref=DELIVERY_REF,
            delivery_digest=request.expected_delivery_digest,
            finance_model_digest=request.expected_finance_model_digest,
            model_semantic_digest=str(delivery_manifest["model_semantic_digest"]),
            source_data_digest=request.expected_source_data_digest,
            checked_file_count=file_count,
            checked_table_count=int(delivery_manifest["delivered_table_count"]),
            checked_row_count=row_count,
            checked_reconciliation_count=int(delivery_manifest["validation_control_count"]),
            checked_workbook_sheet_count=int(delivery_manifest["workbook_sheet_count"]),
            canonical_bytes_status="VERIFIED",
            parquet_replay_status="VERIFIED",
            csv_replay_status="VERIFIED",
            workbook_replay_status="VERIFIED",
        )
