{{ config(tags=['slice_b2']) }}

with spine as (
    select object_ref jurisdiction_code, period_id, legal_entity_id,
           count(*) resolved_business_event_count,
           sum(gl_journal_line_count) gl_journal_line_count,
           sum(gl_debit_minor)::bigint gl_debit_minor,
           sum(gl_credit_minor)::bigint gl_credit_minor
    from {{ ref('fct_subledger_event_links') }}
    where subledger_domain = 'TAX'
    group by object_ref, period_id, legal_entity_id
)
select
    md5(concat_ws('|', schedule.period_id, schedule.legal_entity_id,
                  schedule.jurisdiction_code)) as tax_schedule_hk,
    schedule.* exclude (_ingested_at, _source_file, _source_file_sha256),
    coalesce(spine.resolved_business_event_count, 0) as resolved_business_event_count,
    coalesce(spine.gl_journal_line_count, 0) as gl_journal_line_count,
    coalesce(spine.gl_debit_minor, 0)::bigint as gl_debit_minor,
    coalesce(spine.gl_credit_minor, 0)::bigint as gl_credit_minor,
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest
from {{ ref('stg_tax__tax_schedule') }} schedule
inner join {{ ref('dim_tax_jurisdiction') }} jurisdiction
    using (legal_entity_id, jurisdiction_code)
inner join {{ ref('dim_reporting_version') }} version
  on schedule.period_id = version.period_id and schedule.legal_entity_id = version.scope_id
left join spine
  on schedule.jurisdiction_code = spine.jurisdiction_code
 and schedule.period_id = spine.period_id
 and schedule.legal_entity_id = spine.legal_entity_id
