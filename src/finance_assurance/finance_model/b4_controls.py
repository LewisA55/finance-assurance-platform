"""Independent executable controls for final Q-FINANCE Slice B4."""


B4_CONTROL_QUERIES = (
    (
        "B4_GOLD_POPULATION_RECONCILES_TO_SILVER",
        """
        WITH populations AS (
            SELECT (SELECT COUNT(*) FROM gold.dim_budget_version) actual_rows,
                   (SELECT COUNT(*) FROM silver.stg_planning__budget_versions) expected_rows
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.dim_planning_scenario),
                             (SELECT COUNT(*) FROM silver.stg_planning__forecast_versions)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_budget_plan_lines),
                             (SELECT COUNT(*) FROM silver.stg_planning__budget_lines)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_forecast_plan_lines),
                             (SELECT COUNT(*) FROM silver.stg_planning__forecast_lines)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_planning_variance_source),
                             (SELECT COUNT(*) FROM silver.stg_planning__variance_source_extract)
            UNION ALL SELECT (SELECT COUNT(*) FROM gold.fct_headcount_plan),
                             (SELECT COUNT(*) FROM silver.stg_planning__headcount_plan)
        ) SELECT COUNT(*) FROM populations WHERE actual_rows <> expected_rows
        """,
    ),
    (
        "B4_BUDGET_AUTHORITY_IS_PRESERVED",
        """
        SELECT COUNT(*) FROM gold.fct_budget_plan_lines line
        INNER JOIN gold.dim_budget_version version USING (budget_version_ref)
        WHERE line.period_id < version.planning_start_period
           OR line.period_id > version.planning_end_period
           OR line.approval_status <> version.approval_status
           OR line.planning_input_status <> version.planning_input_status
           OR line.reporting_currency <> 'GBP'
           OR line._source_row_hash IS NULL
        """,
    ),
    (
        "B4_SCENARIO_APPROVAL_AND_HORIZON_ARE_PRESERVED",
        """
        SELECT COUNT(*) FROM gold.fct_forecast_plan_lines line
        INNER JOIN gold.dim_planning_scenario scenario USING (planning_scenario_ref)
        WHERE line.period_id < scenario.forecast_start_period
           OR line.period_id > scenario.forecast_end_period
           OR line.approval_status <> scenario.approval_status
           OR line.planning_input_status <> scenario.planning_input_status
           OR line.actuals_reporting_version_ref <> scenario.actuals_reporting_version_ref
           OR line.assumption_basis_ref IS NULL
           OR line.reporting_currency <> 'GBP'
           OR (scenario.approval_status = 'APPROVED' AND NOT scenario.locked_flag)
           OR (scenario.approval_status <> 'APPROVED' AND scenario.locked_flag)
        """,
    ),
    (
        "B4_FORECAST_GRID_IS_COMPLETE_AND_SCENARIO_ISOLATED",
        """
        WITH expected AS (
            SELECT scenario.planning_scenario_ref,
                   COUNT(DISTINCT period.period_id) expected_period_count,
                   (SELECT COUNT(*) FROM gold.dim_department) expected_department_count,
                   (SELECT COUNT(DISTINCT account_id) FROM gold.fct_forecast_plan_lines) expected_account_count,
                   COUNT(DISTINCT period.period_id)
                   * (SELECT COUNT(*) FROM gold.dim_department)
                   * (SELECT COUNT(DISTINCT account_id) FROM gold.fct_forecast_plan_lines) expected_rows
            FROM gold.dim_planning_scenario scenario
            INNER JOIN gold.dim_period period
              ON period.period_id BETWEEN scenario.forecast_start_period AND scenario.forecast_end_period
            GROUP BY 1
        ), actual AS (
            SELECT planning_scenario_ref, COUNT(*) actual_rows,
                   COUNT(DISTINCT period_id) period_count,
                   COUNT(DISTINCT department_id) department_count,
                   COUNT(DISTINCT account_id) account_count,
                   COUNT(DISTINCT forecast_line_id) unique_line_count
            FROM gold.fct_forecast_plan_lines GROUP BY 1
        )
        SELECT COUNT(*) FROM expected INNER JOIN actual USING (planning_scenario_ref)
        WHERE expected_rows <> actual_rows OR actual_rows <> unique_line_count
           OR period_count <> expected_period_count
           OR department_count <> expected_department_count
           OR account_count <> expected_account_count
        """,
    ),
    (
        "B4_SCENARIOS_BIND_EXACT_RELIABLE_ATLAS_ACTUALS",
        """
        SELECT COUNT(*) FROM gold.dim_planning_scenario scenario
        LEFT JOIN gold.dim_reporting_version actuals
          ON scenario.actuals_reporting_version_ref = actuals.reporting_version_ref
        WHERE actuals.reporting_version_ref IS NULL
           OR scenario.cutover_period <> actuals.period_id
           OR actuals.scope_id <> 'NEXUS-GROUP'
           OR actuals.close_status <> 'HARD_CLOSED'
           OR actuals.reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
           OR actuals.reliability_purpose <> 'STATUTORY_ACTUALS'
           OR scenario.actuals_source_package_digest <> actuals.source_package_digest
           OR scenario.is_governed_pythia_snapshot
        """,
    ),
    (
        "B4_PLANNING_DIMENSION_ENDPOINTS_RESOLVE",
        """
        WITH failures AS (
            SELECT line.budget_line_id object_ref
            FROM gold.fct_budget_plan_lines line
            LEFT JOIN gold.dim_period period USING (period_id)
            LEFT JOIN gold.dim_department department USING (department_id)
            LEFT JOIN gold.dim_gl_account account USING (account_id)
            WHERE period.period_id IS NULL OR department.department_id IS NULL OR account.account_id IS NULL
            UNION ALL
            SELECT line.forecast_line_id
            FROM gold.fct_forecast_plan_lines line
            LEFT JOIN gold.dim_planning_scenario scenario USING (planning_scenario_ref)
            LEFT JOIN gold.dim_period period USING (period_id)
            LEFT JOIN gold.dim_department department USING (department_id)
            LEFT JOIN gold.dim_gl_account account USING (account_id)
            WHERE scenario.planning_scenario_ref IS NULL OR period.period_id IS NULL
               OR department.department_id IS NULL OR account.account_id IS NULL
        ) SELECT COUNT(*) FROM failures
        """,
    ),
    (
        "B4_VARIANCE_FORMULAS_REPLAY",
        """
        SELECT COUNT(*) FROM gold.fct_planning_variance_source
        WHERE actual_amount_minor - budget_amount_minor <> actual_vs_budget_variance_minor
           OR actual_amount_minor - forecast_amount_minor <> actual_vs_forecast_variance_minor
           OR forecast_amount_minor - budget_amount_minor <> forecast_vs_budget_variance_minor
        """,
    ),
    (
        "B4_VARIANCE_SOURCE_LINEAGE_REPLAYS",
        """
        WITH failures AS (
            SELECT variance.variance_line_id object_ref
            FROM gold.fct_planning_variance_source variance
            LEFT JOIN gold.fct_budget_plan_lines budget
              ON variance.source_budget_line_ref = budget.budget_line_id
            LEFT JOIN gold.fct_forecast_plan_lines forecast
              ON variance.source_forecast_line_ref = forecast.forecast_line_id
            WHERE (variance.source_budget_line_ref IS NOT NULL AND (
                       budget.budget_line_id IS NULL
                       OR variance.budget_amount_minor <> budget.reporting_amount_minor
                   ))
               OR (variance.source_forecast_line_ref IS NOT NULL AND (
                       forecast.forecast_line_id IS NULL
                       OR variance.forecast_amount_minor <> forecast.reporting_amount_minor
                       OR forecast.scenario_code <> 'BASE'
                   ))
               OR (variance.period_status = 'ACTUAL' AND variance.source_forecast_line_ref IS NOT NULL)
               OR (variance.period_status = 'FORECAST' AND variance.source_forecast_line_ref IS NULL)
        ) SELECT COUNT(*) FROM failures
        """,
    ),
    (
        "B4_HEADCOUNT_PLAN_PRESERVES_GOVERNANCE",
        """
        SELECT COUNT(*) FROM gold.fct_headcount_plan plan
        LEFT JOIN gold.dim_planning_scenario scenario USING (planning_scenario_ref)
        LEFT JOIN gold.dim_department department USING (department_id)
        LEFT JOIN gold.dim_region region USING (region_id)
        WHERE scenario.planning_scenario_ref IS NULL OR department.department_id IS NULL
           OR region.region_id IS NULL
           OR plan.planned_hire_date <= cast(scenario.cutover_period || '-01' as date)
           OR plan.salary_low_minor > plan.salary_mid_minor
           OR plan.salary_mid_minor > plan.salary_high_minor
           OR (plan.position_status = 'APPROVED'
               AND plan.planning_input_status <> 'APPROVED_AND_LOCKED_PLANNING_INPUT')
           OR (plan.position_status <> 'APPROVED'
               AND plan.planning_input_status <> 'PROPOSED_PLANNING_INPUT')
        """,
    ),
    (
        "B4_TRUTH_CLASSES_REMAIN_SEPARATE",
        """
        SELECT COUNT(*) FROM (
            SELECT variance_line_id object_ref
            FROM gold.fct_planning_variance_source
            WHERE is_statutory_actual OR value_authority <> 'MANAGEMENT_SOURCE_REPORT'
               OR reliability_status <> 'SOURCE_SYSTEM_REPORT_FOR_MANAGEMENT_VARIANCE'
            UNION ALL
            SELECT table_name
            FROM information_schema.columns
            WHERE table_schema = 'gold'
              AND table_name IN (
                  'dim_budget_version', 'dim_planning_scenario', 'fct_budget_plan_lines',
                  'fct_forecast_plan_lines', 'fct_planning_variance_source', 'fct_headcount_plan'
              )
              AND column_name IN ('business_event_ref', 'accounting_event_ref', 'journal_id')
        )
        """,
    ),
    (
        "Q_FINANCE_V4_REGISTRY_CLOSURE",
        """
        WITH count_failures AS (
            SELECT 'DATASETS' object_ref WHERE (SELECT COUNT(*) FROM governance.q_finance_v4_dataset_registry) <> 78
            UNION ALL SELECT 'RELATIONSHIPS' WHERE (SELECT COUNT(*) FROM governance.q_finance_v4_relationship_registry) <> 127
            UNION ALL SELECT 'MEASURES' WHERE (SELECT COUNT(*) FROM governance.q_finance_v4_measure_registry) <> 107
            UNION ALL SELECT 'LINEAGE' WHERE (SELECT COUNT(*) FROM governance.q_finance_v4_lineage_registry) <> 78
        ), relation_failures AS (
            SELECT dataset.dataset_id object_ref
            FROM governance.q_finance_v4_dataset_registry dataset
            LEFT JOIN information_schema.tables relation
              ON relation.table_schema = dataset.relation_schema
             AND relation.table_name = dataset.relation_name
            WHERE relation.table_name IS NULL OR dataset.registry_version <> 4
               OR dataset.finance_model_ref <> 'Q-FINANCE-B4@v1'
        ), endpoint_failures AS (
            SELECT relationship.relationship_id object_ref
            FROM governance.q_finance_v4_relationship_registry relationship
            LEFT JOIN governance.q_finance_v4_dataset_registry source
              ON relationship.from_dataset_id = source.dataset_id
            LEFT JOIN governance.q_finance_v4_dataset_registry target
              ON relationship.to_dataset_id = target.dataset_id
            WHERE source.dataset_id IS NULL OR target.dataset_id IS NULL
        ), measure_failures AS (
            SELECT measure.measure_id object_ref
            FROM governance.q_finance_v4_measure_registry measure
            INNER JOIN governance.q_finance_v4_dataset_registry dataset USING (dataset_id)
            LEFT JOIN information_schema.columns field
              ON field.table_schema = dataset.relation_schema
             AND field.table_name = dataset.relation_name
             AND field.column_name = measure.source_field
            WHERE field.column_name IS NULL
        ), lineage_failures AS (
            SELECT dataset.dataset_id object_ref
            FROM governance.q_finance_v4_dataset_registry dataset
            FULL OUTER JOIN governance.q_finance_v4_lineage_registry lineage USING (dataset_id)
            WHERE dataset.dataset_id IS NULL OR lineage.dataset_id IS NULL
        )
        SELECT COUNT(*) FROM (
            SELECT * FROM count_failures UNION ALL SELECT * FROM relation_failures
            UNION ALL SELECT * FROM endpoint_failures UNION ALL SELECT * FROM measure_failures
            UNION ALL SELECT * FROM lineage_failures
        )
        """,
    ),
)
