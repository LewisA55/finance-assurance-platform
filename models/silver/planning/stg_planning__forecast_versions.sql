{{ config(tags=['slice_b4']) }}

select
    trim(forecast_version_ref) as forecast_version_ref,
    upper(trim(scenario_code)) as scenario_code,
    trim(cutover_period) as cutover_period,
    trim(forecast_start_period) as forecast_start_period,
    trim(forecast_end_period) as forecast_end_period,
    trim(source_budget_version_ref) as source_budget_version_ref,
    upper(trim(approval_status)) as approval_status,
    cast(locked_flag as boolean) as locked_flag,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'planning__forecast_versions') }}
