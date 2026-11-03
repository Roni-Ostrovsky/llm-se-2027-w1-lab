"""Data shapes on either side of triage: the issue that comes in, the record that goes out."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict

IssueType = Literal["bug", "enhancement", "documentation", "question", "other"]
Severity = Literal["critical", "high", "medium", "low"]
Status = Literal["ok", "error"]

ISSUE_TYPES: tuple[IssueType, ...] = ("bug", "enhancement", "documentation", "question", "other")
SEVERITIES: tuple[Severity, ...] = ("critical", "high", "medium", "low")


class Issue(BaseModel):
    """One GitHub issue, in the shape of the records in data/snapshot/.

    Extra keys (labels, gold_* fields, timestamps) are accepted and dropped:
    triage sees only what a brand-new issue would have.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    repo: str
    number: int
    title: str
    body: str | None = None
    url: str | None = None


class TriageRecord(BaseModel):
    """The structured result that routing consumes.

    When `status` is "error" the classification fields are None and
    `needs_human_review` is True; routing must not guess on its behalf.
    """

    model_config = ConfigDict(frozen=True)

    repo: str
    number: int
    title: str
    url: str | None
    status: Status
    issue_type: IssueType | None
    component: str | None
    severity: Severity | None
    has_reproduction_steps: bool | None
    summary: str | None
    confidence: float
    needs_human_review: bool
    error: str | None
    model: str | None


# What the model boundary hands back: untyped values keyed by field name.
# Everything in it is validated before it reaches a TriageRecord.
Predictor = Callable[[Issue, Sequence[str]], Mapping[str, object]]
