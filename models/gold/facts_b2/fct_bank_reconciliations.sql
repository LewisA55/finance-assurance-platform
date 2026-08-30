{{ config(tags=['slice_b2']) }}

select
    md5(concat_ws('|', reconciliation.period_id, reconciliation.bank_account_id)) as bank_reconciliation_hk,
    reconciliation.* exclude (_ingested_at, _source_file, _source_file_sha256),
    account.legal_entity_id,
    account.bank_name,
    account.account_type,
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest
from {{ ref('stg_treasury__bank_reconciliations') }} reconciliation
inner join {{ ref('dim_bank_account') }} account using (bank_account_id)
inner join {{ ref('dim_reporting_version') }} version
  on reconciliation.period_id = version.period_id and account.legal_entity_id = version.scope_id
