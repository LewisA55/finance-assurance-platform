{{ config(tags=['slice_c']) }}

with additions as (
    select * from (values
        ('QF-D79','mart_financial_performance_monthly','fct_statutory_statement_lines','accounting__statutory_statement_lines','PIVOT_PUBLISHED_STATUTORY_INCOME_STATEMENT'),
        ('QF-D80','mart_balance_sheet_monthly','fct_statutory_statement_lines','accounting__statutory_statement_lines','PIVOT_PUBLISHED_STATUTORY_BALANCE_SHEET'),
        ('QF-D81','mart_cash_flow_liquidity_monthly','fct_cash_flow_reconciliation|fct_debt_schedule|fct_lease_schedule','accounting__cash_flow_reconciliation|treasury__debt_schedule|leases__lease_schedule','COMBINE_RECONCILED_CASH_FLOW_AND_FUNDING_STATE'),
        ('QF-D82','mart_o2c_customer_collections_monthly','fct_customer_invoices|fct_customer_payments|fct_ar_ageing_daily','billing__invoices|billing__payments|billing__ar_ageing_snapshot','AGGREGATE_O2C_EVENTS_AND_MONTH_END_STATE'),
        ('QF-D83','mart_revenue_waterfall_monthly','fct_deferred_revenue_rollforward|fct_revenue_recognition','revenue__deferred_revenue_rollforward|revenue__revenue_recognition_schedule','RECONCILE_REVENUE_SCHEDULE_AND_DEFERRED_ROLLFORWARD'),
        ('QF-D84','mart_ap_working_capital_monthly','fct_working_capital_monthly|fct_vendor_invoices|fct_vendor_payments','procurement__vendor_invoices|procurement__vendor_payments|procurement__ap_ageing_snapshot','ENRICH_GOVERNED_WORKING_CAPITAL_STATE'),
        ('QF-D85','mart_workforce_cost_monthly','fct_payroll_expense_lines|fct_headcount_monthly_snapshot','workforce__payroll_expense_lines|hris__headcount_snapshot','AGGREGATE_POSTED_PAYROLL_AND_MONTH_END_HEADCOUNT'),
        ('QF-D86','mart_saas_performance_monthly','fct_saas_monthly_movements|dim_product|dim_region','billing__subscription_events|billing__subscriptions','ENRICH_GOVERNED_MONTHLY_SAAS_STATE'),
        ('QF-D87','mart_fixed_asset_capex_monthly','fct_fixed_asset_movements','fixed_assets__fixed_asset_movements','AGGREGATE_FIXED_ASSET_ROLLFORWARDS_BY_CLASS'),
        ('QF-D88','mart_capital_structure_monthly','fct_debt_schedule|fct_lease_schedule|fct_statutory_statement_lines','treasury__debt_schedule|leases__lease_schedule|accounting__statutory_statement_lines','COMBINE_DEBT_LEASE_AND_CASH_STATE'),
        ('QF-D89','mart_tax_equity_monthly','fct_tax_schedule|fct_equity_movements|fct_retained_earnings_bridge','tax__tax_schedule|equity__equity_movements|accounting__retained_earnings_bridge','COMBINE_TAX_EQUITY_AND_RETAINED_EARNINGS_ROLLFORWARDS'),
        ('QF-D90','mart_planning_performance_monthly','fct_planning_variance_source|dim_department|dim_gl_account','planning__variance_source_extract','ENRICH_WITHOUT_PROMOTING_MANAGEMENT_SOURCE_REPORT'),
        ('QF-D91','mart_cfo_presented_financials','fct_statutory_statement_lines|dim_period','accounting__statutory_statement_lines','LABEL_PUBLISHED_STATUTORY_LINES_FOR_PRESENTATION'),
        ('QF-D92','mart_cfo_presented_operating_metrics','mart_financial_performance_monthly|mart_cash_flow_liquidity_monthly|mart_o2c_customer_collections_monthly|mart_saas_performance_monthly|mart_workforce_cost_monthly|mart_fixed_asset_capex_monthly|mart_capital_structure_monthly','MULTIPLE_GOVERNED_A24_SOURCES','UNION_TYPED_EXECUTIVE_METRICS_WITH_AUTHORITY'),
        ('QF-D93','mart_cfo_metric_readiness','mart_cfo_presented_operating_metrics','MULTIPLE_GOVERNED_A24_SOURCES','VALIDATE_METRIC_COVERAGE_AND_NULL_POLICY'),
        ('QF-D94','mart_executive_cfo_command_center','EXECUTIVE_C1_MARTS|mart_cfo_metric_readiness','MULTIPLE_GOVERNED_A24_SOURCES','JOIN_GROUP_MONTHLY_EXECUTIVE_METRICS'),
        ('QF-D95','mart_model_actuals_feed','fct_statutory_trial_balance|dim_period|dim_reporting_scope|dim_gl_account','accounting__statutory_trial_balance','PUBLISH_ACCOUNT_LEVEL_VERSIONED_MODEL_ACTUALS'),
        ('QF-D96','mart_model_working_capital_drivers','mart_ap_working_capital_monthly|mart_financial_performance_monthly','MULTIPLE_GOVERNED_A24_SOURCES','DERIVE_LAGGED_WORKING_CAPITAL_DRIVERS'),
        ('QF-D97','mart_model_capital_schedules','fct_fixed_asset_movements|fct_debt_schedule|fct_lease_schedule|fct_tax_schedule|fct_equity_movements','MULTIPLE_GOVERNED_A24_SUBLEDGERS','NORMALISE_TYPED_CAPITAL_SCHEDULES_WITHOUT_LOSING_DOMAIN'),
        ('QF-D98','mart_model_planning_inputs','fct_forecast_plan_lines|fct_budget_plan_lines|dim_planning_scenario','planning__forecast_lines|planning__budget_lines|planning__forecast_versions','COMBINE_SCENARIO_INPUTS_AND_EXACT_ACTUALS_BOUNDARY'),
        ('QF-D99','mart_model_readiness_controls','C1_MARTS|dim_reporting_version|dim_planning_scenario','MULTIPLE_GOVERNED_A24_SOURCES','EXECUTE_CURRENT_STATE_MODEL_READINESS_VALIDATORS')
    ) t(dataset_id, gold_model, direct_dependencies, a24_bronze_sources, transformation_class)
)
select * from {{ ref('q_finance_v4_lineage_registry') }}
union all
select * from additions
