Name:
Date:

# Exercise A - Execution findings

Execute your triage module on at least 20 issues from `data/snapshot/dev.json`. 
Look at the output. Write down anything that surprised you.

---
### Surprise 1

- **Input issue json**:
- **Output triaged issue**:
- **What is surprising**:


# Exercise B — Review findings

## Part 1 — found by reading

Record every problem you find in the released diff. One block per finding.
Add as many as you need. Do not delete the unused ones — an empty block is
information too.

**These lock at 1:13.** Once you start running the code, anything new goes in
part 2 instead. That boundary is the measurement: without it there is no way to
tell what reading caught from what the test runner caught.

Confidence: `certain` | `probable` | `uncertain`

---

### Finding 1

- **Location** (file:line):
- **Confidence**:
- **What is wrong**:
- **Why it matters** (what breaks, for whom, when):
- **What would have caught this** (a test? a type? a review rule? nothing?):

---

### Finding 2

- **Location**:
- **Confidence**:
- **What is wrong**:
- **Why it matters**:
- **What would have caught this**:

---

### Finding 3

- **Location**:
- **Confidence**:
- **What is wrong**:
- **Why it matters**:
- **What would have caught this**:

---

### Finding 4

- **Location**:
- **Confidence**:
- **What is wrong**:
- **Why it matters**:
- **What would have caught this**:

---

### Finding 5

- **Location**:
- **Confidence**:
- **What is wrong**:
- **Why it matters**:
- **What would have caught this**:

---

### Finding 6

- **Location**:
- **Confidence**:
- **What is wrong**:
- **Why it matters**:
- **What would have caught this**:

---

## Part 2 — found by running

After `git apply`, `uv run pytest`, `uv run pyright` and the batch run.

### What the tooling found that I did not

- **Which tool** (pytest / pyright / running it):
- **What it showed**:
- **Would I have found this by reading?** (be honest):

### What I found by reading that the tooling did not

- 

### Anything the tooling reported that turned out not to be a problem

- 

---

## Scoring (fill in after the reveal)

| | part 1 (reading) | part 1 + part 2 |
|---|---|---|
| Seeded defects found | | |
| Seeded defects missed | | |
| False positives | | |

**Reading detection rate**: found / (found + missed) = ____%

**Combined detection rate**: found / (found + missed) = ____%

The gap between those two is not a measure of you. It is a measure of which
defects a machine can catch and which ones still need a person — and the
second group is the reason this course exists.

### One sentence: what did you miss, and why do you think you missed it?


