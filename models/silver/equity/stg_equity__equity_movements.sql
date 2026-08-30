{{ config(tags=['slice_b2']) }}

select
    trim(equity_movement_id) as equity_movement_id,
    trim(period_id) as period_id,
    trim(legal_entity_id) as legal_entity_id,
    upper(trim(equity_component)) as equity_component,
    upper(trim(movement_type)) as movement_type,
    trim(business_event_ref) as business_event_ref,
    cast(amount_minor as bigint) as amount_minor,
    upper(trim(currency)) as currency,
    trim(authorisation_ref) as authorisation_ref,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'equity__equity_movements') }}
