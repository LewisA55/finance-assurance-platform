-- depends_on: {{ ref('dim_region') }}
-- depends_on: {{ ref('dim_department') }}
-- depends_on: {{ ref('dim_product') }}
-- depends_on: {{ ref('dim_product_price') }}
-- depends_on: {{ ref('dim_customer') }}
-- depends_on: {{ ref('dim_subscription') }}
-- depends_on: {{ ref('dim_vendor') }}
-- depends_on: {{ ref('dim_employee') }}
-- depends_on: {{ ref('fct_operational_event_links') }}
-- depends_on: {{ ref('fct_subscription_lifecycle_events') }}
-- depends_on: {{ ref('fct_customer_invoices') }}
-- depends_on: {{ ref('fct_customer_invoice_lines') }}
-- depends_on: {{ ref('fct_customer_payments') }}
-- depends_on: {{ ref('fct_payment_allocations') }}
-- depends_on: {{ ref('fct_revenue_recognition') }}
-- depends_on: {{ ref('fct_deferred_revenue_rollforward') }}
-- depends_on: {{ ref('fct_vendor_invoices') }}
-- depends_on: {{ ref('fct_vendor_invoice_lines') }}
-- depends_on: {{ ref('fct_vendor_payments') }}
-- depends_on: {{ ref('fct_capital_purchase_orders') }}
-- depends_on: {{ ref('fct_capital_goods_receipts') }}
-- depends_on: {{ ref('fct_capital_invoices') }}
-- depends_on: {{ ref('fct_payroll_expense_lines') }}
-- depends_on: {{ ref('fct_employee_compensation') }}
-- depends_on: {{ ref('fct_headcount_monthly_snapshot') }}
-- depends_on: {{ ref('fct_ar_ageing_daily') }}
-- depends_on: {{ ref('fct_ap_ageing_daily') }}
-- depends_on: {{ ref('fct_subscription_monthly_state') }}
-- depends_on: {{ ref('fct_saas_monthly_movements') }}
-- depends_on: {{ ref('fct_working_capital_monthly') }}

