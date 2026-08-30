{{ config(tags=['slice_b3']) }}

select
    md5(event.subscription_event_id) as subscription_lifecycle_event_hk,
    event.* exclude (_ingested_at, _source_file, _source_file_sha256),
    subscription.product_id,
    subscription.region_id,
    subscription.customer_segment,
    case
        when event.event_type = 'START' then 'NEW'
        when event.event_type = 'CHURN' then 'CHURN'
        when event.mrr_delta_minor > 0 then 'EXPANSION'
        when event.mrr_delta_minor < 0 then 'CONTRACTION'
        when event.reporting_new_mrr_minor <> event.reporting_previous_mrr_minor
            then 'FX_REMEASUREMENT'
        else 'RENEWAL_FLAT'
    end as movement_class,
    (event.reporting_new_mrr_minor - event.reporting_previous_mrr_minor)::bigint
        as reporting_state_mrr_delta_minor,
    strftime(event.event_date, '%Y-%m') as period_id
from {{ ref('stg_billing__subscription_events') }} event
inner join {{ ref('dim_subscription') }} subscription using (subscription_id, customer_id)
