select
    md5(reconciliation.reconciliation_ref) as statutory_reconciliation_hk,
    reconciliation.reconciliation_ref,
    reconciliation.period_id,
    reconciliation.scope_id,
    reconciliation.reporting_version_ref,
    reconciliation.control_id,
    reconciliation.expected_amount_minor,
    reconciliation.actual_amount_minor,
    reconciliation.difference_minor,
    reconciliation.currency,
    reconciliation.status,
    reconciliation.evidence_ref,
    reconciliation.first_failure_ref,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest,
    reconciliation._source_row_hash,
    reconciliation._source_data_ref
from {{ ref('stg_governance__statutory_reconciliation_results') }} as reconciliation
inner join {{ ref('dim_reporting_version') }} as version
    on reconciliation.reporting_version_ref = version.reporting_version_ref
