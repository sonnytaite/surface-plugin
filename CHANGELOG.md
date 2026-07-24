# Changelog

All notable changes to the surface plugin. Format loosely follows
[Keep a Changelog](https://keepachangelog.com); versions follow semver as far
as a young plugin honestly can.

## [0.3.5] — 2026-07-24

### Fixed
- **`CLAUDE_CONFIG_DIR` is now honoured everywhere.** The vault registry and the
  session-transcript paths hardcoded `~/.claude`, which broke vault discovery and
  `/capture backfill` for profile-split and enterprise setups — and `init` would
  silently recreate `~/.claude`. The registry now lives in
  `${CLAUDE_CONFIG_DIR:-~/.claude}/surface-vaults.json`; a registry left at the
  legacy location is still read (never written) so existing vaults stay found.
- `/capture` annotate flag order (subcommand before `--vault`).

### Added
- **Test suite for the rails** (`tests/test_promote.py`, stdlib unittest, 39
  tests): shield refusal, provenance requirement, dedup/remember-the-drop,
  dispose/park/reconcile, append-only dispositions, publish gating (hold tier,
  missing sensitivity, audience mismatch, shielded content), config-dir and
  vault resolution. The README's "guarantees live in code" claim is now
  executable.
- **CI** (GitHub Actions): tests on Python 3.9–3.13, manifest agreement checks
  (plugin.json ↔ marketplace.json), SKILL.md frontmatter validation, and a
  README↔manifest version-drift check.

### Changed
- `surface-critic` made structurally read-only.
- README status section now tells the truth about the version.

## [0.3.4] — 2026-07-04

### Added
- Backup step at onboard: a private vault remote offered and verified.

## [0.3.3] — 2026-07-04

### Added
- `park` verdict: "decided, homed elsewhere" no longer counts as waiting on you.

## [0.3.2] — 2026-07-04

### Changed
- `/capture backfill` confirms the batch before spending.

## [0.3.1] — 2026-07-04

### Fixed
- Dropped explicit skills/agents path declarations from the manifest — the
  agents array form failed manifest validation; default directory discovery
  covers both.

## [0.3.0] — 2026-07-04

### Changed
- The harvest verb is `/capture` — namespacing embraced.

## [0.2.x] — 2026-07-04

- `/capture backfill` reaches work older than the transcripts (0.2.4).
- Dashboard editorial redesign: question-titled cards, plain language;
  "What have you shared?" (0.2.0–0.2.3).

## [0.1.x] — 2026-07-04

- 0.1.0 — the Surface loop as a Claude Code plugin: `/onboard`, `/capture`
  (then `/surface`), `/weave`, `/share`, `/scan`; rails in `promote.py`;
  doer ≠ judge agents.
- Commons gating as a deterministic rail; commons management; vault discovery
  and routing; Karpathy vault alignment; `/share review`; backfill; onboarding
  stock-take (0.1.1–0.1.9).
