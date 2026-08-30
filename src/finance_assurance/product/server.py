"""Local ASGI composition root for the bounded public product."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path

from finance_assurance.product.demo_lifecycle import DemoLifecycleService
from finance_assurance.product.demo_scenarios import (
    DemoScenarioSet,
    default_demo_scenarios,
)
from finance_assurance.product.http_adapter import PublicHttpAdapter
from finance_assurance.product.query_service import PublicQueryService
from finance_assurance.runtime.persistence.sqlite import SqlitePersistenceBoundary

type AsgiMessage = dict[str, object]
type AsgiReceive = Callable[[], Awaitable[AsgiMessage]]
type AsgiSend = Callable[[AsgiMessage], Awaitable[None]]


class PublicProductApplication:
    """Own one verified demo boundary for an ASGI process lifetime."""

    def __init__(
        self,
        database: Path,
        *,
        workspace_ref: str,
        scenarios: DemoScenarioSet,
    ) -> None:
        self._database = database
        self._workspace_ref = workspace_ref
        self._scenarios = scenarios
        self._boundary: SqlitePersistenceBoundary | None = None
        self._http: PublicHttpAdapter | None = None

    async def __call__(
        self,
        scope: Mapping[str, object],
        receive: AsgiReceive,
        send: AsgiSend,
    ) -> None:
        scope_type = scope.get("type")
        if scope_type == "lifespan":
            await self._lifespan(receive, send)
            return
        if scope_type != "http":
            raise RuntimeError("PublicProductApplication supports HTTP and lifespan")
        if self._http is None:
            self.start()
        assert self._http is not None
        await self._http(scope, receive, send)

    def start(self) -> None:
        """Initialise or verify the disposable demo, then open its read boundary."""

        if self._http is not None:
            return
        lifecycle = DemoLifecycleService()
        if self._database.exists():
            lifecycle.verify(
                self._database,
                workspace_ref=self._workspace_ref,
                scenarios=self._scenarios,
            )
        else:
            lifecycle.initialise(
                self._database,
                workspace_ref=self._workspace_ref,
                scenarios=self._scenarios,
            )
        boundary = SqlitePersistenceBoundary(self._database)
        self._boundary = boundary
        self._http = PublicHttpAdapter(
            PublicQueryService(
                boundary,
                scenarios=self._scenarios,
                workspace_ref=self._workspace_ref,
            ),
            workspace_ref=self._workspace_ref,
        )

    def close(self) -> None:
        """Release the process-owned read boundary without mutating demo state."""

        if self._boundary is not None:
            self._boundary.close()
        self._boundary = None
        self._http = None

    async def _lifespan(self, receive: AsgiReceive, send: AsgiSend) -> None:
        while True:
            message = await receive()
            message_type = message.get("type")
            if message_type == "lifespan.startup":
                try:
                    self.start()
                except Exception:
                    await send(
                        {
                            "type": "lifespan.startup.failed",
                            "message": "The public demo could not be initialised.",
                        }
                    )
                    return
                await send({"type": "lifespan.startup.complete"})
            elif message_type == "lifespan.shutdown":
                self.close()
                await send({"type": "lifespan.shutdown.complete"})
                return
            else:
                raise RuntimeError("Unexpected ASGI lifespan message")


def create_public_product_app(
    database: Path,
    *,
    workspace_ref: str = "PUBLIC-DEMO",
    scenarios: DemoScenarioSet | None = None,
) -> PublicProductApplication:
    """Construct the local product process without initialising it at import time."""

    return PublicProductApplication(
        database,
        workspace_ref=workspace_ref,
        scenarios=scenarios or default_demo_scenarios(),
    )


def _default_database() -> Path:
    configured = os.environ.get("FINANCE_ASSURANCE_DEMO_DB")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.cwd() / "build" / "public-demo.sqlite3").resolve()


app = create_public_product_app(_default_database())
