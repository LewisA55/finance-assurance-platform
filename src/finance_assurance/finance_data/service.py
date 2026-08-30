"""Build and verify the high-volume finance data substrate package."""

from __future__ import annotations

import csv
import gc
import json
import re
import shutil
import time
from datetime import date
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import duckdb

from finance_assurance.exports.serialization import canonical_json_bytes, sha256_bytes
from finance_assurance.finance_data.bronze import (
    DATABASE_RELATIVE_PATH,
    BronzeBuildResult,
    BronzeTableResult,
    build_bronze_database,
    database_file_sha256,
    verify_bronze_database,
)
from finance_assurance.finance_data.contracts import (
    SCALE_PROFILES,
    FinanceDataBuildRequest,
    FinanceDataBuildResult,
    FinanceDataReproduceRequest,
    FinanceDataReproduceResult,
    FinanceDataVerifyResult,
)
from finance_assurance.finance_data.definitions import (
    A1_SOURCE_DATASETS,
    A21_PACKAGE_DATASETS,
    A22_PACKAGE_DATASETS,
    A22B_PACKAGE_DATASETS,
    ALL_SOURCE_DATASETS,
    BUSINESS_EVENTS,
    DEFECT_REGISTRY,
    SOURCE_GL_LINES,
)
from finance_assurance.finance_data.generation import FinancePopulationGenerator

SOURCE_MANIFEST_PATH = "source-manifest.json"
BRONZE_MANIFEST_PATH = "bronze-manifest.json"
CHECKSUMS_PATH = "checksums.json"
DETACHED_DIGEST_PATH = "finance-data.digest"
README_PATH = "README.md"
MONEY_PATTERN = re.compile(r"-?\d+\Z")
CURRENCY_PATTERN = re.compile(r"[A-Z]{3}\Z")


class FinanceDataSubstrateError(RuntimeError):
    """Fail-closed finance-data build or verification error."""


def _stream_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def _read_canonical_json(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    value = json.loads(payload)
    if canonical_json_bytes(value) != payload:
        raise FinanceDataSubstrateError(f"JSON is not canonical: {path.name}")
    if not isinstance(value, dict):
        raise FinanceDataSubstrateError(f"JSON root is not an object: {path.name}")
    return value


def _atomic_publish(staging: Path, final_path: Path) -> None:
    for attempt in range(8):
        try:
            staging.replace(final_path)
            return
        except PermissionError:
            if attempt == 7:
                raise
            gc.collect()
            time.sleep(0.05 * (attempt + 1))


def _relative_files(root: Path) -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        )
    )


def _read_csv_contract(path: Path, expected_columns: tuple[str, ...]) -> int:
    money_indexes = [
        index for index, name in enumerate(expected_columns) if name.endswith("_minor")
    ]
    currency_indexes = [
        index
        for index, name in enumerate(expected_columns)
        if name == "currency" or name.endswith("_currency")
    ]
    row_count = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        header = next(reader, None)
        if tuple(header or ()) != expected_columns:
            raise FinanceDataSubstrateError(f"CSV header differs: {path}")
        for row in reader:
            if len(row) != len(expected_columns):
                raise FinanceDataSubstrateError(f"CSV row width differs: {path}")
            for index in money_indexes:
                if not row[index] or MONEY_PATTERN.fullmatch(row[index]) is None:
                    raise FinanceDataSubstrateError(
                        f"minor-unit value is not an integer: {path}"
                    )
            for index in currency_indexes:
                if row[index] and CURRENCY_PATTERN.fullmatch(row[index]) is None:
                    raise FinanceDataSubstrateError(
                        f"currency value is not a three-letter code: {path}"
                    )
            row_count += 1
    return row_count


def _bronze_tables_from_manifest(
    manifest: dict[str, object],
) -> tuple[BronzeTableResult, ...]:
    tables = manifest.get("tables")
    if not isinstance(tables, list):
        raise FinanceDataSubstrateError("Bronze manifest tables are missing")
    results: list[BronzeTableResult] = []
    for raw in tables:
        if not isinstance(raw, dict):
            raise FinanceDataSubstrateError("Bronze manifest table is invalid")
        results.append(
            BronzeTableResult(
                source_path=str(raw["source_path"]),
                table_name=str(raw["table_name"]),
                source_sha256=str(raw["source_sha256"]),
                row_count=int(raw["row_count"]),
                source_columns=tuple(str(value) for value in raw["source_columns"]),
            )
        )
    return tuple(results)


def _verify_accounting_controls(database_path: Path) -> None:
    with duckdb.connect(str(database_path), read_only=True) as connection:
        source_gl = "bronze.accounting__source_gl_journal_lines"
        business_events = "bronze.events__business_events"
        unbalanced = connection.execute(
            f"""
            SELECT COUNT(*) FROM (
                SELECT source_journal_id
                FROM {source_gl}
                GROUP BY source_journal_id
                HAVING SUM(CAST(debit_minor AS BIGINT))
                    <> SUM(CAST(credit_minor AS BIGINT))
            )
            """
        ).fetchone()[0]
        if unbalanced:
            raise FinanceDataSubstrateError("source-system journals are unbalanced")
        missing_events = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {source_gl} AS journal_line
            LEFT JOIN {business_events} AS business_event
              ON journal_line.business_event_ref = business_event.business_event_ref
            WHERE business_event.business_event_ref IS NULL
            """
        ).fetchone()[0]
        if missing_events:
            raise FinanceDataSubstrateError(
                "source-system journal lines lack causal business events"
            )
        period_imbalances = connection.execute(
            f"""
            SELECT COUNT(*) FROM (
                SELECT period_id
                FROM {source_gl}
                GROUP BY period_id
                HAVING SUM(CAST(debit_minor AS BIGINT))
                    <> SUM(CAST(credit_minor AS BIGINT))
            )
            """
        ).fetchone()[0]
        if period_imbalances:
            raise FinanceDataSubstrateError("period source-system activity is unbalanced")


def _assert_zero(
    connection: duckdb.DuckDBPyConnection, sql: str, message: str
) -> None:
    failure_count = int(connection.execute(sql).fetchone()[0])
    if failure_count:
        raise FinanceDataSubstrateError(f"{message}: {failure_count} failure(s)")


def _verify_a21_controls(database_path: Path) -> None:
    """Recalculate A2.1 treasury controls from independently loaded Bronze rows."""

    with duckdb.connect(str(database_path), read_only=True) as connection:
        entity_count = connection.execute(
            "SELECT COUNT(*) FROM bronze.reference__legal_entities"
        ).fetchone()[0]
        if entity_count != 2:
            raise FinanceDataSubstrateError("A2.1 legal-entity scope differs")

        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT business_event_ref, legal_entity_id,
                       SUM(CAST(debit_minor AS HUGEINT))
                         - SUM(CAST(credit_minor AS HUGEINT)) AS amount_minor
                FROM bronze.accounting__source_gl_journal_lines
                WHERE account_id = '1000'
                GROUP BY business_event_ref, legal_entity_id
            ) AS gl
            FULL OUTER JOIN (
                SELECT business_event_ref, legal_entity_id,
                       SUM(CAST(amount_minor AS HUGEINT)) AS amount_minor
                FROM bronze.treasury__bank_transactions
                GROUP BY business_event_ref, legal_entity_id
            ) AS bank
              ON gl.business_event_ref = bank.business_event_ref
             AND gl.legal_entity_id = bank.legal_entity_id
            WHERE gl.business_event_ref IS NULL
               OR bank.business_event_ref IS NULL
               OR gl.amount_minor <> bank.amount_minor
            """,
            "bank transactions do not reproduce source-GL cash",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.treasury__bank_transactions AS bank
            FULL OUTER JOIN bronze.treasury__bank_statement_lines AS statement
              USING (bank_transaction_id, bank_account_id)
            WHERE bank.bank_transaction_id IS NULL
               OR statement.bank_transaction_id IS NULL
               OR CAST(bank.amount_minor AS HUGEINT)
                    <> CAST(statement.amount_minor AS HUGEINT)
               OR bank.value_date <> statement.value_date
               OR bank.currency <> statement.currency
            """,
            "bank statements do not bind one-for-one to bank transactions",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT statement_line_id,
                       CAST(running_balance_minor AS HUGEINT) AS recorded_balance,
                       SUM(CAST(amount_minor AS HUGEINT)) OVER (
                           PARTITION BY bank_account_id
                           ORDER BY CAST(value_date AS DATE),
                                    CASE WHEN CAST(amount_minor AS HUGEINT) > 0
                                         THEN 0 ELSE 1 END,
                                    bank_transaction_id
                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                       ) AS replayed_balance
                FROM bronze.treasury__bank_statement_lines
            ) AS replay
            WHERE recorded_balance <> replayed_balance
            """,
            "bank-statement running-balance replay differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.treasury__bank_reconciliations
            WHERE CAST(statement_closing_minor AS HUGEINT)
                    + CAST(outstanding_receipts_minor AS HUGEINT)
                    - CAST(outstanding_disbursements_minor AS HUGEINT)
                    + CAST(other_reconciling_items_minor AS HUGEINT)
                  <> CAST(gl_cash_closing_minor AS HUGEINT)
               OR CAST(unreconciled_difference_minor AS HUGEINT) <> 0
               OR reconciliation_status <> 'RECONCILED'
            """,
            "monthly bank reconciliation differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT account.bank_account_id, period.period_id
                FROM bronze.treasury__bank_accounts AS account
                CROSS JOIN bronze.reference__periods AS period
                WHERE LOWER(period.is_actual_period) = 'true'
                  AND CAST(period.month_start AS DATE)
                        >= DATE_TRUNC('month', CAST(account.opened_date AS DATE))
                  AND (account.closed_date = ''
                       OR CAST(period.month_start AS DATE)
                            <= DATE_TRUNC('month', CAST(account.closed_date AS DATE)))
            ) AS expected
            FULL OUTER JOIN bronze.treasury__bank_reconciliations AS actual
              USING (bank_account_id, period_id)
            WHERE expected.bank_account_id IS NULL
               OR actual.bank_account_id IS NULL
            """,
            "monthly bank-reconciliation coverage differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.treasury__debt_schedule AS schedule
            JOIN bronze.treasury__debt_instruments AS instrument
              USING (debt_instrument_id, legal_entity_id, currency)
            WHERE CAST(schedule.opening_principal_minor AS HUGEINT)
                    + CAST(schedule.drawdown_minor AS HUGEINT)
                    - CAST(schedule.principal_repayment_minor AS HUGEINT)
                  <> CAST(schedule.closing_principal_minor AS HUGEINT)
               OR CAST(schedule.closing_principal_minor AS HUGEINT) < 0
               OR CAST(schedule.closing_principal_minor AS HUGEINT)
                    > CAST(instrument.facility_limit_minor AS HUGEINT)
               OR CAST(instrument.facility_limit_minor AS HUGEINT)
                    - CAST(schedule.closing_principal_minor AS HUGEINT)
                  <> CAST(schedule.undrawn_facility_minor AS HUGEINT)
            """,
            "finite debt roll-forward differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT debt_instrument_id, period_id,
                       CAST(opening_principal_minor AS HUGEINT) AS opening_principal,
                       LAG(CAST(closing_principal_minor AS HUGEINT)) OVER (
                           PARTITION BY debt_instrument_id ORDER BY period_id
                       ) AS prior_closing
                FROM bronze.treasury__debt_schedule
            ) AS continuity
            WHERE prior_closing IS NOT NULL
              AND opening_principal <> prior_closing
            """,
            "debt opening principal does not equal prior closing principal",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.treasury__debt_schedule
            WHERE (debt_instrument_id = 'DEBT-TERM-GBP'
                   AND CAST(cash_interest_minor AS HUGEINT)
                       <> FLOOR((CAST(opening_principal_minor AS HUGEINT)
                                 + CAST(drawdown_minor AS HUGEINT))
                                * CAST(effective_interest_rate_bps AS HUGEINT)
                                / 120000))
               OR (debt_instrument_id = 'DEBT-REVOLVER-GBP'
                   AND (CAST(drawdown_minor AS HUGEINT) <> 0
                        OR CAST(closing_principal_minor AS HUGEINT) <> 0
                        OR CAST(cash_interest_minor AS HUGEINT) <> 0))
            """,
            "debt interest or fixed no-draw revolver policy differs",
        )
        drawdown_count, drawdown_total = connection.execute(
            """
            SELECT COUNT(*) FILTER (WHERE CAST(drawdown_minor AS HUGEINT) <> 0),
                   COALESCE(SUM(CAST(drawdown_minor AS HUGEINT)), 0)
            FROM bronze.treasury__debt_schedule
            """
        ).fetchone()
        if drawdown_count != 1 or drawdown_total != 1_500_000_000:
            raise FinanceDataSubstrateError("authorised formation debt draw differs")

        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.equity__equity_movements AS movement
            LEFT JOIN bronze.events__business_events AS event
              ON movement.business_event_ref = event.business_event_ref
            LEFT JOIN (
                SELECT business_event_ref,
                       SUM(CASE WHEN account_id = '1000'
                           THEN CAST(debit_minor AS HUGEINT)
                              - CAST(credit_minor AS HUGEINT) ELSE 0 END) AS cash,
                       SUM(CASE WHEN account_id = '3000'
                           THEN CAST(credit_minor AS HUGEINT)
                              - CAST(debit_minor AS HUGEINT) ELSE 0 END) AS capital
                FROM bronze.accounting__source_gl_journal_lines
                GROUP BY business_event_ref
            ) AS journal
              ON movement.business_event_ref = journal.business_event_ref
            WHERE movement.authorisation_ref = ''
               OR event.business_event_ref IS NULL
               OR event.event_type <> 'CAPITAL_CONTRIBUTION_RECEIVED'
               OR CAST(movement.amount_minor AS HUGEINT)
                    <> CAST(event.reporting_amount_minor AS HUGEINT)
               OR CAST(movement.amount_minor AS HUGEINT) <> journal.cash
               OR CAST(movement.amount_minor AS HUGEINT) <> journal.capital
            """,
            "equity movement lacks authorised event and journal traceability",
        )
        negative_statement_balance = connection.execute(
            """
            SELECT COUNT(*)
            FROM bronze.treasury__bank_statement_lines
            WHERE CAST(running_balance_minor AS HUGEINT) < 0
            """
        ).fetchone()[0]
        if negative_statement_balance:
            raise FinanceDataSubstrateError(
                "fixed authorised funding does not sustain historical cash"
            )


