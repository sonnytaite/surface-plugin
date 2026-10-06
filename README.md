# surface

[![CI](https://github.com/sonnytaite/surface-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/sonnytaite/surface-plugin/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Harvest what your AI sessions taught you into a wiki you own, then hand it back to your team, with a human gate on every step.**

A Claude Code plugin for the researcher who runs ahead of their team with a strong AI and wants to bring the team along. Four verbs, a markdown vault, and rails in code that decide what may leave.

```
 a working session
       │
       ▼  /capture   extract, critic refutes, you keep or dump
 ┌───────────────────────────────┐
 │  your vault (markdown, git)   │  /weave   link, refresh, lint, index
 │  sources/  wiki/  share/      │
 └───────────────────────────────┘
       │
       ▼  /share     digest, brief or pack; verifier tries to fail it
   your gate  ──►  your team's commons repo
       │
       ▼  /scan      the connections nobody can see by reading a list
```

## Install

```
/plugin marketplace add sonnytaite/surface-plugin
/plugin install surface@surface-plugin
/surface:onboard
```

Then finish a real working session and run `/surface:capture`. Needs Claude Code, Python 3.9+ (standard library only, no packages, no API keys, no network calls) and git. Claude Code namespaces the commands, so the full forms are `/surface:capture`, `/surface:weave`, `/surface:share`, `/surface:scan` and `/surface:onboard`; these docs use the short forms.

## The problem it answers

When you work with a strong AI you move fast. Sessions produce decisions, named ideas, prototypes and dead ends that taught you something, and almost all of it stays in the session. Your teammates cannot see the leaps, because the context that produced them scrolled past at machine speed. The better the AI gets, the wider the gap.

A second, quieter problem: once enough work accumulates, the connections between items outnumber what any person can hold. Real links go unseen because the list is long, not because the links are subtle.

## Four verbs

| Command | What it does |
|---|---|
| **`/capture`** | Harvest a working session: extract the durable insights, run them past an adversarial critic, ask you keep or dump on each, weave the keeps into your wiki. Run it again any time; it does the right next thing. |
| **`/weave`** | Tend the whole vault: ingest new raw material, refresh stale pages, find cross-connections, flag contradictions, update the index. One reversible commit. |
| **`/share`** | Give the work back: a ranked **digest** (short executive summaries of everything), a **brief** (one idea, told properly), or a **pack** (the artefact itself, a prototype, mockup or well-described problem, with how to run it and the decision trail). Every draft passes an adversarial fidelity verifier before it reaches your gate. |
| **`/scan`** | Find machine-scale connections across your vault, and across your team's shared **commons** repo if you have one: the same problem attacked from two angles, a problem matching someone else's prototype, clusters nobody has named. |

Plus `/onboard`, once, to set up your vault.

## What makes it trustworthy

- **The human gate is load-bearing.** Nothing enters your wiki and nothing leaves your vault without your verdict. The loop proposes; you dispose.
- **Guarantees live in code, not prompts.** A small standard-library Python script ([rails/promote.py](rails/promote.py), 39 tests, run in CI) enforces the hard rails: content tagged `do-not-syndicate` is refused and never written; every candidate carries provenance; disposed items never resurface; every verdict is an append-only log line.
- **The doer is not the judge.** The agent that drafts never grades its own work. A separate critic tries to refute every harvested candidate; a separate verifier tries to fail every outward draft against a checklist you own.
- **Stage honesty.** Everything shared carries its stage (thought piece, vision, options explored, prototype, in production) and the verifier blocks anything dressed up a rung. A vision shared as a vision builds trust; a vision shared as a product spends it.
- **It learns your taste.** Every keep or dump is logged. There is no built-in definition of a good insight: your dispositions are the rubric, and the written rubric is a file you edit.

## Your first week

The loop feeds on your real work. There is nothing to fill in, migrate or study first; the vault starts empty and that is correct.

1. **Day one: install, onboard, then just work.** `/onboard` takes a few minutes and offers a choice: create a new vault (the convention is `~/vaults/<context>`, one vault per life context so work and personal never share a sensitivity boundary) or adopt an existing folder (an Obsidian vault, a Karpathy-style LLM wiki, any markdown folder; surface adds its config alongside and never rewrites your notes). Then do a normal piece of work with Claude Code.
2. **End of that session: run `/capture`.** It extracts the durable insights, a critic argues against each one, and you answer keep or dump. Your first wiki pages appear. If a real session gives you nothing worth keeping, that is a bug report. Already have weeks of history? `/capture backfill` sweeps past sessions in bounded batches.
3. **Rest of the week: repeat.** `/capture` after each substantive session; keep or dump takes a minute, and your dumps are training signal. Run `/weave` once toward the end of the week.
4. **When the wiki has ten or more pages: run `/share`.** The digest shows what you have built up, ranked by what is worth a teammate's attention. Pick one, get a brief (or point `/share` at a project folder for a pack), gate it, publish it to your team's commons.
5. **Once two people have published: run `/scan`.** Connections between people's work that nobody spotted.

One habit carries the whole thing: end real sessions with `/capture`.

## The team layer (optional)

Point two or more vaults at a shared git repo, the **commons**, and `/share` publishes gated briefs and packs into it while `/scan` finds the connections between people's work. The contract is one page: [docs/commons-contract.md](docs/commons-contract.md). Standing a team up takes one person about twenty minutes: [docs/team-setup.md](docs/team-setup.md).

This plugin repo is not a commons; nobody's research lands here. A commons is a repo your group creates (private for a team, public for a community), and the only path into one is a rails command that refuses `hold`-tier, untagged, shielded or audience-mismatched material in code, before git access control comes into play. `type: problem` is first-class: a well-described, evidence-enriched problem is as valuable a contribution as a solution, and it is what lets the commons match the people who understand problems with the people building things.

## Shape of a vault

```
your-vault/
├── surface.config.json      # paths, categories, commons, shield markers
├── dashboard.html           # the lens: scorecard, recency ladder, library; regenerated after every verb
├── CLAUDE.md                # the vault's schema; any Claude session here knows the rules
├── sources/                 # raw, immutable inputs you drop in; /weave distils them
├── wiki/                    # the second brain: index + projects, research, themes
├── share/                   # what you give back: briefs, digests, packs
│   ├── _style/              # your copies: house style, rubric, checklist, domain rules
│   └── lexicon.md           # coined terms, defined once
└── surfaces/                # loop state: _inbox/ (triage queue) + dispositions.jsonl
```

Your project repos and research folders stay where they are; the vault holds pages about them, never the projects themselves. Only `sources/` holds real content. The shape is Karpathy's three layers (`sources/` as input, `wiki/` as LLM-maintained knowledge, `CLAUDE.md` as schema) with the share layer and loop state added. Vaults register in `surface-vaults.json` in Claude's config dir (`$CLAUDE_CONFIG_DIR`, default `~/.claude`), so the verbs work from any project folder.

The `_style/` files are the point: the voice, the selection rubric, the fidelity checklist and your domain rules are markdown you edit, not prompts you cannot see.

## The dashboard

From the moment `/onboard` finishes, your vault has `dashboard.html`: a self-contained page showing your setup, the harvest scorecard (sessions, keep rate, queue), the active, drifting and dormant recency ladder, commons health, and a linked library of every digest, brief and pack. Every verb regenerates it and it is deliberately read-only: a lens over the files, never a second place where state lives. For editing and wandering the wiki, open the vault in [Obsidian](https://obsidian.md); it is just markdown.

## Lineage

- **Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)**: the spec for a personal, densely linked plain-text knowledge base that an LLM maintains and a human reviews. It shaped the vault format, and his daily operations map onto the verbs here (capture, sync and lint, digest).
- **Every's [compound-engineering](https://github.com/EveryInc/compound-engineering) plugin**: the model for shipping a way of working as a Claude Code plugin, and the lesson that users remember a few workflow verbs, not many component commands. The compounding idea is theirs too; here it takes the form of dispositions training the rubric.
- **Anthropic's Claude Code** plugin, skill and subagent system, which makes "the doer is not the judge" a first-class pattern.

## Status

**v0.3.5, young but tested.** In daily use on the author's own vault since June 2026, with a companion plugin, [steward](https://github.com/sonnytaite/steward), that reads the same vault for a weekly "what needs you" brief. The rails carry a full test suite and CI; the skills are still earning their edges. See [CHANGELOG.md](CHANGELOG.md). Issues and PRs welcome.

Roadmap: the styled render treatment for `/scan` reports; optional per-command model and effort overrides in the config; richer dashboard cards as usage teaches what belongs there, always generated, never live.

## Licence

MIT, see [LICENSE](LICENSE).
