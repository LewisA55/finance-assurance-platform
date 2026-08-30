{{ config(tags=['slice_c']) }}

select metric_id as object_ref from {{ ref('mart_cfo_metric_readiness') }}
where readiness_status <> 'READY'
union all
select period_id from {{ ref('mart_executive_cfo_command_center') }}
where presentation_status <> 'READY' or not_ready_metric_count <> 0
union all
select control_id from {{ ref('mart_model_readiness_controls') }}
where result_status <> 'PASS' or (result_status = 'PASS' and first_failure_ref is not null)
