select
    trim(period_id) as period_id,
    trim(scope_id) as scope_id,
    upper(trim(statement_class)) as statement_class,
    lower(trim(statement_line)) as statement_line,
    cast(amount_minor as bigint) as amount_minor,
    upper(trim(currency)) as currency,
    trim(reporting_version_ref) as reporting_version_ref,
    source_trial_balance_digest,
    cast(presentation_order as integer) as presentation_order,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'accounting__statutory_statement_lines') }}
