"""The MCP server registers every tool, and the npm copy has not drifted."""

import asyncio
import filecmp
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import server
except ImportError:  # mcp is not installed
    server = None


class ServerTests(unittest.TestCase):
    @unittest.skipIf(server is None, "mcp is not installed")
    def test_every_tool_is_registered(self):
        tools = {t.name for t in asyncio.run(server.mcp.list_tools())}
        self.assertEqual(
            tools,
            {"alert_notify", "notify", "ping", "doctor", "agent_done", "agent_working", "agent_status",
             "agent_question", "agent_approval", "agent_error"},
        )

    @unittest.skipIf(server is None, "mcp is not installed")
    def test_tool_calls_land_on_the_status_board(self):
        import tempfile
        from unittest.mock import MagicMock, patch

        import status

        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {"PINTUMCP_HOME": home}), \
                patch.object(server, "deliver_event", MagicMock(return_value={})), \
                patch.object(server.completion_dispatcher, "queue_completion", MagicMock(return_value={})):
            server.agent_working("Refactoring", "API", "Agent 1")
            server.agent_approval("Deploy?", "API", "Agent 2")
            server.agent_done("Built web", "Web", "Agent 1")
            server.agent_status("Still refactoring", "API", "Agent 1")
            rows = {(r["project"], r["agent"]): (r["state"], r["message"]) for r in status.snapshot()}

        self.assertEqual(rows[("API", "Agent 1")], ("working", "Still refactoring"))
        self.assertEqual(rows[("API", "Agent 2")], ("approval", "Deploy?"))
        self.assertEqual(rows[("Web", "Agent 1")], ("done", "Built web"))

    def test_npm_copy_matches_root(self):
        for name in ("server.py", "notifier.py", "events.py", "config.py", "status.py", "tray.py", "hook.py"):
            self.assertTrue(
                filecmp.cmp(ROOT / name, ROOT / "npm/python" / name, shallow=False),
                f"npm/python/{name} drifted; run scripts/sync.sh",
            )
        for icon in [ROOT / "assets/pintumcp-icon.png", *(ROOT / "assets/icons").glob("*.png")]:
            copy = ROOT / "npm/python/assets" / icon.relative_to(ROOT / "assets")
            self.assertTrue(
                copy.is_file() and filecmp.cmp(icon, copy, shallow=False),
                f"{copy.name} drifted; run scripts/sync.sh",
            )


if __name__ == "__main__":
    unittest.main()
