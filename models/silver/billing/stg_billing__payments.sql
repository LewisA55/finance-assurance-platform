{{ config(tags=['slice_b3']) }}

select
    trim(payment_id) as payment_id,
    trim(customer_id) as customer_id,
    cast(payment_date as date) as payment_date,
    cast(payment_amount_minor as bigint) as payment_amount_minor,
    upper(trim(currency)) as currency,
    cast(reporting_amount_minor as bigint) as reporting_amount_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    upper(trim(payment_method)) as payment_method,
    upper(trim(payment_status)) as payment_status,
    trim(source_bank_reference) as source_bank_reference,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'billing__payments') }}
