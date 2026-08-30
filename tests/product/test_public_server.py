from __future__ import annotations

import asyncio
import json
from pathlib import Path
from urllib.parse import urlencode

from finance_assurance.product.demo_scenarios import default_demo_scenarios
from finance_assurance.product.server import create_public_product_app


def _request_overview(database: Path) -> tuple[int, dict[str, object]]:
    scenarios = default_demo_scenarios()
    app = create_public_product_app(database, workspace_ref="SERVER-TEST")
    sent: list[dict[str, object]] = []
    received = False

    async def receive() -> dict[str, object]:
        nonlocal received
        if received:
            return {"type": "http.disconnect"}
        received = True
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, object]) -> None:
        sent.append(message)

    query = urlencode(
        {
            "view_contract_version": "1",
            "scenario_ref": scenarios.c001.scenario_ref,
            "semantic_as_of_time": scenarios.semantic_as_of_time,
        }
    ).encode("ascii")

    async def execute() -> None:
        await app(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/v1/overview",
                "query_string": query,
            },
            receive,
            send,
        )

    try:
        asyncio.run(execute())
    finally:
        app.close()

    assert [message["type"] for message in sent] == [
        "http.response.start",
        "http.response.body",
    ]
    payload = json.loads(sent[1]["body"])
    assert isinstance(payload, dict)
    return int(sent[0]["status"]), payload


def test_local_server_initialises_then_verifies_the_same_demo(
    tmp_path: Path,
) -> None:
    database = tmp_path / "public-product.sqlite3"

    first_status, first = _request_overview(database)
    initial_bytes = database.read_bytes()
    second_status, second = _request_overview(database)

    assert first_status == second_status == 200
    assert first == second
    assert first["view_contract"] == "O-V02"
    assert first["compatibility_read_mode"] == "EXACT_ORIGINAL"
    assert database.read_bytes() == initial_bytes
