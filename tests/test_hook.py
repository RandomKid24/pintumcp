"""Claude Code hook classification."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import hook  # noqa: E402


class HookTests(unittest.TestCase):
    def test_permission_notifications_are_approvals_others_are_questions(self):
        self.assertEqual(hook.classify("Notification", {"message": "Claude needs your permission to use Bash"})[0], "approval")
        self.assertEqual(hook.classify("Notification", {"message": "Claude is waiting for your input"})[0], "question")

    def test_prompt_and_stop_events(self):
        self.assertEqual(hook.classify("UserPromptSubmit", {"prompt": "fix   the\nbug"}), ("working", "Working: fix the bug"))
        self.assertEqual(hook.classify("Stop", {})[0], "done")

    def test_unknown_events_are_ignored(self):
        self.assertIsNone(hook.classify("PreToolUse", {}))


if __name__ == "__main__":
    unittest.main()
