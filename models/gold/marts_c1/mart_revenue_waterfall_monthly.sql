{{ config(tags=['slice_c']) }}

with rollforward as (
    select
        period_id,
        reporting_currency as currency,
        sum(reporting_opening_deferred_revenue_minor)::bigint as opening_deferred_revenue_minor,
        sum(reporting_new_billings_minor)::bigint as new_billings_minor,
        sum(reporting_recognised_revenue_minor)::bigint as recognised_revenue_minor,
        sum(reporting_closing_deferred_revenue_minor)::bigint as closing_deferred_revenue_minor
    from {{ ref('fct_deferred_revenue_rollforward') }}
    group by 1, 2
), schedule as (
    select recognition_period as period_id, reporting_currency as currency,
           sum(reporting_revenue_amount_minor)::bigint as scheduled_revenue_minor,
           count(distinct schedule_id)::bigint as schedule_line_count
    from {{ ref('fct_revenue_recognition') }} group by 1, 2
)
select
    md5(concat_ws('|', rollforward.period_id, rollforward.currency)) as revenue_waterfall_hk,
    rollforward.*,
    schedule.scheduled_revenue_minor,
    schedule.schedule_line_count,
    (opening_deferred_revenue_minor + new_billings_minor - recognised_revenue_minor
        - closing_deferred_revenue_minor)::bigint as rollforward_difference_minor,
    (recognised_revenue_minor - schedule.scheduled_revenue_minor)::bigint as schedule_difference_minor,
    version.reporting_version_ref,
    'REVENUE_SUBLEDGER' as value_authority,
    'RELIABLE_FOR_REVENUE_ANALYTICS' as reliability_status,
    'EXECUTIVE_REVENUE_WATERFALL' as reliability_purpose,
    'gold.fct_deferred_revenue_rollforward|gold.fct_revenue_recognition' as drill_through_relation,
    version.source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from rollforward
inner join schedule using (period_id, currency)
inner join {{ ref('dim_reporting_version') }} version
  on rollforward.period_id = version.period_id and version.scope_id = 'NEXUS-GROUP'
