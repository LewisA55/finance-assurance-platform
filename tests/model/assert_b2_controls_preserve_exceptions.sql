{{ config(tags=['slice_b2']) }}

select test_result_id
from {{ ref('fct_statutory_subledger_controls') }}
where (status = 'PASS' and difference_minor <> 0)
   or (status = 'EXCEPTION' and not (
       subledger_domain = 'PREPAYMENT'
       and observation_type = 'QUARANTINED_DUPLICATE_SOURCE'
   ))
union all
select 'EXPECTED_ONE_QUARANTINED_DUPLICATE'
where (select count(*) from {{ ref('fct_statutory_subledger_controls') }}
       where status = 'EXCEPTION'
         and subledger_domain = 'PREPAYMENT'
         and observation_type = 'QUARANTINED_DUPLICATE_SOURCE') <> 1
