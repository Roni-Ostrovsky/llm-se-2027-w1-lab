"""Turn one issue into one TriageRecord, validating whatever the model said."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ValidationError, field_validator

from triage.schema import Issue, IssueType, Predictor, Severity, TriageRecord
from triage.taxonomy import components_for

# Bodies longer than this are cut before they reach the model. Almost all dev
# issues fit; the few that do not are mostly pasted logs.
MAX_BODY_CHARS = 8000
MAX_SUMMARY_CHARS = 200
# Below this self-reported confidence a record is flagged for a person.
REVIEW_CONFIDENCE = 0.7
MAX_ERROR_CHARS = 300


class _ModelOutput(BaseModel):
    """The model's answer, checked field by field. Any failure rejects the whole answer."""

    issue_type: IssueType
    component: str | None
    severity: Severity
    has_reproduction_steps: bool
    summary: str
    confidence: float

    @field_validator("issue_type", "severity", mode="before")
    @classmethod
    def _lowercase(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("summary")
    @classmethod
    def _one_line(cls, value: str) -> str:
        text = " ".join(value.split())
        if not text:
            raise ValueError("empty summary")
        return text[:MAX_SUMMARY_CHARS]

    @field_validator("confidence")
    @classmethod
    def _unit_interval(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


def prepare(issue: Issue) -> Issue:
    """The issue as the model sees it: body cut to MAX_BODY_CHARS."""
    body = issue.body or ""
    if len(body) > MAX_BODY_CHARS:
        body = body[:MAX_BODY_CHARS] + "\n[truncated]"
    return issue.model_copy(update={"body": body})


def _match_component(value: str | None, allowed: tuple[str, ...]) -> str | None:
    """`value` if it names one of `allowed` (case-insensitively), else None."""
    if value is None:
        return None
    wanted = value.strip().lower()
    return next((name for name in allowed if name.lower() == wanted), None)


def triage_issue(issue: Issue, predict: Predictor, *, model: str | None = None) -> TriageRecord:
    """Classify `issue`. Never raises for a model failure; returns an error record instead."""
    allowed = components_for(issue.repo)
    try:
        raw: Mapping[str, object] = predict(prepare(issue), allowed)
        out = _ModelOutput.model_validate(dict(raw))
    except ValidationError as exc:
        fields = ", ".join(str(e["loc"][0]) if e["loc"] else "?" for e in exc.errors())
        return _error_record(issue, model, f"model output failed validation: {fields}")
    except Exception as exc:  # the model boundary: network, provider, or DSPy parse failure
        return _error_record(issue, model, f"{type(exc).__name__}: {exc}")

    return TriageRecord(
        repo=issue.repo,
        number=issue.number,
        title=issue.title,
        url=issue.url,
        status="ok",
        issue_type=out.issue_type,
        component=_match_component(out.component, allowed),
        severity=out.severity,
        has_reproduction_steps=out.has_reproduction_steps,
        summary=out.summary,
        confidence=out.confidence,
        needs_human_review=out.confidence < REVIEW_CONFIDENCE or out.issue_type == "other",
        error=None,
        model=model,
    )


def _error_record(issue: Issue, model: str | None, message: str) -> TriageRecord:
    return TriageRecord(
        repo=issue.repo,
        number=issue.number,
        title=issue.title,
        url=issue.url,
        status="error",
        issue_type=None,
        component=None,
        severity=None,
        has_reproduction_steps=None,
        summary=None,
        confidence=0.0,
        needs_human_review=True,
        error=message[:MAX_ERROR_CHARS],
        model=model,
    )
