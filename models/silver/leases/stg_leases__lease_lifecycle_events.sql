{{ config(tags=['slice_b2']) }}

select
    trim(lease_lifecycle_event_id) as lease_lifecycle_event_id,
    trim(lease_contract_id) as lease_contract_id,
    trim(legal_entity_id) as legal_entity_id,
    upper(trim(event_type)) as event_type,
    cast(event_date as date) as event_date,
    cast(event_amount_minor as bigint) as event_amount_minor,
    upper(trim(currency)) as currency,
    cast(source_recorded_at as timestamptz) as source_recorded_at,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'leases__lease_lifecycle_events') }}
