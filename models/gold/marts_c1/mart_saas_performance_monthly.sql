{{ config(tags=['slice_c']) }}

select
    md5(concat_ws('|', saas.period_id, saas.product_id, saas.region_id,
                  saas.customer_segment, saas.currency)) as saas_performance_hk,
    saas.period_id,
    saas.product_id,
    product.product_name,
    product.product_family,
    saas.region_id,
    region.region_name,
    saas.customer_segment,
    saas.currency,
    saas.beginning_mrr_minor,
    saas.new_mrr_minor,
    saas.expansion_mrr_minor,
    saas.contraction_mrr_minor,
    saas.churn_mrr_minor,
    saas.fx_remeasurement_mrr_minor,
    saas.ending_mrr_minor,
    saas.ending_arr_minor,
    saas.active_subscription_count,
    saas.active_customer_count,
    saas.new_subscription_count,
    saas.churned_subscription_count,
    saas.gross_revenue_retention_bps,
    saas.net_revenue_retention_bps,
    version.reporting_version_ref,
    'SUBSCRIPTION_EVENT_AND_STATE' as value_authority,
    saas.reliability_status,
    'EXECUTIVE_SAAS_PERFORMANCE' as reliability_purpose,
    'gold.fct_saas_monthly_movements' as drill_through_relation,
    saas.source_package_digest,
    saas._source_data_ref
from {{ ref('fct_saas_monthly_movements') }} saas
inner join {{ ref('dim_product') }} product using (product_id)
inner join {{ ref('dim_region') }} region using (region_id)
inner join {{ ref('dim_reporting_version') }} version
  on saas.period_id = version.period_id and version.scope_id = 'NEXUS-GROUP'
