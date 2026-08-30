{{ config(tags=['slice_b3']) }}

select
    trim(capital_goods_receipt_id) as capital_goods_receipt_id,
    trim(capital_purchase_order_id) as capital_purchase_order_id,
    trim(legal_entity_id) as legal_entity_id,
    cast(receipt_date as date) as receipt_date,
    cast(quantity_received as integer) as quantity_received,
    trim(receiver_ref) as receiver_ref,
    upper(trim(receipt_status)) as receipt_status,
    cast(source_recorded_at as timestamptz) as source_recorded_at,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'procurement__capital_goods_receipts') }}
