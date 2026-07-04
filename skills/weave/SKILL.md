---
name: weave
description: Tend the whole vault — ingest new raw material, refresh stale pages, find genuine cross-connections between pages, lint for contradictions and orphans, then update the index and commit. Run "/weave" periodically (weekly-ish, or after a burst of /surface runs). Incremental by default; "--full" for a deep re-link; "--dry-run" to write without committing.
argument-hint: "[--full | --dry-run]"
---

# /weave — whole-vault synthesis

`/surface` harvests one session at a time, human-gated. `/weave` is the other axis: an
autonomous, git-reversible pass over the **whole vault**. It never deletes user content
and never shares anything; its blast radius is one commit the user can revert.

Find the vault via `surface.config.json`. No vault → `/onboard` first.

## What a weave does, in order

1. **Take stock.** `git log` since the last weave commit (message prefix `weave:`), plus
   a file listing. Incremental = only what changed since then; `--full` = everything.

2. **Ingest raw material.** `sources/` is the vault's raw-input layer (Karpathy's
   Layer 1): immutable documents the owner drops in — articles, papers, notes, exports.
   Never edit or delete a source. For any source (or stray markdown outside `wiki/` and
   `share/`) not yet reflected in the wiki: extract what is durable into the right wiki page — update existing pages
   in place rather than appending duplicates. Respect the shield: skip any file whose
   body contains a shield marker (`do-not-syndicate` plus any in the config).

3. **Refresh stale pages.** Pages that reference files, repos, or projects that have
   moved on (check the referenced paths where they are local). Correct in place;
   epistemic status matters — if a page claims something is built and you cannot verify
   it, mark the claim's stage rather than deleting it.

4. **Find genuine cross-connections.** Read pages pairwise where tags/terms overlap and
   add `[[links]]` both ways ONLY where a real conceptual connection exists — a shared
   noun is not a connection. If several pages orbit an unnamed idea, propose (do not
   create) a new page and ask the user at the end. This step is the point of the weave;
   if pressed for effort, spend it here.

5. **Lint.** Contradictions between pages (flag, don't silently resolve — the user
   decides which is right), orphan pages with no in-links, dead `[[links]]`, index
   entries that no longer exist.

6. **Close.** Update `wiki/index.md` (counts, new pages), write a short weave log entry
   at the top of `<state_dir>/weave-log.md` (date, what changed, what needs the user),
   and commit: `weave: <summary>`. `--dry-run` = do everything except the commit.
   Ask before pushing.

## When to ask questions

Mostly don't — the weave is autonomous and reversible. Ask (AskUserQuestion) only when
you found something the user must decide: a contradiction between two pages, a proposed
new page, or a stale claim you cannot verify. Batch these at the END of the weave, not
during.

## Guardrails

- Never delete a user-authored page; deprecate by noting it and asking.
- Never touch `share/` outputs (they are gated artefacts) or `_inbox/` (that is
  /surface's queue).
- Shielded content stays out of the wiki, always.
- One commit per weave; the commit message lists what changed so the revert is easy.
