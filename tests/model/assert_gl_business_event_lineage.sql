select source_journal_line_id, business_event_ref
from {{ ref('fct_gl_journal_lines') }}
where event_type is null
   or source_system is null
   or business_event_semantic_hash is null
