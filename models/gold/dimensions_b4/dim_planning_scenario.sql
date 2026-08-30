{{ config(tags=['slice_b4']) }}

select
    md5(forecast.forecast_version_ref || '|' || forecast.scenario_code) as planning_scenario_hk,
    forecast.forecast_version_ref || '|' || forecast.scenario_code as planning_scenario_ref,
    forecast.forecast_version_ref,
    forecast.scenario_code,
    forecast.cutover_period,
    forecast.forecast_start_period,
    forecast.forecast_end_period,
    forecast.source_budget_version_ref,
    budget.budget_name as source_budget_name,
    forecast.approval_status,
    forecast.locked_flag,
    case
        when forecast.approval_status = 'APPROVED' and forecast.locked_flag
            then 'APPROVED_AND_LOCKED_PLANNING_INPUT'
        when forecast.approval_status = 'APPROVED'
            then 'APPROVED_UNLOCKED_PLANNING_INPUT'
        else 'DRAFT_PLANNING_INPUT'
    end as planning_input_status,
    'PLANNING_INPUTS' as reliability_purpose,
    actuals.reporting_version_ref as actuals_reporting_version_ref,
    actuals.scope_id as actuals_scope_id,
    actuals.close_status as actuals_close_status,
    actuals.reliability_status as actuals_reliability_status,
    actuals.reliability_purpose as actuals_reliability_purpose,
    actuals.source_package_digest as actuals_source_package_digest,
    false as is_governed_pythia_snapshot,
    forecast._source_row_hash,
    forecast._source_data_ref
from {{ ref('stg_planning__forecast_versions') }} forecast
inner join {{ ref('dim_budget_version') }} budget
  on forecast.source_budget_version_ref = budget.budget_version_ref
inner join {{ ref('dim_reporting_version') }} actuals
  on actuals.period_id = forecast.cutover_period
 and actuals.scope_id = 'NEXUS-GROUP'
