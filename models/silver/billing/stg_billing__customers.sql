{{ config(tags=['slice_b3']) }}

select
    trim(customer_id) as customer_id,
    trim(customer_name) as customer_name,
    trim(region_id) as region_id,
    upper(trim(segment)) as segment,
    trim(industry) as industry,
    cast(created_date as date) as created_date,
    cast(credit_terms_days as integer) as credit_terms_days,
    upper(trim(status)) as status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'billing__customers') }}
