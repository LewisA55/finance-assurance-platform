{{ config(tags=['slice_b3']) }}

select
    md5(concat_ws('|', headcount.snapshot_period, headcount.employee_id)) as headcount_monthly_snapshot_hk,
    headcount.* exclude (_ingested_at, _source_file, _source_file_sha256),
    employee.hire_date,
    employee.termination_date,
    department.business_unit,
    department.opex_class,
    region.region_name,
    'RELIABLE_FOR_WORKFORCE_ANALYTICS' as reliability_status,
    'WORKFORCE_ACTUALS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest
from {{ ref('stg_hris__headcount_snapshot') }} headcount
inner join {{ ref('dim_employee') }} employee using (employee_id)
inner join {{ ref('dim_department') }} department
  on headcount.department_id = department.department_id
inner join {{ ref('dim_region') }} region
  on headcount.region_id = region.region_id
