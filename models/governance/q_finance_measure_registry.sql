select * from (values
    ('QF-M01', 'QF-D08', 'Debit', 'debit_minor', 'ADDITIVE_GOVERNED_TOTAL', 'SUM', 'period_id|legal_entity_id|currency', 'NONE'),
    ('QF-M02', 'QF-D08', 'Credit', 'credit_minor', 'ADDITIVE_GOVERNED_TOTAL', 'SUM', 'period_id|legal_entity_id|currency', 'NONE'),
    ('QF-M03', 'QF-D08', 'Signed journal movement', 'signed_amount_minor', 'ADDITIVE_GOVERNED_TOTAL', 'SUM', 'period_id|legal_entity_id|currency', 'NONE'),
    ('QF-M04', 'QF-D10', 'Opening balance', 'opening_balance_minor', 'EXACT_OR_ADDITIVE_SAME_GRAIN', 'SUM', 'period_id|scope_id|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION'),
    ('QF-M05', 'QF-D10', 'Debit activity', 'debit_activity_minor', 'ADDITIVE_GOVERNED_TOTAL', 'SUM', 'period_id|scope_id|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION'),
    ('QF-M06', 'QF-D10', 'Credit activity', 'credit_activity_minor', 'ADDITIVE_GOVERNED_TOTAL', 'SUM', 'period_id|scope_id|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION'),
    ('QF-M07', 'QF-D10', 'Closing balance', 'closing_balance_minor', 'EXACT_OR_ADDITIVE_SAME_GRAIN', 'SUM', 'period_id|scope_id|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION'),
    ('QF-M08', 'QF-D11', 'Statement amount', 'amount_minor', 'EXACT_VALUE', 'SELECT_EXACT', 'period_id|scope_id|statement_class|statement_line|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION'),
    ('QF-M09', 'QF-D12', 'Net income', 'net_income_minor', 'EXACT_VALUE', 'SELECT_EXACT', 'period_id|scope_id|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION'),
    ('QF-M10', 'QF-D12', 'Closing retained earnings', 'closing_retained_earnings_minor', 'EXACT_VALUE', 'SELECT_EXACT', 'period_id|scope_id|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION'),
    ('QF-M11', 'QF-D13', 'Operating cash flow', 'operating_cash_flow_minor', 'EXACT_VALUE', 'SELECT_EXACT', 'period_id|scope_id|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION'),
    ('QF-M12', 'QF-D13', 'Investing cash flow', 'investing_cash_flow_minor', 'EXACT_VALUE', 'SELECT_EXACT', 'period_id|scope_id|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION'),
    ('QF-M13', 'QF-D13', 'Financing cash flow', 'financing_cash_flow_minor', 'EXACT_VALUE', 'SELECT_EXACT', 'period_id|scope_id|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION'),
    ('QF-M14', 'QF-D13', 'Closing cash', 'closing_cash_minor', 'EXACT_VALUE', 'SELECT_EXACT', 'period_id|scope_id|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION'),
    ('QF-M15', 'QF-D15', 'Reconciliation difference', 'difference_minor', 'EXACT_VALUE', 'SELECT_EXACT', 'period_id|scope_id|control_id|currency|reporting_version_ref', 'EXACT_REPORTING_VERSION')
) as t(measure_id, dataset_id, measure_name, source_field, measure_class, aggregation, required_grain, reporting_version_policy)
