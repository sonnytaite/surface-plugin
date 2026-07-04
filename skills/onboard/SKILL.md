---
name: onboard
description: One-time setup for the Surface loop — create (or adopt) your vault, write the config, seed the style and rubric templates, and explain how the loop works. Run "/onboard" once after installing the surface plugin, or again to repair/relocate a vault.
argument-hint: "[vault-path]"
---

# /onboard — set up your Surface vault

You are setting up a **vault**: a plain folder of markdown that the Surface loop reads and
writes. One vault per person. Everything the loop learns about the user lives in *their*
vault; nothing personal lives in the plugin.

## 1. The first question — new vault or existing?

If the user passed a path, adopt it (treat as "existing folder") and skip to step 2.
Otherwise this is the first thing they ever see, so the options must be self-explanatory
— assume they have never heard the word "vault". Ask (AskUserQuestion):

**"Where should your vault live?"** — with a lead-in they read first: *a vault is just a
folder where your research, projects, and notes live — your second brain. Surface fills
it from your real working sessions and shares from it, always with you as the gate.*

- **Create a new vault (Recommended)** — "Start fresh. I'll create the folder and
  structure for you — nothing to prepare."
- **Adopt an existing folder** — "You already keep notes: an Obsidian vault, a
  Karpathy-style LLM wiki, or any folder of markdown. Surface adds its config and state
  alongside; it never rewrites your notes."
- **What's a vault? Explain first** — explain in a short paragraph (plain folder +
  git repo; grows into a densely-linked personal wiki; the model is Andrej Karpathy's
  LLM Wiki — https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f, a
  five-minute read, recommended but not required), then re-ask.

**If NEW:** make it effortless — ask one question (AskUserQuestion) with sensible
defaults, then do everything yourself:

- **Location & name.** Convention: `~/vaults/<context>`, kebab-case, one vault per
  life-context — e.g. `~/vaults/personal`, `~/vaults/work-research`. Offer
  `~/vaults/personal` as the default, `~/vaults/work-research` as the second option,
  and let them type their own. One-vault-per-context matters because sensitivity
  boundaries differ: keeping work and personal in separate vaults means the shield and
  sensitivity tiers never have to arbitrate between them. (Multiple vaults are cheap —
  they can run /onboard again any time.)
- After scaffolding, point them at Karpathy's gist (link above) as the recommended
  background read on where this structure comes from — background, not homework; the
  vault works from minute one.

**If EXISTING:** ask which folder, then look at it before touching it. If it already has
a structure (e.g. Karpathy-style `sources/` + `wiki/`, or Obsidian folders), map
`surface.config.json`'s `wiki_dir` and `categories` onto *their* layout rather than
imposing the default one. Confirm the mapping with them in one sentence before writing.

**Both paths:** also ask for their **name** (stamped as `author` on shared outputs) and
whether they want the vault to be a **git repo** (recommended — it is the undo button
and, later, the transport to a team commons; default yes for new vaults, respect an
existing repo as-is).

## 2. Scaffold through the rails

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/rails/promote.py" init --vault <path> --author "<name>"
```

Then copy the starter templates into the vault so the user owns and edits them
(never copy over an existing file):

```bash
cp -n "${CLAUDE_PLUGIN_ROOT}/templates/"{house-style.md,selection-rubric.md,fidelity-checklist.md,domain-rules.md} \
      <vault>/share/_style/
```

If they wanted git: `git init`, write a `.gitignore` containing `surfaces/_inbox/`
(candidates are transient and regenerable; only durable layers travel), initial commit.

## 3. Optional: connect a team commons

Ask whether they have a **commons repo** (a shared git repo where a team or community
publishes briefs and packs — see `${CLAUDE_PLUGIN_ROOT}/docs/commons-contract.md`). If
yes, clone it locally and add an entry to the `commons` list in `surface.config.json`:

```json
"commons": [{ "name": "my-team", "path": "~/vaults/my-team-commons", "audience": "team" }]
```

The `audience` declaration matters: `team` accepts `share-now` + `team`-tier artefacts;
`public` accepts `share-now` only — the rails enforce this at publish time, so declare
it honestly. A person can belong to several commons (a private team one AND a public
community one); each is its own list entry. If no, skip — the loop is fully useful
solo, and `/scan` will explain the commons when they are ready.

## 4. Explain the loop (briefly, in your own words)

- **/surface** — after a working session, harvests the durable insights into the vault.
  You judge every candidate: keep, dump, or act. Your verdicts are remembered and become
  the system's taste.
- **/weave** — tends the whole vault: connections, contradictions, the index.
- **/share** — turns what the vault holds into things a team can absorb: briefs, digests,
  packs. Nothing is shared without your explicit gate.
- **/scan** — finds the connections between long lists of work that humans miss — across
  your vault, and across your team's commons if you have one.

Tell them the cold-start plainly: the loop gets better with use, because every keep/dump
verdict trains it.

## 5. Take stock of their history — offer the first fill

Nobody installing a plugin is on day one of Claude Code. Look at
`~/.claude/projects/*/` (count substantive transcript files, note the date range and
project spread) and tell them what you found:

- **Real history** (roughly 5+ substantive sessions): *"You have 23 sessions across 4
  projects going back to April — your past work can join the vault too."* Offer to run
  the backfill sweep now (it hands off to `/surface backfill`: bounded batches, keep/dump
  as normal) or later. Backfilling the most recent batch right now is the strongest
  first experience — the vault is non-empty within minutes of onboarding.
- **Little history** (a fresh setup): say so, skip the offer, and give the ONE next
  step instead: **go do a real piece of work with Claude Code — research a question,
  draft something, build something — and when the session winds down (or the next
  morning), run `/surface`.** Not homework, not migration: the vault fills from real
  work or not at all.

(The fuller first-week arc is in the plugin README; don't recite it here.)

Connection management, mentioned once: `promote.py commons list` shows what this vault
is connected to (also shown by `status`); `commons remove <name>` disconnects instantly
and touches nothing already published.

The scaffold follows Karpathy's three layers: `sources/` (raw immutable inputs — drop
articles, papers, notes there and /weave distils them), `wiki/` (the LLM-maintained,
human-reviewed knowledge), and a vault `CLAUDE.md` (the schema — any Claude session
opened in the vault knows the rules). Say so in one sentence; it helps people who read
the gist recognise the shape.

Last practical note: `init` registers the vault in `~/.claude/surface-vaults.json`, so
the verbs work from **any** folder — the user keeps working in their normal project
directories and `/surface` still finds the vault. With several vaults, the skills ask
which one.

## Guardrails

- Never overwrite existing user files; `cp -n` and check before writing.
- The vault belongs to the user. Do not commit or push it without asking (first-time
  setup commit excepted, with their okay).
- If `python3 --version` is below 3.9 or missing, stop and tell them — that is the only
  hard prerequisite beyond Claude Code and git.
