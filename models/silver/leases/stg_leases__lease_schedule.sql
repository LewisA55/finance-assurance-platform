{{ config(tags=['slice_b2']) }}

select
    trim(period_id) as period_id,
    trim(lease_contract_id) as lease_contract_id,
    trim(legal_entity_id) as legal_entity_id,
    cast(opening_liability_minor as bigint) as opening_liability_minor,
    cast(liability_addition_minor as bigint) as liability_addition_minor,
    cast(cash_payment_minor as bigint) as cash_payment_minor,
    cast(interest_accretion_minor as bigint) as interest_accretion_minor,
    cast(principal_reduction_minor as bigint) as principal_reduction_minor,
    cast(closing_liability_minor as bigint) as closing_liability_minor,
    cast(opening_rou_asset_minor as bigint) as opening_rou_asset_minor,
    cast(rou_asset_addition_minor as bigint) as rou_asset_addition_minor,
    cast(rou_depreciation_minor as bigint) as rou_depreciation_minor,
    cast(rou_impairment_minor as bigint) as rou_impairment_minor,
    cast(closing_rou_asset_minor as bigint) as closing_rou_asset_minor,
    upper(trim(currency)) as currency,
    coalesce(trim(business_event_refs), '') as business_event_refs,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'leases__lease_schedule') }}
