{{ config(tags=['slice_b2']) }}

select
    trim(lease_contract_id) as lease_contract_id,
    trim(legal_entity_id) as legal_entity_id,
    trim(lessor_ref) as lessor_ref,
    upper(trim(lease_class)) as lease_class,
    cast(commencement_date as date) as commencement_date,
    cast(maturity_date as date) as maturity_date,
    upper(trim(payment_frequency)) as payment_frequency,
    cast(payment_minor as bigint) as payment_minor,
    upper(trim(currency)) as currency,
    cast(incremental_borrowing_rate_bps as integer) as incremental_borrowing_rate_bps,
    cast(initial_liability_minor as bigint) as initial_liability_minor,
    cast(initial_rou_asset_minor as bigint) as initial_rou_asset_minor,
    upper(trim(lease_status)) as lease_status,
    trim(approval_ref) as approval_ref,
    cast(source_recorded_at as timestamptz) as source_recorded_at,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'leases__lease_contracts') }}
