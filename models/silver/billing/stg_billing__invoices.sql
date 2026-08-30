{{ config(tags=['slice_b3']) }}

select
    trim(invoice_id) as invoice_id,
    trim(customer_id) as customer_id,
    trim(subscription_id) as subscription_id,
    cast(invoice_date as date) as invoice_date,
    cast(due_date as date) as due_date,
    cast(service_period_start as date) as service_period_start,
    cast(service_period_end as date) as service_period_end,
    cast(invoice_amount_minor as bigint) as invoice_amount_minor,
    cast(tax_amount_minor as bigint) as tax_amount_minor,
    upper(trim(currency)) as currency,
    cast(reporting_amount_minor as bigint) as reporting_amount_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    upper(trim(invoice_status)) as invoice_status,
    trim(external_invoice_number) as external_invoice_number,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'billing__invoices') }}
