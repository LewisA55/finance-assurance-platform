{{ config(tags=['slice_b2']) }}

with spine as (
    select object_ref asset_id, period_id, legal_entity_id,
           count(*) resolved_business_event_count,
           sum(gl_journal_line_count) gl_journal_line_count,
           sum(gl_debit_minor)::bigint gl_debit_minor,
           sum(gl_credit_minor)::bigint gl_credit_minor
    from {{ ref('fct_subledger_event_links') }}
    where subledger_domain = 'FIXED_ASSET'
    group by object_ref, period_id, legal_entity_id
)
select
    md5(movement.asset_movement_id) as fixed_asset_movement_hk,
    movement.* exclude (_ingested_at, _source_file, _source_file_sha256),
    asset.asset_class,
    asset.useful_life_months,
    asset.depreciation_method,
    coalesce(spine.resolved_business_event_count, 0) as resolved_business_event_count,
    coalesce(spine.gl_journal_line_count, 0) as gl_journal_line_count,
    coalesce(spine.gl_debit_minor, 0)::bigint as gl_debit_minor,
    coalesce(spine.gl_credit_minor, 0)::bigint as gl_credit_minor,
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest
from {{ ref('stg_fixed_assets__fixed_asset_movements') }} movement
inner join {{ ref('dim_fixed_asset') }} asset using (asset_id, legal_entity_id)
inner join {{ ref('dim_reporting_version') }} version
  on movement.period_id = version.period_id and movement.legal_entity_id = version.scope_id
left join spine
  on movement.asset_id = spine.asset_id
 and movement.period_id = spine.period_id
 and movement.legal_entity_id = spine.legal_entity_id
