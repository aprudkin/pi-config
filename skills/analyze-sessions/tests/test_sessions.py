"""Regression tests using only temporary, synthetic session metadata."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import sessions as S  # noqa: E402
import cost  # noqa: E402
import list_sessions  # noqa: E402
import prompts  # noqa: E402
import show_session  # noqa: E402
import search  # noqa: E402


class SessionFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old_root = S.SESSIONS_ROOT
        S.SESSIONS_ROOT = self.root
        self.ids = {
            "one": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "two": "aaaaaaaa-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "three": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        }
        self.top("one", "/work/project", "2026-01-01T00:00:00Z")
        self.top("two", "/work/project-extra", "2026-01-02T00:00:00Z")
        self.top("three", "/other", "2026-01-03T00:00:00Z")
        self.sub("one", "dddddddd-dddd-dddd-dddd-dddddddddddd", "/work/project", "2026-01-04T00:00:00Z")

    def tearDown(self):
        S.SESSIONS_ROOT = self.old_root
        self.temp.cleanup()

    def top(self, name, cwd, timestamp):
        path = self.root / "encoded" / f"{name}.jsonl"
        self._write(path, self.ids[name], cwd, timestamp)

    def sub(self, parent, ident, cwd, timestamp):
        path = self.root / "encoded" / f"0_{self.ids[parent]}" / "child" / "run-1" / "x.jsonl"
        self._write(path, ident, cwd, timestamp)

    @staticmethod
    def _write(path, ident, cwd, timestamp):
        path.parent.mkdir(parents=True, exist_ok=True)
        # Include deliberately sensitive-looking text: metadata listing must not emit it.
        path.write_text(json.dumps({"type": "session", "id": ident, "cwd": cwd, "timestamp": timestamp}) + "\n" +
                        json.dumps({"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": "SECRET_PROMPT"}]}}) + "\n")

    def filters(self, **kwargs):
        f = S.Filters(include_subagents=False)
        for key, value in kwargs.items():
            setattr(f, key, value)
        return f

    def invoke(self, module, argv):
        old_argv = sys.argv
        stdout, stderr = io.StringIO(), io.StringIO()
        try:
            sys.argv = [module.__file__] + argv
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    code = module.main()
                except SystemExit as e:
                    code = int(e.code)
        finally:
            sys.argv = old_argv
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cwd_exact_is_literal_and_substring_is_preserved(self):
        self.assertEqual([s.id for s in S.load_summaries(self.filters(cwd_substrs=["project"]))],
                         [self.ids["two"], self.ids["one"]])
        self.assertEqual([s.id for s in S.load_summaries(self.filters(cwd_exacts=["/work/project"]))],
                         [self.ids["one"]])

    def test_repeated_cwd_exact_values_are_or(self):
        got = S.load_summaries(self.filters(cwd_exacts=["/work/project", "/other"]))
        self.assertEqual({s.id for s in got}, {self.ids["one"], self.ids["three"]})

    def test_date_bounds_exclude_sessions_without_timestamps(self):
        unknown_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
        self._write(self.root / "encoded" / "unknown.jsonl", unknown_id, "/work/project", None)
        got = S.load_summaries(self.filters(since=datetime(2025, 1, 1, tzinfo=timezone.utc)))
        self.assertNotIn(unknown_id, {s.id for s in got})

    def test_prefix_collision_rejected_but_full_id_selects(self):
        with self.assertRaisesRegex(S.SessionSelectionError, self.ids["one"]) as caught:
            S.load_summaries(self.filters(session_id="aaaaaaaa"))
        self.assertIn(self.ids["two"], str(caught.exception))
        got = S.load_summaries(self.filters(session_id=self.ids["one"]))
        self.assertEqual([s.id for s in got], [self.ids["one"]])

    def test_ambiguity_is_checked_before_limit(self):
        with self.assertRaises(S.SessionSelectionError):
            S.load_summaries(self.filters(session_id="aaaaaaaa", limit=1))

    def test_top_level_and_subagent_filtering(self):
        top = S.load_summaries(self.filters())
        both = S.load_summaries(self.filters(include_subagents=True))
        self.assertEqual(len(top), 3)
        self.assertEqual(len(both), 4)
        child = next(s for s in both if s.is_subagent)
        self.assertEqual(child.parent_session_id, self.ids["one"])

    def test_list_json_schema_contains_no_content(self):
        code, out, err = self.invoke(list_sessions, ["--cwd-exact", "/work/project", "--json"])
        self.assertEqual((code, err), (0, ""))
        rows = json.loads(out)
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]), {"id", "cwd", "started_at", "is_subagent", "parent_session_id", "path"})
        self.assertEqual(rows[0]["id"], self.ids["one"])
        self.assertNotIn("SECRET_PROMPT", out)

    def test_cli_selector_exit_codes_and_diagnostics(self):
        consumers = (
            (cost, []),
            (list_sessions, []),
            (prompts, []),
            (show_session, []),
            (search, ["x"]),
        )
        for module, prefix_args in consumers:
            code, _, err = self.invoke(module, prefix_args + ["--session", "aaaaaaaa"])
            self.assertEqual(code, 2)
            self.assertIn("ambiguous", err)
            self.assertIn(self.ids["one"], err)

            code, _, err = self.invoke(module, prefix_args + ["--session", "missing"])
            self.assertEqual(code, 2)
            self.assertIn("No session matches", err)

    def test_limit_must_be_positive(self):
        for value in ("0", "-1"):
            code, _, err = self.invoke(list_sessions, ["--limit", value])
            self.assertEqual(code, 2)
            self.assertIn("must be at least 1", err)

    def test_human_outputs_use_full_ids(self):
        commands = (
            (cost, ["--session", self.ids["one"], "--by", "session"]),
            (list_sessions, ["--session", self.ids["one"]]),
            (prompts, ["--session", self.ids["one"]]),
            (show_session, ["--session", self.ids["one"], "--max-thinking", "-1"]),
        )
        for module, argv in commands:
            code, out, err = self.invoke(module, argv)
            self.assertEqual(code, 0, err)
            self.assertIn(self.ids["one"], out)

    def test_search_drill_command_uses_full_id(self):
        s = S.load_summaries(self.filters(session_id=self.ids["one"]))[0]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            search._print_session_hits(s, [])
        self.assertIn(f"--session {self.ids['one']}", out.getvalue())


if __name__ == "__main__":
    unittest.main()
