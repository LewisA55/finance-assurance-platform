{{ config(tags=['slice_b2']) }}

select
    md5(control.test_result_id) as fixed_asset_control_result_hk,
    control.* exclude (_ingested_at, _source_file, _source_file_sha256),
    asset.legal_entity_id,
    case when nullif(control.asset_id, '') is null then 'PORTFOLIO' else 'ASSET' end as control_scope,
    asset.asset_class,
    version.reporting_version_ref,
    version.close_status,
    coalesce(version.reliability_status, 'SOURCE_ASSURANCE_RESULT') as reliability_status,
    coalesce(version.reliability_purpose, 'FIXED_ASSET_ASSURANCE') as reliability_purpose,
    coalesce(version.source_package_digest, '{{ var("a24_package_digest") }}') as source_package_digest
from {{ ref('stg_assurance__fixed_asset_control_results') }} control
left join {{ ref('dim_fixed_asset') }} asset using (asset_id)
left join {{ ref('dim_reporting_version') }} version
  on control.period_id = version.period_id and asset.legal_entity_id = version.scope_id
