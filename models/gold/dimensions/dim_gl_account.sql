select
    md5(account_id) as gl_account_hk,
    account_id,
    account_name,
    account_class,
    statement_class,
    statement_line,
    normal_balance,
    cash_flow_class,
    account_class = 'ASSET' as is_asset,
    account_class = 'LIABILITY' as is_liability,
    account_class = 'EQUITY' as is_equity,
    account_class = 'REVENUE' as is_revenue,
    account_class = 'EXPENSE' as is_expense,
    cash_flow_class = 'CASH' as is_cash_account,
    _source_row_hash,
    _source_data_ref
from {{ ref('stg_accounting__chart_of_accounts') }}