def _verify_a22_fixed_asset_controls(database_path: Path) -> None:
    """Recalculate the A2.2a source, subledger, GL, and assurance controls."""

    with duckdb.connect(str(database_path), read_only=True) as connection:
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.fixed_assets__fixed_asset_movements
            WHERE CAST(opening_gross_book_value_minor AS HUGEINT)
                    + CAST(gross_addition_minor AS HUGEINT)
                    - CAST(gross_disposal_minor AS HUGEINT)
                  <> CAST(closing_gross_book_value_minor AS HUGEINT)
               OR CAST(opening_accumulated_depreciation_minor AS HUGEINT)
                    + CAST(depreciation_minor AS HUGEINT)
                    + CAST(amortisation_minor AS HUGEINT)
                    + CAST(impairment_minor AS HUGEINT)
                    - CAST(accumulated_depreciation_disposal_minor AS HUGEINT)
                  <> CAST(closing_accumulated_depreciation_minor AS HUGEINT)
               OR CAST(closing_gross_book_value_minor AS HUGEINT)
                    - CAST(closing_accumulated_depreciation_minor AS HUGEINT)
                  <> CAST(closing_net_book_value_minor AS HUGEINT)
            """,
            "fixed-asset roll-forward identity differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT asset_id,
                       CAST(opening_gross_book_value_minor AS HUGEINT) AS opening_gross,
                       CAST(opening_accumulated_depreciation_minor AS HUGEINT)
                           AS opening_accumulated,
                       LAG(CAST(closing_gross_book_value_minor AS HUGEINT)) OVER (
                           PARTITION BY asset_id ORDER BY period_id
                       ) AS prior_gross,
                       LAG(CAST(closing_accumulated_depreciation_minor AS HUGEINT))
                           OVER (PARTITION BY asset_id ORDER BY period_id)
                           AS prior_accumulated
                FROM bronze.fixed_assets__fixed_asset_movements
            ) AS continuity
            WHERE prior_gross IS NOT NULL
              AND (opening_gross <> prior_gross
                   OR opening_accumulated <> prior_accumulated)
            """,
            "fixed-asset prior-period continuity differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.hermes__source_admission_results AS admission
            LEFT JOIN bronze.events__business_events AS event
              ON admission.candidate_business_event_ref = event.business_event_ref
            WHERE admission.source_dataset_path IN (
                    'procurement/capital_invoices.csv',
                    'fixed_assets/asset_lifecycle_events.csv'
                  )
              AND admission.admission_decision <> 'QUARANTINED'
              AND event.business_event_ref IS NULL
            """,
            "admitted fixed-asset source lacks its business event",
        )
        quarantined_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM bronze.hermes__source_admission_results
            WHERE admission_decision = 'QUARANTINED'
              AND decision_reason = 'DUPLICATE_SOURCE_IDENTITY'
              AND source_dataset_path = 'procurement/capital_invoices.csv'
            """
        ).fetchone()[0]
        if quarantined_count != 1:
            raise FinanceDataSubstrateError(
                "fixed-asset duplicate quarantine population differs"
            )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.assurance__fixed_asset_control_results
            WHERE status = 'PASS'
              AND CAST(difference_minor AS HUGEINT) <> 0
            """,
            "passing Argus fixed-asset result has a difference",
        )
        exception_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM bronze.assurance__fixed_asset_control_results
            WHERE status = 'EXCEPTION'
              AND observation_type = 'QUARANTINED_DUPLICATE_SOURCE'
            """
        ).fetchone()[0]
        if exception_count != 1:
            raise FinanceDataSubstrateError(
                "Argus fixed-asset exception population differs"
            )


