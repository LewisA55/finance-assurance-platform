{{ config(tags=['slice_b3']) }}

with eligible_periods as (
    select
        subscription.subscription_id,
        subscription.customer_id,
        subscription.product_id,
        subscription.region_id,
        subscription.customer_segment,
        subscription.currency,
        period.period_id,
        period.month_start as period_start_date,
        period.month_end as period_end_date
    from {{ ref('dim_subscription') }} subscription
    cross join {{ ref('dim_period') }} period
    where period.month_end >= subscription.contract_start_date
      and period.month_start <= coalesce(subscription.contract_end_date, period.month_end)
), ranked_state as (
    select
        eligible.*,
        event.subscription_event_id,
        event.event_sequence,
        event.event_date as latest_event_date,
        event.event_type as latest_event_type,
        event.reporting_new_mrr_minor as ending_mrr_minor,
        event.reporting_currency,
        row_number() over (
            partition by eligible.subscription_id, eligible.period_id
            order by event.event_date desc, event.event_sequence desc
        ) as state_rank
    from eligible_periods eligible
    inner join {{ ref('stg_billing__subscription_events') }} event
      on eligible.subscription_id = event.subscription_id
     and event.event_date <= eligible.period_end_date
)
select
    md5(concat_ws('|', subscription_id, period_id)) as subscription_monthly_state_hk,
    subscription_id,
    customer_id,
    product_id,
    region_id,
    customer_segment,
    period_id,
    period_end_date,
    subscription_event_id as latest_subscription_event_id,
    latest_event_date,
    latest_event_type,
    ending_mrr_minor::bigint as ending_mrr_minor,
    (ending_mrr_minor * 12)::bigint as ending_arr_minor,
    ending_mrr_minor > 0 as is_active_subscription,
    reporting_currency as currency,
    'RELIABLE_FOR_SAAS_ANALYTICS' as reliability_status,
    'MONTH_END_SUBSCRIPTION_STATE' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from ranked_state
where state_rank = 1
