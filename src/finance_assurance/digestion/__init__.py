"""Artifact R model-digestion contracts and finite registries.

The application service resolves lazily so metadata-only consumers retain
the R1 cold-start boundary and do not load package verification or I/O code.
"""

from importlib import import_module

from finance_assurance.digestion.contracts import (
    BuildConsumerModel,
    BuildConsumerModelResult,
    DuckDBCacheTableBinding,
    ModelManifest,
    NoncanonicalCacheManifest,
    ReproduceConsumerModel,
    ReproduceConsumerModelResult,
    SemanticCatalogue,
    SemanticTable,
    VerifyConsumerModel,
    VerifyConsumerModelResult,
)
from finance_assurance.digestion.registry import (
    COLUMN_ROLE_REGISTRY,
    MEASURE_REGISTRY,
    PROFILE_DATASET_IDS,
    RELATIONSHIP_KEY_PROJECTIONS,
    relationship_plan,
    validate_registry,
    validate_relationship_graph,
)
from finance_assurance.digestion.writer import (
    PARQUET_WRITER_PROFILE,
    validate_writer_runtime,
)

__all__ = [
    "COLUMN_ROLE_REGISTRY",
    "MEASURE_REGISTRY",
    "PARQUET_WRITER_PROFILE",
    "PROFILE_DATASET_IDS",
    "RELATIONSHIP_KEY_PROJECTIONS",
    "BuildConsumerModel",
    "BuildConsumerModelResult",
    "ConsumerModelError",
    "ConsumerModelService",
    "DuckDBCacheTableBinding",
    "ModelManifest",
    "NoncanonicalCacheManifest",
    "ReproduceConsumerModel",
    "ReproduceConsumerModelResult",
    "SemanticCatalogue",
    "SemanticTable",
    "VerifyConsumerModel",
    "VerifyConsumerModelResult",
    "model_registry_binding",
    "relationship_plan",
    "validate_registry",
    "validate_relationship_graph",
    "validate_writer_runtime",
    "verify_consumer_model",
]

_SERVICE_EXPORTS = {
    "ConsumerModelError",
    "ConsumerModelService",
    "model_registry_binding",
    "verify_consumer_model",
}


def __getattr__(name: str) -> object:
    if name not in _SERVICE_EXPORTS:
        raise AttributeError(name)
    value = getattr(import_module(".service", __name__), name)
    globals()[name] = value
    return value
