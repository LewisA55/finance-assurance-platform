{{ config(tags=['slice_b2']) }}

select
    trim(accrual_schedule_id) as accrual_schedule_id,
    trim(period_id) as period_id,
    trim(legal_entity_id) as legal_entity_id,
    trim(department_id) as department_id,
    trim(expense_account_id) as expense_account_id,
    cast(opening_accrual_minor as bigint) as opening_accrual_minor,
    cast(addition_minor as bigint) as addition_minor,
    cast(release_minor as bigint) as release_minor,
    cast(closing_accrual_minor as bigint) as closing_accrual_minor,
    upper(trim(currency)) as currency,
    coalesce(trim(business_event_refs), '') as business_event_refs,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'working_capital__accrual_schedule') }}
