{{ config(tags=['slice_c']) }}

with o2c as (
    select period_id, sum(billings_minor)::bigint as billings_minor,
           sum(collections_minor)::bigint as collections_minor,
           sum(closing_ar_minor)::bigint as closing_ar_minor,
           sum(overdue_ar_minor)::bigint as overdue_ar_minor
    from {{ ref('mart_o2c_customer_collections_monthly') }} group by 1
), saas as (
    select period_id, sum(beginning_mrr_minor)::bigint as beginning_mrr_minor,
           sum(expansion_mrr_minor)::bigint as expansion_mrr_minor,
           sum(contraction_mrr_minor)::bigint as contraction_mrr_minor,
           sum(churn_mrr_minor)::bigint as churn_mrr_minor,
           sum(ending_arr_minor)::bigint as ending_arr_minor,
           sum(active_customer_count)::bigint as active_customer_count
    from {{ ref('mart_saas_performance_monthly') }} group by 1
), workforce as (
    select period_id, sum(payroll_cost_minor)::bigint as payroll_cost_minor,
           sum(active_headcount_count)::bigint as active_headcount_count
    from {{ ref('mart_workforce_cost_monthly') }} group by 1
), capex as (
    select period_id, sum(capex_additions_minor)::bigint as capex_additions_minor,
           sum(closing_net_book_value_minor)::bigint as closing_net_book_value_minor
    from {{ ref('mart_fixed_asset_capex_monthly') }} group by 1
), readiness as (
    select count(case when readiness_status <> 'READY' then 1 end)::bigint as not_ready_metric_count
    from {{ ref('mart_cfo_metric_readiness') }}
)
select
    md5(concat_ws('|', financial.period_id, 'NEXUS-GROUP')) as executive_cfo_command_center_hk,
    financial.period_id,
    period.month_end,
    period.fiscal_year,
    period.fiscal_quarter,
    'NEXUS-GROUP' as scope_id,
    financial.reporting_version_ref,
    financial.currency,
    financial.revenue_minor,
    financial.gross_profit_minor,
    financial.ebitda_minor,
    financial.net_income_minor,
    financial.gross_margin_bps,
    financial.ebitda_margin_bps,
    balance.total_assets_minor,
    balance.total_liabilities_minor,
    balance.total_equity_minor,
    cash.operating_cash_flow_minor,
    cash.investing_cash_flow_minor,
    cash.financing_cash_flow_minor,
    cash.closing_cash_minor,
    capital.gross_debt_minor,
    capital.net_debt_minor,
    capital.available_liquidity_minor,
    o2c.billings_minor,
    o2c.collections_minor,
    o2c.closing_ar_minor,
    o2c.overdue_ar_minor,
    working.closing_ap_minor,
    working.closing_deferred_revenue_minor,
    working.operating_working_capital_minor,
    working.dso_days,
    working.dpo_days,
    saas.ending_arr_minor,
    saas.active_customer_count,
    case when saas.beginning_mrr_minor = 0 then null else round(10000.0 *
        (saas.beginning_mrr_minor + saas.expansion_mrr_minor
         + saas.contraction_mrr_minor + saas.churn_mrr_minor)
        / saas.beginning_mrr_minor)::integer end as net_revenue_retention_bps,
    workforce.payroll_cost_minor,
    workforce.active_headcount_count,
    capex.capex_additions_minor,
    capex.closing_net_book_value_minor,
    readiness.not_ready_metric_count,
    case when readiness.not_ready_metric_count = 0 then 'READY' else 'USABLE_WITH_REVIEW' end as presentation_status,
    'MIXED_GOVERNED_AUTHORITIES_BY_METRIC' as value_authority,
    'RELIABLE_FOR_EXECUTIVE_PRESENTATION' as reliability_status,
    'CFO_COMMAND_CENTER' as reliability_purpose,
    'gold.mart_cfo_presented_financials|gold.mart_cfo_presented_operating_metrics' as drill_through_relation,
    financial.source_package_digest,
    financial._source_data_ref
from {{ ref('mart_financial_performance_monthly') }} financial
inner join {{ ref('dim_period') }} period using (period_id)
inner join {{ ref('mart_balance_sheet_monthly') }} balance using (period_id, scope_id, reporting_version_ref, currency)
inner join {{ ref('mart_cash_flow_liquidity_monthly') }} cash using (period_id, scope_id, reporting_version_ref, currency)
inner join {{ ref('mart_capital_structure_monthly') }} capital using (period_id, scope_id, reporting_version_ref, currency)
inner join {{ ref('mart_ap_working_capital_monthly') }} working using (period_id, currency)
inner join o2c using (period_id)
inner join saas using (period_id)
inner join workforce using (period_id)
inner join capex using (period_id)
cross join readiness
where financial.scope_id = 'NEXUS-GROUP'
