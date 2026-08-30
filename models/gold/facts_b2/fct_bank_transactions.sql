{{ config(tags=['slice_b2']) }}

select
    md5(transaction.bank_transaction_id) as bank_transaction_hk,
    transaction.* exclude (_ingested_at, _source_file, _source_file_sha256),
    strftime(transaction.book_date, '%Y-%m') as period_id,
    account.account_type,
    link.gl_journal_line_count,
    link.gl_debit_minor,
    link.gl_credit_minor,
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest
from {{ ref('stg_treasury__bank_transactions') }} transaction
inner join {{ ref('dim_bank_account') }} account using (bank_account_id, legal_entity_id)
inner join {{ ref('dim_reporting_version') }} version
  on strftime(transaction.book_date, '%Y-%m') = version.period_id
 and transaction.legal_entity_id = version.scope_id
left join {{ ref('fct_subledger_event_links') }} link
  on link.subledger_domain = 'BANKING'
 and transaction.bank_transaction_id = link.object_ref
 and transaction.business_event_ref = link.business_event_ref
