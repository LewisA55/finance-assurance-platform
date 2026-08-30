"""Execute and independently verify the governed Pythia D6 forecast."""


from __future__ import annotations

import csv
import io
import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from finance_assurance.exports.serialization import canonical_json_bytes, sha256_bytes
from finance_assurance.pythia.contracts import (
    PythiaBuildRequest,
    PythiaBuildResult,
    PythiaVerifyRequest,
    PythiaVerifyResult,
)

PYTHIA_REF = "PYTHIA-D6@v1"
MODEL_RUN_REF = "PYTHIA-D6-RUN-2026-06@v1"
ACTUALS_REPORTING_VERSION = "RV-NEXUS-GROUP-2026-06@v1"
SCENARIO_ORDER = ("BASE", "BULL", "BEAR")
NULL_TOKEN = r"\N"

ASSUMPTIONS: dict[str, dict[str, int]] = {
    "BASE": {
        "wacc_bps": 950,
        "terminal_growth_bps": 250,
        "tax_rate_bps": 2500,
        "cost_of_debt_bps": 700,
        "capex_as_revenue_bps": 600,
        "dso_days_bps": 8500,
        "dpo_days_bps": 12000,
        "deferred_revenue_as_revenue_bps": 7757,
        "prepayments_as_cash_cost_bps": 500,
        "accruals_as_cash_cost_bps": 300,
    },
    "BULL": {
        "wacc_bps": 900,
        "terminal_growth_bps": 300,
        "tax_rate_bps": 2500,
        "cost_of_debt_bps": 675,
        "capex_as_revenue_bps": 750,
        "dso_days_bps": 7800,
        "dpo_days_bps": 10500,
        "deferred_revenue_as_revenue_bps": 8200,
        "prepayments_as_cash_cost_bps": 500,
        "accruals_as_cash_cost_bps": 300,
    },
    "BEAR": {
        "wacc_bps": 1050,
        "terminal_growth_bps": 150,
        "tax_rate_bps": 2500,
        "cost_of_debt_bps": 750,
        "capex_as_revenue_bps": 450,
        "dso_days_bps": 10500,
        "dpo_days_bps": 14500,
        "deferred_revenue_as_revenue_bps": 7000,
        "prepayments_as_cash_cost_bps": 450,
        "accruals_as_cash_cost_bps": 250,
    },
}


class PythiaError(RuntimeError):
    """Raised when Pythia inputs or results cannot be proved."""


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PythiaError(f"cannot read governed JSON: {path}") from error
    if not isinstance(value, dict):
        raise PythiaError(f"governed JSON is not an object: {path}")
    return value


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload))


def _rows(path: Path) -> list[dict[str, str | None]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [
                {key: None if value == NULL_TOKEN else value for key, value in row.items()}
                for row in csv.DictReader(handle)
            ]
    except (OSError, csv.Error) as error:
        raise PythiaError(f"cannot read governed CSV: {path}") from error


def _integer(row: dict[str, str | None], name: str) -> int:
    value = row.get(name)
    if value is None:
        raise PythiaError(f"required integer {name} is null")
    try:
        return int(value)
    except ValueError as error:
        raise PythiaError(f"required integer {name} is malformed") from error


def _mul_bps(value: int, basis_points: int) -> int:
    return round(value * basis_points / 10_000)


def _ratio_bps(numerator: int, denominator: int) -> int | None:
    return None if denominator == 0 else round(numerator * 10_000 / denominator)


def _csv_bytes(rows: list[dict[str, object]]) -> bytes:
    if not rows:
        raise PythiaError("Pythia tables cannot be empty")
    stream = io.StringIO(newline="")
    names = list(rows[0])
    writer = csv.DictWriter(stream, fieldnames=names, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                name: NULL_TOKEN if row.get(name) is None else str(row.get(name))
                for name in names
            }
        )
    return stream.getvalue().encode("utf-8")


def _logical_digest(rows: list[dict[str, object]]) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {"contract_version": "pythia-d6-logical-table@v1", "rows": rows}
        )
    )


def _discount(value: int, month: int, wacc_bps: int) -> int:
    annual_rate = wacc_bps / 10_000
    return round(value / ((1 + annual_rate) ** (month / 12)))


