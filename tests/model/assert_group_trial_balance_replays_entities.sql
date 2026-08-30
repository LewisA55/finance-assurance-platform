with entity_tb as (
    select period_id, account_id, currency,
           sum(debit_activity_minor) as debit_minor,
           sum(credit_activity_minor) as credit_minor
    from {{ ref('fct_statutory_trial_balance') }}
    where scope_id <> 'NEXUS-GROUP'
    group by 1, 2, 3
),
eliminations as (
    select period_id, account_id, currency,
           sum(debit_minor) as debit_minor,
           sum(credit_minor) as credit_minor
    from {{ ref('fct_elimination_journal_lines') }}
    group by 1, 2, 3
)
select group_tb.period_id, group_tb.account_id
from {{ ref('fct_statutory_trial_balance') }} as group_tb
left join entity_tb
    on group_tb.period_id = entity_tb.period_id
   and group_tb.account_id = entity_tb.account_id
   and group_tb.currency = entity_tb.currency
left join eliminations
    on group_tb.period_id = eliminations.period_id
   and group_tb.account_id = eliminations.account_id
   and group_tb.currency = eliminations.currency
where group_tb.scope_id = 'NEXUS-GROUP'
  and (
      group_tb.debit_activity_minor <> coalesce(entity_tb.debit_minor, 0)
      or group_tb.credit_activity_minor <> coalesce(entity_tb.credit_minor, 0)
      or group_tb.elimination_debit_minor <> coalesce(eliminations.debit_minor, 0)
      or group_tb.elimination_credit_minor <> coalesce(eliminations.credit_minor, 0)
  )
