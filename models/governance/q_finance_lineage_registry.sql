select * from (values
    ('QF-D01', 'dim_period', 'stg_reference__periods', 'reference__periods', 'STRICT_TYPE_AND_CONFORM'),
    ('QF-D02', 'dim_legal_entity', 'stg_reference__legal_entities', 'reference__legal_entities', 'STRICT_TYPE_AND_CONFORM'),
    ('QF-D03', 'dim_reporting_scope', 'stg_reference__legal_entities', 'reference__legal_entities|accounting__statutory_trial_balance', 'REGISTER_ENTITY_AND_GROUP_SCOPES'),
    ('QF-D04', 'dim_gl_account', 'stg_accounting__chart_of_accounts', 'accounting__chart_of_accounts', 'STRICT_TYPE_AND_SEMANTIC_FLAGS'),
    ('QF-D05', 'dim_reporting_version', 'stg_accounting__monthly_close_status', 'accounting__monthly_close_status', 'PURPOSE_SPECIFIC_RELIABILITY_CLASSIFICATION'),
    ('QF-D06', 'fct_business_events', 'stg_events__business_events', 'events__business_events', 'LOSSLESS_TYPED_PROJECTION'),
    ('QF-D07', 'fct_accounting_events', 'stg_accounting__accounting_events', 'accounting__accounting_events', 'LOSSLESS_TYPED_PROJECTION'),
    ('QF-D08', 'fct_gl_journal_lines', 'stg_accounting__source_gl_journal_lines|stg_events__business_events', 'accounting__source_gl_journal_lines|events__business_events', 'TYPE_AND_RESOLVE_CAUSAL_EVENT'),
    ('QF-D09', 'fct_elimination_journal_lines', 'stg_consolidation__elimination_journal_lines|stg_accounting__accounting_events', 'consolidation__elimination_journal_lines|accounting__accounting_events', 'TYPE_AND_RESOLVE_ACCOUNTING_EVENT'),
    ('QF-D10', 'fct_statutory_trial_balance', 'stg_accounting__statutory_trial_balance|dim_gl_account|dim_reporting_version', 'accounting__statutory_trial_balance', 'TYPE_AND_ENRICH_WITH_SEMANTICS_AND_RELIABILITY'),
    ('QF-D11', 'fct_statutory_statement_lines', 'stg_accounting__statutory_statement_lines|dim_reporting_version', 'accounting__statutory_statement_lines', 'TYPE_AND_ENRICH_WITH_RELIABILITY'),
    ('QF-D12', 'fct_retained_earnings_bridge', 'stg_accounting__retained_earnings_bridge|dim_reporting_version', 'accounting__retained_earnings_bridge', 'TYPE_AND_ENRICH_WITH_RELIABILITY'),
    ('QF-D13', 'fct_cash_flow_reconciliation', 'stg_accounting__cash_flow_reconciliation|dim_reporting_version', 'accounting__cash_flow_reconciliation', 'TYPE_AND_ENRICH_WITH_RELIABILITY'),
    ('QF-D14', 'fct_monthly_close_status', 'stg_accounting__monthly_close_status|dim_reporting_version', 'accounting__monthly_close_status', 'TYPE_AND_ENRICH_WITH_RELIABILITY'),
    ('QF-D15', 'fct_statutory_reconciliations', 'stg_governance__statutory_reconciliation_results|dim_reporting_version', 'governance__statutory_reconciliation_results', 'TYPE_AND_ENRICH_WITH_RELIABILITY')
) as t(dataset_id, gold_model, direct_dependencies, a24_bronze_sources, transformation_class)