def _verify_a22b_statutory_subledger_controls(database_path: Path) -> None:
    """Recalculate A2.2b source, schedule, GL, and assurance controls."""

    source_paths = (
        "leases/lease_lifecycle_events.csv",
        "tax/tax_calculation_inputs.csv",
        "working_capital/accrual_source_events.csv",
        "working_capital/prepayment_source_events.csv",
    )
    path_sql = ", ".join(f"'{path}'" for path in source_paths)
    with duckdb.connect(str(database_path), read_only=True) as connection:
        _assert_zero(
            connection,
            f"""
            SELECT COUNT(*)
            FROM bronze.hermes__source_admission_results AS admission
            LEFT JOIN bronze.events__business_events AS event
              ON admission.candidate_business_event_ref = event.business_event_ref
            WHERE admission.source_dataset_path IN ({path_sql})
              AND admission.admission_decision <> 'QUARANTINED'
              AND event.business_event_ref IS NULL
            """,
            "admitted A2.2b source lacks its business event",
        )
        _assert_zero(
            connection,
            f"""
            SELECT COUNT(*)
            FROM bronze.hermes__source_admission_results
            WHERE source_dataset_path IN ({path_sql})
              AND admission_decision = 'QUARANTINED'
              AND (
                    candidate_business_event_ref <> ''
                    OR duplicate_of_ref = ''
                    OR quarantine_ref = ''
                  )
            """,
            "quarantined A2.2b source has an invalid admission result",
        )
        late_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM bronze.hermes__source_admission_results
            WHERE source_dataset_path IN ({path_sql})
              AND admission_decision = 'ADMITTED_WITH_WARNING'
              AND decision_reason = 'LATE_ARRIVAL'
            """
        ).fetchone()[0]
        if late_count < 3:
            raise FinanceDataSubstrateError(
                "A2.2b source population lacks required late-arrival cases"
            )
        quarantined_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM bronze.hermes__source_admission_results
            WHERE source_dataset_path IN ({path_sql})
              AND admission_decision = 'QUARANTINED'
              AND decision_reason = 'DUPLICATE_SOURCE_IDENTITY'
            """
        ).fetchone()[0]
        if quarantined_count != 1:
            raise FinanceDataSubstrateError(
                "A2.2b duplicate quarantine population differs"
            )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.events__business_events
            WHERE source_record_ref = 'PSE-DUPLICATE-00001'
            """,
            "quarantined prepayment duplicate produced a business event",
        )

        def source_rows(table_name: str) -> tuple[tuple[str, ...], list[tuple]]:
            columns = tuple(
                row[0]
                for row in connection.execute(
                    "SELECT column_name "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'bronze' AND table_name = ? "
                    "AND column_name NOT LIKE '\\_%' ESCAPE '\\' "
                    "ORDER BY ordinal_position",
                    [table_name],
                ).fetchall()
            )
            quoted = ", ".join(f'"{column}"' for column in columns)
            rows = connection.execute(
                f'SELECT {quoted} FROM bronze."{table_name}"'
            ).fetchall()
            return columns, rows

        expected_hashes: dict[str, str] = {}
        source_id_specs = (
            (
                "leases__lease_lifecycle_events",
                "lease_lifecycle_event_id",
                "",
            ),
            (
                "tax__tax_calculation_inputs",
                "tax_calculation_input_id",
                "#DEFERRED",
            ),
            (
                "working_capital__accrual_source_events",
                "accrual_source_event_id",
                "",
            ),
            (
                "working_capital__prepayment_source_events",
                "prepayment_source_event_id",
                "",
            ),
        )
        for table_name, id_column, suffix in source_id_specs:
            columns, rows = source_rows(table_name)
            for values in rows:
                payload = dict(zip(columns, values, strict=True))
                source_ref = f"{payload[id_column]}{suffix}"
                expected_hashes[source_ref] = sha256_bytes(
                    canonical_json_bytes(payload)
                )
        actual_hashes = {
            source_ref: source_hash
            for source_ref, source_hash in connection.execute(
                f"""
                SELECT source_record_ref, source_record_hash
                FROM bronze.hermes__source_admission_results
                WHERE source_dataset_path IN ({path_sql})
                """
            ).fetchall()
        }
        if actual_hashes != expected_hashes:
            missing = len(set(expected_hashes) - set(actual_hashes))
            unexpected = len(set(actual_hashes) - set(expected_hashes))
            mismatched = sum(
                actual_hashes.get(ref) != expected_hash
                for ref, expected_hash in expected_hashes.items()
                if ref in actual_hashes
            )
            raise FinanceDataSubstrateError(
                "A2.2b Hermes source hashes differ: "
                f"missing={missing}, unexpected={unexpected}, "
                f"mismatched={mismatched}"
            )

        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.leases__lease_lifecycle_events AS lifecycle
            LEFT JOIN bronze.leases__lease_contracts AS contract
              USING (lease_contract_id, legal_entity_id)
            WHERE contract.lease_contract_id IS NULL
               OR lifecycle.currency <> contract.currency
               OR lifecycle.event_date < contract.commencement_date
               OR lifecycle.event_date > contract.maturity_date
            """,
            "lease lifecycle event does not resolve to its contract",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.leases__lease_schedule
            WHERE CAST(opening_liability_minor AS HUGEINT)
                    + CAST(liability_addition_minor AS HUGEINT)
                    + CAST(interest_accretion_minor AS HUGEINT)
                    - CAST(cash_payment_minor AS HUGEINT)
                  <> CAST(closing_liability_minor AS HUGEINT)
               OR CAST(cash_payment_minor AS HUGEINT)
                    - CAST(interest_accretion_minor AS HUGEINT)
                  <> CAST(principal_reduction_minor AS HUGEINT)
               OR CAST(opening_rou_asset_minor AS HUGEINT)
                    + CAST(rou_asset_addition_minor AS HUGEINT)
                    - CAST(rou_depreciation_minor AS HUGEINT)
                    - CAST(rou_impairment_minor AS HUGEINT)
                  <> CAST(closing_rou_asset_minor AS HUGEINT)
               OR CAST(closing_liability_minor AS HUGEINT) < 0
               OR CAST(closing_rou_asset_minor AS HUGEINT) < 0
            """,
            "lease liability or ROU roll-forward differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT lease_contract_id, period_id,
                       CAST(opening_liability_minor AS HUGEINT) AS opening_liability,
                       CAST(opening_rou_asset_minor AS HUGEINT) AS opening_rou,
                       LAG(CAST(closing_liability_minor AS HUGEINT)) OVER (
                           PARTITION BY lease_contract_id ORDER BY period_id
                       ) AS prior_liability,
                       LAG(CAST(closing_rou_asset_minor AS HUGEINT)) OVER (
                           PARTITION BY lease_contract_id ORDER BY period_id
                       ) AS prior_rou
                FROM bronze.leases__lease_schedule
            ) AS continuity
            WHERE prior_liability IS NOT NULL
              AND (
                    opening_liability <> prior_liability
                    OR opening_rou <> prior_rou
                  )
            """,
            "lease schedule prior-period continuity differs",
        )
        _assert_zero(
            connection,
            """
            WITH expected_raw AS (
                SELECT period_id, '1800' AS account_id,
                       CAST(rou_asset_addition_minor AS HUGEINT) AS debit_minor,
                       0::HUGEINT AS credit_minor
                FROM bronze.leases__lease_schedule
                UNION ALL
                SELECT period_id, '1810', 0,
                       CAST(rou_depreciation_minor AS HUGEINT)
                         + CAST(rou_impairment_minor AS HUGEINT)
                FROM bronze.leases__lease_schedule
                UNION ALL
                SELECT period_id, '2500',
                       CAST(principal_reduction_minor AS HUGEINT),
                       CAST(liability_addition_minor AS HUGEINT)
                FROM bronze.leases__lease_schedule
                UNION ALL
                SELECT period_id, '6500',
                       CAST(interest_accretion_minor AS HUGEINT), 0
                FROM bronze.leases__lease_schedule
                UNION ALL
                SELECT period_id, '6300',
                       CAST(rou_depreciation_minor AS HUGEINT)
                         + CAST(rou_impairment_minor AS HUGEINT), 0
                FROM bronze.leases__lease_schedule
                UNION ALL
                SELECT period_id, '1000', 0,
                       CAST(cash_payment_minor AS HUGEINT)
                FROM bronze.leases__lease_schedule
            ), expected AS (
                SELECT period_id, account_id,
                       SUM(debit_minor) AS debit_minor,
                       SUM(credit_minor) AS credit_minor
                FROM expected_raw
                GROUP BY period_id, account_id
                HAVING SUM(debit_minor) <> 0 OR SUM(credit_minor) <> 0
            ), event_refs AS (
                SELECT DISTINCT refs.ref AS business_event_ref
                FROM bronze.leases__lease_schedule AS schedule,
                     UNNEST(STRING_SPLIT(schedule.business_event_refs, ',')) refs(ref)
                WHERE schedule.business_event_refs <> ''
            ), actual AS (
                SELECT gl.period_id, gl.account_id,
                       SUM(CAST(gl.debit_minor AS HUGEINT)) AS debit_minor,
                       SUM(CAST(gl.credit_minor AS HUGEINT)) AS credit_minor
                FROM bronze.accounting__source_gl_journal_lines AS gl
                JOIN event_refs USING (business_event_ref)
                GROUP BY gl.period_id, gl.account_id
            )
            SELECT COUNT(*)
            FROM expected
            FULL OUTER JOIN actual USING (period_id, account_id)
            WHERE expected.period_id IS NULL
               OR actual.period_id IS NULL
               OR expected.debit_minor <> actual.debit_minor
               OR expected.credit_minor <> actual.credit_minor
            """,
            "lease schedules do not reconcile to GL activity",
        )

        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.tax__tax_schedule AS schedule
            JOIN bronze.tax__tax_calculation_inputs AS input
              USING (period_id, legal_entity_id, jurisdiction_code)
            WHERE CAST(schedule.profit_before_tax_minor AS HUGEINT)
                    <> CAST(input.profit_before_tax_minor AS HUGEINT)
               OR CAST(schedule.permanent_difference_minor AS HUGEINT)
                    <> CAST(input.permanent_difference_minor AS HUGEINT)
               OR CAST(schedule.temporary_difference_minor AS HUGEINT)
                    <> CAST(input.temporary_difference_minor AS HUGEINT)
               OR schedule.statutory_tax_rate_bps
                    <> input.statutory_tax_rate_bps
               OR CAST(schedule.opening_tax_payable_minor AS HUGEINT)
                    + CAST(schedule.current_tax_expense_minor AS HUGEINT)
                    - CAST(schedule.cash_tax_paid_minor AS HUGEINT)
                  <> CAST(schedule.closing_tax_payable_minor AS HUGEINT)
               OR CAST(schedule.opening_deferred_tax_asset_minor AS HUGEINT)
                    + CAST(schedule.deferred_tax_movement_minor AS HUGEINT)
                  <> CAST(schedule.closing_deferred_tax_asset_minor AS HUGEINT)
            """,
            "tax input or provision roll-forward differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.tax__tax_loss_register
            WHERE CAST(opening_tax_loss_minor AS HUGEINT)
                    + CAST(loss_generated_minor AS HUGEINT)
                    - CAST(loss_utilised_minor AS HUGEINT)
                    - CAST(loss_expired_minor AS HUGEINT)
                  <> CAST(closing_tax_loss_minor AS HUGEINT)
               OR CAST(closing_tax_loss_minor AS HUGEINT) < 0
               OR CAST(loss_utilised_minor AS HUGEINT)
                    > CAST(opening_tax_loss_minor AS HUGEINT)
            """,
            "tax-loss vintage roll-forward differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT legal_entity_id, jurisdiction_code, loss_vintage_year,
                       period_id,
                       CAST(opening_tax_loss_minor AS HUGEINT) AS opening_loss,
                       LAG(CAST(closing_tax_loss_minor AS HUGEINT)) OVER (
                           PARTITION BY legal_entity_id, jurisdiction_code,
                                        loss_vintage_year
                           ORDER BY period_id
                       ) AS prior_loss
                FROM bronze.tax__tax_loss_register
            ) AS continuity
            WHERE prior_loss IS NOT NULL AND opening_loss <> prior_loss
            """,
            "tax-loss prior-period continuity differs",
        )
        _assert_zero(
            connection,
            """
            WITH losses AS (
                SELECT period_id, legal_entity_id, jurisdiction_code,
                       SUM(CAST(loss_generated_minor AS HUGEINT))
                           AS generated_minor,
                       SUM(CAST(loss_utilised_minor AS HUGEINT))
                           AS utilised_minor,
                       SUM(CAST(closing_tax_loss_minor AS HUGEINT)) closing_loss
                FROM bronze.tax__tax_loss_register
                GROUP BY period_id, legal_entity_id, jurisdiction_code
            )
            SELECT COUNT(*)
            FROM bronze.tax__tax_schedule AS schedule
            JOIN losses USING (period_id, legal_entity_id, jurisdiction_code)
            JOIN bronze.tax__tax_calculation_inputs AS input
              USING (period_id, legal_entity_id, jurisdiction_code)
            WHERE CAST(schedule.loss_generated_minor AS HUGEINT)
                    <> losses.generated_minor
               OR CAST(schedule.loss_utilised_minor AS HUGEINT)
                    <> losses.utilised_minor
               OR CAST(schedule.closing_deferred_tax_asset_minor AS HUGEINT)
                    <> losses.closing_loss
                       * CAST(schedule.statutory_tax_rate_bps AS HUGEINT)
                       * CAST(input.deferred_tax_recognition_bps AS HUGEINT)
                       // 100000000
            """,
            "tax schedule does not reconcile to loss vintages or DTA policy",
        )
        _assert_zero(
            connection,
            """
            WITH expected_raw AS (
                SELECT period_id, '1250' AS account_id,
                       GREATEST(CAST(deferred_tax_movement_minor AS HUGEINT), 0)
                           AS debit_minor,
                       GREATEST(-CAST(deferred_tax_movement_minor AS HUGEINT), 0)
                           AS credit_minor
                FROM bronze.tax__tax_schedule
                UNION ALL
                SELECT period_id, '6600',
                       CAST(current_tax_expense_minor AS HUGEINT)
                         + GREATEST(-CAST(deferred_tax_movement_minor AS HUGEINT), 0),
                       GREATEST(CAST(deferred_tax_movement_minor AS HUGEINT), 0)
                FROM bronze.tax__tax_schedule
                UNION ALL
                SELECT period_id, '2300',
                       CAST(cash_tax_paid_minor AS HUGEINT),
                       CAST(current_tax_expense_minor AS HUGEINT)
                FROM bronze.tax__tax_schedule
                UNION ALL
                SELECT period_id, '1000', 0,
                       CAST(cash_tax_paid_minor AS HUGEINT)
                FROM bronze.tax__tax_schedule
            ), expected AS (
                SELECT period_id, account_id,
                       SUM(debit_minor) AS debit_minor,
                       SUM(credit_minor) AS credit_minor
                FROM expected_raw
                GROUP BY period_id, account_id
                HAVING SUM(debit_minor) <> 0 OR SUM(credit_minor) <> 0
            ), event_refs AS (
                SELECT DISTINCT refs.ref AS business_event_ref
                FROM bronze.tax__tax_schedule AS schedule,
                     UNNEST(STRING_SPLIT(schedule.business_event_refs, ',')) refs(ref)
                WHERE schedule.business_event_refs <> ''
            ), actual AS (
                SELECT gl.period_id, gl.account_id,
                       SUM(CAST(gl.debit_minor AS HUGEINT)) AS debit_minor,
                       SUM(CAST(gl.credit_minor AS HUGEINT)) AS credit_minor
                FROM bronze.accounting__source_gl_journal_lines AS gl
                JOIN event_refs USING (business_event_ref)
                GROUP BY gl.period_id, gl.account_id
            )
            SELECT COUNT(*)
            FROM expected
            FULL OUTER JOIN actual USING (period_id, account_id)
            WHERE expected.period_id IS NULL
               OR actual.period_id IS NULL
               OR expected.debit_minor <> actual.debit_minor
               OR expected.credit_minor <> actual.credit_minor
            """,
            "tax schedules do not reconcile to GL activity",
        )

        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.working_capital__accrual_schedule
            WHERE CAST(opening_accrual_minor AS HUGEINT)
                    + CAST(addition_minor AS HUGEINT)
                    - CAST(release_minor AS HUGEINT)
                  <> CAST(closing_accrual_minor AS HUGEINT)
               OR CAST(closing_accrual_minor AS HUGEINT) < 0
            """,
            "accrual schedule roll-forward differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.working_capital__prepayment_schedule
            WHERE CAST(opening_prepayment_minor AS HUGEINT)
                    + CAST(cash_addition_minor AS HUGEINT)
                    - CAST(expense_release_minor AS HUGEINT)
                  <> CAST(closing_prepayment_minor AS HUGEINT)
               OR CAST(closing_prepayment_minor AS HUGEINT) < 0
            """,
            "prepayment schedule roll-forward differs",
        )
        for table_name, object_column, opening_column, closing_column in (
            (
                "working_capital__accrual_schedule",
                "accrual_schedule_id",
                "opening_accrual_minor",
                "closing_accrual_minor",
            ),
            (
                "working_capital__prepayment_schedule",
                "prepayment_schedule_id",
                "opening_prepayment_minor",
                "closing_prepayment_minor",
            ),
        ):
            _assert_zero(
                connection,
                f"""
                SELECT COUNT(*)
                FROM (
                    SELECT {object_column}, period_id,
                           CAST({opening_column} AS HUGEINT) AS opening_balance,
                           LAG(CAST({closing_column} AS HUGEINT)) OVER (
                               PARTITION BY {object_column} ORDER BY period_id
                           ) AS prior_balance
                    FROM bronze.{table_name}
                ) AS continuity
                WHERE prior_balance IS NOT NULL
                  AND opening_balance <> prior_balance
                """,
                f"{table_name} prior-period continuity differs",
            )
        _assert_zero(
            connection,
            """
            WITH source AS (
                SELECT accrual_schedule_id, SUBSTR(event_date, 1, 7) period_id,
                       SUM(CASE WHEN event_type = 'ACCRUAL_ESTIMATE_APPROVED'
                           THEN CAST(event_amount_minor AS HUGEINT) ELSE 0 END)
                           AS addition_minor,
                       SUM(CASE WHEN event_type = 'ACCRUAL_SETTLED'
                           THEN CAST(event_amount_minor AS HUGEINT) ELSE 0 END)
                           AS release_minor
                FROM bronze.working_capital__accrual_source_events
                GROUP BY accrual_schedule_id, SUBSTR(event_date, 1, 7)
            )
            SELECT COUNT(*)
            FROM bronze.working_capital__accrual_schedule AS schedule
            JOIN source USING (accrual_schedule_id, period_id)
            WHERE CAST(schedule.addition_minor AS HUGEINT) <> source.addition_minor
               OR CAST(schedule.release_minor AS HUGEINT) <> source.release_minor
            """,
            "accrual source events do not reconcile to Atlas schedule",
        )
        _assert_zero(
            connection,
            """
            WITH source AS (
                SELECT prepayment_schedule_id, SUBSTR(event_date, 1, 7) period_id,
                       SUM(CASE WHEN event_type = 'PREPAYMENT_PAID'
                                  AND duplicate_of_ref = ''
                           THEN CAST(event_amount_minor AS HUGEINT) ELSE 0 END)
                           AS addition_minor,
                       SUM(CASE WHEN event_type = 'PREPAID_SERVICE_CONSUMED'
                                  AND duplicate_of_ref = ''
                           THEN CAST(event_amount_minor AS HUGEINT) ELSE 0 END)
                           AS release_minor
                FROM bronze.working_capital__prepayment_source_events
                GROUP BY prepayment_schedule_id, SUBSTR(event_date, 1, 7)
            )
            SELECT COUNT(*)
            FROM bronze.working_capital__prepayment_schedule AS schedule
            JOIN source USING (prepayment_schedule_id, period_id)
            WHERE CAST(schedule.cash_addition_minor AS HUGEINT)
                    <> source.addition_minor
               OR CAST(schedule.expense_release_minor AS HUGEINT)
                    <> source.release_minor
            """,
            "prepayment source events do not reconcile to Atlas schedule",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.assurance__statutory_subledger_control_results
            WHERE status = 'PASS'
              AND CAST(difference_minor AS HUGEINT) <> 0
            """,
            "passing Argus A2.2b result has a difference",
        )
        argus_exception_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM bronze.assurance__statutory_subledger_control_results
            WHERE status = 'EXCEPTION'
              AND subledger_domain = 'PREPAYMENT'
              AND observation_type = 'QUARANTINED_DUPLICATE_SOURCE'
            """
        ).fetchone()[0]
        if argus_exception_count != 1:
            raise FinanceDataSubstrateError(
                "Argus A2.2b exception population differs"
            )


def _verify_a23_multi_entity_close_controls(database_path: Path) -> None:
    """Independently recalculate A2.3 source, close, and statement controls."""

    with duckdb.connect(str(database_path), read_only=True) as connection:
        columns = tuple(
            row[0]
            for row in connection.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'bronze' "
                "AND table_name = 'intercompany__intercompany_transactions' "
                "AND column_name NOT LIKE '\\_%' ESCAPE '\\' "
                "ORDER BY ordinal_position"
            ).fetchall()
        )
        quoted = ", ".join(f'"{column}"' for column in columns)
        source_rows = connection.execute(
            f"SELECT {quoted} "
            "FROM bronze.intercompany__intercompany_transactions"
        ).fetchall()
        expected_hashes: dict[str, str] = {}
        for values in source_rows:
            payload = dict(zip(columns, values, strict=True))
            source_hash = sha256_bytes(canonical_json_bytes(payload))
            expected_hashes[str(payload["seller_source_record_ref"])] = source_hash
            expected_hashes[str(payload["buyer_source_record_ref"])] = source_hash
        actual_hashes = {
            source_ref: source_hash
            for source_ref, source_hash in connection.execute(
                "SELECT source_record_ref, source_record_hash "
                "FROM bronze.hermes__source_admission_results "
                "WHERE source_dataset_path = "
                "'intercompany/intercompany_transactions.csv'"
            ).fetchall()
        }
        if actual_hashes != expected_hashes:
            raise FinanceDataSubstrateError(
                "A2.3 Hermes bilateral source hashes differ"
            )

        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.hermes__source_admission_results AS admission
            LEFT JOIN bronze.events__business_events AS event
              ON admission.candidate_business_event_ref = event.business_event_ref
            WHERE admission.source_dataset_path =
                  'intercompany/intercompany_transactions.csv'
              AND (admission.admission_decision <> 'ADMITTED'
                   OR event.business_event_ref IS NULL
                   OR event.source_record_ref <> admission.source_record_ref
                   OR event.legal_entity_id <> admission.legal_entity_id)
            """,
            "intercompany source does not resolve through Hermes to its event",
        )
        _assert_zero(
            connection,
            """
            WITH admitted AS (
                SELECT transaction.intercompany_transaction_id,
                       COUNT(admission.source_record_ref) AS admission_count
                FROM bronze.intercompany__intercompany_transactions AS transaction
                LEFT JOIN bronze.hermes__source_admission_results AS admission
                  ON admission.source_record_ref IN (
                      transaction.seller_source_record_ref,
                      transaction.buyer_source_record_ref
                  )
                GROUP BY transaction.intercompany_transaction_id
            )
            SELECT COUNT(*) FROM admitted WHERE admission_count <> 2
            """,
            "intercompany transaction lacks two independent source admissions",
        )
        _assert_zero(
            connection,
            """
            WITH expected AS (
                SELECT period_id, seller_entity_id, buyer_entity_id,
                       SUM(CAST(amount_minor AS HUGEINT)) OVER (
                           PARTITION BY seller_entity_id, buyer_entity_id
                           ORDER BY period_id
                       ) AS closing_minor
                FROM bronze.intercompany__intercompany_transactions
            )
            SELECT COUNT(*)
            FROM bronze.intercompany__intercompany_balances AS balance
            FULL OUTER JOIN expected
              USING (period_id, seller_entity_id, buyer_entity_id)
            WHERE balance.period_id IS NULL OR expected.period_id IS NULL
               OR CAST(balance.seller_receivable_minor AS HUGEINT)
                    <> expected.closing_minor
               OR CAST(balance.buyer_payable_minor AS HUGEINT)
                    <> expected.closing_minor
               OR CAST(balance.confirmed_difference_minor AS HUGEINT) <> 0
               OR balance.confirmation_status <> 'CONFIRMED'
            """,
            "bilateral intercompany confirmation does not replay",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.accounting__accounting_events AS accounting_event
            JOIN bronze.events__business_events AS business_event
              ON accounting_event.accounting_event_ref =
                 business_event.business_event_ref
            """,
            "accounting event re-entered business-event identity space",
        )
        _assert_zero(
            connection,
            """
            WITH elimination AS (
                SELECT source_intercompany_transaction_id,
                       COUNT(*) AS line_count,
                       SUM(CAST(debit_minor AS HUGEINT)) AS debits,
                       SUM(CAST(credit_minor AS HUGEINT)) AS credits
                FROM bronze.consolidation__elimination_journal_lines
                GROUP BY source_intercompany_transaction_id
            )
            SELECT COUNT(*)
            FROM bronze.intercompany__intercompany_transactions AS source
            FULL OUTER JOIN elimination
              ON source.intercompany_transaction_id =
                 elimination.source_intercompany_transaction_id
            WHERE source.intercompany_transaction_id IS NULL
               OR elimination.source_intercompany_transaction_id IS NULL
               OR elimination.line_count <> 4
               OR elimination.debits <> 2 * CAST(source.amount_minor AS HUGEINT)
               OR elimination.credits <> 2 * CAST(source.amount_minor AS HUGEINT)
            """,
            "consolidation elimination does not reproduce source transaction",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.consolidation__elimination_journal_lines AS line
            LEFT JOIN bronze.accounting__accounting_events AS event
              ON line.accounting_event_ref = event.accounting_event_ref
            LEFT JOIN bronze.intercompany__intercompany_transactions AS source
              ON line.source_intercompany_transaction_id =
                 source.intercompany_transaction_id
            WHERE event.accounting_event_type <>
                  'CONSOLIDATION_ELIMINATION_POSTED'
               OR source.intercompany_transaction_id IS NULL
               OR line.period_id <> event.period_id
               OR line.period_id <> source.period_id
            """,
            "elimination lineage does not resolve to source and accounting event",
        )
        _assert_zero(
            connection,
            """
            WITH period_source AS (
                SELECT period_id,
                       SUM(CAST(amount_minor AS HUGEINT)) AS total_minor,
                       SUM(CASE WHEN buyer_expense_account_id = '6000'
                           THEN CAST(amount_minor AS HUGEINT) ELSE 0 END) AS rnd_minor,
                       SUM(CASE WHEN buyer_expense_account_id = '6200'
                           THEN CAST(amount_minor AS HUGEINT) ELSE 0 END) AS ga_minor
                FROM bronze.intercompany__intercompany_transactions
                GROUP BY period_id
            ), period_elimination AS (
                SELECT period_id,
                       SUM(CASE WHEN account_id = '1150'
                           THEN CAST(credit_minor AS HUGEINT) ELSE 0 END) AS ar_credit,
                       SUM(CASE WHEN account_id = '2050'
                           THEN CAST(debit_minor AS HUGEINT) ELSE 0 END) AS ap_debit,
                       SUM(CASE WHEN account_id = '4100'
                           THEN CAST(debit_minor AS HUGEINT) ELSE 0 END) AS rev_debit,
                       SUM(CASE WHEN account_id = '6000'
                           THEN CAST(credit_minor AS HUGEINT) ELSE 0 END) AS rnd_credit,
                       SUM(CASE WHEN account_id = '6200'
                           THEN CAST(credit_minor AS HUGEINT) ELSE 0 END) AS ga_credit
                FROM bronze.consolidation__elimination_journal_lines
                GROUP BY period_id
            )
            SELECT COUNT(*)
            FROM period_source JOIN period_elimination USING (period_id)
            WHERE total_minor <> ar_credit OR total_minor <> ap_debit
               OR total_minor <> rev_debit OR rnd_minor <> rnd_credit
               OR ga_minor <> ga_credit
            """,
            "period consolidation elimination amount differs",
        )

        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.accounting__statutory_trial_balance
            WHERE CAST(opening_balance_minor AS HUGEINT)
                  + CAST(debit_activity_minor AS HUGEINT)
                  - CAST(credit_activity_minor AS HUGEINT)
                  + CAST(elimination_debit_minor AS HUGEINT)
                  - CAST(elimination_credit_minor AS HUGEINT)
                  <> CAST(closing_balance_minor AS HUGEINT)
               OR close_status <> 'HARD_CLOSED'
            """,
            "statutory trial-balance rollforward differs",
        )
        _assert_zero(
            connection,
            """
            WITH continuity AS (
                SELECT period_id, scope_id, account_id,
                       CAST(opening_balance_minor AS HUGEINT) AS opening_balance,
                       LAG(CAST(closing_balance_minor AS HUGEINT)) OVER (
                           PARTITION BY scope_id, account_id ORDER BY period_id
                       ) AS prior_closing
                FROM bronze.accounting__statutory_trial_balance
            )
            SELECT COUNT(*) FROM continuity
            WHERE prior_closing IS NOT NULL AND opening_balance <> prior_closing
            """,
            "statutory trial-balance continuity differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*) FROM (
                SELECT period_id, scope_id
                FROM bronze.accounting__statutory_trial_balance
                GROUP BY period_id, scope_id
                HAVING SUM(CAST(closing_balance_minor AS HUGEINT)) <> 0
                    OR COUNT(*) <> (
                        SELECT COUNT(*) FROM bronze.accounting__chart_of_accounts
                    )
            )
            """,
            "statutory trial balance is incomplete or unbalanced",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.accounting__statutory_trial_balance
            WHERE scope_id = 'NEXUS-GROUP'
              AND account_id IN ('1150', '2050')
              AND CAST(closing_balance_minor AS HUGEINT) <> 0
            """,
            "consolidated intercompany balance was not eliminated",
        )

        tb_columns = tuple(
            row[0]
            for row in connection.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'bronze' "
                "AND table_name = 'accounting__statutory_trial_balance' "
                "AND column_name NOT LIKE '\\_%' ESCAPE '\\' "
                "ORDER BY ordinal_position"
            ).fetchall()
        )
        tb_quoted = ", ".join(f'"{column}"' for column in tb_columns)
        tb_rows = connection.execute(
            f"SELECT {tb_quoted} "
            "FROM bronze.accounting__statutory_trial_balance "
            "ORDER BY period_id, scope_id, account_id"
        ).fetchall()
        grouped_rows: dict[tuple[str, str], list[dict[str, str]]] = {}
        for values in tb_rows:
            row = {
                key: str(value)
                for key, value in zip(tb_columns, values, strict=True)
            }
            grouped_rows.setdefault((row["period_id"], row["scope_id"]), []).append(
                row
            )
        expected_digests = {
            key: sha256_bytes(canonical_json_bytes(value))
            for key, value in grouped_rows.items()
        }
        digest_rows = connection.execute(
            "SELECT DISTINCT period_id, scope_id, source_trial_balance_digest "
            "FROM ("
            "SELECT period_id, scope_id, source_trial_balance_digest "
            "FROM bronze.accounting__statutory_statement_lines UNION ALL "
            "SELECT period_id, scope_id, source_trial_balance_digest "
            "FROM bronze.accounting__retained_earnings_bridge UNION ALL "
            "SELECT period_id, scope_id, source_trial_balance_digest "
            "FROM bronze.accounting__cash_flow_reconciliation)"
        ).fetchall()
        actual_digests: dict[tuple[str, str], str] = {}
        for period_id, scope_id, digest in digest_rows:
            key = (period_id, scope_id)
            if key in actual_digests and actual_digests[key] != digest:
                raise FinanceDataSubstrateError(
                    "A2.3 published products disagree on trial-balance digest"
                )
            actual_digests[key] = digest
        if actual_digests != expected_digests:
            raise FinanceDataSubstrateError(
                "A2.3 statement lineage digest does not authenticate trial balance"
            )

        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.accounting__retained_earnings_bridge AS retained
            JOIN bronze.accounting__statutory_statement_lines AS statement
              ON retained.period_id = statement.period_id
             AND retained.scope_id = statement.scope_id
             AND statement.statement_class = 'INCOME_STATEMENT'
             AND statement.statement_line = 'net_income'
            WHERE CAST(retained.opening_retained_earnings_minor AS HUGEINT)
                  + CAST(retained.net_income_minor AS HUGEINT)
                  - CAST(retained.dividends_minor AS HUGEINT)
                  + CAST(retained.other_equity_movements_minor AS HUGEINT)
                  <> CAST(retained.closing_retained_earnings_minor AS HUGEINT)
               OR CAST(retained.net_income_minor AS HUGEINT)
                  <> CAST(statement.amount_minor AS HUGEINT)
               OR retained.reconciliation_status <> 'RECONCILED'
            """,
            "retained earnings does not roll or match net income",
        )
        _assert_zero(
            connection,
            """
            WITH continuity AS (
                SELECT period_id, scope_id,
                       CAST(opening_retained_earnings_minor AS HUGEINT) AS opening_re,
                       LAG(CAST(closing_retained_earnings_minor AS HUGEINT)) OVER (
                           PARTITION BY scope_id ORDER BY period_id
                       ) AS prior_re
                FROM bronze.accounting__retained_earnings_bridge
            )
            SELECT COUNT(*) FROM continuity
            WHERE prior_re IS NOT NULL AND opening_re <> prior_re
            """,
            "retained earnings prior-period continuity differs",
        )
        _assert_zero(
            connection,
            """
            WITH balance_sheet AS (
                SELECT period_id, scope_id,
                       MAX(CASE WHEN statement_line = 'total_assets'
                           THEN CAST(amount_minor AS HUGEINT) END) AS assets,
                       MAX(CASE WHEN statement_line =
                           'total_liabilities_and_equity'
                           THEN CAST(amount_minor AS HUGEINT) END) AS liabilities_equity
                FROM bronze.accounting__statutory_statement_lines
                WHERE statement_class = 'BALANCE_SHEET'
                GROUP BY period_id, scope_id
            )
            SELECT COUNT(*) FROM balance_sheet
            WHERE assets IS NULL OR liabilities_equity IS NULL
               OR assets <> liabilities_equity
            """,
            "published balance sheet equation differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.accounting__cash_flow_reconciliation
            WHERE CAST(opening_cash_minor AS HUGEINT)
                  + CAST(operating_cash_flow_minor AS HUGEINT)
                  + CAST(investing_cash_flow_minor AS HUGEINT)
                  + CAST(financing_cash_flow_minor AS HUGEINT)
                  + CAST(fx_and_other_movement_minor AS HUGEINT)
                  <> CAST(closing_cash_minor AS HUGEINT)
               OR CAST(statement_cash_movement_minor AS HUGEINT)
                  <> CAST(operating_cash_flow_minor AS HUGEINT)
                     + CAST(investing_cash_flow_minor AS HUGEINT)
                     + CAST(financing_cash_flow_minor AS HUGEINT)
                     + CAST(fx_and_other_movement_minor AS HUGEINT)
               OR CAST(unreconciled_difference_minor AS HUGEINT) <> 0
               OR reconciliation_status <> 'RECONCILED'
            """,
            "published cash-flow identity differs",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.accounting__cash_flow_reconciliation AS cash_flow
            JOIN bronze.accounting__statutory_trial_balance AS trial_balance
              ON cash_flow.period_id = trial_balance.period_id
             AND cash_flow.scope_id = trial_balance.scope_id
             AND trial_balance.account_id = '1000'
            WHERE CAST(cash_flow.closing_cash_minor AS HUGEINT)
                  <> CAST(trial_balance.closing_balance_minor AS HUGEINT)
            """,
            "cash-flow closing cash differs from trial balance",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.accounting__monthly_close_status AS close
            LEFT JOIN bronze.accounting__accounting_events AS soft
              ON close.soft_close_accounting_event_ref = soft.accounting_event_ref
            LEFT JOIN bronze.accounting__accounting_events AS hard
              ON close.hard_close_accounting_event_ref = hard.accounting_event_ref
            LEFT JOIN bronze.accounting__accounting_events AS publication
              ON close.reporting_publication_accounting_event_ref =
                 publication.accounting_event_ref
            WHERE close.close_status <> 'HARD_CLOSED'
               OR close.trial_balance_status <> 'BALANCED'
               OR close.statement_status <> 'PUBLISHED'
               OR soft.accounting_event_type <> 'SOFT_CLOSE_COMPLETED'
               OR hard.accounting_event_type <> 'HARD_CLOSE_COMPLETED'
               OR publication.accounting_event_type <>
                  'REPORTING_VERSION_PUBLISHED'
               OR soft.period_id <> close.period_id
               OR hard.period_id <> close.period_id
               OR publication.period_id <> close.period_id
               OR soft.legal_entity_id <> close.legal_entity_id
               OR hard.legal_entity_id <> close.legal_entity_id
               OR publication.legal_entity_id <> close.legal_entity_id
            """,
            "hard-close state does not resolve to lifecycle events",
        )
        close_count = connection.execute(
            "SELECT COUNT(*) FROM bronze.accounting__monthly_close_status"
        ).fetchone()[0]
        reconciliation_count = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.governance__statutory_reconciliation_results "
            "WHERE status = 'PASS' "
            "AND CAST(difference_minor AS HUGEINT) = 0 "
            "AND first_failure_ref = ''"
        ).fetchone()[0]
        if close_count != 66 * 3 or reconciliation_count != close_count * 5:
            raise FinanceDataSubstrateError(
                "A2.3 close or Argus reconciliation population differs"
            )


def _verify_a24_ratification_controls(database_path: Path) -> None:
    """Recompute the A2.4 formation, cross-statement, close, and lineage gates."""

    with duckdb.connect(str(database_path), read_only=True) as connection:
        _assert_zero(
            connection,
            """
            WITH first_period AS (
                SELECT MIN(period_id) AS period_id
                FROM bronze.reference__periods
                WHERE LOWER(is_actual_period) = 'true'
            )
            SELECT COUNT(*)
            FROM bronze.accounting__statutory_trial_balance AS trial_balance
            JOIN first_period USING (period_id)
            WHERE CAST(opening_balance_minor AS HUGEINT) <> 0
            """,
            "formation trial balance does not start from zero",
        )
        _assert_zero(
            connection,
            """
            WITH entity_gl AS (
                SELECT period_id, legal_entity_id AS scope_id, account_id,
                       SUM(CAST(debit_minor AS HUGEINT)) AS debit_minor,
                       SUM(CAST(credit_minor AS HUGEINT)) AS credit_minor
                FROM bronze.accounting__source_gl_journal_lines
                GROUP BY period_id, legal_entity_id, account_id
            ), entity_tb AS (
                SELECT period_id, scope_id, account_id,
                       CAST(debit_activity_minor AS HUGEINT) AS debit_minor,
                       CAST(credit_activity_minor AS HUGEINT) AS credit_minor
                FROM bronze.accounting__statutory_trial_balance
                WHERE scope_id IN ('NEXUS-UK', 'NEXUS-US')
            )
            SELECT COUNT(*)
            FROM entity_tb
            FULL OUTER JOIN entity_gl USING (period_id, scope_id, account_id)
            WHERE entity_tb.period_id IS NULL
               OR entity_tb.debit_minor <> COALESCE(entity_gl.debit_minor, 0)
               OR entity_tb.credit_minor <> COALESCE(entity_gl.credit_minor, 0)
            """,
            "entity trial-balance activity does not replay from source GL",
        )
        _assert_zero(
            connection,
            """
            WITH entity_activity AS (
                SELECT period_id, account_id,
                       SUM(CAST(debit_activity_minor AS HUGEINT)) AS debit_minor,
                       SUM(CAST(credit_activity_minor AS HUGEINT)) AS credit_minor
                FROM bronze.accounting__statutory_trial_balance
                WHERE scope_id IN ('NEXUS-UK', 'NEXUS-US')
                GROUP BY period_id, account_id
            ), elimination AS (
                SELECT period_id, account_id,
                       SUM(CAST(debit_minor AS HUGEINT)) AS debit_minor,
                       SUM(CAST(credit_minor AS HUGEINT)) AS credit_minor
                FROM bronze.consolidation__elimination_journal_lines
                GROUP BY period_id, account_id
            )
            SELECT COUNT(*)
            FROM bronze.accounting__statutory_trial_balance AS group_tb
            LEFT JOIN entity_activity
              ON group_tb.period_id = entity_activity.period_id
             AND group_tb.account_id = entity_activity.account_id
            LEFT JOIN elimination
              ON group_tb.period_id = elimination.period_id
             AND group_tb.account_id = elimination.account_id
            WHERE group_tb.scope_id = 'NEXUS-GROUP'
              AND (
                    CAST(group_tb.debit_activity_minor AS HUGEINT)
                        <> COALESCE(entity_activity.debit_minor, 0)
                    OR CAST(group_tb.credit_activity_minor AS HUGEINT)
                        <> COALESCE(entity_activity.credit_minor, 0)
                    OR CAST(group_tb.elimination_debit_minor AS HUGEINT)
                        <> COALESCE(elimination.debit_minor, 0)
                    OR CAST(group_tb.elimination_credit_minor AS HUGEINT)
                        <> COALESCE(elimination.credit_minor, 0)
                  )
            """,
            "group trial balance does not replay entity and elimination activity",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.accounting__source_gl_journal_lines AS gl
            LEFT JOIN bronze.events__business_events AS event
              USING (business_event_ref)
            WHERE event.business_event_ref IS NULL
               OR gl.source_record_ref = ''
               OR gl.source_record_ref <> event.source_record_ref
               OR gl.legal_entity_id <> event.legal_entity_id
               OR gl.period_id <> SUBSTR(event.effective_date, 1, 7)
            """,
            "trial-balance source GL does not resolve to exact causal source identity",
        )
        _assert_zero(
            connection,
            """
            WITH source_refs AS (
                SELECT invoice_id AS source_ref FROM bronze.billing__invoices
                UNION SELECT payment_id FROM bronze.billing__payments
                UNION SELECT payroll_line_id
                    FROM bronze.workforce__payroll_expense_lines
                UNION SELECT vendor_invoice_id
                    FROM bronze.procurement__vendor_invoices
                UNION SELECT schedule_id
                    FROM bronze.revenue__revenue_recognition_schedule
                UNION SELECT vendor_payment_id
                    FROM bronze.procurement__vendor_payments
                UNION SELECT capital_invoice_id || '#APPROVAL'
                    FROM bronze.procurement__capital_invoices
                UNION SELECT payment_ref
                    FROM bronze.procurement__capital_invoices
                    WHERE payment_ref <> ''
                UNION SELECT asset_lifecycle_event_id
                    FROM bronze.fixed_assets__asset_lifecycle_events
                UNION SELECT accrual_source_event_id
                    FROM bronze.working_capital__accrual_source_events
                UNION SELECT prepayment_source_event_id
                    FROM bronze.working_capital__prepayment_source_events
                UNION SELECT lease_lifecycle_event_id
                    FROM bronze.leases__lease_lifecycle_events
                UNION SELECT tax_calculation_input_id || '#DEFERRED'
                    FROM bronze.tax__tax_calculation_inputs
                UNION SELECT seller_source_record_ref
                    FROM bronze.intercompany__intercompany_transactions
                UNION SELECT buyer_source_record_ref
                    FROM bronze.intercompany__intercompany_transactions
                UNION SELECT event.source_record_ref
                    FROM bronze.equity__equity_movements AS movement
                    JOIN bronze.events__business_events AS event
                      USING (business_event_ref)
                UNION SELECT event.source_record_ref
                    FROM bronze.treasury__debt_schedule AS schedule,
                         UNNEST(STRING_SPLIT(schedule.business_event_refs, ','))
                            AS refs(ref)
                    JOIN bronze.events__business_events AS event
                      ON refs.ref = event.business_event_ref
                    WHERE schedule.business_event_refs <> ''
                UNION SELECT event.source_record_ref
                    FROM bronze.fixed_assets__fixed_asset_register AS asset
                    JOIN bronze.events__business_events AS event
                      ON asset.acquisition_business_event_ref =
                         event.business_event_ref
                UNION SELECT event.source_record_ref
                    FROM bronze.leases__lease_schedule AS schedule,
                         UNNEST(STRING_SPLIT(schedule.business_event_refs, ','))
                            AS refs(ref)
                    JOIN bronze.events__business_events AS event
                      ON refs.ref = event.business_event_ref
                    WHERE schedule.business_event_refs <> ''
            )
            SELECT COUNT(*)
            FROM bronze.events__business_events AS event
            LEFT JOIN source_refs
              ON event.source_record_ref = source_refs.source_ref
            WHERE source_refs.source_ref IS NULL
            """,
            "business event source identity does not resolve to an emitted record",
        )
        _assert_zero(
            connection,
            """
            WITH account_lines AS (
                SELECT DISTINCT statement_class, statement_line
                FROM bronze.accounting__chart_of_accounts
            ), permitted_derived(statement_class, statement_line) AS (
                VALUES
                    ('INCOME_STATEMENT', 'net_income'),
                    ('BALANCE_SHEET', 'total_assets'),
                    ('BALANCE_SHEET', 'total_liabilities'),
                    ('BALANCE_SHEET', 'total_equity'),
                    ('BALANCE_SHEET', 'total_liabilities_and_equity'),
                    ('CASH_FLOW', 'net_income'),
                    ('CASH_FLOW', 'operating_cash_flow'),
                    ('CASH_FLOW', 'investing_cash_flow'),
                    ('CASH_FLOW', 'financing_cash_flow'),
                    ('CASH_FLOW', 'net_change_in_cash'),
                    ('CASH_FLOW', 'closing_cash')
            )
            SELECT COUNT(*)
            FROM bronze.accounting__statutory_statement_lines AS statement
            LEFT JOIN account_lines USING (statement_class, statement_line)
            LEFT JOIN permitted_derived USING (statement_class, statement_line)
            WHERE account_lines.statement_line IS NULL
              AND permitted_derived.statement_line IS NULL
            """,
            "statement line lacks an account mapping or registered derivation",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.accounting__statutory_statement_lines AS statement
            LEFT JOIN (
                SELECT DISTINCT period_id, scope_id, reporting_version_ref
                FROM bronze.accounting__statutory_trial_balance
            ) AS trial_balance
              USING (period_id, scope_id, reporting_version_ref)
            LEFT JOIN bronze.accounting__monthly_close_status AS close
              ON statement.period_id = close.period_id
             AND statement.scope_id = close.legal_entity_id
             AND statement.reporting_version_ref = close.reporting_version_ref
            WHERE trial_balance.period_id IS NULL OR close.period_id IS NULL
            """,
            "statement reporting version does not resolve to trial balance and close",
        )
        _assert_zero(
            connection,
            """
            WITH income AS (
                SELECT period_id, scope_id, reporting_version_ref,
                       CAST(amount_minor AS HUGEINT) AS net_income_minor
                FROM bronze.accounting__statutory_statement_lines
                WHERE statement_class = 'INCOME_STATEMENT'
                  AND statement_line = 'net_income'
            ), cash_flow AS (
                SELECT period_id, scope_id, reporting_version_ref,
                       CAST(amount_minor AS HUGEINT) AS net_income_minor
                FROM bronze.accounting__statutory_statement_lines
                WHERE statement_class = 'CASH_FLOW'
                  AND statement_line = 'net_income'
            )
            SELECT COUNT(*)
            FROM income
            FULL OUTER JOIN cash_flow
              USING (period_id, scope_id, reporting_version_ref)
            FULL OUTER JOIN bronze.accounting__retained_earnings_bridge AS retained
              USING (period_id, scope_id, reporting_version_ref)
            WHERE income.period_id IS NULL OR cash_flow.period_id IS NULL
               OR retained.period_id IS NULL
               OR income.net_income_minor <> cash_flow.net_income_minor
               OR income.net_income_minor
                    <> CAST(retained.net_income_minor AS HUGEINT)
            """,
            "net income does not agree across income, cash flow, and retained earnings",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*)
            FROM bronze.accounting__retained_earnings_bridge
            WHERE CAST(dividends_minor AS HUGEINT) <> 0
               OR CAST(other_equity_movements_minor AS HUGEINT) <> 0
            """,
            "retained earnings contains an untraced dividend or reserve movement",
        )
        _assert_zero(
            connection,
            """
            WITH required AS (
                SELECT close.period_id, close.legal_entity_id,
                       close.hard_close_accounting_event_ref,
                       reconciliation.reconciliation_ref
                FROM bronze.accounting__monthly_close_status AS close
                JOIN bronze.governance__statutory_reconciliation_results
                    AS reconciliation
                  ON close.period_id = reconciliation.period_id
                 AND close.legal_entity_id = reconciliation.scope_id
                 AND close.reporting_version_ref =
                     reconciliation.reporting_version_ref
                WHERE reconciliation.status = 'PASS'
                  AND CAST(reconciliation.difference_minor AS HUGEINT) = 0
            ), hard_sources AS (
                SELECT event.accounting_event_ref, refs.ref AS source_ref
                FROM bronze.accounting__accounting_events AS event,
                     UNNEST(STRING_SPLIT(event.source_record_refs, ',')) AS refs(ref)
                WHERE event.accounting_event_type = 'HARD_CLOSE_COMPLETED'
            )
            SELECT COUNT(*)
            FROM required
            LEFT JOIN hard_sources
              ON required.hard_close_accounting_event_ref =
                 hard_sources.accounting_event_ref
             AND required.reconciliation_ref = hard_sources.source_ref
            WHERE hard_sources.source_ref IS NULL
            """,
            "hard-close event does not cite every passed prerequisite control",
        )
        _assert_zero(
            connection,
            """
            SELECT COUNT(*) FROM (
                SELECT close.period_id, close.legal_entity_id
                FROM bronze.accounting__monthly_close_status AS close
                LEFT JOIN bronze.governance__statutory_reconciliation_results
                    AS reconciliation
                  ON close.period_id = reconciliation.period_id
                 AND close.legal_entity_id = reconciliation.scope_id
                 AND close.reporting_version_ref =
                     reconciliation.reporting_version_ref
                WHERE close.close_status = 'HARD_CLOSED'
                GROUP BY close.period_id, close.legal_entity_id
                HAVING COUNT(reconciliation.reconciliation_ref) <> 5
                    OR COUNT(*) FILTER (
                        WHERE reconciliation.status = 'PASS'
                          AND CAST(reconciliation.difference_minor AS HUGEINT) = 0
                    ) <> 5
            )
            """,
            "hard-close prerequisite population is incomplete",
        )


