"""Immutable assertion values owned by the validation harness."""

from dataclasses import dataclass
from enum import StrEnum

from finance_assurance.runtime.rejections import Detail
from finance_assurance.runtime.rejections import Rejection as Rejection
from finance_assurance.runtime.rejections import RejectionCode as RejectionCode


class AssertionStatus(StrEnum):
    """Permitted Artifact H assertion outcomes."""

    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class AssertionResult:
    """One complete Artifact H assertion result."""

    test_id: str
    layer: str
    source_obligation: str
    status: AssertionStatus
    expected_outcome: str
    actual_outcome: str
    references: tuple[str, ...] = ()
    before_digest: str | None = None
    after_digest: str | None = None
    failure_details: tuple[Detail, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "test_id",
            "layer",
            "source_obligation",
            "expected_outcome",
            "actual_outcome",
        ):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True, slots=True)
class StatusCount:
    status: AssertionStatus
    count: int

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ValueError("status count must be non-negative")


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Complete semantic report passed to a report sink."""

    schema_version: str
    repository_revision: str | None
    fixture_inventory_digest: str
    contract_inventory_digest: str
    status_counts: tuple[StatusCount, ...]
    results: tuple[AssertionResult, ...]
    c001_state_digest: str
    ct1_state_digest: str
    overall: AssertionStatus

    def __post_init__(self) -> None:
        for field_name in (
            "schema_version",
            "fixture_inventory_digest",
            "contract_inventory_digest",
            "c001_state_digest",
            "ct1_state_digest",
        ):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} must not be empty")
        if tuple(item.status for item in self.status_counts) != tuple(AssertionStatus):
            raise ValueError("status counts must use PASS, FAIL, BLOCKED order")
        actual_counts = {
            status: sum(result.status is status for result in self.results)
            for status in AssertionStatus
        }
        if any(
            item.count != actual_counts[item.status] for item in self.status_counts
        ):
            raise ValueError("status counts must reconcile to report results")
        statuses = {result.status for result in self.results}
        if AssertionStatus.FAIL in statuses:
            expected_overall = AssertionStatus.FAIL
        elif AssertionStatus.BLOCKED in statuses:
            expected_overall = AssertionStatus.BLOCKED
        else:
            expected_overall = AssertionStatus.PASS
        if self.overall is not expected_overall:
            raise ValueError("overall status must reconcile to report results")
