{{ config(tags=['slice_b2']) }}

select intercompany_transaction_id
from {{ ref('fct_intercompany_transactions') }}
where seller_admission_decision <> 'ADMITTED'
   or buyer_admission_decision <> 'ADMITTED'
   or elimination_line_count <> 4
   or elimination_debit_minor <> 2 * amount_minor
   or elimination_credit_minor <> 2 * amount_minor
   or elimination_accounting_event_ref is null
