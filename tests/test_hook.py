"""Claude Code hook classification."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The copy that actually ships is npm/python; root/*.py has drifted stale, so test the real one.
sys.path.insert(0, str(ROOT / "npm" / "python"))

import hook  # noqa: E402


class HookTests(unittest.TestCase):
    def test_permission_notifications_are_approvals_others_are_questions(self):
        # Old Claude Code sends no notification_type: fall back to the message wording.
        self.assertEqual(hook.classify("Notification", {"message": "Claude needs your permission to use Bash"})[0], "approval")
        self.assertEqual(hook.classify("Notification", {"message": "Claude is waiting for your input"})[0], "question")

    def test_notification_type_is_preferred_over_the_message(self):
        self.assertEqual(hook.classify("Notification", {"notification_type": "permission_prompt", "message": "Allow?"})[0], "approval")
        self.assertEqual(hook.classify("Notification", {"notification_type": "idle_prompt", "message": "Waiting"})[0], "question")
        # A "permission" word with an idle type must not be mistaken for an approval.
        self.assertEqual(hook.classify("Notification", {"notification_type": "idle_prompt", "message": "no permission needed"})[0], "question")

    def test_informational_notifications_are_ignored(self):
        for kind in ("auth_success", "agent_completed", "quota_auto_resume_fired"):
            self.assertIsNone(hook.classify("Notification", {"notification_type": kind, "message": "fyi"}))

    def test_prompt_and_stop_events(self):
        self.assertEqual(hook.classify("UserPromptSubmit", {"prompt": "fix   the\nbug"}), ("working", "Working: fix the bug"))
        self.assertEqual(hook.classify("Stop", {})[0], "done")

    def test_session_start_shows_the_row_but_compaction_does_not(self):
        self.assertEqual(hook.classify("SessionStart", {"source": "startup"}), ("idle", "Ready"))
        self.assertIsNone(hook.classify("SessionStart", {"source": "compact"}))

    def test_stop_failure_is_an_error(self):
        state, message = hook.classify("StopFailure", {"error": "rate_limit", "last_assistant_message": "API Error: Rate limit reached"})
        self.assertEqual(state, "error")
        self.assertEqual(message, "API Error: Rate limit reached")
        self.assertEqual(hook.classify("StopFailure", {})[0], "error")

    def test_post_tool_use_reports_what_happened(self):
        self.assertEqual(hook.classify("PostToolUse", {"tool_name": "Edit", "tool_input": {"file_path": "/a/b/foo.py"}}),
                         ("working", "Editing foo.py"))

    def test_mcp_tools_read_as_server_colon_tool(self):
        self.assertEqual(hook.describe_tool({"tool_name": "mcp__github__search_repositories", "tool_input": {}}),
                         "github: search_repositories")

    def test_unknown_events_are_ignored(self):
        self.assertIsNone(hook.classify("PreToolUse", {}))


if __name__ == "__main__":
    unittest.main()
