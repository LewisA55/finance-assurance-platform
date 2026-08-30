"""Build and independently verify governed Q-FINANCE model profiles."""


from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

import duckdb

from finance_assurance.exports.serialization import (
    canonical_json_bytes,
    sha256_bytes,
)

B1_REGISTRY_TABLES = (
    "q_finance_dataset_registry",
    "q_finance_relationship_registry",
    "q_finance_measure_registry",
    "q_finance_lineage_registry",
)
C1_REGISTRY_TABLES = (
    "q_finance_v5_dataset_registry",
    "q_finance_v5_relationship_registry",
    "q_finance_v5_measure_registry",
    "q_finance_v5_lineage_registry",
)
B4_REGISTRY_TABLES = (
    "q_finance_v4_dataset_registry",
    "q_finance_v4_relationship_registry",
    "q_finance_v4_measure_registry",
    "q_finance_v4_lineage_registry",
)
B3_REGISTRY_TABLES = (
    "q_finance_v3_dataset_registry",
    "q_finance_v3_relationship_registry",
    "q_finance_v3_measure_registry",
    "q_finance_v3_lineage_registry",
)
B2_REGISTRY_TABLES = (
    "q_finance_v2_dataset_registry",
    "q_finance_v2_relationship_registry",
    "q_finance_v2_measure_registry",
    "q_finance_v2_lineage_registry",
)


@dataclass(frozen=True)
class FinanceModelProfile:
    """Closed executable expectations for one Slice B model reference."""

    model_ref: str
    slice_name: str
    registry_tables: tuple[str, ...]
    dataset_registry: str
    silver_model_count: int
    gold_dataset_count: int
    governance_model_count: int
    dbt_test_count: int


MODEL_PROFILES = {
    "Q-FINANCE-B1@v1": FinanceModelProfile(
        model_ref="Q-FINANCE-B1@v1",
        slice_name="B1",
        registry_tables=B1_REGISTRY_TABLES,
        dataset_registry="q_finance_dataset_registry",
        silver_model_count=13,
        gold_dataset_count=15,
        governance_model_count=4,
        dbt_test_count=71,
    ),
    "Q-FINANCE-B2@v1": FinanceModelProfile(
        model_ref="Q-FINANCE-B2@v1",
        slice_name="B2",
        registry_tables=B2_REGISTRY_TABLES,
        dataset_registry="q_finance_v2_dataset_registry",
        silver_model_count=38,
        gold_dataset_count=42,
        governance_model_count=8,
        dbt_test_count=175,
    ),
    "Q-FINANCE-B3@v1": FinanceModelProfile(
        model_ref="Q-FINANCE-B3@v1",
        slice_name="B3",
        registry_tables=B3_REGISTRY_TABLES,
        dataset_registry="q_finance_v3_dataset_registry",
        silver_model_count=64,
        gold_dataset_count=72,
        governance_model_count=12,
        dbt_test_count=289,
    ),
    "Q-FINANCE-B4@v1": FinanceModelProfile(
        model_ref="Q-FINANCE-B4@v1",
        slice_name="B4",
        registry_tables=B4_REGISTRY_TABLES,
        dataset_registry="q_finance_v4_dataset_registry",
        silver_model_count=70,
        gold_dataset_count=78,
        governance_model_count=16,
        dbt_test_count=327,
    ),
    "Q-FINANCE-C1@v1": FinanceModelProfile(
        model_ref="Q-FINANCE-C1@v1",
        slice_name="C1",
        registry_tables=C1_REGISTRY_TABLES,
        dataset_registry="q_finance_v5_dataset_registry",
        silver_model_count=70,
        gold_dataset_count=99,
        governance_model_count=20,
        dbt_test_count=387,
    ),
}


def _profile_for_ref(model_ref: str) -> FinanceModelProfile:
    try:
        return MODEL_PROFILES[model_ref]
    except KeyError as error:
        raise FinanceModelError(f"unsupported finance-model reference: {model_ref}") from error
