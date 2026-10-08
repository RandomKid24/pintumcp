"""Local agent status board: one small JSON file per agent under ~/.pintumcp/agents.

The MCP server writes (best effort, never raises); the optional menu-bar app reads.
No daemon, socket or account: if nothing is reading, the files are just ignored.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

URGENCY = {"approval": 0, "error": 1, "question": 2, "working": 3, "done": 4, "idle": 5}
IDLE_AFTER = 30 * 60      # a finished agent is "idle" after this many seconds
STALE_AFTER = 10 * 60     # a working agent that went quiet this long may be stuck
FORGET_AFTER = 12 * 3600  # drop agents that have not reported for this long


def root() -> Path:
    """Per-user data folder. PINTUMCP_HOME overrides it (tests); temp is the fallback."""
    base = Path(os.environ.get("PINTUMCP_HOME") or Path.home() / ".pintumcp")
    try:
        base.mkdir(mode=0o700, parents=True, exist_ok=True)
        return base
    except OSError:
        uid = os.getuid() if hasattr(os, "getuid") else "user"
        fallback = Path(tempfile.gettempdir()) / f"pintumcp-{uid}"
        fallback.mkdir(mode=0o700, parents=True, exist_ok=True)
        return fallback


def _dir() -> Path:
    path = root() / "agents"
    path.mkdir(mode=0o700, exist_ok=True)
    return path


def identity(project: str | None, agent: str | None) -> tuple[str, str]:
    """Labels if given; otherwise one anonymous row per MCP server process (= per session)."""
    if project or agent:
        return (project or "", agent or "Agent")
    return ("", f"Session {os.getpid() % 10000}")


def update(state: str, message: str = "", project: str | None = None,
           agent: str | None = None, app: str | None = None, now: float | None = None) -> bool:
    """Record an agent's latest state. Returns False (never raises) if it could not."""
    try:
        project, agent = identity(project, agent)
        now = time.time() if now is None else now
        path = _dir() / f"{hashlib.sha1(f'{project}|{agent}'.encode()).hexdigest()[:12]}.json"
        since = now
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
            if old.get("state") == state:
                since = old.get("since", now)
            app = app or old.get("app")
        except (OSError, ValueError):
            pass
        entry = {"project": project, "agent": agent, "state": state,
                 "message": " ".join(str(message).split())[:200], "since": since,
                 "updated": now, "app": app}
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(entry), encoding="utf-8")
        os.replace(tmp, path)  # atomic: the reader never sees half a file
        return True
    except OSError:
        return False


def snapshot(now: float | None = None) -> list[dict]:
    """All known agents, most urgent first, with derived state, ages and a stale flag."""
    now = time.time() if now is None else now
    items = []
    try:
        files = list(_dir().glob("*.json"))
    except OSError:
        return []
    for path in files:
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            age = now - item["updated"]
        except (OSError, ValueError, KeyError):
            continue
        if age > FORGET_AFTER:
            path.unlink(missing_ok=True)
            continue
        item["age"] = age
        item["in_state"] = now - item.get("since", item["updated"])
        item["stale"] = item["state"] == "working" and age > STALE_AFTER
        if item["state"] == "done" and age > IDLE_AFTER:
            item["state"] = "idle"
        items.append(item)
    items.sort(key=lambda i: (URGENCY.get(i["state"], 9), i["age"]))
    return items


def clear_finished() -> None:
    for item in snapshot():
        if item["state"] in ("done", "idle"):
            (_dir() / f"{hashlib.sha1(f'{item['project']}|{item['agent']}'.encode()).hexdigest()[:12]}.json").unlink(missing_ok=True)


def format_age(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 45:
        return "just now"
    minutes = seconds // 60 or 1
    return f"{minutes}m" if minutes < 60 else f"{minutes // 60}h {minutes % 60}m"


STATE_TEXT = {"working": "Working", "question": "Needs your input", "approval": "Needs approval",
              "error": "Error", "done": "Done", "idle": "Idle"}


def describe(item: dict) -> dict:
    """What the menu shows for one agent: name, one-line status, message, Pintu face."""
    name = " · ".join(p for p in (item["project"], item["agent"]) if p)
    state = item["state"]
    text = STATE_TEXT.get(state, state)
    when = format_age(item["in_state"] if state == "working" else item["age"])
    status = f"{text}, {when}" if when != "just now" else text
    if item["stale"]:
        status += " (quiet, maybe stuck?)"
    return {"name": name, "status": status, "message": item["message"][:70], "state": state}
