from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import duckdb
import pytest

from finance_assurance.finance_data import (
    FinanceDataBuildRequest,
    FinanceDataReproduceRequest,
    FinanceDataSubstrateService,
    StatutoryAcceptanceRequest,
    StatutoryAcceptanceService,
)
from finance_assurance.finance_data.service import (
    FinanceDataSubstrateError,
    _verify_a24_ratification_controls,
)


@pytest.fixture(scope="module")
def smoke_package(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, str]:
    output = tmp_path_factory.mktemp("finance-data") / "smoke"
    request = FinanceDataBuildRequest(
        data_ref="ATLAS-FINANCE-SMOKE@v1",
        output_path=output,
        built_at="2026-08-24T18:00:00Z",
        scale_profile="SMOKE",
        seed=42,
        history_start=date(2021, 1, 1),
        actuals_end=date(2026, 6, 30),
    )
    result = FinanceDataSubstrateService().build(request)
    assert result.status == "PUBLISHED"
    return output, result.package_digest


def test_builds_closed_five_year_source_and_bronze_package(
    smoke_package: tuple[Path, str],
) -> None:
    package, digest = smoke_package
    verified = FinanceDataSubstrateService().verify(
        package,
        expected_digest=digest,
    )
    source_manifest = json.loads(
        (package / "source-manifest.json").read_text(encoding="utf-8")
    )
    bronze_manifest = json.loads(
        (package / "bronze-manifest.json").read_text(encoding="utf-8")
    )

    assert verified.status == "VERIFIED"
    assert source_manifest["history_month_count"] == 66
    assert source_manifest["history_start"] == "2021-01-01"
    assert source_manifest["actuals_end"] == "2026-06-30"
    assert source_manifest["source_row_count"] > 180_000
    assert source_manifest["defect_count"] >= 6
    dataset_paths = {item["path"] for item in source_manifest["datasets"]}
    assert len(dataset_paths) == 78
    assert {
        "accounting/accounting_events.csv",
        "accounting/cash_flow_reconciliation.csv",
        "accounting/monthly_close_status.csv",
        "accounting/retained_earnings_bridge.csv",
        "accounting/statutory_statement_lines.csv",
        "accounting/statutory_trial_balance.csv",
        "assurance/fixed_asset_control_results.csv",
        "assurance/statutory_subledger_control_results.csv",
        "billing/subscription_events.csv",
        "equity/equity_movements.csv",
        "fixed_assets/asset_lifecycle_events.csv",
        "fixed_assets/fixed_asset_movements.csv",
        "fixed_assets/fixed_asset_register.csv",
        "hermes/source_admission_results.csv",
        "intercompany/intercompany_balances.csv",
        "intercompany/intercompany_transactions.csv",
        "leases/lease_contracts.csv",
        "leases/lease_lifecycle_events.csv",
        "leases/lease_schedule.csv",
        "procurement/capital_goods_receipts.csv",
        "procurement/capital_invoices.csv",
        "procurement/capital_purchase_orders.csv",
        "procurement/ap_ageing_snapshot.csv",
        "reference/product_price_book.csv",
        "reference/legal_entities.csv",
        "revenue/deferred_revenue_rollforward.csv",
        "tax/tax_calculation_inputs.csv",
        "tax/tax_loss_register.csv",
        "tax/tax_schedule.csv",
        "treasury/bank_reconciliations.csv",
        "treasury/bank_statement_lines.csv",
        "treasury/bank_transactions.csv",
        "treasury/debt_instruments.csv",
        "treasury/debt_schedule.csv",
        "workforce/employee_compensation.csv",
        "workforce/headcount_plan.csv",
        "working_capital/accrual_schedule.csv",
        "working_capital/accrual_source_events.csv",
        "working_capital/prepayment_schedule.csv",
        "working_capital/prepayment_source_events.csv",
        "planning/variance_source_extract.csv",
        "consolidation/elimination_journal_lines.csv",
        "governance/statutory_reconciliation_results.csv",
    }.issubset(dataset_paths)
    assert bronze_manifest["table_count"] == len(source_manifest["datasets"])
    assert (package / "warehouse" / "atlas-finance.duckdb").is_file()


