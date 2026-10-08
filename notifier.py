"""Cross-platform desktop notifications with gentle, native sounds."""

import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


SYSTEM = platform.system()

# These are deliberately short system sounds. Avoid alarms, fanfares, and
# terminal bells, which are disruptive during normal agent work.
MACOS_SOUNDS = {
    "default": "Glass",
    "success": "Glass",
    "attention": "Ping",
    "error": "Glass",
    "complete": "Glass",
}


def _macos_notify(title: str, message: str) -> bool:
    """Submit a native macOS Notification Center notification through JXA."""
    script = f"""
ObjC.import("Foundation");
const notification = $.NSUserNotification.alloc.init;
notification.title = $({json.dumps(title)});
notification.informativeText = $({json.dumps(message)});
$.NSUserNotificationCenter.defaultUserNotificationCenter.deliverNotification(notification);
"""
    try:
        subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"[pintumcp] macOS notification error: {error}", file=sys.stderr)
        return False


def play_sound(sound_name: str = "default", volume: int = 80) -> bool:
    """Play a brief, non-intrusive system sound without blocking the MCP server."""
    try:
        if SYSTEM == "Darwin":
            sound = MACOS_SOUNDS.get(sound_name, MACOS_SOUNDS["default"])
            path = Path("/System/Library/Sounds") / f"{sound}.aiff"
            if not path.exists():
                return False
            clamped_volume = max(0, min(int(volume), 100)) / 100
            subprocess.Popen(
                ["afplay", "-v", str(clamped_volume), str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True

        if SYSTEM == "Windows":
            import winsound

            winsound.PlaySound(
                "SystemNotification", winsound.SND_ALIAS | winsound.SND_ASYNC
            )
            return True

        if SYSTEM == "Linux":
            if shutil.which("canberra-gtk-play"):
                subprocess.Popen(
                    ["canberra-gtk-play", "-i", "message"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True

            message_sound = Path("/usr/share/sounds/freedesktop/stereo/message.oga")
            if shutil.which("paplay") and message_sound.exists():
                subprocess.Popen(
                    ["paplay", str(message_sound)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
    except (OSError, ValueError, ImportError) as error:
        print(f"[pintumcp] Sound error: {error}", file=sys.stderr)
    return False


def _windows_notify(title: str, message: str) -> bool:
    """Show a Windows toast; winotify is installed by the CLI on Windows."""
    try:
        from winotify import Notification

        Notification(app_id="pintumcp", title=title, msg=message).show()
        return True
    except (ImportError, OSError, RuntimeError) as error:
        print(
            "[pintumcp] Windows notifications require winotify; "
            f"run `pintumcp install` to repair the installation ({error}).",
            file=sys.stderr,
        )
        return False


def _linux_notify(title: str, message: str) -> bool:
    """Show a freedesktop notification when a desktop notification daemon exists."""
    if not shutil.which("notify-send"):
        print(
            "[pintumcp] Linux notifications require notify-send (libnotify-bin).",
            file=sys.stderr,
        )
        return False
    try:
        subprocess.run(
            ["notify-send", "--urgency=normal", title, message],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"[pintumcp] Linux notification error: {error}", file=sys.stderr)
        return False


def send_notification(
    title: str,
    message: str,
    sound: str = "default",
    volume: int = 80,
    play_snd: bool = True,
) -> dict:
    """Send a platform-native popup and, by default, a gentle sound."""
    result = {"notification": False, "sound": False, "platform": SYSTEM}
    if SYSTEM == "Darwin":
        result["notification"] = _macos_notify(title, message)
    elif SYSTEM == "Windows":
        result["notification"] = _windows_notify(title, message)
    elif SYSTEM == "Linux":
        result["notification"] = _linux_notify(title, message)
    else:
        print(f"[pintumcp] Unsupported platform: {SYSTEM}", file=sys.stderr)

    if play_snd:
        result["sound"] = play_sound(sound, volume)
    return result


def alert(
    title: str,
    message: str,
    priority: str = "normal",
    sound: str | None = None,
    volume: int = 80,
) -> dict:
    sound_map = {"low": "default", "normal": "default", "critical": "attention"}
    return send_notification(
        title,
        message,
        sound=sound or sound_map.get(priority, "default"),
        volume=volume,
    )
