---
name: surface
description: Harvest a working session into your vault — extract the durable, net-new insights, run them past an adversarial critic, then triage them with the user (keep/dump) and weave the keeps into the wiki. State-aware — run "/surface" after a session to harvest, and run it again any time to triage or reconcile what is waiting. Use when the user wants to capture what a session taught them.
argument-hint: "[session | topic | \"this\" | \"last\"]"
---

# /surface — harvest a session into your second brain

You are the **doer** in the Surface loop. Judgment is yours; every guarantee (shield,
dedup, provenance, disposition log) lives in
`python3 "${CLAUDE_PLUGIN_ROOT}/rails/promote.py"` — always go through it, never write
to `_inbox/` by hand. The vault is found automatically (cwd walk-up, then the registry
`~/.claude/surface-vaults.json`) — the user works in their normal project folders, NOT
inside the vault, and this still works. If none exists, send the user to `/onboard` and
stop.

**Vault routing (the choice is a sensitivity boundary, not a convenience):** with ONE
registered vault, use it — but always SAY which vault you are staging into before you
stage, so a wrong target costs one sentence to correct. With SEVERAL, read the session
first (step 2), then ask (AskUserQuestion) with a content-based suggestion — a
motorbike session suggests the personal vault, work-adjacent research suggests the work
vault — and put the suggested one first. Never guess silently across a personal/work
boundary; when the content could belong to either, asking IS the feature. Pass the
choice as `--vault` on every rails call.

## 0. Check state first — do the right next thing

Look at `<vault>/<state_dir>/_inbox/`:

- **Notes with `status: keep/act/dump` set** → the user triaged in their editor. Run
  `promote.py reconcile`, then go to step 5 (weave the keeps in).
- **Notes still `status: proposed`** → offer to triage them now (step 4) before
  harvesting more. The queue stays short or the loop dies.
- **Empty inbox** → harvest (steps 1–3).

## 1. Choose the source session

Sessions live in `~/.claude/projects/<project-dir>/*.jsonl` (one file per session; the
project dir is the working directory with `/` replaced by `-`).

- `"this"` / `"last"` / nothing → the current or most recent substantive session for
  this project (check file mtimes; skip tiny files).
- a topic phrase → grep the transcripts for it and pick the matching session; if
  ambiguous, show the top few and ask.
- a session id → use it directly.
- **`backfill`** (or the user asks to harvest their history / past sessions) → the
  bring-past-me-along mode, below.

### Backfill — sweeping your history into the vault

New installs are not day zero of the user's work: weeks or months of past sessions
already sit in `~/.claude/projects/*/`. Backfill harvests them, bounded.

1. **Take stock first.** Enumerate transcript files across ALL project dirs, newest
   first, skipping tiny ones. Check the disposition log for session ids already
   harvested (`grep transcript://<session-id> <state_dir>/dispositions.jsonl`) and skip
   fully-swept sessions. Tell the user what exists — how many substantive sessions,
   over what date range, across which projects — before touching anything.
2. **Ask scope** (AskUserQuestion): last 2 weeks / last 6 weeks / everything /
   pick specific projects.
3. **Process a bounded batch per run:** 3–5 sessions, staging at most ~12 candidates
   total across them, then critic + triage exactly as normal. The triage queue is the
   bottleneck — a big backlog means MORE RUNS, never a bigger queue. Dedup makes
   repeat sweeps safe.
4. **Watch the context watermark.** Reading transcripts is context-heavy. When your
   context use approaches roughly half, stop cleanly at a session boundary — finish the
   current session's staging and triage, do NOT start reading another transcript. Never
   run the sweep so deep that the triage happens in a degraded context.
5. **End each run honestly:** what was swept, what remains, and the restart line —
   *"14 sessions left in your window. Start a fresh session and run `/surface backfill`
   to continue — it picks up exactly where this left off."* A month of history is
   typically two to four sittings, and the vault is genuinely useful after the first.

## 2. Read the content — the reasoning, not the first message

Transcripts are JSONL: one event per line with `type` (`user`/`assistant`), message
content, and timestamps. Read the *middle* of the work: decisions made, corrections,
named ideas, findings. First messages are commands, not insights — that is known noise.
Note line ranges of what you use: that is the provenance.

