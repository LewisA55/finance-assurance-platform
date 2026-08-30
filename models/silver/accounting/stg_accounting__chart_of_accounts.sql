select
    trim(account_id) as account_id,
    trim(account_name) as account_name,
    upper(trim(account_class)) as account_class,
    upper(trim(statement_class)) as statement_class,
    lower(trim(statement_line)) as statement_line,
    upper(trim(normal_balance)) as normal_balance,
    upper(trim(cash_flow_class)) as cash_flow_class,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'accounting__chart_of_accounts') }}
