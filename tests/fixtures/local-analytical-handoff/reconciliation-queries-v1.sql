-- S-QV01
WITH
  "s_v01_a01" AS (
    SELECT
      COUNT(*) = 1
      AND COUNT(*) FILTER (WHERE "amount_minor" = 0 AND "currency" = 'GBP') = 1 AS "assertion_pass"
    FROM "p_evidence_v1"."r_reporting_values"
    WHERE "reporting_version_ref" = 'RV-2026-06@v1'
      AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
      AND "statement_field" = 'subscription_revenue_minor'
  )
SELECT
  'S-V01' AS "check_id",
  CASE WHEN "s_v01_a01"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v01_a01"."assertion_pass" AS "s_v01_a01_pass"
FROM "s_v01_a01"
ORDER BY "check_id" ASC NULLS LAST;

-- S-QV02
WITH
  "s_v02_a01" AS (
    SELECT
      COUNT(*) = 1
      AND COUNT(*) FILTER (WHERE "amount_minor" = 1000000 AND "currency" = 'GBP') = 1 AS "assertion_pass"
    FROM "p_evidence_v1"."r_reporting_values"
    WHERE "reporting_version_ref" = 'RV-2026-06@v2'
      AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
      AND "statement_field" = 'subscription_revenue_minor'
  )
SELECT
  'S-V02' AS "check_id",
  CASE WHEN "s_v02_a01"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v02_a01"."assertion_pass" AS "s_v02_a01_pass"
FROM "s_v02_a01"
ORDER BY "check_id" ASC NULLS LAST;

-- S-QV03
WITH
  "s_v03_a01" AS (
    SELECT
      COUNT(*) = 1
      AND COUNT(*) FILTER (WHERE "adjustment_minor" = 1000000 AND "currency" = 'GBP') = 1 AS "assertion_pass"
    FROM "p_evidence_v1"."r_restatement_bridges"
    WHERE "predecessor_version_ref" = 'RV-2026-06@v1'
      AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
      AND "statement_field" = 'subscription_revenue_minor'
      AND "successor_version_ref" = 'RV-2026-06@v2'
  )
SELECT
  'S-V03' AS "check_id",
  CASE WHEN "s_v03_a01"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v03_a01"."assertion_pass" AS "s_v03_a01_pass"
FROM "s_v03_a01"
ORDER BY "check_id" ASC NULLS LAST;

-- S-QV04
WITH
  "s_v04_a01" AS (
    SELECT
      COUNT(*) = 1
      AND COUNT(*) FILTER (WHERE "difference_minor" = 1000000 AND "currency" = 'GBP') = 1 AS "assertion_pass"
    FROM "p_evidence_v1"."r_source_reconciliations"
    WHERE "reconciliation_ref" = 'RECON-C001@v1'
      AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
  )
SELECT
  'S-V04' AS "check_id",
  CASE WHEN "s_v04_a01"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v04_a01"."assertion_pass" AS "s_v04_a01_pass"
FROM "s_v04_a01"
ORDER BY "check_id" ASC NULLS LAST;

-- S-QV05
WITH
  "s_v05_a01" AS (
    SELECT
      COUNT(*) = 1
      AND COUNT(*) FILTER (WHERE "difference_minor" = 1000000 AND "currency" = 'GBP') = 1 AS "assertion_pass"
    FROM "p_evidence_v1"."r_assurance_exceptions"
    WHERE "exception_ref" = 'EXC-C001@v1'
      AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
  )
SELECT
  'S-V05' AS "check_id",
  CASE WHEN "s_v05_a01"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v05_a01"."assertion_pass" AS "s_v05_a01_pass"
FROM "s_v05_a01"
ORDER BY "check_id" ASC NULLS LAST;

