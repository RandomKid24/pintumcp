"""pintumcp — Agent Alerts MCP Server.

Exposes tools for AI agents to send desktop notifications with sound
when they finish work, need attention, or encounter errors.
"""

from mcp.server.mcpserver import MCPServer
from events import completion_dispatcher, deliver_event
from notifier import alert, doctor as notification_doctor, send_notification, play_sound
from config import get

mcp = MCPServer(
    "Agent Alerts",
    description="Desktop notifications with sound for AI agent events",
    instructions=(
        "Alert the user so they need not watch the screen. Call agent_approval before any "
        "action needing their authorization, agent_question when blocked on their input, "
        "agent_error when work fails, and agent_done once when a task finishes (completions "
        "are bundled). Call agent_working at the start of a task that will take minutes (silent). Pass project and agent when running several agents in parallel."
    ),
)


@mcp.tool()
def alert_notify(
    title: str = "Agent Alert",
    message: str = "Something happened!",
    priority: str = "normal",
    sound: str | None = None,
) -> dict:
    """Send a desktop notification WITH sound. Sound always plays.

    Use this when you need to get the user's attention.
    Priority levels: low, normal, critical (affects sound choice).
    """
    volume = get("volume", 80)
    return alert(title, message, priority=priority, sound=sound, volume=volume)


@mcp.tool()
def notify(
    title: str = "Agent Alert",
    message: str = "Notification from agent",
) -> dict:
    """Send a desktop notification WITH sound. Simple two-arg API.

    Always plays a sound so the user doesn't miss it.
    """
    volume = get("volume", 80)
    sound = get("default_sound", "default")
    return send_notification(title, message, sound=sound, volume=volume)


@mcp.tool()
def ping(sound: str = "default") -> dict:
    """Play a sound only (no notification). Use to get attention silently.

    Available sounds: default, success, attention, error, complete
    """
    volume = get("volume", 80)
    success = play_sound(sound, volume)
    return {"sound": sound, "success": success}


@mcp.tool()
def doctor(send_test: bool = True) -> dict:
    """Check local popup, sound, and icon readiness; optionally send a test alert."""
    return notification_doctor(send_test)


@mcp.tool()
def agent_done(
    message: str = "Agent has finished the task successfully!",
    project: str | None = None,
    agent: str | None = None,
) -> dict:
    """Notify the user that the agent completed its work.

    Plays a success chime and shows a desktop notification.
    """
    return completion_dispatcher.queue_completion(
        message, get("volume", 80), project, agent
    )


@mcp.tool()
def agent_working(
    message: str = "Agent started a long task.",
    project: str | None = None,
    agent: str | None = None,
) -> dict:
    """Silent heads-up that a long task has started (shows the thinking face).

    Use it only for tasks that will take minutes; finish with agent_done.
    """
    return deliver_event("working", message, get("volume", 80), project, agent)


@mcp.tool()
def agent_question(
    message: str = "Agent has a question for you!",
    project: str | None = None,
    agent: str | None = None,
) -> dict:
    """Notify the user that the agent needs input or has a question.

    Plays an attention sound and shows a desktop notification.
    """
    return deliver_event("question", message, get("volume", 80), project, agent)


@mcp.tool()
def agent_approval(
    message: str = "Agent needs your approval before continuing.",
    project: str | None = None,
    agent: str | None = None,
) -> dict:
    """Notify the user immediately that an agent needs approval to continue.

    Use this before any action that needs explicit user authorization.
    """
    return deliver_event("approval", message, get("volume", 80), project, agent)


@mcp.tool()
def agent_error(
    message: str = "Agent encountered an error!",
    project: str | None = None,
    agent: str | None = None,
) -> dict:
    """Notify the user that the agent hit an error.

    Plays an error sound and shows a desktop notification.
    """
    return deliver_event("error", message, get("volume", 80), project, agent)


if __name__ == "__main__":
    mcp.run()
