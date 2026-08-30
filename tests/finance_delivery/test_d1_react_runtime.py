from __future__ import annotations

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DATA = ROOT / "web" / "public" / "finance-data"


def test_d1_parquet_populations_and_governed_results_replay() -> None:
    manifest = json.loads((PUBLIC_DATA / "runtime-manifest.json").read_text("utf-8"))
    connection = duckdb.connect(":memory:")

    populations: dict[str, int] = {}
    for table in manifest["runtimeTables"][:3]:
        files = [str(ROOT / "web" / "public" / path.removeprefix("/")) for path in table["files"]]
        count = connection.execute(
            "select count(*) from read_parquet(?)", [files]
        ).fetchone()[0]
        populations[table["tableName"]] = count
        assert count == table["expectedRows"]

    assert populations == {
        "mart_executive_cfo_command_center": 66,
        "mart_cfo_metric_readiness": 11,
        "mart_model_readiness_controls": 15,
    }

    command_files = [
        str(ROOT / "web" / "public" / path.removeprefix("/"))
        for path in manifest["runtimeTables"][0]["files"]
    ]
    latest = connection.execute(
        """
        select period_id, reporting_version_ref, presentation_status,
               reliability_status, source_package_digest
        from read_parquet(?)
        order by period_id desc
        limit 1
        """,
        [command_files],
    ).fetchone()
    assert latest == (
        "2026-06",
        "RV-NEXUS-GROUP-2026-06@v1",
        "READY",
        "RELIABLE_FOR_EXECUTIVE_PRESENTATION",
        manifest["sourceDataDigest"],
    )

    readiness_files = [
        str(ROOT / "web" / "public" / path.removeprefix("/"))
        for path in manifest["runtimeTables"][1]["files"]
    ]
    control_files = [
        str(ROOT / "web" / "public" / path.removeprefix("/"))
        for path in manifest["runtimeTables"][2]["files"]
    ]
    assert connection.execute(
        "select count(*) from read_parquet(?) where readiness_status = 'READY'",
        [readiness_files],
    ).fetchone()[0] == 11
    assert connection.execute(
        "select count(*) from read_parquet(?) where result_status = 'PASS'",
        [control_files],
    ).fetchone()[0] == 15
