#!/usr/bin/env python3
"""surface — deterministic rails for the Surface loop.

The Surface loop is: source -> surfacer (Claude, the doer) -> critic (a separate
judge) -> YOU (the human gate: keep / act / dump) -> sink (your wiki, your
share layer). Claude supplies judgment; this script supplies the guarantees.

Every guarantee lives HERE, in code, not in a prompt:
  - shield        content tagged do-not-syndicate is refused, logged, never written
  - provenance    no candidate without a --source reference
  - dedup         disposed candidates never resurface (remember-the-drop)
  - dispositions  every verdict is an append-only row in dispositions.jsonl
                  (this is also the learning signal: your keeps/dumps ARE the rubric)

Deliberately standalone: Python 3.9+, stdlib only, no network, no API keys.

Vault resolution order: --vault flag > SURFACE_VAULT env > walk up from cwd
looking for surface.config.json.

Usage:
  python3 promote.py init [--vault PATH]              scaffold a vault (used by /onboard)
  python3 promote.py add --title T --source REF       stage a candidate (body on stdin)
  python3 promote.py annotate <id> --verdict V        write a critic verdict (advisory)
  python3 promote.py dispose <id> <keep|act|dump>     record the human verdict
  python3 promote.py reconcile                        sweep _inbox/ honouring status: fields
  python3 promote.py status                           counts + inbox size
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CONFIG_NAME = "surface.config.json"
DEFAULT_SHIELD_MARKERS = ("do-not-syndicate", "do not syndicate")

DEFAULT_CONFIG = {
    "author": "",
    "wiki_dir": "wiki",
    "share_dir": "share",
    "state_dir": "surfaces",
    "categories": {
        "projects": "wiki/projects",
        "research": "wiki/research",
        "themes": "wiki/themes",
    },
    "commons": [],
    "shield_markers": [],
}

# Which sensitivity tiers may enter a commons, by the commons' declared audience.
# `hold` never leaves the vault; a missing sensitivity tag is a refusal, not a default.
COMMONS_AUDIENCE_TIERS = {
    "team": ("share-now", "team"),
    "public": ("share-now",),
}


# --- Vault + config -----------------------------------------------------------
REGISTRY = Path.home() / ".claude" / "surface-vaults.json"


def load_registry() -> list[str]:
    if not REGISTRY.exists():
        return []
    try:
        vaults = json.loads(REGISTRY.read_text())
    except json.JSONDecodeError:
        return []
    return [v for v in vaults if (Path(v).expanduser() / CONFIG_NAME).exists()]


def register_vault(root: Path) -> None:
    vaults = load_registry()
    if str(root) not in vaults:
        vaults.append(str(root))
        REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        REGISTRY.write_text(json.dumps(vaults, indent=2) + "\n")


def find_vault(explicit: str | None) -> Path:
    """--vault > SURFACE_VAULT > walk up from cwd > registry (if unambiguous).
    The registry (~/.claude/surface-vaults.json, written by init) is what lets the
    verbs work from ANY project folder, not only inside the vault."""
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("SURFACE_VAULT")
    if env:
        return Path(env).expanduser().resolve()
    d = Path.cwd()
    for p in (d, *d.parents):
        if (p / CONFIG_NAME).exists():
            return p
    known = load_registry()
    if len(known) == 1:
        return Path(known[0]).expanduser().resolve()
    if known:
        print("multiple vaults known — pass --vault one of:", file=sys.stderr)
        for v in known:
            print(f"  {v}", file=sys.stderr)
    else:
        print(
            f"no vault found: no {CONFIG_NAME} here or above, no --vault, no "
            "SURFACE_VAULT, none registered.\nRun the /onboard skill "
            "(or `promote.py init --vault <dir>`) first.",
            file=sys.stderr,
        )
    sys.exit(1)


def load_config(vault: Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    f = vault / CONFIG_NAME
    if f.exists():
        try:
            cfg.update(json.loads(f.read_text()))
        except json.JSONDecodeError as e:
            print(f"invalid {CONFIG_NAME}: {e}", file=sys.stderr)
            sys.exit(1)
    return cfg


class Vault:
    def __init__(self, root: Path):
        self.root = root
        self.cfg = load_config(root)
        state = root / self.cfg["state_dir"]
        self.inbox = state / "_inbox"
        self.dispositions = state / "dispositions.jsonl"
        self.shield_markers = tuple(
            m.lower() for m in (*DEFAULT_SHIELD_MARKERS, *self.cfg.get("shield_markers", []))
        )
        # commons: normalise legacy dict form to the list form
        raw = self.cfg.get("commons", [])
        if isinstance(raw, dict):
            raw = [{"name": "default", "path": raw.get("path", ""), "audience": "team"}] \
                if raw.get("enabled") and raw.get("path") else []
        self.commons = [c for c in raw if c.get("path")]

    def is_shielded(self, body: str) -> bool:
        low = (body or "").lower()
        return any(m in low for m in self.shield_markers)

    def find_commons(self, name: str | None) -> dict | None:
        if not self.commons:
            return None
        if name:
            return next((c for c in self.commons if c.get("name") == name), None)
        return self.commons[0] if len(self.commons) == 1 else None


# --- Small helpers -------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def slug(text: str, n: int = 50) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:n] or "untitled").strip("-")


def parse_frontmatter(path: Path) -> dict:
    """Tiny stdlib YAML-frontmatter reader (key: value lines only)."""
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fm: dict[str, str] = {}
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        if ":" in ln:
            k, v = ln.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


# --- Disposition log (the durable signal) --------------------------------------
def read_dispositions(v: Vault) -> list[dict]:
    if not v.dispositions.exists():
        return []
    out = []
    for ln in v.dispositions.read_text().splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return out


def append_disposition(v: Vault, row: dict) -> None:
    v.dispositions.parent.mkdir(parents=True, exist_ok=True)
    with v.dispositions.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def seen_ids(v: Vault) -> set[str]:
    return {r["id"] for r in read_dispositions(v) if "id" in r}


# --- Candidate files -----------------------------------------------------------
def write_candidate(v: Vault, c: dict, cid: str) -> Path:
    v.inbox.mkdir(parents=True, exist_ok=True)
    path = v.inbox / f"{cid}-{slug(c['title'])}.md"
    fm = (
        "---\n"
        f"title: \"{c['title'].replace(chr(34), chr(39))}\"\n"
        f"type: {c.get('type', 'insight')}\n"
        f"sources: [\"{c['source']}\"]\n"
        "related: []\n"
        f"created: {c['created']}\n"
        f"updated: {today()}\n"
        "confidence: medium\n"
        f"tags: [surfaced, {c['origin']}, inbox]\n"
        "status: proposed\n"
        f"candidate_id: {cid}\n"
        "---\n\n"
    )
    footer = (
        f"\n\n---\n*Surfaced from {c['source']} (origin: {c['origin']}). "
        f"**To triage:** answer the keep/dump questions when /capture asks, or set "
        f"`status:` above to `keep` / `act` / `dump` yourself (optionally add a "
        f"`reason:` line) and run /capture again to reconcile.*\n"
    )
    path.write_text(fm + (c["body"] or "") + footer)
    return path


def find_inbox_file(v: Vault, target: str) -> Path | None:
    """Resolve a candidate by filename, id-prefix, or candidate_id frontmatter."""
    if not v.inbox.exists():
        return None
    p = v.inbox / target
    if p.exists():
        return p
    for f in v.inbox.glob("*.md"):
        if f.name.startswith(target):
            return f
    for f in v.inbox.glob("*.md"):
        if parse_frontmatter(f).get("candidate_id") == target:
            return f
    return None


VAULT_CLAUDE_MD = """\
# This is a Surface vault

