"""Derive ground-truth labels from GitHub labels, and split the dataset.

This is the step that turns "issues we downloaded" into "a dataset with gold
labels". Read it carefully: what it can and cannot label is the single most
important fact about every evaluation you will run for the rest of the course.

Usage
-----
    uv run python tools/classify_issues.py
    uv run python tools/classify_issues.py --report   # coverage stats only

Ground truth, honestly
----------------------
issue_type   GOLD, where a mapped label is present. Coverage varies a lot by
             repo - textual is sparsely labelled on purpose.
component    GOLD, where present. PER-REPO taxonomy. Do not pool across repos:
             hono's "middleware" and litestar's "openapi" are not the same
             kind of category, and averaging accuracy over both is meaningless.
has_repro    NO GOLD. Must be hand-labelled if you want to measure it.
severity     NO GOLD. None of these three projects maintains a severity or
             priority taxonomy. If you need it, you build the gold set.
duplicate    NO GOLD here. Recoverable later from closed-as-duplicate links,
             which this script does not attempt.

An issue with no mapped label gets gold_type = null. That is not a bug. It is
an unlabelled example, and how you handle unlabelled data is a real decision
you have to make and defend, not a nuisance to filter away silently.

Splits
------
train / dev / test at 60 / 20 / 20, stratified by repo, seeded and therefore
reproducible. The test split is SEALED: do not look at it, do not tune against
it, do not let an agent read it. You will use it much later in the course, and
its value depends entirely on it staying unseen.
"""

from __future__ import annotations

import argparse
import json
import random
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "repos.toml"
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "snapshot"

SEED = 20270101
SPLITS = (("train", 0.6), ("dev", 0.2), ("test", 0.2))


def load_config() -> list[dict[str, Any]]:
    with CONFIG.open("rb") as fh:
        return tomllib.load(fh)["repos"]


def build_lookup(mapping: dict[str, list[str]]) -> dict[str, str]:
    """Invert {category: [label, ...]} into {label_lowercased: category}."""
    out: dict[str, str] = {}
    for category, labels in mapping.items():
        for label in labels:
            out[label.lower()] = category
    return out


def classify(issue: dict[str, Any], types: dict[str, str], comps: dict[str, str]) -> dict[str, Any]:
    labels = [lbl.lower() for lbl in issue["labels"]]
    gold_type = next((types[lbl] for lbl in labels if lbl in types), None)
    gold_component = next((comps[lbl] for lbl in labels if lbl in comps), None)
    return {
        **issue,
        "gold_type": gold_type,
        "gold_component": gold_component,
        # Fields with no available ground truth. Present so the schema is
        # uniform and so their emptiness is visible rather than implicit.
        "gold_has_reproduction_steps": None,
        "gold_severity": None,
        "gold_duplicate_candidate": None,
    }


def report(rows: list[dict[str, Any]]) -> None:
    by_repo: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_repo.setdefault(row["repo"], []).append(row)

    print(f"{'repo':<12} {'n':>5} {'typed':>7} {'cov%':>6}  type distribution")
    print("-" * 74)
    for repo, items in sorted(by_repo.items()):
        typed = [i for i in items if i["gold_type"]]
        dist = Counter(i["gold_type"] for i in typed)
        pct = 100.0 * len(typed) / len(items) if items else 0.0
        summary = ", ".join(f"{k}={v}" for k, v in dist.most_common())
        print(f"{repo:<12} {len(items):>5} {len(typed):>7} {pct:>5.1f}%  {summary}")

    print("\nComponent coverage (gold labels present):")
    for repo, items in sorted(by_repo.items()):
        comp = Counter(i["gold_component"] for i in items if i["gold_component"])
        total = sum(comp.values())
        detail = ", ".join(f"{k}={v}" for k, v in comp.most_common()) or "none"
        print(f"  {repo:<12} {total:>4}  {detail}")

    print("\nNo ground truth available for: severity, has_reproduction_steps, duplicate_candidate")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", action="store_true", help="print coverage and exit")
    args = ap.parse_args()

    rows: list[dict[str, Any]] = []
    for repo in load_config():
        src = RAW_DIR / f"{repo['key']}.json"
        if not src.exists():
            print(f"missing {src.relative_to(ROOT)} - run tools/fetch_issues.py first")
            continue
        types = build_lookup(repo.get("issue_type_labels", {}))
        comps = build_lookup(repo.get("component_labels", {}))
        issues = json.loads(src.read_text(encoding="utf-8"))
        rows.extend(classify(i, types, comps) for i in issues)

    if not rows:
        raise SystemExit("no input data")

    report(rows)
    if args.report:
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    # Stratify by repo so every split contains all three projects in
    # proportion. Without this, a random split can leave one repo badly
    # under-represented in dev and make your numbers unstable.
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        buckets.setdefault(row["repo"], []).append(row)

    splits: dict[str, list[dict[str, Any]]] = {name: [] for name, _ in SPLITS}
    for items in buckets.values():
        rng.shuffle(items)
        start = 0
        for idx, (name, frac) in enumerate(SPLITS):
            end = len(items) if idx == len(SPLITS) - 1 else start + int(len(items) * frac)
            splits[name].extend(items[start:end])
            start = end

    for name, items in splits.items():
        items.sort(key=lambda r: (r["repo"], r["number"]))
        dest = OUT_DIR / f"{name}.json"
        dest.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {len(items):>4} -> {dest.relative_to(ROOT)}")

    (OUT_DIR / "MANIFEST.md").write_text(
        "# Dataset manifest\n\n"
        f"Seed: {SEED}\n\n"
        f"Splits: {', '.join(f'{n} {int(f * 100)}%' for n, f in SPLITS)}, stratified by repo.\n\n"
        "`test.json` is SEALED. Do not read it, tune against it, or let an agent\n"
        "index it. Its only value is that it has never been seen.\n\n"
        "Gold labels: `gold_type`, `gold_component` (per-repo taxonomy).\n"
        "No gold labels: severity, has_reproduction_steps, duplicate_candidate.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
