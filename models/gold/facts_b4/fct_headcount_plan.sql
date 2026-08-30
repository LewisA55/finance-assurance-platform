{{ config(tags=['slice_b4']) }}

select
    md5(plan.position_id) as headcount_plan_hk,
    plan.* exclude (_ingested_at, _source_file, _source_file_sha256),
    scenario.planning_scenario_hk,
    scenario.planning_scenario_ref,
    scenario.forecast_version_ref,
    scenario.actuals_reporting_version_ref,
    scenario.actuals_scope_id,
    case
        when scenario.planning_input_status = 'APPROVED_AND_LOCKED_PLANNING_INPUT'
             and plan.position_status = 'APPROVED'
            then 'APPROVED_AND_LOCKED_PLANNING_INPUT'
        else 'PROPOSED_PLANNING_INPUT'
    end as planning_input_status,
    'WORKFORCE_PLANNING_INPUTS' as reliability_purpose
from {{ ref('stg_planning__headcount_plan') }} plan
inner join {{ ref('dim_planning_scenario') }} scenario using (scenario_code)
inner join {{ ref('dim_department') }} department using (department_id)
inner join {{ ref('dim_region') }} region using (region_id)
