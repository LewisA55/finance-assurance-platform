{{ config(tags=['slice_c']) }}

select table_name, column_name, data_type
from information_schema.columns
where table_schema = 'gold'
  and table_name like 'mart_%'
  and column_name like '%_minor'
  and data_type <> 'BIGINT'
