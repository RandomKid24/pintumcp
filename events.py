"""Local lifecycle event formatting and completion bundling."""

from __future__ import annotations

from threading import Lock, Timer
from typing import Callable

from notifier import alert


EVENT_DETAILS = {
    "done": ("Task Complete", "normal", "success"),
    "question": ("Input Needed", "normal", "attention"),
    "approval": ("Approval Needed", "normal", "attention"),
    "error": ("Error", "critical", "error"),
}


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
    return alert(
        title=format_event_title(event, project, agent),
        message=message,
        priority=priority,
        sound=sound,
        volume=volume,
    )


class CompletionDispatcher:
    """Group same-label completion events into a short local summary."""

    def __init__(
        self,
        deliver: Callable[[str, str, int, str | None, str | None], dict] = deliver_event,
        timer_factory: Callable[..., Timer] = Timer,
    ) -> None:
        self._deliver = deliver
        self._timer_factory = timer_factory
        self._lock = Lock()
        self._pending: dict[tuple[str | None, str | None], dict] = {}

    def queue_completion(
        self,
        message: str,
        volume: int,
        project: str | None = None,
        agent: str | None = None,
    ) -> dict:
        """Queue a completion for a three-second, process-local bundle."""
        key = (clean_label(project), clean_label(agent))
        with self._lock:
            bucket = self._pending.setdefault(
                key,
                {"messages": [], "volume": volume},
            )
            bucket["messages"].append(message)
            if len(bucket["messages"]) == 1:
                timer = self._timer_factory(3, self.flush_completion, args=(key,))
                timer.daemon = True
                bucket["timer"] = timer
                timer.start()
        return {"queued": True, "delay_seconds": 3}

    def flush_completion(self, key: tuple[str | None, str | None]) -> dict | None:
        """Send and remove one pending bundle exactly once."""
        with self._lock:
            bucket = self._pending.pop(key, None)
        if bucket is None:
            return None
        messages = bucket["messages"]
        message = messages[0] if len(messages) == 1 else f"{len(messages)} agents completed: {'; '.join(messages[:5])}"
        return self._deliver("done", message, bucket["volume"], key[0], key[1])


completion_dispatcher = CompletionDispatcher()