class PythiaService:
    """Run Pythia from immutable C2 inputs without mutating Atlas actuals."""

    def _verify_delivery(self, delivery: Path, expected_digest: str) -> dict[str, Any]:
        checksum_path = delivery / "checksums.json"
        digest_path = delivery / "finance-delivery.digest"
        if not checksum_path.is_file() or not digest_path.is_file():
            raise PythiaError("C2 package seal is incomplete")
        checksum_bytes = checksum_path.read_bytes()
        digest = digest_path.read_text(encoding="ascii").strip()
        if digest != expected_digest or sha256_bytes(checksum_bytes) != digest:
            raise PythiaError("C2 detached digest differs")
        checksums = _json(checksum_path)
        declared = checksums.get("files")
        if not isinstance(declared, list):
            raise PythiaError("C2 checksum inventory is malformed")
        declared_paths = {str(row["path"]) for row in declared}
        physical = {
            path.relative_to(delivery).as_posix()
            for path in delivery.rglob("*")
            if path.is_file()
        }
        if physical != declared_paths | {"checksums.json", "finance-delivery.digest"}:
            raise PythiaError("C2 physical inventory differs from its seal")
        for row in declared:
            payload = (delivery / str(row["path"])).read_bytes()
            if len(payload) != int(row["byte_count"]):
                raise PythiaError(f"C2 byte count differs for {row['path']}")
            if sha256_bytes(payload) != row["sha256"]:
                raise PythiaError(f"C2 checksum differs for {row['path']}")
        manifest = _json(delivery / "delivery-manifest.json")
        if manifest.get("delivery_ref") != "Q-FINANCE-C2@v1":
            raise PythiaError("Pythia requires the exact Q-FINANCE-C2 authority")
        return manifest

    def _inputs(
        self,
        delivery: Path,
        manifest: dict[str, Any],
        finance_delivery_digest: str,
    ) -> tuple[
        list[dict[str, object]],
        dict[tuple[str, str], dict[str, int]],
        dict[str, int],
    ]:
        root = delivery / "csv"
        scenario_rows = _rows(root / "dim_planning_scenario.csv")
        if len(scenario_rows) != 3:
            raise PythiaError("Pythia requires exactly three Atlas scenarios")
        scenarios: list[dict[str, object]] = []
        for code in SCENARIO_ORDER:
            source = next((row for row in scenario_rows if row["scenario_code"] == code), None)
            if source is None:
                raise PythiaError(f"Atlas scenario {code} is missing")
            if (
                source["actuals_reporting_version_ref"] != ACTUALS_REPORTING_VERSION
                or source["cutover_period"] != "2026-06"
                or source["forecast_start_period"] != "2026-07"
                or source["forecast_end_period"] != "2036-06"
                or source["actuals_source_package_digest"]
                != manifest["source_data_digest"]
                or source["is_governed_pythia_snapshot"] != "false"
            ):
                raise PythiaError(f"Atlas scenario boundary differs for {code}")
            scenarios.append(
                {
                    "model_run_ref": MODEL_RUN_REF,
                    "planning_scenario_ref": source["planning_scenario_ref"],
                    "scenario_code": code,
                    "scenario_approval_status": source["approval_status"],
                    "scenario_locked_flag": source["locked_flag"] == "true",
                    "pythia_result_status": (
                        "APPROVED_FORECAST_RESULT"
                        if source["approval_status"] == "APPROVED"
                        and source["locked_flag"] == "true"
                        else "DRAFT_SCENARIO_RESULT"
                    ),
                    "actuals_reporting_version_ref": ACTUALS_REPORTING_VERSION,
                    "cutover_period": "2026-06",
                    "forecast_start_period": "2026-07",
                    "forecast_end_period": "2036-06",
                    "is_governed_pythia_snapshot": True,
                    "value_authority": "PYTHIA_GOVERNED_MODEL_RESULT",
                    "reliability_status": (
                        "RELIABLE_FOR_APPROVED_FORECAST"
                        if code == "BASE"
                        else "PROPOSED_SCENARIO_OUTPUT"
                    ),
                    "reliability_purpose": "PLANNING_SCENARIO_OUTPUT",
                    "finance_delivery_digest": finance_delivery_digest,
                    "source_data_digest": manifest["source_data_digest"],
                }
            )

        planning: dict[tuple[str, str], dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for row in _rows(root / "mart_model_planning_inputs.csv"):
            code = str(row["scenario_code"])
            period = str(row["period_id"])
            if code not in SCENARIO_ORDER:
                raise PythiaError("unexpected planning scenario")
            if row["is_governed_pythia_snapshot"] != "false":
                raise PythiaError("Atlas inputs must not claim Pythia result authority")
            planning[(code, period)][str(row["statement_line"])] += _integer(
                row, "forecast_amount_minor"
            )
        for code in SCENARIO_ORDER:
            months = sorted(period for scenario, period in planning if scenario == code)
            if len(months) != 120 or months[0] != "2026-07" or months[-1] != "2036-06":
                raise PythiaError(f"Atlas planning horizon differs for {code}")

        balance_rows = _rows(root / "mart_balance_sheet_monthly.csv")
        anchor_source = next(
            (
                row
                for row in balance_rows
                if row["period_id"] == "2026-06"
                and row["scope_id"] == "NEXUS-GROUP"
            ),
            None,
        )
        if anchor_source is None:
            raise PythiaError("June 2026 group balance-sheet anchor is missing")
        if anchor_source["reporting_version_ref"] != ACTUALS_REPORTING_VERSION:
            raise PythiaError("balance-sheet anchor reporting version differs")
        anchor_names = (
            "cash_minor",
            "accounts_receivable_minor",
            "prepayments_minor",
            "deferred_tax_asset_minor",
            "net_property_plant_equipment_minor",
            "accounts_payable_minor",
            "deferred_revenue_minor",
            "accrued_expenses_minor",
            "long_term_debt_minor",
            "lease_liabilities_minor",
            "share_capital_minor",
            "retained_earnings_minor",
            "total_assets_minor",
            "total_liabilities_minor",
            "total_equity_minor",
            "net_debt_minor",
            "balance_sheet_difference_minor",
        )
        anchor = {name: _integer(anchor_source, name) for name in anchor_names}
        if anchor["balance_sheet_difference_minor"] != 0:
            raise PythiaError("actuals anchor is not balanced")
        liquidity_rows = _rows(root / "mart_cash_flow_liquidity_monthly.csv")
        liquidity = next(
            (
                row
                for row in liquidity_rows
                if row["period_id"] == "2026-06" and row["scope_id"] == "NEXUS-GROUP"
            ),
            None,
        )
        if liquidity is None:
            raise PythiaError("June 2026 liquidity anchor is missing")
        anchor["undrawn_facility_minor"] = _integer(liquidity, "undrawn_facility_minor")
        return scenarios, planning, anchor

    def _execute(
        self,
        scenarios: list[dict[str, object]],
        planning: dict[tuple[str, str], dict[str, int]],
        anchor: dict[str, int],
        finance_delivery_digest: str,
        source_data_digest: str,
    ) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
        forecast_rows: list[dict[str, object]] = []
        valuation_rows: list[dict[str, object]] = []
        sensitivity_rows: list[dict[str, object]] = []
        scenario_by_code = {str(row["scenario_code"]): row for row in scenarios}
        for code in SCENARIO_ORDER:
            assumption = ASSUMPTIONS[code]
            periods = sorted(period for scenario, period in planning if scenario == code)
            cash = anchor["cash_minor"]
            ar = anchor["accounts_receivable_minor"]
            prepayments = anchor["prepayments_minor"]
            dta = anchor["deferred_tax_asset_minor"]
            net_ppe = anchor["net_property_plant_equipment_minor"]
            ap = anchor["accounts_payable_minor"]
            deferred_revenue = anchor["deferred_revenue_minor"]
            accruals = anchor["accrued_expenses_minor"]
            term_debt = anchor["long_term_debt_minor"]
            revolver = 0
            lease_liability = anchor["lease_liabilities_minor"]
            share_capital = anchor["share_capital_minor"]
            retained_earnings = anchor["retained_earnings_minor"]
            facility_limit = anchor["undrawn_facility_minor"]
            opening_known_assets = cash + ar + prepayments + dta + net_ppe
            static_assets = anchor["total_assets_minor"] - opening_known_assets
            opening_known_liabilities = (
                ap + deferred_revenue + accruals + term_debt + lease_liability
            )
            static_liabilities = anchor["total_liabilities_minor"] - opening_known_liabilities
            existing_asset_base = net_ppe
            capex_vintages: list[int] = []
            scenario_rows: list[dict[str, object]] = []
            cumulative_funding_gap = 0
            for month_index, period in enumerate(periods, start=1):
                plan = planning[(code, period)]
                subscription = plan["subscription_revenue"]
                services = plan["services_revenue"]
                revenue = subscription + services
                cogs = plan["cost_of_revenue"]
                research = plan["research_and_development"]
                sales = plan["sales_and_marketing"]
                admin = plan["general_and_administrative"]
                cash_costs = cogs + research + sales + admin
                gross_profit = revenue - cogs
                ebitda = revenue - cash_costs
                capex = _mul_bps(revenue, assumption["capex_as_revenue_bps"])
                existing_depreciation = (
                    min(net_ppe, round(existing_asset_base / 36))
                    if month_index <= 36
                    else 0
                )
                vintage_depreciation = sum(
                    round(value / 60) for value in capex_vintages[-59:]
                )
                depreciation = min(net_ppe + capex, existing_depreciation + vintage_depreciation)
                capex_vintages.append(capex)
                ebit = ebitda - depreciation
                interest = _mul_bps(
                    term_debt + revolver + lease_liability,
                    assumption["cost_of_debt_bps"],
                ) // 12
                profit_before_tax = ebit - interest
                tax = _mul_bps(max(profit_before_tax, 0), assumption["tax_rate_bps"])
                net_income = profit_before_tax - tax
                new_ar = round(revenue * assumption["dso_days_bps"] / 300_000)
                new_ap = round(cash_costs * assumption["dpo_days_bps"] / 300_000)
                new_deferred = _mul_bps(
                    revenue, assumption["deferred_revenue_as_revenue_bps"]
                )
                new_prepayments = _mul_bps(
                    cash_costs, assumption["prepayments_as_cash_cost_bps"]
                )
                new_accruals = _mul_bps(
                    cash_costs, assumption["accruals_as_cash_cost_bps"]
                )
                opening_wc = ar + prepayments - ap - deferred_revenue - accruals
                closing_wc = (
                    new_ar + new_prepayments - new_ap - new_deferred - new_accruals
                )
                working_capital_change = closing_wc - opening_wc
                operating_cash_flow = net_income + depreciation - working_capital_change
                investing_cash_flow = -capex
                scheduled_term_repayment = min(term_debt, 75_000_000)
                cash_before_facility = (
                    cash
                    + operating_cash_flow
                    + investing_cash_flow
                    - scheduled_term_repayment
                )
                minimum_cash = 100_000_000
                undrawn = facility_limit - revolver
                revolver_draw = min(max(minimum_cash - cash_before_facility, 0), undrawn)
                closing_cash = cash_before_facility + revolver_draw
                monthly_funding_gap = max(minimum_cash - closing_cash, 0)
                cumulative_funding_gap = max(cumulative_funding_gap, monthly_funding_gap)
                financing_cash_flow = revolver_draw - scheduled_term_repayment
                closing_term_debt = term_debt - scheduled_term_repayment
                closing_revolver = revolver + revolver_draw
                closing_net_ppe = net_ppe + capex - depreciation
                closing_retained_earnings = retained_earnings + net_income
                total_assets = (
                    closing_cash
                    + new_ar
                    + new_prepayments
                    + dta
                    + closing_net_ppe
                    + static_assets
                )
                total_liabilities = (
                    new_ap
                    + new_deferred
                    + new_accruals
                    + closing_term_debt
                    + closing_revolver
                    + lease_liability
                    + static_liabilities
                )
                total_equity = share_capital + closing_retained_earnings
                balance_difference = total_assets - total_liabilities - total_equity
                cash_rollforward_difference = closing_cash - (
                    cash
                    + operating_cash_flow
                    + investing_cash_flow
                    + financing_cash_flow
                )
                unlevered_fcf = (
                    ebit
                    - _mul_bps(max(ebit, 0), assumption["tax_rate_bps"])
                    + depreciation
                    - capex
                    - working_capital_change
                )
                row = {
                    "model_run_ref": MODEL_RUN_REF,
                    "planning_scenario_ref": scenario_by_code[code]["planning_scenario_ref"],
                    "scenario_code": code,
                    "scenario_approval_status": scenario_by_code[code]["scenario_approval_status"],
                    "pythia_result_status": scenario_by_code[code]["pythia_result_status"],
                    "period_id": period,
                    "forecast_month_number": month_index,
                    "currency": "GBP",
                    "subscription_revenue_minor": subscription,
                    "services_revenue_minor": services,
                    "revenue_minor": revenue,
                    "cost_of_revenue_minor": -cogs,
                    "gross_profit_minor": gross_profit,
                    "research_and_development_minor": -research,
                    "sales_and_marketing_minor": -sales,
                    "general_and_administrative_minor": -admin,
                    "ebitda_minor": ebitda,
                    "depreciation_and_amortisation_minor": -depreciation,
                    "ebit_minor": ebit,
                    "interest_expense_minor": -interest,
                    "profit_before_tax_minor": profit_before_tax,
                    "income_tax_expense_minor": -tax,
                    "net_income_minor": net_income,
                    "capex_minor": capex,
                    "change_in_operating_working_capital_minor": working_capital_change,
                    "unlevered_free_cash_flow_minor": unlevered_fcf,
                    "operating_cash_flow_minor": operating_cash_flow,
                    "investing_cash_flow_minor": investing_cash_flow,
                    "financing_cash_flow_minor": financing_cash_flow,
                    "opening_cash_minor": cash,
                    "closing_cash_minor": closing_cash,
                    "accounts_receivable_minor": new_ar,
                    "prepayments_minor": new_prepayments,
                    "net_property_plant_equipment_minor": closing_net_ppe,
                    "accounts_payable_minor": new_ap,
                    "deferred_revenue_minor": new_deferred,
                    "accrued_expenses_minor": new_accruals,
                    "term_debt_minor": closing_term_debt,
                    "revolver_debt_minor": closing_revolver,
                    "lease_liabilities_minor": lease_liability,
                    "net_debt_minor": closing_term_debt + closing_revolver + lease_liability - closing_cash,
                    "available_liquidity_minor": closing_cash + facility_limit - closing_revolver,
                    "monthly_funding_gap_minor": monthly_funding_gap,
                    "cumulative_funding_requirement_minor": cumulative_funding_gap,
                    "total_assets_minor": total_assets,
                    "total_liabilities_minor": total_liabilities,
                    "total_equity_minor": total_equity,
                    "balance_sheet_difference_minor": balance_difference,
                    "cash_rollforward_difference_minor": cash_rollforward_difference,
                    "gross_margin_bps": _ratio_bps(gross_profit, revenue),
                    "ebitda_margin_bps": _ratio_bps(ebitda, revenue),
                    "actuals_reporting_version_ref": ACTUALS_REPORTING_VERSION,
                    "assumption_set_ref": f"PYTHIA-{code}-ASSUMPTIONS@v1",
                    "value_authority": "PYTHIA_GOVERNED_MODEL_RESULT",
                    "reliability_status": scenario_by_code[code]["reliability_status"],
                    "reliability_purpose": "INTEGRATED_FORECAST_AND_LIQUIDITY",
                    "finance_delivery_digest": finance_delivery_digest,
                    "source_data_digest": source_data_digest,
                }
                scenario_rows.append(row)
                forecast_rows.append(row)
                cash = closing_cash
                ar = new_ar
                prepayments = new_prepayments
                net_ppe = closing_net_ppe
                ap = new_ap
                deferred_revenue = new_deferred
                accruals = new_accruals
                term_debt = closing_term_debt
                revolver = closing_revolver
                retained_earnings = closing_retained_earnings

            explicit = scenario_rows[:60]
            explicit_pv = sum(
                _discount(int(row["unlevered_free_cash_flow_minor"]), index, assumption["wacc_bps"])
                for index, row in enumerate(explicit, start=1)
            )
            terminal_fcf = sum(
                int(row["unlevered_free_cash_flow_minor"]) for row in explicit[-12:]
            )
            valuation_status = (
                "READY" if terminal_fcf > 0 else "BLOCKED_NEGATIVE_TERMINAL_FCF"
            )
            terminal_value = None
            pv_terminal = None
            if valuation_status == "READY":
                terminal_value = round(
                    terminal_fcf
                    * (10_000 + assumption["terminal_growth_bps"])
                    / (assumption["wacc_bps"] - assumption["terminal_growth_bps"])
                )
                pv_terminal = _discount(terminal_value, 60, assumption["wacc_bps"])
            enterprise_value = explicit_pv + (pv_terminal or 0)
            equity_value = enterprise_value - anchor["net_debt_minor"]
            first_gap = next(
                (
                    str(row["period_id"])
                    for row in scenario_rows
                    if int(row["monthly_funding_gap_minor"]) > 0
                ),
                None,
            )
            valuation_rows.append(
                {
                    "model_run_ref": MODEL_RUN_REF,
                    "scenario_code": code,
                    "scenario_approval_status": scenario_by_code[code]["scenario_approval_status"],
                    "pythia_result_status": scenario_by_code[code]["pythia_result_status"],
                    "valuation_status": valuation_status,
                    "explicit_forecast_months": 60,
                    "wacc_bps": assumption["wacc_bps"],
                    "terminal_growth_bps": assumption["terminal_growth_bps"],
                    "explicit_period_pv_minor": explicit_pv,
                    "terminal_year_fcf_minor": terminal_fcf,
                    "terminal_value_minor": terminal_value,
                    "present_value_terminal_minor": pv_terminal,
                    "enterprise_value_minor": enterprise_value,
                    "opening_net_debt_minor": anchor["net_debt_minor"],
                    "equity_value_minor": equity_value,
                    "diluted_shares": 100_000_000,
                    "implied_value_per_share_minor": round(equity_value / 100_000_000),
                    "five_year_revenue_minor": sum(int(row["revenue_minor"]) for row in explicit),
                    "five_year_ebitda_minor": sum(int(row["ebitda_minor"]) for row in explicit),
                    "five_year_unlevered_fcf_minor": sum(
                        int(row["unlevered_free_cash_flow_minor"]) for row in explicit
                    ),
                    "first_funding_gap_period": first_gap,
                    "peak_funding_requirement_minor": max(
                        int(row["cumulative_funding_requirement_minor"])
                        for row in scenario_rows
                    ),
                    "decision_status": (
                        "FUNDING_ACTION_REQUIRED" if first_gap else "WITHIN_FACILITY"
                    ),
                    "actuals_reporting_version_ref": ACTUALS_REPORTING_VERSION,
                    "assumption_set_ref": f"PYTHIA-{code}-ASSUMPTIONS@v1",
                    "value_authority": "PYTHIA_GOVERNED_VALUATION_RESULT",
                    "reliability_status": scenario_by_code[code]["reliability_status"],
                    "finance_delivery_digest": finance_delivery_digest,
                    "source_data_digest": source_data_digest,
                }
            )
            for wacc in range(assumption["wacc_bps"] - 100, assumption["wacc_bps"] + 101, 50):
                for growth in range(
                    assumption["terminal_growth_bps"] - 100,
                    assumption["terminal_growth_bps"] + 101,
                    50,
                ):
                    status = "READY" if terminal_fcf > 0 and wacc > growth else valuation_status
                    terminal = None
                    pv_term = None
                    ev = None
                    equity = None
                    per_share = None
                    if status == "READY":
                        terminal = round(terminal_fcf * (10_000 + growth) / (wacc - growth))
                        pv_term = _discount(terminal, 60, wacc)
                        pv_explicit = sum(
                            _discount(int(row["unlevered_free_cash_flow_minor"]), index, wacc)
                            for index, row in enumerate(explicit, start=1)
                        )
                        ev = pv_explicit + pv_term
                        equity = ev - anchor["net_debt_minor"]
                        per_share = round(equity / 100_000_000)
                    sensitivity_rows.append(
                        {
                            "model_run_ref": MODEL_RUN_REF,
                            "scenario_code": code,
                            "wacc_bps": wacc,
                            "terminal_growth_bps": growth,
                            "valuation_status": status,
                            "enterprise_value_minor": ev,
                            "equity_value_minor": equity,
                            "implied_value_per_share_minor": per_share,
                            "actuals_reporting_version_ref": ACTUALS_REPORTING_VERSION,
                            "value_authority": "PYTHIA_GOVERNED_DCF_SENSITIVITY",
                            "finance_delivery_digest": finance_delivery_digest,
                        }
                    )
        return forecast_rows, valuation_rows, sensitivity_rows

    def _controls(
        self,
        scenarios: list[dict[str, object]],
        forecast: list[dict[str, object]],
        valuations: list[dict[str, object]],
        sensitivity: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        checks = (
            ("PYT-D6-01", "SCENARIO_COUNT", len(scenarios), 3),
            ("PYT-D6-02", "FORECAST_POPULATION", len(forecast), 360),
            ("PYT-D6-03", "VALUATION_POPULATION", len(valuations), 3),
            ("PYT-D6-04", "SENSITIVITY_POPULATION", len(sensitivity), 75),
            (
                "PYT-D6-05",
                "BALANCE_SHEET_EQUATION",
                sum(int(row["balance_sheet_difference_minor"]) != 0 for row in forecast),
                0,
            ),
            (
                "PYT-D6-06",
                "CASH_FLOW_ROLLFORWARD",
                sum(int(row["cash_rollforward_difference_minor"]) != 0 for row in forecast),
                0,
            ),
            (
                "PYT-D6-07",
                "ACTUALS_SNAPSHOT_BINDING",
                sum(row["actuals_reporting_version_ref"] != ACTUALS_REPORTING_VERSION for row in forecast),
                0,
            ),
            (
                "PYT-D6-08",
                "PYTHIA_VALUE_AUTHORITY",
                sum(row["value_authority"] != "PYTHIA_GOVERNED_MODEL_RESULT" for row in forecast),
                0,
            ),
            (
                "PYT-D6-09",
                "APPROVAL_BOUNDARY",
                sum(
                    row["scenario_code"] != "BASE"
                    and row["pythia_result_status"] == "APPROVED_FORECAST_RESULT"
                    for row in forecast
                ),
                0,
            ),
            (
                "PYT-D6-10",
                "VALUATION_BLOCK_DISCLOSURE",
                sum(
                    row["terminal_year_fcf_minor"] <= 0
                    and row["valuation_status"] != "BLOCKED_NEGATIVE_TERMINAL_FCF"
                    for row in valuations
                ),
                0,
            ),
        )
        rows = []
        for order, (control_id, name, actual, expected) in enumerate(checks, start=1):
            rows.append(
                {
                    "control_order": order,
                    "control_id": control_id,
                    "control_name": name,
                    "actual_value": actual,
                    "expected_value": expected,
                    "result_status": "PASS" if actual == expected else "FAIL",
                    "first_failure_ref": None if actual == expected else control_id,
                    "model_run_ref": MODEL_RUN_REF,
                    "value_authority": "PYTHIA_EXECUTED_VALIDATOR",
                }
            )
        if any(row["result_status"] != "PASS" for row in rows):
            raise PythiaError("one or more Pythia execution controls failed")
        return rows

    def _write_table(
        self, staging: Path, name: str, rows: list[dict[str, object]]
    ) -> dict[str, object]:
        csv_path = staging / "csv" / f"{name}.csv"
        parquet_path = staging / "parquet" / f"{name}.parquet"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_bytes(_csv_bytes(rows))
        pq.write_table(pa.Table.from_pylist(rows), parquet_path, compression="zstd")
        return {
            "table_name": name,
            "row_count": len(rows),
            "csv_path": csv_path.relative_to(staging).as_posix(),
            "parquet_path": parquet_path.relative_to(staging).as_posix(),
            "logical_digest": _logical_digest(rows),
        }

    def _seal(self, staging: Path) -> str:
        files = []
        for path in sorted(item for item in staging.rglob("*") if item.is_file()):
            if path.name in {"checksums.json", "pythia.digest"}:
                continue
            payload = path.read_bytes()
            files.append(
                {
                    "path": path.relative_to(staging).as_posix(),
                    "byte_count": len(payload),
                    "sha256": sha256_bytes(payload),
                }
            )
        checksums = {"contract_version": "pythia-d6-checksums@v1", "files": files}
        checksum_bytes = canonical_json_bytes(checksums)
        digest = sha256_bytes(checksum_bytes)
        (staging / "checksums.json").write_bytes(checksum_bytes)
        (staging / "pythia.digest").write_text(
            f"{digest}\n", encoding="ascii", newline="\n"
        )
        return digest

    def _verify_seal(self, package: Path, expected_digest: str) -> int:
        checksum_path = package / "checksums.json"
        digest_path = package / "pythia.digest"
        if not checksum_path.is_file() or not digest_path.is_file():
            raise PythiaError("Pythia package seal is incomplete")
        checksum_bytes = checksum_path.read_bytes()
        digest = digest_path.read_text(encoding="ascii").strip()
        if digest != expected_digest or sha256_bytes(checksum_bytes) != digest:
            raise PythiaError("Pythia detached digest differs")
        checksums = _json(checksum_path)
        declared = checksums.get("files")
        if not isinstance(declared, list):
            raise PythiaError("Pythia checksum inventory is malformed")
        declared_paths = {str(row["path"]) for row in declared}
        physical = {
            path.relative_to(package).as_posix()
            for path in package.rglob("*")
            if path.is_file()
        }
        if physical != declared_paths | {"checksums.json", "pythia.digest"}:
            raise PythiaError("Pythia physical inventory differs from its seal")
        for row in declared:
            payload = (package / str(row["path"])).read_bytes()
            if len(payload) != int(row["byte_count"]):
                raise PythiaError(f"Pythia byte count differs for {row['path']}")
            if sha256_bytes(payload) != row["sha256"]:
                raise PythiaError(f"Pythia checksum differs for {row['path']}")
        return len(declared)

    def build(self, request: PythiaBuildRequest) -> PythiaBuildResult:
        delivery = request.finance_delivery_path.resolve()
        output = request.output_path.resolve()
        if output.exists():
            raise PythiaError("Pythia output must not already exist")
        staging = output.parent / f".{output.name}.building"
        if staging.exists():
            raise PythiaError("Pythia staging path already exists")
        manifest = self._verify_delivery(
            delivery, request.expected_finance_delivery_digest
        )
        scenarios, planning, anchor = self._inputs(
            delivery,
            manifest,
            request.expected_finance_delivery_digest,
        )
        forecast, valuations, sensitivity = self._execute(
            scenarios,
            planning,
            anchor,
            request.expected_finance_delivery_digest,
            str(manifest["source_data_digest"]),
        )
        controls = self._controls(scenarios, forecast, valuations, sensitivity)
        try:
            staging.mkdir(parents=True)
            tables = [
                self._write_table(staging, "dim_pythia_scenario", scenarios),
                self._write_table(staging, "fct_pythia_forecast_monthly", forecast),
                self._write_table(staging, "mart_pythia_valuation", valuations),
                self._write_table(staging, "mart_pythia_dcf_sensitivity", sensitivity),
                self._write_table(staging, "mart_pythia_execution_controls", controls),
            ]
            assumptions = {
                "contract_version": "pythia-d6-assumption-registry@v1",
                "model_run_ref": MODEL_RUN_REF,
                "actuals_reporting_version_ref": ACTUALS_REPORTING_VERSION,
                "rows": [
                    {
                        "scenario_code": code,
                        "assumption_set_ref": f"PYTHIA-{code}-ASSUMPTIONS@v1",
                        **ASSUMPTIONS[code],
                        "minimum_cash_minor": 100_000_000,
                        "term_debt_monthly_amortisation_minor": 75_000_000,
                        "existing_asset_remaining_life_months": 36,
                        "new_capex_useful_life_months": 60,
                        "diluted_shares": 100_000_000,
                        "assumption_authority": "PYTHIA_MODEL_POLICY",
                    }
                    for code in SCENARIO_ORDER
                ],
            }
            _write_json(staging / "metadata" / "assumptions.json", assumptions)
            _write_json(
                staging / "metadata" / "lineage.json",
                {
                    "contract_version": "pythia-d6-lineage@v1",
                    "model_run_ref": MODEL_RUN_REF,
                    "source_finance_delivery_ref": manifest["delivery_ref"],
                    "source_finance_delivery_digest": request.expected_finance_delivery_digest,
                    "source_data_ref": manifest["source_data_ref"],
                    "source_data_digest": manifest["source_data_digest"],
                    "actuals_reporting_version_ref": ACTUALS_REPORTING_VERSION,
                    "causal_path": [
                        "Q-FINANCE-C2 governed actuals and planning inputs",
                        "PYTHIA-D6 versioned assumption set",
                        "integrated forecast and liquidity engine",
                        "DCF readiness and sensitivity engine",
                        "sealed Pythia result tables",
                    ],
                },
            )
            package_manifest = {
                "contract_version": "pythia-d6-package@v1",
                "status": "PUBLISHED",
                "pythia_ref": PYTHIA_REF,
                "model_run_ref": MODEL_RUN_REF,
                "built_at": request.built_at,
                "producer_release": request.producer_release,
                "finance_delivery_ref": manifest["delivery_ref"],
                "finance_delivery_digest": request.expected_finance_delivery_digest,
                "finance_model_ref": manifest["finance_model_ref"],
                "finance_model_digest": manifest["finance_model_digest"],
                "source_data_ref": manifest["source_data_ref"],
                "source_data_digest": manifest["source_data_digest"],
                "actuals_reporting_version_ref": ACTUALS_REPORTING_VERSION,
                "scenario_count": len(scenarios),
                "forecast_month_count": 120,
                "control_count": len(controls),
                "tables": tables,
            }
            _write_json(staging / "pythia-manifest.json", package_manifest)
            (staging / "README.md").write_text(
                "# PYTHIA-D6 governed model results\n\n"
                "This sealed package consumes Q-FINANCE-C2 actuals and planning inputs. "
                "It publishes integrated forecast, liquidity and valuation-readiness results. "
                "Atlas actuals remain immutable. Draft BULL and BEAR inputs remain draft outputs. "
                "A negative terminal free cash flow blocks terminal-value publication rather than "
                "manufacturing a valuation.\n",
                encoding="ascii",
                newline="\n",
            )
            digest = self._seal(staging)
            staging.replace(output)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        return PythiaBuildResult(
            contract_version="pythia-d6-build-result@v1",
            status="PUBLISHED",
            pythia_ref=PYTHIA_REF,
            output_path=output,
            pythia_digest=digest,
            finance_delivery_digest=request.expected_finance_delivery_digest,
            actuals_reporting_version_ref=ACTUALS_REPORTING_VERSION,
            scenario_count=len(scenarios),
            forecast_month_count=120,
            forecast_row_count=len(forecast),
            valuation_row_count=len(valuations),
            sensitivity_row_count=len(sensitivity),
            control_count=len(controls),
        )

    def verify(self, request: PythiaVerifyRequest) -> PythiaVerifyResult:
        package = request.package_path.resolve()
        delivery = request.finance_delivery_path.resolve()
        self._verify_delivery(delivery, request.expected_finance_delivery_digest)
        checked_files = self._verify_seal(package, request.expected_pythia_digest)
        manifest = _json(package / "pythia-manifest.json")
        if (
            manifest.get("pythia_ref") != PYTHIA_REF
            or manifest.get("finance_delivery_digest")
            != request.expected_finance_delivery_digest
            or manifest.get("actuals_reporting_version_ref")
            != ACTUALS_REPORTING_VERSION
        ):
            raise PythiaError("Pythia manifest authority differs")
        scenarios = _rows(package / "csv" / "dim_pythia_scenario.csv")
        forecast = _rows(package / "csv" / "fct_pythia_forecast_monthly.csv")
        controls = _rows(package / "csv" / "mart_pythia_execution_controls.csv")
        if len(scenarios) != 3 or len(forecast) != 360 or len(controls) != 10:
            raise PythiaError("Pythia replay population differs")
        if any(row["result_status"] != "PASS" for row in controls):
            raise PythiaError("Pythia replay controls are not green")
        if any(_integer(row, "balance_sheet_difference_minor") != 0 for row in forecast):
            raise PythiaError("Pythia replay balance sheet does not balance")
        if any(_integer(row, "cash_rollforward_difference_minor") != 0 for row in forecast):
            raise PythiaError("Pythia replay cash flow does not reconcile")
        return PythiaVerifyResult(
            contract_version="pythia-d6-verify-result@v1",
            status="VERIFIED",
            pythia_ref=PYTHIA_REF,
            pythia_digest=request.expected_pythia_digest,
            finance_delivery_digest=request.expected_finance_delivery_digest,
            checked_file_count=checked_files,
            checked_scenario_count=len(scenarios),
            checked_forecast_row_count=len(forecast),
            checked_control_count=len(controls),
        )
