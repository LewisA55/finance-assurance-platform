{{ config(tags=['slice_b3']) }}

select
    trim(employee_id) as employee_id,
    trim(department_id) as department_id,
    trim(region_id) as region_id,
    cast(hire_date as date) as hire_date,
    cast(nullif(trim(termination_date), '') as date) as termination_date,
    cast(annual_salary_minor as bigint) as annual_salary_minor,
    upper(trim(salary_currency)) as salary_currency,
    upper(trim(employment_status)) as employment_status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'hris__employees') }}
