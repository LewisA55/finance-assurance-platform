{{ config(tags=['slice_b3']) }}

select
    trim(invoice_line_id) as invoice_line_id,
    trim(invoice_id) as invoice_id,
    cast(line_no as integer) as line_no,
    trim(product_id) as product_id,
    upper(trim(line_type)) as line_type,
    cast(quantity as integer) as quantity,
    cast(unit_price_minor as bigint) as unit_price_minor,
    cast(line_amount_minor as bigint) as line_amount_minor,
    upper(trim(currency)) as currency,
    cast(reporting_line_amount_minor as bigint) as reporting_line_amount_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'billing__invoice_lines') }}
