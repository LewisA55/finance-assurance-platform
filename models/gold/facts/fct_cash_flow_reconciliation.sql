select
    md5(concat_ws('|', cash.period_id, cash.scope_id, cash.reporting_version_ref)) as cash_flow_reconciliation_hk,
    cash.period_id,
    cash.scope_id,
    cash.opening_cash_minor,
    cash.operating_cash_flow_minor,
    cash.investing_cash_flow_minor,
    cash.financing_cash_flow_minor,
    cash.fx_and_other_movement_minor,
    cash.closing_cash_minor,
    cash.statement_cash_movement_minor,
    cash.unreconciled_difference_minor,
    cash.currency,
    cash.reporting_version_ref,
    cash.source_trial_balance_digest,
    cash.reconciliation_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest,
    cash._source_row_hash,
    cash._source_data_ref
from {{ ref('stg_accounting__cash_flow_reconciliation') }} as cash
inner join {{ ref('dim_reporting_version') }} as version
    on cash.reporting_version_ref = version.reporting_version_ref