-- S-QV06
WITH
  "selected_readiness" AS (
    SELECT *
    FROM "p_evidence_v1"."r_readiness_assessments"
    WHERE "readiness_ref" = 'READY-C001@v1'
      AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
  ),
  "selected_bases" AS (
    SELECT DISTINCT "parent_row_key", "reference_ref"
    FROM "p_evidence_v1"."r_reference_bindings"
    WHERE "parent_dataset_id" = 'P-D10'
      AND "reference_role" = 'READINESS_BASIS'
      AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
  ),
  "expected_bases"("parent_row_key", "reference_ref") AS (
    VALUES ('P-D10:987976cd1910dc2e201c4b6b', 'PUB-AE-C001-011-G-06-03')
  ),
  "s_v06_a01" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "reporting_version_ref" = 'RV-2026-06@v2') = 1 AS "assertion_pass"
    FROM "selected_readiness"
  ),
  "s_v06_a02" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "purpose_ref" = 'HIRING-FORECAST') = 1 AS "assertion_pass"
    FROM "selected_readiness"
  ),
  "s_v06_a03" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "scope_ref" = 'NEXUS-GROUP') = 1 AS "assertion_pass"
    FROM "selected_readiness"
  ),
  "s_v06_a04" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "status" = 'APPROVED') = 1 AS "assertion_pass"
    FROM "selected_readiness"
  ),
  "s_v06_a05" AS (
    SELECT
      NOT EXISTS (SELECT * FROM "selected_bases" EXCEPT ALL SELECT * FROM "expected_bases")
      AND NOT EXISTS (SELECT * FROM "expected_bases" EXCEPT ALL SELECT * FROM "selected_bases") AS "assertion_pass"
  ),
  "s_v06_a06" AS (
    SELECT NOT EXISTS (
      SELECT "limitation_code"
      FROM "p_evidence_v1"."r_readiness_limitations"
      WHERE "readiness_ref" = 'READY-C001@v1'
        AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
    ) AS "assertion_pass"
  )
SELECT
  'S-V06' AS "check_id",
  CASE WHEN "s_v06_a01"."assertion_pass" AND "s_v06_a02"."assertion_pass" AND "s_v06_a03"."assertion_pass" AND "s_v06_a04"."assertion_pass" AND "s_v06_a05"."assertion_pass" AND "s_v06_a06"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v06_a01"."assertion_pass" AS "s_v06_a01_pass",
  "s_v06_a02"."assertion_pass" AS "s_v06_a02_pass",
  "s_v06_a03"."assertion_pass" AS "s_v06_a03_pass",
  "s_v06_a04"."assertion_pass" AS "s_v06_a04_pass",
  "s_v06_a05"."assertion_pass" AS "s_v06_a05_pass",
  "s_v06_a06"."assertion_pass" AS "s_v06_a06_pass"
FROM "s_v06_a01"
CROSS JOIN "s_v06_a02"
CROSS JOIN "s_v06_a03"
CROSS JOIN "s_v06_a04"
CROSS JOIN "s_v06_a05"
CROSS JOIN "s_v06_a06"
ORDER BY "check_id" ASC NULLS LAST;

-- S-QV07
WITH
  "selected_decision" AS (
    SELECT *
    FROM "p_evidence_v1"."r_governed_decisions"
    WHERE "decision_ref" = 'DECISION-C001@v1'
      AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
  ),
  "s_v07_a01" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "monthly_cost_minor" = 650000 AND "currency" = 'GBP') = 1 AS "assertion_pass"
    FROM "selected_decision"
  ),
  "s_v07_a02" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "readiness_ref" = 'READY-C001@v1') = 1 AS "assertion_pass"
    FROM "selected_decision"
  )
SELECT
  'S-V07' AS "check_id",
  CASE WHEN "s_v07_a01"."assertion_pass" AND "s_v07_a02"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v07_a01"."assertion_pass" AS "s_v07_a01_pass",
  "s_v07_a02"."assertion_pass" AS "s_v07_a02_pass"
FROM "s_v07_a01"
CROSS JOIN "s_v07_a02"
ORDER BY "check_id" ASC NULLS LAST;

-- S-QV08
WITH
  "selected_correction" AS (
    SELECT *
    FROM "p_evidence_v1"."r_correction_cases"
    WHERE "scenario_ref" = 'DEMO-CT1-CORRECTION@v1'
      AND "verification_ref" = 'VERIFY-CT1@v1'
  ),
  "s_v08_a01" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "control_account_net_movement_minor" = 0 AND "currency" = 'GBP') = 1 AS "assertion_pass"
    FROM "selected_correction"
  ),
  "s_v08_a02" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "reversal_binding_status" = 'BOUND_BEFORE_COMPARE') = 1 AS "assertion_pass"
    FROM "selected_correction"
  )
SELECT
  'S-V08' AS "check_id",
  CASE WHEN "s_v08_a01"."assertion_pass" AND "s_v08_a02"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v08_a01"."assertion_pass" AS "s_v08_a01_pass",
  "s_v08_a02"."assertion_pass" AS "s_v08_a02_pass"
FROM "s_v08_a01"
CROSS JOIN "s_v08_a02"
ORDER BY "check_id" ASC NULLS LAST;

-- S-QV09
WITH
  "selected_j011" AS (
    SELECT *
    FROM "q_analytics_v1"."r_journal_headers"
    WHERE "journal_id" = 'J-011'
      AND "scenario_ref" = 'DEMO-CT1-CORRECTION@v1'
  ),
  "s_v09_a01" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "total_debit_minor" = 12000000 AND "currency" = 'GBP') = 1 AS "assertion_pass"
    FROM "selected_j011"
  ),
  "s_v09_a02" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "total_credit_minor" = 12000000 AND "currency" = 'GBP') = 1 AS "assertion_pass"
    FROM "selected_j011"
  )