## 3. Extract candidates (the judgment)

Keep ONLY durable, reusable insight: a **decision**, a **principle or framing**, a
**named pattern**, a **non-obvious finding**, a **contradiction/correction**, or a
**well-described problem** (`--type problem` — a problem the user articulated deeply is
as valuable as a solution). Reject commands, status chatter, ephemeral mechanics, and
anything the wiki already holds (check `wiki/index.md` and the obvious page first).

**When the session concerns a distinct project** (an app, a repo, a build), split two
ways: the **project page** (`wiki/projects/<slug>.md` — what it is, why it exists, where
the repo lives, current status, key decisions; create it if new, update it if not) and
**separate concept pages for the transferable lessons** — the things that would matter
even if the project died. A project session usually yields one project-page update plus
one or two lesson candidates, not five project pages.

Aim for **3–7 candidates from a rich session; fewer is fine; zero is a valid outcome** —
say so and stop. Precision over volume: the human's review queue is the bottleneck.

Write each body in tight prose with `[[wiki-links]]` to existing pages where relevant,
then stage it through the rails:

```bash
printf '%s' "<body>" | python3 "${CLAUDE_PLUGIN_ROOT}/rails/promote.py" add \
  --title "<concise insight title>" \
  --source "transcript://<session-id>#<line-start>-<line-end>" \
  --type <insight|pattern|problem|decision|prototype> \
  --created <YYYY-MM-DD>
```

Honour the output: `shielded` = the rail refused it (leave it); `skip` = seen before
(do not fight it).

## 4. Critic, then the human gate

**Critic (always, not optional):** spawn the `surface-critic` agent (Agent tool) with the
list of staged candidate files and the vault path. It writes advisory verdicts into each
candidate's frontmatter via `promote.py annotate`. Doer ≠ judge — you do not critique
your own candidates.

**Triage in conversation:** present each candidate — title, two-line gist, the critic's
verdict — and ask the user with AskUserQuestion (max 4 questions per call, so batch;
multiSelect off): options **Keep** / **Dump** / **Skip for now**, and they can type notes
via "Other". For each answer:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/rails/promote.py" dispose <candidate_id> <keep|dump> --reason "<their note, if any>"
```

Skipped candidates stay in `_inbox/` for next time. The user can also triage later in
their editor by setting `status:` — mention it once, not every run.

## 5. Weave the keeps in

For each kept candidate: decide **new page vs update existing** (prefer updating — do not
create near-duplicates), place it under the right category dir, re-author the frontmatter
into a clean wiki page (drop the inbox scaffolding), wire links **both ways** — add
`[[links]]` from the new page to related pages AND a back-link from each related page —
then update `wiki/index.md`. Move the file with `git mv` when the vault is a repo.
Commit with a plain message (`surface: <n> insights from <session/topic>`); ask before
pushing. Finish every run — harvest, triage, or backfill — by regenerating the lens:
`python3 "${CLAUDE_PLUGIN_ROOT}/rails/promote.py" dashboard --vault <vault>`.

## Wrapping up? Harvest is time-shiftable

Transcripts persist — nothing is lost by not running `/surface` the second a session
ends. When the user is in a hurry (closing the laptop, heading out), offer the split
explicitly instead of making them wait:

- **Stage now, judge later:** extract and stage the candidates (the fast part), spawn
  the critic as a **background** agent, and tell the user to go — "candidates staged,
  critic running; next `/surface` starts with your keep/dump questions." Step 0's
  state-awareness makes the resume automatic.
- **Nothing now:** tomorrow's `/surface last` (or the next backfill) harvests today's
  session identically. The morning-after habit is as valid as the session-end habit —
  what matters is that it happens, not when.

Never guilt the user about deferring; a loop that demands waiting around is a loop that
gets abandoned.

## Guardrails

- **Never bypass the rails.** The shield/dedup/provenance guarantees only hold there.
- **Never invent provenance** — cite session positions you actually read.
- **This vault is private.** Nothing here is shared; that is /share's job, behind its own
  gates.
- When unsure whether something is durable, lean to skip — the user's dumps are training
  signal, and a short queue keeps them coming back.
