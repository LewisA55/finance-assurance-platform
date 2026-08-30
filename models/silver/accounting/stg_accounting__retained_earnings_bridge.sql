select
    trim(period_id) as period_id,
    trim(scope_id) as scope_id,
    cast(opening_retained_earnings_minor as bigint) as opening_retained_earnings_minor,
    cast(net_income_minor as bigint) as net_income_minor,
    cast(dividends_minor as bigint) as dividends_minor,
    cast(other_equity_movements_minor as bigint) as other_equity_movements_minor,
    cast(closing_retained_earnings_minor as bigint) as closing_retained_earnings_minor,
    upper(trim(currency)) as currency,
    trim(reporting_version_ref) as reporting_version_ref,
    source_trial_balance_digest,
    upper(trim(reconciliation_status)) as reconciliation_status,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'accounting__retained_earnings_bridge') }}
