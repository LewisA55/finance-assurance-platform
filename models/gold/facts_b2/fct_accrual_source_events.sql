{{ config(tags=['slice_b2']) }}

select
    md5(event.accrual_source_event_id) as accrual_source_event_hk,
    event.* exclude (_ingested_at, _source_file, _source_file_sha256),
    admission.admission_decision,
    admission.decision_reason,
    admission.candidate_business_event_ref,
    admission.quarantine_ref,
    'SOURCE_EVENT' as reliability_status,
    'ACCRUAL_ANALYTICS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest
from {{ ref('stg_working_capital__accrual_source_events') }} event
left join {{ ref('stg_hermes__source_admission_results') }} admission
  on event.accrual_source_event_id = admission.source_record_ref
 and admission.source_dataset_path = 'working_capital/accrual_source_events.csv'
