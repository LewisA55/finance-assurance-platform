{{ config(tags=['slice_b2']) }}

select
    trim(asset_lifecycle_event_id) as asset_lifecycle_event_id,
    trim(asset_id) as asset_id,
    trim(legal_entity_id) as legal_entity_id,
    upper(trim(event_type)) as event_type,
    cast(event_date as date) as event_date,
    trim(source_record_ref) as source_record_ref,
    nullif(trim(related_capital_invoice_id), '') as related_capital_invoice_id,
    cast(event_amount_minor as bigint) as event_amount_minor,
    cast(gross_cost_minor as bigint) as gross_cost_minor,
    cast(accumulated_depreciation_minor as bigint) as accumulated_depreciation_minor,
    cast(disposal_proceeds_minor as bigint) as disposal_proceeds_minor,
    upper(trim(currency)) as currency,
    trim(authorisation_ref) as authorisation_ref,
    cast(source_recorded_at as timestamptz) as source_recorded_at,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'fixed_assets__asset_lifecycle_events') }}
