{{ config(tags=['slice_b4']) }}

select
    trim(variance_line_id) as variance_line_id,
    trim(period_id) as period_id,
    upper(trim(period_status)) as period_status,
    trim(department_id) as department_id,
    trim(account_id) as account_id,
    cast(actual_amount_minor as bigint) as actual_amount_minor,
    cast(budget_amount_minor as bigint) as budget_amount_minor,
    cast(forecast_amount_minor as bigint) as forecast_amount_minor,
    cast(actual_vs_budget_variance_minor as bigint) as actual_vs_budget_variance_minor,
    cast(actual_vs_forecast_variance_minor as bigint) as actual_vs_forecast_variance_minor,
    cast(forecast_vs_budget_variance_minor as bigint) as forecast_vs_budget_variance_minor,
    upper(trim(currency)) as currency,
    nullif(trim(source_budget_line_ref), '') as source_budget_line_ref,
    nullif(trim(source_forecast_line_ref), '') as source_forecast_line_ref,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'planning__variance_source_extract') }}
