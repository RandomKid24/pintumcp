"""Tests for the local agent status board."""

import os
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import status  # noqa: E402


class StatusTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patcher = unittest.mock.patch.dict(os.environ, {"PINTUMCP_HOME": tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_rows_sort_by_urgency_then_recency(self):
        status.update("done", "d", "API", "A", now=1000)
        status.update("working", "w", "API", "B", now=1000)
        status.update("approval", "a", "API", "C", now=1000)
        status.update("error", "e", "API", "D", now=1000)
        status.update("question", "q", "API", "E", now=1000)
        order = [i["state"] for i in status.snapshot(now=1010)]
        self.assertEqual(order, ["approval", "error", "question", "working", "done"])

    def test_time_in_state_resets_only_when_the_state_changes(self):
        status.update("working", "start", "API", "A", now=1000)
        status.update("working", "still going", "API", "A", now=1300)
        row = status.snapshot(now=1360)[0]
        self.assertEqual((row["in_state"], row["age"], row["message"]), (360, 60, "still going"))
        status.update("done", "ok", "API", "A", now=1400)
        self.assertEqual(status.snapshot(now=1400)[0]["in_state"], 0)

    def test_quiet_working_agents_are_flagged_and_old_done_agents_go_idle(self):
        status.update("working", "w", "API", "A", now=0)
        status.update("done", "d", "API", "B", now=0)
        rows = {r["agent"]: r for r in status.snapshot(now=status.STALE_AFTER + 1)}
        self.assertTrue(rows["A"]["stale"])
        self.assertEqual(rows["B"]["state"], "done")
        rows = {r["agent"]: r for r in status.snapshot(now=status.IDLE_AFTER + 1)}
        self.assertEqual(rows["B"]["state"], "idle")

    def test_agents_that_stopped_reporting_are_forgotten(self):
        status.update("done", "d", "API", "A", now=0)
        self.assertEqual(status.snapshot(now=status.FORGET_AFTER + 1), [])
        self.assertEqual(list(status._dir().glob("*.json")), [])

    def test_unlabelled_agents_get_one_row_per_session(self):
        status.update("working", "x")
        status.update("question", "y")
        rows = status.snapshot()
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["agent"].startswith("Session "))

    def test_describe_reads_like_a_sentence(self):
        status.update("working", "Refactoring auth module", "API", "Agent 1", now=0)
        shown = status.describe(status.snapshot(now=240)[0])
        self.assertEqual(shown["name"], "API · Agent 1")
        self.assertEqual(shown["status"], "Working, 4m")
        self.assertEqual(shown["state"], "working")

    def test_update_never_raises_on_unwritable_storage(self):
        with unittest.mock.patch.object(status, "_dir", side_effect=OSError("read-only")):
            self.assertFalse(status.update("done", "x", "API", "A"))
            self.assertEqual(status.snapshot(), [])

    def test_clear_finished_keeps_active_agents(self):
        status.update("done", "d", "API", "A")
        status.update("working", "w", "API", "B")
        status.clear_finished()
        self.assertEqual([r["agent"] for r in status.snapshot()], ["B"])


if __name__ == "__main__":
    import unittest.mock  # noqa: F401
    unittest.main()