with inherited as (
    select
        registry_id, 3 as registry_version, dataset_id, dataset_version,
        relation_schema, relation_name, grain, semantic_owner, model_class,
        consumption_class, reliability_purpose, source_data_ref,
        source_package_digest, '{{ var("finance_model_ref") }}' as finance_model_ref,
        money_contract
    from {{ ref('q_finance_v2_dataset_registry') }}
), additions as (
    select * from (values
        ('QF-D43','dim_region','ONE_ROW_PER_REGION','ATLAS','DIMENSION','CORE','REGIONAL_ANALYTICS'),
        ('QF-D44','dim_department','ONE_ROW_PER_DEPARTMENT','ATLAS','DIMENSION','CORE','COST_AND_WORKFORCE_ANALYTICS'),
        ('QF-D45','dim_product','ONE_ROW_PER_PRODUCT','ATLAS','DIMENSION','CORE','PRODUCT_AND_SAAS_ANALYTICS'),
        ('QF-D46','dim_product_price','ONE_ROW_PER_PRODUCT_SEGMENT_REGION_PRICE','ATLAS','DIMENSION','CORE','PRICING_ANALYTICS'),
        ('QF-D47','dim_customer','ONE_ROW_PER_BILLING_CUSTOMER','ATLAS','DIMENSION','CORE','CUSTOMER_ANALYTICS'),
        ('QF-D48','dim_subscription','ONE_ROW_PER_SUBSCRIPTION','ATLAS','DIMENSION','CORE','SAAS_ANALYTICS'),
        ('QF-D49','dim_vendor','ONE_ROW_PER_VENDOR','ATLAS','DIMENSION','CORE','PROCUREMENT_ANALYTICS'),
        ('QF-D50','dim_employee','ONE_ROW_PER_EMPLOYEE','ATLAS','DIMENSION','CORE','WORKFORCE_ANALYTICS'),
        ('QF-D51','fct_operational_event_links','ONE_ROW_PER_POSTING_OPERATIONAL_OBJECT_BUSINESS_EVENT','ATLAS','BRIDGE_FACT','LINEAGE','OPERATIONAL_TO_LEDGER_LINEAGE'),
        ('QF-D52','fct_subscription_lifecycle_events','ONE_ROW_PER_SUBSCRIPTION_LIFECYCLE_EVENT','ATLAS','ATOMIC_FACT','CORE','SAAS_ANALYTICS'),
        ('QF-D53','fct_customer_invoices','ONE_ROW_PER_CUSTOMER_INVOICE','ATLAS','ATOMIC_FACT','CORE','BILLING_AND_AR_ANALYTICS'),
        ('QF-D54','fct_customer_invoice_lines','ONE_ROW_PER_CUSTOMER_INVOICE_LINE','ATLAS','ATOMIC_FACT','CORE','PRODUCT_REVENUE_ANALYTICS'),
        ('QF-D55','fct_customer_payments','ONE_ROW_PER_CASH_RECEIPT','ATLAS','ATOMIC_FACT','CORE','COLLECTIONS_ANALYTICS'),
        ('QF-D56','fct_payment_allocations','ONE_ROW_PER_PAYMENT_TO_INVOICE_ALLOCATION','ATLAS','BRIDGE_FACT','CORE','COLLECTIONS_AND_AR_ANALYTICS'),
        ('QF-D57','fct_revenue_recognition','ONE_ROW_PER_INVOICE_RECOGNITION_MONTH','ATLAS','ATOMIC_FACT','CORE','REVENUE_ANALYTICS'),
        ('QF-D58','fct_deferred_revenue_rollforward','ONE_ROW_PER_PERIOD_CURRENCY','ATLAS','ROLLFORWARD_FACT','CORE','DEFERRED_REVENUE_ANALYTICS'),
        ('QF-D59','fct_vendor_invoices','ONE_ROW_PER_VENDOR_INVOICE','ATLAS','ATOMIC_FACT','CORE','PROCUREMENT_AND_AP_ANALYTICS'),
        ('QF-D60','fct_vendor_invoice_lines','ONE_ROW_PER_VENDOR_INVOICE_LINE','ATLAS','ATOMIC_FACT','CORE','COST_ANALYTICS'),
        ('QF-D61','fct_vendor_payments','ONE_ROW_PER_VENDOR_PAYMENT','ATLAS','ATOMIC_FACT','CORE','SUPPLIER_PAYMENT_ANALYTICS'),
        ('QF-D62','fct_capital_purchase_orders','ONE_ROW_PER_CAPITAL_PURCHASE_ORDER','HERMES','ATOMIC_FACT','CORE','CAPITAL_PROCUREMENT_ANALYTICS'),
        ('QF-D63','fct_capital_goods_receipts','ONE_ROW_PER_CAPITAL_GOODS_RECEIPT','HERMES','ATOMIC_FACT','CORE','CAPITAL_PROCUREMENT_ANALYTICS'),
        ('QF-D64','fct_capital_invoices','ONE_ROW_PER_CAPITAL_SUPPLIER_INVOICE','ATLAS','ATOMIC_FACT','CORE','CAPITAL_PROCUREMENT_ANALYTICS'),
        ('QF-D65','fct_payroll_expense_lines','ONE_ROW_PER_EMPLOYEE_PAYROLL_MONTH','ATLAS','ATOMIC_FACT','CORE','WORKFORCE_COST_ANALYTICS'),
        ('QF-D66','fct_employee_compensation','ONE_ROW_PER_EMPLOYEE_PERIOD_COMPENSATION_COMPONENT','ATLAS','ATOMIC_FACT','CORE','COMPENSATION_ANALYTICS'),
        ('QF-D67','fct_headcount_monthly_snapshot','ONE_ROW_PER_EMPLOYEE_MONTH_END','ATLAS','SNAPSHOT_FACT','CORE','WORKFORCE_ANALYTICS'),
        ('QF-D68','fct_ar_ageing_daily','ONE_ROW_PER_OPEN_INVOICE_DAILY_SNAPSHOT','ATLAS','SNAPSHOT_FACT','CORE','DAILY_AR_ANALYTICS'),
        ('QF-D69','fct_ap_ageing_daily','ONE_ROW_PER_OPEN_VENDOR_INVOICE_DAILY_SNAPSHOT','ATLAS','SNAPSHOT_FACT','CORE','DAILY_AP_ANALYTICS'),
        ('QF-D70','fct_subscription_monthly_state','ONE_ROW_PER_SUBSCRIPTION_MONTH_END','ATLAS','SNAPSHOT_FACT','CORE','SAAS_ANALYTICS'),
        ('QF-D71','fct_saas_monthly_movements','ONE_ROW_PER_PERIOD_PRODUCT_REGION_SEGMENT_CURRENCY','ATLAS','DERIVED_FACT','CORE','SAAS_ANALYTICS'),
        ('QF-D72','fct_working_capital_monthly','ONE_ROW_PER_PERIOD_REPORTING_CURRENCY','ATLAS','DERIVED_FACT','CORE','WORKING_CAPITAL_ANALYTICS')
    ) t(dataset_id, relation_name, grain, semantic_owner, model_class, consumption_class, reliability_purpose)
)
select * from inherited
union all
select
    'Q-FINANCE', 3, dataset_id, 1, 'gold', relation_name, grain,
    semantic_owner, model_class, consumption_class, reliability_purpose,
    '{{ var("a24_data_ref") }}', '{{ var("a24_package_digest") }}',
    '{{ var("finance_model_ref") }}', 'INTEGER_MINOR_UNITS_PLUS_CURRENCY'
from additions
