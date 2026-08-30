-- depends_on: {{ ref('dim_bank_account') }}
-- depends_on: {{ ref('dim_debt_instrument') }}
-- depends_on: {{ ref('dim_fixed_asset') }}
-- depends_on: {{ ref('dim_lease_contract') }}
-- depends_on: {{ ref('dim_tax_jurisdiction') }}
-- depends_on: {{ ref('fct_subledger_event_links') }}
-- depends_on: {{ ref('fct_fixed_asset_lifecycle_events') }}
-- depends_on: {{ ref('fct_fixed_asset_movements') }}
-- depends_on: {{ ref('fct_fixed_asset_control_results') }}
-- depends_on: {{ ref('fct_bank_transactions') }}
-- depends_on: {{ ref('fct_bank_statement_lines') }}
-- depends_on: {{ ref('fct_bank_reconciliations') }}
-- depends_on: {{ ref('fct_debt_schedule') }}
-- depends_on: {{ ref('fct_lease_lifecycle_events') }}
-- depends_on: {{ ref('fct_lease_schedule') }}
-- depends_on: {{ ref('fct_tax_calculation_inputs') }}
-- depends_on: {{ ref('fct_tax_schedule') }}
-- depends_on: {{ ref('fct_tax_loss_register') }}
-- depends_on: {{ ref('fct_equity_movements') }}
-- depends_on: {{ ref('fct_accrual_source_events') }}
-- depends_on: {{ ref('fct_accrual_schedule') }}
-- depends_on: {{ ref('fct_prepayment_source_events') }}
-- depends_on: {{ ref('fct_prepayment_schedule') }}
-- depends_on: {{ ref('fct_intercompany_transactions') }}
-- depends_on: {{ ref('fct_intercompany_balances') }}
-- depends_on: {{ ref('fct_statutory_subledger_controls') }}
-- depends_on: {{ ref('fct_source_admissions') }}

