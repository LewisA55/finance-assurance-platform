{{ config(tags=['slice_b3']) }}

select
    trim(allocation_id) as allocation_id,
    trim(payment_id) as payment_id,
    trim(invoice_id) as invoice_id,
    cast(allocated_amount_minor as bigint) as allocated_amount_minor,
    upper(trim(currency)) as currency,
    cast(reporting_allocated_amount_minor as bigint) as reporting_allocated_amount_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    cast(allocation_date as date) as allocation_date,
    upper(trim(allocation_status)) as allocation_status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'billing__payment_allocations') }}
