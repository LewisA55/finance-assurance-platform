{{ config(tags=['slice_b3']) }}

select
    cast(snapshot_date as date) as snapshot_date,
    trim(vendor_invoice_id) as vendor_invoice_id,
    trim(vendor_id) as vendor_id,
    cast(due_date as date) as due_date,
    cast(invoice_amount_minor as bigint) as invoice_amount_minor,
    cast(paid_amount_minor as bigint) as paid_amount_minor,
    cast(open_amount_minor as bigint) as open_amount_minor,
    upper(trim(currency)) as currency,
    cast(reporting_open_amount_minor as bigint) as reporting_open_amount_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    cast(days_past_due as integer) as days_past_due,
    upper(trim(ageing_bucket)) as ageing_bucket,
    upper(trim(ap_status)) as ap_status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'procurement__ap_ageing_snapshot') }}