A personal knowledge vault managed with the `surface` Claude Code plugin
(https://github.com/sonnytaite/surface-plugin). If you are Claude working in here:

- `sources/` — raw, immutable inputs the owner drops in (articles, papers, notes,
  exports). Read them; never edit or delete them. /weave distils them into the wiki.
- `wiki/` — the curated second brain: markdown pages with [[wiki-links]], grouped by
  category. Update existing pages in place rather than creating near-duplicates; keep
  `wiki/index.md` current.
- `share/` — outward-facing artefacts (briefs, digests, packs) and the owner's style,
  rubric, checklist, and domain-rules files in `share/_style/`. Nothing here is shared
  without the owner's explicit gate.
- `surfaces/` — loop state (triage inbox + disposition log), managed by the plugin's
  rails. Do not write here by hand.
- Anything marked `do-not-syndicate` (or the shield markers in `surface.config.json`)
  never leaves this vault — not into candidates, not into shared artefacts, not into
  a commons.

The verbs: /capture (harvest a session) · /weave (tend the vault) · /share (give
back) · /scan (find connections).
"""


# --- Dashboard (the generated, read-only lens) ----------------------------------
def _page_meta(v: Vault, f: Path) -> dict:
    fm = parse_frontmatter(f)
    title = fm.get("title") or f.stem.replace("-", " ")
    try:
        rel = f.relative_to(v.root / v.cfg["wiki_dir"])
        category = rel.parts[0] if len(rel.parts) > 1 else "general"
    except ValueError:
        category = "general"
    age_days = (datetime.now(timezone.utc).timestamp() - f.stat().st_mtime) / 86400
    return {"title": title, "path": f, "category": category, "age": age_days,
            "status": (fm.get("status") or "").lower(),
            "date": datetime.fromtimestamp(f.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")}


def write_dashboard(v: Vault) -> Path:
    import html as H

    def esc(s: str) -> str:
        return H.escape(str(s))

    def link(p: Path, label: str | None = None) -> str:
        return f'<a href="{esc(p.relative_to(v.root))}">{esc(label or p.name)}</a>'

    wiki = v.root / v.cfg["wiki_dir"]
    pages = [_page_meta(v, f) for f in sorted(wiki.rglob("*.md")) if f.name != "index.md"] \
        if wiki.exists() else []
    open_pages = [p for p in pages if p["status"] not in ("done", "archived")]
    fresh = [p for p in open_pages if p["age"] <= 14]
    drifting = [p for p in open_pages if 14 < p["age"] <= 42]
    dormant = [p for p in open_pages if p["age"] > 42]
    fading = sorted(drifting + dormant, key=lambda p: p["age"])
    closed = [p for p in pages if p["status"] in ("done", "archived")]
    by_cat: dict[str, int] = {}
    for p in pages:
        by_cat[p["category"]] = by_cat.get(p["category"], 0) + 1

    rows = read_dispositions(v)
    counts: dict[str, int] = {}
    sessions: set[str] = set()
    for r in rows:
        counts[r.get("verdict", "?")] = counts.get(r.get("verdict", "?"), 0) + 1
        m = re.match(r"transcript://([^#]+)", r.get("source") or "")
        if m:
            sessions.add(m.group(1))
    kept = counts.get("keep", 0) + counts.get("act", 0)
    dumped = counts.get("dump", 0)
    published = counts.get("published", 0)
    protected = counts.get("shielded", 0)
    last_ts = max((r.get("ts", "") for r in rows), default="")
    days_idle = None
    if last_ts:
        try:
            then = datetime.strptime(last_ts[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_idle = int((datetime.now(timezone.utc) - then).days)
        except ValueError:
            pass
    inbox_all = list(v.inbox.glob("*.md")) if v.inbox.exists() else []
    parked_n = sum(1 for f in inbox_all if parse_frontmatter(f).get("status") == "parked")
    inbox_n = len(inbox_all) - parked_n
    share = v.root / v.cfg["share_dir"]

    # --- "What should you do next?" — one adaptive suggestion, with its why -----
    if inbox_n:
        nxt = ("Run <b>/capture</b> and decide keep-or-let-go.",
               f"{inbox_n} idea{'s' if inbox_n != 1 else ''} from earlier sessions "
               f"{'are' if inbox_n != 1 else 'is'} waiting for your call.")
    elif not pages and not sessions:
        nxt = ("Do a real piece of work, then run <b>/capture</b>.",
               "Your vault is ready and empty — it fills from real sessions, "
               "not from homework.")
    elif len(fading) >= 5:
        nxt = ("Run <b>/share review</b>.",
               f"{len(fading)} pieces of work are fading from memory — "
               "bring past-you back to the table.")
    elif days_idle is not None and days_idle > 7:
        nxt = ("Run <b>/capture backfill</b> to catch up.",
               f"It has been {days_idle} days since the last capture — "
               "the transcripts kept everything while you were away.")
    else:
        nxt = ("All caught up — end your next real session with <b>/capture</b>.",
               "That one habit keeps the whole thing alive.")

    keep_read = (f"You keep about {kept} of every {kept + dumped} ideas — letting go "
                 "is part of the training." if (kept + dumped)
                 else "No keep-or-let-go decisions yet — they start with your first /capture.")
    last_read = (f"Last capture {esc(last_ts[:10])}." if last_ts
                 else "No captures yet.")

    cats_html = " · ".join(f"{n} in {esc(k)}" for k, n in sorted(by_cat.items())) \
        or "It fills from your first kept idea."

    def fading_rows(cap: int = 10) -> str:
        out = []
        for p in fading[:cap]:
            tag = "drifting" if p["age"] <= 42 else "dormant"
            out.append(f"<tr><td>{link(p['path'], p['title'])}</td>"
                       f"<td class=age>{tag}</td><td class=age>{p['date']}</td></tr>")
        if len(fading) > cap:
            out.append(f"<tr><td class=age colspan=3>… and {len(fading) - cap} more "
                       "— /share review walks all of them</td></tr>")
        return "\n".join(out)

    def library(sub: str, empty: str) -> str:
        d = share / sub
        items = []
        if d.exists():
            seen: set[str] = set()
            for p in sorted(d.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if p.name.startswith(("_", ".")) or p.stem in seen:
                    continue
                seen.add(p.stem)
                sib = [link(s, s.suffix[1:]) for s in sorted(d.glob(p.stem + ".*"))
                       if s.suffix in (".md", ".html", ".pdf")]
                if p.is_dir():
                    sib = [link(p, "open")]
                if sib:
                    items.append(f"<li><span class=t>{esc(p.stem.replace('-', ' '))}</span> "
                                 f"<span class=fmt>{' · '.join(sib)}</span></li>")
        return "\n".join(items) or f"<li class=empty>{empty}</li>"

    def commons_line(c: dict) -> str:
        ok = Path(c["path"]).expanduser().is_dir()
        aud = "private team space" if c.get("audience") == "team" else "public space"
        state = "connected and working" if ok \
            else "<b class=warn>folder missing — reconnect or re-clone</b>"
        return (f"<li><span class=t>{esc(c.get('name', '?'))}</span> — {aud}, {state}."
                f"<span class=path>{esc(c['path'])}</span></li>")

    commons_html = "".join(commons_line(c) for c in v.commons) or \
        ("<li class=empty>None — this vault is solo. A team commons is a shared git "
         "repo; /scan can help set one up.</li>")

    shared_total = published + sum(
        1 for sub in ("briefs", "packs") if (share / sub).exists()
        for p in (share / sub).iterdir() if not p.name.startswith(("_", ".")))

    import subprocess
    try:
        r = subprocess.run(["git", "-C", str(v.root), "remote", "get-url", "origin"],
                           capture_output=True, text=True, timeout=10)
        vault_remote = r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        vault_remote = ""
    backup_line = (f"Backed up to <span class=path>{esc(vault_remote)}</span> — keep that repo <b>private</b>, always."
                   if vault_remote else
                   "<b class=warn>Not backed up</b> — this vault lives on one disk only. "
                   "Run /onboard to add a private remote.")

    body = f"""<!doctype html><html lang=en><head><meta charset="utf-8">
<meta name=viewport content="width=device-width,initial-scale=1">
<title>{esc(v.root.name)} — surface</title>
<style>
:root{{--paper:#f6f2ea;--card:#fdfbf7;--ink:#26221a;--soft:#8c8577;--line:#ddd6c8;
 --accent:#0f5c56;--warm:#a04b2c}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--paper);color:var(--ink);max-width:1020px;margin:0 auto;
 padding:3.5rem 1.5rem 2.5rem;
 font:16px/1.55 "Iowan Old Style","Palatino Nova",Palatino,"Book Antiqua",Charter,Georgia,serif}}
a{{color:var(--accent);text-decoration:none;border-bottom:1px solid #0f5c5640}}
a:hover{{border-bottom-color:var(--accent)}}
.kicker{{font:600 .68rem/1 -apple-system,system-ui,sans-serif;letter-spacing:.22em;
 text-transform:uppercase;color:var(--soft)}}
header h1{{font-size:2.5rem;font-weight:600;letter-spacing:-.01em;margin:.35rem 0 .5rem}}
.stamp{{color:var(--soft);font-size:.85rem}}
.next{{margin:2.2rem 0 2.4rem;padding:1.15rem 1.4rem;background:var(--card);
 border-left:3px solid var(--accent);box-shadow:0 1px 0 var(--line)}}
.next p.do{{font-size:1.3rem;margin:.3rem 0 .2rem}}
.next p.why{{color:var(--soft);font-size:.95rem}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:1.1rem}}
.card{{background:var(--card);border:1px solid var(--line);padding:1.1rem 1.2rem 1rem;
 animation:rise .45s ease-out}}
.card:nth-child(2){{animation-delay:.05s}}.card:nth-child(3){{animation-delay:.1s}}
.card:nth-child(4){{animation-delay:.15s}}
@keyframes rise{{from{{opacity:.25;transform:translateY(5px)}}to{{opacity:1;transform:none}}}}
@media(prefers-reduced-motion:reduce),print{{.card{{animation:none}}}}
.card h2{{font-size:1.02rem;font-weight:600;font-style:italic;margin-bottom:.55rem}}
.stat{{font-size:2.6rem;line-height:1;font-variant-numeric:tabular-nums;margin:.2rem 0 .1rem}}
.stat small{{font-size:.85rem;font-variant:normal;color:var(--soft);margin-left:.45rem;
 font-family:-apple-system,system-ui,sans-serif}}
.read{{font-size:.92rem;margin:.45rem 0 .2rem}}
.fine{{font-size:.85rem;color:var(--soft)}}
section{{margin-top:2.4rem}}
section>h2{{font:600 .72rem/1 -apple-system,system-ui,sans-serif;letter-spacing:.22em;
 text-transform:uppercase;color:var(--soft);margin-bottom:.8rem}}
table{{width:100%;border-collapse:collapse;font-size:.95rem}}
td{{padding:.45rem .8rem .45rem 0;border-top:1px solid var(--line)}}
.age{{color:var(--soft);font-size:.85rem;white-space:nowrap}}
.lib{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:1.1rem}}
.lib ul{{list-style:none;padding:0}}
.lib li{{padding:.4rem 0;border-top:1px solid var(--line);font-size:.93rem}}
.lib h3{{font-size:.98rem;font-weight:600}}
.t{{text-transform:capitalize}} .fmt{{color:var(--soft);font-size:.85rem;margin-left:.3rem}}
.empty{{color:var(--soft)}}
.path{{display:block;color:var(--soft);font-size:.75rem;font-family:ui-monospace,monospace;
 word-break:break-all}}
.warn{{color:var(--warm)}}
footer{{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);
 color:var(--soft);font-size:.85rem}}
