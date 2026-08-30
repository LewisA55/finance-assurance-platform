{{ config(tags=['slice_b3']) }}

select
    trim(compensation_line_id) as compensation_line_id,
    trim(period_id) as period_id,
    trim(employee_id) as employee_id,
    trim(department_id) as department_id,
    trim(region_id) as region_id,
    upper(trim(compensation_component)) as compensation_component,
    cast(amount_minor as bigint) as amount_minor,
    upper(trim(currency)) as currency,
    cast(reporting_amount_minor as bigint) as reporting_amount_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    upper(trim(source_system)) as source_system,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'workforce__employee_compensation') }}
