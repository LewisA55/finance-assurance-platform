-- depends_on: {{ ref('dim_period') }}
-- depends_on: {{ ref('dim_legal_entity') }}
-- depends_on: {{ ref('dim_reporting_scope') }}
-- depends_on: {{ ref('dim_gl_account') }}
-- depends_on: {{ ref('dim_reporting_version') }}
-- depends_on: {{ ref('fct_business_events') }}
-- depends_on: {{ ref('fct_accounting_events') }}
-- depends_on: {{ ref('fct_gl_journal_lines') }}
-- depends_on: {{ ref('fct_elimination_journal_lines') }}
-- depends_on: {{ ref('fct_statutory_trial_balance') }}
-- depends_on: {{ ref('fct_statutory_statement_lines') }}
-- depends_on: {{ ref('fct_retained_earnings_bridge') }}
-- depends_on: {{ ref('fct_cash_flow_reconciliation') }}
-- depends_on: {{ ref('fct_monthly_close_status') }}
-- depends_on: {{ ref('fct_statutory_reconciliations') }}

with registry as (
    select * from (values
        ('QF-D01', 'gold', 'dim_period', 'ONE_ROW_PER_FISCAL_MONTH', 'ATLAS', 'DIMENSION', 'CORE'),
        ('QF-D02', 'gold', 'dim_legal_entity', 'ONE_ROW_PER_LEGAL_ENTITY', 'ATLAS', 'DIMENSION', 'CORE'),
        ('QF-D03', 'gold', 'dim_reporting_scope', 'ONE_ROW_PER_REPORTING_SCOPE', 'ATLAS', 'DIMENSION', 'CORE'),
        ('QF-D04', 'gold', 'dim_gl_account', 'ONE_ROW_PER_GL_ACCOUNT', 'ATLAS', 'DIMENSION', 'CORE'),
        ('QF-D05', 'gold', 'dim_reporting_version', 'ONE_ROW_PER_PERIOD_SCOPE_REPORTING_VERSION', 'ATLAS', 'DIMENSION', 'CORE'),
        ('QF-D06', 'gold', 'fct_business_events', 'ONE_ROW_PER_CAUSAL_BUSINESS_EVENT', 'HERMES', 'ATOMIC_FACT', 'LINEAGE'),
        ('QF-D07', 'gold', 'fct_accounting_events', 'ONE_ROW_PER_ACCOUNTING_LIFECYCLE_EVENT', 'ATLAS', 'ATOMIC_FACT', 'LINEAGE'),
        ('QF-D08', 'gold', 'fct_gl_journal_lines', 'ONE_ROW_PER_POSTED_SOURCE_JOURNAL_LINE', 'ATLAS', 'ATOMIC_FACT', 'CORE'),
        ('QF-D09', 'gold', 'fct_elimination_journal_lines', 'ONE_ROW_PER_ELIMINATION_JOURNAL_LINE', 'ATLAS', 'ATOMIC_FACT', 'LINEAGE'),
        ('QF-D10', 'gold', 'fct_statutory_trial_balance', 'ONE_ROW_PER_PERIOD_SCOPE_ENTITY_ACCOUNT_VERSION', 'ATLAS', 'ATOMIC_FACT', 'CORE'),
        ('QF-D11', 'gold', 'fct_statutory_statement_lines', 'ONE_ROW_PER_PERIOD_SCOPE_STATEMENT_LINE_VERSION', 'ATLAS', 'ATOMIC_FACT', 'CORE'),
        ('QF-D12', 'gold', 'fct_retained_earnings_bridge', 'ONE_ROW_PER_PERIOD_SCOPE_VERSION', 'ATLAS', 'RECONCILIATION_FACT', 'CORE'),
        ('QF-D13', 'gold', 'fct_cash_flow_reconciliation', 'ONE_ROW_PER_PERIOD_SCOPE_VERSION', 'ATLAS', 'RECONCILIATION_FACT', 'CORE'),
        ('QF-D14', 'gold', 'fct_monthly_close_status', 'ONE_ROW_PER_PERIOD_SCOPE_VERSION', 'ATLAS', 'GOVERNANCE_FACT', 'CORE'),
        ('QF-D15', 'gold', 'fct_statutory_reconciliations', 'ONE_ROW_PER_PERIOD_SCOPE_CONTROL_VERSION', 'ARGUS', 'ASSURANCE_FACT', 'CORE')
    ) as t(dataset_id, relation_schema, relation_name, grain, semantic_owner, model_class, consumption_class)
)
select
    'Q-FINANCE' as registry_id,
    1 as registry_version,
    dataset_id,
    1 as dataset_version,
    relation_schema,
    relation_name,
    grain,
    semantic_owner,
    model_class,
    consumption_class,
    'STATUTORY_ACTUALS' as reliability_purpose,
    '{{ var("a24_data_ref") }}' as source_data_ref,
    '{{ var("a24_package_digest") }}' as source_package_digest,
    '{{ var("finance_model_ref") }}' as finance_model_ref,
    'INTEGER_MINOR_UNITS_PLUS_CURRENCY' as money_contract
from registry
