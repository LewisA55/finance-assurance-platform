{{ config(tags=['slice_b3']) }}

select
    md5(subscription.subscription_id) as subscription_hk,
    subscription.* exclude (_ingested_at, _source_file, _source_file_sha256),
    customer.region_id,
    customer.segment as customer_segment,
    product.product_family,
    product.revenue_type,
    product.gross_margin_target_bps
from {{ ref('stg_billing__subscriptions') }} subscription
inner join {{ ref('dim_customer') }} customer using (customer_id)
inner join {{ ref('dim_product') }} product using (product_id)
