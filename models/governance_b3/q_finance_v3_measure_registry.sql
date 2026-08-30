-- depends_on: {{ ref('q_finance_v3_dataset_registry') }}

with additions as (
    select * from (values
        ('QF-M51','QF-D46','Monthly list price','reporting_monthly_list_price_minor','EXACT_VALUE','SELECT_EXACT','price_book_id|reporting_currency','EFFECTIVE_DATE_REQUIRED'),
        ('QF-M52','QF-D52','MRR movement','reporting_mrr_delta_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|product_id|region_id|customer_segment|reporting_currency','NONE'),
        ('QF-M53','QF-D53','Customer billings','reporting_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M54','QF-D53','Invoice tax','tax_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M55','QF-D54','Invoice line amount','reporting_line_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|product_id|legal_entity_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M56','QF-D55','Cash collections','reporting_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M57','QF-D56','Allocated cash','reporting_allocated_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M58','QF-D57','Recognised revenue','reporting_revenue_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','recognition_period|legal_entity_id|product_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M59','QF-D58','Deferred revenue opening','reporting_opening_deferred_revenue_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M60','QF-D58','Deferred revenue new billings','reporting_new_billings_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M61','QF-D58','Deferred revenue recognised','reporting_recognised_revenue_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M62','QF-D58','Deferred revenue closing','reporting_closing_deferred_revenue_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M63','QF-D59','Vendor invoice spend','reporting_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|department_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M64','QF-D60','Vendor invoice line spend','reporting_line_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|department_id|expense_account_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M65','QF-D61','Supplier payments','reporting_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M66','QF-D62','Capital ordered','ordered_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|currency','NONE'),
        ('QF-M67','QF-D64','Capital invoiced','invoice_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','legal_entity_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M68','QF-D65','Gross pay','gross_pay_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|department_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M69','QF-D65','Employer payroll tax','employer_tax_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|department_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M70','QF-D65','Employee benefits','benefits_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|department_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M71','QF-D65','Total payroll cost','reporting_payroll_cost_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|department_id|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M72','QF-D66','Compensation component','reporting_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|legal_entity_id|department_id|compensation_component|reporting_currency','EXACT_REPORTING_VERSION'),
        ('QF-M73','QF-D67','FTE','fte_bps','ADDITIVE_BASIS_POINTS','SUM','snapshot_period|department_id|region_id','NONE'),
        ('QF-M74','QF-D67','Annual salary run rate','reporting_annual_salary_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','snapshot_period|department_id|region_id|reporting_currency','NONE'),
        ('QF-M75','QF-D68','Open accounts receivable','reporting_open_amount_minor','SNAPSHOT_ADDITIVE_SAME_DATE','SUM','snapshot_date|legal_entity_id|reporting_currency','NONE'),
        ('QF-M76','QF-D69','Open accounts payable','reporting_open_amount_minor','SNAPSHOT_ADDITIVE_SAME_DATE','SUM','snapshot_date|legal_entity_id|reporting_currency','NONE'),
        ('QF-M77','QF-D70','Ending MRR','ending_mrr_minor','SNAPSHOT_ADDITIVE_SAME_PERIOD','SUM','period_id|product_id|region_id|customer_segment|currency','NONE'),
        ('QF-M78','QF-D70','Ending ARR','ending_arr_minor','SNAPSHOT_ADDITIVE_SAME_PERIOD','SUM','period_id|product_id|region_id|customer_segment|currency','NONE'),
        ('QF-M79','QF-D71','Beginning MRR','beginning_mrr_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|product_id|region_id|customer_segment|currency','NONE'),
        ('QF-M80','QF-D71','New MRR','new_mrr_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|product_id|region_id|customer_segment|currency','NONE'),
        ('QF-M81','QF-D71','Expansion MRR','expansion_mrr_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|product_id|region_id|customer_segment|currency','NONE'),
        ('QF-M82','QF-D71','Contraction MRR','contraction_mrr_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|product_id|region_id|customer_segment|currency','NONE'),
        ('QF-M83','QF-D71','Churn MRR','churn_mrr_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|product_id|region_id|customer_segment|currency','NONE'),
        ('QF-M84','QF-D71','Ending MRR','ending_mrr_minor','EXACT_OR_ADDITIVE_SAME_GRAIN','SUM','period_id|product_id|region_id|customer_segment|currency','NONE'),
        ('QF-M85','QF-D71','Gross revenue retention','gross_revenue_retention_bps','NON_ADDITIVE_RATIO','RECALCULATE','period_id|product_id|region_id|customer_segment|currency','NONE'),
        ('QF-M86','QF-D71','Net revenue retention','net_revenue_retention_bps','NON_ADDITIVE_RATIO','RECALCULATE','period_id|product_id|region_id|customer_segment|currency','NONE'),
        ('QF-M87','QF-D72','Closing trade working capital','trade_working_capital_minor','EXACT_VALUE','SELECT_EXACT','period_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M88','QF-D72','Closing operating working capital','operating_working_capital_minor','EXACT_VALUE','SELECT_EXACT','period_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M89','QF-D72','DSO','dso_days','NON_ADDITIVE_RATIO','RECALCULATE','period_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M90','QF-D72','DPO','dpo_days','NON_ADDITIVE_RATIO','RECALCULATE','period_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M91','QF-D71','FX remeasurement MRR','fx_remeasurement_mrr_minor','ADDITIVE_GOVERNED_TOTAL','SUM','period_id|product_id|region_id|customer_segment|currency','NONE'),
        ('QF-M92','QF-D72','Closing trade AP','closing_trade_ap_minor','EXACT_VALUE','SELECT_EXACT','period_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M93','QF-D72','Closing capital AP','closing_capital_ap_minor','EXACT_VALUE','SELECT_EXACT','period_id|currency','EXACT_REPORTING_VERSION'),
        ('QF-M94','QF-D72','Closing total AP','closing_ap_minor','EXACT_VALUE','SELECT_EXACT','period_id|currency','EXACT_REPORTING_VERSION')
    ) t(measure_id, dataset_id, measure_name, source_field, measure_class, aggregation, required_grain, reporting_version_policy)
)
select * from {{ ref('q_finance_v2_measure_registry') }}
union all
select * from additions
