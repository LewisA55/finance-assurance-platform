{{ config(tags=['slice_b2']) }}

select
    md5(lifecycle.asset_lifecycle_event_id) as fixed_asset_lifecycle_event_hk,
    lifecycle.* exclude (_ingested_at, _source_file, _source_file_sha256),
    admission.admission_decision,
    admission.decision_reason,
    admission.candidate_business_event_ref,
    admission.quarantine_ref,
    asset.asset_class,
    asset.asset_status,
    asset.useful_life_months,
    asset.depreciation_method,
    'SOURCE_EVENT' as reliability_status,
    'FIXED_ASSET_ANALYTICS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest
from {{ ref('stg_fixed_assets__asset_lifecycle_events') }} lifecycle
inner join {{ ref('dim_fixed_asset') }} asset using (asset_id, legal_entity_id)
left join {{ ref('stg_hermes__source_admission_results') }} admission
  on lifecycle.source_record_ref = admission.source_record_ref
 and admission.source_dataset_path = 'fixed_assets/asset_lifecycle_events.csv'