SEMANTIC_CONTROL_QUERIES = (
    (
        "GOLD_POPULATION_RECONCILES_TO_SILVER",
        """
        WITH populations AS (
            SELECT (SELECT COUNT(*) FROM gold.dim_period) actual_rows,
                   (SELECT COUNT(*) FROM silver.stg_reference__periods) expected_rows
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_legal_entity),
                             (SELECT COUNT(*) FROM silver.stg_reference__legal_entities)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_reporting_scope),
                             (SELECT COUNT(*) + 1 FROM silver.stg_reference__legal_entities)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_gl_account),
                             (SELECT COUNT(*) FROM silver.stg_accounting__chart_of_accounts)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_reporting_version),
                             (SELECT COUNT(*) FROM silver.stg_accounting__monthly_close_status)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_business_events),
                             (SELECT COUNT(*) FROM silver.stg_events__business_events)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_accounting_events),
                             (SELECT COUNT(*) FROM silver.stg_accounting__accounting_events)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_gl_journal_lines),
                             (SELECT COUNT(*) FROM silver.stg_accounting__source_gl_journal_lines)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_elimination_journal_lines),
                             (SELECT COUNT(*) FROM silver.stg_consolidation__elimination_journal_lines)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_statutory_trial_balance),
                             (SELECT COUNT(*) FROM silver.stg_accounting__statutory_trial_balance)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_statutory_statement_lines),
                             (SELECT COUNT(*) FROM silver.stg_accounting__statutory_statement_lines)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_retained_earnings_bridge),
                             (SELECT COUNT(*) FROM silver.stg_accounting__retained_earnings_bridge)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_cash_flow_reconciliation),
                             (SELECT COUNT(*) FROM silver.stg_accounting__cash_flow_reconciliation)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_monthly_close_status),
                             (SELECT COUNT(*) FROM silver.stg_accounting__monthly_close_status)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_statutory_reconciliations),
                             (SELECT COUNT(*) FROM silver.stg_governance__statutory_reconciliation_results)
        )
        SELECT COUNT(*) FROM populations WHERE actual_rows <> expected_rows
        """,
    ),
    (
        "GOLD_MONEY_IS_INTEGER_MINOR_UNITS",
        """
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_schema = 'gold'
          AND column_name LIKE '%_minor'
          AND data_type <> 'BIGINT'
        """,
    ),
    (
        "SOURCE_JOURNALS_BALANCE",
        """
        SELECT COUNT(*) FROM (
            SELECT source_journal_id, legal_entity_id, currency
            FROM gold.fct_gl_journal_lines
            GROUP BY 1, 2, 3
            HAVING SUM(debit_minor) <> SUM(credit_minor)
        )
        """,
    ),
    (
        "SOURCE_JOURNALS_RESOLVE_TO_BUSINESS_EVENTS",
        """
        SELECT COUNT(*) FROM gold.fct_gl_journal_lines
        WHERE event_type IS NULL OR source_system IS NULL
           OR business_event_semantic_hash IS NULL
        """,
    ),
    (
        "ENTITY_TRIAL_BALANCE_REPLAYS_GL",
        """
        WITH gl AS (
            SELECT period_id, legal_entity_id, account_id, currency,
                   SUM(debit_minor) debit_minor, SUM(credit_minor) credit_minor
            FROM gold.fct_gl_journal_lines GROUP BY 1, 2, 3, 4
        )
        SELECT COUNT(*)
        FROM gold.fct_statutory_trial_balance tb
        LEFT JOIN gl USING (period_id, legal_entity_id, account_id, currency)
        WHERE tb.scope_id <> 'NEXUS-GROUP'
          AND (tb.debit_activity_minor <> COALESCE(gl.debit_minor, 0)
            OR tb.credit_activity_minor <> COALESCE(gl.credit_minor, 0)
            OR tb.elimination_debit_minor <> 0
            OR tb.elimination_credit_minor <> 0)
        """,
    ),
    (
        "GROUP_TRIAL_BALANCE_REPLAYS_ENTITIES_AND_ELIMINATIONS",
        """
        WITH entity_activity AS (
            SELECT period_id, account_id, currency,
                   SUM(debit_activity_minor) debit_minor,
                   SUM(credit_activity_minor) credit_minor
            FROM gold.fct_statutory_trial_balance
            WHERE scope_id <> 'NEXUS-GROUP' GROUP BY 1, 2, 3
        ), elimination AS (
            SELECT period_id, account_id, currency,
                   SUM(debit_minor) debit_minor, SUM(credit_minor) credit_minor
            FROM gold.fct_elimination_journal_lines GROUP BY 1, 2, 3
        )
        SELECT COUNT(*)
        FROM gold.fct_statutory_trial_balance group_tb
        LEFT JOIN entity_activity USING (period_id, account_id, currency)
        LEFT JOIN elimination USING (period_id, account_id, currency)
        WHERE group_tb.scope_id = 'NEXUS-GROUP'
          AND (group_tb.debit_activity_minor <> COALESCE(entity_activity.debit_minor, 0)
            OR group_tb.credit_activity_minor <> COALESCE(entity_activity.credit_minor, 0)
            OR group_tb.elimination_debit_minor <> COALESCE(elimination.debit_minor, 0)
            OR group_tb.elimination_credit_minor <> COALESCE(elimination.credit_minor, 0))
        """,
    ),
    (
        "TRIAL_BALANCE_ROLLFORWARD",
        """
        SELECT COUNT(*) FROM gold.fct_statutory_trial_balance
        WHERE opening_balance_minor + debit_activity_minor - credit_activity_minor
              + elimination_debit_minor - elimination_credit_minor
              <> closing_balance_minor
           OR close_status <> 'HARD_CLOSED'
        """,
    ),
    (
        "CASH_FLOW_RECONCILIATION",
        """
        SELECT COUNT(*) FROM gold.fct_cash_flow_reconciliation
        WHERE opening_cash_minor + operating_cash_flow_minor
              + investing_cash_flow_minor + financing_cash_flow_minor
              + fx_and_other_movement_minor <> closing_cash_minor
           OR statement_cash_movement_minor <> operating_cash_flow_minor
              + investing_cash_flow_minor + financing_cash_flow_minor
              + fx_and_other_movement_minor
           OR unreconciled_difference_minor <> 0
           OR reconciliation_status <> 'RECONCILED'
        """,
    ),
    (
        "RETAINED_EARNINGS_RECONCILIATION",
        """
        SELECT COUNT(*) FROM gold.fct_retained_earnings_bridge
        WHERE opening_retained_earnings_minor + net_income_minor
              - dividends_minor + other_equity_movements_minor
              <> closing_retained_earnings_minor
           OR reconciliation_status <> 'RECONCILED'
        """,
    ),
    (
        "CROSS_STATEMENT_NET_INCOME",
        """
        WITH income AS (
            SELECT reporting_version_ref,
                MAX(CASE WHEN statement_class = 'INCOME_STATEMENT'
                          AND statement_line = 'net_income' THEN amount_minor END) is_income,
                MAX(CASE WHEN statement_class = 'CASH_FLOW'
                          AND statement_line = 'net_income' THEN amount_minor END) cf_income
            FROM gold.fct_statutory_statement_lines GROUP BY 1
        )
        SELECT COUNT(*) FROM income
        JOIN gold.fct_retained_earnings_bridge retained USING (reporting_version_ref)
        WHERE is_income <> cf_income OR is_income <> retained.net_income_minor
        """,
    ),
    (
        "BALANCE_SHEET_EQUATION",
        """
        WITH balance_sheet AS (
            SELECT reporting_version_ref,
                MAX(CASE WHEN statement_line = 'total_assets' THEN amount_minor END) assets,
                MAX(CASE WHEN statement_line = 'total_liabilities_and_equity' THEN amount_minor END) liabilities_equity
            FROM gold.fct_statutory_statement_lines
            WHERE statement_class = 'BALANCE_SHEET' GROUP BY 1
        )
        SELECT COUNT(*) FROM balance_sheet
        WHERE assets IS NULL OR liabilities_equity IS NULL
           OR assets <> liabilities_equity
        """,
    ),
    (
        "STATUTORY_RECONCILIATIONS_PASS",
        """
        SELECT COUNT(*) FROM gold.fct_statutory_reconciliations
        WHERE status <> 'PASS' OR difference_minor <> 0
           OR first_failure_ref IS NOT NULL
        """,
    ),
    (
        "REPORTING_VERSION_RELIABILITY",
        """
        SELECT COUNT(*) FROM gold.dim_reporting_version
        WHERE reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
           OR reliability_purpose <> 'STATUTORY_ACTUALS'
           OR source_package_digest <> ?
        """,
    ),
    (
        "Q_FINANCE_REGISTRY_CLOSURE",
        """
        SELECT COUNT(*) FROM (
            SELECT registry.dataset_id
            FROM governance.q_finance_dataset_registry registry
            LEFT JOIN information_schema.tables physical
              ON registry.relation_schema = physical.table_schema
             AND registry.relation_name = physical.table_name
            WHERE physical.table_name IS NULL
            UNION ALL
            SELECT 'COUNT'
            WHERE (SELECT COUNT(*) FROM governance.q_finance_dataset_registry) <> 15
        )
        """,
    ),
    (
        "GOLD_DIMENSION_RELATIONSHIPS",
        """
        SELECT COUNT(*) FROM (
            SELECT tb.trial_balance_hk
            FROM gold.fct_statutory_trial_balance tb
            LEFT JOIN gold.dim_period period USING (period_id)
            LEFT JOIN gold.dim_reporting_scope scope USING (scope_id)
            LEFT JOIN gold.dim_gl_account account USING (account_id)
            LEFT JOIN gold.dim_reporting_version version USING (reporting_version_ref)
            WHERE period.period_hk IS NULL OR scope.reporting_scope_hk IS NULL
               OR account.gl_account_hk IS NULL OR version.reporting_version_hk IS NULL
            UNION ALL
            SELECT statement.statement_line_hk
            FROM gold.fct_statutory_statement_lines statement
            LEFT JOIN gold.dim_period period USING (period_id)
            LEFT JOIN gold.dim_reporting_scope scope USING (scope_id)
            LEFT JOIN gold.dim_reporting_version version USING (reporting_version_ref)
            WHERE period.period_hk IS NULL OR scope.reporting_scope_hk IS NULL
               OR version.reporting_version_hk IS NULL
        )
        """,
    ),
)
from finance_assurance.finance_data.service import FinanceDataSubstrateService
from finance_assurance.finance_model.b2_controls import B2_CONTROL_QUERIES
from finance_assurance.finance_model.b3_controls import B3_CONTROL_QUERIES
from finance_assurance.finance_model.b4_controls import B4_CONTROL_QUERIES
from finance_assurance.finance_model.c1_controls import C1_CONTROL_QUERIES
from finance_assurance.finance_model.contracts import (
    FinanceModelBuildRequest,
    FinanceModelBuildResult,
    FinanceModelVerifyRequest,
    FinanceModelVerifyResult,
)

