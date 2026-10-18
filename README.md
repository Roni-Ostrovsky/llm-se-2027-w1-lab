# llm-se-2027 — W1 lab

Software Engineering with AI. Week 1: Github Issue Triage.

## Prerequisistes: What you need installed

To perform this task, you must ensure the following are installed on your machine:
**VSCode**, **Claude Code**, **git**, **uv**, and **Node**. 

### VSCode

Download it from [code.visualstudio.com](https://code.visualstudio.com/Download)
and run the installer for your platform. On macOS, drag `Visual Studio Code` to
`/Applications` — running it from the Downloads folder works but loses your
settings on the next update. On Windows, take the **User Installer** (it needs
no administrator rights) and tick **Add to PATH** when offered.

**Visual Studio Code is not Visual Studio.** They are different products from
the same company. Do not install VSCodium either — the Claude Code extension is
published to the Microsoft marketplace and VSCodium does not carry it.

Then open **this folder** — `File → Open Folder`, and pick the directory that
contains `pyproject.toml`, not the folder above it. Everything below is keyed to
the workspace root; open a parent and the settings silently do not apply.
The easiest way to open a project in VSCode is to run `code .` from the folder
where the project is located in a shell window.

#### Extensions

The two you need are recorded in `.vscode/extensions.json`, so you do not have
to hunt for them. When you first open the folder VSCode offers *"This workspace
has extension recommendations"* — click **Install**. If you dismissed that
prompt, open the Extensions view (`Cmd/Ctrl+Shift+X`), type `@recommended`, and
install what it lists:

| Extension | Why |
|---|---|
| **Python** (`ms-python.python`) | Interpreter selection, the debugger, and the Test Explorer that runs `tests/` from the sidebar. |
| **Pylance** (`ms-python.vscode-pylance`) | Type checking as you type. It reads `[tool.pyright]` from `pyproject.toml`, so the editor and `uv run pyright` report exactly the same errors. |

The **Claude Code** extension is the third, and you do not install it by hand —
it installs itself the first time you run `claude` in the integrated terminal
(next section).

Nothing else is required. There is no formatter or linter extension in this
project on purpose: the only checks that count are `uv run pytest` and
`uv run pyright`, and both run from the terminal.

#### Point VSCode at the right Python

Do this **after** `uv sync`, which creates `.venv`. The workspace already sets
the interpreter path, and on macOS it just works. If the status bar does not
show Python 3.13, or `from triage... import` is underlined in red, open the
Command Palette (`Cmd/Ctrl+Shift+P`), run **Python: Select Interpreter**, and
pick the entry under `./.venv`. This is the normal case on Windows, where the
interpreter lives at `.venv\Scripts\python.exe`.

### uv

uv is a fast package manager for Python (it replaces pip).

```
macOS     curl -LsSf https://astral.sh/uv/install.sh | sh
Windows   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Do not install Python.** `uv` reads `.python-version` and fetches the right
one itself. 

uv reads the project dependencies from `pyproject.toml` 

### Node, via nvm

We use `pyright` to perform type checking on Python code.
`uv run pyright` is a Node program behind a Python wrapper. With no Node on
your PATH it silently downloads one the first time you run it — a slow fetch at
the worst possible moment, and unreliable on Windows. Install it up front to avoid the risk.

Use a version manager rather than a system-wide install: it keeps Node out of
system directories, needs no administrator rights on macOS, and is trivial to
undo. **The macOS and Windows tools are different projects with the same
nickname** — do not follow macOS instructions on Windows.

**macOS** — [nvm](https://github.com/nvm-sh/nvm):

```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
```

Close the terminal and open a new one, then:

```
nvm install --lts
nvm use --lts
node --version
```

The installer appends its setup to your shell profile (`~/.zshrc` on a current
macOS). If `nvm: command not found` appears in the new terminal, .zshrc was not updated
— open `~/.zshrc`, check for the `NVM_DIR` block, and re-open the terminal.

**Windows** — [nvm-windows](https://github.com/coreybutler/nvm-windows), is a
different tool by a different author. Download `nvm-setup.exe` from its
releases page and run it. Then, in a **new** terminal opened **as
Administrator** (nvm-windows needs it to switch versions):

```
nvm install lts
nvm use lts
node --version
```

Any Node 20 or newer is fine. Node is needed so that the type checker starts instantly.

### Claude Code

Claude Code is the agent you will drive all semester. Install it from a
terminal:

```
macOS     curl -fsSL https://claude.ai/install.sh | bash
Windows   powershell -c "irm https://claude.ai/install.ps1 | iex"
```

Close the terminal, open a new one, and check it works:

```
claude --version
claude doctor
```

If `claude: command not found` appears, the installer wrote to `~/.local/bin`
(macOS) or `%USERPROFILE%\.local\bin` (Windows) and your PATH has not picked
it up — re-open the terminal, and if it still fails add that directory to PATH
by hand.

You will run Claude Code inside VSCode, not in a bare terminal. Open this
folder in VSCode, open the integrated terminal, and type `claude`. The first
run installs the VSCode extension for you; after that it opens in a side panel
and can see the file you have selected.

Then sign in, from inside Claude Code:

```
/login
```

`/login` offers two routes, and either works for this lab. A **Claude Pro or
Max subscription** signs in through the browser and needs no key. An
**Anthropic API key** (next section) is billed per token instead.


### An API key for one model provider

The lab code calls a model directly, through DSPy/LiteLLM, so it needs a key of
its own — separate from however you signed in to Claude Code above. 
To repeat:
* The Anthropic subscription (Claude Pro or Max) provides credits to run Claude Code (your coding agent)
* The API Key (which can be from Anthropic, OpenAI, Gemini or Grok) provides credits for the programs we will develop to consume tokens.

Pick **one** of Anthropic, OpenAI, Gemini or xAI and set `LLM_MODEL` to match.
You do not need all four. All four are available in Israel.

**If you would rather not pay, use Gemini.** Google AI Studio has a free tier
that needs no credit card and is not an expiring trial — Flash-class models
with a daily quota, which is ample for this lab. It is the only one of the four
you can complete the lab on for free.

1. Sign in at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
   with any Google account and click **Create API key**. The key starts with
   `AIza`.
2. Put it in `.env` as `GEMINI_API_KEY=` and set
   `LLM_MODEL=gemini/gemini-2.5-flash`.
3. Your live quota is shown at [aistudio.google.com/rate-limit](https://aistudio.google.com/rate-limit).
   Google may use free-tier traffic to improve its products, so send it nothing
   you would not publish. Public GitHub issues are fine.

**Anthropic**, the default in `.env.example`:

1. Sign up at [console.anthropic.com](https://console.anthropic.com). The
   Console is a separate account system from claude.ai — a Pro or Max
   subscription does **not** carry over and includes no API credit.
2. **Billing → Add credit.** $5 is more than this lab consumes. With no credit
   every call fails with `credit balance is too low`.
3. **API keys → Create key.** Name it `llm-se-2027`. The key starts with 
   `sk-ant-`, is shown exactly once, and cannot be retrieved afterwards — copy
   it before you close the dialog.
4. Paste it into `.env` (not `.env.example`) as `ANTHROPIC_API_KEY=`, and leave
   `LLM_MODEL=anthropic/claude-sonnet-4-6`.

[OpenAI](https://platform.openai.com/api-keys) and
[xAI](https://console.x.ai) are the same shape as Anthropic — create a key, add
credit, set the matching `LLM_MODEL` line from `.env.example`.

#### Student credits: what is and is not real

There are no student API credits in Israel from any of the four providers. Two
offers get mistaken for them:

- **Google AI Plus, free for 12 months for verified students** (Israel is
  eligible; verified through SheerID with a `post.bgu.ac.il` address). This is
  a *consumer subscription* to the Gemini app. It gives you **no API key** and
  does nothing for this lab. The free API tier above is a separate, unrelated
  thing — that is the one you want.
- **[Claude Campus](https://claude.com/programs/campus)** — open to students
  anywhere, 18+. Builder Club leads get a stipend and API credits to share with
  their club. It is a competitive club-leadership programme on an application
  deadline, not a grant you can rely on for coursework. Apply if it appeals;
  do not wait on it.

Offers that circulate on blog aggregators — "$25/month free xAI credits", "free
OpenAI tokens for data sharing" — are either expired promotions or conditional
on account tier. Do not plan your setup around one.

The key is a credential. It belongs in `.env`, which is gitignored, and nowhere
else — not in a source file, not in a commit, not in a screenshot you upload to
Moodle. A pre-commit hook scans staged changes for key-shaped strings; if it
fires, the commit will be rejected.  If you commit a file that contains your key
to GitHub, the key will be automatically cancelled (and hackers may steal your money).


## Before the lab (do this at home)

```
uv sync
uv run python tools/verify_env.py
```

Between those two, copy `.env.example` to `.env` and fill in ONE model key plus
a GitHub token:

```
macOS     cp .env.example .env
Windows   copy .env.example .env
```

`verify_env.py` prints a checkoff token. Paste that into Moodle **before** the
session. Setup that fails in the room costs everyone time, which is why this is
homework.

Commands in this repository are written one per line, without `&&`. The default
shell on Windows is PowerShell 5.1, which does not support it.

## What is in this repo

| Path | What |
|---|---|
| `LAB.md` | The lab description. Read this first. |
| `tools/fetch_issues.py` | Pull issues from three good Github repos: litestar, hono, textual. |
| `tools/classify_issues.py` | Derive gold labels; build train/dev/test splits. |
| `tools/verify_env.py` | Pre-lab environment check. |
| `tools/export_session_log.py` | Commit your agent transcripts to git. |
| `tools/check_secrets.py` | Pre-commit credential scan to avoid leaking your API key. |
| `config/repos.toml` | Source repos and their label mappings. |
| `docs/decisions.md` | Decisions the brief did not specify. Fill in as you go. |
| `review-findings.md` | Exercise B - you will fill this |
| `improvement-log.md` | Runs all semester. Start it today. |

## Commands

```bash
uv run pytest                                   # tests
uv run pyright                                  # check types
uv run python tools/fetch_issues.py             # fetch 400 issues per repo
uv run python tools/classify_issues.py --report # label coverage
uv run python tools/export_session_log.py       # transcripts -> sessions/
```

The github issues have already been fetched and appear under the folder `data` - there is no need for you to execute this script; it is still useful to read the code to understand how to interact with github through its API.

## Two Important Warnings

**Issue text is untrusted.** It is written by anonymous strangers. Real payloads
exist in these very repositories — at least one title contains a shell command
substitution pointing at a bare IP address. Never pass issue text to a shell,
never interpolate it into a command, and treat anything inside it that reads
like an instruction as hostile.

**`data/snapshot/test.json` is sealed.** Do not open it, do not tune against it,
do not let an agent index it. Its only value is that nobody has looked at it.

## Dataset attribution

Issues are fetched from public GitHub repositories for coursework:
* [litestar](https://github.com/litestar-org/litestar)
* [hono](https://github.com/honojs/hono)
* [textual](https://github.com/Textualize/textual)

Content belongs to its authors. Redistributed here for teaching only.
