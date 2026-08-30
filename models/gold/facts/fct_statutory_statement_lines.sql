select
    md5(concat_ws('|', statement.period_id, statement.scope_id, statement.statement_class, statement.statement_line, statement.reporting_version_ref)) as statement_line_hk,
    statement.period_id,
    statement.scope_id,
    statement.statement_class,
    statement.statement_line,
    statement.amount_minor,
    statement.currency,
    statement.reporting_version_ref,
    statement.source_trial_balance_digest,
    statement.presentation_order,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest,
    statement._source_row_hash,
    statement._source_data_ref
from {{ ref('stg_accounting__statutory_statement_lines') }} as statement
inner join {{ ref('dim_reporting_version') }} as version
    on statement.reporting_version_ref = version.reporting_version_ref
