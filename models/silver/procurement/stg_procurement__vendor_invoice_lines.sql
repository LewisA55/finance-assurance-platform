{{ config(tags=['slice_b3']) }}

select
    trim(vendor_invoice_line_id) as vendor_invoice_line_id,
    trim(vendor_invoice_id) as vendor_invoice_id,
    trim(vendor_id) as vendor_id,
    cast(line_no as integer) as line_no,
    trim(department_id) as department_id,
    trim(expense_account_id) as expense_account_id,
    cast(service_period_start as date) as service_period_start,
    cast(service_period_end as date) as service_period_end,
    trim(line_description) as line_description,
    cast(line_amount_minor as bigint) as line_amount_minor,
    upper(trim(currency)) as currency,
    cast(reporting_line_amount_minor as bigint) as reporting_line_amount_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'procurement__vendor_invoice_lines') }}
