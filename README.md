# surface

[![CI](https://github.com/sonnytaite/surface-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/sonnytaite/surface-plugin/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A Claude Code plugin for the augmented researcher who runs ahead of their team —
and wants to hand the leap back.

## The problem

When you work with a strong AI, you move fast. Sessions produce decisions, named ideas,
prototypes, dead ends that taught you something — and almost all of it stays trapped in
the session. Your teammates can't see the leaps you made, because the context that
produced them scrolled past at machine speed. The better the AI gets, the wider this gap
grows: the lone augmented researcher pulls further ahead, and there is no good way to
share back.

There is a second, quieter problem: once enough work accumulates — projects, research
threads, described problems, several people's outputs — the *connections between items*
outnumber what any human can hold. Real links go unseen because the list is long, not
because the links are subtle.

`surface` is a working answer to both: a bounded, human-verified loop that harvests what
your sessions taught you into a personal knowledge vault, and turns the vault into
things a team can actually absorb — plus a connection engine for the links nobody can
see by reading a list.

## Four verbs

| Command | What it does |
|---|---|
| **`/capture`** | Harvest a working session: extract the durable insights, run them past an adversarial critic, ask you keep/dump on each, weave the keeps into your wiki. Run it again anytime — it does the right next thing. |
| **`/weave`** | Tend the whole vault: ingest new raw material, refresh stale pages, find cross-connections, flag contradictions, update the index. One reversible commit. |
| **`/share`** | Give the work back: a ranked **digest** (back-of-magazine executive summaries of everything), a **brief** (one idea, told properly), or a **pack** (the artefact itself — prototype, mockup, or a deeply-described problem — with how-to-run and the decision trail). Every draft passes an adversarial fidelity check before it reaches you, and nothing leaves without your explicit gate. `/share review` flips the same machinery inward: a private review digest of everything you've worked on, grouped by recency (active / drifting / dormant) with your open threads — so three-week-old work stops vanishing into the abyss. |
| **`/scan`** | Find machine-scale connections — across your vault, and across your team's shared **commons** repo if you have one: same problem attacked from two angles, a problem matching someone else's prototype, clusters nobody has named. |

Plus `/onboard`, once, to set up your vault.

## What makes it trustworthy

- **The human gate is load-bearing.** Nothing enters your wiki and nothing leaves your
  vault without your verdict. The loop proposes; you dispose.
- **Guarantees live in code, not prompts.** A small stdlib-only Python script
  ([rails/promote.py](rails/promote.py)) enforces the hard rails: content tagged
  `do-not-syndicate` is refused and never written; every candidate carries provenance;
  disposed items never resurface; every verdict is an append-only log line.
- **Doer ≠ judge.** The agent that drafts never grades its own work. A separate critic
  tries to refute every harvested candidate; a separate verifier tries to fail every
  outward draft against a checklist you own.
- **Stage honesty.** Everything shared carries its stage — *thought piece / vision /
  options explored / prototype / in production* — and the verifier blocks anything
  dressed up a rung. A vision shared as a vision builds trust; a vision shared as a
  product spends it.
- **It learns your taste.** Every keep/dump is logged. There is no built-in definition
  of a "good insight" — your dispositions are the rubric, and the written rubric is a
  file you edit.

## Prerequisites

Minimum (this is all of it):

- [Claude Code](https://claude.com/claude-code)
- Python 3.9+ (stdlib only — no packages, no API keys, no network calls)
- git

You do **not** need an existing note system. A **vault** is just a folder where your
research, projects, and notes live — your second brain. `/onboard` offers the choice on
first run: **create a new vault** (it scaffolds everything; the convention is
`~/vaults/<context>`, one vault per life-context so work and personal never share a
sensitivity boundary) or **adopt an existing folder** (an Obsidian vault, a
Karpathy-style LLM wiki, any markdown folder — Surface adds its config alongside and
never rewrites your notes). A curated, densely-linked personal wiki is where this ends
up — it is the outcome, not the entry fee.

## Install

```
/plugin marketplace add sonnytaite/surface-plugin
/plugin install surface@surface-plugin
/surface:onboard
```

Then finish a real working session and run `/surface:capture`.

**A note on command names:** Claude Code namespaces plugin commands, so the full forms
are `/surface:onboard`, `/surface:capture`, `/surface:weave`, `/surface:share`, and
`/surface:scan` — typing the short name in the `/` picker finds them. These docs write
the short forms (`/capture`, `/share`, …) for readability.

## Your first week

The loop feeds on your real work, not on homework. There is nothing to fill in,
migrate, or study first — the vault starts empty and that is correct.

1. **Day one — install, onboard, then just work.** Set up your vault with `/onboard`
   (a few minutes). Then do a normal piece of work with Claude Code — research a
   question, draft a document, prototype something. Any session where you learned
   something counts.
2. **End of that session — run `/capture`.** It extracts the durable insights, a
   critic argues against each one, and you answer keep or dump. Your first few wiki
   pages appear. This is the moment the plugin proves itself or doesn't — if a real
   session gives you nothing worth keeping, tell us, that's a bug report.
   *(Already have weeks of Claude Code history? `/capture backfill` sweeps your past
   sessions in bounded batches — past-you joins the vault too.)*
3. **Rest of the week — repeat.** `/capture` after each substantive session. Keep/dump
   takes a minute; your dumps are training signal, not waste. Run `/weave` once toward
   the end of the week — it links what accumulated and tidies the index.
4. **When the wiki has ~10+ pages — run `/share`.** The digest shows you what you've
   built up, ranked by what is worth a teammate's attention. Pick one, get a brief
   (or point `/share` at a project folder for a pack), gate it, publish it to your
   team's commons.
5. **Once two people have published — run `/scan`.** This is where the compound
   interest starts: connections between people's work that nobody spotted.

One habit carries the whole thing: **end real sessions with `/capture`.** Everything
else follows from the vault that habit builds.

## The team layer (optional)

Point two or more vaults at a shared git repo — the **commons** — and `/share` publishes
gated briefs and packs into it, while `/scan` finds the connections between people's
work. The contract is one page: [docs/commons-contract.md](docs/commons-contract.md).

Standing a team up takes one person ~20 minutes: [docs/team-setup.md](docs/team-setup.md)
has the steps and a copy-paste commons README template.

To be clear about gating: **this plugin repo is not a commons** — nobody's research
ever lands here. A commons is a repo *your* group creates (private for a team, public
for a community — you can belong to several), and the only path into one is a rails
command that refuses `hold`-tier, untagged, shielded, or audience-mismatched material
in code, before git access control even comes into play. Reading is gated by repo
visibility; writing by repo membership (plus PR review, if a community wants a second
human gate).
One field worth calling out: `type: problem` is first-class. A fully-described,
evidence-enriched problem is as valuable a contribution as a solution — often more —
and it is what lets the commons match the people who understand problems deeply with
the people building things.

## Shape of a vault

```
your-vault/
├── surface.config.json      # paths, categories, commons, shield markers
├── dashboard.html           # the lens: scorecard, recency ladder, library — regenerated after every verb
├── CLAUDE.md                # the vault's schema — any Claude session here knows the rules
├── sources/                 # raw, immutable inputs you drop in; /weave distils them
├── wiki/                    # the second brain: index + projects/research/themes
├── share/                   # what you give back: briefs/ digests/ packs/
│   ├── _style/              # YOUR copies: house style, rubric, checklist, domain rules
│   └── lexicon.md           # coined terms, defined once
└── surfaces/                # loop state: _inbox/ (triage queue) + dispositions.jsonl
```

Your actual project repos and research folders stay wherever they live today — the
vault holds pages *about* them (what, why, status, where the repo lives), never the
projects themselves. Only `sources/` holds real content: raw inputs you drop in for
distilling.

The shape is Karpathy's three layers — `sources/` (input), `wiki/` (LLM-maintained
knowledge), `CLAUDE.md` (schema) — with the share layer and loop state added. Vaults
register in `surface-vaults.json` in Claude's config dir (`$CLAUDE_CONFIG_DIR`, default
`~/.claude`) at init, so the verbs work from any project folder: you keep working where
you normally work, and `/capture` finds the vault.

The `_style/` files are the point: the voice, the selection rubric, the fidelity
checklist, and your domain rules are markdown you edit, not prompts you can't see.

## Lineage

This plugin packages a loop that was hand-built and dogfooded first; the machinery
earned its way here by producing briefings a real team read. It stands on:

- **Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)**
  — the spec for a personal, densely-linked plain-text knowledge base that an LLM
  maintains and a human reviews shaped the vault format, and his four daily operations
  map closely onto the verbs here (capture → `/capture`, sync + lint → `/weave`,
  digest → `/share`). Recommended reading before (or after) your first vault.
