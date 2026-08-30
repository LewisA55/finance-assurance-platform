with gl as (
    select period_id, legal_entity_id, account_id, currency,
           sum(debit_minor) as debit_minor,
           sum(credit_minor) as credit_minor
    from {{ ref('fct_gl_journal_lines') }}
    group by 1, 2, 3, 4
)
select tb.period_id, tb.scope_id, tb.account_id
from {{ ref('fct_statutory_trial_balance') }} as tb
left join gl
    on tb.period_id = gl.period_id
   and tb.legal_entity_id = gl.legal_entity_id
   and tb.account_id = gl.account_id
   and tb.currency = gl.currency
where tb.scope_id <> 'NEXUS-GROUP'
  and (
      tb.debit_activity_minor <> coalesce(gl.debit_minor, 0)
      or tb.credit_activity_minor <> coalesce(gl.credit_minor, 0)
      or tb.elimination_debit_minor <> 0
      or tb.elimination_credit_minor <> 0
  )