def test_bronze_preserves_source_values_and_causal_event_binding(
    smoke_package: tuple[Path, str],
) -> None:
    package, _ = smoke_package
    database = package / "warehouse" / "atlas-finance.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        gl_columns = connection.execute(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_schema = 'bronze' "
            "AND table_name = 'accounting__source_gl_journal_lines' "
            "AND column_name NOT LIKE '\\_%' ESCAPE '\\'"
        ).fetchall()
        missing_events = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.accounting__source_gl_journal_lines AS gl "
            "LEFT JOIN bronze.events__business_events AS event "
            "USING (business_event_ref) "
            "WHERE event.business_event_ref IS NULL"
        ).fetchone()[0]
        unbalanced_journals = connection.execute(
            "SELECT COUNT(*) FROM ("
            "SELECT source_journal_id "
            "FROM bronze.accounting__source_gl_journal_lines "
            "GROUP BY source_journal_id "
            "HAVING SUM(CAST(debit_minor AS HUGEINT)) "
            "<> SUM(CAST(credit_minor AS HUGEINT)))"
        ).fetchone()[0]
        duplicate_event_refs = connection.execute(
            "SELECT COUNT(*) - COUNT(DISTINCT business_event_ref) "
            "FROM bronze.events__business_events"
        ).fetchone()[0]

    assert gl_columns
    assert {row[0] for row in gl_columns} == {"VARCHAR"}
    assert missing_events == 0
    assert unbalanced_journals == 0
    assert duplicate_event_refs == 0


def test_annual_invoice_reporting_revenue_does_not_create_fx_leakage(
    smoke_package: tuple[Path, str],
) -> None:
    package, _ = smoke_package
    database = package / "warehouse" / "atlas-finance.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        leakage = connection.execute(
            "SELECT COUNT(*) FROM ("
            "SELECT invoice.invoice_id "
            "FROM bronze.billing__invoices AS invoice "
            "JOIN bronze.billing__subscriptions AS subscription "
            "USING (subscription_id) "
            "JOIN bronze.revenue__revenue_recognition_schedule AS schedule "
            "USING (invoice_id) "
            "WHERE subscription.billing_frequency = 'ANNUAL' "
            "AND invoice.service_period_end <= '2026-06-30' "
            "GROUP BY invoice.invoice_id, invoice.reporting_amount_minor "
            "HAVING SUM(CAST(schedule.reporting_revenue_amount_minor AS HUGEINT)) "
            "<> CAST(invoice.reporting_amount_minor AS HUGEINT))"
        ).fetchone()[0]

    assert leakage == 0


def test_restored_source_products_close_their_local_controls(
    smoke_package: tuple[Path, str],
) -> None:
    package, _ = smoke_package
    database = package / "warehouse" / "atlas-finance.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        broken_deferred_rollforwards = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.revenue__deferred_revenue_rollforward "
            "WHERE CAST(opening_deferred_revenue_minor AS HUGEINT) "
            "+ CAST(new_billings_minor AS HUGEINT) "
            "- CAST(recognised_revenue_minor AS HUGEINT) "
            "<> CAST(closing_deferred_revenue_minor AS HUGEINT)"
        ).fetchone()[0]
        compensation_mismatch = connection.execute(
            "SELECT COUNT(*) FROM ("
            "SELECT payroll.period_id, payroll.employee_id "
            "FROM bronze.workforce__payroll_expense_lines AS payroll "
            "JOIN bronze.workforce__employee_compensation AS compensation "
            "USING (period_id, employee_id) "
            "GROUP BY payroll.period_id, payroll.employee_id, "
            "payroll.reporting_payroll_cost_minor "
            "HAVING SUM(CAST(compensation.reporting_amount_minor AS HUGEINT)) "
            "<> CAST(payroll.reporting_payroll_cost_minor AS HUGEINT))"
        ).fetchone()[0]
        failed_source_qa = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.governance__source_generation_qa_results "
            "WHERE status <> 'PASS'"
        ).fetchone()[0]

    assert broken_deferred_rollforwards == 0
    assert compensation_mismatch == 0
    assert failed_source_qa == 0


