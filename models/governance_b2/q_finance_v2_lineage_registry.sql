with additions as (
    select * from (values
        ('QF-D16', 'dim_bank_account', 'stg_treasury__bank_accounts|dim_legal_entity', 'treasury__bank_accounts', 'STRICT_TYPE_AND_CONFORM'),
        ('QF-D17', 'dim_debt_instrument', 'stg_treasury__debt_instruments|dim_legal_entity', 'treasury__debt_instruments', 'STRICT_TYPE_AND_CONFORM'),
        ('QF-D18', 'dim_fixed_asset', 'stg_fixed_assets__fixed_asset_register|dim_legal_entity|fct_business_events', 'fixed_assets__fixed_asset_register', 'TYPE_CONFORM_AND_RESOLVE_ACQUISITION_EVENT'),
        ('QF-D19', 'dim_lease_contract', 'stg_leases__lease_contracts|dim_legal_entity', 'leases__lease_contracts', 'STRICT_TYPE_AND_CONFORM'),
        ('QF-D20', 'dim_tax_jurisdiction', 'stg_tax__tax_calculation_inputs', 'tax__tax_calculation_inputs', 'TYPE_AND_CONFORM_ENTITY_JURISDICTION'),
        ('QF-D21', 'fct_subledger_event_links', 'B2_SCHEDULES|fct_business_events|fct_gl_journal_lines|dim_reporting_version', 'MULTIPLE_B2_SUBLEDGERS', 'RESOLVE_OBJECT_TO_CAUSAL_EVENT_LEDGER_AND_CLOSE'),
        ('QF-D22', 'fct_fixed_asset_lifecycle_events', 'stg_fixed_assets__asset_lifecycle_events|stg_hermes__source_admission_results|dim_fixed_asset', 'fixed_assets__asset_lifecycle_events|hermes__source_admission_results', 'TYPE_AND_PRESERVE_ADMISSION'),
        ('QF-D23', 'fct_fixed_asset_movements', 'stg_fixed_assets__fixed_asset_movements|dim_fixed_asset|fct_subledger_event_links|dim_reporting_version', 'fixed_assets__fixed_asset_movements', 'TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D24', 'fct_fixed_asset_control_results', 'stg_assurance__fixed_asset_control_results|dim_fixed_asset|dim_reporting_version', 'assurance__fixed_asset_control_results', 'TYPE_AND_BIND_ASSURANCE_TO_B1'),
        ('QF-D25', 'fct_bank_transactions', 'stg_treasury__bank_transactions|dim_bank_account|fct_subledger_event_links|dim_reporting_version', 'treasury__bank_transactions', 'TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D26', 'fct_bank_statement_lines', 'stg_treasury__bank_statement_lines|stg_treasury__bank_transactions|dim_reporting_version', 'treasury__bank_statement_lines|treasury__bank_transactions', 'TYPE_AND_RESOLVE_BANK_EVIDENCE'),
        ('QF-D27', 'fct_bank_reconciliations', 'stg_treasury__bank_reconciliations|dim_bank_account|dim_reporting_version', 'treasury__bank_reconciliations', 'TYPE_AND_BIND_RECONCILIATION_TO_B1'),
        ('QF-D28', 'fct_debt_schedule', 'stg_treasury__debt_schedule|dim_debt_instrument|fct_subledger_event_links|dim_reporting_version', 'treasury__debt_schedule', 'TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D29', 'fct_lease_lifecycle_events', 'stg_leases__lease_lifecycle_events|stg_hermes__source_admission_results|dim_lease_contract', 'leases__lease_lifecycle_events|hermes__source_admission_results', 'TYPE_AND_PRESERVE_ADMISSION'),
        ('QF-D30', 'fct_lease_schedule', 'stg_leases__lease_schedule|dim_lease_contract|fct_subledger_event_links|dim_reporting_version', 'leases__lease_schedule', 'TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D31', 'fct_tax_calculation_inputs', 'stg_tax__tax_calculation_inputs|dim_tax_jurisdiction|dim_reporting_version', 'tax__tax_calculation_inputs', 'TYPE_AND_BIND_APPROVED_INPUT_TO_B1'),
        ('QF-D32', 'fct_tax_schedule', 'stg_tax__tax_schedule|dim_tax_jurisdiction|fct_subledger_event_links|dim_reporting_version', 'tax__tax_schedule', 'TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D33', 'fct_tax_loss_register', 'stg_tax__tax_loss_register|dim_tax_jurisdiction|dim_reporting_version', 'tax__tax_loss_register', 'TYPE_AND_BIND_VINTAGE_TO_B1'),
        ('QF-D34', 'fct_equity_movements', 'stg_equity__equity_movements|fct_business_events|fct_subledger_event_links|dim_reporting_version', 'equity__equity_movements', 'TYPE_RESOLVE_EVENT_AND_BIND_TO_B1'),
        ('QF-D35', 'fct_accrual_source_events', 'stg_working_capital__accrual_source_events|stg_hermes__source_admission_results', 'working_capital__accrual_source_events|hermes__source_admission_results', 'TYPE_AND_PRESERVE_ADMISSION'),
        ('QF-D36', 'fct_accrual_schedule', 'stg_working_capital__accrual_schedule|dim_gl_account|fct_subledger_event_links|dim_reporting_version', 'working_capital__accrual_schedule', 'TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D37', 'fct_prepayment_source_events', 'stg_working_capital__prepayment_source_events|stg_hermes__source_admission_results', 'working_capital__prepayment_source_events|hermes__source_admission_results', 'TYPE_AND_PRESERVE_QUARANTINE'),
        ('QF-D38', 'fct_prepayment_schedule', 'stg_working_capital__prepayment_schedule|dim_gl_account|fct_subledger_event_links|dim_reporting_version', 'working_capital__prepayment_schedule', 'TYPE_ENRICH_AND_BIND_TO_B1'),
        ('QF-D39', 'fct_intercompany_transactions', 'stg_intercompany__intercompany_transactions|stg_hermes__source_admission_results|fct_elimination_journal_lines|dim_reporting_version', 'intercompany__intercompany_transactions|hermes__source_admission_results|consolidation__elimination_journal_lines', 'RESOLVE_DUAL_ADMISSION_ELIMINATION_AND_B1'),
        ('QF-D40', 'fct_intercompany_balances', 'stg_intercompany__intercompany_balances|dim_reporting_version', 'intercompany__intercompany_balances', 'TYPE_AND_BIND_BILATERAL_CONFIRMATION_TO_B1'),
        ('QF-D41', 'fct_statutory_subledger_controls', 'stg_assurance__statutory_subledger_control_results|dim_reporting_version', 'assurance__statutory_subledger_control_results', 'TYPE_AND_BIND_ASSURANCE_TO_B1'),
        ('QF-D42', 'fct_source_admissions', 'stg_hermes__source_admission_results|fct_business_events|dim_reporting_version', 'hermes__source_admission_results', 'TYPE_AND_PRESERVE_ADMISSION_AND_QUARANTINE')
    ) t(dataset_id, gold_model, direct_dependencies, a24_bronze_sources, transformation_class)
)
select * from {{ ref('q_finance_lineage_registry') }}
union all
select * from additions
