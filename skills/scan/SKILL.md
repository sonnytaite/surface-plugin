---
name: scan
description: Find the machine-scale connections humans miss — across your own vault, across your team's commons repo, or both. Surfaces clusters, same-problem-from-different-angles pairs, and bridges between different people's work, as a report the user can act on. Run "/scan" when you want to see what connects across a long list of projects, research, and problems.
argument-hint: "[local | commons | both]"
---

# /scan — the connection engine

The premise: when work accumulates — many projects, research threads, described problems,
several people's outputs — the connections between items are **machine-scale**: too many
pairs for a human to hold, so real links go unseen. `/scan` reads everything and reports
only the connections worth a human's attention.

Find the vault via `surface.config.json`.

## 1. Scope

If no argument, ask (AskUserQuestion): **My vault** / **Team commons** / **Both**.
If the config has no commons and they choose it, explain the commons contract
(`${CLAUDE_PLUGIN_ROOT}/docs/commons-contract.md`) and offer to set one up — a plain
shared git repo is all it takes.

## 2. Build the map

- **Local:** walk `wiki/` (all categories) + `share/briefs|packs` frontmatter. Collect
  per item: title, type (insight/pattern/problem/prototype/…), stage, tags, existing
  `[[links]]`/`connects`, and a one-line gist from the body.
- **Commons:** walk the commons repo the same way — every item carries the same
  frontmatter contract, plus `author`. `git pull` first.

For anything beyond a small vault, fan out subagents (one per category or per author)
to read and return structured item lists; you synthesise.

## 3. Find connections that matter

You are looking for **non-obvious, load-bearing** links — a shared noun is not a
connection. The kinds worth reporting, in value order:

1. **Same problem, different angle** — two items (often two *people*) attacking one
   underlying problem from different directions. This is the highest-value find: it
   turns two lone efforts into a collaboration.
2. **Problem ↔ capability match** — a described problem in one place and a
   prototype/pattern elsewhere that plausibly addresses it.
3. **Contradiction** — two items whose claims cannot both be true. Flag, never resolve.
4. **Cluster without a name** — several items orbiting an idea nobody has written down;
   propose the page/brief that would name it.
5. **Bridge** — an item that connects two otherwise-disjoint clusters.

For each finding: the items (with authors if commons), why the connection is real (one
sentence citing both), and the suggested next action (link the pages / introduce the two
people / write the naming page / resolve the contradiction).

## 4. Report and act

Write `share/digests/<YYYY-MM-DD>-scan.md` — findings ranked, ~5–15 of them; if you
found nothing non-obvious, say so, that is a valid result. Present it. Then offer
(AskUserQuestion, multiSelect) to apply the mechanical ones: wire `[[links]]` both ways
in the local vault, add `connects:` entries. Never edit the commons content of *other*
authors — connections to their work go in the report and, if the user wants, a
`connections.md` note in the commons under their own name.

## Guardrails

- Report connections; never merge or rewrite other people's items.
- A finding must cite both sides — no vibes-based links.
- Shielded/`hold` content is invisible to /scan output even when it can read it locally:
  connections may not leak what the item itself would not share.
