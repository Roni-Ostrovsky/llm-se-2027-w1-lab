# Dataset manifest

Seed: 20270101

Splits: train 60%, dev 20%, test 20%, stratified by repo.

`test.json` is SEALED. Do not read it, tune against it, or let an agent
index it. Its only value is that it has never been seen.

Gold labels: `gold_type`, `gold_component` (per-repo taxonomy).
No gold labels: severity, has_reproduction_steps, duplicate_candidate.
