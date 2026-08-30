"""Finite read-only ASGI transport for the Artifact O public query facade."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, cast
from urllib.parse import parse_qsl

from pydantic import ValidationError

from finance_assurance.product.contracts import (
    PublicFailureEnvelope,
    PublicSuccessEnvelope,
    StartupFailureEnvelope,
)
from finance_assurance.product.query_models import (
    PUBLIC_QUERY_ADAPTER,
    PublicQuery,
)
from finance_assurance.product.registry import (
    PUBLIC_QUERY_REGISTRY,
    PublicQueryId,
    PublicViewId,
)
from finance_assurance.runtime.canonical import canonical_bytes

type AsgiMessage = dict[str, object]
type AsgiReceive = Callable[[], Awaitable[AsgiMessage]]
type AsgiSend = Callable[[AsgiMessage], Awaitable[None]]

_COMMON_QUERY_FIELDS = (
    "view_contract_version",
    "scenario_ref",
    "semantic_as_of_time",
)
_MAX_REQUEST_BODY_BYTES = 1


class PublicQueryExecutor(Protocol):
    """The only application capability exposed to the HTTP adapter."""

    def execute(
        self, query: PublicQuery
    ) -> PublicSuccessEnvelope | PublicFailureEnvelope: ...


@dataclass(frozen=True, slots=True)
class PublicHttpRoute:
    """One closed HTTP route mapped to one Artifact O query and view."""

    path_template: str
    path_pattern: re.Pattern[str]
    query_id: PublicQueryId
    view_id: PublicViewId
    path_bindings: tuple[tuple[str, str], ...] = ()
    additional_query_fields: tuple[str, ...] = ()

    @property
    def allowed_query_fields(self) -> tuple[str, ...]:
        return _COMMON_QUERY_FIELDS + self.additional_query_fields

    def match(self, path: str) -> dict[str, str] | None:
        match = self.path_pattern.fullmatch(path)
        if match is None:
            return None
        captured = match.groupdict()
        return {
            target: captured[source]
            for source, target in self.path_bindings
        }


def _route(
    path_template: str,
    path_expression: str,
    query_id: PublicQueryId,
    *,
    path_bindings: tuple[tuple[str, str], ...] = (),
    additional_query_fields: tuple[str, ...] = (),
) -> PublicHttpRoute:
    descriptor = PUBLIC_QUERY_REGISTRY[query_id]
    return PublicHttpRoute(
        path_template=path_template,
        path_pattern=re.compile(path_expression, re.ASCII),
        query_id=query_id,
        view_id=descriptor.view_id,
        path_bindings=path_bindings,
        additional_query_fields=additional_query_fields,
    )


PUBLIC_HTTP_ROUTES = (
    _route("/api/v1/demo", r"/api/v1/demo", "O-Q01"),
    _route("/api/v1/overview", r"/api/v1/overview", "O-Q02"),
    _route(
        "/api/v1/hermes/reconciliations/{product_ref}",
        r"/api/v1/hermes/reconciliations/(?P<product_ref>[^/]+)",
        "O-Q03",
        path_bindings=(("product_ref", "reconciliation_ref"),),
    ),
    _route(
        "/api/v1/atlas/reporting-periods/{period_id}",
        r"/api/v1/atlas/reporting-periods/(?P<period_id>[^/]+)",
        "O-Q04",
        path_bindings=(("period_id", "period_id"),),
    ),
    _route(
        "/api/v1/atlas/reporting-versions/{version_ref}",
        r"/api/v1/atlas/reporting-versions/(?P<version_ref>[^/]+)",
        "O-Q05",
        path_bindings=(("version_ref", "reporting_version_ref"),),
    ),
    _route(
        "/api/v1/argus/exceptions/{exception_ref}",
        r"/api/v1/argus/exceptions/(?P<exception_ref>[^/]+)",
        "O-Q06",
        path_bindings=(("exception_ref", "exception_ref"),),
    ),
    _route(
        "/api/v1/aegis/cases/{issue_ref}",
        r"/api/v1/aegis/cases/(?P<issue_ref>[^/]+)",
        "O-Q07",
        path_bindings=(("issue_ref", "issue_ref"),),
    ),
    _route(
        "/api/v1/aegis/readiness/{reporting_version_ref}",
        r"/api/v1/aegis/readiness/(?P<reporting_version_ref>[^/]+)",
        "O-Q08",
        path_bindings=(
            ("reporting_version_ref", "reporting_version_ref"),
        ),
        additional_query_fields=("period_id", "purpose_ref", "scope_ref"),
    ),
    _route(
        "/api/v1/pythia/decisions/{decision_ref}",
        r"/api/v1/pythia/decisions/(?P<decision_ref>[^/]+)",
        "O-Q09",
        path_bindings=(("decision_ref", "decision_ref"),),
    ),
    _route(
        "/api/v1/traces/reporting-values/{version_ref}/{statement_field}",
        (
            r"/api/v1/traces/reporting-values/"
            r"(?P<version_ref>[^/]+)/(?P<statement_field>[^/]+)"
        ),
        "O-Q10",
        path_bindings=(
            ("version_ref", "reporting_version_ref"),
            ("statement_field", "statement_field"),
        ),
    ),
    _route(
        "/api/v1/corrections/{verification_ref}",
        r"/api/v1/corrections/(?P<verification_ref>[^/]+)",
        "O-Q11",
        path_bindings=(("verification_ref", "verification_ref"),),
    ),
)

if (
    len(PUBLIC_HTTP_ROUTES) != 11
    or {route.query_id for route in PUBLIC_HTTP_ROUTES}
    != set(PUBLIC_QUERY_REGISTRY)
    or len({route.view_id for route in PUBLIC_HTTP_ROUTES}) != 11
    or len({route.path_template for route in PUBLIC_HTTP_ROUTES}) != 11
):
    raise RuntimeError("Artifact O HTTP registry must remain finite and one-to-one")


_FAILURE_STATUS: Mapping[str, int] = {
    "DEMO_NOT_INITIALISED": 503,
    "UNSUPPORTED_CONTRACT": 400,
    "NOT_FOUND": 404,
    "UNAVAILABLE": 409,
    "UNVERIFIED_CONTENT": 409,
    "REVISION_CONFLICT": 409,
    "TRACE_INTEGRITY_FAILURE": 500,
    "INTERNAL_FAILURE": 500,
}


class PublicHttpAdapter:
    """Serve exactly eleven GET routes over one public query executor."""

    def __init__(self, executor: PublicQueryExecutor, *, workspace_ref: str) -> None:
        self._executor = executor
        self._workspace_ref = workspace_ref

    async def __call__(
        self,
        scope: Mapping[str, object],
        receive: AsgiReceive,
        send: AsgiSend,
    ) -> None:
        if scope.get("type") != "http":
            raise RuntimeError("PublicHttpAdapter supports ASGI HTTP scopes only")

        method = str(scope.get("method", ""))
        path = str(scope.get("path", ""))
        route_match = self._match_route(path)

        if route_match is None:
            await self._send_failure(
                send,
                self._unsupported(
                    "The requested public route is not supported.",
                    "HTTP_ROUTE",
                ),
                status=404,
            )
            return
        if method != "GET":
            await self._send_failure(
                send,
                self._unsupported(
                    "The requested HTTP method is not supported.",
                    route_match[0].query_id,
                ),
                status=405,
                additional_headers=((b"allow", b"GET"),),
            )
            return

        if await self._request_has_body(receive):
            await self._send_failure(
                send,
                self._unsupported(
                    "Public GET requests do not accept a request body.",
                    route_match[0].query_id,
                ),
                status=400,
            )
            return

        route, path_values = route_match
        try:
            query_values = self._parse_query_string(scope.get("query_string", b""))
            query = self._build_query(route, path_values, query_values)
        except (UnicodeError, ValueError, ValidationError):
            await self._send_failure(
                send,
                self._unsupported(
                    "The public query parameters do not satisfy the route contract.",
                    route.query_id,
                    query_values if "query_values" in locals() else None,
                ),
                status=400,
            )
            return

        try:
            result = self._executor.execute(query)
        except Exception:
            await self._send_failure(
                send,
                StartupFailureEnvelope(
                    error_code="DEMO_NOT_INITIALISED",
                    message="The public demo is unavailable.",
                    scenario_ref=query.scenario_ref,
                    subject_ref=query.query_id,
                ),
                status=503,
            )
            return
        if hasattr(result, "view_contract"):
            await self._send_model(send, result, status=200)
            return
        await self._send_failure(
            send,
            cast(PublicFailureEnvelope, result),
            status=_FAILURE_STATUS[result.error_code],
        )

    @staticmethod
    def _match_route(path: str) -> tuple[PublicHttpRoute, dict[str, str]] | None:
        for route in PUBLIC_HTTP_ROUTES:
            values = route.match(path)
            if values is not None:
                return route, values
        return None

    @staticmethod
    async def _request_has_body(receive: AsgiReceive) -> bool:
        size = 0
        more_body = True
        while more_body:
            message = await receive()
            if message.get("type") == "http.disconnect":
                break
            if message.get("type") != "http.request":
                raise RuntimeError("Unexpected ASGI receive message")
            body = message.get("body", b"")
            if not isinstance(body, bytes):
                raise RuntimeError("ASGI request body must be bytes")
            size += len(body)
            if size >= _MAX_REQUEST_BODY_BYTES:
                return True
            more_body = bool(message.get("more_body", False))
        return False

    @staticmethod
    def _parse_query_string(raw: object) -> dict[str, str]:
        if not isinstance(raw, bytes):
            raise ValueError("ASGI query_string must be bytes")
        pairs = parse_qsl(
            raw.decode("ascii"),
            keep_blank_values=True,
            strict_parsing=True,
            encoding="utf-8",
            errors="strict",
            max_num_fields=8,
        )
        values: dict[str, str] = {}
        for key, value in pairs:
            if key in values:
                raise ValueError("duplicate query parameter")
            values[key] = value
        return values

    def _build_query(
        self,
        route: PublicHttpRoute,
        path_values: Mapping[str, str],
        query_values: Mapping[str, str],
    ) -> PublicQuery:
        allowed = set(route.allowed_query_fields)
        if set(query_values) != allowed:
            raise ValueError("query fields must match the route contract exactly")
        if query_values["view_contract_version"] != "1":
            raise ValueError("view contract version is unsupported")

        payload: dict[str, object] = {
            "query_id": route.query_id,
            "view_contract_version": 1,
            **path_values,
            **{
                key: value
                for key, value in query_values.items()
                if key != "view_contract_version"
            },
        }
        if route.query_id == "O-Q01":
            payload["workspace_ref"] = self._workspace_ref
        return PUBLIC_QUERY_ADAPTER.validate_python(payload)

    @staticmethod
    def _unsupported(
        message: str,
        subject_ref: str,
        query_values: Mapping[str, str] | None = None,
    ) -> StartupFailureEnvelope:
        candidate = (query_values or {}).get("scenario_ref", "UNRESOLVED")
        scenario_ref = (
            candidate
            if candidate and candidate.isascii()
            else "UNRESOLVED"
        )
        return StartupFailureEnvelope(
            error_code="UNSUPPORTED_CONTRACT",
            message=message,
            scenario_ref=scenario_ref,
            subject_ref=subject_ref,
        )

    @classmethod
    async def _send_failure(
        cls,
        send: AsgiSend,
        failure: PublicFailureEnvelope,
        *,
        status: int,
        additional_headers: tuple[tuple[bytes, bytes], ...] = (),
    ) -> None:
        await cls._send_model(
            send,
            failure,
            status=status,
            additional_headers=additional_headers,
        )

    @staticmethod
    async def _send_model(
        send: AsgiSend,
        model: PublicSuccessEnvelope | PublicFailureEnvelope,
        *,
        status: int,
        additional_headers: tuple[tuple[bytes, bytes], ...] = (),
    ) -> None:
        body = canonical_bytes(model.model_dump(mode="json"))
        headers = (
            (b"content-type", b"application/json; charset=utf-8"),
            (b"cache-control", b"no-store"),
            (b"x-content-type-options", b"nosniff"),
            *additional_headers,
        )
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": list(headers),
            }
        )
        await send({"type": "http.response.body", "body": body})
