"""Independent executable controls for the Q-FINANCE B2 successor profile."""


from __future__ import annotations

B2_CONTROL_QUERIES: tuple[tuple[str, str], ...] = (
    (
        "B2_POPULATION_RECONCILES_TO_SILVER",
        """
        WITH populations AS (
            SELECT (SELECT COUNT(*) FROM gold.dim_bank_account) actual_rows,
                   (SELECT COUNT(*) FROM silver.stg_treasury__bank_accounts) expected_rows
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_debt_instrument),
                             (SELECT COUNT(*) FROM silver.stg_treasury__debt_instruments)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_fixed_asset),
                             (SELECT COUNT(*) FROM silver.stg_fixed_assets__fixed_asset_register)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_lease_contract),
                             (SELECT COUNT(*) FROM silver.stg_leases__lease_contracts)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_fixed_asset_lifecycle_events),
                             (SELECT COUNT(*) FROM silver.stg_fixed_assets__asset_lifecycle_events)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_fixed_asset_movements),
                             (SELECT COUNT(*) FROM silver.stg_fixed_assets__fixed_asset_movements)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_fixed_asset_control_results),
                             (SELECT COUNT(*) FROM silver.stg_assurance__fixed_asset_control_results)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_bank_transactions),
                             (SELECT COUNT(*) FROM silver.stg_treasury__bank_transactions)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_bank_statement_lines),
                             (SELECT COUNT(*) FROM silver.stg_treasury__bank_statement_lines)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_bank_reconciliations),
                             (SELECT COUNT(*) FROM silver.stg_treasury__bank_reconciliations)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_debt_schedule),
                             (SELECT COUNT(*) FROM silver.stg_treasury__debt_schedule)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_lease_lifecycle_events),
                             (SELECT COUNT(*) FROM silver.stg_leases__lease_lifecycle_events)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_lease_schedule),
                             (SELECT COUNT(*) FROM silver.stg_leases__lease_schedule)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_tax_calculation_inputs),
                             (SELECT COUNT(*) FROM silver.stg_tax__tax_calculation_inputs)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_tax_schedule),
                             (SELECT COUNT(*) FROM silver.stg_tax__tax_schedule)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_tax_loss_register),
                             (SELECT COUNT(*) FROM silver.stg_tax__tax_loss_register)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_equity_movements),
                             (SELECT COUNT(*) FROM silver.stg_equity__equity_movements)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_accrual_source_events),
                             (SELECT COUNT(*) FROM silver.stg_working_capital__accrual_source_events)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_accrual_schedule),
                             (SELECT COUNT(*) FROM silver.stg_working_capital__accrual_schedule)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_prepayment_source_events),
                             (SELECT COUNT(*) FROM silver.stg_working_capital__prepayment_source_events)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_prepayment_schedule),
                             (SELECT COUNT(*) FROM silver.stg_working_capital__prepayment_schedule)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_intercompany_transactions),
                             (SELECT COUNT(*) FROM silver.stg_intercompany__intercompany_transactions)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_intercompany_balances),
                             (SELECT COUNT(*) FROM silver.stg_intercompany__intercompany_balances)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_statutory_subledger_controls),
                             (SELECT COUNT(*) FROM silver.stg_assurance__statutory_subledger_control_results)
        )
        SELECT COUNT(*) FROM populations WHERE actual_rows <> expected_rows
        """,
    ),
    (
        "B2_ROLLFORWARDS_RECONCILE",
        """
        SELECT COUNT(*) FROM (
            SELECT asset_movement_id object_ref FROM gold.fct_fixed_asset_movements
            WHERE opening_gross_book_value_minor + gross_addition_minor - gross_disposal_minor <> closing_gross_book_value_minor
               OR opening_accumulated_depreciation_minor + depreciation_minor + amortisation_minor
                  + impairment_minor - accumulated_depreciation_disposal_minor <> closing_accumulated_depreciation_minor
               OR closing_gross_book_value_minor - closing_accumulated_depreciation_minor <> closing_net_book_value_minor
            UNION ALL SELECT bank_account_id FROM gold.fct_bank_reconciliations
            WHERE statement_closing_minor + outstanding_receipts_minor - outstanding_disbursements_minor
                  + other_reconciling_items_minor <> gl_cash_closing_minor
               OR unreconciled_difference_minor <> 0 OR reconciliation_status <> 'RECONCILED'
            UNION ALL SELECT debt_instrument_id FROM gold.fct_debt_schedule
            WHERE opening_principal_minor + drawdown_minor - principal_repayment_minor <> closing_principal_minor
               OR facility_limit_minor - closing_principal_minor <> undrawn_facility_minor
            UNION ALL SELECT lease_contract_id FROM gold.fct_lease_schedule
            WHERE opening_liability_minor + liability_addition_minor + interest_accretion_minor
                  - cash_payment_minor <> closing_liability_minor
               OR cash_payment_minor - interest_accretion_minor <> principal_reduction_minor
               OR opening_rou_asset_minor + rou_asset_addition_minor - rou_depreciation_minor
                  - rou_impairment_minor <> closing_rou_asset_minor
            UNION ALL SELECT jurisdiction_code FROM gold.fct_tax_schedule
            WHERE opening_tax_payable_minor + current_tax_expense_minor - cash_tax_paid_minor <> closing_tax_payable_minor
               OR opening_deferred_tax_asset_minor + deferred_tax_movement_minor <> closing_deferred_tax_asset_minor
            UNION ALL SELECT CAST(loss_vintage_year AS VARCHAR) FROM gold.fct_tax_loss_register
            WHERE opening_tax_loss_minor + loss_generated_minor - loss_utilised_minor
                  - loss_expired_minor <> closing_tax_loss_minor
            UNION ALL SELECT accrual_schedule_id FROM gold.fct_accrual_schedule
            WHERE opening_accrual_minor + addition_minor - release_minor <> closing_accrual_minor
            UNION ALL SELECT prepayment_schedule_id FROM gold.fct_prepayment_schedule
            WHERE opening_prepayment_minor + cash_addition_minor - expense_release_minor <> closing_prepayment_minor
            UNION ALL SELECT seller_entity_id FROM gold.fct_intercompany_balances
            WHERE seller_receivable_minor <> buyer_payable_minor OR confirmed_difference_minor <> 0
               OR confirmation_status <> 'CONFIRMED'
        )
        """,
    ),
    (
        "BANK_STATEMENT_RUNNING_BALANCE_REPLAYS",
        """
        SELECT COUNT(*) FROM (
            SELECT running_balance_minor recorded_balance,
                   SUM(amount_minor) OVER (
                     PARTITION BY bank_account_id
                     ORDER BY value_date,
                              CASE WHEN amount_minor > 0 THEN 0 ELSE 1 END,
                              bank_transaction_id
                     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                   ) replayed_balance
            FROM gold.fct_bank_statement_lines
        ) WHERE recorded_balance <> replayed_balance
        """,
    ),
    (
        "B2_PRIOR_PERIOD_CONTINUITY",
        """
        SELECT COUNT(*) FROM (
            SELECT asset_id object_ref, opening_gross_book_value_minor opening_one,
                   LAG(closing_gross_book_value_minor) OVER (PARTITION BY asset_id ORDER BY period_id) prior_one,
                   opening_accumulated_depreciation_minor opening_two,
                   LAG(closing_accumulated_depreciation_minor) OVER (PARTITION BY asset_id ORDER BY period_id) prior_two
            FROM gold.fct_fixed_asset_movements
            UNION ALL
            SELECT debt_instrument_id, opening_principal_minor,
                   LAG(closing_principal_minor) OVER (PARTITION BY debt_instrument_id ORDER BY period_id), NULL, NULL
            FROM gold.fct_debt_schedule
            UNION ALL
            SELECT lease_contract_id, opening_liability_minor,
                   LAG(closing_liability_minor) OVER (PARTITION BY lease_contract_id ORDER BY period_id),
                   opening_rou_asset_minor,
                   LAG(closing_rou_asset_minor) OVER (PARTITION BY lease_contract_id ORDER BY period_id)
            FROM gold.fct_lease_schedule
            UNION ALL
            SELECT accrual_schedule_id, opening_accrual_minor,
                   LAG(closing_accrual_minor) OVER (PARTITION BY accrual_schedule_id ORDER BY period_id), NULL, NULL
            FROM gold.fct_accrual_schedule
            UNION ALL
            SELECT prepayment_schedule_id, opening_prepayment_minor,
                   LAG(closing_prepayment_minor) OVER (PARTITION BY prepayment_schedule_id ORDER BY period_id), NULL, NULL
            FROM gold.fct_prepayment_schedule
        ) continuity
        WHERE prior_one IS NOT NULL AND (opening_one <> prior_one OR COALESCE(opening_two <> prior_two, FALSE))
        """,
    ),
    (
        "B2_SOURCE_EVENTS_RECONCILE_TO_SCHEDULES",
        """
        WITH accrual_source AS (
            SELECT accrual_schedule_id, strftime(event_date, '%Y-%m') period_id,
                   SUM(CASE WHEN event_type = 'ACCRUAL_ESTIMATE_APPROVED' THEN event_amount_minor ELSE 0 END) additions,
                   SUM(CASE WHEN event_type = 'ACCRUAL_SETTLED' THEN event_amount_minor ELSE 0 END) releases
            FROM gold.fct_accrual_source_events GROUP BY 1, 2
        ), prepayment_source AS (
            SELECT prepayment_schedule_id, strftime(event_date, '%Y-%m') period_id,
                   SUM(CASE WHEN event_type = 'PREPAYMENT_PAID' AND duplicate_of_ref IS NULL THEN event_amount_minor ELSE 0 END) additions,
                   SUM(CASE WHEN event_type = 'PREPAID_SERVICE_CONSUMED' AND duplicate_of_ref IS NULL THEN event_amount_minor ELSE 0 END) releases
            FROM gold.fct_prepayment_source_events GROUP BY 1, 2
        ), failures AS (
            SELECT schedule.accrual_schedule_id object_ref
            FROM gold.fct_accrual_schedule schedule
            LEFT JOIN accrual_source source USING (accrual_schedule_id, period_id)
            WHERE schedule.addition_minor <> COALESCE(source.additions, 0)
               OR schedule.release_minor <> COALESCE(source.releases, 0)
            UNION ALL
            SELECT schedule.prepayment_schedule_id
            FROM gold.fct_prepayment_schedule schedule
            LEFT JOIN prepayment_source source USING (prepayment_schedule_id, period_id)
            WHERE schedule.cash_addition_minor <> COALESCE(source.additions, 0)
               OR schedule.expense_release_minor <> COALESCE(source.releases, 0)
        ) SELECT COUNT(*) FROM failures
        """,
    ),
    (
        "B2_EVENT_SPINE_RESOLVES_TO_B1",
        """
        SELECT COUNT(*) FROM gold.fct_subledger_event_links
        WHERE event_type IS NULL OR record_semantic_hash IS NULL
           OR reporting_version_ref IS NULL OR close_status <> 'HARD_CLOSED'
           OR reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
           OR gl_journal_line_count = 0
        """,
    ),
    (
        "B2_EVENT_SPINE_REPLAYS_B1_GL",
        """
        WITH gl AS (
            SELECT business_event_ref, legal_entity_id, COUNT(*) line_count,
                   SUM(debit_minor) debit_minor, SUM(credit_minor) credit_minor
            FROM gold.fct_gl_journal_lines GROUP BY 1, 2
        )
        SELECT COUNT(*) FROM gold.fct_subledger_event_links link
        LEFT JOIN gl USING (business_event_ref, legal_entity_id)
        WHERE link.gl_journal_line_count <> COALESCE(gl.line_count, 0)
           OR link.gl_debit_minor <> COALESCE(gl.debit_minor, 0)
           OR link.gl_credit_minor <> COALESCE(gl.credit_minor, 0)
        """,
    ),
    (
        "B2_INTERCOMPANY_REPLAYS_AND_ELIMINATES",
        """
        WITH cumulative AS (
            SELECT period_id, seller_entity_id, buyer_entity_id,
                   SUM(amount_minor) OVER (
                     PARTITION BY seller_entity_id, buyer_entity_id ORDER BY period_id
                   ) closing_minor
            FROM gold.fct_intercompany_transactions
        ), failures AS (
            SELECT transaction.intercompany_transaction_id object_ref
            FROM gold.fct_intercompany_transactions transaction
            WHERE seller_admission_decision <> 'ADMITTED' OR buyer_admission_decision <> 'ADMITTED'
               OR elimination_line_count <> 4
               OR elimination_debit_minor <> 2 * amount_minor
               OR elimination_credit_minor <> 2 * amount_minor
               OR elimination_accounting_event_ref IS NULL
            UNION ALL
            SELECT balance.seller_entity_id
            FROM gold.fct_intercompany_balances balance
            JOIN cumulative USING (period_id, seller_entity_id, buyer_entity_id)
            WHERE balance.seller_receivable_minor <> cumulative.closing_minor
               OR balance.buyer_payable_minor <> cumulative.closing_minor
        ) SELECT COUNT(*) FROM failures
        """,
    ),
    (
        "B2_ARGUS_RESULTS_PRESERVE_EXCEPTIONS",
        """
        SELECT COUNT(*) FROM (
            SELECT test_result_id FROM gold.fct_fixed_asset_control_results
            WHERE status = 'PASS' AND difference_minor <> 0
            UNION ALL
            SELECT test_result_id FROM gold.fct_statutory_subledger_controls
            WHERE (status = 'PASS' AND difference_minor <> 0)
               OR (status = 'EXCEPTION' AND NOT (
                   subledger_domain = 'PREPAYMENT'
                   AND observation_type = 'QUARANTINED_DUPLICATE_SOURCE'
               ))
            UNION ALL SELECT 'EXPECTED_EXCEPTION'
            WHERE (SELECT COUNT(*) FROM gold.fct_statutory_subledger_controls
                   WHERE status = 'EXCEPTION' AND subledger_domain = 'PREPAYMENT'
                     AND observation_type = 'QUARANTINED_DUPLICATE_SOURCE') <> 1
        )
        """,
    ),
    (
        "Q_FINANCE_V2_REGISTRY_CLOSURE",
        """
        SELECT COUNT(*) FROM (
            SELECT registry.dataset_id
            FROM governance.q_finance_v2_dataset_registry registry
            LEFT JOIN information_schema.tables physical
              ON registry.relation_schema = physical.table_schema
             AND registry.relation_name = physical.table_name
            WHERE physical.table_name IS NULL
            UNION ALL SELECT 'COUNT'
            WHERE (SELECT COUNT(*) FROM governance.q_finance_v2_dataset_registry) <> 42
        )
        """,
    ),
    (
        "B2_REPORTING_VERSION_BINDING",
        """
        SELECT COUNT(*) FROM (
            SELECT reporting_version_ref, close_status, reliability_status FROM gold.fct_fixed_asset_movements
            UNION ALL SELECT reporting_version_ref, close_status, reliability_status FROM gold.fct_bank_transactions
            UNION ALL SELECT reporting_version_ref, close_status, reliability_status FROM gold.fct_bank_reconciliations
            UNION ALL SELECT reporting_version_ref, close_status, reliability_status FROM gold.fct_debt_schedule
            UNION ALL SELECT reporting_version_ref, close_status, reliability_status FROM gold.fct_lease_schedule
            UNION ALL SELECT reporting_version_ref, close_status, reliability_status FROM gold.fct_tax_schedule
            UNION ALL SELECT reporting_version_ref, close_status, reliability_status FROM gold.fct_equity_movements
            UNION ALL SELECT reporting_version_ref, close_status, reliability_status FROM gold.fct_accrual_schedule
            UNION ALL SELECT reporting_version_ref, close_status, reliability_status FROM gold.fct_prepayment_schedule
        ) WHERE reporting_version_ref IS NULL OR close_status <> 'HARD_CLOSED'
             OR reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
        """,
    ),
    (
        "B2_HERMES_ADMISSION_OUTCOMES",
        """
        SELECT COUNT(*) FROM gold.fct_source_admissions
        WHERE (admission_decision IN ('ADMITTED', 'ADMITTED_WITH_WARNING') AND (
                   candidate_business_event_ref IS NULL OR business_event_semantic_hash IS NULL
              ))
           OR (admission_decision = 'QUARANTINED' AND (
                   duplicate_of_ref IS NULL OR quarantine_ref IS NULL
              ))
           OR admission_decision NOT IN (
               'ADMITTED', 'ADMITTED_WITH_WARNING', 'QUARANTINED'
           )
        """,
    ),
)