def test_a21_bank_statements_replay_and_reconcile_to_cash_gl(
    smoke_package: tuple[Path, str],
) -> None:
    package, _ = smoke_package
    database = package / "warehouse" / "atlas-finance.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        mismatched_cash = connection.execute(
            "SELECT COUNT(*) FROM ("
            "SELECT business_event_ref, legal_entity_id, "
            "SUM(CAST(debit_minor AS HUGEINT)) "
            "- SUM(CAST(credit_minor AS HUGEINT)) AS amount_minor "
            "FROM bronze.accounting__source_gl_journal_lines "
            "WHERE account_id = '1000' "
            "GROUP BY business_event_ref, legal_entity_id) AS gl "
            "FULL OUTER JOIN ("
            "SELECT business_event_ref, legal_entity_id, "
            "SUM(CAST(amount_minor AS HUGEINT)) AS amount_minor "
            "FROM bronze.treasury__bank_transactions "
            "GROUP BY business_event_ref, legal_entity_id) AS bank "
            "USING (business_event_ref, legal_entity_id) "
            "WHERE gl.business_event_ref IS NULL "
            "OR bank.business_event_ref IS NULL "
            "OR gl.amount_minor <> bank.amount_minor"
        ).fetchone()[0]
        failed_reconciliations = connection.execute(
            "SELECT COUNT(*) FROM bronze.treasury__bank_reconciliations "
            "WHERE reconciliation_status <> 'RECONCILED' "
            "OR CAST(unreconciled_difference_minor AS HUGEINT) <> 0"
        ).fetchone()[0]
        minimum_balance = connection.execute(
            "SELECT MIN(CAST(running_balance_minor AS HUGEINT)) "
            "FROM bronze.treasury__bank_statement_lines"
        ).fetchone()[0]

    assert mismatched_cash == 0
    assert failed_reconciliations == 0
    assert minimum_balance >= 0


def test_a21_debt_is_finite_continuous_and_not_a_cash_plug(
    smoke_package: tuple[Path, str],
) -> None:
    package, _ = smoke_package
    database = package / "warehouse" / "atlas-finance.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        facilities = connection.execute(
            "SELECT debt_instrument_id, CAST(facility_limit_minor AS HUGEINT) "
            "FROM bronze.treasury__debt_instruments "
            "ORDER BY debt_instrument_id"
        ).fetchall()
        broken_rollforwards = connection.execute(
            "SELECT COUNT(*) FROM bronze.treasury__debt_schedule "
            "WHERE CAST(opening_principal_minor AS HUGEINT) "
            "+ CAST(drawdown_minor AS HUGEINT) "
            "- CAST(principal_repayment_minor AS HUGEINT) "
            "<> CAST(closing_principal_minor AS HUGEINT)"
        ).fetchone()[0]
        revolver_draws = connection.execute(
            "SELECT COALESCE(SUM(CAST(drawdown_minor AS HUGEINT)), 0) "
            "FROM bronze.treasury__debt_schedule "
            "WHERE debt_instrument_id = 'DEBT-REVOLVER-GBP'"
        ).fetchone()[0]

    assert facilities == [
        ("DEBT-REVOLVER-GBP", 2_000_000_000),
        ("DEBT-TERM-GBP", 1_500_000_000),
    ]
    assert broken_rollforwards == 0
    assert revolver_draws == 0


def test_a23_publishes_multi_entity_close_and_three_statements(
    smoke_package: tuple[Path, str],
) -> None:
    package, _ = smoke_package
    database = package / "warehouse" / "atlas-finance.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        counts = {
            table_name: connection.execute(
                f'SELECT COUNT(*) FROM bronze."{table_name}"'
            ).fetchone()[0]
            for table_name in (
                "intercompany__intercompany_transactions",
                "intercompany__intercompany_balances",
                "consolidation__elimination_journal_lines",
                "accounting__accounting_events",
                "accounting__statutory_trial_balance",
                "accounting__statutory_statement_lines",
                "accounting__retained_earnings_bridge",
                "accounting__cash_flow_reconciliation",
                "accounting__monthly_close_status",
                "governance__statutory_reconciliation_results",
            )
        }
        statement_classes = connection.execute(
            "SELECT DISTINCT statement_class "
            "FROM bronze.accounting__statutory_statement_lines "
            "ORDER BY statement_class"
        ).fetchall()
        failed_close_controls = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.governance__statutory_reconciliation_results "
            "WHERE status <> 'PASS' "
            "OR CAST(difference_minor AS HUGEINT) <> 0"
        ).fetchone()[0]
        uneliminated_group_balances = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.accounting__statutory_trial_balance "
            "WHERE scope_id = 'NEXUS-GROUP' "
            "AND account_id IN ('1150', '2050') "
            "AND CAST(closing_balance_minor AS HUGEINT) <> 0"
        ).fetchone()[0]

    assert counts == {
        "intercompany__intercompany_transactions": 120,
        "intercompany__intercompany_balances": 120,
        "consolidation__elimination_journal_lines": 480,
        "accounting__accounting_events": 654,
        "accounting__statutory_trial_balance": 6_732,
        "accounting__statutory_statement_lines": 8_514,
        "accounting__retained_earnings_bridge": 198,
        "accounting__cash_flow_reconciliation": 198,
        "accounting__monthly_close_status": 198,
        "governance__statutory_reconciliation_results": 990,
    }
    assert statement_classes == [
        ("BALANCE_SHEET",),
        ("CASH_FLOW",),
        ("INCOME_STATEMENT",),
    ]
    assert failed_close_controls == 0
    assert uneliminated_group_balances == 0


