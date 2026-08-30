{{ config(tags=['slice_b3']) }}

select
    md5(employee.employee_id) as employee_hk,
    employee.* exclude (_ingested_at, _source_file, _source_file_sha256),
    department.department_name,
    department.business_unit,
    department.opex_class,
    region.region_name
from {{ ref('stg_hris__employees') }} employee
left join {{ ref('dim_department') }} department using (department_id)
left join {{ ref('dim_region') }} region using (region_id)
