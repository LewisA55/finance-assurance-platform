{{ config(tags=['slice_c']) }}

select feed.model_actuals_feed_hk as object_ref
from {{ ref('mart_model_actuals_feed') }} feed
inner join {{ ref('fct_statutory_trial_balance') }} trial
  using (period_id, scope_id, account_id, currency, reporting_version_ref)
inner join {{ ref('dim_gl_account') }} account using (account_id)
where feed.opening_balance_minor <> trial.opening_balance_minor
   or feed.closing_balance_minor <> trial.closing_balance_minor
   or feed.model_actual_amount_minor <> case
        when account.statement_class = 'BALANCE_SHEET' and account.normal_balance = 'CREDIT'
            then -trial.closing_balance_minor
        when account.statement_class = 'BALANCE_SHEET' then trial.closing_balance_minor
        else trial.credit_activity_minor - trial.debit_activity_minor
             + trial.elimination_credit_minor - trial.elimination_debit_minor
      end
