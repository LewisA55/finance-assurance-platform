"""Build the two review datasets from the pinned delivery and accounting replay."""
import json
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
import nexus_build as nb

from finance_assurance.finance_delivery.service import FinanceDeliveryService
from finance_assurance.validation.canonical import canonical_sha256
from finance_assurance.validation.h7_reporting import run_h7

POLICY = json.loads((HERE / "forecast-policy.json").read_text())
FIXTURES = nb.REPO / "docs/architecture/fixtures"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fixtures(name):
    return [json.loads(line) for line in (FIXTURES / f"{name}.jsonl").read_text().splitlines()]


def planning(root):
    seal, _ = FinanceDeliveryService()._verify_seal(root, POLICY["deliveryDigest"])
    delivery = json.loads((root / "delivery-manifest.json").read_text())
    require(delivery["delivery_ref"] == POLICY["deliveryRef"] and delivery["status"] == "PUBLISHED",
            "Planning source delivery is not the pinned publication")
    path = str(root / "powerbi/parquet/mart_planning_performance_monthly.parquet")
    with duckdb.connect() as db:
        cursor = db.execute("""
            select period_id, department_id, department_name, account_id, account_name,
                   currency, actual_amount_minor, budget_amount_minor, budget_version_ref,
                   source_budget_line_ref, planning_performance_hk, value_authority,
                   reliability_purpose, reliability_status, is_statutory_actual, source_forecast_line_ref
            from read_parquet(?) where period_id in (?, ?) and period_status = 'ACTUAL'
            order by period_id, account_id, department_id
        """, [path, POLICY["baselinePeriod"], POLICY["targetPeriod"]])
        names = [c[0] for c in cursor.description]
        data = [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]
    by_period = {}
    for r in data:
        require(r["currency"] == "GBP" and r["value_authority"] == "MANAGEMENT_SOURCE_REPORT"
                and r["reliability_purpose"] == "EXECUTIVE_MANAGEMENT_VARIANCE"
                and r["reliability_status"] == "SOURCE_SYSTEM_REPORT_FOR_MANAGEMENT_VARIANCE"
                and not r["is_statutory_actual"] and not r["source_forecast_line_ref"]
                and r["budget_version_ref"] == "AOP-2026@v1"
                and r["source_budget_line_ref"] and r["planning_performance_hk"]
                and r["actual_amount_minor"] >= 0 and r["budget_amount_minor"] >= 0,
                "Planning source contains an unsupported authority, sign or currency")
        key = r["account_id"], r["department_id"]
        period_rows = by_period.setdefault(r["period_id"], {})
        require(key not in period_rows, f"Duplicate management row for {key}")
        period_rows[key] = r
    baseline = by_period[POLICY["baselinePeriod"]]
    target = by_period[POLICY["targetPeriod"]]
    require(baseline.keys() == target.keys() and len(target) == 56
            and {key[0] for key in target} == POLICY["accounts"].keys(),
            "Forecast and outcome populations must match on department and account")
    require(POLICY["baselinePeriod"] < POLICY["vintagePeriod"] < POLICY["targetPeriod"],
            "Forecast baseline must precede its vintage and target")
    rows = []
    policy_digest = canonical_sha256(POLICY)
    for (account, dept), r in target.items():
        previous = baseline[account, dept]
        require((r["account_name"], r["department_name"]) ==
                (previous["account_name"], previous["department_name"]), "A comparison label has changed")
        assumption = POLICY["accounts"][account]
        budget = r["budget_amount_minor"]
        forecast = (previous["actual_amount_minor"] * assumption["factorBps"] + 5000) // 10000
        actual = r["actual_amount_minor"]
        rows.append({
            "mode": "variance", "key": f"{account}|{dept}", "groupKey": account,
            "groupLabel": r["account_name"], "label": r["department_name"],
            "period": r["period_id"], "scope": POLICY["scope"], "currency": r["currency"],
            "base": budget, "middle": forecast, "end": actual, "firstDelta": forecast - budget,
            "secondDelta": actual - forecast, "netDelta": actual - budget,
            "direction": assumption["direction"], "expected": len(target),
            "baseRef": f'{r["budget_version_ref"]} / {r["source_budget_line_ref"]}',
            "middleRef": f'{POLICY["forecastRef"]} / {account}|{dept}',
            "endRef": f'{r["value_authority"]} / {r["planning_performance_hk"]}',
            "evidence": (f'{POLICY["version"]} ({policy_digest}) | {POLICY["baselinePeriod"]} '
                         f'management row {previous["planning_performance_hk"]} '
                         f'x {assumption["factorBps"]} bps | {POLICY["deliveryRef"]} / {seal}'),
        })
    return rows


