{{ config(tags=['slice_c']) }}

with payroll as (
    select period_id, department_id, region_id, reporting_currency as currency,
           sum(reporting_payroll_cost_minor)::bigint as payroll_cost_minor,
           count(distinct employee_id)::bigint as paid_employee_count
    from {{ ref('fct_payroll_expense_lines') }} group by 1, 2, 3, 4
), headcount as (
    select snapshot_period as period_id, department_id, region_id,
           reporting_currency as currency,
           count(distinct employee_id)::bigint as active_headcount_count,
           sum(fte_bps)::bigint as total_fte_bps,
           sum(reporting_annual_salary_minor)::bigint as annual_salary_run_rate_minor,
           count(case when is_ghost_headcount then 1 end)::bigint as ghost_headcount_count
    from {{ ref('fct_headcount_monthly_snapshot') }} group by 1, 2, 3, 4
)
select
    md5(concat_ws('|', headcount.period_id, headcount.department_id, headcount.region_id, headcount.currency)) as workforce_cost_hk,
    headcount.period_id,
    headcount.department_id,
    department.department_name,
    department.business_unit,
    department.opex_class,
    headcount.region_id,
    region.region_name,
    headcount.currency,
    payroll.payroll_cost_minor,
    payroll.paid_employee_count,
    headcount.active_headcount_count,
    headcount.total_fte_bps,
    headcount.annual_salary_run_rate_minor,
    headcount.ghost_headcount_count,
    case when headcount.active_headcount_count = 0 then null else
        (payroll.payroll_cost_minor / headcount.active_headcount_count)::bigint
    end as average_monthly_payroll_cost_minor,
    version.reporting_version_ref,
    'WORKFORCE_EVENT_AND_STATE' as value_authority,
    'RELIABLE_FOR_WORKFORCE_ANALYTICS' as reliability_status,
    'EXECUTIVE_WORKFORCE_COST' as reliability_purpose,
    'gold.fct_payroll_expense_lines|gold.fct_headcount_monthly_snapshot' as drill_through_relation,
    version.source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from headcount
inner join payroll using (period_id, department_id, region_id, currency)
inner join {{ ref('dim_department') }} department using (department_id)
inner join {{ ref('dim_region') }} region using (region_id)
inner join {{ ref('dim_reporting_version') }} version
  on headcount.period_id = version.period_id and version.scope_id = 'NEXUS-GROUP'
