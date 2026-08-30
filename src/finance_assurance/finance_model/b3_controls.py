"""Independent executable controls for the Q-FINANCE Slice B3 successor."""


B3_CONTROL_QUERIES = (
    (
        "B3_GOLD_POPULATION_RECONCILES_TO_SILVER",
        """
        WITH populations AS (
            SELECT (SELECT COUNT(*) FROM gold.dim_region) actual_rows,
                   (SELECT COUNT(*) FROM silver.stg_reference__regions) expected_rows
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_department),
                             (SELECT COUNT(*) FROM silver.stg_reference__departments)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_product),
                             (SELECT COUNT(*) FROM silver.stg_reference__products)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_product_price),
                             (SELECT COUNT(*) FROM silver.stg_reference__product_price_book)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_customer),
                             (SELECT COUNT(*) FROM silver.stg_billing__customers)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_subscription),
                             (SELECT COUNT(*) FROM silver.stg_billing__subscriptions)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_vendor),
                             (SELECT COUNT(*) FROM silver.stg_procurement__vendors)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_employee),
                             (SELECT COUNT(*) FROM silver.stg_hris__employees)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_subscription_lifecycle_events),
                             (SELECT COUNT(*) FROM silver.stg_billing__subscription_events)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_customer_invoices),
                             (SELECT COUNT(*) FROM silver.stg_billing__invoices)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_customer_invoice_lines),
                             (SELECT COUNT(*) FROM silver.stg_billing__invoice_lines)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_customer_payments),
                             (SELECT COUNT(*) FROM silver.stg_billing__payments)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_payment_allocations),
                             (SELECT COUNT(*) FROM silver.stg_billing__payment_allocations)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_ar_ageing_daily),
                             (SELECT COUNT(*) FROM silver.stg_billing__ar_ageing_snapshot)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_revenue_recognition),
                             (SELECT COUNT(*) FROM silver.stg_revenue__revenue_recognition_schedule)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_deferred_revenue_rollforward),
                             (SELECT COUNT(*) FROM silver.stg_revenue__deferred_revenue_rollforward)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_vendor_invoices),
                             (SELECT COUNT(*) FROM silver.stg_procurement__vendor_invoices)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_vendor_invoice_lines),
                             (SELECT COUNT(*) FROM silver.stg_procurement__vendor_invoice_lines)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_vendor_payments),
                             (SELECT COUNT(*) FROM silver.stg_procurement__vendor_payments)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_ap_ageing_daily),
                             (SELECT COUNT(*) FROM silver.stg_procurement__ap_ageing_snapshot)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_capital_purchase_orders),
                             (SELECT COUNT(*) FROM silver.stg_procurement__capital_purchase_orders)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_capital_goods_receipts),
                             (SELECT COUNT(*) FROM silver.stg_procurement__capital_goods_receipts)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_capital_invoices),
                             (SELECT COUNT(*) FROM silver.stg_procurement__capital_invoices)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_payroll_expense_lines),
                             (SELECT COUNT(*) FROM silver.stg_workforce__payroll_expense_lines)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_employee_compensation),
                             (SELECT COUNT(*) FROM silver.stg_workforce__employee_compensation)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_headcount_monthly_snapshot),
                             (SELECT COUNT(*) FROM silver.stg_hris__headcount_snapshot)
        )
        SELECT COUNT(*) FROM populations WHERE actual_rows <> expected_rows
        """,
    ),
    (
        "B3_EVENT_BRIDGE_COVERS_POSTING_POPULATION",
        """
        WITH expected AS (
            SELECT business_event_ref
            FROM gold.fct_business_events
            WHERE event_type IN (
                'CUSTOMER_INVOICE_ISSUED', 'CASH_RECEIPT_RECORDED',
                'SUBSCRIPTION_REVENUE_RECOGNISED', 'VENDOR_INVOICE_APPROVED',
                'VENDOR_PAYMENT_SETTLED', 'PAYROLL_COST_INCURRED',
                'CAPITAL_ASSET_INVOICE_APPROVED', 'CAPITAL_ASSET_INVOICE_PAID'
            )
        ), failures AS (
            SELECT expected.business_event_ref
            FROM expected LEFT JOIN gold.fct_operational_event_links link USING (business_event_ref)
            WHERE link.business_event_ref IS NULL
            UNION ALL
            SELECT link.business_event_ref
            FROM gold.fct_operational_event_links link
            LEFT JOIN expected USING (business_event_ref)
            WHERE expected.business_event_ref IS NULL
               OR link.object_ref IS NULL OR link.record_semantic_hash IS NULL
               OR link.gl_journal_line_count = 0
               OR link.reporting_version_ref IS NULL
               OR link.close_status <> 'HARD_CLOSED'
               OR link.reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
        ) SELECT COUNT(*) FROM failures
        """,
    ),
    (
        "B3_EVENT_BRIDGE_REPLAYS_B1_GL",
        """
        WITH gl AS (
            SELECT business_event_ref, legal_entity_id, COUNT(*) line_count,
                   SUM(debit_minor) debit_minor, SUM(credit_minor) credit_minor
            FROM gold.fct_gl_journal_lines GROUP BY 1, 2
        )
        SELECT COUNT(*)
        FROM gold.fct_operational_event_links link
        INNER JOIN gl USING (business_event_ref, legal_entity_id)
        INNER JOIN gold.fct_business_events event USING (business_event_ref, legal_entity_id)
        WHERE link.gl_journal_line_count <> gl.line_count
           OR link.gl_debit_minor <> gl.debit_minor
           OR link.gl_credit_minor <> gl.credit_minor
           OR link.gl_debit_minor <> event.reporting_amount_minor
           OR link.gl_debit_minor <> link.gl_credit_minor
        """,
    ),
    (
        "B3_POSTING_FACTS_BIND_TO_B1_CLOSE",
        """
        SELECT COUNT(*) FROM (
            SELECT invoice_id object_ref, reporting_version_ref, close_status, reliability_status FROM gold.fct_customer_invoices
            UNION ALL SELECT invoice_line_id, reporting_version_ref, close_status, reliability_status FROM gold.fct_customer_invoice_lines
            UNION ALL SELECT payment_id, reporting_version_ref, close_status, reliability_status FROM gold.fct_customer_payments
            UNION ALL SELECT allocation_id, reporting_version_ref, close_status, reliability_status FROM gold.fct_payment_allocations
            UNION ALL SELECT schedule_id, reporting_version_ref, close_status, reliability_status FROM gold.fct_revenue_recognition
            UNION ALL SELECT vendor_invoice_id, reporting_version_ref, close_status, reliability_status FROM gold.fct_vendor_invoices
            UNION ALL SELECT vendor_invoice_line_id, reporting_version_ref, close_status, reliability_status FROM gold.fct_vendor_invoice_lines
            UNION ALL SELECT vendor_payment_id, reporting_version_ref, close_status, reliability_status FROM gold.fct_vendor_payments
            UNION ALL SELECT payroll_line_id, reporting_version_ref, close_status, reliability_status FROM gold.fct_payroll_expense_lines
            UNION ALL SELECT compensation_line_id, reporting_version_ref, close_status, reliability_status FROM gold.fct_employee_compensation
        ) WHERE reporting_version_ref IS NULL OR close_status <> 'HARD_CLOSED'
             OR reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
        """,
    ),
    (
        "B3_BILLING_LINES_RECONCILE",
        """
        WITH lines AS (
            SELECT invoice_id, SUM(line_amount_minor) line_minor,
                   SUM(reporting_line_amount_minor) reporting_line_minor
            FROM gold.fct_customer_invoice_lines GROUP BY 1
        )
        SELECT COUNT(*) FROM lines
        INNER JOIN gold.fct_customer_invoices invoice USING (invoice_id)
        WHERE lines.line_minor <> invoice.invoice_amount_minor
           OR lines.reporting_line_minor <> invoice.reporting_amount_minor
        """,
    ),
    (
        "B3_CASH_ALLOCATIONS_RECONCILE",
        """
        WITH by_payment AS (
            SELECT payment_id, SUM(allocated_amount_minor) allocated_minor,
                   SUM(reporting_allocated_amount_minor) reporting_allocated_minor
            FROM gold.fct_payment_allocations GROUP BY 1
        ), by_invoice AS (
            SELECT invoice_id, SUM(allocated_amount_minor) allocated_minor
            FROM gold.fct_payment_allocations GROUP BY 1
        ), failures AS (
            SELECT payment.payment_id object_ref
            FROM by_payment allocation
            INNER JOIN gold.fct_customer_payments payment USING (payment_id)
            WHERE allocation.allocated_minor <> payment.payment_amount_minor
               OR allocation.reporting_allocated_minor <> payment.reporting_amount_minor
            UNION ALL
            SELECT invoice.invoice_id
            FROM by_invoice allocation
            INNER JOIN gold.fct_customer_invoices invoice USING (invoice_id)
            WHERE allocation.allocated_minor <> invoice.invoice_amount_minor + invoice.tax_amount_minor
        ) SELECT COUNT(*) FROM failures
        """,
    ),
    (
        "B3_REVENUE_SCHEDULE_IS_COMPLETE_TO_CLOSED_HORIZON",
        """
        WITH recognised AS (
            SELECT invoice_id, SUM(revenue_amount_minor) recognised_minor,
                   MAX(recognition_date) final_recognition_date
            FROM gold.fct_revenue_recognition
            WHERE recognition_status = 'RECOGNISED'
            GROUP BY 1
        ), horizon AS (
            SELECT MAX(recognition_date) horizon_date FROM gold.fct_revenue_recognition
        )
        SELECT COUNT(*)
        FROM recognised
        INNER JOIN gold.fct_customer_invoices invoice USING (invoice_id)
        CROSS JOIN horizon
        WHERE recognised.recognised_minor > invoice.invoice_amount_minor
           OR (invoice.service_period_end <= horizon.horizon_date
               AND recognised.recognised_minor <> invoice.invoice_amount_minor)
        """,
    ),
    (
        "B3_DEFERRED_REVENUE_ROLLFORWARD",
        """
        SELECT COUNT(*) FROM (
            SELECT period_id, currency,
                   opening_deferred_revenue_minor opening_minor,
                   LAG(closing_deferred_revenue_minor) OVER (PARTITION BY currency ORDER BY period_id) prior_closing,
                   opening_deferred_revenue_minor + new_billings_minor - recognised_revenue_minor calculated_closing,
                   closing_deferred_revenue_minor,
                   reporting_opening_deferred_revenue_minor + reporting_new_billings_minor
                       - reporting_recognised_revenue_minor calculated_reporting_closing,
                   reporting_closing_deferred_revenue_minor
            FROM gold.fct_deferred_revenue_rollforward
        )
        WHERE calculated_closing <> closing_deferred_revenue_minor
           OR calculated_reporting_closing <> reporting_closing_deferred_revenue_minor
           OR (prior_closing IS NOT NULL AND opening_minor <> prior_closing)
        """,
    ),
    (
        "B3_PROCUREMENT_AND_PAYMENTS_RECONCILE",
        """
        WITH lines AS (
            SELECT vendor_invoice_id, SUM(line_amount_minor) line_minor,
                   SUM(reporting_line_amount_minor) reporting_line_minor
            FROM gold.fct_vendor_invoice_lines GROUP BY 1
        ), payments AS (
            SELECT vendor_invoice_id, SUM(payment_amount_minor) paid_minor
            FROM gold.fct_vendor_payments GROUP BY 1
        ), failures AS (
            SELECT invoice.vendor_invoice_id object_ref
            FROM gold.fct_vendor_invoices invoice
            INNER JOIN lines USING (vendor_invoice_id)
            WHERE invoice.invoice_amount_minor <> lines.line_minor
               OR invoice.reporting_amount_minor <> lines.reporting_line_minor
            UNION ALL
            SELECT invoice.vendor_invoice_id
            FROM gold.fct_vendor_invoices invoice
            INNER JOIN payments USING (vendor_invoice_id)
            WHERE payments.paid_minor <> invoice.invoice_amount_minor + invoice.tax_amount_minor
        ) SELECT COUNT(*) FROM failures
        """,
    ),
    (
        "B3_CAPITAL_PROCUREMENT_PRESERVES_POSTING_BOUNDARY",
        """
        SELECT COUNT(*) FROM (
            SELECT invoice.capital_invoice_id object_ref
            FROM gold.fct_capital_invoices invoice
            LEFT JOIN gold.fct_capital_purchase_orders po USING (capital_purchase_order_id, legal_entity_id, vendor_id)
            LEFT JOIN gold.fct_capital_goods_receipts receipt USING (capital_goods_receipt_id, capital_purchase_order_id, legal_entity_id)
            WHERE po.capital_purchase_order_id IS NULL OR receipt.capital_goods_receipt_id IS NULL
               OR (invoice.is_posted_to_gl AND (
                    invoice.business_event_refs IS NULL OR invoice.gl_journal_line_count = 0
                    OR invoice.asset_id IS NULL OR invoice.close_status <> 'HARD_CLOSED'
               ))
               OR (NOT invoice.is_posted_to_gl AND (
                    invoice.business_event_refs IS NOT NULL OR invoice.gl_journal_line_count <> 0
                    OR invoice.reliability_status <> 'SOURCE_RECORD_UNPOSTED'
               ))
            UNION ALL SELECT 'UNPOSTED_COUNT'
            WHERE (SELECT COUNT(*) FROM gold.fct_capital_invoices WHERE NOT is_posted_to_gl) <> 1
        )
        """,
    ),
    (
        "B3_PAYROLL_COMPONENTS_RECONCILE",
        """
        WITH components AS (
            SELECT period_id, employee_id, SUM(amount_minor) amount_minor,
                   SUM(reporting_amount_minor) reporting_amount_minor
            FROM gold.fct_employee_compensation GROUP BY 1, 2
        )
        SELECT COUNT(*)
        FROM components
        INNER JOIN gold.fct_payroll_expense_lines payroll USING (period_id, employee_id)
        WHERE components.amount_minor <> payroll.total_payroll_cost_minor
           OR components.reporting_amount_minor <> payroll.reporting_payroll_cost_minor
           OR payroll.gross_pay_minor + payroll.employer_tax_minor + payroll.benefits_minor
              <> payroll.total_payroll_cost_minor
        """,
    ),
    (
        "B3_SAAS_STATE_AND_MOVEMENT_REPLAY",
        """
        SELECT COUNT(*) FROM (
            SELECT state.subscription_monthly_state_hk object_ref
            FROM gold.fct_subscription_monthly_state state
            LEFT JOIN gold.fct_subscription_lifecycle_events event
              ON state.latest_subscription_event_id = event.subscription_event_id
            WHERE event.subscription_event_id IS NULL
               OR state.ending_mrr_minor <> event.reporting_new_mrr_minor
               OR state.ending_arr_minor <> 12 * state.ending_mrr_minor
               OR state.is_active_subscription <> (state.ending_mrr_minor > 0)
            UNION ALL
            SELECT movement.saas_monthly_movement_hk
            FROM gold.fct_saas_monthly_movements movement
            WHERE movement.beginning_mrr_minor + movement.new_mrr_minor
                  + movement.expansion_mrr_minor + movement.contraction_mrr_minor
                  + movement.churn_mrr_minor + movement.fx_remeasurement_mrr_minor
                  <> movement.ending_mrr_minor
               OR movement.ending_arr_minor <> 12 * movement.ending_mrr_minor
        )
        """,
    ),
    (
        "B3_WORKING_CAPITAL_RECONCILES_TO_B1",
        """
        WITH balances AS (
            SELECT period_id,
                   MAX(CASE WHEN account_id = '1100' THEN closing_balance_minor END) ar_minor,
                   -MAX(CASE WHEN account_id = '2000' THEN closing_balance_minor END) ap_minor,
                   -MAX(CASE WHEN account_id = '2100' THEN closing_balance_minor END) deferred_minor
            FROM gold.fct_statutory_trial_balance
            WHERE scope_id = 'NEXUS-GROUP' AND account_id IN ('1100', '2000', '2100')
            GROUP BY 1
        )
        SELECT COUNT(*)
        FROM gold.fct_working_capital_monthly working
        INNER JOIN balances USING (period_id)
        WHERE working.closing_ar_minor <> balances.ar_minor
           OR working.closing_ap_minor <> balances.ap_minor
           OR working.closing_deferred_revenue_minor <> balances.deferred_minor
           OR working.closing_ap_minor <> working.closing_trade_ap_minor + working.closing_capital_ap_minor
           OR working.trade_working_capital_minor <> working.closing_ar_minor - working.closing_trade_ap_minor
           OR working.operating_working_capital_minor <>
              working.closing_ar_minor - working.closing_trade_ap_minor - working.closing_deferred_revenue_minor
           OR working.reporting_version_ref IS NULL OR working.close_status <> 'HARD_CLOSED'
        """,
    ),
    (
        "B3_DIMENSION_RELATIONSHIPS_RESOLVE",
        """
        SELECT COUNT(*) FROM (
            SELECT subscription.subscription_id object_ref
            FROM gold.dim_subscription subscription
            LEFT JOIN gold.dim_customer customer USING (customer_id)
            LEFT JOIN gold.dim_product product USING (product_id)
            WHERE customer.customer_id IS NULL OR product.product_id IS NULL
            UNION ALL
            SELECT invoice.invoice_id
            FROM gold.fct_customer_invoices invoice
            LEFT JOIN gold.dim_customer customer USING (customer_id)
            LEFT JOIN gold.dim_subscription subscription USING (subscription_id)
            WHERE customer.customer_id IS NULL OR subscription.subscription_id IS NULL
            UNION ALL
            SELECT invoice.vendor_invoice_id
            FROM gold.fct_vendor_invoices invoice
            LEFT JOIN gold.dim_vendor vendor USING (vendor_id)
            LEFT JOIN gold.dim_department department USING (department_id)
            WHERE vendor.vendor_id IS NULL OR department.department_id IS NULL
            UNION ALL
            SELECT payroll.payroll_line_id
            FROM gold.fct_payroll_expense_lines payroll
            LEFT JOIN gold.dim_employee employee USING (employee_id)
            WHERE employee.employee_id IS NULL
        )
        """,
    ),
    (
        "Q_FINANCE_V3_REGISTRY_CLOSURE",
        """
        SELECT COUNT(*) FROM (
            SELECT registry.dataset_id
            FROM governance.q_finance_v3_dataset_registry registry
            LEFT JOIN information_schema.tables physical
              ON registry.relation_schema = physical.table_schema
             AND registry.relation_name = physical.table_name
            WHERE physical.table_name IS NULL
            UNION ALL SELECT 'DATASET_COUNT'
            WHERE (SELECT COUNT(*) FROM governance.q_finance_v3_dataset_registry) <> 72
            UNION ALL SELECT 'RELATIONSHIP_COUNT'
            WHERE (SELECT COUNT(*) FROM governance.q_finance_v3_relationship_registry) <> 109
            UNION ALL SELECT 'MEASURE_COUNT'
            WHERE (SELECT COUNT(*) FROM governance.q_finance_v3_measure_registry) <> 94
            UNION ALL SELECT 'LINEAGE_COUNT'
            WHERE (SELECT COUNT(*) FROM governance.q_finance_v3_lineage_registry) <> 72
        )
        """,
    ),
)
