with additions as (
    select * from (values
        ('QF-D43','dim_region','stg_reference__regions','reference__regions','STRICT_TYPE_AND_CONFORM'),
        ('QF-D44','dim_department','stg_reference__departments','reference__departments','STRICT_TYPE_AND_CONFORM'),
        ('QF-D45','dim_product','stg_reference__products','reference__products','STRICT_TYPE_AND_CONFORM'),
        ('QF-D46','dim_product_price','stg_reference__product_price_book|dim_product|dim_region','reference__product_price_book','TYPE_AND_CONFORM_PRODUCT_REGION_PRICE'),
        ('QF-D47','dim_customer','stg_billing__customers|dim_region','billing__customers','TYPE_AND_CONFORM_CUSTOMER_REGION'),
        ('QF-D48','dim_subscription','stg_billing__subscriptions|dim_customer|dim_product','billing__subscriptions','TYPE_AND_CONFORM_CUSTOMER_PRODUCT'),
        ('QF-D49','dim_vendor','stg_procurement__vendors|dim_region','procurement__vendors','TYPE_AND_CONFORM_VENDOR_REGION'),
        ('QF-D50','dim_employee','stg_hris__employees|dim_department|dim_region','hris__employees','TYPE_AND_CONFORM_ORGANISATION'),
        ('QF-D51','fct_operational_event_links','fct_business_events|fct_gl_journal_lines|dim_reporting_version|stg_procurement__capital_invoices','events__business_events|accounting__source_gl_journal_lines|procurement__capital_invoices','RESOLVE_POSTING_OBJECT_TO_CAUSAL_EVENT_LEDGER_AND_CLOSE'),
        ('QF-D52','fct_subscription_lifecycle_events','stg_billing__subscription_events|dim_subscription','billing__subscription_events','TYPE_CLASSIFY_AND_CONFORM_SAAS_MOVEMENT'),
        ('QF-D53','fct_customer_invoices','stg_billing__invoices|dim_customer|dim_subscription|fct_operational_event_links','billing__invoices','TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D54','fct_customer_invoice_lines','stg_billing__invoice_lines|fct_customer_invoices','billing__invoice_lines|billing__invoices','TYPE_AND_INHERIT_PARENT_B1_LINEAGE'),
        ('QF-D55','fct_customer_payments','stg_billing__payments|dim_customer|fct_operational_event_links','billing__payments','TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D56','fct_payment_allocations','stg_billing__payment_allocations|fct_customer_invoices|fct_customer_payments','billing__payment_allocations','TYPE_AND_RESOLVE_PAYMENT_INVOICE_BRIDGE'),
        ('QF-D57','fct_revenue_recognition','stg_revenue__revenue_recognition_schedule|fct_customer_invoices|dim_subscription|fct_operational_event_links','revenue__revenue_recognition_schedule','TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D58','fct_deferred_revenue_rollforward','stg_revenue__deferred_revenue_rollforward|dim_reporting_version','revenue__deferred_revenue_rollforward','TYPE_AND_BIND_ROLLFORWARD_TO_GROUP_CLOSE'),
        ('QF-D59','fct_vendor_invoices','stg_procurement__vendor_invoices|dim_vendor|dim_department|dim_gl_account|fct_operational_event_links','procurement__vendor_invoices','TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D60','fct_vendor_invoice_lines','stg_procurement__vendor_invoice_lines|fct_vendor_invoices','procurement__vendor_invoice_lines|procurement__vendor_invoices','TYPE_AND_INHERIT_PARENT_B1_LINEAGE'),
        ('QF-D61','fct_vendor_payments','stg_procurement__vendor_payments|fct_vendor_invoices|fct_operational_event_links','procurement__vendor_payments','TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D62','fct_capital_purchase_orders','stg_procurement__capital_purchase_orders|dim_vendor|dim_legal_entity','procurement__capital_purchase_orders','TYPE_AND_CONFORM_CAPITAL_ORDER'),
        ('QF-D63','fct_capital_goods_receipts','stg_procurement__capital_goods_receipts|fct_capital_purchase_orders','procurement__capital_goods_receipts|procurement__capital_purchase_orders','TYPE_AND_RESOLVE_ORDER_RECEIPT'),
        ('QF-D64','fct_capital_invoices','stg_procurement__capital_invoices|fct_capital_purchase_orders|fct_capital_goods_receipts|fct_operational_event_links|dim_fixed_asset','procurement__capital_invoices','RESOLVE_THREE_WAY_MATCH_EVENT_LEDGER_AND_ASSET'),
        ('QF-D65','fct_payroll_expense_lines','stg_workforce__payroll_expense_lines|dim_employee|dim_department|fct_operational_event_links','workforce__payroll_expense_lines','TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D66','fct_employee_compensation','stg_workforce__employee_compensation|fct_payroll_expense_lines','workforce__employee_compensation|workforce__payroll_expense_lines','TYPE_AND_INHERIT_PAYROLL_B1_LINEAGE'),
        ('QF-D67','fct_headcount_monthly_snapshot','stg_hris__headcount_snapshot|dim_employee|dim_department|dim_region','hris__headcount_snapshot','TYPE_AND_CONFORM_MONTHLY_WORKFORCE_STATE'),
        ('QF-D68','fct_ar_ageing_daily','stg_billing__ar_ageing_snapshot|fct_customer_invoices','billing__ar_ageing_snapshot|billing__invoices','TYPE_AND_RESOLVE_DAILY_OPEN_INVOICE_STATE'),
        ('QF-D69','fct_ap_ageing_daily','stg_procurement__ap_ageing_snapshot|fct_vendor_invoices','procurement__ap_ageing_snapshot|procurement__vendor_invoices','TYPE_AND_RESOLVE_DAILY_OPEN_VENDOR_INVOICE_STATE'),
        ('QF-D70','fct_subscription_monthly_state','dim_subscription|dim_period|stg_billing__subscription_events','billing__subscriptions|billing__subscription_events','TEMPORAL_ASOF_REPLAY_FROM_LIFECYCLE_EVENTS'),
        ('QF-D71','fct_saas_monthly_movements','fct_subscription_monthly_state|fct_subscription_lifecycle_events','billing__subscriptions|billing__subscription_events','DERIVE_MONTHLY_MOVEMENT_AND_RETENTION_STATE'),
        ('QF-D72','fct_working_capital_monthly','fct_ar_ageing_daily|fct_ap_ageing_daily|fct_customer_invoices|fct_customer_payments|fct_vendor_invoices|fct_vendor_payments|fct_deferred_revenue_rollforward|dim_reporting_version','billing__ar_ageing_snapshot|procurement__ap_ageing_snapshot|billing__invoices|billing__payments|procurement__vendor_invoices|procurement__vendor_payments|revenue__deferred_revenue_rollforward','DERIVE_MONTH_END_WORKING_CAPITAL_AND_BIND_TO_GROUP_CLOSE')
    ) t(dataset_id, gold_model, direct_dependencies, a24_bronze_sources, transformation_class)
)
select * from {{ ref('q_finance_v2_lineage_registry') }}
union all
select * from additions
