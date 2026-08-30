-- S-QS01
SELECT
  "reporting_version_ref",
  "statement_field",
  "amount_minor",
  "currency"
FROM "p_evidence_v1"."r_reporting_values"
WHERE "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
ORDER BY "reporting_version_ref" ASC NULLS LAST, "statement_field" ASC NULLS LAST;

-- S-QS02
SELECT
  "reconciliation_ref",
  "difference_minor",
  "currency",
  "reconciliation_status"
FROM "p_evidence_v1"."r_source_reconciliations"
WHERE "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
ORDER BY "reconciliation_ref" ASC NULLS LAST;

-- S-QS03
SELECT
  "readiness_ref",
  "reporting_version_ref",
  "purpose_ref",
  "scope_ref",
  "status"
FROM "p_evidence_v1"."r_readiness_assessments"
WHERE "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
ORDER BY "readiness_ref" ASC NULLS LAST;

-- S-QS04
SELECT
  "journal_id",
  "entry_class",
  "total_debit_minor",
  "total_credit_minor",
  "currency"
FROM "q_analytics_v1"."r_journal_headers"
WHERE "scenario_ref" = 'DEMO-CT1-CORRECTION@v1'
ORDER BY "journal_id" ASC NULLS LAST;

-- S-QS05
SELECT
  "source_ref",
  "target_ref",
  "relationship"
FROM "p_evidence_v1"."r_trace_edges"
WHERE "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
  AND "reporting_version_ref" = 'RV-2026-06@v2'
  AND "statement_field" = 'subscription_revenue_minor'
ORDER BY "source_ref" ASC NULLS LAST, "target_ref" ASC NULLS LAST, "relationship" ASC NULLS LAST;