def test_a24_cross_statement_and_close_prerequisites_are_explicit(
    smoke_package: tuple[Path, str],
) -> None:
    package, _ = smoke_package
    database = package / "warehouse" / "atlas-finance.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        cash_flow_net_income_rows = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.accounting__statutory_statement_lines "
            "WHERE statement_class = 'CASH_FLOW' "
            "AND statement_line = 'net_income'"
        ).fetchone()[0]
        cited_close_prerequisites = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.accounting__accounting_events AS event, "
            "UNNEST(STRING_SPLIT(event.source_record_refs, ',')) AS refs(ref) "
            "JOIN bronze.governance__statutory_reconciliation_results AS result "
            "ON refs.ref = result.reconciliation_ref "
            "WHERE event.accounting_event_type = 'HARD_CLOSE_COMPLETED'"
        ).fetchone()[0]

    assert cash_flow_net_income_rows == 198
    assert cited_close_prerequisites == 990


def test_a24_strict_controls_reject_semantic_mutations(
    smoke_package: tuple[Path, str], tmp_path: Path
) -> None:
    package, _ = smoke_package
    mutated_database = tmp_path / "mutated-atlas-finance.duckdb"
    shutil.copy2(package / "warehouse" / "atlas-finance.duckdb", mutated_database)

    with duckdb.connect(str(mutated_database)) as connection:
        original_net_income = connection.execute(
            "SELECT amount_minor "
            "FROM bronze.accounting__statutory_statement_lines "
            "WHERE period_id = '2021-01' AND scope_id = 'NEXUS-UK' "
            "AND statement_class = 'CASH_FLOW' "
            "AND statement_line = 'net_income'"
        ).fetchone()[0]
        connection.execute(
            "UPDATE bronze.accounting__statutory_statement_lines "
            "SET amount_minor = CAST(CAST(amount_minor AS HUGEINT) + 1 AS VARCHAR) "
            "WHERE period_id = '2021-01' AND scope_id = 'NEXUS-UK' "
            "AND statement_class = 'CASH_FLOW' "
            "AND statement_line = 'net_income'"
        )
    with pytest.raises(FinanceDataSubstrateError, match="net income does not agree"):
        _verify_a24_ratification_controls(mutated_database)
    with duckdb.connect(str(mutated_database)) as connection:
        connection.execute(
            "UPDATE bronze.accounting__statutory_statement_lines "
            "SET amount_minor = ? "
            "WHERE period_id = '2021-01' AND scope_id = 'NEXUS-UK' "
            "AND statement_class = 'CASH_FLOW' "
            "AND statement_line = 'net_income'",
            [original_net_income],
        )
        event_ref, original_sources = connection.execute(
            "SELECT accounting_event_ref, source_record_refs "
            "FROM bronze.accounting__accounting_events "
            "WHERE accounting_event_type = 'HARD_CLOSE_COMPLETED' "
            "ORDER BY accounting_event_ref LIMIT 1"
        ).fetchone()
        connection.execute(
            "UPDATE bronze.accounting__accounting_events "
            "SET source_record_refs = '' WHERE accounting_event_ref = ?",
            [event_ref],
        )
    with pytest.raises(
        FinanceDataSubstrateError, match="hard-close event does not cite"
    ):
        _verify_a24_ratification_controls(mutated_database)
    with duckdb.connect(str(mutated_database)) as connection:
        connection.execute(
            "UPDATE bronze.accounting__accounting_events "
            "SET source_record_refs = ? WHERE accounting_event_ref = ?",
            [original_sources, event_ref],
        )
        line_id = connection.execute(
            "SELECT source_journal_line_id "
            "FROM bronze.accounting__source_gl_journal_lines "
            "ORDER BY source_journal_line_id LIMIT 1"
        ).fetchone()[0]
        connection.execute(
            "UPDATE bronze.accounting__source_gl_journal_lines "
            "SET source_record_ref = 'BROKEN-SOURCE' "
            "WHERE source_journal_line_id = ?",
            [line_id],
        )
    with pytest.raises(
        FinanceDataSubstrateError, match="does not resolve to exact causal source"
    ):
        _verify_a24_ratification_controls(mutated_database)


