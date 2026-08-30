"""Governed synthetic-output package boundary (Artifact P).

Exports are resolved lazily so metadata-only consumers such as Artifact R can
read the P registry without importing Artifact O's runtime-facing contracts.
"""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "BuildGovernedExport",
    "BuildGovernedExportResult",
    "ExportDiscoveryDescriptor",
    "ExportDiscoveryView",
    "ExportSubjectSet",
    "VerificationResult",
    "build_export_discovery",
    "compile_export_discovery",
]

_EXPORT_MODULES = {
    "BuildGovernedExport": ".contracts",
    "BuildGovernedExportResult": ".contracts",
    "ExportDiscoveryDescriptor": ".contracts",
    "ExportDiscoveryView": ".contracts",
    "ExportSubjectSet": ".discovery",
    "VerificationResult": ".contracts",
    "build_export_discovery": ".discovery",
    "compile_export_discovery": ".discovery",
}


def __getattr__(name: str) -> object:
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(name)
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value
