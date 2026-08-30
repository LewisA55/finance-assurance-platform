select
    source_journal_id,
    legal_entity_id,
    currency,
    sum(debit_minor) as debit_minor,
    sum(credit_minor) as credit_minor
from {{ ref('fct_gl_journal_lines') }}
group by 1, 2, 3
having sum(debit_minor) <> sum(credit_minor)
