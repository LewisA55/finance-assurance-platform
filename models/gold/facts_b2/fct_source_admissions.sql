{{ config(tags=['slice_b2']) }}

select
    md5(admission.admission_result_id) as source_admission_hk,
    admission.* exclude (_ingested_at, _source_file, _source_file_sha256),
    event.event_type,
    event.record_semantic_hash as business_event_semantic_hash,
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    'SOURCE_ADMISSION_AND_QUARANTINE' as reliability_purpose,
    version.source_package_digest
from {{ ref('stg_hermes__source_admission_results') }} admission
left join {{ ref('fct_business_events') }} event
  on admission.candidate_business_event_ref = event.business_event_ref
left join {{ ref('dim_reporting_version') }} version
  on strftime(cast(admission.event_time as date), '%Y-%m') = version.period_id
 and admission.legal_entity_id = version.scope_id
where admission.source_dataset_path in (
    'fixed_assets/asset_lifecycle_events.csv',
    'leases/lease_lifecycle_events.csv',
    'working_capital/accrual_source_events.csv',
    'working_capital/prepayment_source_events.csv',
    'intercompany/intercompany_transactions.csv'
)
