"""Claude Code hook: report this session's state to the local status board.

Usage (set up by `pintumcp hooks install`):  python hook.py <UserPromptSubmit|Notification|PostToolUse|Stop|SessionEnd>
Reads the hook JSON on stdin. Best effort: it always exits 0 so it can never block Claude.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import status


def _proc(pid: int):
    """(parent pid, command line) of a process, or None."""
    try:
        if sys.platform.startswith("linux"):
            with open(f"/proc/{pid}/stat") as f:
                ppid = int(f.read().rsplit(")", 1)[1].split()[1])
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                return ppid, f.read().replace(b"\0", b" ").decode(errors="ignore")
        out = subprocess.run(["ps", "-o", "ppid=,command=", "-p", str(pid)], capture_output=True, text=True, timeout=2).stdout.strip()
        ppid, _, command = out.partition(" ")
        return int(ppid), command
    except Exception:
        return None


def owner_pid():
    """The Claude Code process that ran this hook (the hook itself exits at once), or None if not found."""
    if os.name == "nt":
        return None
    pid = os.getppid()
    for _ in range(6):
        info = _proc(pid)
        if not info or pid <= 1:
            return None
        if "claude" in info[1].lower():
            return pid
        pid = info[0]
    return None


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
        status.update(result[0], result[1], project, agent.strip(), app=os.environ.get("__CFBundleIdentifier"), pid=owner_pid)
        if result[0] in ("done", "approval", "question"):
            import events
            events.deliver_event(result[0], result[1], 80, project, agent.strip())


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hook must never break the agent
        pass
    sys.exit(0)
