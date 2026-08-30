{{ config(tags=['slice_b2']) }}

select
    trim(asset_movement_id) as asset_movement_id,
    trim(period_id) as period_id,
    trim(asset_id) as asset_id,
    trim(legal_entity_id) as legal_entity_id,
    upper(trim(movement_type)) as movement_type,
    coalesce(trim(business_event_refs), '') as business_event_refs,
    cast(opening_gross_book_value_minor as bigint) as opening_gross_book_value_minor,
    cast(gross_addition_minor as bigint) as gross_addition_minor,
    cast(gross_disposal_minor as bigint) as gross_disposal_minor,
    cast(closing_gross_book_value_minor as bigint) as closing_gross_book_value_minor,
    cast(opening_accumulated_depreciation_minor as bigint) as opening_accumulated_depreciation_minor,
    cast(depreciation_minor as bigint) as depreciation_minor,
    cast(amortisation_minor as bigint) as amortisation_minor,
    cast(impairment_minor as bigint) as impairment_minor,
    cast(accumulated_depreciation_disposal_minor as bigint) as accumulated_depreciation_disposal_minor,
    cast(closing_accumulated_depreciation_minor as bigint) as closing_accumulated_depreciation_minor,
    cast(disposal_proceeds_minor as bigint) as disposal_proceeds_minor,
    cast(disposal_gain_loss_minor as bigint) as disposal_gain_loss_minor,
    cast(closing_net_book_value_minor as bigint) as closing_net_book_value_minor,
    upper(trim(currency)) as currency,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'fixed_assets__fixed_asset_movements') }}