- **Every's [compound-engineering](https://github.com/EveryInc/compound-engineering)
  plugin** — the architectural model for shipping a way-of-working as a Claude Code
  plugin, and the lesson (from their own pivots) that users remember a few workflow
  verbs, not many component commands. The compounding idea itself — every cycle makes
  the next one better — is theirs too; here it takes the form of dispositions training
  the rubric.
- **Anthropic's Claude Code** plugin, skill, and subagent system, which makes
  doer ≠ judge a first-class pattern.

## The dashboard, and GUIs generally

From the moment `/onboard` finishes, your vault has **`dashboard.html`** — a
self-contained page showing your setup, the harvest scorecard (sessions, keep rate,
queue), the active/drifting/dormant recency ladder, commons health, and a linked
library of every digest, brief, and pack. Every verb regenerates it, so it is always
current — and it is deliberately **read-only**: a lens over the files, never a second
place where state lives. (A companion app that *claims* to show live system state
inevitably drifts from the files and starts lying; a page regenerated from them
cannot.)

For editing, graph visualisation, and wandering the wiki: open the vault in
[Obsidian](https://obsidian.md) — it is just markdown, so backlinks, graph view, and
click-to-edit come free, and can never disagree with the plugin because the files *are*
the state. See → dashboard; touch → Obsidian; do → the verbs.

## Roadmap

- the styled render treatment for `/scan` reports (review digests already have it);
- optional per-command model/effort overrides in the config (everything currently
  inherits your session's model, so every plan tier already works);
- richer dashboard cards as usage teaches us what belongs there — always generated,
  never live.

## Status

**v0.3.5 — young but tested.** The loop shape is proven in daily personal use; this
packaged, vault-agnostic form is young. The rails (`promote.py`) carry a full test
suite and CI; the skills are still earning their edges. See [CHANGELOG.md](CHANGELOG.md).
Issues and PRs welcome.

## License

MIT — see [LICENSE](LICENSE).
