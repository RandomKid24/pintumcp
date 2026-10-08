"""pintumcp — Agent Alerts MCP Server.

Exposes tools for AI agents to send desktop notifications with sound
when they finish work, need attention, or encounter errors.
"""

from mcp.server.mcpserver import MCPServer
from notifier import alert, send_notification, play_sound
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
def agent_done(message: str = "Agent has finished the task successfully!") -> dict:
    """Notify the user that the agent completed its work.

    Plays a success chime and shows a desktop notification.
    """
    return alert(
        title="Agent: Task Complete",
        message=message,
        priority="normal",
        sound="success",
        volume=get("volume", 80),
    )


@mcp.tool()
def agent_question(message: str = "Agent has a question for you!") -> dict:
    """Notify the user that the agent needs input or has a question.

    Plays an attention sound and shows a desktop notification.
    """
    return alert(
        title="Agent: Input Needed",
        message=message,
        priority="normal",
        sound="attention",
        volume=get("volume", 80),
    )


@mcp.tool()
def agent_error(message: str = "Agent encountered an error!") -> dict:
    """Notify the user that the agent hit an error.

    Plays an error sound and shows a desktop notification.
    """
    return alert(
        title="Agent: Error",
        message=message,
        priority="critical",
        sound="error",
        volume=get("volume", 80),
    )


if __name__ == "__main__":
    mcp.run()