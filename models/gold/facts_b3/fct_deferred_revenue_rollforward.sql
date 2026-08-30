{{ config(tags=['slice_b3']) }}

select
    md5(concat_ws('|', rollforward.period_id, rollforward.currency)) as deferred_revenue_rollforward_hk,
    rollforward.* exclude (_ingested_at, _source_file, _source_file_sha256),
    group_version.reporting_version_ref,
    group_version.close_status,
    group_version.reliability_status,
    group_version.reliability_purpose,
    group_version.source_package_digest
from {{ ref('stg_revenue__deferred_revenue_rollforward') }} rollforward
inner join {{ ref('dim_reporting_version') }} group_version
  on rollforward.period_id = group_version.period_id
 and group_version.scope_id = 'NEXUS-GROUP'
