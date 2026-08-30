{{ config(tags=['slice_b2']) }}

select 'FIXED_ASSET' subledger_domain, asset_movement_id object_ref, period_id
from {{ ref('fct_fixed_asset_movements') }}
where opening_gross_book_value_minor + gross_addition_minor - gross_disposal_minor <> closing_gross_book_value_minor
   or opening_accumulated_depreciation_minor + depreciation_minor + amortisation_minor
      + impairment_minor - accumulated_depreciation_disposal_minor <> closing_accumulated_depreciation_minor
   or closing_gross_book_value_minor - closing_accumulated_depreciation_minor <> closing_net_book_value_minor
union all
select 'BANKING', bank_account_id, period_id
from {{ ref('fct_bank_reconciliations') }}
where statement_closing_minor + outstanding_receipts_minor - outstanding_disbursements_minor
      + other_reconciling_items_minor <> gl_cash_closing_minor
   or unreconciled_difference_minor <> 0 or reconciliation_status <> 'RECONCILED'
union all
select 'DEBT', debt_instrument_id, period_id
from {{ ref('fct_debt_schedule') }}
where opening_principal_minor + drawdown_minor - principal_repayment_minor <> closing_principal_minor
   or facility_limit_minor - closing_principal_minor <> undrawn_facility_minor
union all
select 'LEASE', lease_contract_id, period_id
from {{ ref('fct_lease_schedule') }}
where opening_liability_minor + liability_addition_minor + interest_accretion_minor
      - cash_payment_minor <> closing_liability_minor
   or cash_payment_minor - interest_accretion_minor <> principal_reduction_minor
   or opening_rou_asset_minor + rou_asset_addition_minor - rou_depreciation_minor
      - rou_impairment_minor <> closing_rou_asset_minor
union all
select 'TAX', jurisdiction_code, period_id
from {{ ref('fct_tax_schedule') }}
where opening_tax_payable_minor + current_tax_expense_minor - cash_tax_paid_minor <> closing_tax_payable_minor
   or opening_deferred_tax_asset_minor + deferred_tax_movement_minor <> closing_deferred_tax_asset_minor
union all
select 'TAX_LOSS', cast(loss_vintage_year as varchar), period_id
from {{ ref('fct_tax_loss_register') }}
where opening_tax_loss_minor + loss_generated_minor - loss_utilised_minor
      - loss_expired_minor <> closing_tax_loss_minor
union all
select 'ACCRUAL', accrual_schedule_id, period_id
from {{ ref('fct_accrual_schedule') }}
where opening_accrual_minor + addition_minor - release_minor <> closing_accrual_minor
union all
select 'PREPAYMENT', prepayment_schedule_id, period_id
from {{ ref('fct_prepayment_schedule') }}
where opening_prepayment_minor + cash_addition_minor - expense_release_minor <> closing_prepayment_minor
union all
select 'INTERCOMPANY', concat_ws('|', seller_entity_id, buyer_entity_id), period_id
from {{ ref('fct_intercompany_balances') }}
where seller_receivable_minor <> buyer_payable_minor
   or confirmed_difference_minor <> 0 or confirmation_status <> 'CONFIRMED'
