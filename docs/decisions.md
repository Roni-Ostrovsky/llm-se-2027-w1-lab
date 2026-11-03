# Unspecified decisions

The brief did not tell you everything. Every time you or your agent chose
something the brief did not specify, add a line here.

Examples of the kind of thing that counts: what fields the record has, what
happens to an issue with no clear type, how confident is confident enough,
what the output looks like when the model returns nothing usable.

You will need this list in W2, when we reconstruct the requirements this
build implicitly assumed. The comparison across the cohort is the lesson, so
write down what you actually decided, not what you think is the right answer.

---

- Record fields: repo, number, title, url, status, issue_type, component, severity, has_reproduction_steps, summary, confidence, needs_human_review, error, model.
- Classification field names reuse the dataset's gold names (issue_type, component, severity, has_reproduction_steps) so records can be scored against gold later.
- `duplicate_candidate` is left out: one issue in means there is nothing to compare against.
- issue_type vocabulary: bug, enhancement, documentation, question, other. hono's "meta" (announcements) folds into "other".
- An issue with no clear type gets the model's best guess with low confidence; "other" is for meta, chores, and spam, not for "unsure".
- component is restricted to the repo's taxonomy in config/repos.toml; anything outside it (including every component for textual) becomes null, not an error.
- severity has a four-level rubric (critical/high/medium/low) written into the prompt; there is no gold for it, so the rubric is unvalidated.
- Non-bugs get a severity too (usually low), so routing always has a priority to sort by.
- confidence is the model's self-reported probability that issue_type is correct; it is uncalibrated, and values outside 0..1 are clamped.
- needs_human_review = confidence < 0.7, or issue_type is "other", or the call failed. 0.7 was picked, not measured.
- Model failure (network, provider, unparseable output, any field failing validation) produces a status="error" record with null fields; it never raises and never guesses a partial record.
- A component name outside the taxonomy is quietly dropped, while a bad issue_type or severity rejects the whole answer.
- GitHub labels are never shown to the model: gold labels are derived from them, and a newly filed issue has none.
- Issue bodies are truncated to 8000 characters before the model call.
- Issue text is treated as untrusted data: the prompt says so, outputs are constrained to enums where possible, and nothing is passed to a shell.
- Output is ASCII-escaped JSON (one indented object for a single issue, JSON Lines for several), so terminal control characters in titles can't take effect.
- CLI input: an issue JSON file in the snapshot's shape, stdin, or `--split train|dev` with `--repo/--number/--limit`. The test split cannot be selected at all.
- Exit code 1 if any record is status="error", 2 for bad input or missing configuration.
- The model comes from LLM_MODEL in .env, called with temperature 0 and dspy.Predict (no chain-of-thought), using DSPy's default on-disk cache.
- tests/triage has no __init__.py, so it does not become a package named `triage` that shadows src/triage.