def _readme(request: FinanceDataBuildRequest) -> str:
    statutory_contract = (
        f"\nStatutory contract: {request.statutory_contract_version}\n"
        if request.statutory_contract_version == "A2.4"
        else ""
    )
    return (
        "# Atlas Finance Data Substrate\n\n"
        "Synthetic demonstration data only. No client or employer data.\n\n"
        f"Data reference: {request.data_ref}\n\n"
        f"Scale profile: {request.scale_profile}\n\n"
        f"Actual history: {request.history_start.isoformat()} to "
        f"{request.actuals_end.isoformat()}\n\n"
        f"{statutory_contract}"
        "The raw tree contains source-domain records, explicitly classified "
        "module-derived records, and declared intentional defects. The DuckDB "
        "Bronze database preserves every CSV value as text and adds only "
        "ingestion metadata. Loading a row into Bronze does not change its truth "
        "class or owner. Only rows classified as BUSINESS_EVENT may enter "
        "posting-rule evaluation. Monetary fields use integer minor units plus "
        "explicit currency.\n"
    )


class FinanceDataSubstrateService:
    """Application service for Atlas source build and independent verification."""

    def build(self, request: FinanceDataBuildRequest) -> FinanceDataBuildResult:
        request.validate()
        final_path = request.output_path.resolve()
        if final_path.exists():
            raise FileExistsError(final_path)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        staging = final_path.parent / f".{final_path.name}.staging-{uuid4().hex}"
        staging.mkdir(parents=False, exist_ok=False)
        try:
            raw_root = staging / "raw"
            raw_root.mkdir()
            population = FinancePopulationGenerator(
                request=request,
                profile=SCALE_PROFILES[request.scale_profile],
                raw_root=raw_root,
            ).generate()
            dataset_entries = []
            for definition in ALL_SOURCE_DATASETS:
                path = raw_root / definition.path
                dataset_entries.append(
                    {
                        "path": definition.path,
                        "source_system": definition.source_system,
                        "record_class": definition.record_class,
                        "grain": definition.grain,
                        "columns": list(definition.columns),
                        "row_count": population.row_counts[definition.path],
                        "sha256": _stream_sha256(path),
                        "byte_count": path.stat().st_size,
                    }
                )
            source_manifest = {
                "contract_version": "atlas-finance-source-manifest@v1",
                "data_ref": request.data_ref,
                "built_at": request.built_at,
                "synthetic_data": True,
                "synthetic_data_notice": (
                    "Synthetic demonstration data only; no client or employer data."
                ),
                "scale_profile": request.scale_profile,
                "seed": request.seed,
                "history_start": request.history_start.isoformat(),
                "actuals_end": request.actuals_end.isoformat(),
                "history_month_count": population.history_month_count,
                "total_period_count": population.total_period_count,
                "reporting_currency": request.reporting_currency,
                "money_contract": "INTEGER_MINOR_UNITS_PLUS_CURRENCY",
                "posting_causality": "BUSINESS_EVENT_ONLY",
                "dataset_count": len(dataset_entries),
                "source_row_count": sum(population.row_counts.values()),
                "defect_count": population.defect_count,
                "datasets": dataset_entries,
            }
            if request.statutory_contract_version == "A2.4":
                source_manifest["statutory_contract_version"] = "A2.4"
            _write_json(staging / SOURCE_MANIFEST_PATH, source_manifest)

            bronze = build_bronze_database(
                raw_root=raw_root,
                database_path=staging / DATABASE_RELATIVE_PATH,
                source_data_ref=request.data_ref,
                ingested_at=request.built_at,
            )
            bronze_manifest = self._bronze_manifest(request, bronze)
            _write_json(staging / BRONZE_MANIFEST_PATH, bronze_manifest)
            (staging / README_PATH).write_text(
                _readme(request), encoding="ascii", newline="\n"
            )

            canonical_paths = (
                README_PATH,
                SOURCE_MANIFEST_PATH,
                *(f"raw/{item.path}" for item in ALL_SOURCE_DATASETS),
            )
            checksum_entries = []
            for relative_path in sorted(canonical_paths):
                path = staging / relative_path
                checksum_entries.append(
                    {
                        "path": relative_path,
                        "sha256": _stream_sha256(path),
                        "byte_count": path.stat().st_size,
                    }
                )
            checksum_value = {
                "contract_version": "atlas-finance-checksum-ledger@v1",
                "entries": checksum_entries,
            }
            checksum_bytes = canonical_json_bytes(checksum_value)
            (staging / CHECKSUMS_PATH).write_bytes(checksum_bytes)
            package_digest = sha256_bytes(checksum_bytes)
            (staging / DETACHED_DIGEST_PATH).write_text(
                package_digest + "\n", encoding="ascii", newline="\n"
            )
            self.verify(staging, expected_digest=package_digest)
            _atomic_publish(staging, final_path)
            return FinanceDataBuildResult(
                data_ref=request.data_ref,
                output_path=final_path,
                package_digest=package_digest,
                scale_profile=request.scale_profile,
                dataset_count=len(dataset_entries),
                source_row_count=sum(population.row_counts.values()),
                bronze_table_count=len(bronze.tables),
                defect_count=population.defect_count,
                history_month_count=population.history_month_count,
            )
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            raise

    @staticmethod
    def _bronze_manifest(
        request: FinanceDataBuildRequest, bronze: BronzeBuildResult
    ) -> dict[str, object]:
        return {
            "contract_version": "atlas-bronze-manifest@v1",
            "data_ref": request.data_ref,
            "database_path": DATABASE_RELATIVE_PATH,
            "database_sha256": bronze.database_sha256,
            "database_byte_count": bronze.database_byte_count,
            "engine": "DUCKDB",
            "engine_version": duckdb.__version__,
            "loader_contract": "ATLAS-BRONZE-LOSSLESS@v1",
            "read_only_consumer_required": True,
            "table_count": len(bronze.tables),
            "tables": [
                {
                    "source_path": item.source_path,
                    "table_name": item.table_name,
                    "source_sha256": item.source_sha256,
                    "row_count": item.row_count,
                    "source_columns": list(item.source_columns),
                }
                for item in bronze.tables
            ],
        }

    def reproduce(
        self, request: FinanceDataReproduceRequest
    ) -> FinanceDataReproduceResult:
        """Rebuild canonical source bytes and logically reproduce Bronze."""

        source_root = request.source_package_path.resolve()
        reproduction_root = request.reproduction_output_path.resolve()
        if source_root == reproduction_root:
            raise FinanceDataSubstrateError(
                "reproduction output must differ from source package"
            )
        source_manifest = _read_canonical_json(source_root / SOURCE_MANIFEST_PATH)
        source_digest = (
            source_root / DETACHED_DIGEST_PATH
        ).read_text(encoding="ascii").strip()
        expected_digest = request.expected_digest or source_digest
        self.verify(source_root, expected_digest=expected_digest)
        statutory_contract_version = str(
            source_manifest.get("statutory_contract_version", "A2.3")
        )
        built = self.build(
            FinanceDataBuildRequest(
                data_ref=str(source_manifest["data_ref"]),
                output_path=reproduction_root,
                built_at=str(source_manifest["built_at"]),
                scale_profile=str(source_manifest["scale_profile"]),
                seed=int(source_manifest["seed"]),
                history_start=date.fromisoformat(
                    str(source_manifest["history_start"])
                ),
                actuals_end=date.fromisoformat(str(source_manifest["actuals_end"])),
                reporting_currency=str(source_manifest["reporting_currency"]),
                statutory_contract_version=statutory_contract_version,
            )
        )
        if built.package_digest != source_digest:
            raise FinanceDataSubstrateError(
                "reproduced canonical package digest differs"
            )
        source_checksums = _read_canonical_json(source_root / CHECKSUMS_PATH)
        reproduced_checksums = _read_canonical_json(
            reproduction_root / CHECKSUMS_PATH
        )
        if source_checksums != reproduced_checksums:
            raise FinanceDataSubstrateError("reproduced checksum ledger differs")
        entries = source_checksums.get("entries")
        if not isinstance(entries, list):
            raise FinanceDataSubstrateError("source checksum entries are missing")
        for entry in entries:
            if not isinstance(entry, dict):
                raise FinanceDataSubstrateError("source checksum entry is invalid")
            relative_path = str(entry["path"])
            if (source_root / relative_path).read_bytes() != (
                reproduction_root / relative_path
            ).read_bytes():
                raise FinanceDataSubstrateError(
                    f"reproduced canonical bytes differ: {relative_path}"
                )
        for relative_path in (CHECKSUMS_PATH, DETACHED_DIGEST_PATH):
            if (source_root / relative_path).read_bytes() != (
                reproduction_root / relative_path
            ).read_bytes():
                raise FinanceDataSubstrateError(
                    f"reproduced seal bytes differ: {relative_path}"
                )
        source_bronze = _read_canonical_json(source_root / BRONZE_MANIFEST_PATH)
        reproduced_bronze = _read_canonical_json(
            reproduction_root / BRONZE_MANIFEST_PATH
        )
        for value in (source_bronze, reproduced_bronze):
            value.pop("database_sha256", None)
            value.pop("database_byte_count", None)
        if source_bronze != reproduced_bronze:
            raise FinanceDataSubstrateError(
                "reproduced logical Bronze manifest differs"
            )
        reproduced = self.verify(
            reproduction_root, expected_digest=expected_digest
        )
        return FinanceDataReproduceResult(
            data_ref=built.data_ref,
            source_package_digest=source_digest,
            reproduced_package_digest=built.package_digest,
            canonical_file_count=len(entries) + 2,
            checked_dataset_count=reproduced.checked_dataset_count,
            checked_source_row_count=reproduced.checked_source_row_count,
            checked_bronze_table_count=reproduced.checked_bronze_table_count,
            reproduction_output_path=reproduction_root,
        )

    def verify(
        self, package_path: Path, *, expected_digest: str | None = None
    ) -> FinanceDataVerifyResult:
        root = package_path.resolve()
        source_manifest = _read_canonical_json(root / SOURCE_MANIFEST_PATH)
        bronze_manifest = _read_canonical_json(root / BRONZE_MANIFEST_PATH)
        checksums = _read_canonical_json(root / CHECKSUMS_PATH)
        digest = (root / DETACHED_DIGEST_PATH).read_text(encoding="ascii").strip()
        actual_digest = sha256_bytes((root / CHECKSUMS_PATH).read_bytes())
        if digest != actual_digest or (
            expected_digest is not None and digest != expected_digest
        ):
            raise FinanceDataSubstrateError("detached package digest differs")
        datasets = source_manifest.get("datasets")
        if not isinstance(datasets, list):
            raise FinanceDataSubstrateError("source manifest datasets are missing")
        manifest_by_path = {
            str(item["path"]): item for item in datasets if isinstance(item, dict)
        }
        current_paths = {item.path for item in ALL_SOURCE_DATASETS}
        a22b_paths = {item.path for item in A22B_PACKAGE_DATASETS}
        a22_paths = {item.path for item in A22_PACKAGE_DATASETS}
        a21_paths = {item.path for item in A21_PACKAGE_DATASETS}
        legacy_paths = {item.path for item in A1_SOURCE_DATASETS}
        statutory_contract_version = str(
            source_manifest.get("statutory_contract_version", "A2.3")
        )
        if statutory_contract_version not in {"A2.3", "A2.4"}:
            raise FinanceDataSubstrateError(
                "source manifest statutory contract version differs"
            )
        if set(manifest_by_path) == current_paths:
            package_definitions = ALL_SOURCE_DATASETS
            includes_a21 = True
            includes_a22_fixed_assets = True
            includes_a22b_statutory_subledgers = True
            includes_a23_multi_entity_close = True
            includes_a24_ratification = statutory_contract_version == "A2.4"
        elif set(manifest_by_path) == a22b_paths:
            package_definitions = A22B_PACKAGE_DATASETS
            includes_a21 = True
            includes_a22_fixed_assets = True
            includes_a22b_statutory_subledgers = True
            includes_a23_multi_entity_close = False
            includes_a24_ratification = False
            includes_a24_ratification = False
            includes_a24_ratification = False
            includes_a24_ratification = False
        elif set(manifest_by_path) == a22_paths:
            package_definitions = A22_PACKAGE_DATASETS
            includes_a21 = True
            includes_a22_fixed_assets = True
            includes_a22b_statutory_subledgers = False
            includes_a23_multi_entity_close = False
            includes_a23_multi_entity_close = False
            includes_a23_multi_entity_close = False
        elif set(manifest_by_path) == a21_paths:
            package_definitions = A21_PACKAGE_DATASETS
            includes_a21 = True
            includes_a22_fixed_assets = False
            includes_a22b_statutory_subledgers = False
            includes_a22b_statutory_subledgers = False
        elif set(manifest_by_path) == legacy_paths:
            package_definitions = A1_SOURCE_DATASETS
            includes_a21 = False
            includes_a22_fixed_assets = False
        else:
            raise FinanceDataSubstrateError("source manifest paths differ")
        if statutory_contract_version == "A2.4" and not includes_a24_ratification:
            raise FinanceDataSubstrateError(
                "A2.4 contract requires the complete current dataset inventory"
            )
        if len(datasets) != len(package_definitions):
            raise FinanceDataSubstrateError("source manifest dataset inventory differs")
        entries = checksums.get("entries")
        if not isinstance(entries, list):
            raise FinanceDataSubstrateError("checksum entries are missing")
        canonical_paths: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise FinanceDataSubstrateError("checksum entry is invalid")
            relative_path = str(entry["path"])
            if relative_path in canonical_paths:
                raise FinanceDataSubstrateError("checksum paths are duplicated")
            canonical_paths.add(relative_path)
            path = root / relative_path
            if not path.is_file():
                raise FinanceDataSubstrateError(f"checksum path is absent: {relative_path}")
            if _stream_sha256(path) != entry["sha256"]:
                raise FinanceDataSubstrateError(f"checksum differs: {relative_path}")
            if path.stat().st_size != entry["byte_count"]:
                raise FinanceDataSubstrateError(f"byte count differs: {relative_path}")
        expected_canonical = {
            README_PATH,
            SOURCE_MANIFEST_PATH,
            *(f"raw/{item.path}" for item in package_definitions),
        }
        if canonical_paths != expected_canonical:
            raise FinanceDataSubstrateError("canonical package scope differs")
        expected_physical = {
            *expected_canonical,
            BRONZE_MANIFEST_PATH,
            CHECKSUMS_PATH,
            DETACHED_DIGEST_PATH,
            DATABASE_RELATIVE_PATH,
        }
        if set(_relative_files(root)) != expected_physical:
            raise FinanceDataSubstrateError("physical package inventory differs")
        checked_rows = 0
        for definition in package_definitions:
            source_path = definition.path
            entry = manifest_by_path[source_path]
            path = root / "raw" / source_path
            row_count = _read_csv_contract(path, definition.columns)
            if row_count != entry["row_count"]:
                raise FinanceDataSubstrateError(f"source row count differs: {source_path}")
            if _stream_sha256(path) != entry["sha256"]:
                raise FinanceDataSubstrateError(f"source hash differs: {source_path}")
            checked_rows += row_count
        if checked_rows != source_manifest.get("source_row_count"):
            raise FinanceDataSubstrateError("source manifest total row count differs")
        database_path = root / DATABASE_RELATIVE_PATH
        if database_file_sha256(database_path) != bronze_manifest.get(
            "database_sha256"
        ):
            raise FinanceDataSubstrateError("same-build Bronze database hash differs")
        bronze_tables = _bronze_tables_from_manifest(bronze_manifest)
        verify_bronze_database(
            raw_root=root / "raw",
            database_path=database_path,
            source_data_ref=str(source_manifest["data_ref"]),
            expected_tables=bronze_tables,
        )
        _verify_accounting_controls(database_path)
        if includes_a21:
            _verify_a21_controls(database_path)
        if includes_a22_fixed_assets:
            _verify_a22_fixed_asset_controls(database_path)
        if includes_a22b_statutory_subledgers:
            _verify_a22b_statutory_subledger_controls(database_path)
        if includes_a23_multi_entity_close:
            _verify_a23_multi_entity_close_controls(database_path)
        if includes_a24_ratification:
            _verify_a24_ratification_controls(database_path)
        defect_count = int(manifest_by_path[DEFECT_REGISTRY.path]["row_count"])
        if defect_count != source_manifest.get("defect_count"):
            raise FinanceDataSubstrateError("defect count differs")
        if manifest_by_path[BUSINESS_EVENTS.path]["row_count"] == 0:
            raise FinanceDataSubstrateError("business-event population is empty")
        if manifest_by_path[SOURCE_GL_LINES.path]["row_count"] == 0:
            raise FinanceDataSubstrateError("source GL population is empty")
        return FinanceDataVerifyResult(
            data_ref=str(source_manifest["data_ref"]),
            package_digest=digest,
            checked_dataset_count=len(datasets),
            checked_source_row_count=checked_rows,
            checked_bronze_table_count=len(bronze_tables),
            checked_defect_count=defect_count,
        )
