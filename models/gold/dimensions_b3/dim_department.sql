{{ config(tags=['slice_b3']) }}

select
    md5(department_id) as department_hk,
    * exclude (_ingested_at, _source_file, _source_file_sha256)
from {{ ref('stg_reference__departments') }}
