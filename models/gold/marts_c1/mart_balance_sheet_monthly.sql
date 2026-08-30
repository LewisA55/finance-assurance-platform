{{ config(tags=['slice_c']) }}

with statement as (
    select
        period_id,
        scope_id,
        reporting_version_ref,
        currency,
        max(case when statement_line = 'cash' then amount_minor end)::bigint as cash_minor,
        max(case when statement_line = 'accounts_receivable' then amount_minor end)::bigint as accounts_receivable_minor,
        max(case when statement_line = 'intercompany_receivables' then amount_minor end)::bigint as intercompany_receivables_minor,
        max(case when statement_line = 'prepayments' then amount_minor end)::bigint as prepayments_minor,
        max(case when statement_line = 'deferred_tax_asset' then amount_minor end)::bigint as deferred_tax_asset_minor,
        max(case when statement_line = 'inventory' then amount_minor end)::bigint as inventory_minor,
        max(case when statement_line = 'property_plant_equipment' then amount_minor end)::bigint as property_plant_equipment_minor,
        max(case when statement_line = 'accumulated_depreciation' then amount_minor end)::bigint as accumulated_depreciation_minor,
        max(case when statement_line = 'goodwill' then amount_minor end)::bigint as goodwill_minor,
        max(case when statement_line = 'intangible_assets' then amount_minor end)::bigint as intangible_assets_minor,
        max(case when statement_line = 'accumulated_amortisation' then amount_minor end)::bigint as accumulated_amortisation_minor,
        max(case when statement_line = 'right_of_use_assets' then amount_minor end)::bigint as right_of_use_assets_minor,
        max(case when statement_line = 'accumulated_right_of_use_depreciation' then amount_minor end)::bigint as accumulated_right_of_use_depreciation_minor,
        max(case when statement_line = 'accounts_payable' then amount_minor end)::bigint as accounts_payable_minor,
        max(case when statement_line = 'intercompany_payables' then amount_minor end)::bigint as intercompany_payables_minor,
        max(case when statement_line = 'deferred_revenue' then amount_minor end)::bigint as deferred_revenue_minor,
        max(case when statement_line = 'accrued_expenses' then amount_minor end)::bigint as accrued_expenses_minor,
        max(case when statement_line = 'unapplied_cash' then amount_minor end)::bigint as unapplied_cash_minor,
        max(case when statement_line = 'tax_payable' then amount_minor end)::bigint as tax_payable_minor,
        max(case when statement_line = 'long_term_debt' then amount_minor end)::bigint as long_term_debt_minor,
        max(case when statement_line = 'lease_liabilities' then amount_minor end)::bigint as lease_liabilities_minor,
        max(case when statement_line = 'share_capital' then amount_minor end)::bigint as share_capital_minor,
        max(case when statement_line = 'retained_earnings' then amount_minor end)::bigint as retained_earnings_minor,
        max(case when statement_line = 'total_assets' then amount_minor end)::bigint as total_assets_minor,
        max(case when statement_line = 'total_liabilities' then amount_minor end)::bigint as total_liabilities_minor,
        max(case when statement_line = 'total_equity' then amount_minor end)::bigint as total_equity_minor,
        max(case when statement_line = 'total_liabilities_and_equity' then amount_minor end)::bigint as total_liabilities_and_equity_minor,
        max(reliability_status) as reliability_status,
        max(source_package_digest) as source_package_digest
    from {{ ref('fct_statutory_statement_lines') }}
    where statement_class = 'BALANCE_SHEET'
    group by 1, 2, 3, 4
)
select
    md5(concat_ws('|', period_id, scope_id, reporting_version_ref)) as balance_sheet_monthly_hk,
    *,
    (property_plant_equipment_minor + accumulated_depreciation_minor)::bigint as net_property_plant_equipment_minor,
    (intangible_assets_minor + accumulated_amortisation_minor)::bigint as net_intangible_assets_minor,
    (right_of_use_assets_minor + accumulated_right_of_use_depreciation_minor)::bigint as net_right_of_use_assets_minor,
    (accounts_receivable_minor + inventory_minor + prepayments_minor
        - accounts_payable_minor - deferred_revenue_minor - accrued_expenses_minor)::bigint as operating_working_capital_minor,
    (long_term_debt_minor + lease_liabilities_minor - cash_minor)::bigint as net_debt_minor,
    (total_assets_minor - total_liabilities_and_equity_minor)::bigint as balance_sheet_difference_minor,
    'STATUTORY_STATEMENT' as value_authority,
    'EXECUTIVE_BALANCE_SHEET' as reliability_purpose,
    'gold.fct_statutory_statement_lines' as drill_through_relation,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from statement
