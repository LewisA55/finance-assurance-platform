from __future__ import annotations

import subprocess
import sys


def test_persistence_memory_adapter_imports_in_a_fresh_interpreter() -> None:
    result = subprocess.run(
        (
            sys.executable,
            "-c",
            "from finance_assurance.runtime.persistence.memory import "
            "InMemoryPersistenceBoundary; print(InMemoryPersistenceBoundary.__name__)",
        ),
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "InMemoryPersistenceBoundary"
