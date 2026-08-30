{{ config(tags=['slice_c']) }}

select
    md5(concat_ws('|', forecast.planning_scenario_ref, forecast.period_id,
                  forecast.department_id, forecast.account_id)) as model_planning_input_hk,
    forecast.planning_scenario_ref,
    forecast.forecast_version_ref,
    forecast.scenario_code,
    scenario.cutover_period,
    scenario.forecast_start_period,
    scenario.forecast_end_period,
    scenario.source_budget_version_ref as budget_version_ref,
    scenario.approval_status as scenario_approval_status,
    scenario.locked_flag as scenario_locked_flag,
    scenario.planning_input_status,
    scenario.is_governed_pythia_snapshot,
    forecast.period_id,
    forecast.department_id,
    department.department_name,
    department.business_unit,
    department.opex_class,
    forecast.account_id,
    account.account_name,
    account.statement_class,
    account.statement_line,
    forecast.reporting_currency as currency,
    budget.reporting_amount_minor::bigint as budget_amount_minor,
    forecast.reporting_amount_minor::bigint as forecast_amount_minor,
    forecast.assumption_basis_ref,
    forecast.approval_status as forecast_line_approval_status,
    forecast.actuals_reporting_version_ref,
    forecast.actuals_scope_id,
    forecast.actuals_close_status,
    forecast.actuals_reliability_status,
    'PLANNING_SOURCE_INPUT' as value_authority,
    case when scenario.planning_input_status = 'APPROVED_AND_LOCKED_PLANNING_INPUT'
         then 'RELIABLE_FOR_APPROVED_PLANNING_INPUT'
         else 'PROPOSED_PLANNING_INPUT' end as reliability_status,
    'MODEL_SERVING_PLANNING_INPUTS' as reliability_purpose,
    'gold.fct_forecast_plan_lines|gold.fct_budget_plan_lines|gold.dim_planning_scenario' as drill_through_relation,
    scenario.actuals_source_package_digest as source_package_digest,
    forecast._source_data_ref
from {{ ref('fct_forecast_plan_lines') }} forecast
inner join {{ ref('dim_planning_scenario') }} scenario using (planning_scenario_ref)
inner join {{ ref('dim_department') }} department using (department_id)
inner join {{ ref('dim_gl_account') }} account using (account_id)
left join {{ ref('fct_budget_plan_lines') }} budget
  on budget.budget_version_ref = scenario.source_budget_version_ref
 and budget.period_id = forecast.period_id
 and budget.department_id = forecast.department_id
 and budget.account_id = forecast.account_id
