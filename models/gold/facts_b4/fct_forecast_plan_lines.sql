{{ config(tags=['slice_b4']) }}

select
    md5(line.forecast_line_id) as forecast_plan_line_hk,
    line.* exclude (_ingested_at, _source_file, _source_file_sha256),
    scenario.planning_scenario_hk,
    scenario.planning_scenario_ref,
    scenario.cutover_period,
    scenario.actuals_reporting_version_ref,
    scenario.actuals_scope_id,
    scenario.actuals_close_status,
    scenario.actuals_reliability_status,
    scenario.planning_input_status,
    scenario.reliability_purpose
from {{ ref('stg_planning__forecast_lines') }} line
inner join {{ ref('dim_planning_scenario') }} scenario
  using (forecast_version_ref, scenario_code)
inner join {{ ref('dim_period') }} period using (period_id)
inner join {{ ref('dim_department') }} department using (department_id)
inner join {{ ref('dim_gl_account') }} account using (account_id)
