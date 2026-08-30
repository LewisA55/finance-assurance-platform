{{ config(tags=['slice_c']) }}

select
    md5(variance.variance_line_id) as planning_performance_hk,
    variance.period_id,
    variance.period_status,
    variance.department_id,
    department.department_name,
    department.business_unit,
    department.opex_class,
    variance.account_id,
    account.account_name,
    account.statement_class,
    account.statement_line,
    variance.currency,
    variance.actual_amount_minor,
    variance.budget_amount_minor,
    variance.forecast_amount_minor,
    variance.actual_vs_budget_variance_minor,
    variance.actual_vs_forecast_variance_minor,
    variance.forecast_vs_budget_variance_minor,
    variance.budget_version_ref,
    variance.forecast_version_ref,
    variance.scenario_code,
    variance.planning_scenario_ref,
    variance.source_budget_line_ref,
    variance.source_forecast_line_ref,
    variance.is_statutory_actual,
    variance.value_authority,
    variance.reliability_status,
    'EXECUTIVE_MANAGEMENT_VARIANCE' as reliability_purpose,
    'gold.fct_planning_variance_source' as drill_through_relation,
    '{{ var("a24_package_digest") }}' as source_package_digest,
    variance._source_data_ref
from {{ ref('fct_planning_variance_source') }} variance
inner join {{ ref('dim_department') }} department using (department_id)
inner join {{ ref('dim_gl_account') }} account using (account_id)