footer b{{color:var(--ink);font-weight:600}}
ul.plain{{list-style:none;padding:0}} ul.plain li{{padding:.3rem 0}}
</style></head><body>

<header>
<p class=kicker>Surface · your second brain</p>
<h1>{esc(v.root.name.replace('-', ' '))}</h1>
<p class=stamp>Snapshot taken {now_iso()[:10]} · this page regenerates after every
command · the files are the truth — read and edit them in Obsidian or any editor.</p>
</header>

<div class=next>
<p class=kicker>What should you do next?</p>
<p class=do>{nxt[0]}</p>
<p class=why>{nxt[1]}</p>
</div>

<div class=cards>
<article class=card>
<h2>Is your brain growing?</h2>
<p class=stat>{len(pages)}<small>page{'s' if len(pages) != 1 else ''}</small></p>
<p class=read>{len(fresh)} touched in the last two weeks.</p>
<p class=fine>{cats_html}{f" · {len(closed)} closed" if closed else ""}</p>
</article>

<article class=card>
<h2>Are you keeping the habit?</h2>
<p class=stat>{len(sessions)}<small>session{'s' if len(sessions) != 1 else ''} captured</small></p>
<p class=read>{last_read} {keep_read}</p>
<p class=fine>{f"{inbox_n} waiting for your decision. " if inbox_n else "Nothing waiting on you. "}{f"{parked_n} parked for another vault." if parked_n else ""}</p>
</article>

