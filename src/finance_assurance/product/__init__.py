"""Read-only public product contracts over the authoritative runtime."""

from finance_assurance.product.contracts import (
    PUBLIC_FAILURE_ADAPTER,
    PUBLIC_SUCCESS_ADAPTER,
    PublicFailureEnvelope,
    PublicSuccessEnvelope,
)
from finance_assurance.product.demo_lifecycle import (
    DemoLifecycleResult,
    DemoLifecycleService,
    DemoVerificationReport,
)
from finance_assurance.product.demo_scenarios import (
    DemoScenarioSet,
    default_demo_scenarios,
)
from finance_assurance.product.http_adapter import (
    PUBLIC_HTTP_ROUTES,
    PublicHttpAdapter,
    PublicHttpRoute,
)
from finance_assurance.product.query_models import PUBLIC_QUERY_ADAPTER, PublicQuery
from finance_assurance.product.query_service import PublicQueryService
from finance_assurance.product.registry import PUBLIC_QUERY_REGISTRY

__all__ = [
    "PUBLIC_FAILURE_ADAPTER",
    "PUBLIC_HTTP_ROUTES",
    "PUBLIC_QUERY_ADAPTER",
    "PUBLIC_QUERY_REGISTRY",
    "PUBLIC_SUCCESS_ADAPTER",
    "DemoLifecycleResult",
    "DemoLifecycleService",
    "DemoScenarioSet",
    "DemoVerificationReport",
    "PublicFailureEnvelope",
    "PublicHttpAdapter",
    "PublicHttpRoute",
    "PublicQuery",
    "PublicQueryService",
    "PublicSuccessEnvelope",
    "default_demo_scenarios",
]
