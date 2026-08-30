{{ config(tags=['slice_c']) }}

select
    md5(concat_ws('|', working.period_id, working.currency)) as model_working_capital_driver_hk,
    working.period_id,
    period.month_end,
    working.currency,
    financial.revenue_minor,
    lag(financial.revenue_minor) over (partition by working.currency order by working.period_id)::bigint as prior_month_revenue_minor,
    (financial.revenue_minor - lag(financial.revenue_minor) over (
        partition by working.currency order by working.period_id))::bigint as revenue_change_minor,
    working.billings_minor,
    working.collections_minor,
    working.closing_ar_minor,
    working.overdue_ar_minor,
    working.purchases_minor,
    working.supplier_payments_minor,
    working.closing_trade_ap_minor,
    working.closing_capital_ap_minor,
    working.closing_ap_minor,
    working.overdue_ap_minor,
    working.closing_deferred_revenue_minor,
    working.trade_working_capital_minor,
    working.operating_working_capital_minor,
    lag(working.operating_working_capital_minor) over (
        partition by working.currency order by working.period_id)::bigint as prior_operating_working_capital_minor,
    (working.operating_working_capital_minor - lag(working.operating_working_capital_minor) over (
        partition by working.currency order by working.period_id))::bigint as change_in_operating_working_capital_minor,
    working.dso_days,
    working.dpo_days,
    working.reporting_version_ref,
    'STATUTORY_AND_OPERATIONAL_GOVERNED_STATE' as value_authority,
    'RELIABLE_FOR_FINANCIAL_MODELLING' as reliability_status,
    'MODEL_SERVING_WORKING_CAPITAL_DRIVERS' as reliability_purpose,
    'gold.mart_ap_working_capital_monthly|gold.mart_financial_performance_monthly' as drill_through_relation,
    working.source_package_digest,
    working._source_data_ref
from {{ ref('mart_ap_working_capital_monthly') }} working
inner join {{ ref('dim_period') }} period using (period_id)
inner join {{ ref('mart_financial_performance_monthly') }} financial
  on working.period_id = financial.period_id
 and working.currency = financial.currency
 and financial.scope_id = 'NEXUS-GROUP'
