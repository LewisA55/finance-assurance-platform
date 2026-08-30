"""Deterministic validation harness for the ratified platform architecture."""


def main() -> int:
    """Load and run the harness without importing the runner eagerly."""

    from finance_assurance.validation.runner import main as run

    return run()


__all__ = ["main"]
