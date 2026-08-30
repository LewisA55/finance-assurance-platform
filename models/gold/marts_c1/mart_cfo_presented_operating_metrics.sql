{{ config(tags=['slice_c']) }}

with financial as (
    select period_id, reporting_version_ref, currency,
           revenue_minor, ebitda_minor, net_income_minor, reliability_status, source_package_digest
    from {{ ref('mart_financial_performance_monthly') }} where scope_id = 'NEXUS-GROUP'
), cash as (
    select period_id, reporting_version_ref, currency, closing_cash_minor, reliability_status, source_package_digest
    from {{ ref('mart_cash_flow_liquidity_monthly') }} where scope_id = 'NEXUS-GROUP'
), o2c as (
    select period_id, max(reporting_version_ref) as reporting_version_ref, currency,
           sum(collections_minor)::bigint as collections_minor,
           sum(overdue_ar_minor)::bigint as overdue_ar_minor,
           max(source_package_digest) as source_package_digest
    from {{ ref('mart_o2c_customer_collections_monthly') }} group by 1, 3
), saas as (
    select period_id, max(reporting_version_ref) as reporting_version_ref, currency,
           sum(beginning_mrr_minor)::bigint as beginning_mrr_minor,
           sum(expansion_mrr_minor)::bigint as expansion_mrr_minor,
           sum(contraction_mrr_minor)::bigint as contraction_mrr_minor,
           sum(churn_mrr_minor)::bigint as churn_mrr_minor,
           sum(ending_arr_minor)::bigint as ending_arr_minor,
           max(source_package_digest) as source_package_digest
    from {{ ref('mart_saas_performance_monthly') }} group by 1, 3
), workforce as (
    select period_id, max(reporting_version_ref) as reporting_version_ref, currency,
           sum(active_headcount_count)::bigint as active_headcount_count,
           max(source_package_digest) as source_package_digest
    from {{ ref('mart_workforce_cost_monthly') }} group by 1, 3
), capex as (
    select period_id, max(reporting_version_ref) as reporting_version_ref, currency,
           sum(capex_additions_minor)::bigint as capex_additions_minor,
           max(source_package_digest) as source_package_digest
    from {{ ref('mart_fixed_asset_capex_monthly') }} group by 1, 3
), capital as (
    select period_id, reporting_version_ref, currency, net_debt_minor, source_package_digest
    from {{ ref('mart_capital_structure_monthly') }} where scope_id = 'NEXUS-GROUP'
), metric as (
    select period_id, reporting_version_ref, currency, 'REVENUE' as metric_id, 'Revenue' as metric_label,
           revenue_minor::bigint as metric_value_minor, null::bigint as metric_value_count,
           null::integer as metric_value_bps, 'MINOR_UNITS' as value_unit,
           'STATUTORY_STATEMENT' as value_authority, source_package_digest from financial
    union all select period_id, reporting_version_ref, currency, 'EBITDA', 'EBITDA',
           ebitda_minor, null::bigint, null::integer, 'MINOR_UNITS', 'STATUTORY_STATEMENT', source_package_digest from financial
    union all select period_id, reporting_version_ref, currency, 'NET_INCOME', 'Net income',
           net_income_minor, null::bigint, null::integer, 'MINOR_UNITS', 'STATUTORY_STATEMENT', source_package_digest from financial
    union all select period_id, reporting_version_ref, currency, 'CLOSING_CASH', 'Closing cash',
           closing_cash_minor, null::bigint, null::integer, 'MINOR_UNITS', 'STATUTORY_CASH_FLOW', source_package_digest from cash
    union all select period_id, reporting_version_ref, currency, 'COLLECTIONS', 'Customer collections',
           collections_minor, null::bigint, null::integer, 'MINOR_UNITS', 'OPERATIONAL_EVENT', source_package_digest from o2c
    union all select period_id, reporting_version_ref, currency, 'OVERDUE_AR', 'Overdue accounts receivable',
           overdue_ar_minor, null::bigint, null::integer, 'MINOR_UNITS', 'OPERATIONAL_STATE', source_package_digest from o2c
    union all select period_id, reporting_version_ref, currency, 'ENDING_ARR', 'Ending ARR',
           ending_arr_minor, null::bigint, null::integer, 'MINOR_UNITS', 'SUBSCRIPTION_STATE', source_package_digest from saas
    union all select period_id, reporting_version_ref, currency, 'NET_REVENUE_RETENTION', 'Net revenue retention',
           null::bigint, null::bigint,
           case when beginning_mrr_minor = 0 then null else round(10000.0 *
               (beginning_mrr_minor + expansion_mrr_minor + contraction_mrr_minor + churn_mrr_minor)
               / beginning_mrr_minor)::integer end,
           'BASIS_POINTS', 'SUBSCRIPTION_STATE', source_package_digest from saas
    union all select period_id, reporting_version_ref, currency, 'ACTIVE_HEADCOUNT', 'Active headcount',
           null::bigint, active_headcount_count, null::integer, 'COUNT', 'WORKFORCE_STATE', source_package_digest from workforce
    union all select period_id, reporting_version_ref, currency, 'CAPEX_ADDITIONS', 'Capital additions',
           capex_additions_minor, null::bigint, null::integer, 'MINOR_UNITS', 'FIXED_ASSET_SUBLEDGER', source_package_digest from capex
    union all select period_id, reporting_version_ref, currency, 'NET_DEBT', 'Net debt',
           net_debt_minor, null::bigint, null::integer, 'MINOR_UNITS', 'TREASURY_AND_LEASE_SUBLEDGER', source_package_digest from capital
)
select
    md5(concat_ws('|', period_id, metric_id)) as cfo_presented_operating_metric_hk,
    period_id,
    'NEXUS-GROUP' as scope_id,
    reporting_version_ref,
    metric_id,
    metric_label,
    metric_value_minor,
    metric_value_count,
    metric_value_bps,
    currency,
    value_unit,
    value_authority,
    'RELIABLE_FOR_EXECUTIVE_PRESENTATION' as reliability_status,
    'CFO_PRESENTED_OPERATING_METRICS' as reliability_purpose,
    case metric_id
        when 'REVENUE' then 'gold.mart_financial_performance_monthly'
        when 'EBITDA' then 'gold.mart_financial_performance_monthly'
        when 'NET_INCOME' then 'gold.mart_financial_performance_monthly'
        when 'CLOSING_CASH' then 'gold.mart_cash_flow_liquidity_monthly'
        when 'COLLECTIONS' then 'gold.mart_o2c_customer_collections_monthly'
        when 'OVERDUE_AR' then 'gold.mart_o2c_customer_collections_monthly'
        when 'ENDING_ARR' then 'gold.mart_saas_performance_monthly'
        when 'NET_REVENUE_RETENTION' then 'gold.mart_saas_performance_monthly'
        when 'ACTIVE_HEADCOUNT' then 'gold.mart_workforce_cost_monthly'
        when 'CAPEX_ADDITIONS' then 'gold.mart_fixed_asset_capex_monthly'
        else 'gold.mart_capital_structure_monthly'
    end as drill_through_relation,
    source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from metric
