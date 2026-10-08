"""pintumcp — Agent Alerts MCP Server."""

from mcp.server.mcpserver import MCPServer
from events import completion_dispatcher, deliver_event
from notifier import alert, doctor as notification_doctor, send_notification, play_sound
from config import get

mcp = MCPServer(
    "Agent Alerts",
    description="Desktop notifications with sound for AI agent events",
)


@mcp.tool()
def alert_notify(
    title: str = "Agent Alert",
    message: str = "Something happened!",
    priority: str = "normal",
    sound: str | None = None,
) -> dict:
    """Send a desktop notification WITH sound. Sound always plays.
    Priority levels: low, normal, critical (affects sound choice).
    """
    return alert(title, message, priority=priority, sound=sound, volume=get("volume", 80))


@mcp.tool()
def notify(
    title: str = "Agent Alert",
    message: str = "Notification from agent",
) -> dict:
    """Send a desktop notification WITH sound. Simple two-arg API."""
    return send_notification(title, message, sound=get("default_sound", "default"), volume=get("volume", 80))


@mcp.tool()
def ping(sound: str = "default") -> dict:
    """Play a sound only. Available: default, success, attention, error, complete"""
    return {"sound": sound, "success": play_sound(sound, get("volume", 80))}


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
    """Notify the user that the agent completed its work."""
    return completion_dispatcher.queue_completion(
        message, get("volume", 80), project, agent
    )


@mcp.tool()
def agent_question(
    message: str = "Agent has a question for you!",
    project: str | None = None,
    agent: str | None = None,
) -> dict:
    """Notify the user that the agent needs input or has a question."""
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
    """Notify the user that the agent hit an error."""
    return deliver_event("error", message, get("volume", 80), project, agent)


if __name__ == "__main__":
    mcp.run()
