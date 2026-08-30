{{ config(tags=['slice_c']) }}

-- depends_on: {{ ref('mart_financial_performance_monthly') }}
-- depends_on: {{ ref('mart_balance_sheet_monthly') }}
-- depends_on: {{ ref('mart_cash_flow_liquidity_monthly') }}
-- depends_on: {{ ref('mart_o2c_customer_collections_monthly') }}
-- depends_on: {{ ref('mart_revenue_waterfall_monthly') }}
-- depends_on: {{ ref('mart_ap_working_capital_monthly') }}
-- depends_on: {{ ref('mart_workforce_cost_monthly') }}
-- depends_on: {{ ref('mart_saas_performance_monthly') }}
-- depends_on: {{ ref('mart_fixed_asset_capex_monthly') }}
-- depends_on: {{ ref('mart_capital_structure_monthly') }}
-- depends_on: {{ ref('mart_tax_equity_monthly') }}
-- depends_on: {{ ref('mart_planning_performance_monthly') }}
-- depends_on: {{ ref('mart_cfo_presented_financials') }}
-- depends_on: {{ ref('mart_cfo_presented_operating_metrics') }}
-- depends_on: {{ ref('mart_cfo_metric_readiness') }}
-- depends_on: {{ ref('mart_executive_cfo_command_center') }}
-- depends_on: {{ ref('mart_model_actuals_feed') }}
-- depends_on: {{ ref('mart_model_working_capital_drivers') }}
-- depends_on: {{ ref('mart_model_capital_schedules') }}
-- depends_on: {{ ref('mart_model_planning_inputs') }}
-- depends_on: {{ ref('mart_model_readiness_controls') }}

with inherited as (
    select
        registry_id, 5 as registry_version, dataset_id, dataset_version,
        relation_schema, relation_name, grain, semantic_owner, model_class,
        consumption_class, reliability_purpose, source_data_ref,
        source_package_digest, '{{ var("finance_model_ref") }}' as finance_model_ref,
        money_contract
    from {{ ref('q_finance_v4_dataset_registry') }}
), additions as (
    select * from (values
        ('QF-D79','mart_financial_performance_monthly','ONE_ROW_PER_PERIOD_SCOPE_REPORTING_VERSION','ATLAS','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_FINANCIAL_PERFORMANCE'),
        ('QF-D80','mart_balance_sheet_monthly','ONE_ROW_PER_PERIOD_SCOPE_REPORTING_VERSION','ATLAS','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_BALANCE_SHEET'),
        ('QF-D81','mart_cash_flow_liquidity_monthly','ONE_ROW_PER_PERIOD_SCOPE_REPORTING_VERSION','ATLAS','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_CASH_FLOW_AND_LIQUIDITY'),
        ('QF-D82','mart_o2c_customer_collections_monthly','ONE_ROW_PER_PERIOD_REGION_CUSTOMER_SEGMENT','ATLAS','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_CUSTOMER_COLLECTIONS'),
        ('QF-D83','mart_revenue_waterfall_monthly','ONE_ROW_PER_PERIOD_REPORTING_CURRENCY','ATLAS','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_REVENUE_WATERFALL'),
        ('QF-D84','mart_ap_working_capital_monthly','ONE_ROW_PER_PERIOD_REPORTING_CURRENCY','ATLAS','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_AP_AND_WORKING_CAPITAL'),
        ('QF-D85','mart_workforce_cost_monthly','ONE_ROW_PER_PERIOD_DEPARTMENT_REGION','ATLAS','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_WORKFORCE_COST'),
        ('QF-D86','mart_saas_performance_monthly','ONE_ROW_PER_PERIOD_PRODUCT_REGION_CUSTOMER_SEGMENT','ATLAS','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_SAAS_PERFORMANCE'),
        ('QF-D87','mart_fixed_asset_capex_monthly','ONE_ROW_PER_PERIOD_ENTITY_ASSET_CLASS','ATLAS','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_FIXED_ASSET_AND_CAPEX'),
        ('QF-D88','mart_capital_structure_monthly','ONE_ROW_PER_PERIOD_SCOPE_REPORTING_CURRENCY','ATLAS','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_CAPITAL_STRUCTURE'),
        ('QF-D89','mart_tax_equity_monthly','ONE_ROW_PER_PERIOD_SCOPE_REPORTING_CURRENCY','ATLAS','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_TAX_AND_EQUITY'),
        ('QF-D90','mart_planning_performance_monthly','ONE_ROW_PER_SOURCE_VARIANCE_LINE','PYTHIA','ANALYTICAL_MART','EXECUTIVE','EXECUTIVE_MANAGEMENT_VARIANCE'),
        ('QF-D91','mart_cfo_presented_financials','ONE_ROW_PER_REPORTING_VERSION_STATEMENT_LINE','ATLAS','PRESENTATION_MART','PRESENTATION','CFO_PRESENTED_FINANCIALS'),
        ('QF-D92','mart_cfo_presented_operating_metrics','ONE_ROW_PER_PERIOD_EXECUTIVE_METRIC','ATLAS','PRESENTATION_MART','PRESENTATION','CFO_PRESENTED_OPERATING_METRICS'),
        ('QF-D93','mart_cfo_metric_readiness','ONE_ROW_PER_EXECUTIVE_METRIC','ATLAS','PRESENTATION_MART','PRESENTATION','CFO_METRIC_READINESS'),
        ('QF-D94','mart_executive_cfo_command_center','ONE_ROW_PER_GROUP_PERIOD','ATLAS','PRESENTATION_MART','PRESENTATION','CFO_COMMAND_CENTER'),
        ('QF-D95','mart_model_actuals_feed','ONE_ROW_PER_PERIOD_SCOPE_ACCOUNT','ATLAS','MODEL_SERVING_MART','MODEL_SERVING','MODEL_SERVING_ACTUALS'),
        ('QF-D96','mart_model_working_capital_drivers','ONE_ROW_PER_PERIOD_REPORTING_CURRENCY','ATLAS','MODEL_SERVING_MART','MODEL_SERVING','MODEL_SERVING_WORKING_CAPITAL_DRIVERS'),
        ('QF-D97','mart_model_capital_schedules','ONE_ROW_PER_DOMAIN_PERIOD_ENTITY_OBJECT','ATLAS','MODEL_SERVING_MART','MODEL_SERVING','MODEL_SERVING_CAPITAL_SCHEDULES'),
        ('QF-D98','mart_model_planning_inputs','ONE_ROW_PER_SCENARIO_PERIOD_DEPARTMENT_ACCOUNT','PYTHIA','MODEL_SERVING_MART','MODEL_SERVING','MODEL_SERVING_PLANNING_INPUTS'),
        ('QF-D99','mart_model_readiness_controls','ONE_ROW_PER_EXECUTED_READINESS_CONTROL','ATLAS','MODEL_SERVING_MART','MODEL_SERVING','MODEL_SERVING_READINESS_CONTROLS')
    ) t(dataset_id, relation_name, grain, semantic_owner, model_class, consumption_class, reliability_purpose)
)
select * from inherited
union all
select
    'Q-FINANCE', 5, dataset_id, 1, 'gold', relation_name, grain,
    semantic_owner, model_class, consumption_class, reliability_purpose,
    '{{ var("a24_data_ref") }}', '{{ var("a24_package_digest") }}',
    '{{ var("finance_model_ref") }}', 'INTEGER_MINOR_UNITS_PLUS_CURRENCY'
from additions
