{{ config(tags=['slice_b2']) }}

with schedule_links as (
    select 'FIXED_ASSET' subledger_domain, asset_id object_ref, period_id, legal_entity_id,
           trim(ref) business_event_ref
    from {{ ref('stg_fixed_assets__fixed_asset_movements') }},
         unnest(string_split(business_event_refs, ',')) refs(ref)
    where business_event_refs <> ''
    union all
    select 'DEBT', debt_instrument_id, period_id, legal_entity_id, trim(ref)
    from {{ ref('stg_treasury__debt_schedule') }},
         unnest(string_split(business_event_refs, ',')) refs(ref)
    where business_event_refs <> ''
    union all
    select 'LEASE', lease_contract_id, period_id, legal_entity_id, trim(ref)
    from {{ ref('stg_leases__lease_schedule') }},
         unnest(string_split(business_event_refs, ',')) refs(ref)
    where business_event_refs <> ''
    union all
    select 'TAX', jurisdiction_code, period_id, legal_entity_id, trim(ref)
    from {{ ref('stg_tax__tax_schedule') }},
         unnest(string_split(business_event_refs, ',')) refs(ref)
    where business_event_refs <> ''
    union all
    select 'ACCRUAL', accrual_schedule_id, period_id, legal_entity_id, trim(ref)
    from {{ ref('stg_working_capital__accrual_schedule') }},
         unnest(string_split(business_event_refs, ',')) refs(ref)
    where business_event_refs <> ''
    union all
    select 'PREPAYMENT', prepayment_schedule_id, period_id, legal_entity_id, trim(ref)
    from {{ ref('stg_working_capital__prepayment_schedule') }},
         unnest(string_split(business_event_refs, ',')) refs(ref)
    where business_event_refs <> ''
    union all
    select 'EQUITY', equity_movement_id, period_id, legal_entity_id, business_event_ref
    from {{ ref('stg_equity__equity_movements') }}
    union all
    select 'BANKING', bank_transaction_id, strftime(book_date, '%Y-%m'),
           legal_entity_id, business_event_ref
    from {{ ref('stg_treasury__bank_transactions') }}
), intercompany_links as (
    select 'INTERCOMPANY' subledger_domain, transaction.intercompany_transaction_id object_ref,
           transaction.period_id, admission.legal_entity_id,
           admission.candidate_business_event_ref business_event_ref
    from {{ ref('stg_intercompany__intercompany_transactions') }} transaction
    inner join {{ ref('stg_hermes__source_admission_results') }} admission
      on admission.source_record_ref in (
          transaction.seller_source_record_ref, transaction.buyer_source_record_ref
      )
    where admission.admission_decision = 'ADMITTED'
), links as (
    select distinct * from schedule_links
    union
    select distinct * from intercompany_links
), gl as (
    select business_event_ref, legal_entity_id,
           count(*) gl_journal_line_count,
           sum(debit_minor) gl_debit_minor,
           sum(credit_minor) gl_credit_minor
    from {{ ref('fct_gl_journal_lines') }}
    group by business_event_ref, legal_entity_id
)
select
    md5(concat_ws('|', link.subledger_domain, link.object_ref, link.period_id,
                  link.legal_entity_id, link.business_event_ref)) as subledger_event_link_hk,
    link.subledger_domain,
    link.object_ref,
    link.period_id,
    link.legal_entity_id,
    link.business_event_ref,
    event.event_type,
    event.source_system,
    event.source_record_ref,
    event.record_semantic_hash,
    coalesce(gl.gl_journal_line_count, 0) as gl_journal_line_count,
    coalesce(gl.gl_debit_minor, 0)::bigint as gl_debit_minor,
    coalesce(gl.gl_credit_minor, 0)::bigint as gl_credit_minor,
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest,
    event._source_data_ref
from links link
left join {{ ref('fct_business_events') }} event
  on link.business_event_ref = event.business_event_ref
left join gl
  on link.business_event_ref = gl.business_event_ref
 and link.legal_entity_id = gl.legal_entity_id
left join {{ ref('dim_reporting_version') }} version
  on link.period_id = version.period_id and link.legal_entity_id = version.scope_id
