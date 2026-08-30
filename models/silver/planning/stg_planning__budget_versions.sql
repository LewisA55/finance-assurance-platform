{{ config(tags=['slice_b4']) }}

select
    trim(budget_version_ref) as budget_version_ref,
    trim(budget_name) as budget_name,
    trim(planning_start_period) as planning_start_period,
    trim(planning_end_period) as planning_end_period,
    upper(trim(approval_status)) as approval_status,
    cast(approved_at as timestamptz) as approved_at,
    cast(locked_flag as boolean) as locked_flag,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'planning__budget_versions') }}
