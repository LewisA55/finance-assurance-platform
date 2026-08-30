{{ config(tags=['slice_b3']) }}

select
    trim(capital_invoice_id) as capital_invoice_id,
    trim(capital_purchase_order_id) as capital_purchase_order_id,
    trim(capital_goods_receipt_id) as capital_goods_receipt_id,
    trim(legal_entity_id) as legal_entity_id,
    trim(vendor_id) as vendor_id,
    trim(supplier_invoice_number) as supplier_invoice_number,
    cast(invoice_date as date) as invoice_date,
    cast(due_date as date) as due_date,
    cast(invoice_amount_minor as bigint) as invoice_amount_minor,
    upper(trim(currency)) as currency,
    upper(trim(invoice_status)) as invoice_status,
    trim(payment_ref) as payment_ref,
    cast(nullif(trim(payment_date), '') as date) as payment_date,
    upper(trim(payment_status)) as payment_status,
    cast(source_recorded_at as timestamptz) as source_recorded_at,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'procurement__capital_invoices') }}
