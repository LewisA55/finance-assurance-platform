{{ config(tags=['slice_b4']) }}

select
    trim(budget_line_id) as budget_line_id,
    trim(budget_version_ref) as budget_version_ref,
    trim(period_id) as period_id,
    trim(department_id) as department_id,
    trim(account_id) as account_id,
    cast(amount_minor as bigint) as amount_minor,
    upper(trim(currency)) as currency,
    cast(reporting_amount_minor as bigint) as reporting_amount_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    upper(trim(approval_status)) as approval_status,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'planning__budget_lines') }}
