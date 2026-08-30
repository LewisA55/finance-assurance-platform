"""Strict revision-bound manual browser evidence for Artifact O."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ManualStatus = Literal["PASS", "FAIL", "BLOCKED"]


class ViewportEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    name: Literal["desktop", "tablet", "mobile"]
    width: int = Field(ge=320)
    height: int = Field(ge=480)


class ManualChecks(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    keyboard_traversal: bool
    visible_focus: bool
    skip_and_bottom_navigation: bool
    screen_reader_names_and_order: bool
    no_horizontal_overflow: bool
    exact_context_preserved: bool
    screenshots_recorded: bool


class ScreenshotEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    viewport: Literal["desktop", "tablet", "mobile"]
    path: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class ManualBrowserEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal["milestone-3-manual-browser-evidence@v1"]
    repository_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    reviewer: str = Field(min_length=1)
    reviewed_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    journeys: tuple[Literal["overview", "O-J01", "O-J02", "O-J03", "O-SJ01"], ...]
    viewports: tuple[ViewportEvidence, ...]
    checks: ManualChecks
    screenshots: tuple[ScreenshotEvidence, ...]


@dataclass(frozen=True, slots=True)
class ManualReviewResult:
    status: ManualStatus
    evidence_digest: str | None
    outcome: str


def evaluate_manual_evidence(path: Path, *, repository_revision: str | None) -> ManualReviewResult:
    """Validate complete manual evidence without weakening missing to passing."""

    if not path.exists():
        return ManualReviewResult("BLOCKED", None, f"manual browser evidence is absent: {path.as_posix()}")
    payload = path.read_bytes()
    try:
        evidence = ManualBrowserEvidence.model_validate_json(payload)
    except ValidationError as error:
        return ManualReviewResult("FAIL", None, f"invalid manual evidence: {error}")
    if repository_revision is None or evidence.repository_revision != repository_revision:
        return ManualReviewResult("FAIL", None, "manual evidence is not bound to the accepted repository revision")
    if evidence.journeys != ("overview", "O-J01", "O-J02", "O-J03", "O-SJ01"):
        return ManualReviewResult("FAIL", None, "manual journey coverage is incomplete")
    if tuple(item.name for item in evidence.viewports) != ("desktop", "tablet", "mobile"):
        return ManualReviewResult("FAIL", None, "manual viewport coverage is incomplete")
    if not all(evidence.checks.model_dump().values()) or not evidence.screenshots:
        return ManualReviewResult("FAIL", None, "one or more manual checks did not pass")
    return ManualReviewResult("PASS", f"sha256:{hashlib.sha256(payload).hexdigest()}", "revision-bound desktop, tablet, mobile, keyboard, and screen-reader review passed")
