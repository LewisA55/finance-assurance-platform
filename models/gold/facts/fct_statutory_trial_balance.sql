select
    md5(concat_ws('|', tb.period_id, tb.scope_id, tb.legal_entity_id, tb.account_id, tb.reporting_version_ref)) as trial_balance_hk,
    tb.period_id,
    tb.scope_id,
    tb.legal_entity_id,
    tb.account_id,
    tb.opening_balance_minor,
    tb.debit_activity_minor,
    tb.credit_activity_minor,
    tb.elimination_debit_minor,
    tb.elimination_credit_minor,
    tb.closing_balance_minor,
    tb.currency,
    tb.reporting_version_ref,
    tb.close_status,
    account.account_class,
    account.statement_class,
    account.statement_line,
    account.normal_balance,
    account.cash_flow_class,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest,
    tb._source_row_hash,
    tb._source_data_ref
from {{ ref('stg_accounting__statutory_trial_balance') }} as tb
inner join {{ ref('dim_gl_account') }} as account
    on tb.account_id = account.account_id
inner join {{ ref('dim_reporting_version') }} as version
    on tb.reporting_version_ref = version.reporting_version_ref
