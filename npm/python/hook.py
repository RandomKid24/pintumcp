"""Claude Code hook: report this session's state to the local status board.

Usage (set up by `pintumcp hooks install`):  python hook.py <UserPromptSubmit|Notification|PostToolUse|Stop|SessionEnd>
Reads the hook JSON on stdin. Best effort: it always exits 0 so it can never block Claude.
"""

import json
import os
import sys
from pathlib import Path

import status


def classify(event: str, payload: dict):
    """(state, message) for a Claude Code hook event, or None to ignore it."""
    message = str(payload.get("message") or "")
    if event == "UserPromptSubmit":
        prompt = " ".join(str(payload.get("prompt") or "").split())[:80]
        return "working", f"Working: {prompt}" if prompt else "Working on your request"
    if event == "Notification":
        needs_permission = "permission" in message.lower()
        return ("approval" if needs_permission else "question"), message or "Needs you"
    if event == "Stop":
        return "done", "Finished responding"
    if event == "PostToolUse":  # a tool ran, so any pending permission/question was answered
        return "working", "Working on your request"
    if event == "SessionEnd":
        return "gone", ""
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            payload = {}
    except ValueError:
        payload = {}
    result = classify(sys.argv[1] if len(sys.argv) > 1 else "", payload)
    if result:
        project = Path(payload.get("cwd") or os.getcwd()).name
        agent = "Claude " + str(payload.get("session_id") or "")[:4]
        if result[0] == "gone":
            return status.remove(project, agent.strip())
        status.update(result[0], result[1], project, agent.strip(), app=os.environ.get("__CFBundleIdentifier"))
        if result[0] in ("done", "approval", "question"):
            import events
            events.deliver_event(result[0], result[1], 80, project, agent.strip())


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hook must never break the agent
        pass
    sys.exit(0)
