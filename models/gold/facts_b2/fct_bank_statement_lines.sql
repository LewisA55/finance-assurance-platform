{{ config(tags=['slice_b2']) }}

select
    md5(statement.statement_line_id) as bank_statement_line_hk,
    statement.* exclude (_ingested_at, _source_file, _source_file_sha256),
    transaction.legal_entity_id,
    transaction.business_event_ref,
    transaction.source_record_ref,
    transaction.transaction_type,
    transaction.bank_status,
    transaction.reconciliation_status,
    strftime(statement.statement_date, '%Y-%m') as period_id,
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest
from {{ ref('stg_treasury__bank_statement_lines') }} statement
inner join {{ ref('stg_treasury__bank_transactions') }} transaction
    using (bank_transaction_id, bank_account_id)
inner join {{ ref('dim_reporting_version') }} version
  on strftime(statement.statement_date, '%Y-%m') = version.period_id
 and transaction.legal_entity_id = version.scope_id
