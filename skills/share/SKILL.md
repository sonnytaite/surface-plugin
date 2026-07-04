---
name: share
description: Turn what the vault holds into something a team can absorb — a ranked digest of what is worth sharing, a brief (HBR-style short article) for one idea, or a pack (the artefact itself, bundled with how-to-run and the decision trail) for a project or prototype. Run "/share" bare for the digest menu, "/share <idea-or-slug>" for a brief, "/share <path>" for a pack. Nothing leaves the vault without the user's explicit gate.
argument-hint: "[idea-slug | path-to-project]"
---

# /share — give the work back

You are the SHARE side of the Surface loop. The vault is *pull* (you query when you know
what to ask); `/share` is **push** — it offers what is worth the team's attention without
the user having to formulate the query. **Selection is the hard part, not prose.**
Selection happens on paper (the digest) before anything is written.

Find the vault via `surface.config.json`. Read the user's edited copies of
`share/_style/house-style.md`, `share/_style/selection-rubric.md`,
`share/_style/fidelity-checklist.md`, and `share/_style/domain-rules.md` — those files
are the behaviour; edit-the-file is how the user tunes this skill.

## Route by argument

- **Bare `/share`** → ask (AskUserQuestion): **My review — everything, for my eyes** /
  **Projects digest** / **Research digest** / **Full digest — everything,
  back-of-magazine style** / **Show existing digests**. (Themes/custom categories from
  the config go in a second question if they exist.)
- **`/share review`** → the review digest directly (skip the menu).
- **`/share <idea-or-slug>`** → write a **brief** for that idea.
- **`/share <path>`** (a directory) → assemble a **pack** for that project.

## The review digest — the back page for YOUR OWN memory

Different animal from the team digests: the reader is the owner, so there is **no
rubric ranking, no sensitivity gate — `hold` items belong here** — and recency beats
importance. The job is to stop work from drifting into the abyss: what you touched three
weeks ago is fading; two months back is gone until something resurfaces it. This
resurfaces it.

Write `share/digests/<YYYY-MM-DD>-review.md`, opening with a banner: **PERSONAL REVIEW —
not for sharing (contains held material); never publish this to a commons.**

1. **Every wiki page, grouped by category** (projects / research / themes), each entry:
   one-sentence gist + stage + **last-touched date**. Compute last-touched honestly from
   git (`git log -1 --format=%as -- <file>`), falling back to file mtime — never guess.
2. **Then regroup by recency** — this ladder is the payoff:
   - **Active** (touched within ~2 weeks) — one line each, you know these.
   - **Drifting** (2–6 weeks) — full synopsis each; these are the save-able ones.
   - **Dormant** (older) — synopsis + one honest question each: *still alive, done, or
     dead?* Suggest the disposition, let the owner call it.
3. **Open threads** — sweep pages for open questions, "next:" lines, and statuses that
   look stale against reality (a "prototype next week" line from two months ago). List
   them with their page and age.

Present it in conversation too, not just as a file — the whole point is that the owner
does not go reading the wiki unprompted. If they act on an entry ("carbsync is dead",
"revive the X research"), update the page's status there and then.

The rail: because the review digest contains held material, NEVER hand it to
`promote.py publish` — and say so in the banner. (The rail would refuse a `hold`-tagged
artefact anyway; tag the review digest `sensitivity: hold` in its frontmatter so the
refusal is guaranteed, not just instructed.)

## Digest — the back-of-magazine executive summary

The model is a magazine's back-page spread: a busy reader learns what is in the *entire*
issue in two pages. A digest covers one category (projects / research / themes) or all of
them (the full digest, grouped by category).

1. **Gather** candidates from the category's wiki pages (config `categories`) — the
   load-bearing, named, connected ideas, not every page.
