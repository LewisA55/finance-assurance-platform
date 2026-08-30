{{ config(tags=['slice_b2']) }}

select
    trim(bank_account_id) as bank_account_id,
    trim(legal_entity_id) as legal_entity_id,
    trim(bank_name) as bank_name,
    upper(trim(account_type)) as account_type,
    upper(trim(currency)) as currency,
    cast(opened_date as date) as opened_date,
    cast(nullif(closed_date, '') as date) as closed_date,
    nullif(trim(linked_facility_id), '') as linked_facility_id,
    upper(trim(status)) as status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'treasury__bank_accounts') }}
