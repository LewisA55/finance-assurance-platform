{{ config(tags=['slice_b2']) }}

select
    md5(control.test_result_id) as statutory_subledger_control_hk,
    control.* exclude (_ingested_at, _source_file, _source_file_sha256),
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest
from {{ ref('stg_assurance__statutory_subledger_control_results') }} control
inner join {{ ref('dim_reporting_version') }} version
  on control.period_id = version.period_id and control.legal_entity_id = version.scope_id
