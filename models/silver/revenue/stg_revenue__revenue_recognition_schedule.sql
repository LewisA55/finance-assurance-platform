{{ config(tags=['slice_b3']) }}

select
    trim(schedule_id) as schedule_id,
    trim(invoice_id) as invoice_id,
    trim(subscription_id) as subscription_id,
    trim(recognition_period) as recognition_period,
    cast(recognition_date as date) as recognition_date,
    cast(revenue_amount_minor as bigint) as revenue_amount_minor,
    upper(trim(currency)) as currency,
    cast(reporting_revenue_amount_minor as bigint) as reporting_revenue_amount_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    upper(trim(recognition_status)) as recognition_status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'revenue__revenue_recognition_schedule') }}