def test_a21_equity_is_authorised_and_event_derived(
    smoke_package: tuple[Path, str],
) -> None:
    package, _ = smoke_package
    database = package / "warehouse" / "atlas-finance.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        movements = connection.execute(
            "SELECT movement_type, CAST(movement.amount_minor AS HUGEINT), "
            "authorisation_ref, event.event_type "
            "FROM bronze.equity__equity_movements AS movement "
            "JOIN bronze.events__business_events AS event "
            "USING (business_event_ref) "
            "ORDER BY movement.period_id"
        ).fetchall()

    assert movements == [
        (
            "ORDINARY_SHARE_ISSUANCE",
            5_000_000_000,
            "BOARD-FORMATION-FUNDING@v1",
            "CAPITAL_CONTRIBUTION_RECEIVED",
        ),
        (
            "SERIES_B_EQUITY_ISSUANCE",
            2_000_000_000,
            "BOARD-SERIES-B-EQUITY-2024@v1",
            "CAPITAL_CONTRIBUTION_RECEIVED",
        ),
        (
            "GROWTH_EQUITY_ISSUANCE",
            2_500_000_000,
            "BOARD-GROWTH-EQUITY-2025@v1",
            "CAPITAL_CONTRIBUTION_RECEIVED",
        ),
    ]


def test_a22_fixed_asset_vertical_reconciles_and_preserves_quarantine(
    smoke_package: tuple[Path, str],
) -> None:
    package, _ = smoke_package
    database = package / "warehouse" / "atlas-finance.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        asset_count = connection.execute(
            "SELECT COUNT(*) FROM bronze.fixed_assets__fixed_asset_register"
        ).fetchone()[0]
        broken_rollforwards = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.fixed_assets__fixed_asset_movements "
            "WHERE CAST(opening_gross_book_value_minor AS HUGEINT) "
            "+ CAST(gross_addition_minor AS HUGEINT) "
            "- CAST(gross_disposal_minor AS HUGEINT) "
            "<> CAST(closing_gross_book_value_minor AS HUGEINT) "
            "OR CAST(opening_accumulated_depreciation_minor AS HUGEINT) "
            "+ CAST(depreciation_minor AS HUGEINT) "
            "+ CAST(amortisation_minor AS HUGEINT) "
            "+ CAST(impairment_minor AS HUGEINT) "
            "- CAST(accumulated_depreciation_disposal_minor AS HUGEINT) "
            "<> CAST(closing_accumulated_depreciation_minor AS HUGEINT)"
        ).fetchone()[0]
        lifecycle_counts = connection.execute(
            "SELECT "
            "COUNT(*) FILTER (WHERE event_type = 'FIXED_ASSET_DISPOSED'), "
            "COUNT(*) FILTER ("
            "WHERE event_type = 'FIXED_ASSET_IMPAIRMENT_APPROVED') "
            "FROM bronze.fixed_assets__asset_lifecycle_events"
        ).fetchone()
        admission_counts = connection.execute(
            "SELECT "
            "COUNT(*) FILTER (WHERE admission_decision = 'QUARANTINED'), "
            "COUNT(*) FILTER (WHERE admission_decision = 'ADMITTED_WITH_WARNING') "
            "FROM bronze.hermes__source_admission_results "
            "WHERE source_dataset_path IN ("
            "'procurement/capital_invoices.csv', "
            "'fixed_assets/asset_lifecycle_events.csv')"
        ).fetchone()
        argus_exceptions = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.assurance__fixed_asset_control_results "
            "WHERE status = 'EXCEPTION' "
            "AND observation_type = 'QUARANTINED_DUPLICATE_SOURCE'"
        ).fetchone()[0]
        duplicate_postings = connection.execute(
            "SELECT COUNT(*) FROM bronze.events__business_events "
            "WHERE source_record_ref = 'CINV-DUPLICATE-00001#APPROVAL'"
        ).fetchone()[0]

    assert asset_count > 5
    assert broken_rollforwards == 0
    assert lifecycle_counts == (1, 1)
    assert admission_counts[0] == 1
    assert admission_counts[1] > 0
    assert argus_exceptions == 1
    assert duplicate_postings == 0


