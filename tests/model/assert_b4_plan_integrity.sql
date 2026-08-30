{{ config(tags=['slice_b4']) }}

with failures as (
    select budget_line_id as object_ref
    from {{ ref('fct_budget_plan_lines') }} line
    inner join {{ ref('dim_budget_version') }} version using (budget_version_ref)
    where line.period_id < version.planning_start_period
       or line.period_id > version.planning_end_period
       or line.approval_status <> version.approval_status
       or line.reporting_currency <> 'GBP'
    union all
    select forecast_line_id
    from {{ ref('fct_forecast_plan_lines') }} line
    inner join {{ ref('dim_planning_scenario') }} scenario using (planning_scenario_ref)
    where line.period_id < scenario.forecast_start_period
       or line.period_id > scenario.forecast_end_period
       or line.approval_status <> scenario.approval_status
       or line.reporting_currency <> 'GBP'
       or line.actuals_reporting_version_ref <> scenario.actuals_reporting_version_ref
)
select * from failures
