{{ config(tags=['slice_b2']) }}

with registered as (
    select dataset_id, relation_schema, relation_name
    from {{ ref('q_finance_v2_dataset_registry') }}
), missing as (
    select registered.*
    from registered
    left join information_schema.tables physical
      on registered.relation_schema = physical.table_schema
     and registered.relation_name = physical.table_name
    where physical.table_name is null
)
select * from missing
union all
select 'COUNT', cast(count(*) as varchar), 'EXPECTED_42'
from registered having count(*) <> 42
