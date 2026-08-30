{{ config(tags=['slice_c']) }}

select
    md5(concat_ws('|', trial.period_id, trial.scope_id, trial.account_id, trial.currency,
                  trial.reporting_version_ref)) as model_actuals_feed_hk,
    trial.period_id,
    period.month_start,
    period.month_end,
    period.fiscal_year,
    period.fiscal_quarter,
    trial.scope_id,
    scope.scope_type,
    trial.account_id,
    account.account_name,
    account.account_class,
    account.statement_class,
    account.statement_line,
    account.normal_balance,
    account.cash_flow_class,
    trial.currency,
    trial.opening_balance_minor,
    trial.debit_activity_minor,
    trial.credit_activity_minor,
    trial.elimination_debit_minor,
    trial.elimination_credit_minor,
    trial.closing_balance_minor,
    case
        when account.statement_class = 'BALANCE_SHEET' and account.normal_balance = 'CREDIT'
            then (-trial.closing_balance_minor)::bigint
        when account.statement_class = 'BALANCE_SHEET'
            then trial.closing_balance_minor
        else (trial.credit_activity_minor - trial.debit_activity_minor
              + trial.elimination_credit_minor - trial.elimination_debit_minor)::bigint
    end as model_actual_amount_minor,
    trial.reporting_version_ref,
    'STATUTORY_TRIAL_BALANCE' as value_authority,
    trial.reliability_status,
    'MODEL_SERVING_ACTUALS' as reliability_purpose,
    'gold.fct_statutory_trial_balance' as drill_through_relation,
    trial._source_row_hash as evidence_digest,
    trial.source_package_digest,
    trial._source_data_ref
from {{ ref('fct_statutory_trial_balance') }} trial
inner join {{ ref('dim_period') }} period using (period_id)
inner join {{ ref('dim_reporting_scope') }} scope using (scope_id)
inner join {{ ref('dim_gl_account') }} account using (account_id)
