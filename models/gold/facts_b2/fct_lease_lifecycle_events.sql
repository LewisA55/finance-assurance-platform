{{ config(tags=['slice_b2']) }}

select
    md5(lifecycle.lease_lifecycle_event_id) as lease_lifecycle_event_hk,
    lifecycle.* exclude (_ingested_at, _source_file, _source_file_sha256),
    lease.lease_class,
    lease.lessor_ref,
    lease.maturity_date,
    lease.lease_status,
    admission.admission_decision,
    admission.decision_reason,
    admission.candidate_business_event_ref,
    admission.quarantine_ref,
    'SOURCE_EVENT' as reliability_status,
    'LEASE_ANALYTICS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest
from {{ ref('stg_leases__lease_lifecycle_events') }} lifecycle
inner join {{ ref('dim_lease_contract') }} lease using (lease_contract_id, legal_entity_id)
left join {{ ref('stg_hermes__source_admission_results') }} admission
  on lifecycle.lease_lifecycle_event_id = admission.source_record_ref
 and admission.source_dataset_path = 'leases/lease_lifecycle_events.csv'