def restatement():
    replay = run_h7()
    require(replay.passed, "C-001 and CT-1 runtime replay must pass before materialisation")
    proofs = sorted(fixtures("reporting-content-proof-bodies"), key=lambda p: p["content_ref"])
    original, successor = proofs
    for proof in proofs:
        require(canonical_sha256(proof["canonical_body"]) == proof["content_hash"],
                "A published reporting content hash differs")
    before, after = [p["canonical_body"] for p in proofs]
    version = next(r["payload"] for r in fixtures("canonical-object-payloads")
                   if r["fixture_id"] == "OBJ-C001-RV-001")
    case = next(r["payload"] for r in fixtures("canonical-object-payloads")
                if r["fixture_id"] == "OBJ-C001-RC-001")
    event = next(e for e in fixtures("c001-accounting-events") if e["event_id"] == version["published_by_event_id"])
    require(event["event_type"] == "reporting_version.published"
            and event["payload"]["reporting_version_ref"] == version["reporting_version_ref"] == after["reporting_version_ref"]
            and event["basis"]["predecessor_version_ref"] == version["predecessor_version_ref"] == before["reporting_version_ref"]
            and event["basis"]["content_hash"] == version["content_hash"] == successor["content_hash"]
            and event["basis"]["content_ref"] == version["content_ref"] == successor["content_ref"]
            and event["basis"]["manifest_hash"] == version["adjustment_manifest_hash"] == case["manifest_hash"]
            and case["status"] == "PUBLISHED"
            and event["basis"]["restatement_case_id"] == version["restatement_case_id"] == case["restatement_case_id"]
            and before["currency"] == after["currency"] == "GBP"
            and before["presented_period_id"] == after["presented_period_id"] == version["period_id"],
            "Restatement predecessor, publication or adjustment evidence differs")
    mappings = {
        "subscription_revenue_minor": ("Subscription revenue", "ACC-SUBSCRIPTION-REVENUE"),
        "deferred_revenue_minor": ("Deferred revenue", "ACC-DEFERRED-REVENUE"),
    }
    rows = []
    for field, (label, account) in mappings.items():
        adjustments = [line for line in case["adjustment_manifest"] if line["account_id"] == account]
        require(len(adjustments) == 1, f"Expected a single adjustment for {field}")
        line = adjustments[0]
        delta = after[field] - before[field]
        require(line["currency"] == before["currency"]
                and line["presented_period_id"] == version["period_id"]
                and line["ledger_period_id"] > line["presented_period_id"]
                and delta == line["credit_minor"] - line["debit_minor"],
                f"Unexplained restatement delta for {field}")
        rows.append({
            "mode": "restatement", "key": field, "groupKey": case["restatement_case_id"],
            "groupLabel": "C-001 recognition correction", "label": label,
            "period": version["period_id"], "scope": "C-001 accounting replay", "currency": before["currency"],
            "base": before[field], "middle": None, "end": after[field], "firstDelta": None,
            "secondDelta": None, "netDelta": delta, "direction": "neutral", "expected": len(mappings),
            "baseRef": f'{before["reporting_version_ref"]} / {original["content_hash"]}',
            "middleRef": f'{event["event_id"]} / {case["restatement_case_id"]}',
            "endRef": f'{after["reporting_version_ref"]} / {successor["content_hash"]}',
            "evidence": (f'{line["journal_line_ref"]} | Ledger {line["ledger_period_id"]} | '
                         f'Presented {line["presented_period_id"]} | {case["manifest_hash"]} | '
                         f'C-001 replay {replay.report.c001_state_digest}'),
        })
    return rows


def materialize():
    rows = planning(nb.DELIVERY) + restatement()
    # The two inputs keep their own evidence. This digest names the adapter
    # output and provides a reproducibility check for the inlined tables.
    digest = canonical_sha256(rows)
    for row in rows:
        row["adapterDigest"] = digest
    return rows
