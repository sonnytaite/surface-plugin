---
name: onboard
description: One-time setup for the Surface loop — create (or adopt) your vault, write the config, seed the style and rubric templates, and explain how the loop works. Run "/onboard" once after installing the surface plugin, or again to repair/relocate a vault.
argument-hint: "[vault-path]"
---

# /onboard — set up your Surface vault

You are setting up a **vault**: a plain folder of markdown that the Surface loop reads and
writes. One vault per person. Everything the loop learns about the user lives in *their*
vault; nothing personal lives in the plugin.

## 1. Find out where the vault should live

If the user passed a path, use it. Otherwise ask (AskUserQuestion):

- **New folder** — recommend `~/vault` or similar; create it.
- **Existing notes folder / Obsidian vault** — adopt it in place. The loop only adds
  `surface.config.json`, a `surfaces/` state dir, and (if absent) `wiki/` and `share/`
  dirs; it never rewrites existing notes.

Also ask for their **name** (stamped as `author` on shared outputs) and whether they want
the vault to be a **git repo** (recommended — it is the undo button and, later, the
transport to a team commons).

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

Ask whether they have a **team commons repo** (a shared git repo where teammates publish
briefs and packs — see `${CLAUDE_PLUGIN_ROOT}/docs/commons-contract.md`). If yes, clone it
somewhere local and set `commons.enabled: true` and `commons.path` in
`surface.config.json`. If no, skip — the loop is fully useful solo, and `/scan` will
explain the commons when they are ready.

## 4. Explain the loop (briefly, in your own words)

- **/surface** — after a working session, harvests the durable insights into the vault.
  You judge every candidate: keep, dump, or act. Your verdicts are remembered and become
  the system's taste.
- **/weave** — tends the whole vault: connections, contradictions, the index.
- **/share** — turns what the vault holds into things a team can absorb: briefs, digests,
  packs. Nothing is shared without your explicit gate.
- **/scan** — finds the connections between long lists of work that humans miss — across
  your vault, and across your team's commons if you have one.

Tell them the honest cold-start: the loop gets better with use, because every keep/dump
verdict trains it. The first `/surface` run is the acceptance test — point it at a real
session.

## Guardrails

- Never overwrite existing user files; `cp -n` and check before writing.
- The vault belongs to the user. Do not commit or push it without asking (first-time
  setup commit excepted, with their okay).
- If `python3 --version` is below 3.9 or missing, stop and tell them — that is the only
  hard prerequisite beyond Claude Code and git.
