"""Strict non-canonical DuckDB cache writer and verifier for Artifact R3."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import duckdb
import pyarrow.parquet as pq

from finance_assurance.digestion.contracts import (
    DatasetCoordinate,
    DuckDBCacheTableBinding,
    ModelManifest,
    NoncanonicalCacheManifest,
    ProfileCoordinate,
)
from finance_assurance.exports.serialization import canonical_json_bytes, sha256_bytes

DUCKDB_CACHE_CONTRACT = "duckdb-cache-manifest@v1"
DUCKDB_ENGINE_VERSION = "1.5.5"
DUCKDB_STORAGE_COMPATIBILITY_VERSION = "v1.5.0"
DUCKDB_DATABASE_STORAGE_VERSION = "v1.5.0+"
DUCKDB_DATABASE_PATH = "warehouse/finance-assurance.duckdb"
DUCKDB_CACHE_MANIFEST_PATH = "noncanonical-cache.json"
DUCKDB_SCHEMAS = ("p_evidence_v1", "q_analytics_v1", "model_meta")
DUCKDB_METADATA_TABLES = ("cache_profile", "documents", "table_bindings")


def validate_duckdb_runtime() -> None:
    """Fail closed unless the exact R3 engine runtime is installed."""

    if duckdb.__version__ != DUCKDB_ENGINE_VERSION:
        raise ValueError(
            f"DuckDB {DUCKDB_ENGINE_VERSION} is required, found {duckdb.__version__}"
        )


def duckdb_schema(registry_id: str) -> str:
    return {
        "P-EVIDENCE": "p_evidence_v1",
        "Q-ANALYTICS": "q_analytics_v1",
    }[registry_id]


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _qualified(schema: str, table: str) -> str:
    return f"{_quote_identifier(schema)}.{_quote_identifier(table)}"


def _storage_version(connection: duckdb.DuckDBPyConnection) -> str:
    rows = connection.execute(
        "SELECT tags['storage_version'] FROM duckdb_databases() "
        "WHERE internal = false AND type = 'duckdb'"
    ).fetchall()
    if rows != [(DUCKDB_DATABASE_STORAGE_VERSION,)]:
        raise ValueError("DuckDB database storage version differs from R3")
    return cast(str, rows[0][0])


def _document_rows(root: Path) -> tuple[tuple[str, str, str], ...]:
    rows = []
    for name in ("model-manifest.json", "relationships.json", "semantic-model.json"):
        payload = (root / name).read_bytes()
        rows.append((name, sha256_bytes(payload), payload.decode("ascii")))
    return tuple(rows)


def _binding_rows(manifest: ModelManifest) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            entry.source_registry_id,
            entry.source_dataset_id,
            entry.duckdb_schema,
            entry.duckdb_object,
            entry.parquet_path,
            entry.parquet_hash,
            entry.row_count,
            entry.logical_table_digest,
            entry.technical_projection_digest,
        )
        for entry in manifest.table_entries
    )


def _create_metadata_tables(
    connection: duckdb.DuckDBPyConnection,
    root: Path,
    manifest: ModelManifest,
    database_storage_version: str,
) -> None:
    connection.execute(
        """
        CREATE TABLE model_meta.cache_profile (
            cache_contract_version VARCHAR NOT NULL,
            engine_version VARCHAR NOT NULL,
            storage_compatibility_version VARCHAR NOT NULL,
            database_storage_version VARCHAR NOT NULL,
            read_only_consumer_required BOOLEAN NOT NULL
        )
        """
    )
    connection.execute(
        "INSERT INTO model_meta.cache_profile VALUES (?, ?, ?, ?, ?)",
        (
            DUCKDB_CACHE_CONTRACT,
            DUCKDB_ENGINE_VERSION,
            DUCKDB_STORAGE_COMPATIBILITY_VERSION,
            database_storage_version,
            True,
        ),
    )
    connection.execute(
        """
        CREATE TABLE model_meta.documents (
            document_name VARCHAR NOT NULL,
            document_sha256 VARCHAR NOT NULL,
            canonical_json VARCHAR NOT NULL
        )
        """
    )
    connection.executemany(
        "INSERT INTO model_meta.documents VALUES (?, ?, ?)",
        _document_rows(root),
    )
    connection.execute(
        """
        CREATE TABLE model_meta.table_bindings (
            source_registry_id VARCHAR NOT NULL,
            source_dataset_id VARCHAR NOT NULL,
            duckdb_schema VARCHAR NOT NULL,
            duckdb_object VARCHAR NOT NULL,
            parquet_path VARCHAR NOT NULL,
            parquet_hash VARCHAR NOT NULL,
            row_count BIGINT NOT NULL,
            logical_table_digest VARCHAR NOT NULL,
            technical_projection_digest VARCHAR NOT NULL
        )
        """
    )
    connection.executemany(
        "INSERT INTO model_meta.table_bindings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        _binding_rows(manifest),
    )


def build_duckdb_cache(
    root: Path, manifest: ModelManifest
) -> NoncanonicalCacheManifest:
    """Build the R3 cache solely from the package's canonical Parquet tables."""

    validate_duckdb_runtime()
    database_path = root / DUCKDB_DATABASE_PATH
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(
        str(database_path),
        config={
            "storage_compatibility_version": DUCKDB_STORAGE_COMPATIBILITY_VERSION,
            "threads": "1",
        },
    )
    cache_entries: list[DuckDBCacheTableBinding] = []
    try:
        database_storage_version = _storage_version(connection)
        for schema in DUCKDB_SCHEMAS:
            connection.execute(f"CREATE SCHEMA {_quote_identifier(schema)}")
        for entry in manifest.table_entries:
            if (
                entry.parquet_path is None
                or entry.parquet_hash is None
                or entry.duckdb_schema is None
                or entry.duckdb_object is None
            ):
                raise ValueError("DuckDB cache requires complete Parquet bindings")
            parquet_path = root / entry.parquet_path
            qualified = _qualified(entry.duckdb_schema, entry.duckdb_object)
            connection.execute(
                f"CREATE TABLE {qualified} AS "
                "SELECT * FROM read_parquet(?) ORDER BY row_key",
                (str(parquet_path),),
            )
            table = pq.read_table(parquet_path)
            cache_entries.append(
                DuckDBCacheTableBinding(
                    source_coordinate=DatasetCoordinate(
                        registry_id=entry.source_registry_id,
                        registry_version=entry.source_registry_version,
                        dataset_id=entry.source_dataset_id,
                        dataset_version=entry.source_dataset_version,
                    ),
                    duckdb_schema=entry.duckdb_schema,
                    duckdb_object=entry.duckdb_object,
                    parquet_path=entry.parquet_path,
                    parquet_hash=entry.parquet_hash,
                    row_count=entry.row_count,
                    column_names=tuple(table.column_names),
                    logical_table_digest=entry.logical_table_digest,
                    technical_projection_digest=entry.technical_projection_digest,
                )
            )
        _create_metadata_tables(connection, root, manifest, database_storage_version)
        connection.execute("CHECKPOINT")
    finally:
        connection.close()
    wal_path = database_path.with_name(database_path.name + ".wal")
    if wal_path.exists():
        raise ValueError("DuckDB cache retained a WAL sidecar after checkpoint")
    database_bytes = database_path.read_bytes()
    cache_manifest = NoncanonicalCacheManifest(
        cache_contract_version=DUCKDB_CACHE_CONTRACT,
        model_ref=manifest.model_ref,
        source_package_digest=manifest.source_package_digest,
        profile_coordinate=ProfileCoordinate(
            profile_id=manifest.profile_id,
            profile_version=manifest.profile_version,
        ),
        database_path=DUCKDB_DATABASE_PATH,
        database_sha256=sha256_bytes(database_bytes),
        database_byte_count=len(database_bytes),
        engine="DUCKDB",
        engine_version=DUCKDB_ENGINE_VERSION,
        storage_compatibility_version=DUCKDB_STORAGE_COMPATIBILITY_VERSION,
        database_storage_version=DUCKDB_DATABASE_STORAGE_VERSION,
        build_source_format="PARQUET",
        schema_names=DUCKDB_SCHEMAS,
        metadata_table_names=DUCKDB_METADATA_TABLES,
        table_entries=tuple(cache_entries),
        read_only_consumer_required=True,
    )
    (root / DUCKDB_CACHE_MANIFEST_PATH).write_bytes(
        canonical_json_bytes(cache_manifest.model_dump(mode="json"))
    )
    return cache_manifest


