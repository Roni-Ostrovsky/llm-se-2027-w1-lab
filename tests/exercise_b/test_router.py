from typing import Any

from triage_by_agent.router import route
from triage_by_agent.schema import TriageRecord


def rec(**kw: Any) -> TriageRecord:
    base: dict[str, Any] = dict(
        issue_number=1,
        repo="hono",
        issue_type="bug",
        component="middleware",
        severity="medium",
        has_reproduction_steps=True,
        confidence=0.9,
    )
    base.update(kw)
    return TriageRecord(**base)


def test_bug_goes_to_engineering() -> None:
    assert route(rec()).queue == "engineering"


def test_bug_without_repro_is_held() -> None:
    assert route(rec(has_reproduction_steps=False)).queue == "triage-clarify"


def test_critical_escalates() -> None:
    r = route(rec(severity="critical"))
    assert r.escalate
    assert r.sla_hours == 4


def test_low_confidence_high_severity_escalates() -> None:
    assert route(rec(severity="high", confidence=0.4)).escalate


def test_enhancement_goes_to_product() -> None:
    assert route(rec(issue_type="enhancement")).queue == "product"
