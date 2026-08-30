{{ config(tags=['slice_b2']) }}

select
    trim(test_result_id) as test_result_id,
    trim(test_definition_ref) as test_definition_ref,
    trim(test_run_ref) as test_run_ref,
    trim(period_id) as period_id,
    trim(legal_entity_id) as legal_entity_id,
    upper(trim(subledger_domain)) as subledger_domain,
    trim(object_ref) as object_ref,
    upper(trim(observation_type)) as observation_type,
    upper(trim(status)) as status,
    upper(trim(severity)) as severity,
    cast(expected_amount_minor as bigint) as expected_amount_minor,
    cast(actual_amount_minor as bigint) as actual_amount_minor,
    cast(difference_minor as bigint) as difference_minor,
    upper(trim(currency)) as currency,
    trim(evidence_ref) as evidence_ref,
    coalesce(trim(source_record_refs), '') as source_record_refs,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'assurance__statutory_subledger_control_results') }}