def read_duckdb_cache_manifest(path: Path) -> NoncanonicalCacheManifest:
    payload = path.read_bytes()
    manifest = NoncanonicalCacheManifest.model_validate_json(payload)
    if canonical_json_bytes(manifest.model_dump(mode="json")) != payload:
        raise ValueError("noncanonical-cache.json is not canonical")
    return manifest


def _expected_table_inventory(
    manifest: ModelManifest,
) -> set[tuple[str, str]]:
    return {
        (cast(str, entry.duckdb_schema), cast(str, entry.duckdb_object))
        for entry in manifest.table_entries
    } | {("model_meta", name) for name in DUCKDB_METADATA_TABLES}


def verify_duckdb_cache(root: Path, manifest: ModelManifest) -> int:
    """Verify cache bytes, objects, metadata, and Parquet logical equivalence."""

    validate_duckdb_runtime()
    if manifest.noncanonical_cache_manifest_path != DUCKDB_CACHE_MANIFEST_PATH:
        raise ValueError("DuckDB cache manifest coordinate differs")
    cache = read_duckdb_cache_manifest(root / DUCKDB_CACHE_MANIFEST_PATH)
    if (
        cache.model_ref != manifest.model_ref
        or cache.source_package_digest != manifest.source_package_digest
        or cache.profile_coordinate.profile_id != manifest.profile_id
        or cache.profile_coordinate.profile_version != manifest.profile_version
    ):
        raise ValueError("DuckDB cache source binding differs")
    database_path = root / cache.database_path
    database_bytes = database_path.read_bytes()
    if (
        cache.database_sha256 != sha256_bytes(database_bytes)
        or cache.database_byte_count != len(database_bytes)
    ):
        raise ValueError("DuckDB cache file binding differs")
    expected_entries = {
        (entry.source_registry_id, entry.source_dataset_id): entry
        for entry in manifest.table_entries
    }
    cache_entries = {
        (entry.source_coordinate.registry_id, entry.source_coordinate.dataset_id): entry
        for entry in cache.table_entries
    }
    if set(cache_entries) != set(expected_entries):
        raise ValueError("DuckDB cache table inventory differs")
    if tuple(cache_entries) != tuple(expected_entries):
        raise ValueError("DuckDB cache table order differs")
    for coordinate, entry in expected_entries.items():
        cache_entry = cache_entries[coordinate]
        if (
            cache_entry.source_coordinate.registry_version
            != entry.source_registry_version
            or cache_entry.source_coordinate.dataset_version
            != entry.source_dataset_version
            or cache_entry.duckdb_schema != entry.duckdb_schema
            or cache_entry.duckdb_object != entry.duckdb_object
            or cache_entry.parquet_path != entry.parquet_path
            or cache_entry.parquet_hash != entry.parquet_hash
            or cache_entry.row_count != entry.row_count
            or cache_entry.logical_table_digest != entry.logical_table_digest
            or cache_entry.technical_projection_digest
            != entry.technical_projection_digest
        ):
            raise ValueError("DuckDB cache table binding differs")
    connection = duckdb.connect(str(database_path), read_only=True)
    try:
        _storage_version(connection)
        database_rows = connection.execute(
            "SELECT readonly FROM duckdb_databases() "
            "WHERE internal = false AND type = 'duckdb'"
        ).fetchall()
        if database_rows != [(True,)]:
            raise ValueError("DuckDB verifier did not open the cache read-only")
        actual_schemas = tuple(
            row[0]
            for row in connection.execute(
                "SELECT schema_name FROM duckdb_schemas() "
                "WHERE internal = false ORDER BY schema_name"
            ).fetchall()
        )
        if actual_schemas != tuple(sorted(DUCKDB_SCHEMAS)):
            raise ValueError("DuckDB schema inventory differs")
        actual_tables = set(
            connection.execute(
                "SELECT schema_name, table_name FROM duckdb_tables() "
                "WHERE internal = false"
            ).fetchall()
        )
        if actual_tables != _expected_table_inventory(manifest):
            raise ValueError("DuckDB object inventory differs")
        actual_views = connection.execute(
            "SELECT schema_name, view_name FROM duckdb_views() WHERE internal = false"
        ).fetchall()
        if actual_views:
            raise ValueError("DuckDB cache contains unregistered views")
        actual_macros = connection.execute(
            "SELECT schema_name, function_name FROM duckdb_functions() "
            "WHERE internal = false AND function_type = 'macro'"
        ).fetchall()
        if actual_macros:
            raise ValueError("DuckDB cache contains unregistered macros")
        actual_indexes = connection.execute(
            "SELECT schema_name, index_name FROM duckdb_indexes()"
        ).fetchall()
        if actual_indexes:
            raise ValueError("DuckDB cache contains unregistered indexes")
        for cache_entry in cache.table_entries:
            qualified = _qualified(
                cache_entry.duckdb_schema, cache_entry.duckdb_object
            )
            cursor = connection.execute(f"SELECT * FROM {qualified} LIMIT 0")
            actual_names = tuple(item[0] for item in cursor.description)
            expected = pq.read_table(root / cache_entry.parquet_path)
            parquet_path = str(root / cache_entry.parquet_path)
            difference_count = connection.execute(
                f"SELECT count(*) FROM ("
                f"(SELECT * FROM {qualified} EXCEPT ALL SELECT * FROM read_parquet(?)) "
                "UNION ALL "
                f"(SELECT * FROM read_parquet(?) EXCEPT ALL SELECT * FROM {qualified})"
                ")",
                (parquet_path, parquet_path),
            ).fetchone()
            actual_count = connection.execute(
                f"SELECT count(*) FROM {qualified}"
            ).fetchone()
            if (
                actual_names != cache_entry.column_names
                or tuple(expected.column_names) != cache_entry.column_names
                or difference_count != (0,)
                or actual_count != (cache_entry.row_count,)
            ):
                raise ValueError("DuckDB logical table differs from Parquet")
        profile_rows = connection.execute(
            "SELECT * FROM model_meta.cache_profile"
        ).fetchall()
        if profile_rows != [
            (
                DUCKDB_CACHE_CONTRACT,
                DUCKDB_ENGINE_VERSION,
                DUCKDB_STORAGE_COMPATIBILITY_VERSION,
                DUCKDB_DATABASE_STORAGE_VERSION,
                True,
            )
        ]:
            raise ValueError("DuckDB cache profile metadata differs")
        if connection.execute(
            "SELECT document_name, document_sha256, canonical_json "
            "FROM model_meta.documents ORDER BY document_name"
        ).fetchall() != sorted(_document_rows(root)):
            raise ValueError("DuckDB embedded documents differ")
        if connection.execute(
            "SELECT * FROM model_meta.table_bindings "
            "ORDER BY source_registry_id, source_dataset_id"
        ).fetchall() != sorted(_binding_rows(manifest)):
            raise ValueError("DuckDB embedded table bindings differ")
    finally:
        connection.close()
    return 2
