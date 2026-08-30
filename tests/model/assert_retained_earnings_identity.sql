select period_id, scope_id, reporting_version_ref
from {{ ref('fct_retained_earnings_bridge') }}
where opening_retained_earnings_minor
      + net_income_minor
      - dividends_minor
      + other_equity_movements_minor <> closing_retained_earnings_minor
   or reconciliation_status <> 'RECONCILED'
