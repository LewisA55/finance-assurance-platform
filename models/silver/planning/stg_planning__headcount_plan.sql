{{ config(tags=['slice_b4']) }}

select
    trim(position_id) as position_id,
    upper(trim(scenario_code)) as scenario_code,
    trim(department_id) as department_id,
    trim(region_id) as region_id,
    cast(planned_hire_date as date) as planned_hire_date,
    upper(trim(role_family)) as role_family,
    upper(trim(seniority_level)) as seniority_level,
    cast(salary_low_minor as bigint) as salary_low_minor,
    cast(salary_mid_minor as bigint) as salary_mid_minor,
    cast(salary_high_minor as bigint) as salary_high_minor,
    upper(trim(currency)) as currency,
    cast(reporting_salary_mid_minor as bigint) as reporting_salary_mid_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    upper(trim(position_status)) as position_status,
    cast(backfill_flag as boolean) as backfill_flag,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'workforce__headcount_plan') }}
