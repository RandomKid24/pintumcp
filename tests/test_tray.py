"""Menu-bar logic that does not need a screen."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tray  # noqa: E402


class TrayTests(unittest.TestCase):
    def test_bar_shows_the_most_urgent_agent_and_how_many_need_you(self):
        items = [{"state": "approval"}, {"state": "error"}, {"state": "working"}, {"state": "done"}]
        self.assertEqual(tray.bar_state(items), ("approval", "2"))

    def test_bar_is_quiet_when_nobody_needs_you(self):
        self.assertEqual(tray.bar_state([{"state": "working"}, {"state": "done"}]), ("working", ""))
        self.assertEqual(tray.bar_state([]), ("empty", ""))

    def test_panel_payload_has_agents_and_the_today_card(self):
        item = {"project": "API", "agent": "Agent 1", "state": "working", "message": "m", "in_state": 5,
                "age": 1, "stale": False, "updated": 0}
        data = tray.payload([item], now=100)
        self.assertEqual(data["agents"][0]["key"], "API|Agent 1")
        self.assertEqual(data["agents"][0]["name"], "API · Agent 1")
        self.assertEqual(set(data["today"]), {"done", "errors", "trend", "longest"})

    def test_every_state_has_a_face(self):
        for state in ("working", "question", "approval", "error", "done", "idle", "empty"):
            self.assertTrue(Path(tray.icon_for(state)).name == f"{state}.png")


if __name__ == "__main__":
    unittest.main()