MODEL_CONTRACT_VERSION = "q-finance-model-package@v1"
B1_REGISTRY_TABLES = (
    "q_finance_dataset_registry",
    "q_finance_relationship_registry",
    "q_finance_measure_registry",
    "q_finance_lineage_registry",
)


class FinanceModelError(RuntimeError):
    """The governed finance-model build or verification failed."""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _warehouse_path(package_path: Path) -> Path:
    return package_path / "warehouse" / "finance-analytics.duckdb"


def _source_warehouse_path(source_package_path: Path) -> Path:
    candidates = tuple((source_package_path / "warehouse").glob("*.duckdb"))
    if len(candidates) != 1:
        raise FinanceModelError("A2.4 package must contain one DuckDB warehouse")
    return candidates[0]


def _attach_source(connection: duckdb.DuckDBPyConnection, source_path: Path) -> None:
    resolved = str(source_path.resolve())
    if "'" in resolved:
        raise FinanceModelError("source warehouse path contains an unsupported quote")
    connection.execute(f"ATTACH '{resolved}' AS a24_source (READ_ONLY)")


def _model_signatures(
    connection: duckdb.DuckDBPyConnection,
) -> list[dict[str, object]]:
    relations = connection.execute(
        """
        SELECT table_schema, table_name, table_type
        FROM information_schema.tables
        WHERE table_schema IN ('silver', 'gold', 'governance')
        ORDER BY table_schema, table_name
        """
    ).fetchall()
    signatures: list[dict[str, object]] = []
    for schema_name, relation_name, relation_type in relations:
        columns = connection.execute(
            """
            SELECT column_name, data_type, is_nullable, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = ? AND table_name = ?
            ORDER BY ordinal_position
            """,
            [schema_name, relation_name],
        ).fetchall()
        row_count = connection.execute(
            f'SELECT COUNT(*) FROM "{schema_name}"."{relation_name}"'
        ).fetchone()[0]
        signatures.append(
            {
                "schema": schema_name,
                "name": relation_name,
                "relation_type": relation_type,
                "row_count": row_count,
                "columns": [
                    {
                        "name": item[0],
                        "data_type": item[1],
                        "nullable": item[2] == "YES",
                        "ordinal": item[3],
                    }
                    for item in columns
                ],
            }
        )
    return signatures


