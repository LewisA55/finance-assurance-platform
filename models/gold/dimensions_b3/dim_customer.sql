{{ config(tags=['slice_b3']) }}

select
    md5(customer.customer_id) as customer_hk,
    customer.* exclude (_ingested_at, _source_file, _source_file_sha256),
    region.region_name,
    region.local_currency,
    region.reporting_currency
from {{ ref('stg_billing__customers') }} customer
inner join {{ ref('dim_region') }} region using (region_id)
