"""Canonical machine-report sinks for the ordered Artifact H result."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from finance_assurance.validation.canonical import canonical_bytes
from finance_assurance.validation.results import ValidationReport
from finance_assurance.validation.state import stable_value


@runtime_checkable
class ReportSink(Protocol):
    """Writes a completed report without changing its semantic content."""

    def write(self, report: ValidationReport) -> None:
        """Write one complete validation report."""


def report_bytes(report: ValidationReport) -> bytes:
    """Return the complete semantic report as canonical UTF-8 JSON."""

    return canonical_bytes(stable_value(report))


@dataclass(slots=True)
class MemoryReportSink:
    content: bytes | None = None

    def write(self, report: ValidationReport) -> None:
        self.content = report_bytes(report)


@dataclass(frozen=True, slots=True)
class JsonFileReportSink:
    path: Path

    def write(self, report: ValidationReport) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(report_bytes(report))


def parse_report_bytes(content: bytes) -> dict[str, object]:
    """Parse a sink result for H7 round-trip assertions."""

    value = json.loads(content.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("validation report must be one JSON object")
    return value
