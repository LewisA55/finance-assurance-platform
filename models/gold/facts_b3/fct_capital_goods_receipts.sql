{{ config(tags=['slice_b3']) }}

select
    md5(receipt.capital_goods_receipt_id) as capital_goods_receipt_hk,
    receipt.* exclude (_ingested_at, _source_file, _source_file_sha256),
    po.vendor_id,
    po.asset_class,
    po.ordered_amount_minor,
    po.currency,
    po.approval_ref,
    strftime(receipt.receipt_date, '%Y-%m') as period_id
from {{ ref('stg_procurement__capital_goods_receipts') }} receipt
inner join {{ ref('fct_capital_purchase_orders') }} po
  using (capital_purchase_order_id, legal_entity_id)
