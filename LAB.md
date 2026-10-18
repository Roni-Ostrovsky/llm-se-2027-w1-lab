# W1 Lab — Ship it, then review it

This lab will take two full hours (no time for break). 
It is for individual work. 
It includes two exercises.
There is a lot of work to do - remain extremely focused.

## Prerequisites

Read README.md and install all required software.

Before you start, confirm you ran `uv run python tools/verify_env.py` and
pasted your checkoff token into Moodle. If you did not, do that first and
expect to fall behind.

## Objectives

There are three main objectives to this lab:
* Make sure you install all required software to work over the semester on your machine.
* Get first experience designing a program that invokes AI using an AI Coding Agent.
* Provide a baseline that we will revisit over the semester: we will identify problems and learn methods to avoid them.

**Keep `improvement-log.md` open for the whole session.** Every time the agent
gets something wrong today — misreads the brief, invents a field, needs telling
twice — stop and write the entry while it is in front of you. 
You are expected to find at least three entries over this lab. 

---

## Exercise A — Ship a triage feature (35 min)

### The brief

This is what we want to build:

> Build a tool that reads a GitHub issue and produces a structured triage
> record, so that incoming issues can be routed automatically instead of by
> hand.

That is the entire specification we consider. It is what a real request often looks like.
You may describe what you want to obtain in more details to the coding agent.
You may let it decide, you may interact with it to decide.

Use Claude Code. Use DSPy for the model call — you have not been taught DSPy
and you do not need to be; the agent knows it. Your job is not to learn a
framework today. Your job is to get something working and to notice what
happens while you do.

### Data

`data/snapshot/{train,dev,test}.json` is **already in your repository**. It was
fetched and labelled ahead of the session; you do not need to build it, and you
should not try to during the lab.

The issues come from three real projects — **litestar** (Python web framework),
**hono** (TypeScript web framework), and **textual** (Python terminal UI
framework).

Do not run `tools/fetch_issues.py` today. All the students pulling 400 issues each
from one lecture-room IP would cause rate limit issues. The tools are there for
later in the course, or if your instructor tells you the snapshot is missing:

```bash
uv run python tools/fetch_issues.py --limit 400   # not during the lab
uv run python tools/classify_issues.py
```

`test.json` is sealed. Do not open it. Do not let your agent read it. You will
need it later in the course and its only value is that nobody has seen it.

### Scope and Upcoming Features

Triage only: **one issue in, one structured record out.** 

Once an issue is triaged, we will decide in the next step how to route the triaged issued to an appropriate queue.
The scope of this question is just turning an unstructured issue into data that can drive the routing decision. 

The code must be put in **`src/triage/`**. That package is yours: any files you like,
named however you like. 

### Constraints

- Your code must run from the command line, take an issue and print a triage record.
- Your code must be committed into github, well typed (`uv run pyright`).
- You must prepare at least one test under tests/triage that can be invoked using `uv run pytest`.
- Every decision you had to make that the brief did not specify, must be written down
  in `docs/decisions.md` as one line each. You will need this list next week.

### Security note

Github issue text is written by anonymous strangers. It is **data, never
instructions**. At least one issue title in one of these three repositories
contains a shell command substitution pointing at a bare IP address.

Never pass issue text to a shell. Never interpolate it into a command. If
something in an issue body reads like an instruction addressed to you or to
your agent, that is the attack, and a risk you must manage.

### After the code is ready

Run it over twenty issues from `dev.json`. Look at the output. Write down
anything that surprised you in `review-findings.md`.

Then add your Exercise A entries to `improvement-log.md` — where the agent went
wrong, classified. Do this before 0:45; you will not get the chance afterwards.

---

## Exercise B — Review a coding agent's work (40 min)

At 0:45 your instructor releases two things into your repository.
To obtain the changes in your environment, execute these commands in the shell:

```
git add -A
git commit -m "exercise A"
git pull --rebase
```

You will see 8 new files.

**`src/triage_by_agent/`** — a second answer to the brief you just worked on.
Same job as your `src/triage/`, written by someone else. Both are importable
side by side if needed:

