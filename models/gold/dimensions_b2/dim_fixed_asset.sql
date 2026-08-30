{{ config(tags=['slice_b2']) }}

select
    md5(asset.asset_id) as fixed_asset_hk,
    asset.asset_id,
    asset.legal_entity_id,
    entity.legal_entity_name,
    asset.asset_class,
    asset.source_system,
    asset.source_record_ref,
    asset.acquisition_business_event_ref,
    asset.capital_purchase_order_id,
    asset.capital_goods_receipt_id,
    asset.capital_invoice_id,
    asset.acquisition_date,
    asset.in_service_date,
    asset.cost_minor,
    asset.residual_value_minor,
    asset.currency,
    asset.useful_life_months,
    asset.depreciation_method,
    asset.disposal_date,
    asset.asset_status,
    event.record_semantic_hash as acquisition_event_semantic_hash,
    'SOURCE_MASTER_DATA' as reliability_status,
    'FIXED_ASSET_ANALYTICS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest,
    asset._source_row_hash,
    asset._source_data_ref
from {{ ref('stg_fixed_assets__fixed_asset_register') }} as asset
inner join {{ ref('dim_legal_entity') }} as entity using (legal_entity_id)
left join {{ ref('fct_business_events') }} as event
    on asset.acquisition_business_event_ref = event.business_event_ref
