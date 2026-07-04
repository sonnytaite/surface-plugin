# surface

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
| **`/surface`** | Harvest a working session: extract the durable insights, run them past an adversarial critic, ask you keep/dump on each, weave the keeps into your wiki. Run it again anytime — it does the right next thing. |
| **`/weave`** | Tend the whole vault: ingest new raw material, refresh stale pages, find cross-connections, flag contradictions, update the index. One reversible commit. |
| **`/share`** | Give the work back: a ranked **digest** (back-of-magazine executive summaries of everything), a **brief** (one idea, told properly), or a **pack** (the artefact itself — prototype, mockup, or a deeply-described problem — with how-to-run and the decision trail). Every draft passes an adversarial fidelity check before it reaches you, and nothing leaves without your explicit gate. |
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
/onboard
```

Then finish a real working session and run `/surface`.

## The team layer (optional)

Point two or more vaults at a shared git repo — the **commons** — and `/share` publishes
gated briefs and packs into it, while `/scan` finds the connections between people's
work. The contract is one page: [docs/commons-contract.md](docs/commons-contract.md).
One field worth calling out: `type: problem` is first-class. A fully-described,
evidence-enriched problem is as valuable a contribution as a solution — often more —
and it is what lets the commons match the people who understand problems deeply with
the people building things.

## Shape of a vault

```
your-vault/
├── surface.config.json      # paths, categories, commons, shield markers
├── wiki/                    # the second brain: index + projects/research/themes
├── share/                   # what you give back: briefs/ digests/ packs/
│   ├── _style/              # YOUR copies: house style, rubric, checklist, domain rules
│   └── lexicon.md           # coined terms, defined once
└── surfaces/                # loop state: _inbox/ (triage queue) + dispositions.jsonl
```

The `_style/` files are the point: the voice, the selection rubric, the fidelity
checklist, and your domain rules are markdown you edit, not prompts you can't see.

## Lineage

This plugin packages a loop that was hand-built and dogfooded first; the machinery
earned its way here by producing briefings a real team read. It stands on:

- **Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)**
  — the spec for a personal, densely-linked plain-text knowledge base that an LLM
  maintains and a human reviews shaped the vault format, and his four daily operations
  map closely onto the verbs here (capture → `/surface`, sync + lint → `/weave`,
  digest → `/share`). Recommended reading before (or after) your first vault.
- **Every's [compound-engineering](https://github.com/EveryInc/compound-engineering)
  plugin** — the architectural model for shipping a way-of-working as a Claude Code
  plugin, and the lesson (from their own pivots) that users remember a few workflow
  verbs, not many component commands. The compounding idea itself — every cycle makes
  the next one better — is theirs too; here it takes the form of dispositions training
  the rubric.
- **Anthropic's Claude Code** plugin, skill, and subagent system, which makes
  doer ≠ judge a first-class pattern.

## Status

**v0.1 — prototype.** The loop shape is proven in daily personal use; this packaged,
vault-agnostic form is young. Expect edges. Issues and PRs welcome.

## License

MIT — see [LICENSE](LICENSE).
