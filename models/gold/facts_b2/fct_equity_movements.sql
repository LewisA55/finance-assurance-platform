{{ config(tags=['slice_b2']) }}

select
    md5(movement.equity_movement_id) as equity_movement_hk,
    movement.* exclude (_ingested_at, _source_file, _source_file_sha256),
    link.gl_journal_line_count,
    link.gl_debit_minor,
    link.gl_credit_minor,
    event.record_semantic_hash as business_event_semantic_hash,
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest
from {{ ref('stg_equity__equity_movements') }} movement
inner join {{ ref('fct_business_events') }} event using (business_event_ref)
inner join {{ ref('dim_reporting_version') }} version
  on movement.period_id = version.period_id and movement.legal_entity_id = version.scope_id
left join {{ ref('fct_subledger_event_links') }} link
  on link.subledger_domain = 'EQUITY'
 and movement.equity_movement_id = link.object_ref
 and movement.business_event_ref = link.business_event_ref