SELECT
  'S-V09' AS "check_id",
  CASE WHEN "s_v09_a01"."assertion_pass" AND "s_v09_a02"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v09_a01"."assertion_pass" AS "s_v09_a01_pass",
  "s_v09_a02"."assertion_pass" AS "s_v09_a02_pass"
FROM "s_v09_a01"
CROSS JOIN "s_v09_a02"
ORDER BY "check_id" ASC NULLS LAST;

-- S-QV10
WITH
  "selected_j012" AS (
    SELECT *
    FROM "q_analytics_v1"."r_journal_headers"
    WHERE "journal_id" = 'J-012'
      AND "scenario_ref" = 'DEMO-CT1-CORRECTION@v1'
  ),
  "s_v10_a01" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "total_debit_minor" = 12000000 AND "currency" = 'GBP') = 1 AS "assertion_pass"
    FROM "selected_j012"
  ),
  "s_v10_a02" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "total_credit_minor" = 12000000 AND "currency" = 'GBP') = 1 AS "assertion_pass"
    FROM "selected_j012"
  )
SELECT
  'S-V10' AS "check_id",
  CASE WHEN "s_v10_a01"."assertion_pass" AND "s_v10_a02"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v10_a01"."assertion_pass" AS "s_v10_a01_pass",
  "s_v10_a02"."assertion_pass" AS "s_v10_a02_pass"
FROM "s_v10_a01"
CROSS JOIN "s_v10_a02"
ORDER BY "check_id" ASC NULLS LAST;

-- S-QV11
WITH
  "authored_headers" AS (
    SELECT DISTINCT "journal_id"
    FROM "q_analytics_v1"."r_journal_headers"
    WHERE "scenario_ref" = 'DEMO-CT1-CORRECTION@v1'
  ),
  "authored_lines" AS (
    SELECT DISTINCT "journal_id"
    FROM "q_analytics_v1"."r_journal_lines"
    WHERE "scenario_ref" = 'DEMO-CT1-CORRECTION@v1'
  ),
  "referenced_headers" AS (
    SELECT DISTINCT "journal_id"
    FROM "q_analytics_v1"."r_referenced_journals"
    WHERE "scenario_ref" = 'DEMO-CT1-CORRECTION@v1'
  ),
  "referenced_lines" AS (
    SELECT DISTINCT "journal_id"
    FROM "q_analytics_v1"."r_referenced_journal_lines"
    WHERE "scenario_ref" = 'DEMO-CT1-CORRECTION@v1'
  ),
  "expected_j010"("journal_id") AS (
    VALUES ('J-010')
  ),
  "s_v11_a01" AS (
    SELECT NOT EXISTS (
      SELECT "authored_headers"."journal_id"
      FROM "authored_headers"
      INNER JOIN "referenced_headers" USING ("journal_id")
    ) AS "assertion_pass"
  ),
  "s_v11_a02" AS (
    SELECT NOT EXISTS (
      SELECT "authored_lines"."journal_id"
      FROM "authored_lines"
      INNER JOIN "referenced_lines" USING ("journal_id")
    ) AS "assertion_pass"
  ),
  "s_v11_a03" AS (
    SELECT EXISTS (SELECT 1 FROM "authored_headers" WHERE "journal_id" = 'J-011') AS "assertion_pass"
  ),
  "s_v11_a04" AS (
    SELECT EXISTS (SELECT 1 FROM "authored_headers" WHERE "journal_id" = 'J-012') AS "assertion_pass"
  ),
  "s_v11_a05" AS (
    SELECT COUNT(*) = 1 AND COUNT(*) FILTER (WHERE "authored_by_f" = FALSE) = 1 AS "assertion_pass"
    FROM "q_analytics_v1"."r_referenced_journals"
    WHERE "journal_id" = 'J-010'
      AND "scenario_ref" = 'DEMO-CT1-CORRECTION@v1'
  ),
  "s_v11_a06" AS (
    SELECT
      NOT EXISTS (SELECT * FROM "referenced_lines" EXCEPT ALL SELECT * FROM "expected_j010")
      AND NOT EXISTS (SELECT * FROM "expected_j010" EXCEPT ALL SELECT * FROM "referenced_lines") AS "assertion_pass"
  )
