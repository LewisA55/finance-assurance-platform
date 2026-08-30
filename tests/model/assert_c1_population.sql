{{ config(tags=['slice_c']) }}

with nonempty as (
    select 'mart_financial_performance_monthly' model_name, (select count(*) from {{ ref('mart_financial_performance_monthly') }}) actual_rows
    union all select 'mart_balance_sheet_monthly', (select count(*) from {{ ref('mart_balance_sheet_monthly') }})
    union all select 'mart_cash_flow_liquidity_monthly', (select count(*) from {{ ref('mart_cash_flow_liquidity_monthly') }})
    union all select 'mart_o2c_customer_collections_monthly', (select count(*) from {{ ref('mart_o2c_customer_collections_monthly') }})
    union all select 'mart_revenue_waterfall_monthly', (select count(*) from {{ ref('mart_revenue_waterfall_monthly') }})
    union all select 'mart_ap_working_capital_monthly', (select count(*) from {{ ref('mart_ap_working_capital_monthly') }})
    union all select 'mart_workforce_cost_monthly', (select count(*) from {{ ref('mart_workforce_cost_monthly') }})
    union all select 'mart_saas_performance_monthly', (select count(*) from {{ ref('mart_saas_performance_monthly') }})
    union all select 'mart_fixed_asset_capex_monthly', (select count(*) from {{ ref('mart_fixed_asset_capex_monthly') }})
    union all select 'mart_capital_structure_monthly', (select count(*) from {{ ref('mart_capital_structure_monthly') }})
    union all select 'mart_tax_equity_monthly', (select count(*) from {{ ref('mart_tax_equity_monthly') }})
    union all select 'mart_planning_performance_monthly', (select count(*) from {{ ref('mart_planning_performance_monthly') }})
    union all select 'mart_cfo_presented_financials', (select count(*) from {{ ref('mart_cfo_presented_financials') }})
    union all select 'mart_cfo_presented_operating_metrics', (select count(*) from {{ ref('mart_cfo_presented_operating_metrics') }})
    union all select 'mart_cfo_metric_readiness', (select count(*) from {{ ref('mart_cfo_metric_readiness') }})
    union all select 'mart_executive_cfo_command_center', (select count(*) from {{ ref('mart_executive_cfo_command_center') }})
    union all select 'mart_model_actuals_feed', (select count(*) from {{ ref('mart_model_actuals_feed') }})
    union all select 'mart_model_working_capital_drivers', (select count(*) from {{ ref('mart_model_working_capital_drivers') }})
    union all select 'mart_model_capital_schedules', (select count(*) from {{ ref('mart_model_capital_schedules') }})
    union all select 'mart_model_planning_inputs', (select count(*) from {{ ref('mart_model_planning_inputs') }})
    union all select 'mart_model_readiness_controls', (select count(*) from {{ ref('mart_model_readiness_controls') }})
), closed_populations as (
    select 'FINANCIAL_PERFORMANCE' model_name,
           (select count(*) from {{ ref('mart_financial_performance_monthly') }}) actual_rows,
           (select count(distinct reporting_version_ref) from {{ ref('fct_statutory_statement_lines') }}) expected_rows
    union all select 'BALANCE_SHEET',
           (select count(*) from {{ ref('mart_balance_sheet_monthly') }}),
           (select count(distinct reporting_version_ref) from {{ ref('fct_statutory_statement_lines') }})
    union all select 'CASH_FLOW',
           (select count(*) from {{ ref('mart_cash_flow_liquidity_monthly') }}),
           (select count(*) from {{ ref('fct_cash_flow_reconciliation') }})
    union all select 'CFO_FINANCIALS',
           (select count(*) from {{ ref('mart_cfo_presented_financials') }}),
           (select count(*) from {{ ref('fct_statutory_statement_lines') }})
    union all select 'CFO_OPERATING_METRICS',
           (select count(*) from {{ ref('mart_cfo_presented_operating_metrics') }}),
           (select count(*) * 11 from {{ ref('dim_reporting_version') }} where scope_id = 'NEXUS-GROUP')
    union all select 'MODEL_ACTUALS',
           (select count(*) from {{ ref('mart_model_actuals_feed') }}),
           (select count(*) from {{ ref('fct_statutory_trial_balance') }})
    union all select 'PLANNING_PERFORMANCE',
           (select count(*) from {{ ref('mart_planning_performance_monthly') }}),
           (select count(*) from {{ ref('fct_planning_variance_source') }})
    union all select 'MODEL_PLANNING_INPUTS',
           (select count(*) from {{ ref('mart_model_planning_inputs') }}),
           (select count(*) from {{ ref('fct_forecast_plan_lines') }})
    union all select 'CFO_METRIC_READINESS',
           (select count(*) from {{ ref('mart_cfo_metric_readiness') }}), 11
    union all select 'MODEL_READINESS',
           (select count(*) from {{ ref('mart_model_readiness_controls') }}), 15
)
select model_name from nonempty where actual_rows = 0
union all
select model_name from closed_populations where actual_rows <> expected_rows
