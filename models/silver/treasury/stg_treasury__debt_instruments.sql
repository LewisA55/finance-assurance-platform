{{ config(tags=['slice_b2']) }}

select
    trim(debt_instrument_id) as debt_instrument_id,
    trim(legal_entity_id) as legal_entity_id,
    trim(lender_name) as lender_name,
    upper(trim(facility_type)) as facility_type,
    upper(trim(currency)) as currency,
    cast(facility_limit_minor as bigint) as facility_limit_minor,
    cast(start_date as date) as start_date,
    cast(maturity_date as date) as maturity_date,
    cast(fixed_rate_bps as integer) as fixed_rate_bps,
    cast(margin_bps as integer) as margin_bps,
    nullif(trim(base_rate_ref), '') as base_rate_ref,
    upper(trim(repayment_profile)) as repayment_profile,
    trim(covenant_policy_ref) as covenant_policy_ref,
    upper(trim(instrument_status)) as instrument_status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'treasury__debt_instruments') }}
