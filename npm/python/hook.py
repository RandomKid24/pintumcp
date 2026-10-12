"""Claude Code hook: report this session's state to the local status board.

Usage (set up by `pintumcp hooks install`):
    python hook.py <SessionStart|UserPromptSubmit|Notification|PostToolUse|Stop|StopFailure|SessionEnd>
Reads the hook JSON on stdin. Best effort: it always exits 0 so it can never block Claude.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import status

try:  # optional: one fast, cross-platform call beats `/proc`/`ps`/`wmic` (especially on Windows)
    import psutil
except ImportError:
    psutil = None

# Notification `notification_type`s that mean the user has to act, vs. plain information.
_APPROVAL_TYPES = {"permission_prompt"}
_QUESTION_TYPES = {"idle_prompt", "agent_needs_input", "elicitation_dialog",
                   "elicitation_url_dialog", "elicitation_response"}


def _windows_proc(pid: int):
    """(parent pid, command line) on Windows, where there is no /proc and no ps."""
    try:  # wmic ships with Windows 10; deprecated but usually still present
        out = subprocess.run(
            ["wmic", "process", "where", f"processid={pid}", "get", "parentprocessid,commandline", "/format:list"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        ppid, command = None, ""
        for line in out.splitlines():
            key, _, value = line.partition("=")
            key = key.strip().lower()
            if key == "parentprocessid" and value.strip():
                ppid = int(value.strip())
            elif key == "commandline" and value.strip():
                command = value.strip()
        if ppid:
            return ppid, command
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    try:  # fall back to PowerShell CIM (wmic is gone on some Windows 11 machines)
        script = (f'Get-CimInstance Win32_Process -Filter "ProcessId={int(pid)}" | '
                  "Select-Object ParentProcessId,CommandLine | ConvertTo-Json -Compress")
        out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                             capture_output=True, text=True, timeout=8).stdout
        data = json.loads(out)
        if data.get("ParentProcessId"):
            return int(data["ParentProcessId"]), data.get("CommandLine") or ""
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        pass
    return None


def _proc(pid: int):
    """(parent pid, command line) of a process, or None."""
    try:
        if psutil is not None:
            proc = psutil.Process(int(pid))
            return proc.ppid(), " ".join(proc.cmdline())
        if sys.platform.startswith("linux"):
            with open(f"/proc/{pid}/stat") as f:
                ppid = int(f.read().rsplit(")", 1)[1].split()[1])
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                return ppid, f.read().replace(b"\0", b" ").decode(errors="ignore")
        if os.name == "nt":
            return _windows_proc(pid)
        out = subprocess.run(["ps", "-o", "ppid=,command=", "-p", str(pid)], capture_output=True, text=True, timeout=2).stdout.strip()
        ppid, _, command = out.partition(" ")
        return int(ppid), command
    except Exception:
        return None


def owner_pid():
    """The Claude Code process that ran this hook (the hook itself exits at once), or None if not found."""
    pid = os.getppid()
    for _ in range(6):
        info = _proc(pid)
        if not info or pid <= 1:
            return None
        if "claude" in info[1].lower():
            return pid
        pid = info[0]
    return None


def describe_tool(payload: dict) -> str:
    """What the agent just did, in a few words (shown on its row)."""
    name, args = str(payload.get("tool_name") or ""), payload.get("tool_input") or {}
    if not isinstance(args, dict):
        return ""
    target = os.path.basename(str(args.get("file_path") or args.get("notebook_path") or args.get("path") or ""))
    text = " ".join(str(args.get("command") or args.get("pattern") or args.get("query") or args.get("url") or "").split())[:48]
    if name in ("Edit", "MultiEdit", "Write", "NotebookEdit"):
        return f"Editing {target}" if target else "Editing files"
    if name == "Read":
        return f"Reading {target}" if target else "Reading files"
    if name == "Bash":
        return f"Running: {text}" if text else "Running a command"
    if name in ("Grep", "Glob"):
        return f"Searching: {text}" if text else "Searching the code"
    if name in ("WebFetch", "WebSearch"):
        return f"Browsing: {text}" if text else "Browsing the web"
    if name in ("Task", "Agent"):
        return "Delegating to a sub-agent"
    if name == "TodoWrite":
        return "Planning the next steps"
    if name.startswith("mcp__"):  # mcp__server__tool -> "server: tool"
        parts = name.split("__")
        if len(parts) >= 3 and parts[2]:
            return f"{parts[1]}: {parts[2]}"
        return name.replace("mcp__", "").replace("__", " ")
    return name if name else ""


def classify(event: str, payload: dict):
    """(state, message) for a Claude Code hook event, or None to ignore it."""
    message = str(payload.get("message") or "")
    if event == "SessionStart":
        if str(payload.get("source") or "") == "compact":
            return None  # a compaction is mid-session; don't reset a row that is busy
        return "idle", "Ready"
    if event == "UserPromptSubmit":
        prompt = " ".join(str(payload.get("prompt") or "").split())[:80]
        return "working", f"Working: {prompt}" if prompt else "Working on your request"
    if event == "Notification":
        kind = str(payload.get("notification_type") or "").lower()
        if kind in _APPROVAL_TYPES:
            return "approval", message or "Needs approval"
        if kind in _QUESTION_TYPES:
            return "question", message or "Needs you"
        if kind:
            return None  # auth_success, agent_completed, quota_* …: informational, nothing to do
        # Older Claude Code sends no notification_type: fall back to the wording.
        needs_permission = "permission" in message.lower()
        return ("approval" if needs_permission else "question"), message or "Needs you"
    if event == "Stop":
        return "done", "Finished responding"
    if event == "StopFailure":  # the turn ended due to an API error, not a normal stop
        detail = " ".join(str(payload.get("last_assistant_message") or payload.get("error_details")
                              or payload.get("error") or "").split())[:120]
        return "error", detail or "The turn failed"
    if event == "PostToolUse":  # a tool ran, so any pending permission/question was answered
        return "working", describe_tool(payload) or "Working on your request"
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
        if result[0] in ("done", "approval", "question", "error"):
            import events
            events.deliver(result[0], result[1], project, agent.strip())


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hook must never break the agent
        pass
    sys.exit(0)
