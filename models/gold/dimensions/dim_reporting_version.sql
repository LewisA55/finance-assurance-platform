select
    md5(close.reporting_version_ref) as reporting_version_hk,
    close.reporting_version_ref,
    close.period_id,
    close.legal_entity_id as scope_id,
    case
        when close.legal_entity_id = 'NEXUS-GROUP' then 'CONSOLIDATED_GROUP'
        else 'LEGAL_ENTITY'
    end as scope_type,
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
    case
        when close.close_status = 'HARD_CLOSED'
         and close.subledger_reconciliation_status = 'RECONCILED'
         and close.bank_reconciliation_status in ('RECONCILED', 'CONSOLIDATED', 'NOT_APPLICABLE')
         and close.intercompany_reconciliation_status in ('CONFIRMED', 'NOT_APPLICABLE')
         and close.trial_balance_status = 'BALANCED'
         and close.statement_status = 'PUBLISHED'
        then 'RELIABLE_FOR_STATUTORY_ACTUALS'
        else 'NOT_RELIABLE_FOR_STATUTORY_ACTUALS'
    end as reliability_status,
    'STATUTORY_ACTUALS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest,
    close._source_row_hash,
    close._source_data_ref
from {{ ref('stg_accounting__monthly_close_status') }} as close
