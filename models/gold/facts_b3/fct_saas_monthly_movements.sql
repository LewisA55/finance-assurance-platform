{{ config(tags=['slice_b3']) }}

with state as (
    select
        period_id, product_id, region_id, customer_segment, currency,
        sum(ending_mrr_minor)::bigint as ending_mrr_minor,
        sum(ending_arr_minor)::bigint as ending_arr_minor,
        count(distinct case when is_active_subscription then subscription_id end)::bigint as active_subscription_count,
        count(distinct case when is_active_subscription then customer_id end)::bigint as active_customer_count
    from {{ ref('fct_subscription_monthly_state') }}
    group by 1, 2, 3, 4, 5
), state_with_opening as (
    select *,
        coalesce(lag(ending_mrr_minor) over (
            partition by product_id, region_id, customer_segment, currency order by period_id
        ), 0)::bigint as beginning_mrr_minor
    from state
), movement as (
    select
        period_id, product_id, region_id, customer_segment,
        reporting_currency as currency,
        sum(case when movement_class = 'NEW' then reporting_mrr_delta_minor else 0 end)::bigint as new_mrr_minor,
        sum(case when movement_class = 'EXPANSION' then reporting_mrr_delta_minor else 0 end)::bigint as expansion_mrr_minor,
        sum(case when movement_class = 'CONTRACTION' then reporting_mrr_delta_minor else 0 end)::bigint as contraction_mrr_minor,
        sum(case when movement_class = 'CHURN' then reporting_mrr_delta_minor else 0 end)::bigint as churn_mrr_minor,
        sum(case when movement_class = 'FX_REMEASUREMENT' then reporting_state_mrr_delta_minor else 0 end)::bigint as fx_remeasurement_mrr_minor,
        count(case when movement_class = 'NEW' then 1 end)::bigint as new_subscription_count,
        count(case when movement_class = 'CHURN' then 1 end)::bigint as churned_subscription_count
    from {{ ref('fct_subscription_lifecycle_events') }}
    group by 1, 2, 3, 4, 5
)
select
    md5(concat_ws('|', state.period_id, state.product_id, state.region_id,
                  state.customer_segment, state.currency)) as saas_monthly_movement_hk,
    state.period_id,
    state.product_id,
    state.region_id,
    state.customer_segment,
    state.currency,
    state.beginning_mrr_minor,
    coalesce(movement.new_mrr_minor, 0)::bigint as new_mrr_minor,
    coalesce(movement.expansion_mrr_minor, 0)::bigint as expansion_mrr_minor,
    coalesce(movement.contraction_mrr_minor, 0)::bigint as contraction_mrr_minor,
    coalesce(movement.churn_mrr_minor, 0)::bigint as churn_mrr_minor,
    (state.ending_mrr_minor - state.beginning_mrr_minor
        - coalesce(movement.new_mrr_minor, 0)
        - coalesce(movement.expansion_mrr_minor, 0)
        - coalesce(movement.contraction_mrr_minor, 0)
        - coalesce(movement.churn_mrr_minor, 0))::bigint as fx_remeasurement_mrr_minor,
    state.ending_mrr_minor,
    state.ending_arr_minor,
    state.active_subscription_count,
    state.active_customer_count,
    coalesce(movement.new_subscription_count, 0)::bigint as new_subscription_count,
    coalesce(movement.churned_subscription_count, 0)::bigint as churned_subscription_count,
    case when state.beginning_mrr_minor = 0 then null else
        round(10000.0 * (state.beginning_mrr_minor
            + coalesce(movement.contraction_mrr_minor, 0)
            + coalesce(movement.churn_mrr_minor, 0)) / state.beginning_mrr_minor)::integer
    end as gross_revenue_retention_bps,
    case when state.beginning_mrr_minor = 0 then null else
        round(10000.0 * (state.beginning_mrr_minor
            + coalesce(movement.expansion_mrr_minor, 0)
            + coalesce(movement.contraction_mrr_minor, 0)
            + coalesce(movement.churn_mrr_minor, 0)) / state.beginning_mrr_minor)::integer
    end as net_revenue_retention_bps,
    'RELIABLE_FOR_SAAS_ANALYTICS' as reliability_status,
    'MONTHLY_SAAS_MOVEMENT' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from state_with_opening state
left join movement using (period_id, product_id, region_id, customer_segment, currency)
