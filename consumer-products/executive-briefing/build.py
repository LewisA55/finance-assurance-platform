"""Build the June 2026 executive deck from the sealed C2 delivery."""
import argparse
import calendar
import html
import json
from datetime import date, timedelta
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from itertools import pairwise
from pathlib import Path
from string import Template

import charts
import duckdb

from finance_assurance.finance_delivery.service import FinanceDeliveryService

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_DELIVERY = ROOT / "build/finance-delivery/Q-FINANCE-C2-V1"
DEFAULT_OUTPUT = HERE / "exports/output/pdf/Nexus-June-2026-Executive-Deck.html"
DELIVERY_REF = "Q-FINANCE-C2@v1"
DELIVERY_SEAL = "sha256:7538132e08ea2b7e8c20f339db10e6c138cd2a08c71c4708c47c378d7c1b0141"
VERSION = "RV-NEXUS-GROUP-2026-06@v1"
UK_VERSION = "RV-NEXUS-UK-2026-06@v1"
PERIOD = "2026-06"
PRIOR = "2026-05"
YEAR_AGO = "2025-06"
WINDOW = "2025-07"
CLOSE_DATE = date(2026, 6, 30)
QUARTER_END = date(2026, 9, 30)
GROUP = "NEXUS-GROUP"
POLICY_PATH = HERE.parent / "power-bi/custom-visuals/tie-out-panel/policy.json"
CASH = "mart_cash_flow_liquidity_monthly"
DEBT = "mart_capital_structure_monthly"
FIN = "mart_financial_performance_monthly"
SAAS = "mart_saas_performance_monthly"
CFO = "mart_executive_cfo_command_center"
WC = "mart_ap_working_capital_monthly"
BALANCE = "mart_balance_sheet_monthly"
SCHEDULES = "mart_model_capital_schedules"
EN_DASH, MINUS = "\u2013", "\u2212"
REFERENCES = {key: f"E{number}" for number, key in enumerate(
    ("e-liquidity", "e-cover", "e-facility", "e-movement", "e-performance", "e-recurring",
     "e-close", "e-controls", "e-working-capital"), 1
)}
# Proposed deadlines, in working days after the close. The review must land
# well before the earliest date on which cash alone runs out.
TREASURY_DAYS, FPA_DAYS, REVIEW_DAYS = 5, 8, 10
SLIDES = 12


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def pounds(minor, abbreviated=False):
    divisor = 100_000_000 if abbreviated else 100
    unit = "m" if abbreviated else ""
    value = f"£{Decimal(abs(minor)) / divisor:,.2f}{unit}"
    return f"({value})" if minor < 0 else value


def thousands(minor):
    return f"£{Decimal(abs(minor)) / 100_000:.1f}k"


def signed(minor):
    """An abbreviated change with an explicit sign, such as +£0.19m."""
    sign = "+" if minor > 0 else MINUS if minor < 0 else ""
    return sign + pounds(abs(minor), True)


def millions(minor):
    return float(Decimal(minor) / 100_000_000)


def rounded(value, places="0.1"):
    return Decimal(value).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def share(part, whole, places="0.01"):
    return rounded(Decimal(part) * 100 / whole, places)


def minus(text):
    return str(text).replace("-", MINUS)


def percent(bps):
    return f"{Decimal(bps) / 100:.2f}%"


def working_days_after(start, count):
    day = start
    while count:
        day += timedelta(days=1)
        if day.weekday() < 5:
            count -= 1
    return day


def long_date(day):
    return f"{day.day} {day:%B}"


def month_name(period):
    return f"{date(int(period[:4]), int(period[5:]), 1):%B %Y}"


def days_in(period):
    return calendar.monthrange(int(period[:4]), int(period[5:]))[1]