def test_a22b_statutory_subledgers_reconcile_and_preserve_quarantine(
    smoke_package: tuple[Path, str],
) -> None:
    package, _ = smoke_package
    database = package / "warehouse" / "atlas-finance.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        lease_contracts = connection.execute(
            "SELECT COUNT(*) FROM bronze.leases__lease_contracts"
        ).fetchone()[0]
        broken_leases = connection.execute(
            "SELECT COUNT(*) FROM bronze.leases__lease_schedule "
            "WHERE CAST(opening_liability_minor AS HUGEINT) "
            "+ CAST(liability_addition_minor AS HUGEINT) "
            "+ CAST(interest_accretion_minor AS HUGEINT) "
            "- CAST(cash_payment_minor AS HUGEINT) "
            "<> CAST(closing_liability_minor AS HUGEINT) "
            "OR CAST(opening_rou_asset_minor AS HUGEINT) "
            "+ CAST(rou_asset_addition_minor AS HUGEINT) "
            "- CAST(rou_depreciation_minor AS HUGEINT) "
            "- CAST(rou_impairment_minor AS HUGEINT) "
            "<> CAST(closing_rou_asset_minor AS HUGEINT)"
        ).fetchone()[0]
        tax_vintages = connection.execute(
            "SELECT COUNT(DISTINCT loss_vintage_year), "
            "MIN(CAST(closing_tax_loss_minor AS HUGEINT)) "
            "FROM bronze.tax__tax_loss_register"
        ).fetchone()
        broken_accruals = connection.execute(
            "SELECT COUNT(*) FROM bronze.working_capital__accrual_schedule "
            "WHERE CAST(opening_accrual_minor AS HUGEINT) "
            "+ CAST(addition_minor AS HUGEINT) "
            "- CAST(release_minor AS HUGEINT) "
            "<> CAST(closing_accrual_minor AS HUGEINT)"
        ).fetchone()[0]
        broken_prepayments = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.working_capital__prepayment_schedule "
            "WHERE CAST(opening_prepayment_minor AS HUGEINT) "
            "+ CAST(cash_addition_minor AS HUGEINT) "
            "- CAST(expense_release_minor AS HUGEINT) "
            "<> CAST(closing_prepayment_minor AS HUGEINT)"
        ).fetchone()[0]
        duplicate_quarantine = connection.execute(
            "SELECT COUNT(*) FROM bronze.hermes__source_admission_results "
            "WHERE source_record_ref = 'PSE-DUPLICATE-00001' "
            "AND admission_decision = 'QUARANTINED' "
            "AND candidate_business_event_ref = ''"
        ).fetchone()[0]
        duplicate_postings = connection.execute(
            "SELECT COUNT(*) FROM bronze.events__business_events "
            "WHERE source_record_ref = 'PSE-DUPLICATE-00001'"
        ).fetchone()[0]
        passing_controls = connection.execute(
            "SELECT COUNT(*) "
            "FROM bronze.assurance__statutory_subledger_control_results "
            "WHERE status = 'PASS'"
        ).fetchone()[0]

    assert lease_contracts == 4
    assert broken_leases == 0
    assert tax_vintages[0] == 6
    assert tax_vintages[1] >= 0
    assert broken_accruals == 0
    assert broken_prepayments == 0
    assert duplicate_quarantine == 1
    assert duplicate_postings == 0
    assert passing_controls > 500


def test_canonical_source_digest_is_reproducible(
    smoke_package: tuple[Path, str],
    tmp_path: Path,
) -> None:
    _, first_digest = smoke_package
    package, _ = smoke_package
    reproduced_path = tmp_path / "reproduced"
    result = FinanceDataSubstrateService().reproduce(
        FinanceDataReproduceRequest(
            source_package_path=package,
            reproduction_output_path=reproduced_path,
            expected_digest=first_digest,
        )
    )
    report = StatutoryAcceptanceService().assess(
        StatutoryAcceptanceRequest(
            source_package_path=package,
            reproduction_package_path=reproduced_path,
            expected_digest=first_digest,
        )
    )

    assert result.reproduced_package_digest == first_digest
    assert result.canonical_file_count == 82
    assert report.passed_criterion_count == 30
    assert report.failed_criterion_count == 0
    assert tuple(value.criterion_id for value in report.criteria) == tuple(
        f"A2-A{number:02d}" for number in range(1, 31)
    )
    assert report.status == "RATIFIED"
