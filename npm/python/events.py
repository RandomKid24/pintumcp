"""Local lifecycle event formatting and completion bundling."""

from __future__ import annotations

import atexit
import hashlib
import itertools
import json
import os
import sys
import tempfile
import time
import uuid
from datetime import datetime, time as dtime
from pathlib import Path
from threading import Timer
from typing import Callable

import notifier
from config import get
from notifier import alert


EVENT_DETAILS = {
    "done": ("Task Complete", "normal", "success"),
    "question": ("Input Needed", "normal", "attention"),
    "approval": ("Approval Needed", "normal", "attention"),
    "error": ("Error", "critical", "error"),
}

DELAY_SECONDS = 3
DEDUPE_SECONDS = 5
MAX_LISTED = 5
_recent: dict[tuple[str, str], float] = {}
_counter = itertools.count()  # keeps arrival order when the clock repeats a timestamp


def in_quiet_hours(now: datetime | None = None) -> bool:
    """True inside the configured quiet window (it may wrap past midnight)."""
    window = get("quiet_hours")
    if not window:
        return False
    try:
        start = dtime.fromisoformat(window["start"])
        end = dtime.fromisoformat(window["end"])
    except (KeyError, TypeError, ValueError):
        return False
    t = (now or datetime.now()).time()
    return start <= t < end if start <= end else t >= start or t < end


def event_icon(event: str) -> Path | None:
    """Per-event mascot pose, if the icon file ships; otherwise the default icon."""
    path = notifier.ICON_DIR / "icons" / f"{event}.png"
    return path if path.is_file() else None


def clean_label(value: str | None) -> str | None:
    """Normalize labels for compact, single-line native notification titles."""
    if value is None:
        return None
    cleaned = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    return cleaned[:64] or None


def format_event_title(
    event: str, project: str | None = None, agent: str | None = None
) -> str:
    """Build a backwards-compatible, optionally labelled lifecycle title."""
    try:
        suffix, _, _ = EVENT_DETAILS[event]
    except KeyError as error:
        raise ValueError(f"Unsupported agent event: {event}") from error
    labels = [label for label in (clean_label(project), clean_label(agent)) if label]
    return f"{' · '.join(labels) or 'Agent'}: {suffix}"


def deliver_event(
    event: str,
    message: str,
    volume: int,
    project: str | None = None,
    agent: str | None = None,
) -> dict:
    """Deliver one labelled agent lifecycle event immediately."""
    try:
        _, priority, sound = EVENT_DETAILS[event]
    except KeyError as error:
        raise ValueError(f"Unsupported agent event: {event}") from error
    title = format_event_title(event, project, agent)
    if event == "done" and get("mute_when_focused"):
        app = os.environ.get("__CFBundleIdentifier")
        if app and notifier.frontmost_app() == app:
            return {"notification": False, "sound": False, "muted": "focused"}
    now = time.monotonic()
    if now - _recent.get((title, message), -DEDUPE_SECONDS) < DEDUPE_SECONDS:
        return {"notification": False, "sound": False, "duplicate": True}
    _recent[(title, message)] = now
    return alert(
        title=title,
        message=message,
        priority=priority,
        sound=sound,
        volume=volume,
        icon=event_icon(event),
        silent=priority != "critical" and in_quiet_hours(),
    )


class CompletionDispatcher:
    """Bundle completions into one popup, across every MCP server on this machine.

    Each completion is a small file in a per-user temp spool. Whichever server's
    timer fires first claims (atomic rename) every file for that project and sends
    one summary; the others find nothing left. No daemon, lock, or backend.
    """

    def __init__(
        self,
        deliver: Callable[..., dict] = deliver_event,
        timer_factory: Callable[..., Timer] = Timer,
        spool: Path | None = None,
    ) -> None:
        self._deliver = deliver
        self._timer_factory = timer_factory
        uid = os.getuid() if hasattr(os, "getuid") else "user"
        self._spool = spool or Path(tempfile.gettempdir()) / f"pintumcp-{uid}"
        self._spool.mkdir(mode=0o700, exist_ok=True)
        self._timers: dict[str, Timer] = {}

    @staticmethod
    def _key(project: str | None) -> str:
        return hashlib.sha1((clean_label(project) or "").encode()).hexdigest()[:12]

    def queue_completion(
        self,
        message: str,
        volume: int,
        project: str | None = None,
        agent: str | None = None,
    ) -> dict:
        """Spool a completion and schedule a flush three seconds from now."""
        key = self._key(project)
        entry = {
            "message": message,
            "volume": volume,
            "project": clean_label(project),
            "agent": clean_label(agent),
        }
        # Windows' coarse clock repeats time_ns: the counter orders, the uuid keeps names unique
        name = f"{key}.{time.time_ns()}.{next(_counter):06d}.{uuid.uuid4().hex[:8]}.json"
        with open(self._spool / name, "x", encoding="utf-8") as f:
            json.dump(entry, f)
        if key not in self._timers:
            timer = self._timer_factory(DELAY_SECONDS, self.flush_completion, args=(key,))
            timer.daemon = True
            self._timers[key] = timer
            timer.start()
        return {"queued": True, "delay_seconds": DELAY_SECONDS}

    def flush_completion(self, key: str) -> dict | None:
        """Claim and send everything spooled for one project, exactly once."""
        self._timers.pop(key, None)
        entries = []
        for path in sorted(self._spool.glob(f"{key}.*.json")):
            claimed = path.with_suffix(f".{os.getpid()}.claimed")
            try:
                path.rename(claimed)  # atomic: only one process wins each file
                entries.append(json.loads(claimed.read_text(encoding="utf-8")))
                claimed.unlink()
            except (OSError, ValueError):
                continue
        if not entries:
            return None
        project = entries[0]["project"]
        agents = {e["agent"] for e in entries if e["agent"]}
        agent = next(iter(agents)) if len(agents) == 1 else None
        messages = [
            f"{e['agent']}: {e['message']}" if len(agents) > 1 and e["agent"] else e["message"]
            for e in entries
        ]
        if len(messages) == 1:
            text = messages[0]
        else:
            extra = len(messages) - MAX_LISTED
            text = f"{len(messages)} tasks completed: " + "; ".join(messages[:MAX_LISTED])
            text += f"; +{extra} more" if extra > 0 else ""
        try:
            result = self._deliver("done", text, max(e["volume"] for e in entries), project, agent)
        except Exception as error:  # timer threads swallow exceptions; make failures visible
            print(f"[pintumcp] completion alert failed: {error}", file=sys.stderr)
            return None
        if not result.get("notification") and not result.get("muted"):
            print("[pintumcp] completion popup was not shown; run doctor", file=sys.stderr)
        return result

    def flush_all(self) -> None:
        """Send this process's pending completions now (used at interpreter exit)."""
        for key, timer in list(self._timers.items()):
            timer.cancel()
            self.flush_completion(key)


completion_dispatcher = CompletionDispatcher()
atexit.register(completion_dispatcher.flush_all)
