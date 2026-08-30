{{ config(tags=['slice_b3']) }}

select
    trim(period_id) as period_id,
    upper(trim(currency)) as currency,
    cast(opening_deferred_revenue_minor as bigint) as opening_deferred_revenue_minor,
    cast(new_billings_minor as bigint) as new_billings_minor,
    cast(recognised_revenue_minor as bigint) as recognised_revenue_minor,
    cast(closing_deferred_revenue_minor as bigint) as closing_deferred_revenue_minor,
    cast(reporting_opening_deferred_revenue_minor as bigint) as reporting_opening_deferred_revenue_minor,
    cast(reporting_new_billings_minor as bigint) as reporting_new_billings_minor,
    cast(reporting_recognised_revenue_minor as bigint) as reporting_recognised_revenue_minor,
    cast(reporting_closing_deferred_revenue_minor as bigint) as reporting_closing_deferred_revenue_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    upper(trim(source_system)) as source_system,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'revenue__deferred_revenue_rollforward') }}
