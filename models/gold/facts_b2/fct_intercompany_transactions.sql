{{ config(tags=['slice_b2']) }}

with admission as (
    select source_record_ref, legal_entity_id, candidate_business_event_ref,
           admission_decision, decision_reason, source_record_hash
    from {{ ref('stg_hermes__source_admission_results') }}
    where source_dataset_path = 'intercompany/intercompany_transactions.csv'
), elimination as (
    select source_intercompany_transaction_id as intercompany_transaction_id,
           count(*) elimination_line_count,
           sum(debit_minor)::bigint elimination_debit_minor,
           sum(credit_minor)::bigint elimination_credit_minor,
           min(accounting_event_ref) accounting_event_ref
    from {{ ref('fct_elimination_journal_lines') }}
    group by source_intercompany_transaction_id
)
select
    md5(tx.intercompany_transaction_id) as intercompany_transaction_hk,
    tx.* exclude (_ingested_at, _source_file, _source_file_sha256),
    seller.candidate_business_event_ref as seller_business_event_ref,
    buyer.candidate_business_event_ref as buyer_business_event_ref,
    seller.source_record_hash as seller_source_record_hash,
    buyer.source_record_hash as buyer_source_record_hash,
    seller.admission_decision as seller_admission_decision,
    buyer.admission_decision as buyer_admission_decision,
    coalesce(elimination.elimination_line_count, 0) as elimination_line_count,
    coalesce(elimination.elimination_debit_minor, 0)::bigint as elimination_debit_minor,
    coalesce(elimination.elimination_credit_minor, 0)::bigint as elimination_credit_minor,
    elimination.accounting_event_ref as elimination_accounting_event_ref,
    seller_version.reporting_version_ref as seller_reporting_version_ref,
    buyer_version.reporting_version_ref as buyer_reporting_version_ref,
    seller_version.close_status as seller_close_status,
    buyer_version.close_status as buyer_close_status,
    case
      when seller_version.reliability_status = 'RELIABLE_FOR_STATUTORY_ACTUALS'
       and buyer_version.reliability_status = 'RELIABLE_FOR_STATUTORY_ACTUALS'
      then 'RELIABLE_FOR_STATUTORY_ACTUALS'
      else 'NOT_RELIABLE_FOR_STATUTORY_ACTUALS'
    end as reliability_status,
    'INTERCOMPANY_ANALYTICS' as reliability_purpose,
    seller_version.source_package_digest
from {{ ref('stg_intercompany__intercompany_transactions') }} tx
inner join admission seller
  on tx.seller_source_record_ref = seller.source_record_ref
 and tx.seller_entity_id = seller.legal_entity_id
inner join admission buyer
  on tx.buyer_source_record_ref = buyer.source_record_ref
 and tx.buyer_entity_id = buyer.legal_entity_id
inner join {{ ref('dim_reporting_version') }} seller_version
  on tx.period_id = seller_version.period_id and tx.seller_entity_id = seller_version.scope_id
inner join {{ ref('dim_reporting_version') }} buyer_version
  on tx.period_id = buyer_version.period_id and tx.buyer_entity_id = buyer_version.scope_id
left join elimination using (intercompany_transaction_id)