2. **Score each against the rubric, independently** — you are grading the wiki's ideas,
   not defending your own prose. Per candidate: the rubric dimensions, **centrality**
   (in-degree — `grep -rl "[[<page>]]" wiki/ | wc -l`, compute it, don't guess), the
   **stage** (see gates), and the wiki pages that justify the scores.
3. **Apply the two hard gates:**
   - **Stage gate.** Every entry carries its stage from the ladder — *thought piece /
     vision / options explored / prototype / in production*. An idea fails ONLY if it can
     be told only by dressing it up a rung. A concept written as the stage it is passes.
   - **Sensitivity gate.** `share-now` / `team` / `hold` per the rubric.
     `hold` items never enter a digest destined for sharing; list them for the user in a
     separate "held" note if they exist.
4. **Write** `share/digests/<YYYY-MM-DD>-<category>-digest.md`: one synopsis paragraph
   per entry (problem → insight → what it means for you), the stage line, ranked.
   Then present it and let the user pick which entries become briefs or packs.

## Brief — one idea, told properly

Write `share/briefs/<slug>.md` to the house style, **grounded in the wiki**:

- Frontmatter per the commons contract (`${CLAUDE_PLUGIN_ROOT}/docs/commons-contract.md`):
  `title, type, author, date, stage, sensitivity, tags, connects, sources`.
- Shape: Summary → **Idea in Brief** (Problem / Solution / Result) → the arc → **Where
  This Stands** (the stage, plainly) → what the reader can use tomorrow → bottom line.
- Open from what the user was actually trying to do — never a manufactured "everyone
  does X" premise. Every claim traces to a wiki page. Invent nothing.
- Explain coined terms on first use (the reader wasn't in the room) and maintain
  `share/lexicon.md` — definitions drawn from the page that defines the term.
- No raw `[[wiki-links]]` in the body — the reader can't follow them into a private
  vault. End with a reachable next step.

## Pack — when the artefact IS the message

For a project, prototype, mockup, or **a deeply-described problem**, a brief *about* it
is weaker than the thing itself. Assemble `share/packs/<slug>/`:

- `README.md` — what it is, the stage line, how to run/open it (verify the steps
  actually work before writing them), and **the decision trail**: what was tried, what
  failed and why, how it landed here. The trail is what lets a peer grasp the leap.
- The artefact (copy or link), stripped of anything shielded or `hold`-tier.
- Same commons frontmatter on the README.

## Verify, then gate — always, in this order

1. **Fidelity check (every outward draft, no exceptions):** spawn the
   `fidelity-verifier` agent with the draft path and vault path. It tries to *fail* the
   draft against the checklist + the user's domain rules. Fix block-level findings and
   re-verify (up to 3 rounds); hand persistent findings to the user, not under the rug.
2. **The human gate:** present the draft. Writing is not sharing — the user decides what
   leaves the vault, and when. On their approval, log to `share/dispositions.jsonl`:
   `{"id":"<slug>","ts":"...","verdict":"written","kind":"brief|pack|digest","stage":"...","sensitivity":"..."}`
   — and log `"shared"` when they actually send it (the strongest taste signal).
3. **Commons publish (only through the rails, never a manual copy):** if the config
   lists commons and the user wants this artefact shared beyond their vault, ask which
   commons (they are named in the config, each with an `audience`), then:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/rails/promote.py" publish <artefact> --commons <name>
   ```

   The rail enforces the boundary in code: `hold` and untagged artefacts are refused
   everywhere; `team`-tier is refused by a `public`-audience commons; shielded content
   is refused file-by-file (packs included). If it refuses, relay the reason — do not
   work around it by copying by hand. On success, commit in the commons repo
   (`share(<author>): <title>`) and push only when the user says go.

## Guardrails

- **Shield, absolute.** Content carrying a shield marker never enters any digest, brief,
  or pack.
- **Stage honesty.** Never present a concept as built. State the stage; never *claim*
  honesty in the prose — just be at the right rung.
- **Selection before prose.** No brief until a digest exists and the user picked, unless
  the user named the idea themselves.
- **Write ≠ publish ≠ send.** Three separate moments; the send is always the user's.
- Divergence between what the rubric ranks high and what the user actually picks is
  signal: suggest a rubric re-weight (bump its version) when you notice it.