SELECT
  'S-V11' AS "check_id",
  CASE WHEN "s_v11_a01"."assertion_pass" AND "s_v11_a02"."assertion_pass" AND "s_v11_a03"."assertion_pass" AND "s_v11_a04"."assertion_pass" AND "s_v11_a05"."assertion_pass" AND "s_v11_a06"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v11_a01"."assertion_pass" AS "s_v11_a01_pass",
  "s_v11_a02"."assertion_pass" AS "s_v11_a02_pass",
  "s_v11_a03"."assertion_pass" AS "s_v11_a03_pass",
  "s_v11_a04"."assertion_pass" AS "s_v11_a04_pass",
  "s_v11_a05"."assertion_pass" AS "s_v11_a05_pass",
  "s_v11_a06"."assertion_pass" AS "s_v11_a06_pass"
FROM "s_v11_a01"
CROSS JOIN "s_v11_a02"
CROSS JOIN "s_v11_a03"
CROSS JOIN "s_v11_a04"
CROSS JOIN "s_v11_a05"
CROSS JOIN "s_v11_a06"
ORDER BY "check_id" ASC NULLS LAST;

-- S-QV12
WITH
  "selected_nodes" AS (
    SELECT "node_ref"
    FROM "p_evidence_v1"."r_trace_nodes"
    WHERE "reporting_version_ref" = 'RV-2026-06@v2'
      AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
      AND "statement_field" = 'subscription_revenue_minor'
  ),
  "selected_edges" AS (
    SELECT "source_ref", "target_ref", "relationship"
    FROM "p_evidence_v1"."r_trace_edges"
    WHERE "reporting_version_ref" = 'RV-2026-06@v2'
      AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
      AND "statement_field" = 'subscription_revenue_minor'
  ),
  "s_v12_a01" AS (
    SELECT
      (SELECT COUNT(*) FROM "selected_nodes") = 42
      AND (SELECT COUNT(*) FROM "selected_edges") = 58
      AND (SELECT 'sha256:' || sha256(to_json(struct_pack(contract_version := 'validation-member-set@v1', fields := ['node_ref'], members := list(list_value("node_ref") ORDER BY "node_ref")))) FROM "selected_nodes") = 'sha256:9f4cff10f2689171c44139e00b1f5fd33bfbbb36a102c85396451a166490bc37'
      AND (SELECT 'sha256:' || sha256(to_json(struct_pack(contract_version := 'validation-member-set@v1', fields := ['source_ref','target_ref','relationship'], members := list(list_value("source_ref","target_ref","relationship") ORDER BY "source_ref","target_ref","relationship")))) FROM "selected_edges") = 'sha256:f70c2c84b33d66fb48f51f65e0d77a906b3907f24ed59f7a1b9ed3f33d608db1' AS "assertion_pass"
  ),
  "s_v12_a02" AS (
    SELECT NOT EXISTS (
      SELECT 1
      FROM "selected_edges"
      WHERE NOT EXISTS (
        SELECT 1 FROM "selected_nodes" WHERE "node_ref" = "selected_edges"."source_ref"
      )
    ) AS "assertion_pass"
  ),
  "s_v12_a03" AS (
    SELECT NOT EXISTS (
      SELECT 1
      FROM "selected_edges"
      WHERE NOT EXISTS (
        SELECT 1 FROM "selected_nodes" WHERE "node_ref" = "selected_edges"."target_ref"
      )
    ) AS "assertion_pass"
  ),
  "s_v12_a04" AS (
    SELECT
      COUNT(*) = 1
      AND COUNT(*) FILTER (WHERE "content_verification_status" = 'CONTENT_BYTES_VERIFIED' AND "trace_available" = TRUE) = 1 AS "assertion_pass"
    FROM "p_evidence_v1"."r_reporting_values"
    WHERE "reporting_version_ref" = 'RV-2026-06@v2'
      AND "scenario_ref" = 'DEMO-C001-RESTATEMENT@v1'
      AND "statement_field" = 'subscription_revenue_minor'
  )
SELECT
  'S-V12' AS "check_id",
  CASE WHEN "s_v12_a01"."assertion_pass" AND "s_v12_a02"."assertion_pass" AND "s_v12_a03"."assertion_pass" AND "s_v12_a04"."assertion_pass" THEN 'PASS' ELSE 'FAIL' END AS "check_status",
  "s_v12_a01"."assertion_pass" AS "s_v12_a01_pass",
  "s_v12_a02"."assertion_pass" AS "s_v12_a02_pass",
  "s_v12_a03"."assertion_pass" AS "s_v12_a03_pass",
  "s_v12_a04"."assertion_pass" AS "s_v12_a04_pass"
FROM "s_v12_a01"
CROSS JOIN "s_v12_a02"
CROSS JOIN "s_v12_a03"
CROSS JOIN "s_v12_a04"
ORDER BY "check_id" ASC NULLS LAST;
