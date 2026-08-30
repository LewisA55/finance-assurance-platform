{{ config(tags=['slice_b2']) }}

select
    trim(admission_result_id) as admission_result_id,
    trim(source_dataset_path) as source_dataset_path,
    upper(trim(source_system)) as source_system,
    trim(source_record_ref) as source_record_ref,
    trim(source_record_hash) as source_record_hash,
    nullif(trim(candidate_business_event_ref), '') as candidate_business_event_ref,
    upper(trim(admission_decision)) as admission_decision,
    upper(trim(decision_reason)) as decision_reason,
    cast(event_time as timestamptz) as event_time,
    cast(ingested_at as timestamptz) as ingested_at,
    trim(legal_entity_id) as legal_entity_id,
    upper(trim(currency)) as currency,
    nullif(trim(duplicate_of_ref), '') as duplicate_of_ref,
    nullif(trim(quarantine_ref), '') as quarantine_ref,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'hermes__source_admission_results') }}
