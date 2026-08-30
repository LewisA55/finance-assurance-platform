{{ config(tags=['slice_b3']) }}

select
    trim(region_id) as region_id,
    trim(region_name) as region_name,
    upper(trim(local_currency)) as local_currency,
    upper(trim(reporting_currency)) as reporting_currency,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'reference__regions') }}
