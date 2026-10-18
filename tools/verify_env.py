"""Pre-lab environment check. Run this BEFORE the session, not during it.

    uv run python tools/verify_env.py

On success it prints a token. Paste that token into Moodle before the lab.
Setup that fails in the room costs the whole room time, which is why this is
homework.

Checks, in order of how often they fail:
  1. Python >= 3.13
  2. uv-managed environment with dependencies resolved
  3. .env exists and is NOT tracked by git
  4. exactly one model provider key present, matching LLM_MODEL
  5. the model key actually works (one tiny live call)
  6. GITHUB_TOKEN present and valid
  7. git identity configured
  8. pre-commit hook installed
  9. Node present, and pyright actually runs
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PROVIDERS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "xai": "XAI_API_KEY",
}

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
results: list[tuple[str, str, str]] = []


def check(name: str, status: str, detail: str = "") -> None:
    results.append((name, status, detail))
    symbol = {PASS: "  ok  ", FAIL: " FAIL ", WARN: " warn "}[status]
    print(f"[{symbol}] {name}" + (f" - {detail}" if detail else ""))


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    path = ROOT / ".env"
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip("\"'")
    return env


def looks_placeholder(value: str) -> bool:
    return (not value) or "xxxx" in value.lower()


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"llm-se-2027 W1 lab - environment check")
    print(f"{platform.system()} {platform.release()} | python {sys.version.split()[0]} | {stamp}\n")

    # 1. Python
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 13):
        check("python >= 3.13", PASS, f"{major}.{minor}")
    else:
        check("python >= 3.13", FAIL, f"found {major}.{minor}; run `uv sync`")

    # 2. dependencies
    try:
        import dspy  # noqa: F401
        import pydantic  # noqa: F401

        check("dependencies importable", PASS, "dspy, pydantic")
    except ImportError as exc:
        check("dependencies importable", FAIL, f"{exc}; run `uv sync`")

    # 3. .env present and untracked
    env = load_env()
    if not env:
        check(".env present", FAIL, "copy .env.example to .env")
    else:
        check(".env present", PASS, f"{len(env)} entries")

    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ".env"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if tracked.returncode == 0:
        check(".env untracked", FAIL, "your .env IS TRACKED. `git rm --cached .env` now, then rotate every key in it")
    else:
        check(".env untracked", PASS)

    # 4. exactly one provider
    model = env.get("LLM_MODEL", "")
    present = [p for p, k in PROVIDERS.items() if not looks_placeholder(env.get(k, ""))]
    if not present:
        check("model provider key", FAIL, "no real key found; fill in exactly one")
    elif len(present) > 1:
        check("model provider key", WARN, f"{len(present)} keys set ({', '.join(present)}); only LLM_MODEL is used")
    else:
        check("model provider key", PASS, present[0])

    provider = model.split("/", 1)[0] if "/" in model else ""
    if provider and present and provider not in present:
        check("LLM_MODEL matches key", FAIL, f"LLM_MODEL is {provider!r} but you set {present[0]!r} key")
    elif provider:
        check("LLM_MODEL matches key", PASS, model)
    else:
        check("LLM_MODEL matches key", FAIL, "LLM_MODEL missing or malformed (expected provider/model)")

    # 5. live model call
    if present and provider in present:
        try:
            import dspy

            os.environ.setdefault(PROVIDERS[provider], env[PROVIDERS[provider]])
            lm = dspy.LM(model, max_tokens=16)
            reply = lm("Reply with the single word: ready")
            text = reply[0] if isinstance(reply, list) else str(reply)
            check("live model call", PASS, text.strip()[:40])
        except Exception as exc:  # noqa: BLE001 - report anything, this is a smoke test
            check("live model call", FAIL, f"{type(exc).__name__}: {str(exc)[:120]}")
    else:
        check("live model call", FAIL, "skipped - fix the key first")

    # 6. GitHub token
    tok = env.get("GITHUB_TOKEN", "")
    if looks_placeholder(tok):
        check("github token", FAIL, "needed by tools/fetch_issues.py; create one with NO scopes")
    else:
        req = urllib.request.Request(
            "https://api.github.com/rate_limit",
            headers={"Authorization": f"Bearer {tok}", "User-Agent": "w1-verify"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                limit = json.load(resp)["resources"]["core"]["limit"]
            check("github token", PASS if limit > 1000 else WARN, f"limit={limit}/hr")
        except urllib.error.HTTPError as exc:
            check("github token", FAIL, f"rejected ({exc.code})")
        except Exception as exc:  # noqa: BLE001
            check("github token", WARN, f"unverified: {type(exc).__name__}")

    # 7. git identity
    name = subprocess.run(["git", "config", "user.name"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    email = subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if name and email:
        check("git identity", PASS, f"{name} <{email}>")
    else:
        check("git identity", FAIL, "git config user.name / user.email")

    # 8. hook
    #
    # Two ways this goes wrong, both of which have bitten us:
    #
    #   `exec python ...`   - `python` is not on PATH on a stock macOS, and git
    #                         runs hooks without the virtualenv active, so every
    #                         commit dies with "exec: python: not found".
    #   `exec "C:\...exe"`  - baking sys.executable in works on macOS but not on
    #                         Windows, where git runs hooks under Git Bash and a
    #                         backslashed drive path is not executable there.
    #
    # `uv run` is the one spelling that holds on both: uv is a prerequisite, it
    # is on PATH, and it resolves the project's own interpreter.
    hook_body = (
        "#!/bin/sh\n"
        "# Installed by tools/verify_env.py. Blocks credential-shaped strings.\n"
        'cd "$(git rev-parse --show-toplevel)" || exit 1\n'
        "exec uv run python tools/check_secrets.py\n"
    )
    hook = ROOT / ".git" / "hooks" / "pre-commit"
    stale = hook.exists() and "exec uv run python" not in hook.read_text(encoding="utf-8")
    if hook.exists() and not stale:
        check("pre-commit hook", PASS)
    else:
        try:
            hook.parent.mkdir(parents=True, exist_ok=True)
            hook.write_text(hook_body, encoding="utf-8")
            hook.chmod(0o755)
            check("pre-commit hook", PASS, "repaired" if stale else "installed now")
        except OSError as exc:
            check("pre-commit hook", WARN, str(exc))

    # 9. node, and pyright actually running
    #
    # pyright is a Node program wearing a Python wrapper. With no Node on PATH
    # it downloads one on first use, which is a slow network fetch at exactly
    # the wrong moment and is unreliable on Windows. So we check for Node here,
    # at home, and then RUN pyright once - which also warms its package cache,
    # so the first run in the room is fast.
    node = shutil.which("node")
    if node:
        try:
            version = subprocess.run([node, "--version"], capture_output=True,
                                     text=True, timeout=30).stdout.strip()
            check("node", PASS, version)
        except (OSError, subprocess.SubprocessError) as exc:
            check("node", WARN, f"found at {node} but would not run: {exc}")
    else:
        check("node", FAIL, "install it with nvm - see README, 'What you need installed'")

    try:
        pyright = subprocess.run(
            ["uv", "run", "pyright", "--outputjson"],
            cwd=ROOT, capture_output=True, text=True, timeout=600,
        )
        # Exit code 1 just means it found type errors, which is not our problem
        # here. What we are checking is that it ran at all.
        if pyright.returncode in (0, 1):
            check("pyright runs", PASS)
        else:
            detail = (pyright.stderr or pyright.stdout).strip().splitlines()
            check("pyright runs", FAIL, detail[-1] if detail else f"exit {pyright.returncode}")
    except subprocess.TimeoutExpired:
        check("pyright runs", FAIL, "timed out - it was probably downloading Node")
    except OSError as exc:
        check("pyright runs", FAIL, str(exc))

    # verdict
    failures = [r for r in results if r[1] == FAIL]
    warnings = [r for r in results if r[1] == WARN]
    print()

    if failures:
        print(f"{len(failures)} check(s) failed:")
        for failed_name, _, detail in failures:
            print(f"  - {failed_name}: {detail}")
        print()
        print("=" * 62)
        print("SUBMIT THIS OUTPUT TO MOODLE ANYWAY, BEFORE THE DEADLINE.")
        print("=" * 62)
        print(
            "\nA failed run submitted on time is fine - it tells me what broke\n"
            "and I can help you fix it by email. A missing submission is not:\n"
            "there is no time to debug your setup during the lab.\n"
            "\nCopy everything from the first [ ok ] line to here.\n"
            "Nothing above contains a credential. If you are about to paste a\n"
            "key, stop - it is not part of this output.\n"
            "\nStuck? Post the same text in the course forum."
        )
        return 1

    ident = f"{name}|{email}|{model}"
    token_value = hashlib.sha256(ident.encode()).hexdigest()[:12]
    if warnings:
        print(f"All checks passed ({len(warnings)} warning(s) above, not blocking).\n")
    else:
        print("All checks passed.\n")
    print(f"    CHECKOFF TOKEN: w1-{token_value}")
    print()
    print("=" * 62)
    print("SUBMIT THIS OUTPUT TO MOODLE BEFORE THE DEADLINE.")
    print("=" * 62)
    print(
        "\nCopy everything from the first [ ok ] line to here, not just the\n"
        "token line. Nothing above contains a credential.\n"
        "\nYou are set up. See you at the lab."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
