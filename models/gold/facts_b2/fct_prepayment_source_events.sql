{{ config(tags=['slice_b2']) }}

select
    md5(event.prepayment_source_event_id) as prepayment_source_event_hk,
    event.* exclude (_ingested_at, _source_file, _source_file_sha256),
    admission.admission_decision,
    admission.decision_reason,
    admission.candidate_business_event_ref,
    admission.quarantine_ref,
    case when event.duplicate_of_ref is null then false else true end as is_declared_duplicate,
    case when admission.admission_decision = 'ADMITTED' then true else false end as is_posting_eligible,
    'SOURCE_EVENT_WITH_ADMISSION_DECISION' as reliability_status,
    'PREPAYMENT_ANALYTICS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest
from {{ ref('stg_working_capital__prepayment_source_events') }} event
left join {{ ref('stg_hermes__source_admission_results') }} admission
  on event.prepayment_source_event_id = admission.source_record_ref
 and admission.source_dataset_path = 'working_capital/prepayment_source_events.csv'
