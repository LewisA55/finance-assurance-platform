{{ config(tags=['slice_b3']) }}

select
    trim(snapshot_period) as snapshot_period,
    trim(employee_id) as employee_id,
    trim(department_id) as department_id,
    trim(region_id) as region_id,
    upper(trim(employment_status)) as employment_status,
    cast(fte_bps as integer) as fte_bps,
    cast(annual_salary_minor as bigint) as annual_salary_minor,
    upper(trim(currency)) as currency,
    cast(reporting_annual_salary_minor as bigint) as reporting_annual_salary_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    cast(is_ghost_headcount as boolean) as is_ghost_headcount,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'hris__headcount_snapshot') }}
