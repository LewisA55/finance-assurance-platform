from __future__ import annotations

import ast
import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlencode

import pytest

from finance_assurance.product.demo_runtime import materialize_demo
from finance_assurance.product.demo_scenarios import (
    DemoScenarioSet,
    default_demo_scenarios,
)
from finance_assurance.product.http_adapter import (
    PUBLIC_HTTP_ROUTES,
    PublicHttpAdapter,
)
from finance_assurance.product.query_models import PublicQuery
from finance_assurance.product.query_service import PublicQueryService
from finance_assurance.product.registry import PUBLIC_QUERY_REGISTRY
from finance_assurance.runtime.canonical import canonical_bytes
from finance_assurance.runtime.persistence.sqlite import SqlitePersistenceBoundary


@dataclass(frozen=True, slots=True)
class HttpResult:
    status: int
    headers: dict[str, str]
    body: bytes

    def json(self) -> dict[str, object]:
        value = json.loads(self.body)
        assert isinstance(value, dict)
        return value


async def _asgi_request_async(
    app: PublicHttpAdapter,
    method: str,
    path: str,
    *,
    query: list[tuple[str, str]] | None = None,
    raw_query: bytes | None = None,
    body: bytes = b"",
) -> HttpResult:
    received = False
    messages: list[dict[str, object]] = []

    async def receive() -> dict[str, object]:
        nonlocal received
        if received:
            return {"type": "http.disconnect"}
        received = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: dict[str, object]) -> None:
        messages.append(message)

    query_string = (
        raw_query
        if raw_query is not None
        else urlencode(query or []).encode("ascii")
    )
    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": query_string,
            "headers": [],
        },
        receive,
        send,
    )
    assert [message["type"] for message in messages] == [
        "http.response.start",
        "http.response.body",
    ]
    start, response = messages
    headers = {
        key.decode("ascii"): value.decode("ascii")
        for key, value in start["headers"]  # type: ignore[union-attr]
    }
    return HttpResult(
        status=int(start["status"]),
        headers=headers,
        body=response["body"],  # type: ignore[arg-type]
    )


