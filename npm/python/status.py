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
FORGET_NEEDS_AFTER = 2 * 3600   # an unanswered approval/question this old was abandoned
FORGET_WORKING_AFTER = 30 * 60  # a "working" agent silent this long is a dead session, not a busy one


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


HISTORY_MAX = 512 * 1024  # bytes; the log is trimmed to its newest half past this


def _path(project: str, agent: str) -> Path:
    return _dir() / (hashlib.sha1((project + "|" + agent).encode()).hexdigest()[:12] + ".json")


def _log_transition(entry: dict) -> None:
    """Append a state change to history.jsonl (used for the Today card). Best effort."""
    path = root() / "history.jsonl"
    line = json.dumps({k: entry[k] for k in ("updated", "project", "agent", "state")}) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
    if path.stat().st_size > HISTORY_MAX:
        lines = path.read_text(encoding="utf-8").splitlines(True)
        path.write_text("".join(lines[len(lines) // 2:]), encoding="utf-8")


def update(state: str, message: str = "", project: str | None = None,
           agent: str | None = None, app: str | None = None, now: float | None = None) -> bool:
    """Record an agent's latest state. Returns False (never raises) if it could not."""
    try:
        project, agent = identity(project, agent)
        now = time.time() if now is None else now
        path = _path(project, agent)
        since = now
        changed = True
        took = None  # how long the last piece of work took (set when "working" ends)
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
            if old.get("state") == state:
                since = old.get("since", now)
                changed = False
            if old.get("state") == "working" and state != "working":
                took = now - old.get("since", now)
            elif state != "working":
                took = old.get("took")
            app = app or old.get("app")
        except (OSError, ValueError):
            pass
        entry = {"project": project, "agent": agent, "state": state,
                 "message": " ".join(str(message).split())[:200], "since": since,
                 "updated": now, "app": app, "took": took}
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(entry), encoding="utf-8")
        os.replace(tmp, path)  # atomic: the reader never sees half a file
        if changed:
            _log_transition(entry)
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
        if age > FORGET_AFTER or (item.get("state") == "working" and age > FORGET_WORKING_AFTER) \
                or (item.get("state") in ("approval", "question") and age > FORGET_NEEDS_AFTER):
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


def remove(project: str, agent: str) -> None:
    _path(*identity(project, agent)).unlink(missing_ok=True)


def clear_finished() -> None:
    for item in snapshot():
        if item["state"] in ("done", "idle"):
            _path(item["project"], item["agent"]).unlink(missing_ok=True)


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


def today_stats(now: float | None = None, hours: int = 12) -> dict:
    """Numbers for the Today card, from history.jsonl: finished, errors, hourly trend, longest run."""
    now = time.time() if now is None else now
    day_start = now - 24 * 3600
    events = []
    try:
        for line in (root() / "history.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                if e["updated"] >= day_start:
                    events.append(e)
            except (ValueError, KeyError):
                continue
    except OSError:
        pass
    events.sort(key=lambda e: e["updated"])
    trend = [0] * hours
    err_trend = [0] * hours
    done = errors = 0
    longest = 0.0
    started: dict[tuple, float] = {}
    for e in events:
        key = (e["project"], e["agent"])
        if e["state"] == "working":
            started.setdefault(key, e["updated"])
        elif key in started:
            longest = max(longest, e["updated"] - started.pop(key))
        if e["state"] == "done":
            done += 1
            bucket = int((now - e["updated"]) // 3600)
            if bucket < hours:
                trend[hours - 1 - bucket] += 1
        elif e["state"] == "error":
            errors += 1
            bucket = int((now - e["updated"]) // 3600)
            if bucket < hours:
                err_trend[hours - 1 - bucket] += 1
    for t in started.values():
        longest = max(longest, now - t)  # still running
    return {"done": done, "errors": errors, "trend": trend, "err_trend": err_trend, "longest": format_age(longest) if longest else "-"}


# ---- mute, tray heartbeat and toast hand-off (small files, same no-daemon style as the agent rows)
def muted_until() -> float:
    """Epoch seconds until which alerts are muted (0 when not muted)."""
    try:
        until = float((root() / "mute_until").read_text())
    except (OSError, ValueError):
        return 0.0
    return until if until > time.time() else 0.0


def set_mute(seconds: float) -> None:
    """Mute alerts for `seconds`; 0 unmutes."""
    path = root() / "mute_until"
    if seconds <= 0:
        path.unlink(missing_ok=True)
    else:
        path.write_text(str(time.time() + seconds))


def tray_heartbeat() -> None:
    (root() / "tray.alive").write_text(str(time.time()))


def tray_alive() -> bool:
    try:
        return time.time() - float((root() / "tray.alive").read_text()) < 4
    except (OSError, ValueError):
        return False


def queue_toast(toast: dict) -> None:
    """Hand an alert to the tray app, which shows it as an animated Pintu popup."""
    folder = root() / "toasts"
    folder.mkdir(mode=0o700, exist_ok=True)
    tmp = folder / f"{time.time_ns()}.tmp"
    tmp.write_text(json.dumps(toast), encoding="utf-8")
    os.replace(tmp, tmp.with_suffix(".json"))


def take_toasts() -> list[dict]:
    """Newest-last list of queued toasts; the files are removed."""
    out = []
    for path in sorted((root() / "toasts").glob("*.json")) if (root() / "toasts").is_dir() else []:
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
        path.unlink(missing_ok=True)
    return out
