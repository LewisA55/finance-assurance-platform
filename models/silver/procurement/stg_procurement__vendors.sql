{{ config(tags=['slice_b3']) }}

select
    trim(vendor_id) as vendor_id,
    trim(vendor_name) as vendor_name,
    trim(category) as category,
    trim(region_id) as region_id,
    cast(payment_terms_days as integer) as payment_terms_days,
    upper(trim(status)) as status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'procurement__vendors') }}
