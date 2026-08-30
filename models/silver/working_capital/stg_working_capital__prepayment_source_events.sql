{{ config(tags=['slice_b2']) }}

select
    trim(prepayment_source_event_id) as prepayment_source_event_id,
    trim(prepayment_schedule_id) as prepayment_schedule_id,
    upper(trim(event_type)) as event_type,
    cast(event_date as date) as event_date,
    trim(legal_entity_id) as legal_entity_id,
    trim(department_id) as department_id,
    trim(expense_account_id) as expense_account_id,
    trim(counterparty_ref) as counterparty_ref,
    cast(event_amount_minor as bigint) as event_amount_minor,
    upper(trim(currency)) as currency,
    trim(approval_ref) as approval_ref,
    cast(source_recorded_at as timestamptz) as source_recorded_at,
    nullif(trim(duplicate_of_ref), '') as duplicate_of_ref,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'working_capital__prepayment_source_events') }}