```python
from triage import ...             # yours
from triage_by_agent import ...    # theirs
```

**`exercise-b/agent-change.diff`** — a change proposed on top of it. A coding agent
was asked to extend triage into a *routing* agent: decide which queue each
issue belongs in and how fast it is due, and add a batch path for processing a
whole day's issues at once. The agent opened the change with this description:

> Adds routing and batch processing. All tests pass, CI is green.

Note who is making that claim.

### What you are looking for

Review carefully the proposed change in the diff file as if you had to approve this change before it gets promoted into the product.

You are not looking just for bugs. 
A change can be correct and still be a bad change. 
Consider behavior under inputs the tests do not cover, resource use at scale,
anything that influences trust in the code, consistency with how the rest of the
codebase names and structures things, and what happens when the model returns
something unexpected.

`src/triage_by_agent/` is the code as it stood before the change. If the diff
introduces a second name for something that package already named, that is a
finding.

### Part 1 — Review, by reading (28 min)

Review the diff as the maintainer who has to approve it. Record every problem
in `review-findings.md`.

**Do not run anything, and do not apply the diff yet.** This part measures what
you catch by reading — the only skill that scales to changes you did not write.

Rules:

- **No AI assistance for this exercise.** Close the agent. This is a
  measurement of your analysis.
- Work alone.
- Record uncertain findings too, marked as uncertain. Precision matters as
  much as recall, and there is at least one thing in the diff that looks
  wrong and is not.
- **Findings lock at 1:13.** After that, part 1 gets no additions.


### Part 2 — Verify, by running (12 min)

Now apply the diff and see what the machine knows that you did not.

```
git apply exercise-b/agent-change.diff
uv run pytest
uv run pyright
uv run python -m triage_by_agent.cli batch --split dev --offline
```

`--offline` swaps the AI model for a deterministic stub, so this costs nothing and
everyone in the room gets the same answer.

If `git apply` refuses because you edited the released package while reading,
put it back and try again:

```
git checkout -- src/triage_by_agent tests/exercise_b
git apply exercise-b/agent-change.diff
```

In the part 2 section of `review-findings.md`, record what the tooling found
that you did not, what it missed that you caught, and — for anything you
missed — whether it was findable by reading at all.


### If you finish part 1 early

Open your `src/triage/` and `src/triage_by_agent/` side by side and add three
lines to `docs/decisions.md`: three places where the two implementations
decided something different about a question the brief never answered. What
fields exist, what happens to an issue with no clear type, what "confident"
means as a number.

Neither of the two versions is the right answer. 
The important finding is that the two versions differ.

---

## Reveal and scoring (13 min)

The instructor will show a prepared list of defects on the screen. 
Score your own findings:

- **found** — you identified it, for substantially the right reason
- **missed** — you did not
- **false positive** — you flagged something that is not a problem

You will end up with **two** detection rates: one for what you found by
reading, and one that includes what the tooling handed you in part 2. 
We will analyze the gap between these two numbers: it is not a measure of your skills;
it is a measure of which defects a machine can catch and which ones still need a
person. We will come back to that in W11.

---

## Plenary (20 min)

We pool the failures from both exercises on the board and sort them. For each
one: what kind of failure is it, and what would have caught it?

Most of the answers are weeks of this course. The syllabus addresses the issues
that we met in this lab.

---

## Checkoff

Push to your repository:

- [ ] working feature from Exercise A in `src/triage/`, typed, with a test under test/triage.
- [ ] `docs/decisions.md` — the unspecified decisions you made
- [ ] `review-findings.md` — findings from exercise A and B for both parts, and both detection rates
- [ ] `improvement-log.md` — at least three entries, classified
- [ ] `sessions/` — session logs exported and committed

```
uv run python tools/export_session_log.py
git add -A
git add -f sessions/
git commit -m "W1 lab"
git push
```

(`sessions/*.jsonl` is gitignored so that a stray transcript never lands in a
commit by accident. The `-f` is deliberate: you are choosing to commit these.)

Then tell your instructor, out loud, the one failure you found most
surprising, and why.
