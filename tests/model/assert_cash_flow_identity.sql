select period_id, scope_id, reporting_version_ref
from {{ ref('fct_cash_flow_reconciliation') }}
where opening_cash_minor
      + operating_cash_flow_minor
      + investing_cash_flow_minor
      + financing_cash_flow_minor
      + fx_and_other_movement_minor <> closing_cash_minor
   or operating_cash_flow_minor
      + investing_cash_flow_minor
      + financing_cash_flow_minor
      + fx_and_other_movement_minor <> statement_cash_movement_minor
   or unreconciled_difference_minor <> 0
   or reconciliation_status <> 'RECONCILED'
