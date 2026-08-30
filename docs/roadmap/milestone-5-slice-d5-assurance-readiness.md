# Milestone 5 Slice D5 - Assurance and Control Readiness

Status: Implementation authorised on 2026-08-26

## 0. Objective

Slice D5 extends the browser-local CFO product with a governed `/assurance`
experience over the published `Q-FINANCE-C2@v1` delivery. It explains whether
the selected reporting version is closed, reconciled, model-ready and bound to
the published package while preserving the existing Hermes, Argus and Aegis
evidence journeys.

D5 answers six management questions:

1. Is the selected scope-period reporting version hard closed and published?
2. Are subledger, bank, intercompany and trial-balance states reconciled?
3. Which model-serving controls passed, and against what expected values?
4. Which executive metrics have adequate historical and null-value coverage?
5. Did the C2 delivery reproduce the exact C1 table populations and digests?
6. Where can a reviewer inspect representative reconciliation, exception,
   issue, remediation and readiness evidence?

## 1. Product boundary

D5 provides:

- an `/assurance` route within the existing finance shell;
- scope-period close and reconciliation status across Group, UK and US;
- all 15 validator-produced model-readiness controls;
- all 11 executive metric-readiness assessments;
- the 36-control C2 package reconciliation catalogue;
- exact reporting-version, source-state and package-digest context;
- explicit separation between current package readiness and controlled
  assurance case-study journeys; and
- read-only links into existing Hermes, Argus and Aegis evidence routes.

D5 does not provide:

- an external-audit opinion, statutory certification or management sign-off;
- new Argus observations, findings or statistical anomaly tests;
- Aegis case creation, assignment, approval or remediation actuation;
- inferred control failures where the published result is `PASS`;
- Pythia forecast, scenario or valuation results; or
- Excel formulas, DAX, a semantic model or Power BI visuals.

## 2. Data authority

D5 reuses three already-admitted C2 browser tables:

1. `dim_reporting_version` - 198 exact scope-period close states;
2. `mart_cfo_metric_readiness` - 11 executive metric assessments; and
3. `mart_model_readiness_controls` - 15 executed model-serving controls.

It also consumes the signed C2 reconciliation catalogue containing 29 table
population/digest controls and seven package-level replay controls. D5 adds no
new finance mart and does not change the 19-table runtime population.

## 3. Semantic rules

1. Close status is copied from the exact selected reporting version.
2. `CONSOLIDATED` and `NOT_APPLICABLE` are valid source states and are not
   relabelled as `RECONCILED`.
3. Readiness-control outcomes use validator-produced actual, expected,
   comparison and first-failure fields without consumer reinterpretation.
4. Metric readiness retains the published minimum-period and acceptable-null
   thresholds.
5. Package controls describe delivery reproducibility, not the effectiveness
   of every underlying business control.
6. A passed model-serving control is not presented as an audit opinion.
7. Existing C-001 and CT-1 journeys remain separate controlled demonstrations;
   their exceptions and issues are not counted as current C2 package failures.
8. Exception, finding, issue, remediation, readiness and decision remain
   distinct lifecycle objects.
9. UI selections filter loaded rows and never become SQL identifiers or
   unvalidated SQL literals.
10. Missing rows or first-failure evidence produce an explicit unavailable
    state rather than an inferred conclusion.

## 4. Acceptance

- D1-D4 routes remain buildable and behaviourally intact;
- the Assurance navigation item and route are active;
- the D5 manifest contains the same nineteen governed runtime tables;
- the latest snapshot contains three June 2026 reporting versions, 15
  readiness controls, 11 metric assessments and 36 package controls;
- every reporting version remains hard closed, balanced and published;
- all readiness and package control counts reconcile to their sources;
- scope selection never substitutes one entity's close status for another;
- controlled case-study findings are not reported as current package failures;
- the UI explicitly states that readiness is not an audit opinion; and
- focused D1-D5 tests, full application tests, typecheck, lint and build pass.
