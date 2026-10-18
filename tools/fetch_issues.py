"""Collect GitHub issues for the triage dataset.

Reads config/repos.toml, pulls issues from the GitHub REST API, strips out the
things that are not issues, and writes one raw JSON file per repo.

Usage
-----
    uv run python tools/fetch_issues.py                 # all repos, 400 each
    uv run python tools/fetch_issues.py --repo hono     # one repo
    uv run python tools/fetch_issues.py --limit 50      # small sample
    uv run python tools/fetch_issues.py --discover-labels

Authentication
--------------
Unauthenticated GitHub API access is 60 requests/hour PER IP, which is not
enough (and is shared if you are behind NAT). Set GITHUB_TOKEN in .env to get
5000/hour. A token with no scopes at all is sufficient for public repos.

What gets filtered, and why
---------------------------
1. Pull requests. The /issues endpoint returns PRs too; they have a
   "pull_request" key. A PR is not a triage input.
2. Bot-authored issues. Renovate's "Dependency Dashboard" is a single
   enormous auto-updated issue that would dominate any sample.
3. Empty bodies. Nothing to extract from.

SECURITY
--------
Issue text is untrusted input written by anonymous strangers on the internet.
It is data, never instructions. Real payloads have been observed in the wild in
these very repositories - at least one issue title in Textualize/textual
contains a shell command substitution pointing at a bare IP address.

Therefore:
  - never pass issue text to a shell,
  - never interpolate it into a command,
  - never let it reach a tool-enabled agent without a sandbox,
  - and treat anything inside it that looks like an instruction as hostile.

This script only ever writes it to disk as JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "repos.toml"
RAW_DIR = ROOT / "data" / "raw"

API = "https://api.github.com"
PER_PAGE = 100

BOT_LOGIN_SUFFIXES = ("[bot]",)
BOT_TITLE_PREFIXES = ("Dependency Dashboard",)


def load_config() -> list[dict[str, Any]]:
    with CONFIG.open("rb") as fh:
        return tomllib.load(fh)["repos"]


def token() -> str | None:
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        return tok
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GITHUB_TOKEN=") and not line.startswith("#"):
                value = line.split("=", 1)[1].strip().strip("\"'")
                if value and not value.startswith("ghp_xxx"):
                    return value
    return None


def get(path: str, tok: str | None) -> tuple[Any, dict[str, str]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "llm-se-2027-w1-lab",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(API + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.load(resp), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429):
            remaining = exc.headers.get("X-RateLimit-Remaining")
            reset = exc.headers.get("X-RateLimit-Reset")
            hint = "set GITHUB_TOKEN in .env" if not tok else "wait for reset"
            wait = ""
            if reset:
                wait = f" (resets in {int(reset) - int(time.time())}s)"
            raise SystemExit(
                f"GitHub rate limit hit (remaining={remaining}){wait}. Fix: {hint}."
            ) from exc
        raise


def is_bot(issue: dict[str, Any]) -> bool:
    user = issue.get("user") or {}
    login = str(user.get("login", ""))
    if user.get("type") == "Bot" or login.endswith(BOT_LOGIN_SUFFIXES):
        return True
    title = str(issue.get("title", ""))
    return title.startswith(BOT_TITLE_PREFIXES)


def keep(issue: dict[str, Any]) -> bool:
    if "pull_request" in issue:
        return False
    if is_bot(issue):
        return False
    body = issue.get("body") or ""
    return len(body.strip()) >= 30


def slim(issue: dict[str, Any], repo_key: str) -> dict[str, Any]:
    """Keep only the fields the course actually uses.

    Dropping the rest is deliberate: smaller diffs, no avatar URLs, and no
    incidental personal data beyond the author login that GitHub already
    publishes.
    """
    return {
        "repo": repo_key,
        "number": issue["number"],
        "title": issue["title"],
        "body": issue.get("body") or "",
        "state": issue["state"],
        "labels": [lbl["name"] for lbl in issue.get("labels", [])],
        "created_at": issue["created_at"],
        "closed_at": issue.get("closed_at"),
        "comments": issue.get("comments", 0),
        "author_association": issue.get("author_association", ""),
        "url": issue["html_url"],
    }


def fetch_repo(full_name: str, repo_key: str, limit: int, tok: str | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    page = 1
    while len(out) < limit:
        qs = urllib.parse.urlencode(
            {"state": "all", "per_page": PER_PAGE, "page": page, "sort": "created", "direction": "desc"}
        )
        batch, _ = get(f"/repos/{full_name}/issues?{qs}", tok)
        if not isinstance(batch, list) or not batch:
            break
        out.extend(slim(i, repo_key) for i in batch if keep(i))
        print(f"  page {page}: +{len(batch)} raw, {len(out)} kept", file=sys.stderr)
        page += 1
        time.sleep(0.6)
    return out[:limit]


def discover_labels(tok: str | None) -> None:
    for repo in load_config():
        labels, _ = get(f"/repos/{repo['full_name']}/labels?per_page=100", tok)
        names = sorted(lbl["name"] for lbl in labels)
        print(f"\n{repo['full_name']} ({len(names)} labels)")
        for name in names:
            print(f"  {name}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", help="single repo key from config/repos.toml")
    ap.add_argument("--limit", type=int, default=400, help="issues per repo")
    ap.add_argument("--discover-labels", action="store_true")
    args = ap.parse_args()

    tok = token()
    if not tok:
        print(
            "WARNING: no GITHUB_TOKEN found. Unauthenticated limit is 60 req/hour "
            "and will not be enough for a full fetch.",
            file=sys.stderr,
        )

    if args.discover_labels:
        discover_labels(tok)
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for repo in load_config():
        if args.repo and repo["key"] != args.repo:
            continue
        print(f"fetching {repo['full_name']} (target {args.limit})", file=sys.stderr)
        issues = fetch_repo(repo["full_name"], repo["key"], args.limit, tok)
        dest = RAW_DIR / f"{repo['key']}.json"
        dest.write_text(json.dumps(issues, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  wrote {len(issues)} issues -> {dest.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