def test_overview_advertised_successor_issue_route_resolves_exact_case(
    http_demo: tuple[PublicHttpAdapter, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    app, scenarios, _ = http_demo
    query = _common(scenarios, scenarios.c001.scenario_ref)
    overview = _asgi_request(app, "GET", "/api/v1/overview", query=query).json()
    data = overview["data"]
    assert isinstance(data, dict)
    modules = data["module_summaries"]
    assert isinstance(modules, list)
    aegis = next(item for item in modules if item["module"] == "Aegis")

    assert aegis["route"] == "/aegis/cases/ISSUE-C001@v2"
    result = _asgi_request(
        app,
        "GET",
        f"/api/v1{aegis['route']}",
        query=query,
    )

    assert result.status == 200
    payload = result.json()
    assert payload["view_contract"] == "O-V07"
    assert payload["data"]["initial_issue_ref"] == "ISSUE-C001@v1"  # type: ignore[index]
    assert payload["data"]["final_issue_ref"] == "ISSUE-C001@v2"  # type: ignore[index]
def _asgi_request(
    app: PublicHttpAdapter,
    method: str,
    path: str,
    *,
    query: list[tuple[str, str]] | None = None,
    raw_query: bytes | None = None,
    body: bytes = b"",
) -> HttpResult:
    return asyncio.run(
        _asgi_request_async(
            app,
            method,
            path,
            query=query,
            raw_query=raw_query,
            body=body,
        )
    )


def _common(scenarios: DemoScenarioSet, scenario_ref: str) -> list[tuple[str, str]]:
    return [
        ("view_contract_version", "1"),
        ("scenario_ref", scenario_ref),
        ("semantic_as_of_time", str(scenarios.semantic_as_of_time)),
    ]


@pytest.fixture(scope="module")
def http_demo(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[PublicHttpAdapter, DemoScenarioSet, SqlitePersistenceBoundary]:
    scenarios = default_demo_scenarios()
    database = tmp_path_factory.mktemp("public-http-demo") / "demo.sqlite3"
    materialize_demo(database, scenarios)
    boundary = SqlitePersistenceBoundary(database)
    service = PublicQueryService(
        boundary,
        scenarios=scenarios,
        workspace_ref="TEST-DEMO",
    )
    yield PublicHttpAdapter(service, workspace_ref="TEST-DEMO"), scenarios, boundary
    boundary.close()


def test_http_registry_is_exactly_one_to_one_with_artifact_o() -> None:
    assert len(PUBLIC_HTTP_ROUTES) == 11
    assert tuple(route.query_id for route in PUBLIC_HTTP_ROUTES) == tuple(
        PUBLIC_QUERY_REGISTRY
    )
    assert tuple(route.view_id for route in PUBLIC_HTTP_ROUTES) == tuple(
        descriptor.view_id for descriptor in PUBLIC_QUERY_REGISTRY.values()
    )
    assert tuple(route.path_template for route in PUBLIC_HTTP_ROUTES) == (
        "/api/v1/demo",
        "/api/v1/overview",
        "/api/v1/hermes/reconciliations/{product_ref}",
        "/api/v1/atlas/reporting-periods/{period_id}",
        "/api/v1/atlas/reporting-versions/{version_ref}",
        "/api/v1/argus/exceptions/{exception_ref}",
        "/api/v1/aegis/cases/{issue_ref}",
        "/api/v1/aegis/readiness/{reporting_version_ref}",
        "/api/v1/pythia/decisions/{decision_ref}",
        "/api/v1/traces/reporting-values/{version_ref}/{statement_field}",
        "/api/v1/corrections/{verification_ref}",
    )


def test_all_eleven_get_routes_return_closed_no_store_json(
    http_demo: tuple[PublicHttpAdapter, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    app, scenarios, boundary = http_demo
    c001 = _common(scenarios, scenarios.c001.scenario_ref)
    ct1 = _common(scenarios, scenarios.ct1.scenario_ref)
    cases = (
        ("/api/v1/demo", c001),
        ("/api/v1/overview", c001),
        ("/api/v1/hermes/reconciliations/RECON-C001@v1", c001),
        ("/api/v1/atlas/reporting-periods/2026-06", c001),
        ("/api/v1/atlas/reporting-versions/RV-2026-06@v2", c001),
        ("/api/v1/argus/exceptions/EXC-C001@v1", c001),
        ("/api/v1/aegis/cases/ISSUE-C001@v1", c001),
        (
            "/api/v1/aegis/readiness/RV-2026-06@v2",
            [
                *c001,
                ("period_id", "2026-06"),
                ("purpose_ref", "HIRING-FORECAST"),
                ("scope_ref", "NEXUS-GROUP"),
            ],
        ),
        ("/api/v1/pythia/decisions/DECISION-C001@v1", c001),
        (
            "/api/v1/traces/reporting-values/"
            "RV-2026-06@v2/subscription_revenue_minor",
            c001,
        ),
        ("/api/v1/corrections/VERIFY-CT1@v1", ct1),
    )

    results = tuple(
        _asgi_request(app, "GET", path, query=query) for path, query in cases
    )

    assert tuple(result.status for result in results) == (200,) * 11
    assert tuple(result.json()["view_contract"] for result in results) == tuple(
        f"O-V{index:02d}" for index in range(1, 12)
    )
    assert {result.json()["query_revision"] for result in results} == {
        boundary.revision
    }
    assert {
        result.json()["compatibility_read_mode"] for result in results
    } == {"EXACT_ORIGINAL"}
    for result in results:
        assert result.headers["content-type"] == "application/json; charset=utf-8"
        assert result.headers["cache-control"] == "no-store"
        assert result.headers["x-content-type-options"] == "nosniff"
        assert result.body == canonical_bytes(result.json())


@pytest.mark.parametrize(
    ("query", "raw_query"),
    [
        (
            [
                ("view_contract_version", "1"),
                ("semantic_as_of_time", "2026-07-14T12:00:00Z"),
            ],
            None,
        ),
        (
            [
                ("view_contract_version", "2"),
                ("scenario_ref", "DEMO-C001-RESTATEMENT@v1"),
                ("semantic_as_of_time", "2026-07-14T12:00:00Z"),
            ],
            None,
        ),
        (
            [
                ("view_contract_version", "1"),
                ("scenario_ref", "DEMO-C001-RESTATEMENT@v1"),
                ("semantic_as_of_time", "2026-07-14T12:00:00Z"),
                ("latest", "true"),
            ],
            None,
        ),
        (None, b"view_contract_version=1&scenario_ref=a&scenario_ref=b"),
        (None, b"not-a-pair"),
    ],
)
def test_transport_rejects_missing_unsupported_unknown_duplicate_and_malformed_inputs(
    http_demo: tuple[PublicHttpAdapter, DemoScenarioSet, SqlitePersistenceBoundary],
    query: list[tuple[str, str]] | None,
    raw_query: bytes | None,
) -> None:
    app, _, _ = http_demo

    result = _asgi_request(
        app,
        "GET",
        "/api/v1/overview",
        query=query,
        raw_query=raw_query,
    )

    assert result.status == 400
    assert result.json()["error_code"] == "UNSUPPORTED_CONTRACT"
    assert "query_revision" not in result.json()
    assert result.headers["cache-control"] == "no-store"


def test_readiness_route_requires_exact_period_purpose_and_scope(
    http_demo: tuple[PublicHttpAdapter, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    app, scenarios, _ = http_demo
    common = _common(scenarios, scenarios.c001.scenario_ref)

    for missing in ("period_id", "purpose_ref", "scope_ref"):
        fields = [
            ("period_id", "2026-06"),
            ("purpose_ref", "HIRING-FORECAST"),
            ("scope_ref", "NEXUS-GROUP"),
        ]
        result = _asgi_request(
            app,
            "GET",
            "/api/v1/aegis/readiness/RV-2026-06@v2",
            query=common + [(key, value) for key, value in fields if key != missing],
        )
        assert result.status == 400
        assert result.json()["error_code"] == "UNSUPPORTED_CONTRACT"


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "HEAD"])
def test_public_transport_is_read_only(
    http_demo: tuple[PublicHttpAdapter, DemoScenarioSet, SqlitePersistenceBoundary],
    method: str,
) -> None:
    app, scenarios, _ = http_demo

    result = _asgi_request(
        app,
        method,
        "/api/v1/overview",
        query=_common(scenarios, scenarios.c001.scenario_ref),
        body=b"{}" if method == "POST" else b"",
    )

    assert result.status == 405
    assert result.headers["allow"] == "GET"
    assert result.json()["error_code"] == "UNSUPPORTED_CONTRACT"


def test_unknown_route_trailing_slash_and_get_body_are_rejected(
    http_demo: tuple[PublicHttpAdapter, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    app, scenarios, _ = http_demo
    common = _common(scenarios, scenarios.c001.scenario_ref)

    unknown = _asgi_request(app, "GET", "/api/v1/raw-records", query=common)
    trailing = _asgi_request(app, "GET", "/api/v1/overview/", query=common)
    body = _asgi_request(
        app,
        "GET",
        "/api/v1/overview",
        query=common,
        body=b"{}",
    )

    assert unknown.status == 404
    assert trailing.status == 404
    assert body.status == 400
    assert {unknown.json()["error_code"], trailing.json()["error_code"]} == {
        "UNSUPPORTED_CONTRACT"
    }
    assert body.json()["error_code"] == "UNSUPPORTED_CONTRACT"
    assert body.json()["error_code"] == "UNSUPPORTED_CONTRACT"


def test_application_failure_maps_to_safe_http_status_without_false_data(
    http_demo: tuple[PublicHttpAdapter, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    app, scenarios, _ = http_demo

    result = _asgi_request(
        app,
        "GET",
        "/api/v1/atlas/reporting-versions/RV-MISSING@v1",
        query=_common(scenarios, scenarios.c001.scenario_ref),
    )

    payload = result.json()
    assert result.status == 404
    assert payload["error_code"] == "NOT_FOUND"
    assert "data" not in payload
    assert "traceback" not in result.body.decode("utf-8").lower()
    assert "sqlite" not in result.body.decode("utf-8").lower()


def test_executor_failure_maps_to_closed_demo_unavailable_state(
    http_demo: tuple[PublicHttpAdapter, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    _, scenarios, _ = http_demo

    class FailingExecutor:
        def execute(self, query: PublicQuery) -> object:
            raise RuntimeError(f"secret backend detail for {query.query_id}")

    app = PublicHttpAdapter(  # type: ignore[arg-type]
        FailingExecutor(),
        workspace_ref="TEST-DEMO",
    )
    result = _asgi_request(
        app,
        "GET",
        "/api/v1/overview",
        query=_common(scenarios, scenarios.c001.scenario_ref),
    )

    assert result.status == 503
    assert result.json() == {
        "error_code": "DEMO_NOT_INITIALISED",
        "message": "The public demo is unavailable.",
        "scenario_ref": scenarios.c001.scenario_ref,
        "subject_ref": "O-Q02",
    }
    assert "secret" not in result.body.decode("utf-8").lower()


def test_rejected_transport_never_invokes_the_query_executor(
    http_demo: tuple[PublicHttpAdapter, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    _, scenarios, _ = http_demo
    executor = _CountingExecutor(None)
    app = PublicHttpAdapter(  # type: ignore[arg-type]
        executor,
        workspace_ref="TEST-DEMO",
    )
    common = _common(scenarios, scenarios.c001.scenario_ref)

    results = (
        _asgi_request(app, "POST", "/api/v1/overview", query=common),
        _asgi_request(app, "GET", "/api/v1/overview", query=common, body=b"x"),
        _asgi_request(app, "GET", "/api/v1/overview", query=common[:-1]),
        _asgi_request(app, "GET", "/api/v1/not-a-route", query=common),
    )

    assert tuple(result.status for result in results) == (405, 400, 400, 404)
    assert executor.queries == []


@dataclass(slots=True)
class _CountingExecutor:
    result: object
    queries: list[PublicQuery] = field(default_factory=list)

    def execute(self, query: PublicQuery) -> object:
        self.queries.append(query)
        return self.result


def test_one_http_request_executes_exactly_one_public_query(
    http_demo: tuple[PublicHttpAdapter, DemoScenarioSet, SqlitePersistenceBoundary],
) -> None:
    app, scenarios, _ = http_demo
    baseline = _asgi_request(
        app,
        "GET",
        "/api/v1/overview",
        query=_common(scenarios, scenarios.c001.scenario_ref),
    )
    from finance_assurance.product.contracts import PUBLIC_SUCCESS_ADAPTER

    result_model = PUBLIC_SUCCESS_ADAPTER.validate_json(baseline.body)
    executor = _CountingExecutor(result_model)
    counting_app = PublicHttpAdapter(  # type: ignore[arg-type]
        executor,
        workspace_ref="TEST-DEMO",
    )

    result = _asgi_request(
        counting_app,
        "GET",
        "/api/v1/overview",
        query=_common(scenarios, scenarios.c001.scenario_ref),
    )

    assert result.status == 200
    assert len(executor.queries) == 1
    assert executor.queries[0].query_id == "O-Q02"


def test_http_adapter_imports_no_persistence_fixture_or_command_layer() -> None:
    source_path = (
        Path(__file__).parents[2]
        / "src"
        / "finance_assurance"
        / "product"
        / "http_adapter.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)

    assert not any("sqlite" in name for name in imports)
    assert not any("fixture" in name for name in imports)
    assert not any("validation" in name for name in imports)
    assert not any(".commands" in name for name in imports)
    assert not any("demo_runtime" in name for name in imports)
