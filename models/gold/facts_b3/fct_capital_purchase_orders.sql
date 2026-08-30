{{ config(tags=['slice_b3']) }}

select
    md5(po.capital_purchase_order_id) as capital_purchase_order_hk,
    po.* exclude (_ingested_at, _source_file, _source_file_sha256),
    vendor.category as vendor_category,
    vendor.region_id,
    strftime(po.order_date, '%Y-%m') as period_id
from {{ ref('stg_procurement__capital_purchase_orders') }} po
inner join {{ ref('dim_vendor') }} vendor using (vendor_id)
inner join {{ ref('dim_legal_entity') }} entity using (legal_entity_id)
