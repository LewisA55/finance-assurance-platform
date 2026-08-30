{{ config(tags=['slice_b3']) }}

select
    trim(capital_purchase_order_id) as capital_purchase_order_id,
    trim(legal_entity_id) as legal_entity_id,
    trim(vendor_id) as vendor_id,
    cast(order_date as date) as order_date,
    upper(trim(asset_class)) as asset_class,
    trim(asset_description) as asset_description,
    cast(ordered_amount_minor as bigint) as ordered_amount_minor,
    upper(trim(currency)) as currency,
    trim(approval_ref) as approval_ref,
    upper(trim(purchase_order_status)) as purchase_order_status,
    cast(source_recorded_at as timestamptz) as source_recorded_at,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'procurement__capital_purchase_orders') }}
