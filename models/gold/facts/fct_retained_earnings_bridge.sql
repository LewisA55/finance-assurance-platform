select
    md5(concat_ws('|', bridge.period_id, bridge.scope_id, bridge.reporting_version_ref)) as retained_earnings_bridge_hk,
    bridge.period_id,
    bridge.scope_id,
    bridge.opening_retained_earnings_minor,
    bridge.net_income_minor,
    bridge.dividends_minor,
    bridge.other_equity_movements_minor,
    bridge.closing_retained_earnings_minor,
    bridge.currency,
    bridge.reporting_version_ref,
    bridge.source_trial_balance_digest,
    bridge.reconciliation_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest,
    bridge._source_row_hash,
    bridge._source_data_ref
from {{ ref('stg_accounting__retained_earnings_bridge') }} as bridge
inner join {{ ref('dim_reporting_version') }} as version
    on bridge.reporting_version_ref = version.reporting_version_ref
