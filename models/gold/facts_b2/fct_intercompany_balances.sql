{{ config(tags=['slice_b2']) }}

select
    md5(concat_ws('|', balance.period_id, balance.seller_entity_id,
                  balance.buyer_entity_id)) as intercompany_balance_hk,
    balance.* exclude (_ingested_at, _source_file, _source_file_sha256),
    seller.reporting_version_ref as seller_reporting_version_ref,
    buyer.reporting_version_ref as buyer_reporting_version_ref,
    seller.close_status as seller_close_status,
    buyer.close_status as buyer_close_status,
    case
      when seller.reliability_status = 'RELIABLE_FOR_STATUTORY_ACTUALS'
       and buyer.reliability_status = 'RELIABLE_FOR_STATUTORY_ACTUALS'
      then 'RELIABLE_FOR_STATUTORY_ACTUALS'
      else 'NOT_RELIABLE_FOR_STATUTORY_ACTUALS'
    end as reliability_status,
    'INTERCOMPANY_ANALYTICS' as reliability_purpose,
    seller.source_package_digest
from {{ ref('stg_intercompany__intercompany_balances') }} balance
inner join {{ ref('dim_reporting_version') }} seller
  on balance.period_id = seller.period_id and balance.seller_entity_id = seller.scope_id
inner join {{ ref('dim_reporting_version') }} buyer
  on balance.period_id = buyer.period_id and balance.buyer_entity_id = buyer.scope_id
