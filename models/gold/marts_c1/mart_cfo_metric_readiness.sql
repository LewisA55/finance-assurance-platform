{{ config(tags=['slice_c']) }}

with coverage as (
    select
        metric_id,
        max(metric_label) as metric_label,
        min(period_id) as first_period,
        max(period_id) as last_period,
        count(distinct period_id)::bigint as period_count,
        count(case when metric_value_minor is null and metric_value_count is null and metric_value_bps is null then 1 end)::bigint as null_value_count,
        max(value_authority) as value_authority,
        max(drill_through_relation) as drill_through_relation,
        max(source_package_digest) as source_package_digest
    from {{ ref('mart_cfo_presented_operating_metrics') }}
    group by 1
)
select
    md5(metric_id) as cfo_metric_readiness_hk,
    metric_id,
    metric_label,
    first_period,
    last_period,
    period_count,
    60::bigint as minimum_period_count,
    null_value_count,
    case when metric_id = 'NET_REVENUE_RETENTION' then 1 else 0 end::bigint as acceptable_null_value_count,
    case when period_count >= 60
               and null_value_count <= case when metric_id = 'NET_REVENUE_RETENTION' then 1 else 0 end
         then 'READY' else 'NOT_READY' end as readiness_status,
    case when period_count < 60 then 'INSUFFICIENT_HISTORY'
         when null_value_count > case when metric_id = 'NET_REVENUE_RETENTION' then 1 else 0 end
              then 'UNEXPECTED_NULL_METRIC_VALUES'
         else null end as first_failure_reason,
    value_authority,
    'VALIDATOR_PRODUCED' as readiness_authority,
    'RELIABLE_FOR_EXECUTIVE_PRESENTATION' as reliability_status,
    'CFO_METRIC_READINESS' as reliability_purpose,
    drill_through_relation,
    source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from coverage
