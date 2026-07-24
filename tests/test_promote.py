"""Tests for rails/promote.py — the deterministic rails of the Surface loop.

The README claims every guarantee lives in code, not in a prompt. These tests
are that claim, executable:

  shield        do-not-syndicate content is refused, logged opaquely, never written
  provenance    no candidate without a --source reference
  dedup         disposed candidates never resurface (remember-the-drop)
  dispositions  every verdict is an append-only row
  publish       hold-tier / untagged / shielded / audience-mismatched material
                never enters a commons
  config dir    CLAUDE_CONFIG_DIR is honoured; the legacy ~/.claude registry
                is still read, never written

stdlib only (unittest), matching the plugin's no-dependency ethos.
Run:  python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from shutil import rmtree

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("promote", ROOT / "rails" / "promote.py")
promote = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(promote)


class RailsTest(unittest.TestCase):
    """Base: every test runs against a throwaway HOME, config dir, and vault."""

    def setUp(self):
        # resolve() so tests agree with promote.py on symlinked tempdirs
        # (macOS: /var -> /private/var)
        self.tmp = Path(tempfile.mkdtemp(prefix="surface-test-")).resolve()
        self.home = self.tmp / "home"
        self.cfgdir = self.tmp / "claude-config"
        self.vault = self.tmp / "vault"
        self.home.mkdir()
        self._env = {k: os.environ.get(k) for k in
                     ("HOME", "CLAUDE_CONFIG_DIR", "SURFACE_VAULT")}
        os.environ["HOME"] = str(self.home)
        os.environ["CLAUDE_CONFIG_DIR"] = str(self.cfgdir)
        os.environ.pop("SURFACE_VAULT", None)
        self._cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self._cwd)
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        rmtree(self.tmp, ignore_errors=True)

    def run_cli(self, *argv, stdin=""):
        """Invoke promote.main(argv); returns (exit_code, stdout, stderr)."""
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(stdin)
        out, err = io.StringIO(), io.StringIO()
        code = 0
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = promote.main(list(argv))
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
        finally:
            sys.stdin = old_stdin
        return code, out.getvalue(), err.getvalue()

    def init_vault(self, author="Test User"):
        code, _, err = self.run_cli("init", "--vault", str(self.vault), "--author", author)
        self.assertEqual(code, 0, err)
        return promote.Vault(self.vault)

    def add(self, title, body="a body", source="transcript://abc#1"):
        return self.run_cli("add", "--vault", str(self.vault),
                            "--title", title, "--source", source, stdin=body)

    def dispositions(self):
        f = self.vault / "surfaces" / "dispositions.jsonl"
        if not f.exists():
            return []
        return [json.loads(ln) for ln in f.read_text().splitlines() if ln.strip()]

    def inbox_files(self):
        d = self.vault / "surfaces" / "_inbox"
        return sorted(d.glob("*.md")) if d.exists() else []


# --- Config dir & registry ------------------------------------------------------
class TestConfigDir(RailsTest):
    def test_env_var_wins(self):
        self.assertEqual(promote.claude_config_dir(), self.cfgdir)
        self.assertEqual(promote.registry_path(),
                         self.cfgdir / "surface-vaults.json")

    def test_defaults_to_home_dot_claude(self):
        os.environ.pop("CLAUDE_CONFIG_DIR")
        self.assertEqual(promote.claude_config_dir(), self.home / ".claude")

    def test_blank_env_var_falls_back(self):
        os.environ["CLAUDE_CONFIG_DIR"] = "  "
        self.assertEqual(promote.claude_config_dir(), self.home / ".claude")

    def test_init_registers_in_config_dir_not_legacy(self):
        self.init_vault()
        reg = self.cfgdir / "surface-vaults.json"
        self.assertTrue(reg.exists())
        self.assertIn(str(self.vault), json.loads(reg.read_text()))
        # The fix's point: init must NOT recreate ~/.claude
        self.assertFalse((self.home / ".claude").exists())

    def test_legacy_registry_still_read_never_written(self):
        # A vault registered before the CLAUDE_CONFIG_DIR fix must still be found.
        legacy_vault = self.tmp / "old-vault"
        code, _, _ = self.run_cli("init", "--vault", str(legacy_vault))
        self.assertEqual(code, 0)
        legacy = self.home / ".claude"
        legacy.mkdir()
        (self.cfgdir / "surface-vaults.json").rename(legacy / "surface-vaults.json")
        self.assertEqual(promote.load_registry(), [str(legacy_vault)])
        # Registering a new vault merges the legacy entry into the NEW registry
        self.init_vault()
        new_reg = json.loads((self.cfgdir / "surface-vaults.json").read_text())
        self.assertIn(str(legacy_vault), new_reg)
        self.assertIn(str(self.vault), new_reg)
        # ...and the legacy file is left untouched
        self.assertEqual(json.loads((legacy / "surface-vaults.json").read_text()),
                         [str(legacy_vault)])

    def test_registry_drops_vanished_vaults(self):
        self.init_vault()
        rmtree(self.vault)
        self.assertEqual(promote.load_registry(), [])

    def test_corrupt_registry_is_empty_not_fatal(self):
        self.cfgdir.mkdir(parents=True)
        (self.cfgdir / "surface-vaults.json").write_text("{not json")
        self.assertEqual(promote.load_registry(), [])


# --- Vault resolution -----------------------------------------------------------
class TestFindVault(RailsTest):
    def test_explicit_flag_wins(self):
        self.init_vault()
        os.environ["SURFACE_VAULT"] = str(self.tmp / "nonexistent")
        self.assertEqual(promote.find_vault(str(self.vault)), self.vault.resolve())

    def test_env_beats_walkup(self):
        self.init_vault()
        os.environ["SURFACE_VAULT"] = str(self.vault)
        self.assertEqual(promote.find_vault(None), self.vault.resolve())

    def test_walkup_from_cwd(self):
        self.init_vault()
        sub = self.vault / "wiki" / "projects"
        os.chdir(sub)
        self.assertEqual(promote.find_vault(None), self.vault)

    def test_single_registered_vault_found_from_anywhere(self):
        self.init_vault()
        os.chdir(self.tmp)  # not inside the vault
        self.assertEqual(promote.find_vault(None), self.vault.resolve())

    def test_ambiguous_registry_exits(self):
        self.init_vault()
        code, _, _ = self.run_cli("init", "--vault", str(self.tmp / "vault2"))
        self.assertEqual(code, 0)
        os.chdir(self.tmp)
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                promote.find_vault(None)

    def test_no_vault_anywhere_exits(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                promote.find_vault(None)


# --- init scaffolding -----------------------------------------------------------
class TestInit(RailsTest):
    def test_scaffold_layout(self):
        self.init_vault()
        for rel in ("surface.config.json", "CLAUDE.md", "dashboard.html", "sources",
                    "wiki/index.md", "wiki/projects", "wiki/research", "wiki/themes",
                    "share/briefs", "share/digests", "share/packs", "share/_style",
                    "surfaces/_inbox"):
            self.assertTrue((self.vault / rel).exists(), rel)

    def test_init_is_idempotent_and_preserves_edits(self):
        self.init_vault()
        (self.vault / "CLAUDE.md").write_text("my edited schema\n")
        index = self.vault / "wiki" / "index.md"
        index.write_text("# my index\n")
        code, _, _ = self.run_cli("init", "--vault", str(self.vault))
        self.assertEqual(code, 0)
        self.assertEqual((self.vault / "CLAUDE.md").read_text(), "my edited schema\n")
        self.assertEqual(index.read_text(), "# my index\n")

    def test_author_stamped_into_config(self):
        v = self.init_vault(author="Ada Lovelace")
        self.assertEqual(v.cfg["author"], "Ada Lovelace")


# --- add: provenance, shield, dedup --------------------------------------------
class TestAdd(RailsTest):
    def test_add_writes_candidate_with_provenance(self):
        self.init_vault()
        code, out, _ = self.add("Test insight", body="the insight body")
        self.assertEqual(code, 0)
        files = self.inbox_files()
        self.assertEqual(len(files), 1)
        text = files[0].read_text()
        self.assertIn('sources: ["transcript://abc#1"]', text)
        self.assertIn("the insight body", text)
        rows = self.dispositions()
        self.assertEqual(rows[-1]["verdict"], "proposed")
        self.assertEqual(rows[-1]["source"], "transcript://abc#1")

    def test_source_is_required(self):
        self.init_vault()
        code, _, err = self.run_cli("add", "--vault", str(self.vault),
                                    "--title", "No provenance", stdin="body")
        self.assertNotEqual(code, 0)
        self.assertIn("--source", err)
        self.assertEqual(self.inbox_files(), [])

    def test_shielded_content_never_written(self):
        self.init_vault()
        code, out, _ = self.add("Secret", body="contains do-not-syndicate marker")
        self.assertEqual(code, 0)
        self.assertIn("shielded", out)
        self.assertEqual(self.inbox_files(), [])          # no file
        row = self.dispositions()[-1]
        self.assertEqual(row["verdict"], "shielded")
        self.assertNotIn("title", row)                    # opaque: no title stored
        self.assertNotIn("Secret", json.dumps(row))

    def test_shield_marker_spelled_with_spaces(self):
        self.init_vault()
        code, out, _ = self.add("Secret 2", body="please do not syndicate this")
        self.assertEqual(code, 0)
        self.assertIn("shielded", out)
        self.assertEqual(self.inbox_files(), [])

    def test_custom_shield_markers_from_config(self):
        self.init_vault()
        cfg_path = self.vault / "surface.config.json"
        cfg = json.loads(cfg_path.read_text())
        cfg["shield_markers"] = ["CONFIDENTIAL-ACME"]
        cfg_path.write_text(json.dumps(cfg))
        code, out, _ = self.add("Acme", body="stamped confidential-acme internally")
        self.assertEqual(code, 0)
        self.assertIn("shielded", out)

    def test_disposed_candidates_never_resurface(self):
        self.init_vault()
        _, out, _ = self.add("Dup me")
        cid = out.split()[1]
        code, _, _ = self.run_cli("dispose", "--vault", str(self.vault), cid, "dump")
        self.assertEqual(code, 0)
        self.assertEqual(self.inbox_files(), [])          # dump deleted the file
        code, out, _ = self.add("Dup me")                 # same origin+source+title
        self.assertEqual(code, 0)
        self.assertIn("skip", out)
        self.assertEqual(self.inbox_files(), [])          # remember-the-drop


# --- dispose / reconcile / append-only log --------------------------------------
class TestDisposeReconcile(RailsTest):
    def test_invalid_verdict_rejected(self):
        self.init_vault()
        code, _, err = self.run_cli("dispose", "--vault", str(self.vault), "xyz", "maybe")
        self.assertEqual(code, 1)
        self.assertIn("keep|act|dump", err)

    def test_park_marks_file_not_waiting(self):
        self.init_vault()
        _, out, _ = self.add("Parked idea")
        cid = out.split()[1]
        code, _, _ = self.run_cli("dispose", "--vault", str(self.vault), cid, "park")
        self.assertEqual(code, 0)
        text = self.inbox_files()[0].read_text()
        self.assertIn("status: parked", text)

    def test_log_is_append_only(self):
        self.init_vault()
        self.add("First")
        before = (self.vault / "surfaces" / "dispositions.jsonl").read_text()
        self.add("Second")
        after = (self.vault / "surfaces" / "dispositions.jsonl").read_text()
        self.assertTrue(after.startswith(before))         # prior rows untouched
        self.assertEqual(len(self.dispositions()), 2)

    def test_reconcile_honours_status_fields(self):
        self.init_vault()
        self.add("Keep me")
        self.add("Dump me", source="transcript://abc#2")
        self.add("Leave me", source="transcript://abc#3")
        keep_f, dump_f, _ = self.inbox_files()[0], None, None
        for f in self.inbox_files():
            if "dump-me" in f.name:
                dump_f = f
            if "keep-me" in f.name:
                keep_f = f
        keep_f.write_text(keep_f.read_text().replace("status: proposed", "status: keep"))
        dump_f.write_text(dump_f.read_text().replace("status: proposed", "status: dump"))
        code, out, _ = self.run_cli("reconcile", "--vault", str(self.vault))
        self.assertEqual(code, 0)
        self.assertIn("keep 1", out)
        self.assertIn("dump 1", out)
        self.assertIn("untriaged left in _inbox: 1", out)
        names = [f.name for f in self.inbox_files()]
        self.assertEqual(len(names), 2)                   # dump deleted, keep left to place
        self.assertFalse(any("dump-me" in n for n in names))
        verdicts = [r["verdict"] for r in self.dispositions()]
        self.assertIn("keep", verdicts)
        self.assertIn("dump", verdicts)


# --- annotate: advisory, never disposes -----------------------------------------
class TestAnnotate(RailsTest):
    def test_annotate_is_advisory(self):
        self.init_vault()
        _, out, _ = self.add("Judged idea")
        cid = out.split()[1]
        code, _, _ = self.run_cli("annotate", "--vault", str(self.vault), cid,
                                  "--verdict", "weak", "--note", "thin evidence",
                                  "--suggest", "dump")
        self.assertEqual(code, 0)
        text = self.inbox_files()[0].read_text()
        self.assertIn("critic_verdict: weak", text)
        self.assertIn("critic_suggest: dump", text)
        self.assertIn("status: proposed", text)           # critic never disposes
        self.assertEqual(len(self.inbox_files()), 1)      # file still present

    def test_annotate_unknown_target_fails(self):
        self.init_vault()
        code, _, err = self.run_cli("annotate", "--vault", str(self.vault),
                                    "nope", "--verdict", "weak")
        self.assertEqual(code, 1)
        self.assertIn("no candidate", err)


# --- publish: the only path into a commons --------------------------------------
class TestPublish(RailsTest):
    def make_commons(self, audience="team", name="teamspace"):
        croot = self.tmp / f"commons-{name}"
        croot.mkdir()
        code, _, err = self.run_cli("commons", "--vault", str(self.vault),
                                    "add", name, "--path", str(croot),
                                    "--audience", audience)
        self.assertEqual(code, 0, err)
        return croot

    def make_brief(self, sensitivity="share-now", body="the brief body\n"):
        f = self.vault / "share" / "briefs" / "my-brief.md"
        fm = f"---\ntitle: \"My brief\"\nsensitivity: {sensitivity}\n---\n" \
            if sensitivity is not None else "---\ntitle: \"My brief\"\n---\n"
        f.write_text(fm + body)
        return f

    def test_happy_path_team_commons(self):
        self.init_vault()
        croot = self.make_commons()
        brief = self.make_brief(sensitivity="team")
        code, out, _ = self.run_cli("publish", "--vault", str(self.vault), str(brief))
        self.assertEqual(code, 0)
        dest = croot / "test-user" / "briefs" / "my-brief.md"
        self.assertTrue(dest.exists())
        self.assertEqual(self.dispositions()[-1]["verdict"], "published")

    def test_hold_tier_refused(self):
        self.init_vault()
        self.make_commons()
        brief = self.make_brief(sensitivity="hold")
        code, _, err = self.run_cli("publish", "--vault", str(self.vault), str(brief))
        self.assertEqual(code, 2)
        self.assertIn("REFUSED", err)
        self.assertEqual(list((self.tmp / "commons-teamspace").rglob("*.md")), [])

    def test_missing_sensitivity_is_refusal_not_default(self):
        self.init_vault()
        self.make_commons()
        brief = self.make_brief(sensitivity=None)
        code, _, err = self.run_cli("publish", "--vault", str(self.vault), str(brief))
        self.assertEqual(code, 2)
        self.assertIn("REFUSED", err)

    def test_team_tier_refused_in_public_commons(self):
        self.init_vault()
        self.make_commons(audience="public", name="pub")
        brief = self.make_brief(sensitivity="team")
        code, _, err = self.run_cli("publish", "--vault", str(self.vault), str(brief))
        self.assertEqual(code, 2)
        self.assertIn("REFUSED", err)

    def test_shielded_content_refused_even_when_tier_ok(self):
        self.init_vault()
        self.make_commons()
        brief = self.make_brief(sensitivity="team",
                                body="fine intro\nbut do-not-syndicate lurks here\n")
        code, _, err = self.run_cli("publish", "--vault", str(self.vault), str(brief))
        self.assertEqual(code, 2)
        self.assertIn("shielded", err)

    def test_no_commons_configured_fails_cleanly(self):
        self.init_vault()
        brief = self.make_brief()
        code, _, err = self.run_cli("publish", "--vault", str(self.vault), str(brief))
        self.assertEqual(code, 1)
        self.assertIn("no commons", err)

    def test_publish_requires_author(self):
        self.init_vault(author="")
        self.make_commons()
        brief = self.make_brief(sensitivity="team")
        code, _, err = self.run_cli("publish", "--vault", str(self.vault), str(brief))
        self.assertEqual(code, 1)
        self.assertIn("author", err)

    def test_commons_remove_never_touches_published(self):
        self.init_vault()
        croot = self.make_commons()
        brief = self.make_brief(sensitivity="team")
        self.run_cli("publish", "--vault", str(self.vault), str(brief))
        code, _, _ = self.run_cli("commons", "--vault", str(self.vault),
                                  "remove", "teamspace")
        self.assertEqual(code, 0)
        self.assertTrue((croot / "test-user" / "briefs" / "my-brief.md").exists())
        self.assertEqual(promote.Vault(self.vault).commons, [])


# --- helpers --------------------------------------------------------------------
class TestHelpers(RailsTest):
    def test_slug(self):
        self.assertEqual(promote.slug("Hello, World!"), "hello-world")
        self.assertEqual(promote.slug(""), "untitled")
        self.assertEqual(promote.slug("x" * 100), "x" * 50)

    def test_parse_frontmatter_roundtrip(self):
        self.init_vault()
        self.add("A titled thing")
        fm = promote.parse_frontmatter(self.inbox_files()[0])
        self.assertEqual(fm["title"], "A titled thing")
        self.assertEqual(fm["status"], "proposed")
        self.assertTrue(fm["candidate_id"])

    def test_dashboard_regenerates(self):
        self.init_vault()
        dash = self.vault / "dashboard.html"
        dash.unlink()
        code, _, _ = self.run_cli("dashboard", "--vault", str(self.vault))
        self.assertEqual(code, 0)
        self.assertTrue(dash.exists())
        self.assertIn("surface", dash.read_text())


if __name__ == "__main__":
    unittest.main()
