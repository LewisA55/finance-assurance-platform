{{ config(tags=['slice_b3']) }}

select
    trim(subscription_event_id) as subscription_event_id,
    trim(subscription_id) as subscription_id,
    trim(customer_id) as customer_id,
    cast(event_sequence as integer) as event_sequence,
    cast(event_date as date) as event_date,
    upper(trim(event_type)) as event_type,
    trim(event_reason) as event_reason,
    cast(previous_mrr_minor as bigint) as previous_mrr_minor,
    cast(new_mrr_minor as bigint) as new_mrr_minor,
    cast(mrr_delta_minor as bigint) as mrr_delta_minor,
    upper(trim(currency)) as currency,
    cast(reporting_previous_mrr_minor as bigint) as reporting_previous_mrr_minor,
    cast(reporting_new_mrr_minor as bigint) as reporting_new_mrr_minor,
    cast(reporting_mrr_delta_minor as bigint) as reporting_mrr_delta_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    upper(trim(source_system)) as source_system,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'billing__subscription_events') }}
