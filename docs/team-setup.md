# Setting up surface for a team

One person (you, presumably) does steps 1–2 once. Every member — including you — does
step 3 on their own machine. Total: ~20 minutes for you, ~15 per person.

New members need to know nothing in advance. The plugin explains itself at each step;
this page is for the person standing the team up.

## 1. Create the team commons (once)

The commons is a plain **private git repo** — no server, nothing to run. Create it on
your git host, invite your team as collaborators (that invitation IS the read gate),
and seed a `README.md` from the template below. Done.

## 2. Seed the commons README (template — replace the bracketed bits)

```markdown
# [Team name] research commons

A private, shared home for the research, ideas, prototypes, and well-described
problems each of us produces while working with AI — so the leaps one person makes
stop being invisible to everyone else. Your personal vault stays yours and private;
only what you explicitly gate lands here.

## Get set up (~15 minutes)

1. Install the plugin in Claude Code:
   /plugin marketplace add sonnytaite/surface-plugin
   /plugin install surface@surface-plugin
   /onboard
   (/onboard walks you through creating your vault — say yes to the defaults if unsure.)
2. Clone this repo locally:  git clone [repo-url] ~/vaults/[team]-commons
3. Connect it (or let /onboard do it when it asks about a commons):
   python3 <plugin>/rails/promote.py commons add [team] --path ~/vaults/[team]-commons --audience team
4. Then just work. Do a real piece of research or building in Claude Code and end the
   session with /capture. That's the whole habit. /share brings gated work here;
   /scan finds the connections between all of us.

## How this repo works

- One directory per person (your name, kebab-case); you only write under yours.
- Everything here passed its author's explicit gate; the plugin physically cannot
  publish hold-tier, untagged, or shielded material.
- Problems are first-class: if you know a problem deeply, publish the problem.
- Stage honesty: every artefact says what it is — thought piece / vision / options
  explored / prototype / in production. A vision labelled as a vision is welcome here.
```

## 3. Each member sets up (per person, ~15 min)

Exactly the four steps in the commons README they just got access to. Their vault is
theirs (personal machine, private); the commons connection is one command; severing it
is one command (`commons remove <name>` — touches nothing already published).

## 4. Cadence that makes it compound

- **The one habit:** everyone ends real working sessions with `/capture`. Everything
  else follows from this.
- **`/share` when a digest says so** — not on a schedule. The first briefs usually
  appear in week two.
- **`/scan` weekly, run by anyone** once two or more people have published. Post the
  scan report to the commons — the "same problem, two angles" findings are where the
  team layer pays for itself.
- **Divergence is signal:** when what people actually pick to share keeps differing
  from what their rubric ranks, they edit their rubric file. Taste stays personal;
  only gated artefacts are shared.

## Gating recap (what protects whom)

| Layer | Mechanism | Protects against |
|---|---|---|
| Your gate | explicit approval per artefact | anything leaving your vault unreviewed |
| The rail | `publish` refuses hold / untagged / shielded / audience-mismatch, in code | mis-aimed or accidental publishing |
| The repo | private repo membership; PRs if you want a second human gate | the wrong people reading |

Full contract: [commons-contract.md](commons-contract.md).
