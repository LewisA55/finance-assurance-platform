{{ config(tags=['slice_b3']) }}

select
    trim(product_id) as product_id,
    trim(product_name) as product_name,
    trim(product_family) as product_family,
    upper(trim(revenue_type)) as revenue_type,
    cast(gross_margin_target_bps as integer) as gross_margin_target_bps,
    cast(active_from as date) as active_from,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'reference__products') }}
