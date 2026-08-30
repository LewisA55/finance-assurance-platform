"""Black-box characterization for the extracted Milestone 2 runtime kernel."""

from __future__ import annotations

from inspect import getfile
from pathlib import Path

from finance_assurance.runtime.contracts.events import (
    ACCOUNTING_EVENT_ADAPTER as RUNTIME_EVENT_ADAPTER,
)
from finance_assurance.runtime.contracts.objects import (
    OBJECT_ADAPTERS as RUNTIME_OBJECT_ADAPTERS,
)
from finance_assurance.runtime.planner import plan as runtime_plan
from finance_assurance.runtime.rejections import Rejection as RuntimeRejection
from finance_assurance.validation.contracts.events import (
    ACCOUNTING_EVENT_ADAPTER as VALIDATION_EVENT_ADAPTER,
)
from finance_assurance.validation.contracts.objects import (
    OBJECT_ADAPTERS as VALIDATION_OBJECT_ADAPTERS,
)
from finance_assurance.validation.h2 import run_h2
from finance_assurance.validation.h3_guards import accepted_controls, guard_cases
from finance_assurance.validation.planner import plan as validation_plan
from finance_assurance.validation.results import Rejection as ValidationRejection
from finance_assurance.validation.state import stable_value, value_digest

GUARD_VECTOR_DIGEST = (
    "sha256:bf8241b979f20e626f7d14e471a14ad90f93195f7d610f28e21663da6b8fcb49"
)
ACCEPTED_VECTOR_DIGEST = (
    "sha256:e493dd70f0a83b12c0a8e50f4e6f876d004e9cf713c8935feca171de55c33773"
)
COMBINED_VECTOR_DIGEST = (
    "sha256:a8cb0dc06380a815febd301d1edba461803330607e016af73ae7ab7a686d4168"
)


def test_runtime_planner_matches_locked_milestone_1_characterization() -> None:
    """All accepted and rejected planner vectors retain their exact semantics."""

    index = run_h2().index
    guards = [
        {
            "test_id": case.test_id,
            "result": stable_value(runtime_plan(command, case.state)),
        }
        for case in guard_cases(index)
        for command in case.commands
    ]
    accepted = [
        {
            "name": control.name,
            "result": stable_value(runtime_plan(control.command, control.state)),
        }
        for control in accepted_controls(index)
    ]

    assert len(guards) == 20
    assert len(accepted) == 13
    assert value_digest(guards) == GUARD_VECTOR_DIGEST
    assert value_digest(accepted) == ACCEPTED_VECTOR_DIGEST
    assert value_digest({"guards": guards, "accepted": accepted}) == (
        COMBINED_VECTOR_DIGEST
    )


def test_validation_facades_resolve_to_runtime_owned_semantics() -> None:
    """Existing H-layer imports remain compatible without owning domain types."""

    assert validation_plan is runtime_plan
    assert ValidationRejection is RuntimeRejection
    assert VALIDATION_EVENT_ADAPTER is RUNTIME_EVENT_ADAPTER
    assert VALIDATION_OBJECT_ADAPTERS is RUNTIME_OBJECT_ADAPTERS


def test_runtime_kernel_has_no_validation_layer_dependency() -> None:
    """Dependency direction remains validation harness to runtime kernel only."""

    runtime_root = Path(getfile(runtime_plan)).parent
    offenders = [
        path
        for path in runtime_root.rglob("*.py")
        if "finance_assurance.validation" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
