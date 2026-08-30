{{ config(tags=['slice_b3']) }}

with reporting_value as (
    select
        vendor_invoice_id,
        sum(cast(reporting_line_amount_minor as bigint))::bigint
            as reporting_amount_minor,
        max(upper(trim(reporting_currency))) as reporting_currency
    from {{ source('a24_bronze', 'procurement__vendor_invoice_lines') }}
    group by vendor_invoice_id
)
select
    trim(vendor_payment_id) as vendor_payment_id,
    trim(vendor_invoice_id) as vendor_invoice_id,
    trim(vendor_id) as vendor_id,
    cast(payment_date as date) as payment_date,
    cast(payment_amount_minor as bigint) as payment_amount_minor,
    upper(trim(currency)) as currency,
    reporting_value.reporting_amount_minor,
    reporting_value.reporting_currency,
    upper(trim(payment_status)) as payment_status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'procurement__vendor_payments') }} as payment
inner join reporting_value using (vendor_invoice_id)
