"""Per-repo component vocabulary, read from config/repos.toml.

Components are a per-repo taxonomy and are deliberately not pooled: hono's
"middleware" and litestar's "openapi" are different kinds of category.
"""

from __future__ import annotations

import tomllib
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "repos.toml"


@cache
def _components_by_repo() -> dict[str, tuple[str, ...]]:
    with CONFIG.open("rb") as fh:
        config = tomllib.load(fh)
    out: dict[str, tuple[str, ...]] = {}
    for repo in config.get("repos", []):
        labels = repo.get("component_labels", {})
        out[str(repo["key"])] = tuple(sorted(str(name) for name in labels))
    return out


def components_for(repo: str) -> tuple[str, ...]:
    """Allowed component values for `repo`; empty for textual or an unknown repo."""
    return _components_by_repo().get(repo, ())
