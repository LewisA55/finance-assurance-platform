"""Independent Slice C1 mart and serving-layer controls."""


from __future__ import annotations

C1_CONTROL_QUERIES = (
    (
        "C1_MART_POPULATION",
        """
        WITH cfo_operating_metric_expected AS (
            SELECT (
                (SELECT COUNT(*)*3 FROM gold.mart_financial_performance_monthly WHERE scope_id='NEXUS-GROUP')
                +(SELECT COUNT(*) FROM gold.mart_cash_flow_liquidity_monthly WHERE scope_id='NEXUS-GROUP')
                +(SELECT COUNT(*)*2 FROM (SELECT period_id,currency FROM gold.mart_o2c_customer_collections_monthly GROUP BY 1,2))
                +(SELECT COUNT(*)*2 FROM (SELECT period_id,currency FROM gold.mart_saas_performance_monthly GROUP BY 1,2))
                +(SELECT COUNT(*) FROM (SELECT period_id,currency FROM gold.mart_workforce_cost_monthly GROUP BY 1,2))
                +(SELECT COUNT(*) FROM (SELECT period_id,currency FROM gold.mart_fixed_asset_capex_monthly GROUP BY 1,2))
                +(SELECT COUNT(*) FROM gold.mart_capital_structure_monthly WHERE scope_id='NEXUS-GROUP')
            )::BIGINT expected_rows
        ), nonempty AS (
            SELECT 'D79' model_name,(SELECT COUNT(*) FROM gold.mart_financial_performance_monthly) actual_rows
            UNION ALL SELECT 'D80',(SELECT COUNT(*) FROM gold.mart_balance_sheet_monthly)
            UNION ALL SELECT 'D81',(SELECT COUNT(*) FROM gold.mart_cash_flow_liquidity_monthly)
            UNION ALL SELECT 'D82',(SELECT COUNT(*) FROM gold.mart_o2c_customer_collections_monthly)
            UNION ALL SELECT 'D83',(SELECT COUNT(*) FROM gold.mart_revenue_waterfall_monthly)
            UNION ALL SELECT 'D84',(SELECT COUNT(*) FROM gold.mart_ap_working_capital_monthly)
            UNION ALL SELECT 'D85',(SELECT COUNT(*) FROM gold.mart_workforce_cost_monthly)
            UNION ALL SELECT 'D86',(SELECT COUNT(*) FROM gold.mart_saas_performance_monthly)
            UNION ALL SELECT 'D87',(SELECT COUNT(*) FROM gold.mart_fixed_asset_capex_monthly)
            UNION ALL SELECT 'D88',(SELECT COUNT(*) FROM gold.mart_capital_structure_monthly)
            UNION ALL SELECT 'D89',(SELECT COUNT(*) FROM gold.mart_tax_equity_monthly)
            UNION ALL SELECT 'D90',(SELECT COUNT(*) FROM gold.mart_planning_performance_monthly)
            UNION ALL SELECT 'D91',(SELECT COUNT(*) FROM gold.mart_cfo_presented_financials)
            UNION ALL SELECT 'D92',(SELECT COUNT(*) FROM gold.mart_cfo_presented_operating_metrics)
            UNION ALL SELECT 'D93',(SELECT COUNT(*) FROM gold.mart_cfo_metric_readiness)
            UNION ALL SELECT 'D94',(SELECT COUNT(*) FROM gold.mart_executive_cfo_command_center)
            UNION ALL SELECT 'D95',(SELECT COUNT(*) FROM gold.mart_model_actuals_feed)
            UNION ALL SELECT 'D96',(SELECT COUNT(*) FROM gold.mart_model_working_capital_drivers)
            UNION ALL SELECT 'D97',(SELECT COUNT(*) FROM gold.mart_model_capital_schedules)
            UNION ALL SELECT 'D98',(SELECT COUNT(*) FROM gold.mart_model_planning_inputs)
            UNION ALL SELECT 'D99',(SELECT COUNT(*) FROM gold.mart_model_readiness_controls)
        ), closed AS (
            SELECT 'FINANCIAL' model_name,(SELECT COUNT(*) FROM gold.mart_financial_performance_monthly) actual_rows,
                   (SELECT COUNT(DISTINCT reporting_version_ref) FROM gold.fct_statutory_statement_lines) expected_rows
            UNION ALL SELECT 'BALANCE_SHEET',(SELECT COUNT(*) FROM gold.mart_balance_sheet_monthly),(SELECT COUNT(DISTINCT reporting_version_ref) FROM gold.fct_statutory_statement_lines)
            UNION ALL SELECT 'CASH_FLOW',(SELECT COUNT(*) FROM gold.mart_cash_flow_liquidity_monthly),(SELECT COUNT(*) FROM gold.fct_cash_flow_reconciliation)
            UNION ALL SELECT 'CFO_FINANCIALS',(SELECT COUNT(*) FROM gold.mart_cfo_presented_financials),(SELECT COUNT(*) FROM gold.fct_statutory_statement_lines)
            UNION ALL SELECT 'CFO_METRICS',(SELECT COUNT(*) FROM gold.mart_cfo_presented_operating_metrics),(SELECT expected_rows FROM cfo_operating_metric_expected)
            UNION ALL SELECT 'MODEL_ACTUALS',(SELECT COUNT(*) FROM gold.mart_model_actuals_feed),(SELECT COUNT(*) FROM gold.fct_statutory_trial_balance)
            UNION ALL SELECT 'PLANNING',(SELECT COUNT(*) FROM gold.mart_planning_performance_monthly),(SELECT COUNT(*) FROM gold.fct_planning_variance_source)
            UNION ALL SELECT 'MODEL_PLANNING',(SELECT COUNT(*) FROM gold.mart_model_planning_inputs),(SELECT COUNT(*) FROM gold.fct_forecast_plan_lines)
            UNION ALL SELECT 'CFO_READINESS',(SELECT COUNT(*) FROM gold.mart_cfo_metric_readiness),11
            UNION ALL SELECT 'MODEL_READINESS',(SELECT COUNT(*) FROM gold.mart_model_readiness_controls),15
        ) SELECT COUNT(*) FROM (
            SELECT model_name FROM nonempty WHERE actual_rows=0
            UNION ALL SELECT model_name FROM closed WHERE actual_rows<>expected_rows
        )
        """,
    ),
    (
        "C1_STATUTORY_MARTS_RECONCILE",
        """
        WITH statement AS (
            SELECT period_id, scope_id, reporting_version_ref,
                   SUM(CASE WHEN statement_class = 'INCOME_STATEMENT'
                                 AND statement_line IN ('subscription_revenue','services_revenue')
                            THEN amount_minor ELSE 0 END)::BIGINT revenue_minor,
                   MAX(CASE WHEN statement_class = 'INCOME_STATEMENT' AND statement_line = 'net_income' THEN amount_minor END)::BIGINT net_income_minor,
                   MAX(CASE WHEN statement_class = 'BALANCE_SHEET' AND statement_line = 'total_assets' THEN amount_minor END)::BIGINT total_assets_minor,
                   MAX(CASE WHEN statement_class = 'BALANCE_SHEET' AND statement_line = 'total_liabilities_and_equity' THEN amount_minor END)::BIGINT total_liabilities_and_equity_minor
            FROM gold.fct_statutory_statement_lines GROUP BY 1,2,3
        ), failures AS (
            SELECT financial.reporting_version_ref object_ref
            FROM gold.mart_financial_performance_monthly financial
            INNER JOIN statement USING (period_id,scope_id,reporting_version_ref)
            WHERE financial.revenue_minor <> statement.revenue_minor OR financial.net_income_minor <> statement.net_income_minor
            UNION ALL
            SELECT balance.reporting_version_ref
            FROM gold.mart_balance_sheet_monthly balance
            INNER JOIN statement USING (period_id,scope_id,reporting_version_ref)
            WHERE balance.total_assets_minor <> statement.total_assets_minor
               OR balance.total_liabilities_and_equity_minor <> statement.total_liabilities_and_equity_minor
               OR balance.balance_sheet_difference_minor <> 0
            UNION ALL
            SELECT mart.reporting_version_ref
            FROM gold.mart_cash_flow_liquidity_monthly mart
            INNER JOIN gold.fct_cash_flow_reconciliation source
              USING (period_id,scope_id,reporting_version_ref,currency)
            WHERE mart.opening_cash_minor <> source.opening_cash_minor
               OR mart.closing_cash_minor <> source.closing_cash_minor
               OR mart.unreconciled_difference_minor <> 0
        ) SELECT COUNT(*) FROM failures
        """,
    ),
    (
        "C1_OPERATIONAL_MARTS_RECONCILE",
        """
        WITH o2c_mart AS (
            SELECT period_id, SUM(billings_minor)::BIGINT billings_minor,
                   SUM(collections_minor)::BIGINT collections_minor,
                   SUM(closing_ar_minor)::BIGINT closing_ar_minor
            FROM gold.mart_o2c_customer_collections_monthly GROUP BY 1
        ), o2c_source AS (
            SELECT period.period_id,
                   (SELECT SUM(reporting_amount_minor) FROM gold.fct_customer_invoices invoice WHERE invoice.period_id=period.period_id)::BIGINT billings_minor,
                   (SELECT SUM(reporting_amount_minor) FROM gold.fct_customer_payments payment WHERE payment.period_id=period.period_id)::BIGINT collections_minor,
                   (SELECT SUM(reporting_open_amount_minor) FROM gold.fct_ar_ageing_daily ageing
                     WHERE ageing.period_id=period.period_id AND snapshot_date=last_day(snapshot_date))::BIGINT closing_ar_minor
            FROM gold.dim_period period WHERE period.is_actual_period
        ), failures AS (
            SELECT mart.period_id object_ref FROM o2c_mart mart INNER JOIN o2c_source source USING (period_id)
            WHERE mart.billings_minor<>source.billings_minor OR mart.collections_minor<>source.collections_minor OR mart.closing_ar_minor<>source.closing_ar_minor
            UNION ALL SELECT 'WORKFORCE'
            WHERE (SELECT SUM(payroll_cost_minor) FROM gold.mart_workforce_cost_monthly)
               <> (SELECT SUM(reporting_payroll_cost_minor) FROM gold.fct_payroll_expense_lines)
            UNION ALL SELECT period_id FROM gold.mart_revenue_waterfall_monthly
            WHERE rollforward_difference_minor<>0 OR schedule_difference_minor<>0
            UNION ALL SELECT 'SAAS'
            WHERE (SELECT SUM(ending_arr_minor) FROM gold.mart_saas_performance_monthly)
               <> (SELECT SUM(saas.ending_arr_minor)
                   FROM gold.fct_saas_monthly_movements saas
                   INNER JOIN gold.dim_reporting_version version
                     ON saas.period_id=version.period_id AND version.scope_id='NEXUS-GROUP')
        ) SELECT COUNT(*) FROM failures
        """,
    ),
    (
        "C1_CAPITAL_MARTS_RECONCILE",
        """
        WITH fixed_mart AS (
            SELECT period_id,legal_entity_id,asset_class,SUM(capex_additions_minor)::BIGINT additions_minor,
                   SUM(closing_net_book_value_minor)::BIGINT closing_minor
            FROM gold.mart_fixed_asset_capex_monthly GROUP BY 1,2,3
        ), fixed_source AS (
            SELECT period_id,legal_entity_id,asset_class,SUM(gross_addition_minor)::BIGINT additions_minor,
                   SUM(closing_net_book_value_minor)::BIGINT closing_minor
            FROM gold.fct_fixed_asset_movements GROUP BY 1,2,3
        ), debt_source AS (
            SELECT period_id,SUM(closing_principal_minor)::BIGINT closing_debt_minor
            FROM gold.fct_debt_schedule GROUP BY 1
        ), failures AS (
            SELECT mart.period_id object_ref FROM fixed_mart mart INNER JOIN fixed_source source USING(period_id,legal_entity_id,asset_class)
            WHERE mart.additions_minor<>source.additions_minor OR mart.closing_minor<>source.closing_minor
            UNION ALL SELECT mart.period_id FROM gold.mart_capital_structure_monthly mart INNER JOIN debt_source source USING(period_id)
            WHERE mart.scope_id='NEXUS-GROUP' AND mart.closing_debt_minor<>source.closing_debt_minor
            UNION ALL SELECT reporting_version_ref FROM gold.mart_tax_equity_monthly WHERE reconciliation_status<>'RECONCILED'
        ) SELECT COUNT(*) FROM failures
        """,
    ),
    (
        "C1_PLANNING_BOUNDARY",
        """
        SELECT COUNT(*) FROM (
            SELECT planning_performance_hk object_ref FROM gold.mart_planning_performance_monthly
            WHERE is_statutory_actual OR value_authority<>'MANAGEMENT_SOURCE_REPORT'
            UNION ALL
            SELECT model_planning_input_hk FROM gold.mart_model_planning_inputs
            WHERE is_governed_pythia_snapshot OR actuals_scope_id<>'NEXUS-GROUP'
               OR actuals_close_status<>'HARD_CLOSED'
               OR actuals_reliability_status<>'RELIABLE_FOR_STATUTORY_ACTUALS'
        )
        """,
    ),
    (
        "C1_MODEL_ACTUALS_REPLAY",
        """
        SELECT COUNT(*)
        FROM gold.mart_model_actuals_feed feed
        INNER JOIN gold.fct_statutory_trial_balance trial USING(period_id,scope_id,account_id,currency,reporting_version_ref)
        INNER JOIN gold.dim_gl_account account USING(account_id)
        WHERE feed.opening_balance_minor<>trial.opening_balance_minor
           OR feed.closing_balance_minor<>trial.closing_balance_minor
           OR feed.model_actual_amount_minor<>CASE
                WHEN account.statement_class='BALANCE_SHEET' AND account.normal_balance='CREDIT' THEN -trial.closing_balance_minor
                WHEN account.statement_class='BALANCE_SHEET' THEN trial.closing_balance_minor
                ELSE trial.credit_activity_minor-trial.debit_activity_minor
                     +trial.elimination_credit_minor-trial.elimination_debit_minor END
        """,
    ),
    (
        "C1_PRESENTATION_COVERAGE",
        """
        WITH cfo_operating_metric_expected AS (
            SELECT (
                (SELECT COUNT(*)*3 FROM gold.mart_financial_performance_monthly WHERE scope_id='NEXUS-GROUP')
                +(SELECT COUNT(*) FROM gold.mart_cash_flow_liquidity_monthly WHERE scope_id='NEXUS-GROUP')
                +(SELECT COUNT(*)*2 FROM (SELECT period_id,currency FROM gold.mart_o2c_customer_collections_monthly GROUP BY 1,2))
                +(SELECT COUNT(*)*2 FROM (SELECT period_id,currency FROM gold.mart_saas_performance_monthly GROUP BY 1,2))
                +(SELECT COUNT(*) FROM (SELECT period_id,currency FROM gold.mart_workforce_cost_monthly GROUP BY 1,2))
                +(SELECT COUNT(*) FROM (SELECT period_id,currency FROM gold.mart_fixed_asset_capex_monthly GROUP BY 1,2))
                +(SELECT COUNT(*) FROM gold.mart_capital_structure_monthly WHERE scope_id='NEXUS-GROUP')
            )::BIGINT expected_rows
        ), command_center_expected AS (
            SELECT COUNT(*)::BIGINT expected_rows
            FROM gold.mart_financial_performance_monthly financial
            INNER JOIN gold.mart_balance_sheet_monthly balance USING(period_id,scope_id,reporting_version_ref,currency)
            INNER JOIN gold.mart_cash_flow_liquidity_monthly cash USING(period_id,scope_id,reporting_version_ref,currency)
            INNER JOIN gold.mart_capital_structure_monthly capital USING(period_id,scope_id,reporting_version_ref,currency)
            INNER JOIN gold.mart_ap_working_capital_monthly working USING(period_id,currency)
            INNER JOIN (SELECT DISTINCT period_id FROM gold.mart_o2c_customer_collections_monthly) o2c USING(period_id)
            INNER JOIN (SELECT DISTINCT period_id FROM gold.mart_saas_performance_monthly) saas USING(period_id)
            INNER JOIN (SELECT DISTINCT period_id FROM gold.mart_workforce_cost_monthly) workforce USING(period_id)
            INNER JOIN (SELECT DISTINCT period_id FROM gold.mart_fixed_asset_capex_monthly) capex USING(period_id)
            WHERE financial.scope_id='NEXUS-GROUP'
        ) SELECT COUNT(*) FROM (
            SELECT metric_id object_ref FROM gold.mart_cfo_metric_readiness WHERE readiness_status<>'READY'
            UNION ALL SELECT period_id FROM gold.mart_executive_cfo_command_center
            WHERE presentation_status<>'READY' OR not_ready_metric_count<>0
            UNION ALL SELECT 'COMMAND_CENTER_MONTHS'
            WHERE (SELECT COUNT(*) FROM gold.mart_executive_cfo_command_center)
               <> (SELECT expected_rows FROM command_center_expected)
            UNION ALL SELECT 'OPERATING_METRICS'
            WHERE (SELECT COUNT(*) FROM gold.mart_cfo_presented_operating_metrics)
               <> (SELECT expected_rows FROM cfo_operating_metric_expected)
        )
        """,
    ),
    (
        "C1_MODEL_READINESS_REPLAYS",
        """
        WITH periods AS (
            SELECT COUNT(*)::BIGINT period_count FROM gold.dim_reporting_version
            WHERE scope_id='NEXUS-GROUP' AND close_status='HARD_CLOSED'
              AND reliability_status='RELIABLE_FOR_STATUTORY_ACTUALS'
        ), replay AS (
            SELECT 'C1-RDY-01' control_id,(SELECT period_count FROM periods) actual_value,60::BIGINT expected_value
            UNION ALL SELECT 'C1-RDY-02',(SELECT COUNT(*) FROM gold.mart_balance_sheet_monthly WHERE scope_id='NEXUS-GROUP'),(SELECT period_count FROM periods)
            UNION ALL SELECT 'C1-RDY-03',(SELECT COUNT(*) FROM gold.mart_balance_sheet_monthly WHERE balance_sheet_difference_minor<>0),0
            UNION ALL SELECT 'C1-RDY-04',(SELECT COUNT(*) FROM gold.mart_cash_flow_liquidity_monthly WHERE unreconciled_difference_minor<>0 OR reconciliation_status<>'RECONCILED'),0
            UNION ALL SELECT 'C1-RDY-05',(SELECT COUNT(DISTINCT period_id) FROM gold.mart_model_actuals_feed WHERE scope_id='NEXUS-GROUP'),(SELECT period_count FROM periods)
            UNION ALL SELECT 'C1-RDY-06',(SELECT COUNT(DISTINCT period_id) FROM gold.mart_model_working_capital_drivers),
                (SELECT COUNT(DISTINCT working.period_id)
                 FROM gold.mart_ap_working_capital_monthly working
                 INNER JOIN gold.mart_financial_performance_monthly financial
                   ON working.period_id=financial.period_id AND working.currency=financial.currency
                  AND financial.scope_id='NEXUS-GROUP')
            UNION ALL SELECT 'C1-RDY-07',(SELECT COUNT(DISTINCT period_id) FROM gold.mart_model_capital_schedules WHERE schedule_domain='FIXED_ASSET'),(SELECT COUNT(DISTINCT period_id) FROM gold.fct_fixed_asset_movements)
            UNION ALL SELECT 'C1-RDY-08',(SELECT COUNT(DISTINCT period_id) FROM gold.mart_model_capital_schedules WHERE schedule_domain='DEBT'),(SELECT COUNT(DISTINCT period_id) FROM gold.fct_debt_schedule)
            UNION ALL SELECT 'C1-RDY-09',(SELECT COUNT(DISTINCT period_id) FROM gold.mart_model_capital_schedules WHERE schedule_domain='LEASE'),(SELECT COUNT(DISTINCT period_id) FROM gold.fct_lease_schedule)
            UNION ALL SELECT 'C1-RDY-10',(SELECT COUNT(DISTINCT period_id) FROM gold.mart_model_capital_schedules WHERE schedule_domain='TAX'),(SELECT COUNT(DISTINCT period_id) FROM gold.fct_tax_schedule)
            UNION ALL SELECT 'C1-RDY-11',(SELECT COUNT(DISTINCT period_id) FROM gold.mart_saas_performance_monthly),(SELECT COUNT(DISTINCT saas.period_id) FROM gold.fct_saas_monthly_movements saas INNER JOIN gold.dim_reporting_version version ON saas.period_id=version.period_id AND version.scope_id='NEXUS-GROUP')
            UNION ALL SELECT 'C1-RDY-12',(SELECT COUNT(*) FROM gold.dim_planning_scenario scenario LEFT JOIN gold.dim_reporting_version actuals ON scenario.actuals_reporting_version_ref=actuals.reporting_version_ref WHERE actuals.reporting_version_ref IS NULL OR scenario.cutover_period<>actuals.period_id OR actuals.scope_id<>'NEXUS-GROUP' OR actuals.reliability_status<>'RELIABLE_FOR_STATUTORY_ACTUALS' OR scenario.actuals_source_package_digest<>actuals.source_package_digest),0
            UNION ALL SELECT 'C1-RDY-13',(SELECT COUNT(*) FROM gold.dim_planning_scenario WHERE scenario_code='BASE' AND approval_status='APPROVED' AND locked_flag),1
            UNION ALL SELECT 'C1-RDY-14',(SELECT COUNT(*) FROM gold.mart_planning_performance_monthly WHERE is_statutory_actual OR value_authority<>'MANAGEMENT_SOURCE_REPORT'),0
            UNION ALL SELECT 'C1-RDY-15',(SELECT COUNT(*) FROM gold.mart_cfo_metric_readiness WHERE readiness_status<>'READY'),0
        )
        SELECT COUNT(*) FROM replay
        FULL OUTER JOIN gold.mart_model_readiness_controls observed USING(control_id)
        WHERE replay.control_id IS NULL OR observed.control_id IS NULL
           OR replay.actual_value<>observed.actual_value OR replay.expected_value<>observed.expected_value
           OR observed.result_status<>'PASS' OR observed.first_failure_ref IS NOT NULL
           OR observed.value_authority<>'VALIDATOR_PRODUCED'
        """,
    ),
    (
        "C1_MONEY_IS_INTEGER_MINOR_UNITS",
        """
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema='gold' AND table_name LIKE 'mart_%'
          AND column_name LIKE '%_minor' AND data_type<>'BIGINT'
        """,
    ),
    (
        "Q_FINANCE_V5_REGISTRY_CLOSURE",
        """
        WITH count_failures AS (
            SELECT 'DATASETS' object_ref WHERE (SELECT COUNT(*) FROM governance.q_finance_v5_dataset_registry)<>99
            UNION ALL SELECT 'RELATIONSHIPS' WHERE (SELECT COUNT(*) FROM governance.q_finance_v5_relationship_registry)<>187
            UNION ALL SELECT 'MEASURES' WHERE (SELECT COUNT(*) FROM governance.q_finance_v5_measure_registry)<>189
            UNION ALL SELECT 'LINEAGE' WHERE (SELECT COUNT(*) FROM governance.q_finance_v5_lineage_registry)<>99
        ), relation_failures AS (
            SELECT dataset.dataset_id object_ref FROM governance.q_finance_v5_dataset_registry dataset
            LEFT JOIN information_schema.tables relation ON relation.table_schema=dataset.relation_schema AND relation.table_name=dataset.relation_name
            WHERE relation.table_name IS NULL OR dataset.registry_version<>5 OR dataset.finance_model_ref<>'Q-FINANCE-C1@v1'
        ), endpoint_failures AS (
            SELECT relationship.relationship_id object_ref FROM governance.q_finance_v5_relationship_registry relationship
            LEFT JOIN governance.q_finance_v5_dataset_registry source ON relationship.from_dataset_id=source.dataset_id
            LEFT JOIN governance.q_finance_v5_dataset_registry target ON relationship.to_dataset_id=target.dataset_id
            WHERE source.dataset_id IS NULL OR target.dataset_id IS NULL
        ), measure_failures AS (
            SELECT measure.measure_id object_ref FROM governance.q_finance_v5_measure_registry measure
            INNER JOIN governance.q_finance_v5_dataset_registry dataset USING(dataset_id)
            LEFT JOIN information_schema.columns field ON field.table_schema=dataset.relation_schema AND field.table_name=dataset.relation_name AND field.column_name=measure.source_field
            WHERE field.column_name IS NULL
        ), lineage_failures AS (
            SELECT COALESCE(dataset.dataset_id,lineage.dataset_id) object_ref
            FROM governance.q_finance_v5_dataset_registry dataset
            FULL OUTER JOIN governance.q_finance_v5_lineage_registry lineage USING(dataset_id)
            WHERE dataset.dataset_id IS NULL OR lineage.dataset_id IS NULL
        ) SELECT COUNT(*) FROM (
            SELECT * FROM count_failures UNION ALL SELECT * FROM relation_failures
            UNION ALL SELECT * FROM endpoint_failures UNION ALL SELECT * FROM measure_failures
            UNION ALL SELECT * FROM lineage_failures
        )
        """,
    ),
    (
        "C1_MART_PACKAGE_AUTHORITY",
        """
        SELECT COUNT(*) FROM (
            SELECT dataset_id object_ref FROM governance.q_finance_v5_dataset_registry
            WHERE dataset_id BETWEEN 'QF-D79' AND 'QF-D99'
              AND (source_data_ref<>(
                    SELECT MIN(_source_data_ref)
                    FROM gold.mart_financial_performance_monthly
                  )
                OR finance_model_ref<>'Q-FINANCE-C1@v1')
            UNION ALL SELECT 'DATASET_COUNT'
            WHERE (SELECT COUNT(*) FROM governance.q_finance_v5_dataset_registry WHERE dataset_id BETWEEN 'QF-D79' AND 'QF-D99')<>21
            UNION ALL SELECT table_name FROM information_schema.tables
            WHERE table_schema='gold' AND table_name='mart_opening_balance_sheet'
        )
        """,
    ),
    (
        "C1_NO_PROXY_FINANCIAL_ACTUALS",
        """
        SELECT COUNT(*) FROM (
            SELECT financial_performance_hk object_ref FROM gold.mart_financial_performance_monthly
            WHERE value_authority<>'STATUTORY_STATEMENT'
            UNION ALL SELECT model_actuals_feed_hk FROM gold.mart_model_actuals_feed
            WHERE value_authority<>'STATUTORY_TRIAL_BALANCE'
            UNION ALL SELECT model_capital_schedule_hk FROM gold.mart_model_capital_schedules
            WHERE schedule_domain='FIXED_ASSET' AND cash_flow_minor IS NOT NULL
            UNION ALL SELECT planning_performance_hk FROM gold.mart_planning_performance_monthly
            WHERE is_statutory_actual OR value_authority<>'MANAGEMENT_SOURCE_REPORT'
        )
        """,
    ),
)
