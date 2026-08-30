{{ config(tags=['slice_b4']) }}

select
    md5(variance.variance_line_id) as planning_variance_source_hk,
    variance.* exclude (_ingested_at, _source_file, _source_file_sha256),
    budget.budget_version_ref,
    forecast.forecast_version_ref,
    forecast.scenario_code,
    forecast.planning_scenario_ref,
    false as is_statutory_actual,
    'MANAGEMENT_SOURCE_REPORT' as value_authority,
    'SOURCE_SYSTEM_REPORT_FOR_MANAGEMENT_VARIANCE' as reliability_status,
    'MANAGEMENT_VARIANCE_ANALYTICS' as reliability_purpose
from {{ ref('stg_planning__variance_source_extract') }} variance
inner join {{ ref('dim_period') }} period using (period_id)
inner join {{ ref('dim_department') }} department using (department_id)
inner join {{ ref('dim_gl_account') }} account using (account_id)
left join {{ ref('fct_budget_plan_lines') }} budget
  on variance.source_budget_line_ref = budget.budget_line_id
left join {{ ref('fct_forecast_plan_lines') }} forecast
  on variance.source_forecast_line_ref = forecast.forecast_line_id
