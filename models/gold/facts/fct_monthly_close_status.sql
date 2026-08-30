select
    md5(concat_ws('|', close.period_id, close.legal_entity_id, close.reporting_version_ref)) as monthly_close_status_hk,
    close.period_id,
    close.legal_entity_id as scope_id,
    close.reporting_version_ref,
    close.soft_close_accounting_event_ref,
    close.hard_close_accounting_event_ref,
    close.reporting_publication_accounting_event_ref,
    close.subledger_reconciliation_status,
    close.bank_reconciliation_status,
    close.intercompany_reconciliation_status,
    close.trial_balance_status,
    close.statement_status,
    close.close_status,
    close.closed_at,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest,
    close._source_row_hash,
    close._source_data_ref
from {{ ref('stg_accounting__monthly_close_status') }} as close
inner join {{ ref('dim_reporting_version') }} as version
    on close.reporting_version_ref = version.reporting_version_ref
