"""Lossless DuckDB Bronze ingestion for generated finance sources."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import duckdb

from finance_assurance.finance_data.definitions import ALL_SOURCE_DATASETS

BRONZE_SCHEMA = "bronze"
META_SCHEMA = "bronze_meta"
DATABASE_RELATIVE_PATH = "warehouse/atlas-finance.duckdb"
BRONZE_METADATA_COLUMNS = (
    "_source_row_hash",
    "_ingested_at",
    "_source_file",
    "_source_file_sha256",
    "_source_data_ref",
)


@dataclass(frozen=True)
class BronzeTableResult:
    source_path: str
    table_name: str
    source_sha256: str
    row_count: int
    source_columns: tuple[str, ...]


@dataclass(frozen=True)
class BronzeBuildResult:
    database_path: Path
    database_sha256: str
    database_byte_count: int
    tables: tuple[BronzeTableResult, ...]


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _table_name(source_path: str) -> str:
    value = source_path.removesuffix(".csv").replace("/", "__")
    value = re.sub(r"[^0-9A-Za-z_]+", "_", value).lower()
    value = re.sub(r"_+", "_", value.replace("__", "_namespace_"))
    value = value.replace("_namespace_", "__").strip("_")
    if not value or value[0].isdigit():
        value = f"source_{value}"
    return value


def _csv_header(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        header = next(reader, None)
    if not header or any(not item for item in header):
        raise ValueError(f"source CSV has an invalid header: {path}")
    if len(header) != len(set(header)):
        raise ValueError(f"source CSV has duplicate columns: {path}")
    collision = sorted(set(header).intersection(BRONZE_METADATA_COLUMNS))
    if collision:
        raise ValueError(f"source CSV uses reserved Bronze columns: {collision}")
    return tuple(header)


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _row_hash_expression(columns: tuple[str, ...]) -> str:
    values = ", ".join(
        f"COALESCE(CAST({_quote_identifier(item)} AS VARCHAR), '<NULL>')"
        for item in columns
    )
    return f"'sha256:' || sha256(to_json(list_value({values})))"


def _read_csv_expression(path: Path, columns: tuple[str, ...]) -> str:
    column_map = ", ".join(
        f"{_sql_text(column)}: 'VARCHAR'" for column in columns
    )
    return (
        "read_csv("
        f"{_sql_text(path.as_posix())}, "
        "header = true, "
        f"columns = {{{column_map}}}, "
        "nullstr = '<ATLAS_NULL_NOT_USED>', "
        "strict_mode = true, "
        "parallel = true"
        ")"
    )


def _initialise(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(f"CREATE SCHEMA {_quote_identifier(BRONZE_SCHEMA)}")
    connection.execute(f"CREATE SCHEMA {_quote_identifier(META_SCHEMA)}")
    connection.execute(
        f"""
        CREATE TABLE {_quote_identifier(META_SCHEMA)}.source_files (
            source_path VARCHAR NOT NULL,
            source_sha256 VARCHAR NOT NULL,
            table_name VARCHAR NOT NULL,
            row_count BIGINT NOT NULL,
            source_column_count BIGINT NOT NULL
        )
        """
    )
    connection.execute(
        f"""
        CREATE TABLE {_quote_identifier(META_SCHEMA)}.load_context (
            source_data_ref VARCHAR NOT NULL,
            ingested_at VARCHAR NOT NULL,
            loader_contract VARCHAR NOT NULL,
            source_format VARCHAR NOT NULL,
            money_contract VARCHAR NOT NULL
        )
        """
    )


def build_bronze_database(
    *,
    raw_root: Path,
    database_path: Path,
    source_data_ref: str,
    ingested_at: str,
) -> BronzeBuildResult:
    """Build one closed Bronze database directly from raw CSV bytes."""

    if database_path.exists():
        raise FileExistsError(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[BronzeTableResult] = []
    with duckdb.connect(str(database_path)) as connection:
        _initialise(connection)
        connection.execute(
            f"INSERT INTO {_quote_identifier(META_SCHEMA)}.load_context "
            "VALUES (?, ?, ?, ?, ?)",
            [
                source_data_ref,
                ingested_at,
                "ATLAS-BRONZE-LOSSLESS@v1",
                "CSV_UTF8_LF",
                "INTEGER_MINOR_UNITS_PLUS_CURRENCY",
            ],
        )
        for definition in ALL_SOURCE_DATASETS:
            source_path = raw_root / definition.path
            columns = _csv_header(source_path)
            if columns != definition.columns:
                raise ValueError(f"source header differs from contract: {definition.path}")
            table_name = _table_name(definition.path)
            file_hash = _file_sha256(source_path)
            select_columns = ", ".join(_quote_identifier(item) for item in columns)
            row_hash = _row_hash_expression(columns)
            source_reader = _read_csv_expression(source_path, columns)
            qualified_table = (
                f"{_quote_identifier(BRONZE_SCHEMA)}."
                f"{_quote_identifier(table_name)}"
            )
            connection.execute(
                f"""
                CREATE TABLE {qualified_table} AS
                SELECT
                    {select_columns},
                    {row_hash} AS _source_row_hash,
                    {_sql_text(ingested_at)} AS _ingested_at,
                    {_sql_text(definition.path)} AS _source_file,
                    {_sql_text(file_hash)} AS _source_file_sha256,
                    {_sql_text(source_data_ref)} AS _source_data_ref
                FROM {source_reader}
                """
            )
            row_count = connection.execute(
                f"SELECT COUNT(*) FROM {_quote_identifier(BRONZE_SCHEMA)}."
                f"{_quote_identifier(table_name)}"
            ).fetchone()[0]
            connection.execute(
                f"INSERT INTO {_quote_identifier(META_SCHEMA)}.source_files "
                "VALUES (?, ?, ?, ?, ?)",
                [definition.path, file_hash, table_name, row_count, len(columns)],
            )
            results.append(
                BronzeTableResult(
                    source_path=definition.path,
                    table_name=table_name,
                    source_sha256=file_hash,
                    row_count=row_count,
                    source_columns=columns,
                )
            )
        connection.execute("CHECKPOINT")
    return BronzeBuildResult(
        database_path=database_path,
        database_sha256=database_file_sha256(database_path),
        database_byte_count=database_path.stat().st_size,
        tables=tuple(results),
    )


def verify_bronze_database(
    *,
    raw_root: Path,
    database_path: Path,
    source_data_ref: str,
    expected_tables: tuple[BronzeTableResult, ...],
) -> None:
    """Verify Bronze closure, source binding, row parity and metadata."""

    if not database_path.is_file():
        raise FileNotFoundError(database_path)
    expected_by_name = {item.table_name: item for item in expected_tables}
    with duckdb.connect(str(database_path), read_only=True) as connection:
        schemas = {
            row[0]
            for row in connection.execute(
                "SELECT schema_name FROM information_schema.schemata"
            ).fetchall()
        }
        if not {BRONZE_SCHEMA, META_SCHEMA}.issubset(schemas):
            raise ValueError("Bronze database schemas are incomplete")
        actual_tables = {
            row[0]
            for row in connection.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = ? ORDER BY table_name",
                [BRONZE_SCHEMA],
            ).fetchall()
        }
        if actual_tables != set(expected_by_name):
            raise ValueError("Bronze source-table inventory differs")
        context = connection.execute(
            f"SELECT * FROM {_quote_identifier(META_SCHEMA)}.load_context"
        ).fetchall()
        if len(context) != 1 or context[0][0] != source_data_ref:
            raise ValueError("Bronze load context differs")
        for table_name, expected in expected_by_name.items():
            source_path = raw_root / expected.source_path
            if _file_sha256(source_path) != expected.source_sha256:
                raise ValueError(f"Bronze source file hash differs: {expected.source_path}")
            actual_count = connection.execute(
                f"SELECT COUNT(*) FROM {_quote_identifier(BRONZE_SCHEMA)}."
                f"{_quote_identifier(table_name)}"
            ).fetchone()[0]
            if actual_count != expected.row_count:
                raise ValueError(f"Bronze row count differs: {expected.source_path}")
            metadata = connection.execute(
                f"SELECT COUNT(DISTINCT _source_file), "
                f"MIN(_source_file), MIN(_source_file_sha256), "
                f"MIN(_source_data_ref), COUNT_IF(_source_row_hash IS NULL) "
                f"FROM {_quote_identifier(BRONZE_SCHEMA)}."
                f"{_quote_identifier(table_name)}"
            ).fetchone()
            if expected.row_count == 0:
                continue
            if metadata != (
                1,
                expected.source_path,
                expected.source_sha256,
                source_data_ref,
                0,
            ):
                raise ValueError(f"Bronze metadata differs: {expected.source_path}")


def database_file_sha256(path: Path) -> str:
    """Return the same-build database SHA-256."""

    digest = sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"