<article class=card>
<h2>What are you forgetting?</h2>
<p class=stat>{len(fading)}<small>fading</small></p>
<p class=read>{f"{len(drifting)} drifting (2–6 weeks old), {len(dormant)} dormant (older)."
               if fading else "Nothing — everything is fresh or deliberately closed."}</p>
<p class=fine>{"The list is below — /share review walks it with you." if fading
               else "This fills as work ages; /share review is the antidote."}</p>
</article>

<article class=card>
<h2>What have you shared?</h2>
<p class=stat>{shared_total}<small>made to share</small></p>
<p class=read>{published} actually published to a team space — writing and sharing
are separate gates.</p>
<p class=fine>{protected} private item{'s' if protected != 1 else ''} automatically
blocked from ever leaving.</p>
</article>
</div>

{f'''<section>
<h2>Fading — worth a look before it is gone</h2>
<table>{fading_rows()}</table>
</section>''' if fading else ""}

<section>
<h2>Your library — everything made to share or recall</h2>
<div class=lib>
<div><h3>Digests &amp; reviews</h3><ul>{library("digests", "Run /share for your first digest — or /share review to see everything you have.")}</ul></div>
<div><h3>Briefs</h3><ul>{library("briefs", "A brief is one idea, told properly — /share offers them once the wiki has substance.")}</ul></div>
<div><h3>Packs</h3><ul>{library("packs", "A pack is the artefact itself, ready to hand over — /share &lt;project-path&gt;.")}</ul></div>
</div>
</section>

<section>
<h2>Your team connection</h2>
<ul class=plain>{commons_html}</ul>
</section>

<footer>
<p><b>{esc(v.cfg.get('author') or 'Unnamed')}</b>'s vault at
<span class=path>{esc(v.root)}</span></p>
<p style="margin-top:.5rem">{backup_line}</p>
<p style="margin-top:.5rem">Settings live in surface.config.json (this page only reads
them — run /onboard to change answers). The four commands, plainly:
<b>/capture</b> capture what a session taught you · <b>/weave</b> tidy and connect the
whole vault · <b>/share</b> give work back (or “/share review” to remind yourself) ·
<b>/scan</b> find connections across yours and your team's work.</p>
</footer>
</body></html>"""
    out = v.root / "dashboard.html"
    out.write_text(body)
    return out


def cmd_dashboard(args) -> int:
    v = Vault(find_vault(args.vault))
    print(f"dashboard -> {write_dashboard(v)}")
    return 0


# --- Commands -------------------------------------------------------------------
def cmd_init(args) -> int:
    root = Path(args.vault).expanduser().resolve() if args.vault else Path.cwd()
    root.mkdir(parents=True, exist_ok=True)
    cfg_path = root / CONFIG_NAME
    if cfg_path.exists():
        print(f"vault already initialised: {cfg_path}")
    else:
        cfg = dict(DEFAULT_CONFIG)
        if args.author:
            cfg["author"] = args.author
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")
        print(f"wrote {cfg_path}")
    v = Vault(root)
    for d in (
        v.inbox,
        root / "sources",
        root / v.cfg["wiki_dir"],
        *(root / p for p in v.cfg["categories"].values()),
        root / v.cfg["share_dir"] / "briefs",
        root / v.cfg["share_dir"] / "digests",
        root / v.cfg["share_dir"] / "packs",
        root / v.cfg["share_dir"] / "_style",
    ):
        d.mkdir(parents=True, exist_ok=True)
    index = root / v.cfg["wiki_dir"] / "index.md"
    if not index.exists():
        index.write_text("# Wiki index\n\nPages are listed here as they are kept.\n")
    claude_md = root / "CLAUDE.md"
    if not claude_md.exists():
        claude_md.write_text(VAULT_CLAUDE_MD)
    register_vault(root)
    dash = write_dashboard(v)
    print(f"vault ready at {root}  (registered — the verbs will find it from any folder)")
    print(f"dashboard -> {dash}  (your running reference; regenerated after every verb)")
    return 0


def cmd_add(args) -> int:
    """Stage a Claude-authored candidate through the rails: shield, dedup,
    _inbox write, disposition log. Body on stdin. Judgment is the caller's;
    the guarantees are here."""
    v = Vault(find_vault(args.vault))
    body = sys.stdin.read()
    cid = hashlib.sha1(f"{args.origin}:{args.source}:{args.title}".encode()).hexdigest()[:10]
    if cid in seen_ids(v):
        print(f"skip (already seen/disposed): {cid}")
        return 0
    if v.is_shielded(body):
        # Hard rail: log an opaque ref (so it is remembered, never re-surfaced)
        # but write NO file and store NO title or content.
        append_disposition(v, {"id": cid, "ts": now_iso(), "verdict": "shielded",
                               "reason": "do-not-syndicate", "source": args.source})
        print(f"shielded (do-not-syndicate), not written: {cid}")
        return 0
    c = {"origin": args.origin, "source": args.source, "type": args.type,
         "created": args.created or today(), "title": args.title, "body": body}
    path = write_candidate(v, c, cid)
    append_disposition(v, {"id": cid, "ts": now_iso(), "verdict": "proposed",
                           "origin": args.origin, "source": args.source, "title": args.title})
    print(f"added {cid} -> {path.name}")
    return 0


def cmd_annotate(args) -> int:
    """Write a critic verdict into a candidate's frontmatter. Advisory only:
    it never changes `status:` — the human still disposes."""
    v = Vault(find_vault(args.vault))
    f = find_inbox_file(v, args.target)
    if not f:
        print(f"no candidate matching {args.target!r} in _inbox/", file=sys.stderr)
        return 1
    text = f.read_text()
    if not text.startswith("---"):
        print("candidate has no frontmatter", file=sys.stderr)
        return 1
    _, fm_block, body = text.split("---", 2)
    order: list = []
    vals: dict = {}
    for ln in fm_block.strip("\n").splitlines():
        if ":" in ln and not ln.startswith(" "):
            k = ln.split(":", 1)[0].strip()
            vals[k] = ln
            order.append(k)
        else:
            order.append(("_raw", ln))

    def setk(key: str, value: str) -> None:
        vals[key] = f"{key}: {value}"
        if key not in order:
            order.append(key)

    setk("critic_verdict", args.verdict)
    if args.note:
        setk("critic_note", '"' + args.note.replace('"', "'") + '"')
    if args.suggest:
        setk("critic_suggest", args.suggest)

    out = [k[1] if isinstance(k, tuple) else vals[k] for k in order]
    f.write_text("---\n" + "\n".join(out) + "\n---" + body)
    print(f"annotated {f.name}: {args.verdict}" + (f" -> suggest {args.suggest}" if args.suggest else ""))
    return 0


def cmd_dispose(args) -> int:
    if args.verdict not in {"keep", "act", "dump", "park"}:
        print("verdict must be keep|act|dump|park", file=sys.stderr)
        return 1
    v = Vault(find_vault(args.vault))
    append_disposition(v, {"id": args.candidate_id, "ts": now_iso(),
                           "verdict": args.verdict, "reason": args.reason or ""})
    if args.verdict == "dump":
        f = find_inbox_file(v, args.candidate_id)
        if f:
            f.unlink()
    elif args.verdict == "park":
        # Decided, but homed elsewhere (e.g. belongs in a different vault). The file
        # stays in _inbox with status: parked so it never counts as "waiting on you".
        f = find_inbox_file(v, args.candidate_id)
        if f:
            f.write_text(f.read_text().replace("status: proposed\n", "status: parked\n", 1))
    print(f"recorded: {args.candidate_id} -> {args.verdict}")
    return 0


def cmd_reconcile(args) -> int:
    """Sweep _inbox/ honouring the `status:` property each note carries.
    dump -> log + delete; keep/act -> log + leave the file to be placed."""
    v = Vault(find_vault(args.vault))
    if not v.inbox.exists():
        print("no _inbox/ — nothing to reconcile")
        return 0
    acted = {"keep": 0, "act": 0, "dump": 0}
    untriaged = 0
    for f in sorted(v.inbox.glob("*.md")):
        fm = parse_frontmatter(f)
        status = (fm.get("status") or "").lower()
        cid = fm.get("candidate_id", "")
        if status in ("keep", "act", "dump") and cid:
            append_disposition(v, {"id": cid, "ts": now_iso(), "verdict": status,
                                   "reason": fm.get("reason", "")})
            acted[status] += 1
            if status == "dump":
                f.unlink()
        else:
            untriaged += 1
    print(f"reconciled -> keep {acted['keep']} · act {acted['act']} · dump {acted['dump']}"
          f"  (untriaged left in _inbox: {untriaged})")
    return 0


def cmd_publish(args) -> int:
    """The ONLY sanctioned path from a vault into a commons. Refuses, in order:
    unknown commons; missing/`hold` sensitivity; a tier the commons' audience does
    not permit; any shielded content anywhere in the artefact. Copy-only — the
    caller commits/pushes the commons repo, with the human's explicit okay."""
    v = Vault(find_vault(args.vault))
    if not v.commons:
        print("no commons configured — add one to surface.config.json (see docs/commons-contract.md)",
              file=sys.stderr)
        return 1
    commons = v.find_commons(args.commons)
    if not commons:
        names = ", ".join(c.get("name", "?") for c in v.commons)
        print(f"which commons? pass --commons <name>  (configured: {names})", file=sys.stderr)
        return 1
    audience = commons.get("audience", "team")
    allowed = COMMONS_AUDIENCE_TIERS.get(audience)
    if not allowed:
        print(f"commons {commons.get('name')!r} has unknown audience {audience!r} "
              f"(use one of: {', '.join(COMMONS_AUDIENCE_TIERS)})", file=sys.stderr)
        return 1
    croot = Path(commons["path"]).expanduser()
    if not croot.is_dir():
        print(f"commons path does not exist: {croot}", file=sys.stderr)
        return 1

    src = Path(args.artefact).expanduser()
    if not src.exists():
        print(f"artefact not found: {src}", file=sys.stderr)
        return 1
    is_pack = src.is_dir()
    meta_file = (src / "README.md") if is_pack else src
    if not meta_file.exists():
        print("a pack must carry a README.md with the commons frontmatter", file=sys.stderr)
        return 1

    fm = parse_frontmatter(meta_file)
    tier = (fm.get("sensitivity") or "").lower()
    if tier == "hold":
        print("REFUSED: sensitivity is `hold` — hold-tier material never enters a commons.",
              file=sys.stderr)
        return 2
    if tier not in allowed:
        have = tier or "(missing)"
        print(f"REFUSED: sensitivity {have} is not allowed in a {audience!r} commons "
              f"(allowed: {', '.join(allowed)}). Tag the artefact honestly, or pick a "
              f"commons whose audience matches.", file=sys.stderr)
        return 2

    files = sorted(p for p in src.rglob("*") if p.is_file()) if is_pack else [src]
    for f in files:
        try:
            body = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue  # binary artefact content — the shield applies to text
        if v.is_shielded(body):
            print(f"REFUSED: shielded content in {f.relative_to(src.parent)} — "
                  "nothing shielded ever enters a commons.", file=sys.stderr)
            return 2

    author = slug(v.cfg.get("author") or "")
    if author == "untitled":
        print("config has no `author` — set it in surface.config.json (it names your "
              "directory in the commons)", file=sys.stderr)
        return 1
    kind = "packs" if is_pack else ("digests" if "digest" in src.name else "briefs")
    dest = croot / author / kind / src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if is_pack:
        import shutil
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        dest.write_text(src.read_text())
    append_disposition(v, {"id": slug(src.stem), "ts": now_iso(), "verdict": "published",
                           "commons": commons.get("name"), "audience": audience,
                           "sensitivity": tier, "artefact": str(src)})
    print(f"published -> {dest}  (commons {commons.get('name')!r}, audience {audience}, "
          f"tier {tier})")
    print("Now commit + push the commons repo when the owner says go — the copy alone "
          "is not shared until pushed.")
    return 0


def describe_commons(c: dict) -> str:
    import subprocess
    p = Path(c["path"]).expanduser()
    state = "ok" if p.is_dir() else "MISSING PATH"
    remote = ""
    if p.is_dir():
        try:
            r = subprocess.run(["git", "-C", str(p), "remote", "get-url", "origin"],
                               capture_output=True, text=True, timeout=10)
            remote = r.stdout.strip() if r.returncode == 0 else "(no git remote)"
        except (OSError, subprocess.TimeoutExpired):
            remote = "(git unavailable)"
    return (f"  {c.get('name', '?'):<14} audience={c.get('audience', '?'):<7} "
            f"{state:<13} {c['path']}" + (f"\n{'':17}remote: {remote}" if remote else ""))


def save_commons(vault_root: Path, commons: list[dict]) -> None:
    cfg_path = vault_root / CONFIG_NAME
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else dict(DEFAULT_CONFIG)
    cfg["commons"] = commons
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")


def cmd_commons(args) -> int:
    """Manage commons connections. The connection is one config entry — adding it
    connects, removing it disconnects. Removing NEVER touches the commons repo or
    anything already published there."""
    v = Vault(find_vault(args.vault))
    if args.action == "list":
        if not v.commons:
            print("no commons connected — this vault is solo.\n"
                  "connect one: promote.py commons add <name> --path <dir> --audience <team|public>")
            return 0
        print(f"commons connected to {v.root.name}:")
        for c in v.commons:
            print(describe_commons(c))
        return 0
    if args.action == "add":
        if not (args.name and args.path and args.audience):
            print("usage: commons add <name> --path <dir> --audience <team|public>", file=sys.stderr)
            return 1
        if args.audience not in COMMONS_AUDIENCE_TIERS:
            print(f"audience must be one of: {', '.join(COMMONS_AUDIENCE_TIERS)}", file=sys.stderr)
            return 1
        if any(c.get("name") == args.name for c in v.commons):
            print(f"a commons named {args.name!r} is already connected", file=sys.stderr)
            return 1
        p = Path(args.path).expanduser()
        if not p.is_dir():
            print(f"path does not exist: {p} — clone the commons repo there first", file=sys.stderr)
            return 1
        entry = {"name": args.name, "path": args.path, "audience": args.audience}
        save_commons(v.root, [*v.commons, entry])
        print(f"connected: {args.name} (audience {args.audience}) -> {args.path}")
        return 0
    if args.action == "remove":
        if not args.name:
            print("usage: commons remove <name>", file=sys.stderr)
            return 1
        kept = [c for c in v.commons if c.get("name") != args.name]
        if len(kept) == len(v.commons):
            names = ", ".join(c.get("name", "?") for c in v.commons) or "(none)"
            print(f"no commons named {args.name!r} (connected: {names})", file=sys.stderr)
            return 1
        save_commons(v.root, kept)
        print(f"disconnected: {args.name}. Your local clone and anything you already "
              f"published there are untouched — to withdraw content, delete your files "
              f"in the commons repo itself and push (note: git history keeps old "
              f"versions; that is why hold-tier never enters in the first place).")
        return 0
    return 1


def cmd_status(args) -> int:
    v = Vault(find_vault(args.vault))
    rows = read_dispositions(v)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.get("verdict", "?")] = counts.get(r.get("verdict", "?"), 0) + 1
    inbox_n = len(list(v.inbox.glob("*.md"))) if v.inbox.exists() else 0
    print(f"vault: {v.root}")
    print(f"dispositions: {len(rows)} rows")
    for verdict, n in sorted(counts.items()):
        print(f"  {verdict:<10} {n}")
    print(f"_inbox awaiting review: {inbox_n}")
    if v.commons:
        print(f"commons connected: {len(v.commons)}")
        for c in v.commons:
            print(describe_commons(c))
    else:
        print("commons connected: none (solo vault)")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="promote", description="Deterministic rails for the Surface loop")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--vault", help="Vault root (default: SURFACE_VAULT env, else walk up from cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init", parents=[common], help="Scaffold a vault: config + directories (used by /onboard)")
    pi.add_argument("--author", default="", help="Your name, stamped on shared outputs")
    pi.set_defaults(func=cmd_init)

    pa = sub.add_parser("add", parents=[common], help="Stage a candidate through the rails; body on stdin")
    pa.add_argument("--title", required=True)
    pa.add_argument("--source", required=True,
                    help="provenance, e.g. transcript://<session-id>#<range> or a file path")
    pa.add_argument("--origin", default="doer")
    pa.add_argument("--type", default="insight",
                    choices=["insight", "pattern", "problem", "decision", "prototype"])
    pa.add_argument("--created", help="ISO date (default today)")
    pa.set_defaults(func=cmd_add)

    pn = sub.add_parser("annotate", parents=[common], help="Write a critic verdict into a candidate (advisory; never disposes)")
    pn.add_argument("target", help="candidate_id, id-prefix, or filename")
    pn.add_argument("--verdict", required=True,
                    choices=["pass", "weak", "duplicate", "unsupported", "contradictory"])
    pn.add_argument("--note", default="")
    pn.add_argument("--suggest", choices=["keep", "dump"])
    pn.set_defaults(func=cmd_annotate)

    pr = sub.add_parser("reconcile", parents=[common], help="Sweep _inbox/ and honour each note's status: property")
    pr.set_defaults(func=cmd_reconcile)

    pd = sub.add_parser("dispose", parents=[common], help="Record a keep/act/dump verdict by id")
    pd.add_argument("candidate_id")
    pd.add_argument("verdict")
    pd.add_argument("--reason", default="")
    pd.set_defaults(func=cmd_dispose)

    pdash = sub.add_parser("dashboard", parents=[common],
                           help="Regenerate dashboard.html from vault state (pure lens)")
    pdash.set_defaults(func=cmd_dashboard)

    pc = sub.add_parser("commons", parents=[common],
                        help="Manage commons connections: list / add / remove")
    pc.add_argument("action", choices=["list", "add", "remove"])
    pc.add_argument("name", nargs="?", help="commons name (for add/remove)")
    pc.add_argument("--path", help="local clone of the commons repo (for add)")
    pc.add_argument("--audience", choices=list(COMMONS_AUDIENCE_TIERS), help="team|public (for add)")
    pc.set_defaults(func=cmd_commons)

    pb = sub.add_parser("publish", parents=[common],
                        help="Copy a gated brief/pack into a commons (tier + shield enforced)")
    pb.add_argument("artefact", help="path to a brief .md or a pack directory")
    pb.add_argument("--commons", help="commons name from surface.config.json (optional if only one)")
    pb.set_defaults(func=cmd_publish)

    ps = sub.add_parser("status", parents=[common], help="Show disposition counts + inbox size")
    ps.set_defaults(func=cmd_status)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
