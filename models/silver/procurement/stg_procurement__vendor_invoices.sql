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
    trim(vendor_invoice_id) as vendor_invoice_id,
    trim(vendor_id) as vendor_id,
    trim(department_id) as department_id,
    cast(invoice_date as date) as invoice_date,
    cast(due_date as date) as due_date,
    trim(expense_account_id) as expense_account_id,
    cast(invoice_amount_minor as bigint) as invoice_amount_minor,
    cast(tax_amount_minor as bigint) as tax_amount_minor,
    upper(trim(currency)) as currency,
    reporting_value.reporting_amount_minor,
    reporting_value.reporting_currency,
    upper(trim(invoice_status)) as invoice_status,
    trim(external_invoice_number) as external_invoice_number,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'procurement__vendor_invoices') }} as invoice
inner join reporting_value using (vendor_invoice_id)
