select
    trim(reconciliation_ref) as reconciliation_ref,
    trim(period_id) as period_id,
    trim(scope_id) as scope_id,
    trim(reporting_version_ref) as reporting_version_ref,
    upper(trim(control_id)) as control_id,
    cast(expected_amount_minor as bigint) as expected_amount_minor,
    cast(actual_amount_minor as bigint) as actual_amount_minor,
    cast(difference_minor as bigint) as difference_minor,
    upper(trim(currency)) as currency,
    upper(trim(status)) as status,
    trim(evidence_ref) as evidence_ref,
    nullif(trim(first_failure_ref), '') as first_failure_ref,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'governance__statutory_reconciliation_results') }}
