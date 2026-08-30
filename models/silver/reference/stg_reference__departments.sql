{{ config(tags=['slice_b3']) }}

select
    trim(department_id) as department_id,
    trim(department_name) as department_name,
    trim(business_unit) as business_unit,
    upper(trim(opex_class)) as opex_class,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'reference__departments') }}
