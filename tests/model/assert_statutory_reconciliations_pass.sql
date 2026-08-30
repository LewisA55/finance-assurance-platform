select reconciliation_ref
from {{ ref('fct_statutory_reconciliations') }}
where status <> 'PASS'
   or difference_minor <> 0
   or first_failure_ref is not null
