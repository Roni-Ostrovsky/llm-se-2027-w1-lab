"""Command line: take an issue, print its triage record as JSON.

    uv run python -m triage.cli issue.json              # one issue object from a file
    uv run python -m triage.cli -  < issue.json         # ... or from stdin
    uv run python -m triage.cli --split dev --repo hono --number 3891
    uv run python -m triage.cli --split dev --limit 20  # first N issues, one record per line

Output is ASCII-only JSON: issue text is untrusted, and escaping it means no
terminal control sequence in a title can reach your terminal unescaped.
Exit status is 1 if any record has status "error", 2 for bad input.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from dotenv import load_dotenv
from pydantic import TypeAdapter, ValidationError

from triage.schema import Issue, Predictor, TriageRecord
from triage.taxonomy import ROOT
from triage.triage import triage_issue

SNAPSHOT = ROOT / "data" / "snapshot"
# test.json is sealed for the rest of the course; there is no way to ask for it.
READABLE_SPLITS = ("train", "dev")


def load_split(split: str) -> list[Issue]:
    if split not in READABLE_SPLITS:
        raise ValueError(f"split {split!r} is not readable (allowed: {', '.join(READABLE_SPLITS)})")
    data = (SNAPSHOT / f"{split}.json").read_bytes()
    return TypeAdapter(list[Issue]).validate_json(data)


def select_issues(args: argparse.Namespace) -> list[Issue]:
    if args.split is None:
        if args.issue is None:
            raise ValueError("give an issue file, '-' for stdin, or --split")
        text = sys.stdin.read() if args.issue == "-" else Path(args.issue).read_text(encoding="utf-8")
        return [Issue.model_validate_json(text)]

    issues = load_split(args.split)
    if args.repo is not None:
        issues = [i for i in issues if i.repo == args.repo]
    if args.number is not None:
        issues = [i for i in issues if i.number == args.number]
        if not issues:
            raise ValueError(f"no issue #{args.number} in {args.split}")
        return issues[:1]
    return issues[: args.limit]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="triage", description="Print a triage record for a GitHub issue.")
    parser.add_argument("issue", nargs="?", help="path to an issue JSON object, or '-' for stdin")
    parser.add_argument("--split", choices=READABLE_SPLITS, help="read issues from data/snapshot/<split>.json")
    parser.add_argument("--repo", help="with --split: only this repo (litestar, hono, textual)")
    parser.add_argument("--number", type=int, help="with --split: the issue with this number")
    parser.add_argument("--limit", type=int, default=1, help="with --split: how many issues (default 1)")
    parser.add_argument("--model", help="DSPy model string; defaults to LLM_MODEL from .env")
    return parser


def main(argv: Sequence[str] | None = None, predict: Predictor | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        issues = select_issues(args)
    except (OSError, ValueError, ValidationError) as exc:
        print(f"triage: {exc}", file=sys.stderr)
        return 2

    model: str | None = args.model
    if predict is None:
        from triage.extract import configured_model, predictor  # deferred: imports dspy

        load_dotenv(ROOT / ".env")
        try:
            model = model or configured_model()
        except RuntimeError as exc:
            print(f"triage: {exc}", file=sys.stderr)
            return 2
        predict = predictor(model)

    records: list[TriageRecord] = [triage_issue(issue, predict, model=model) for issue in issues]
    indent = 2 if len(records) == 1 else None
    for record in records:
        print(json.dumps(record.model_dump(mode="json"), indent=indent, ensure_ascii=True))
    return 1 if any(r.status == "error" for r in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
