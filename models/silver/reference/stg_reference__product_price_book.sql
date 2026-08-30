{{ config(tags=['slice_b3']) }}

select
    trim(price_book_id) as price_book_id,
    trim(product_id) as product_id,
    upper(trim(customer_segment)) as customer_segment,
    trim(region_id) as region_id,
    upper(trim(currency)) as currency,
    cast(monthly_list_price_minor as bigint) as monthly_list_price_minor,
    cast(annual_list_price_minor as bigint) as annual_list_price_minor,
    cast(reporting_monthly_list_price_minor as bigint) as reporting_monthly_list_price_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    cast(effective_start_date as date) as effective_start_date,
    cast(nullif(trim(effective_end_date), '') as date) as effective_end_date,
    upper(trim(status)) as status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'reference__product_price_book') }}