def _relation_rows(
    connection: duckdb.DuckDBPyConnection,
    schema_name: str,
    relation_name: str,
) -> list[dict[str, object]]:
    cursor = connection.execute(
        f'SELECT * FROM "{schema_name}"."{relation_name}" ORDER BY 1'
    )
    columns = [item[0] for item in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def _registry_payloads(
    connection: duckdb.DuckDBPyConnection,
    profile: FinanceModelProfile,
) -> dict[str, list[dict[str, object]]]:
    return {
        name: _relation_rows(connection, "governance", name)
        for name in profile.registry_tables
    }


def _verify_semantic_controls(
    connection: duckdb.DuckDBPyConnection,
    *,
    source_data_ref: str,
    source_package_digest: str,
    profile: FinanceModelProfile,
) -> int:
    controls = SEMANTIC_CONTROL_QUERIES
    if profile.slice_name == "B2":
        controls = tuple(
            item for item in controls if item[0] != "Q_FINANCE_REGISTRY_CLOSURE"
        ) + B2_CONTROL_QUERIES
    elif profile.slice_name == "B3":
        controls = (
            tuple(
                item for item in controls
                if item[0] != "Q_FINANCE_REGISTRY_CLOSURE"
            )
            + B2_CONTROL_QUERIES
            + B3_CONTROL_QUERIES
        )
    elif profile.slice_name == "B4":
        controls = (
            tuple(
                item for item in controls
                if item[0] != "Q_FINANCE_REGISTRY_CLOSURE"
            )
            + B2_CONTROL_QUERIES
            + B3_CONTROL_QUERIES
            + B4_CONTROL_QUERIES
        )
    elif profile.slice_name == "C1":
        controls = (
            tuple(
                item for item in controls
                if item[0] != "Q_FINANCE_REGISTRY_CLOSURE"
            )
            + B2_CONTROL_QUERIES
            + B3_CONTROL_QUERIES
            + tuple(
                item for item in B4_CONTROL_QUERIES
                if item[0] != "Q_FINANCE_V4_REGISTRY_CLOSURE"
            )
            + C1_CONTROL_QUERIES
        )
    for control_name, query in controls:
        parameters = (
            [source_package_digest]
            if control_name == "REPORTING_VERSION_RELIABILITY"
            else None
        )
        failure_count = connection.execute(query, parameters).fetchone()[0]
        if failure_count != 0:
            raise FinanceModelError(
                f"independent control {control_name} failed: {failure_count}"
            )
    dataset_rows = _relation_rows(
        connection,
        "governance",
        profile.dataset_registry,
    )
    for item in dataset_rows:
        relation_name = str(item["relation_name"])
        if re.fullmatch(r"[a-z0-9_]+", relation_name) is None:
            raise FinanceModelError("Q-FINANCE relation name is not safe")
        failure_count = connection.execute(
            f"""
            SELECT COUNT(*) FROM gold.\"{relation_name}\"
            WHERE _source_data_ref IS NULL OR _source_data_ref <> ?
            """,
            [source_data_ref],
        ).fetchone()[0]
        if failure_count != 0:
            raise FinanceModelError(
                f"independent source-reference control failed for {relation_name}"
            )
    return len(controls) + 1


def _semantic_body(
    *,
    model_ref: str,
    slice_name: str,
    source_data_ref: str,
    source_package_digest: str,
    models: list[dict[str, object]],
    registries: dict[str, list[dict[str, object]]],
) -> dict[str, object]:
    return {
        "contract_version": MODEL_CONTRACT_VERSION,
        "model_ref": model_ref,
        "slice_name": slice_name,
        "source_data_ref": source_data_ref,
        "source_package_digest": source_package_digest,
        "models": models,
        "registries": registries,
    }


def _write_metadata(
    *,
    staging_path: Path,
    source_package_path: Path,
    source_data_ref: str,
    source_package_digest: str,
    model_ref: str,
    built_at: str,
    target_path: Path,
    profile: FinanceModelProfile,
) -> tuple[str, int, int, int, int, int]:
    warehouse_path = _warehouse_path(staging_path)
    with duckdb.connect(str(warehouse_path), read_only=True) as connection:
        _attach_source(connection, _source_warehouse_path(source_package_path))
        models = _model_signatures(connection)
        registries = _registry_payloads(connection, profile)
        control_count = _verify_semantic_controls(
            connection,
            source_data_ref=source_data_ref,
            source_package_digest=source_package_digest,
            profile=profile,
        )

    semantic_body = _semantic_body(
        model_ref=model_ref,
        slice_name=profile.slice_name,
        source_data_ref=source_data_ref,
        source_package_digest=source_package_digest,
        models=models,
        registries=registries,
    )
    semantic_digest = sha256_bytes(canonical_json_bytes(semantic_body))
    run_results_path = target_path / "run_results.json"
    run_results = json.loads(run_results_path.read_bytes())
    test_results = [
        item
        for item in run_results["results"]
        if str(item["unique_id"]).startswith("test.")
    ]
    if not test_results or any(item["status"] != "pass" for item in test_results):
        raise FinanceModelError("dbt run results do not contain an all-pass test set")

    metadata_path = staging_path / "metadata"
    metadata_path.mkdir(parents=True)
    for name, rows in registries.items():
        (metadata_path / f"{name}.json").write_bytes(
            canonical_json_bytes(
                {
                    "contract_version": f"{name}@v1",
                    "rows": rows,
                }
            )
        )
    shutil.copyfile(target_path / "manifest.json", metadata_path / "dbt-manifest.json")
    shutil.copyfile(run_results_path, metadata_path / "dbt-run-results.json")

    silver_count = sum(item["schema"] == "silver" for item in models)
    gold_count = sum(item["schema"] == "gold" for item in models)
    governance_count = sum(item["schema"] == "governance" for item in models)
    actual_counts = (silver_count, gold_count, governance_count, len(test_results))
    expected_counts = (
        profile.silver_model_count,
        profile.gold_dataset_count,
        profile.governance_model_count,
        profile.dbt_test_count,
    )
    if actual_counts != expected_counts:
        raise FinanceModelError(
            f"{profile.slice_name} executable inventory differs: "
            f"actual={actual_counts}, expected={expected_counts}"
        )
    manifest = {
        "contract_version": MODEL_CONTRACT_VERSION,
        "model_ref": model_ref,
        "built_at": built_at,
        "source_data_ref": source_data_ref,
        "source_package_digest": source_package_digest,
        "source_package_path": str(source_package_path.resolve()),
        "source_attachment_mode": "READ_ONLY",
        "warehouse_path": "warehouse/finance-analytics.duckdb",
        "dbt_core_version": version("dbt-core"),
        "dbt_duckdb_version": version("dbt-duckdb"),
        "silver_model_count": silver_count,
        "gold_dataset_count": gold_count,
        "governance_model_count": governance_count,
        "dbt_test_count": len(test_results),
        "independent_control_count": control_count,
        "models": models,
        "model_semantic_digest": semantic_digest,
        "money_contract": "INTEGER_MINOR_UNITS_PLUS_CURRENCY",
        "status": "PUBLISHED",
    }
    if profile.slice_name == "B2":
        manifest["predecessor_model_ref"] = "Q-FINANCE-B1@v1"
    elif profile.slice_name == "B3":
        manifest["predecessor_model_ref"] = "Q-FINANCE-B2@v1"
    elif profile.slice_name == "B4":
        manifest["predecessor_model_ref"] = "Q-FINANCE-B3@v1"
        manifest["logical_rebuild_identity"] = "MODEL_SEMANTIC_DIGEST"
    elif profile.slice_name == "C1":
        manifest["predecessor_model_ref"] = "Q-FINANCE-B4@v1"
        manifest["logical_rebuild_identity"] = "MODEL_SEMANTIC_DIGEST"
    (metadata_path / "model-manifest.json").write_bytes(
        canonical_json_bytes(manifest)
    )
    return (
        semantic_digest,
        silver_count,
        gold_count,
        governance_count,
        len(test_results),
        control_count,
    )


def _readme(
    model_ref: str,
    source_data_ref: str,
    source_digest: str,
    profile: FinanceModelProfile,
) -> bytes:
    text = (
        f"# Governed Finance Model - Slice {profile.slice_name}\n\n"
        f"Model: {model_ref}\n"
        f"Source authority: {source_data_ref}\n"
        f"Source digest: {source_digest}\n\n"
        "The A2.4 DuckDB source was attached read-only. Silver applies strict "
        "typing; Gold publishes conformed dimensions, atomic facts, rollforwards, "
        "assurance results, and exact B1 statutory-spine coordinates. "
        "All monetary values remain integer minor units with currency.\n"
    )
    return text.encode("ascii")


def _verify_dbt_results(package_path: Path, profile: FinanceModelProfile) -> None:
    run_results_path = package_path / "metadata" / "dbt-run-results.json"
    run_results = json.loads(run_results_path.read_bytes())
    tests = [
        item
        for item in run_results["results"]
        if str(item["unique_id"]).startswith("test.")
    ]
    if len(tests) != profile.dbt_test_count:
        raise FinanceModelError("dbt test inventory differs from the closed profile")
    failures = [item for item in tests if item["status"] != "pass"]
    if failures:
        raise FinanceModelError(
            f"dbt test result is not all-pass: {failures[0]['unique_id']}"
        )


def _seal(staging_path: Path) -> str:
    declared: list[dict[str, object]] = []
    for path in sorted(item for item in staging_path.rglob("*") if item.is_file()):
        if path.name in {"checksums.json", "finance-model.digest"}:
            continue
        payload = path.read_bytes()
        declared.append(
            {
                "path": path.relative_to(staging_path).as_posix(),
                "sha256": sha256_bytes(payload),
                "byte_count": len(payload),
            }
        )
    checksums = {
        "contract_version": "q-finance-model-checksums@v1",
        "files": declared,
    }
    checksum_bytes = canonical_json_bytes(checksums)
    package_digest = sha256_bytes(checksum_bytes)
    (staging_path / "checksums.json").write_bytes(checksum_bytes)
    (staging_path / "finance-model.digest").write_bytes(
        f"{package_digest}\n".encode("ascii")
    )
    return package_digest


class FinanceModelService:
    """Build and verify bounded Q-FINANCE analytical warehouse profiles."""

    def build(self, request: FinanceModelBuildRequest) -> FinanceModelBuildResult:
        request.validate()
        profile = _profile_for_ref(request.model_ref)
        output_path = request.output_path.resolve()
        if output_path.exists():
            raise FinanceModelError("finance-model output already exists")
        source_package_path = request.source_package_path.resolve()
        source_result = FinanceDataSubstrateService().verify(
            source_package_path,
            expected_digest=request.expected_source_digest,
        )
        source_manifest = json.loads(
            (source_package_path / "source-manifest.json").read_bytes()
        )
        if source_manifest.get("statutory_contract_version") != "A2.4":
            raise FinanceModelError(
                f"Slice {profile.slice_name} requires the ratified A2.4 contract"
            )

        staging_path = output_path.parent / f".{output_path.name}.building"
        if staging_path.exists():
            raise FinanceModelError("finance-model staging path already exists")
        staging_path.mkdir(parents=True)
        try:
            warehouse_path = _warehouse_path(staging_path)
            warehouse_path.parent.mkdir(parents=True)
            with tempfile.TemporaryDirectory(
                prefix=f"fap-{profile.slice_name.lower()}-dbt-"
            ) as temp_dir:
                temp_path = Path(temp_dir)
                target_path = temp_path / "target"
                log_path = temp_path / "logs"
                environment = os.environ.copy()
                environment.update(
                    {
                        "FAP_A24_SOURCE_PATH": str(
                            _source_warehouse_path(source_package_path).resolve()
                        ),
                        "FAP_ANALYTICS_PATH": str(warehouse_path.resolve()),
                        "FAP_A24_DATA_REF": source_result.data_ref,
                        "FAP_A24_PACKAGE_DIGEST": source_result.package_digest,
                        "FAP_FINANCE_MODEL_REF": request.model_ref,
                        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
                    }
                )
                executable_name = "dbt.exe" if os.name == "nt" else "dbt"
                dbt_executable = Path(sys.executable).with_name(executable_name)
                dbt_arguments = [
                        str(dbt_executable),
                        "build",
                        "--project-dir",
                        str(_project_root()),
                        "--profiles-dir",
                        str(_project_root()),
                        "--target-path",
                        str(target_path),
                        "--log-path",
                        str(log_path),
                        "--no-use-colors",
                    ]
                if profile.slice_name == "B1":
                    dbt_arguments.extend(
                        [
                            "--exclude",
                            "tag:slice_b2",
                            "tag:slice_b3",
                            "tag:slice_b4",
                            "tag:slice_c",
                        ]
                    )
                elif profile.slice_name == "B2":
                    dbt_arguments.extend(
                        ["--exclude", "tag:slice_b3", "tag:slice_b4", "tag:slice_c"]
                    )
                elif profile.slice_name == "B3":
                    dbt_arguments.extend(["--exclude", "tag:slice_b4", "tag:slice_c"])
                elif profile.slice_name == "B4":
                    dbt_arguments.extend(["--exclude", "tag:slice_c"])
                completed = subprocess.run(
                    dbt_arguments,
                    cwd=_project_root(),
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode != 0:
                    message = completed.stdout[-4000:] + completed.stderr[-4000:]
                    raise FinanceModelError(f"dbt build failed:\n{message}")
                (
                    semantic_digest,
                    silver_count,
                    gold_count,
                    governance_count,
                    dbt_test_count,
                    control_count,
                ) = _write_metadata(
                    staging_path=staging_path,
                    source_package_path=source_package_path,
                    source_data_ref=source_result.data_ref,
                    source_package_digest=source_result.package_digest,
                    model_ref=request.model_ref,
                    built_at=request.built_at,
                    target_path=target_path,
                    profile=profile,
                )
            (staging_path / "README.md").write_bytes(
                _readme(
                    request.model_ref,
                    source_result.data_ref,
                    source_result.package_digest,
                    profile,
                )
            )
            package_digest = _seal(staging_path)
            self.verify(
                FinanceModelVerifyRequest(
                    source_package_path=source_package_path,
                    package_path=staging_path,
                    expected_source_digest=request.expected_source_digest,
                    expected_package_digest=package_digest,
                )
            )
            staging_path.replace(output_path)
        except Exception:
            shutil.rmtree(staging_path, ignore_errors=True)
            raise

        return FinanceModelBuildResult(
            model_ref=request.model_ref,
            source_data_ref=source_result.data_ref,
            source_package_digest=source_result.package_digest,
            package_digest=package_digest,
            model_semantic_digest=semantic_digest,
            output_path=output_path,
            silver_model_count=silver_count,
            gold_dataset_count=gold_count,
            governance_model_count=governance_count,
            dbt_test_count=dbt_test_count,
            independent_control_count=control_count,
        )

    def verify(self, request: FinanceModelVerifyRequest) -> FinanceModelVerifyResult:
        package_path = request.package_path.resolve()
        source_path = request.source_package_path.resolve()
        source_result = FinanceDataSubstrateService().verify(
            source_path,
            expected_digest=request.expected_source_digest,
        )
        checksum_path = package_path / "checksums.json"
        digest_path = package_path / "finance-model.digest"
        if not checksum_path.is_file() or not digest_path.is_file():
            raise FinanceModelError("finance-model seal is incomplete")
        checksum_bytes = checksum_path.read_bytes()
        checksums = json.loads(checksum_bytes)
        package_digest = digest_path.read_text(encoding="ascii").strip()
        if sha256_bytes(checksum_bytes) != package_digest:
            raise FinanceModelError("finance-model digest does not bind checksums")
        if (
            request.expected_package_digest is not None
            and request.expected_package_digest != package_digest
        ):
            raise FinanceModelError("finance-model package digest differs")
        declared_paths = {item["path"] for item in checksums["files"]}
        physical_paths = {
            item.relative_to(package_path).as_posix()
            for item in package_path.rglob("*")
            if item.is_file()
        }
        if physical_paths != declared_paths | {
            "checksums.json",
            "finance-model.digest",
        }:
            raise FinanceModelError("finance-model physical inventory differs")
        for item in checksums["files"]:
            payload = (package_path / item["path"]).read_bytes()
            if len(payload) != item["byte_count"]:
                raise FinanceModelError(f"byte count differs for {item['path']}")
            if sha256_bytes(payload) != item["sha256"]:
                raise FinanceModelError(f"checksum differs for {item['path']}")

        manifest = json.loads(
            (package_path / "metadata" / "model-manifest.json").read_bytes()
        )
        profile = _profile_for_ref(str(manifest["model_ref"]))
        if manifest["contract_version"] != MODEL_CONTRACT_VERSION:
            raise FinanceModelError("finance-model contract version differs")
        if manifest["source_data_ref"] != source_result.data_ref:
            raise FinanceModelError("finance-model source data reference differs")
        if manifest["source_package_digest"] != source_result.package_digest:
            raise FinanceModelError("finance-model source digest differs")
        if manifest["source_attachment_mode"] != "READ_ONLY":
            raise FinanceModelError("finance-model source attachment is not read-only")

        warehouse_path = _warehouse_path(package_path)
        with duckdb.connect(str(warehouse_path), read_only=True) as connection:
            _attach_source(connection, _source_warehouse_path(source_path))
            models = _model_signatures(connection)
            registries = _registry_payloads(connection, profile)
            control_count = _verify_semantic_controls(
                connection,
                source_data_ref=source_result.data_ref,
                source_package_digest=source_result.package_digest,
                profile=profile,
            )
        _verify_dbt_results(package_path, profile)
        if models != manifest["models"]:
            raise FinanceModelError("finance-model logical signatures differ")
        for name, rows in registries.items():
            registry_file = json.loads(
                (package_path / "metadata" / f"{name}.json").read_bytes()
            )
            if registry_file["rows"] != rows:
                raise FinanceModelError(f"{name} export differs from DuckDB")
        semantic_digest = sha256_bytes(
            canonical_json_bytes(
                _semantic_body(
                    model_ref=manifest["model_ref"],
                    slice_name=profile.slice_name,
                    source_data_ref=source_result.data_ref,
                    source_package_digest=source_result.package_digest,
                    models=models,
                    registries=registries,
                )
            )
        )
        if semantic_digest != manifest["model_semantic_digest"]:
            raise FinanceModelError("finance-model semantic digest differs")
        if control_count != manifest["independent_control_count"]:
            raise FinanceModelError("finance-model independent control count differs")
        gold_count = sum(item["schema"] == "gold" for item in models)
        silver_count = sum(item["schema"] == "silver" for item in models)
        governance_count = sum(item["schema"] == "governance" for item in models)
        registry_count = len(registries[profile.dataset_registry])
        if (
            gold_count != profile.gold_dataset_count
            or silver_count != profile.silver_model_count
            or governance_count != profile.governance_model_count
            or registry_count != profile.gold_dataset_count
            or manifest["dbt_test_count"] != profile.dbt_test_count
        ):
            raise FinanceModelError(
                f"Q-FINANCE {profile.slice_name} executable inventory is not closed"
            )
        return FinanceModelVerifyResult(
            model_ref=manifest["model_ref"],
            source_data_ref=source_result.data_ref,
            source_package_digest=source_result.package_digest,
            package_digest=package_digest,
            model_semantic_digest=semantic_digest,
            checked_model_count=len(models),
            checked_gold_dataset_count=gold_count,
            checked_dbt_test_count=manifest["dbt_test_count"],
            checked_control_count=control_count,
        )
