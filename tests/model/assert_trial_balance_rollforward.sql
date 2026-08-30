select period_id, scope_id, account_id, reporting_version_ref
from {{ ref('fct_statutory_trial_balance') }}
where opening_balance_minor
      + debit_activity_minor
      - credit_activity_minor
      + elimination_debit_minor
      - elimination_credit_minor <> closing_balance_minor
   or close_status <> 'HARD_CLOSED'
