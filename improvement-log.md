# Improvement log

Every time the agent gets something wrong, it goes here. Not the fix — the
*failure*, classified.

This file runs for the whole semester. In W12 you will use it to show what
changed about how you work. That only works if it was written as things
happened, so write entries the day they occur. An improvement log
reconstructed from memory in week eleven is a creative writing exercise.

## The taxonomy

Classify every entry as exactly one of:

| Class | Meaning | Where the fix usually belongs |
|---|---|---|
| `capability` | the model could not do this | change the task, or the model |
| `context` | it could have, but did not know something | what the agent is given to read |
| `tool` | it lacked a way to act or to check | tooling |
| `spec` | the request was ambiguous and it guessed | the specification |
| `concept` | it used the wrong idea or the wrong name | the domain model |
| `bug` | ordinary defect, nothing AI-specific | the code |

The class matters more than the fix. Choosing between `context` and `spec`
forces you to say whether the agent lacked information or you did — and those
have different remedies.

---

## Entries

### E1

- **Date**:
- **What happened**:
- **Class**:
- **Evidence** (session log timestamp, commit, or file:line):
- **What I did about it**:
- **Did it work?**:

---

### E2

- **Date**:
- **What happened**:
- **Class**:
- **Evidence**:
- **What I did about it**:
- **Did it work?**:

---

### E3

- **Date**:
- **What happened**:
- **Class**:
- **Evidence**:
- **What I did about it**:
- **Did it work?**:
