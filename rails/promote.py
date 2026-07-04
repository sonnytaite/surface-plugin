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
    "commons": {"enabled": False, "path": ""},
    "shield_markers": [],
}


# --- Vault + config -----------------------------------------------------------
def find_vault(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("SURFACE_VAULT")
    if env:
        return Path(env).expanduser().resolve()
    d = Path.cwd()
    for p in (d, *d.parents):
        if (p / CONFIG_NAME).exists():
            return p
    print(
        f"no vault found: no {CONFIG_NAME} here or above, no --vault, no SURFACE_VAULT.\n"
        "Run the /onboard skill (or `promote.py init --vault <dir>`) first.",
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

    def is_shielded(self, body: str) -> bool:
        low = (body or "").lower()
        return any(m in low for m in self.shield_markers)


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
        f"**To triage:** answer the keep/dump questions when /surface asks, or set "
        f"`status:` above to `keep` / `act` / `dump` yourself (optionally add a "
        f"`reason:` line) and run /surface again to reconcile.*\n"
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
    print(f"vault ready at {root}")
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
    if args.verdict not in {"keep", "act", "dump"}:
        print("verdict must be keep|act|dump", file=sys.stderr)
        return 1
    v = Vault(find_vault(args.vault))
    append_disposition(v, {"id": args.candidate_id, "ts": now_iso(),
                           "verdict": args.verdict, "reason": args.reason or ""})
    if args.verdict == "dump":
        f = find_inbox_file(v, args.candidate_id)
        if f:
            f.unlink()
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

    ps = sub.add_parser("status", parents=[common], help="Show disposition counts + inbox size")
    ps.set_defaults(func=cmd_status)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
