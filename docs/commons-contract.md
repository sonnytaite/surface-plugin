# The commons contract

A **commons** is the optional team layer: a plain shared git repo where each person's
gated briefs and packs land. No server, no service — git is the transport. The moment
two vaults publish into one commons, `/scan` can find connections *between people's
work*: same problem attacked from two angles, a described problem matching someone
else's prototype, clusters nobody has named.

**The plugin repo is not a commons.** Nobody's research goes to the repo you installed
this plugin from, ever — it ships code only. A commons only exists when your group
creates one and you add it to your own `surface.config.json`. Anyone can create one:
a team, a community of practice, an organisation, a public interest group.

## Gating — three layers, none of them optional

1. **Your gate (per artefact).** Nothing enters any commons without your explicit
   approval of that specific brief or pack. `/share` cannot auto-publish.
2. **The rail (in code).** The only path into a commons is
   `promote.py publish <artefact> --commons <name>`, and it refuses: `hold`-tier
   material (everywhere, always); artefacts with **no** sensitivity tag (untagged is a
   refusal, not a default); `team`-tier material offered to a `public`-audience
   commons; and any file — pack contents included — carrying a shield marker. A
   mis-aimed publish fails loudly instead of leaking quietly.
3. **The repo (git-native).** Who can *read* a commons is repo visibility: a private
   repo for a team, an internal repo for an org, a public repo for a community. Who can
   *write* is membership plus, if you want a second human gate at the community
   boundary, ordinary branch protection — contributors publish to a branch and open a
   PR; maintainers merge. Nothing new to learn or run; it is just a git repo.

## Choosing an audience honestly

Each commons entry in `surface.config.json` declares `audience: team | public`. Declare
what the *repo access* actually is, not what you intend: if the repo is world-readable,
its audience is `public` even if only five friends know the URL — and the rail will then
correctly refuse `team`-tier material. One person can publish to several commons (a
private team one and a public community one); each artefact goes to the commons whose
audience matches its tier.

## Repo shape

```
<commons-repo>/
├── README.md                  # what this commons is, who is in it
├── <author>/                  # one directory per person, kebab-case
│   ├── briefs/<slug>.md
│   ├── packs/<slug>/          # README.md + the artefact
│   └── connections.md         # optional: connections this person proposes
```

People only write under their own directory. Connections to someone else's work are
*proposed* (in your `connections.md` or a conversation), never edited into their files.

## The frontmatter contract

Every brief and pack README carries this frontmatter — it is what makes the commons
machine-scannable. `/share` writes it automatically; hand-authored contributions are
welcome if they carry it too.

```yaml
---
title: "..."
type: insight | pattern | problem | prototype | brief | pack
author: your-name
date: YYYY-MM-DD
stage: thought piece | vision | options explored | prototype | in production
sensitivity: share-now | team          # hold never enters a commons
tags: [..]
connects: [author/slug, ..]            # known related items, both people's
sources: [..]                          # what grounds it (titles/refs, not private paths)
---
```

Two fields do the heavy lifting:

- **`type: problem`** is first-class. A fully-described, evidence-enriched problem —
  what it is, who has it, what has been tried, what data exists — is as valuable a
  contribution as any solution, and it is what lets `/scan` match problems to
  capabilities across the team. If you know a problem deeply, publish the problem.
- **`stage`** keeps the commons honest. A vision in the commons is useful; a vision
  disguised as a product poisons trust in everyone's entries.

## Ground rules

- Everything in a commons passed its author's human gate first — the commons never
  receives auto-published content.
- `hold`-tier and shielded material never enters, even in excerpts, even in connection
  descriptions.
- The commons is append-mostly: correct your own entries in place (stage changes rung
  as work progresses); never rewrite someone else's.
