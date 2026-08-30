"""Static guards for Milestone 2's deliberately bounded product scope."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

DEFERRED_RUNTIME_PACKAGES = frozenset({"api", "auth", "broker", "graphql", "http", "ui", "web", "workers"})
DEFERRED_DEPENDENCIES = frozenset({"django", "fastapi", "flask", "graphql-core", "pyjwt", "sqlalchemy", "starlette"})


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def runtime_validation_imports(root: Path | None = None) -> tuple[str, ...]:
    """Return forbidden validation imports found inside the runtime package."""

    base = (root or repository_root()) / "src" / "finance_assurance" / "runtime"
    violations: list[str] = []
    for path in sorted(base.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: tuple[str, ...] = ()
            if isinstance(node, ast.Import):
                names = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = (node.module,)
            if any(name.startswith("finance_assurance.validation") for name in names):
                violations.append(path.relative_to(base).as_posix())
    return tuple(sorted(set(violations)))


def deferred_surface_violations(root: Path | None = None) -> tuple[str, ...]:
    """Return packages or dependencies that would expand Milestone 2 scope."""

    repo = root or repository_root()
    runtime = repo / "src" / "finance_assurance" / "runtime"
    violations = {
        path.name
        for path in runtime.iterdir()
        if path.is_dir() and path.name.lower() in DEFERRED_RUNTIME_PACKAGES
    }
    project = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
    for declaration in project["project"].get("dependencies", []):
        name = declaration.split("[", 1)[0].split("=", 1)[0].split("<", 1)[0]
        if name.strip().lower() in DEFERRED_DEPENDENCIES:
            violations.add(name.strip().lower())
    return tuple(sorted(violations))
