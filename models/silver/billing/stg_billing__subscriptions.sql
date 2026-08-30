{{ config(tags=['slice_b3']) }}

select
    trim(subscription_id) as subscription_id,
    trim(customer_id) as customer_id,
    trim(product_id) as product_id,
    cast(contract_start_date as date) as contract_start_date,
    cast(nullif(trim(contract_end_date), '') as date) as contract_end_date,
    upper(trim(billing_frequency)) as billing_frequency,
    cast(monthly_recurring_revenue_minor as bigint) as monthly_recurring_revenue_minor,
    upper(trim(currency)) as currency,
    upper(trim(status)) as status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'billing__subscriptions') }}
