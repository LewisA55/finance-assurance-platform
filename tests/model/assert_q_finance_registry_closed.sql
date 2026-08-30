with registered as (
    select dataset_id, relation_schema, relation_name
    from {{ ref('q_finance_dataset_registry') }}
),
missing as (
    select registered.*
    from registered
    left join information_schema.tables as physical
      on registered.relation_schema = physical.table_schema
     and registered.relation_name = physical.table_name
    where physical.table_name is null
),
counts as (
    select count(*) as dataset_count from registered
)
select * from missing
union all
select 'COUNT' as dataset_id, cast(dataset_count as varchar), 'EXPECTED_15'
from counts where dataset_count <> 15