with inherited as (
    select
        registry_id, 2 as registry_version, dataset_id, dataset_version,
        relation_schema, relation_name, grain, semantic_owner, model_class,
        consumption_class, reliability_purpose, source_data_ref,
        source_package_digest, '{{ var("finance_model_ref") }}' as finance_model_ref,
        money_contract
    from {{ ref('q_finance_dataset_registry') }}
), additions as (
    select * from (values
        ('QF-D16', 'dim_bank_account', 'ONE_ROW_PER_BANK_ACCOUNT', 'ATLAS', 'DIMENSION', 'CORE', 'TREASURY_ANALYTICS'),
        ('QF-D17', 'dim_debt_instrument', 'ONE_ROW_PER_DEBT_INSTRUMENT', 'ATLAS', 'DIMENSION', 'CORE', 'DEBT_AND_LIQUIDITY_ANALYTICS'),
        ('QF-D18', 'dim_fixed_asset', 'ONE_ROW_PER_FIXED_OR_INTANGIBLE_ASSET', 'ATLAS', 'DIMENSION', 'CORE', 'FIXED_ASSET_ANALYTICS'),
        ('QF-D19', 'dim_lease_contract', 'ONE_ROW_PER_LEASE_CONTRACT', 'ATLAS', 'DIMENSION', 'CORE', 'LEASE_ANALYTICS'),
        ('QF-D20', 'dim_tax_jurisdiction', 'ONE_ROW_PER_ENTITY_TAX_JURISDICTION', 'ATLAS', 'DIMENSION', 'CORE', 'TAX_ANALYTICS'),
        ('QF-D21', 'fct_subledger_event_links', 'ONE_ROW_PER_SUBLEDGER_OBJECT_BUSINESS_EVENT', 'ATLAS', 'BRIDGE_FACT', 'LINEAGE', 'SUBLEDGER_TO_LEDGER_LINEAGE'),
        ('QF-D22', 'fct_fixed_asset_lifecycle_events', 'ONE_ROW_PER_FIXED_ASSET_SOURCE_LIFECYCLE_EVENT', 'HERMES', 'ATOMIC_FACT', 'LINEAGE', 'FIXED_ASSET_ANALYTICS'),
        ('QF-D23', 'fct_fixed_asset_movements', 'ONE_ROW_PER_PERIOD_ASSET_MOVEMENT', 'ATLAS', 'ROLLFORWARD_FACT', 'CORE', 'FIXED_ASSET_ANALYTICS'),
        ('QF-D24', 'fct_fixed_asset_control_results', 'ONE_ROW_PER_FIXED_ASSET_CONTROL_RESULT', 'ARGUS', 'ASSURANCE_FACT', 'CORE', 'FIXED_ASSET_ASSURANCE'),
        ('QF-D25', 'fct_bank_transactions', 'ONE_ROW_PER_BANK_TRANSACTION', 'HERMES', 'ATOMIC_FACT', 'CORE', 'TREASURY_ANALYTICS'),
        ('QF-D26', 'fct_bank_statement_lines', 'ONE_ROW_PER_BANK_STATEMENT_LINE', 'HERMES', 'ATOMIC_FACT', 'LINEAGE', 'BANK_EVIDENCE'),
        ('QF-D27', 'fct_bank_reconciliations', 'ONE_ROW_PER_PERIOD_BANK_ACCOUNT', 'ARGUS', 'RECONCILIATION_FACT', 'CORE', 'TREASURY_ANALYTICS'),
        ('QF-D28', 'fct_debt_schedule', 'ONE_ROW_PER_PERIOD_DEBT_INSTRUMENT', 'ATLAS', 'ROLLFORWARD_FACT', 'CORE', 'DEBT_AND_LIQUIDITY_ANALYTICS'),
        ('QF-D29', 'fct_lease_lifecycle_events', 'ONE_ROW_PER_LEASE_SOURCE_LIFECYCLE_EVENT', 'HERMES', 'ATOMIC_FACT', 'LINEAGE', 'LEASE_ANALYTICS'),
        ('QF-D30', 'fct_lease_schedule', 'ONE_ROW_PER_PERIOD_LEASE_CONTRACT', 'ATLAS', 'ROLLFORWARD_FACT', 'CORE', 'LEASE_ANALYTICS'),
        ('QF-D31', 'fct_tax_calculation_inputs', 'ONE_ROW_PER_PERIOD_ENTITY_JURISDICTION_INPUT', 'HERMES', 'ATOMIC_FACT', 'CORE', 'TAX_ANALYTICS'),
        ('QF-D32', 'fct_tax_schedule', 'ONE_ROW_PER_PERIOD_ENTITY_JURISDICTION', 'ATLAS', 'ROLLFORWARD_FACT', 'CORE', 'TAX_ANALYTICS'),
        ('QF-D33', 'fct_tax_loss_register', 'ONE_ROW_PER_PERIOD_JURISDICTION_LOSS_VINTAGE', 'ATLAS', 'ROLLFORWARD_FACT', 'CORE', 'TAX_ANALYTICS'),
        ('QF-D34', 'fct_equity_movements', 'ONE_ROW_PER_AUTHORISED_EQUITY_MOVEMENT', 'ATLAS', 'ATOMIC_FACT', 'CORE', 'EQUITY_ANALYTICS'),
        ('QF-D35', 'fct_accrual_source_events', 'ONE_ROW_PER_ACCRUAL_SOURCE_EVENT', 'HERMES', 'ATOMIC_FACT', 'LINEAGE', 'ACCRUAL_ANALYTICS'),
        ('QF-D36', 'fct_accrual_schedule', 'ONE_ROW_PER_PERIOD_ACCRUAL', 'ATLAS', 'ROLLFORWARD_FACT', 'CORE', 'ACCRUAL_ANALYTICS'),
        ('QF-D37', 'fct_prepayment_source_events', 'ONE_ROW_PER_PREPAYMENT_SOURCE_EVENT', 'HERMES', 'ATOMIC_FACT', 'LINEAGE', 'PREPAYMENT_ANALYTICS'),
        ('QF-D38', 'fct_prepayment_schedule', 'ONE_ROW_PER_PERIOD_PREPAYMENT', 'ATLAS', 'ROLLFORWARD_FACT', 'CORE', 'PREPAYMENT_ANALYTICS'),
        ('QF-D39', 'fct_intercompany_transactions', 'ONE_ROW_PER_BILATERAL_INTERCOMPANY_TRANSACTION', 'HERMES', 'ATOMIC_FACT', 'CORE', 'INTERCOMPANY_ANALYTICS'),
        ('QF-D40', 'fct_intercompany_balances', 'ONE_ROW_PER_PERIOD_ENTITY_PAIR', 'ARGUS', 'RECONCILIATION_FACT', 'CORE', 'INTERCOMPANY_ANALYTICS'),
        ('QF-D41', 'fct_statutory_subledger_controls', 'ONE_ROW_PER_STATUTORY_SUBLEDGER_CONTROL_RESULT', 'ARGUS', 'ASSURANCE_FACT', 'CORE', 'SUBLEDGER_ASSURANCE'),
        ('QF-D42', 'fct_source_admissions', 'ONE_ROW_PER_B2_POSTING_CANDIDATE_ADMISSION', 'HERMES', 'GOVERNANCE_FACT', 'LINEAGE', 'SOURCE_ADMISSION_AND_QUARANTINE')
    ) t(dataset_id, relation_name, grain, semantic_owner, model_class, consumption_class, reliability_purpose)
)
select * from inherited
union all
select
    'Q-FINANCE', 2, dataset_id, 1, 'gold', relation_name, grain,
    semantic_owner, model_class, consumption_class, reliability_purpose,
    '{{ var("a24_data_ref") }}', '{{ var("a24_package_digest") }}',
    '{{ var("finance_model_ref") }}', 'INTEGER_MINOR_UNITS_PLUS_CURRENCY'
from additions
