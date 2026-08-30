-- depends_on: {{ ref('q_finance_v2_dataset_registry') }}

with additions as (
    select * from (values
        ('QF-M16','QF-D18','Asset cost','cost_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','asset_id|currency','NONE'),
        ('QF-M17','QF-D23','Gross additions','gross_addition_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M18','QF-D23','Depreciation','depreciation_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M19','QF-D23','Amortisation','amortisation_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M20','QF-D23','Closing net book value','closing_net_book_value_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M21','QF-D25','Bank transaction amount','amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|bank_account_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M22','QF-D27','Statement closing cash','statement_closing_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|bank_account_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M23','QF-D27','GL cash closing','gl_cash_closing_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|bank_account_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M24','QF-D27','Bank unreconciled difference','unreconciled_difference_minor','EXACT_VALUE','SELECT_EXACT','period_id|bank_account_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M25','QF-D28','Debt drawdown','drawdown_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|debt_instrument_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M26','QF-D28','Principal repayment','principal_repayment_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|debt_instrument_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M27','QF-D28','Cash interest','cash_interest_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|debt_instrument_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M28','QF-D28','Closing principal','closing_principal_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|debt_instrument_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M29','QF-D28','Undrawn facility','undrawn_facility_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|debt_instrument_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M30','QF-D30','Lease cash payment','cash_payment_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|lease_contract_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M31','QF-D30','Lease interest','interest_accretion_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|lease_contract_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M32','QF-D30','Closing lease liability','closing_liability_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|lease_contract_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M33','QF-D30','ROU depreciation','rou_depreciation_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|lease_contract_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M34','QF-D30','Closing ROU asset','closing_rou_asset_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|lease_contract_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M35','QF-D32','Taxable profit','taxable_profit_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|jurisdiction_code|currency','EXACT_REPORTING_VERSION'),
        ('QF-M36','QF-D32','Current tax expense','current_tax_expense_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|jurisdiction_code|currency','EXACT_REPORTING_VERSION'),
        ('QF-M37','QF-D32','Cash tax paid','cash_tax_paid_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|jurisdiction_code|currency','EXACT_REPORTING_VERSION'),
        ('QF-M38','QF-D32','Closing tax payable','closing_tax_payable_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|legal_entity_id|jurisdiction_code|currency','EXACT_REPORTING_VERSION'),
        ('QF-M39','QF-D32','Closing deferred tax asset','closing_deferred_tax_asset_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|legal_entity_id|jurisdiction_code|currency','EXACT_REPORTING_VERSION'),
        ('QF-M40','QF-D33','Closing tax losses','closing_tax_loss_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|legal_entity_id|jurisdiction_code|loss_vintage_year|currency','EXACT_REPORTING_VERSION'),
        ('QF-M41','QF-D34','Equity movement','amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|equity_component|currency','EXACT_REPORTING_VERSION'),
        ('QF-M42','QF-D36','Accrual addition','addition_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M43','QF-D36','Accrual release','release_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M44','QF-D36','Closing accrual','closing_accrual_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M45','QF-D38','Prepayment cash addition','cash_addition_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M46','QF-D38','Prepayment expense release','expense_release_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M47','QF-D38','Closing prepayment','closing_prepayment_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M48','QF-D39','Intercompany transaction amount','amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|seller_entity_id|buyer_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M49','QF-D40','Intercompany confirmed balance','seller_receivable_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|seller_entity_id|buyer_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M50','QF-D41','Subledger control difference','difference_minor','EXACT_VALUE','SELECT_EXACT','test_result_id|currency','EXACT_REPORTING_VERSION')
    ) t(measure_id, dataset_id, measure_name, source_field, measure_class, aggregation, required_grain, reporting_version_policy)
)
select * from {{ ref('q_finance_measure_registry') }}
union all
select * from additions
