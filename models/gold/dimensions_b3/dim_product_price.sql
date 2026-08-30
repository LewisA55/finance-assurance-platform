{{ config(tags=['slice_b3']) }}

select
    md5(price_book_id) as product_price_hk,
    price.* exclude (_ingested_at, _source_file, _source_file_sha256),
    product.product_name,
    region.region_name
from {{ ref('stg_reference__product_price_book') }} price
inner join {{ ref('dim_product') }} product using (product_id)
inner join {{ ref('dim_region') }} region using (region_id)