def periods(first, count):
    year, month = int(first[:4]), int(first[5:])
    out = []
    for _ in range(count):
        out.append(f"{year}-{month:02}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return out


def table_row(key, figure, value, source, scope="June Group"):
    row_id = f' id="{key}"' if key else ""
    marker = f'<span class="trace-ref">{REFERENCES[key]}</span>' if key else ""
    cells = "".join(f"<td>{html.escape(v)}</td>" for v in (value, source, scope))
    return f'<tr{row_id}><th scope="row">{marker}{html.escape(figure)}</th>{cells}</tr>'


def read(db, delivery, relation, where, params=()):
    path = delivery / "powerbi/parquet" / (relation + ".parquet")
    cursor = db.execute(f"select * from read_parquet(?) where {where}", [str(path), *params])
    names = [entry[0] for entry in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def group_version(period):
    return f"RV-{GROUP}-{period}@v1"


def group(db, delivery, relation, first=PERIOD):
    rows = read(db, delivery, relation, "scope_id = ? and period_id between ? and ? order by period_id",
                [GROUP, first, PERIOD])
    require(all(r.get("currency", "GBP") == "GBP" and r["reporting_version_ref"] == group_version(r["period_id"])
                for r in rows), f"Unexpected reporting version or currency in {relation}")
    return rows


def assurance(db, delivery):
    policy = load(POLICY_PATH)
    controls = load(delivery / "metadata/reconciliation.json")["rows"]
    readiness = read(db, delivery, "mart_model_readiness_controls", "true")
    source_bindings = policy["sources"]["C2_DELIVERY"]["sourceBindingIds"]
    parity = sum(r["control_id"].startswith("C2-TABLE-") for r in controls)
    bindings = sum(r["control_id"] in source_bindings for r in controls)
    replayed = len(controls) - parity - bindings
    require(len(controls) == 36 and len(readiness) == 15 and (parity, bindings, replayed) == (29, 2, 5)
            and all(r["status"] == "PASS" for r in controls)
            and all(r["result_status"] == "PASS" for r in readiness),
            "Delivery-wide control classifications or outcomes differ")

    observed, rules = {}, []
    for rule in policy["observations"]:
        field = rule["field"]
        limit = rule["expected"] if rule["expected"] is not None else 0
        hits = read(db, delivery, rule["table"], f"period_id = ? and {field} is not null and {field} <> ?",
                    [PERIOD, limit])
        if rule["class"] == "CONTROL":
            require(not hits, f"June contains control hits for {rule['rule']}")
            # Slide 8 says no registered control tests payment timing.
            require(rule["metric"].endswith("_DIFFERENCE") or rule["metric"] == "GHOST_HEADCOUNT",
                    f"Review the payment-timing statement against {rule['rule']}")
            rules.append(rule["label"])
        else:
            require(rule["expected"] is None and rule["operator"] is None,
                    f"Exposure {rule['rule']} has an assessment threshold")
            observed[rule["metric"]] = hits
    require(len(rules) == 4, "The deck names four registered control rules")
    unapplied = observed["UNAPPLIED_CASH"]
    overdue = observed["OVERDUE_AP_BPS"]
    # Only the UK and Group rows carry unapplied cash, so the US holds none and
    # the Group figure is wholly UK.
    require(len(unapplied) == 2 and len(overdue) == 1
            and {r["reporting_version_ref"] for r in unapplied} == {VERSION, UK_VERSION}
            and unapplied[0]["unapplied_cash_minor"] == unapplied[1]["unapplied_cash_minor"]
            and overdue[0]["reporting_version_ref"] == VERSION, "Exposure scopes or values differ")
    return unapplied[0]["unapplied_cash_minor"], overdue[0]["overdue_ap_bps"], policy["version"], rules


def evidence(db, delivery):
    v = {}
    history = group(db, delivery, CASH, "2021-01")
    debt_rows = group(db, delivery, DEBT, "2021-01")
    require(len(history) == len(debt_rows) == 66
            and [r["period_id"] for r in history] == [r["period_id"] for r in debt_rows],
            "Expected 66 months of Group cash and debt")
    year = history[-13:]
    half = history[-6:]
    prior, cash = history[-2:]
    fin = group(db, delivery, FIN, WINDOW)
    cfo = group(db, delivery, CFO, YEAR_AGO)
    balance = group(db, delivery, BALANCE, "2026-01")
    version, = group(db, delivery, "dim_reporting_version")
    working = read(db, delivery, WC, "period_id between ? and ? order by period_id", [YEAR_AGO, PERIOD])
    require([r["period_id"] for r in year] == periods(YEAR_AGO, 13)
            and [r["period_id"] for r in fin] == periods(WINDOW, 12)
            and [r["period_id"] for r in cfo] == periods(YEAR_AGO, 13)
            and [r["period_id"] for r in working] == periods(YEAR_AGO, 13)
            and [r["period_id"] for r in balance] == periods("2026-01", 6),
            "Expected complete monthly series")
    require(all(r["reporting_version_ref"] == group_version(r["period_id"]) and r["currency"] == "GBP"
                for r in working), "Working capital is not the Group version")
    require(version["close_status"] == "HARD_CLOSED" and version["statement_status"] == "PUBLISHED",
            "The June Group version must be hard-closed and published")
    digest = cash["source_package_digest"]
    require(all(r["source_package_digest"] == digest
                for r in [*history, *debt_rows, *fin, *cfo, *balance, *working, version]), "Source identities differ")

    # ---------------------------------------------------------- liquidity ---
    closing = cash["closing_cash_minor"]
    facility = cash["undrawn_facility_minor"]
    total = cash["available_liquidity_minor"]
    outflow = -cash["net_change_in_cash_minor"]
    require(closing > 0 and facility > 0 and closing + facility == total, "Liquidity split does not tie")
    require(cash["opening_cash_minor"] - outflow == closing and -sum(cash[f] for f in (
        "operating_cash_flow_minor", "investing_cash_flow_minor", "financing_cash_flow_minor",
        "fx_and_other_movement_minor")) == outflow and outflow > 0, "June cash movements do not tie")
    june_cfo = cfo[-1]
    require(fin[-1]["revenue_minor"] == june_cfo["revenue_minor"]
            and fin[-1]["ebitda_minor"] == june_cfo["ebitda_minor"]
            and closing == june_cfo["closing_cash_minor"] and total == june_cfo["available_liquidity_minor"],
            "Executive mart values do not tie")
    cash_share = share(closing, total, "1")
    v.update(cash=pounds(closing, True), facility=pounds(facility, True), total=pounds(total, True),
             outflow=pounds(outflow, True), cash_share=f"{cash_share}%", undrawn_share=f"{100 - cash_share}%",
             cash_width=f"{Decimal(closing) * 100 / total:.4f}%",
             cash_year_ago=pounds(year[0]["closing_cash_minor"], True))

    # -------------------------------------------------------------- cover ---
    # Observed rates with repayments included: June alone and the day-weighted
    # January to June average. A sensitivity, not a forecast.
    half_outflow = -sum(r["net_change_in_cash_minor"] for r in half)
    half_days = sum(days_in(r["period_id"]) for r in half)
    june_days = days_in(PERIOD)
    june_cover = Decimal(closing) * june_days / outflow
    half_cover = Decimal(closing) * half_days / half_outflow
    # Ordered shortest first: the June rate includes a whole quarterly repayment.
    cover_days = [june_cover, half_cover]
    weeks = [rounded(days / 7) for days in cover_days]
    runs_out = [CLOSE_DATE + timedelta(days=int(days)) for days in cover_days]
    require(june_cover < half_cover and all(d.month == 8 for d in runs_out) and runs_out[-1] < QUARTER_END,
            "The deck dates the cash-only window in August, before the quarter-end")
    to_quarter_end = (QUARTER_END - CLOSE_DATE).days
    v.update(cover_range=f"{weeks[0]}{EN_DASH}{weeks[1]}",
             cover_dates=f"{runs_out[0].day}{EN_DASH}{runs_out[1].day} {runs_out[1]:%B}",
             meter_low=f"{june_cover * 100 / to_quarter_end:.2f}%",
             meter_high=f"{(half_cover - june_cover) * 100 / to_quarter_end:.2f}%",
             quarter_weeks=f"{rounded(Decimal(to_quarter_end) / 7)}")

    # ----------------------------------------------------------- facility ---
    first, last = debt_rows[0], debt_rows[-1]
    limits = {r["closing_debt_minor"] + r["undrawn_facility_minor"] for r in debt_rows}
    draws = [r for r in debt_rows if r["debt_drawdown_minor"]]
    require(len(limits) == 1 and draws == [first] and first["opening_debt_minor"] == 0,
            "Expected one constant facility limit with a single opening draw")
    limit, = limits
    require(last["undrawn_facility_minor"] == facility and last["closing_debt_minor"] == cash["closing_debt_minor"],
            "Debt and cash marts disagree on the facility")
    # Slide 4 says undrawn capacity rose in step with each repayment.
    require(all(row["undrawn_facility_minor"] - before["undrawn_facility_minor"] == row["debt_repayment_minor"]
                == before["closing_debt_minor"] - row["closing_debt_minor"]
                for before, row in pairwise(debt_rows)),
            "Headroom does not move in step with repayments")
    payment = last["debt_repayment_minor"]
    repayments = [r for r in debt_rows if r["debt_repayment_minor"]]
    quarter_ends = [r["period_id"] for r in debt_rows if r["period_id"] >= "2023-03"
                    and r["period_id"].endswith(("-03", "-06", "-09", "-12"))]
    restored = sum(r["debt_repayment_minor"] for r in repayments)
    require(len(repayments) == 14 and [r["period_id"] for r in repayments] == quarter_ends
            and all(r["debt_repayment_minor"] == payment for r in repayments)
            and facility - first["undrawn_facility_minor"] == restored,
            "The repayment history does not explain the restored headroom")
    # Two instruments sit behind the combined limit: a term loan that carries
    # all drawn debt and a revolving credit facility that has never been drawn.
    instruments = read(db, delivery, SCHEDULES, "schedule_domain = 'DEBT' order by period_id")
    term = [r for r in instruments if r["schedule_class"] == "TERM_LOAN"]
    revolver = [r for r in instruments if r["schedule_class"] == "REVOLVING_CREDIT_FACILITY"]
    require(len(term) == len(revolver) == len(debt_rows) and len(instruments) == 2 * len(debt_rows)
            and all(r["source_package_digest"] == digest and r["currency"] == "GBP"
                    and r["reporting_version_ref"] == f"RV-NEXUS-UK-{r['period_id']}@v1" for r in instruments)
            and all(r["opening_balance_minor"] == r["additions_minor"] == r["reductions_minor"]
                    == r["closing_balance_minor"] == 0 for r in revolver)
            and [(r["period_id"], r["additions_minor"], r["reductions_minor"], r["closing_balance_minor"]) for r in term]
            == [(r["period_id"], r["debt_drawdown_minor"], r["debt_repayment_minor"], r["closing_debt_minor"])
                for r in debt_rows],
            "Slide 4 says a term loan carries all drawn debt and the revolver has never been drawn")
    revolver_undrawn = first["undrawn_facility_minor"]
    quarters =[(r["period_id"], millions(r["closing_debt_minor"]), millions(r["undrawn_facility_minor"]))
                for r in debt_rows if r["period_id"].endswith(("-03", "-06", "-09", "-12"))]
    v.update(payment=pounds(payment, True), restored=pounds(restored, True),
             first_draw=pounds(first["debt_drawdown_minor"], True), closing_debt=pounds(last["closing_debt_minor"], True),
             revolver_undrawn=pounds(revolver_undrawn, True),
             first_repayment=month_name(repayments[0]["period_id"]), repayment_count=str(len(repayments)),
             chart_facility=charts.facility(quarters, millions(limit), {
                 "limit": pounds(limit, True), "limit_note": ["combined instrument", "limits"],
                 "undrawn": pounds(facility, True), "drawn": pounds(last["closing_debt_minor"], True),
                 "aria": f"Drawn term loan and undrawn capacity at each quarter-end, 2021 to 2026, "
                         f"against combined instrument limits of {pounds(limit, True)}."}))

    # ----------------------------------------------------- what changed ---
    require(all(r["fx_and_other_movement_minor"] == 0 for r in (prior, cash))
            and prior["financing_cash_flow_minor"] - cash["financing_cash_flow_minor"] == payment
            and not any(r["debt_repayment_minor"] for r in debt_rows if r["period_id"] == PRIOR)
            and cash["investing_cash_flow_minor"] == 0 and prior["investing_cash_flow_minor"] < 0
            and cash["operating_cash_flow_minor"] < 0 and prior["operating_cash_flow_minor"] < 0,
            "The June change is no longer explained by repayment, operating and investing flows")
    prior_outflow = -prior["net_change_in_cash_minor"]
    operating = -cash["operating_cash_flow_minor"]
    prior_operating = -prior["operating_cash_flow_minor"]
    operating_delta = operating - prior_operating
    investing_delta = prior["investing_cash_flow_minor"]
    offset = -(operating_delta + investing_delta)
    require(operating_delta > 0 and offset > 0 and outflow - prior_outflow == payment - offset,
            "The May to June outflow bridge does not tie")
    running = [prior_outflow, prior_outflow + payment, prior_outflow + payment + operating_delta, outflow]
    steps = [
        (["May", "net outflow"], "total", 0, millions(running[0]), pounds(prior_outflow, True)),
        (["Quarterly", "repayment"], "step", millions(running[0]), millions(running[1]), signed(payment)),
        (["Operating", "outflow"], "step", millions(running[1]), millions(running[2]), signed(operating_delta)),
        (["Investing", "outflow"], "step", millions(running[2]), millions(running[3]), signed(investing_delta)),
        (["June", "net outflow"], "total", 0, millions(outflow), pounds(outflow, True)),
    ]
    ceiling = float((Decimal(max(running)) / 100_000_000).to_integral_value(ROUND_CEILING))
    v.update(outflow_delta=pounds(outflow - prior_outflow, True), prior_outflow=pounds(prior_outflow, True),
             operating=pounds(operating, True), prior_operating=pounds(prior_operating, True),
             operating_delta=pounds(operating_delta, True), may_investing=pounds(-investing_delta, True),
             offset=pounds(offset, True),
             chart_bridge=charts.waterfall(steps, ceiling, "Net outflow bridge from May to June."))

    # -------------------------------------------------------- performance ---
    revenue = [r["revenue_minor"] for r in fin]
    ebitda = [r["ebitda_minor"] for r in fin]
    require(all(e < 0 for e in ebitda) and (max(revenue) - min(revenue)) * 100 < 2 * min(revenue),
            "Slide 6 says revenue is broadly flat and EBITDA negative in every month")
    revenue_change = share(revenue[-1] - revenue[-2], revenue[-2], "0.1")
    require(abs(revenue_change) < Decimal("0.5"), "The deck describes revenue as flat on May")
    losses = sorted(-e for e in ebitda)
    v.update(revenue=pounds(revenue[-1], True), revenue_change=minus(f"{revenue_change}%"),
             ebitda=pounds(ebitda[-1], True), ebitda_margin=minus(f"{share(ebitda[-1], revenue[-1], '0.1')}%"),
             ebitda_low=pounds(losses[0], True), ebitda_high=pounds(losses[-1], True),
             ltm_revenue=pounds(sum(revenue), True), ltm_ebitda=pounds(sum(ebitda), True),
             revenue_year_change=minus(f"{share(revenue[-1] - revenue[0], revenue[0], '0.1')}%"),
             spark_revenue=charts.sparkline([millions(x) for x in revenue], "Monthly revenue, July 2025 to June 2026."),
             spark_ebitda=charts.sparkline([millions(x) for x in ebitda], "Monthly EBITDA, July 2025 to June 2026."),
             chart_pl=charts.diverging([r["period_id"] for r in fin], [millions(x) for x in revenue],
                                       [millions(x) for x in ebitda], {
                                           "revenue_first": pounds(revenue[0], True),
                                           "revenue_last": pounds(revenue[-1], True),
                                           "ebitda_first": pounds(ebitda[0], True),
                                           "ebitda_last": pounds(ebitda[-1], True),
                                           "aria": "Monthly revenue and EBITDA, July 2025 to June 2026."}))

    # ---------------------------------------------------------- recurring ---
    saas = read(db, delivery, SAAS, "period_id between ? and ? and currency = ? order by period_id",
                [WINDOW, PERIOD, "GBP"])
    require(len(saas) == 720 and all(r["reporting_version_ref"] == group_version(r["period_id"]) for r in saas),
            "Expected 60 Group SaaS components in each of 12 months")
    monthly = {p: [r for r in saas if r["period_id"] == p] for p in periods(WINDOW, 12)}
    require(all(r[f] == 0 for r in saas for f in ("new_mrr_minor", "expansion_mrr_minor", "contraction_mrr_minor")),
            "Slide 7 notes that churn and FX are the only MRR movements delivered")
    churn = [-sum(r["churn_mrr_minor"] for r in rows) for rows in monthly.values()]
    june = monthly[PERIOD]
    opening_mrr = sum(r["beginning_mrr_minor"] for r in june)
    retained_mrr = opening_mrr + sum(r[f] for r in june for f in (
        "expansion_mrr_minor", "contraction_mrr_minor", "churn_mrr_minor"))
    nrr = (Decimal(retained_mrr) * 10_000 / opening_mrr).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    arr = [r["ending_arr_minor"] for r in cfo]
    nrr_series = [r["net_revenue_retention_bps"] for r in cfo[1:]]
    require(nrr == june_cfo["net_revenue_retention_bps"] and sum(r["ending_arr_minor"] for r in june) == arr[-1],
            "Group SaaS metrics do not tie")
    require(churn[-1] == max(churn) and churn.count(churn[-1]) == 1 and nrr == min(nrr_series)
            and nrr_series.count(nrr) == 1 and opening_mrr - retained_mrr == churn[-1],
            "Slide 7 says June churn was the highest and NRR the lowest of the twelve months")
    arr_change = arr[-1] - arr[0]
    require(arr_change < 0, "Slide 7 says ARR is down on a year earlier")
    v.update(arr=pounds(arr[-1], True), arr_year_ago=pounds(arr[0], True), arr_yoy=signed(arr_change),
             arr_yoy_abs=pounds(-arr_change, True), arr_yoy_pct=minus(f"{share(arr_change, arr[0], '0.1')}%"),
             nrr=percent(nrr), june_churn=thousands(churn[-1]),
             spark_arr=charts.sparkline([millions(x) for x in arr], "Ending ARR, June 2025 to June 2026."),
             chart_arr=charts.arr([r["period_id"] for r in cfo], [millions(x) for x in arr],
                                  [float(Decimal(x) / 100_000) for x in churn], {
                                      "arr_first": pounds(arr[0], True), "arr_last": pounds(arr[-1], True),
                                      "churn_last": thousands(churn[-1]),
                                      "aria": "Ending ARR at each month-end from June 2025 with monthly MRR churn."}))
    v["spark_cash"] = charts.sparkline([millions(r["closing_cash_minor"]) for r in year],
                                       "Closing cash, June 2025 to June 2026.")

    # ---------------------------------------------- controls and working ---
    unapplied, overdue_bps, assertion_policy, rules = assurance(db, delivery)
    now, then = working[-1], working[0]
    overdue_ar, closing_ar = now["overdue_ar_minor"], now["closing_ar_minor"]
    overdue_ap, closing_ap = now["overdue_ap_minor"], now["closing_ap_minor"]
    require(rounded(Decimal(overdue_ap) * 10_000 / closing_ap, "1") == overdue_bps == now["overdue_ap_bps"],
            "Overdue payables share does not tie to its amounts")
    require(rounded(Decimal(overdue_ar) / closing) == 2, "Slide 8 says overdue receivables are twice closing cash")
    above = [w["overdue_ar_minor"] > c["closing_cash_minor"] for w, c in zip(working, year, strict=True)]
    cross = above.index(True)
    require(all(above[cross:]) and working[cross]["period_id"] == PRIOR,
            "Slide 8 says overdue receivables have exceeded cash since May")
    unapplied_series = [r["unapplied_cash_minor"] for r in balance]
    require(unapplied_series[-1] == unapplied
            and all(b > a for a, b in pairwise(unapplied_series)),
            "Slide 8 says unapplied cash has risen every month since January")
    v.update(overdue_ar=pounds(overdue_ar, True), ar_percent=f"{share(overdue_ar, closing_ar, '1')}%",
             ar_yoy=signed(overdue_ar - then["overdue_ar_minor"]),
             dso=f"{rounded(now['dso_days'], '1')}", dso_year_ago=f"{rounded(then['dso_days'], '1')}",
             overdue_ap=pounds(overdue_ap, True), ap_percent=f"{rounded(Decimal(overdue_bps) / 100, '1')}%",
             dpo=f"{rounded(now['dpo_days'], '1')}", unapplied=pounds(unapplied, True),
             unapplied_jan=pounds(unapplied_series[0], True), assertion_policy=assertion_policy,
             control_tiles="".join(f'<div class="control"><span class="hits">0</span><span>{html.escape(name)}</span></div>'
                                   for name in rules),
             chart_wc=charts.two_lines([r["period_id"] for r in year],
                                       [millions(r["closing_cash_minor"]) for r in year],
                                       [millions(r["overdue_ar_minor"]) for r in working], {
                                           "first_name": "Closing cash", "second_name": "Overdue receivables",
                                           "first_last": pounds(closing, True), "first_note": "closing cash",
                                           "second_last": pounds(overdue_ar, True), "second_note": "overdue receivables",
                                           "cross_index": cross, "cross_text": "Overdue receivables exceed cash from May",
                                           "aria": "Closing cash and overdue receivables at each month-end from June 2025."}))

    planning = read(db, delivery, "mart_planning_performance_monthly", "true")
    require(len(planning) == 10416 and {r["statement_class"] for r in planning} == {"INCOME_STATEMENT"},
            "The delivery now holds non-income-statement planning data; review the forecast note")
    inventory = load(delivery / "powerbi/field-roles.json")["rows"]
    draw_fields = [r["column_name"] for r in inventory if any(
        name in r["column_name"].lower() for name in ("draw_condition", "facility_agreement", "borrowing_base", "covenant"))]
    require(not draw_fields, "Review the facility-terms evidence against the updated delivery")

    # ----------------------------------------------------------- decision ---
    treasury, fpa, review = (working_days_after(CLOSE_DATE, n) for n in (TREASURY_DAYS, FPA_DAYS, REVIEW_DAYS))
    require(review + timedelta(weeks=3) <= runs_out[0], "The review leaves too little time to act")
    horizon = CLOSE_DATE + timedelta(weeks=13)
    require(QUARTER_END - horizon == timedelta(days=1), "Slide 10 says a 13-week view stops a day short")
    v.update(treasury_date=long_date(treasury), fpa_date=long_date(fpa), review_date=long_date(review),
             quarter_end=long_date(QUARTER_END), horizon=long_date(horizon),
             chart_timeline=charts.timeline(
                 CLOSE_DATE, date(2026, 10, 4),
                 [(date(2026, m, 1), f"{date(2026, m, 1):%B}") for m in (7, 8, 9, 10)],
                 (runs_out[0], runs_out[1], [f"Cash alone runs out, {v['cover_dates']}", "at observed outflow rates"]),
                 [(CLOSE_DATE, ["Close", "30 June"], 0, "close"),
                  (treasury, ["Treasury", f"by {long_date(treasury)}"], 2, "action"),
                  (fpa, ["FP&A", f"by {long_date(fpa)}"], 1, "action"),
                  (review, ["CFO review", long_date(review)], 0, "action"),
                  (horizon, ["13-week view ends", long_date(horizon)], 1, "close"),
                  (QUARTER_END, [f"Model {v['payment']} repayment", long_date(QUARTER_END)], -1, "risk")],
                 "Proposed actions, the cash-only window and the September repayment, July to September 2026."))

    # ------------------------------------------------------ evidence rows ---
    trace_a = [
        table_row("e-liquidity", "Cash / undrawn / available", " / ".join(map(pounds, (closing, facility, total))),
                  f"{CASH} · closing_cash_minor + undrawn_facility_minor = available_liquidity_minor"),
        table_row("e-cover", "Cash cover, observed rates", f"{weeks[0]} / {weeks[1]} weeks",
                  f"Closing cash ÷ net outflow per day. June {pounds(outflow)} over {june_days} days; "
                  f"Jan{EN_DASH}Jun {pounds(half_outflow)} over {half_days} days. Repayments included. "
                  f"Cash alone runs out {runs_out[0].day} / {runs_out[1].day} August.", f"Jan{EN_DASH}Jun Group"),
        table_row("e-facility", "Combined limits / term loan drawn / repaid",
                  " / ".join(map(pounds, (limit, first["debt_drawdown_minor"], restored))),
                  f"{DEBT}; {SCHEDULES}. Drawn + undrawn constant for 66 months. Term loan: one drawdown, January "
                  f"2021, and {len(repayments)} repayments of {pounds(payment)}, Mar 2023 to Jun 2026. Revolver: nil "
                  f"balance throughout. Undrawn {pounds(revolver_undrawn)} before any repayment, rising by each.",
                  "Group; instruments NEXUS-UK"),
        table_row("e-movement", "Net outflow, May / June", f"{pounds(prior_outflow)} / {pounds(outflow)}",
                  f"{CASH}. Operating {pounds(-prior_operating)} / {pounds(-operating)}; investing "
                  f"{pounds(prior['investing_cash_flow_minor'])} / {pounds(cash['investing_cash_flow_minor'])}; financing "
                  f"{pounds(prior['financing_cash_flow_minor'])} / {pounds(cash['financing_cash_flow_minor'])}.",
                  f"May{EN_DASH}Jun Group"),
        table_row("e-performance", "Revenue / EBITDA, June", f"{pounds(revenue[-1])} / {pounds(ebitda[-1])}",
                  f"{FIN}. May {pounds(revenue[-2])} / {pounds(ebitda[-2])}. Twelve months: revenue "
                  f"{pounds(sum(revenue))}, EBITDA {pounds(sum(ebitda))}.", f"Jul 2025{EN_DASH}Jun 2026 Group"),
        table_row("e-recurring", "Ending ARR / NRR / churn", f"{pounds(arr[-1])} / {percent(nrr)} / {pounds(churn[-1])}",
                  f"{CFO}; {SAAS}. June 2025 ARR {pounds(arr[0])}. NRR = retained ÷ opening MRR, "
                  f"{pounds(retained_mrr)} ÷ {pounds(opening_mrr)}. New, expansion and contraction MRR are zero "
                  "in all 12 months.", f"Jun 2025{EN_DASH}Jun 2026 Group"),
    ]
    trace_b = [
        table_row("e-close", "Close / checks", "Hard-closed, published / 36 + 15 passed",
                  "dim_reporting_version; metadata/reconciliation.json (29 cross-format delivery parity, 2 source "
                  "binding, 5 replayed difference); mart_model_readiness_controls (15 model readiness).",
                  "June Group; delivery-wide"),
        table_row("e-controls", "Control rule hits", f"0 of {len(rules)} rules",
                  f"{assertion_policy}: {', '.join(r.lower() for r in rules)}.", "June, delivered scopes"),
        table_row("e-working-capital", "Overdue receivables",
                  f"{pounds(overdue_ar)} of {pounds(closing_ar)} ({share(overdue_ar, closing_ar)}%)",
                  f"{WC} · overdue_ar_minor ÷ closing_ar_minor. June 2025 {pounds(then['overdue_ar_minor'])}; "
                  f"debtor days {rounded(now['dso_days'])} ({rounded(then['dso_days'])} a year earlier).",
                  f"Jun 2025{EN_DASH}Jun 2026 Group"),
        table_row(None, "Overdue payables", f"{pounds(overdue_ap)} of {pounds(closing_ap)} ({percent(overdue_bps)})",
                  f"{WC} · overdue_ap_minor ÷ closing_ap_minor. Creditor days {rounded(now['dpo_days'])}.", "June Group"),
        table_row(None, "Unapplied cash", pounds(unapplied),
                  f"{BALANCE} · unapplied_cash_minor. January {pounds(unapplied_series[0])}. Held wholly in NEXUS-UK.",
                  "June Group = June UK"),
    ]
    v.update(trace_a="\n".join(trace_a), trace_b="\n".join(trace_b), source_digest=digest)
    return v


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delivery", type=Path, default=DEFAULT_DELIVERY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    delivery = args.delivery.resolve()
    FinanceDeliveryService()._verify_seal(delivery, DELIVERY_SEAL)
    manifest = load(delivery / "delivery-manifest.json")
    require(manifest["delivery_ref"] == DELIVERY_REF and manifest["status"] == "PUBLISHED",
            "Unexpected C2 delivery identity or status")
    with duckdb.connect() as db:
        values = evidence(db, delivery)
    markup = {k for k in values if k.startswith(("chart_", "spark_", "trace_")) or k == "control_tiles"}
    values = {k: v if k in markup else html.escape(str(v), quote=True) for k, v in values.items()}
    values.update(css=(HERE / "deck.css").read_text(encoding="utf-8"), version=VERSION, uk_version=UK_VERSION,
                  delivery_ref=DELIVERY_REF, delivery_seal=DELIVERY_SEAL, slides=str(SLIDES),
                  delivery_seal_short=f"{DELIVERY_SEAL[:15]}…{DELIVERY_SEAL[-8:]}")
    template = Template((HERE / "deck.html").read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(template.substitute(values), encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
