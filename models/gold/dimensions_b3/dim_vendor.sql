{{ config(tags=['slice_b3']) }}

select
    md5(vendor.vendor_id) as vendor_hk,
    vendor.* exclude (_ingested_at, _source_file, _source_file_sha256),
    region.region_name,
    region.local_currency,
    region.reporting_currency
from {{ ref('stg_procurement__vendors') }} vendor
inner join {{ ref('dim_region') }} region using (region_id)
