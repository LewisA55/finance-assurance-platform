{{ config(tags=['slice_b2']) }}

select
    trim(statement_line_id) as statement_line_id,
    trim(bank_account_id) as bank_account_id,
    cast(statement_date as date) as statement_date,
    trim(bank_transaction_id) as bank_transaction_id,
    cast(value_date as date) as value_date,
    cast(amount_minor as bigint) as amount_minor,
    cast(running_balance_minor as bigint) as running_balance_minor,
    upper(trim(currency)) as currency,
    trim(statement_ref) as statement_ref,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'treasury__bank_statement_lines') }}
