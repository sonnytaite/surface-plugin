# Contributing

Issues and PRs are welcome — this plugin is young and real-world reports are the
most valuable thing you can send.

## The one rule that matters

**Guarantees live in code, not prompts.** Anything the plugin *promises* (shield,
provenance, dedup, gating) belongs in `rails/promote.py` with a test in
`tests/test_promote.py`. Skills and agents supply judgment; they must never be
the only thing standing between a user's private material and a commons.

## Running the tests

```
python3 -m unittest discover -s tests -v
```

Stdlib only, Python 3.9+ — no packages to install. CI runs the same suite on
3.9–3.13 plus manifest/skill validation; keep it green.

## Sending a change

1. Fork, branch, make the change.
2. If it touches `rails/promote.py`, add or adjust a test.
3. If it changes behaviour a user would notice, add a line to `CHANGELOG.md`
   under an `Unreleased` heading (the maintainer folds it into the next version).
4. Open a PR describing *what a user gains*, not just what changed.

## Reporting a bug

The most useful bug report for a loop like this is: what you ran, what you
expected the loop to do, what it did instead — plus your `promote.py status`
output if the rails are involved. Nothing from your vault's *content* is ever
needed; please don't paste it.

## Style

- Skills are prose — write them like you'd brief a sharp colleague, not like a
  config file.
- `promote.py` stays stdlib-only, single-file, no network. That constraint is
  load-bearing: it keeps the rails auditable in one sitting.
