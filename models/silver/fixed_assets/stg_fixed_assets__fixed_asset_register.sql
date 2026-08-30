{{ config(tags=['slice_b2']) }}

select
    trim(asset_id) as asset_id,
    trim(legal_entity_id) as legal_entity_id,
    upper(trim(asset_class)) as asset_class,
    upper(trim(source_system)) as source_system,
    trim(source_record_ref) as source_record_ref,
    trim(acquisition_business_event_ref) as acquisition_business_event_ref,
    nullif(trim(capital_purchase_order_id), '') as capital_purchase_order_id,
    nullif(trim(capital_goods_receipt_id), '') as capital_goods_receipt_id,
    nullif(trim(capital_invoice_id), '') as capital_invoice_id,
    cast(acquisition_date as date) as acquisition_date,
    cast(in_service_date as date) as in_service_date,
    cast(cost_minor as bigint) as cost_minor,
    cast(residual_value_minor as bigint) as residual_value_minor,
    upper(trim(currency)) as currency,
    cast(useful_life_months as integer) as useful_life_months,
    upper(trim(depreciation_method)) as depreciation_method,
    cast(nullif(disposal_date, '') as date) as disposal_date,
    upper(trim(asset_status)) as asset_status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'fixed_assets__fixed_asset_register') }}
