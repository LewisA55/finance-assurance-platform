{{ config(tags=['slice_b2']) }}

select
    trim(period_id) as period_id,
    trim(debt_instrument_id) as debt_instrument_id,
    trim(legal_entity_id) as legal_entity_id,
    cast(opening_principal_minor as bigint) as opening_principal_minor,
    cast(drawdown_minor as bigint) as drawdown_minor,
    cast(principal_repayment_minor as bigint) as principal_repayment_minor,
    cast(cash_interest_minor as bigint) as cash_interest_minor,
    cast(accrued_interest_minor as bigint) as accrued_interest_minor,
    cast(closing_principal_minor as bigint) as closing_principal_minor,
    cast(undrawn_facility_minor as bigint) as undrawn_facility_minor,
    cast(effective_interest_rate_bps as integer) as effective_interest_rate_bps,
    upper(trim(currency)) as currency,
    coalesce(trim(business_event_refs), '') as business_event_refs,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'treasury__debt_schedule') }}
