from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from finance_assurance.product.demo_lifecycle import (
    DemoAlreadyExistsError,
    DemoLifecycleService,
    DemoWorkspaceUnrecognisedError,
)
from finance_assurance.product.demo_scenarios import default_demo_scenarios


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_demo_lifecycle_is_deterministic_read_only_and_complete(
    tmp_path: Path,
) -> None:
    target = tmp_path / "demo.sqlite3"
    scenarios = default_demo_scenarios()
    service = DemoLifecycleService()

    created = service.initialise(
        target,
        workspace_ref="TEST-DEMO",
        scenarios=scenarios,
    )
    before_verify = _sha256(target)
    verified = service.verify(
        target,
        workspace_ref="TEST-DEMO",
        scenarios=scenarios,
    )
    after_verify = _sha256(target)
    recreated = service.recreate(
        target,
        workspace_ref="TEST-DEMO",
        scenarios=scenarios,
    )

    assert created.operation == "O-C01"
    assert recreated.operation == "O-C02"
    assert created.verification.passed
    assert verified.passed
    assert recreated.verification.passed
    assert before_verify == after_verify
    assert verified.read_only_verified
    assert [item.event_count for item in verified.scenario_verification] == [11, 6]
    assert all(item.available for item in verified.view_verification)
    assert len(verified.view_verification) == 11
    assert (
        verified.semantic_state_digest
        == verified.restart_semantic_digest
        == verified.rebuilt_semantic_digest
        == recreated.verification.semantic_state_digest
    )
    assert (
        verified.authoritative_inventory_digest
        == recreated.verification.authoritative_inventory_digest
    )

    with pytest.raises(DemoAlreadyExistsError):
        service.initialise(
            target,
            workspace_ref="TEST-DEMO",
            scenarios=scenarios,
        )


def test_recreate_failure_preserves_prior_workspace_atomically(tmp_path: Path) -> None:
    target = tmp_path / "demo.sqlite3"
    scenarios = default_demo_scenarios()
    DemoLifecycleService().initialise(
        target,
        workspace_ref="TEST-DEMO",
        scenarios=scenarios,
    )
    before = target.read_bytes()

    def fail_before_replace(stage: str) -> None:
        if stage == "before_replace":
            raise RuntimeError("injected replacement failure")

    with pytest.raises(RuntimeError, match="injected replacement failure"):
        DemoLifecycleService(fault_injector=fail_before_replace).recreate(
            target,
            workspace_ref="TEST-DEMO",
            scenarios=scenarios,
        )

    assert target.read_bytes() == before
    assert not tuple(tmp_path.glob("*.building"))


def test_unrecognised_workspace_rejection_is_read_only(tmp_path: Path) -> None:
    target = tmp_path / "not-a-demo.sqlite3"
    original = b"not an Artifact O workspace"
    target.write_bytes(original)

    with pytest.raises(DemoWorkspaceUnrecognisedError):
        DemoLifecycleService().verify(
            target,
            workspace_ref="TEST-DEMO",
            scenarios=default_demo_scenarios(),
        )

    assert target.read_bytes() == original
