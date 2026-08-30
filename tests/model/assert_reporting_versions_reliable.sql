select reporting_version_ref
from {{ ref('dim_reporting_version') }}
where reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
   or reliability_purpose <> 'STATUTORY_ACTUALS'
   or source_package_digest <> '{{ var("a24_package_digest") }}'
