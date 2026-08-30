{{ config(tags=['slice_b2']) }}

select
    trim(prepayment_schedule_id) as prepayment_schedule_id,
    trim(period_id) as period_id,
    trim(legal_entity_id) as legal_entity_id,
    trim(department_id) as department_id,
    trim(expense_account_id) as expense_account_id,
    cast(opening_prepayment_minor as bigint) as opening_prepayment_minor,
    cast(cash_addition_minor as bigint) as cash_addition_minor,
    cast(expense_release_minor as bigint) as expense_release_minor,
    cast(closing_prepayment_minor as bigint) as closing_prepayment_minor,
    upper(trim(currency)) as currency,
    coalesce(trim(business_event_refs), '') as business_event_refs,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'working_capital__prepayment_schedule') }}
