"""Ordered SQLite schema migrations for the durable runtime adapter."""

from __future__ import annotations

from dataclasses import dataclass
from sqlite3 import Connection


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    sql: str


MIGRATIONS = (
    Migration(
        version=1,
        name="initial_runtime_boundary",
        sql="""
        CREATE TABLE IF NOT EXISTS runtime_metadata (
            singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
            revision INTEGER NOT NULL CHECK (revision >= 0),
            codec_version TEXT NOT NULL,
            canonicalization_version TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS current_authoritative_state (
            singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
            payload BLOB NOT NULL,
            payload_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS baseline_projection (
            singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
            manifest_id TEXT NOT NULL UNIQUE,
            payload BLOB NOT NULL,
            payload_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS projection_checkpoint (
            singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
            revision INTEGER NOT NULL CHECK (revision >= 0),
            authoritative_state_hash TEXT NOT NULL,
            payload BLOB NOT NULL,
            payload_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS command_contexts (
            command_owner TEXT NOT NULL,
            command_id TEXT NOT NULL,
            input_digest TEXT NOT NULL,
            payload BLOB NOT NULL,
            payload_hash TEXT NOT NULL,
            PRIMARY KEY (command_owner, command_id),
            UNIQUE (command_id)
        );

        CREATE TABLE IF NOT EXISTS authoritative_records (
            record_family TEXT NOT NULL,
            record_identity TEXT NOT NULL,
            semantic_hash TEXT NOT NULL,
            payload BLOB NOT NULL,
            command_id TEXT,
            record_ordinal INTEGER NOT NULL CHECK (record_ordinal >= 0),
            PRIMARY KEY (record_family, record_identity)
        );

        CREATE TABLE IF NOT EXISTS effect_claims (
            idempotency_key TEXT PRIMARY KEY,
            command_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            semantic_hash TEXT NOT NULL,
            payload BLOB NOT NULL
        );

        CREATE TABLE IF NOT EXISTS admission_registry (
            admission_mode TEXT NOT NULL,
            admission_id TEXT NOT NULL,
            input_digest TEXT NOT NULL,
            committed_revision INTEGER NOT NULL,
            PRIMARY KEY (admission_mode, admission_id)
        );
        """,
    ),
    Migration(
        version=2,
        name="sealed_admission_projections",
        sql="""
        CREATE TABLE IF NOT EXISTS admission_projections (
            admission_mode TEXT NOT NULL,
            admission_id TEXT NOT NULL,
            projection_family TEXT NOT NULL,
            projection_token TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            payload BLOB NOT NULL,
            PRIMARY KEY (
                admission_mode,
                admission_id,
                projection_family,
                projection_token
            )
        );
        """,
    ),
    Migration(
        version=3,
        name="bind_baseline_projection_to_authority",
        sql="""
        ALTER TABLE baseline_projection
            ADD COLUMN source_record_family TEXT;
        ALTER TABLE baseline_projection
            ADD COLUMN source_record_identity TEXT;
        """,
    ),
    Migration(
        version=4,
        name="semantic_record_availability",
        sql="""
        ALTER TABLE authoritative_records
            ADD COLUMN available_from TEXT;
        ALTER TABLE effect_claims
            ADD COLUMN available_from TEXT;
        """,
    ),
)

LATEST_SCHEMA_VERSION = MIGRATIONS[-1].version


def apply_migrations(connection: Connection) -> None:
    """Apply every pending migration atomically and in numeric order."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    applied = {
        int(row[0])
        for row in connection.execute("SELECT version FROM schema_migrations")
    }
    for migration in MIGRATIONS:
        if migration.version in applied:
            continue
        connection.execute("BEGIN IMMEDIATE")
        try:
            for statement in migration.sql.split(";"):
                if statement.strip():
                    connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations(version, name) VALUES (?, ?)",
                (migration.version, migration.name),
            )
            connection.commit()
        except BaseException:
            connection.rollback()
            raise


def schema_version(connection: Connection) -> int:
    row = connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
    return int(row[0] or 0)
