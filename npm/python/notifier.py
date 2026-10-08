"""Cross-platform desktop notifications with gentle, native sounds."""

import json
import importlib.util
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


SYSTEM = platform.system()
ICON_DIR = Path(__file__).parent / "assets"
ICON_PATH = ICON_DIR / "pintumcp-icon.png"

# These are deliberately short system sounds. Avoid alarms, fanfares, and
# terminal bells, which are disruptive during normal agent work.
MACOS_SOUNDS = {
    "default": "Glass",
    "success": "Glass",
    "attention": "Ping",
    "error": "Glass",
    "complete": "Glass",
}

def _check_notification_backend() -> dict:
    if SYSTEM == "Darwin":
        ready = bool(shutil.which("osascript"))
        detail = "terminal-notifier" if _terminal_notifier() else "JXA Notification Center (falls back to display notification)"
        return {"ready": ready, "detail": detail, "fix": "macOS includes osascript"}
    if SYSTEM == "Windows":
        ready = importlib.util.find_spec("winotify") is not None
        return {
            "ready": ready,
            "detail": "winotify native toast",
            "fix": "Run `pintumcp install` to install winotify.",
        }
    if SYSTEM == "Linux":
        ready = bool(shutil.which("notify-send"))
        return {
            "ready": ready,
            "detail": "notify-send desktop notification",
            "fix": "Install libnotify-bin (Debian/Ubuntu) or your distribution's libnotify package.",
        }
    return {"ready": False, "detail": f"Unsupported platform: {SYSTEM}", "fix": "Use macOS, Windows, or Linux."}


def _check_sound_backend() -> dict:
    if SYSTEM == "Darwin":
        ready = Path("/System/Library/Sounds/Glass.aiff").exists()
        return {"ready": ready, "detail": "macOS Glass sound", "fix": "macOS system sounds are built in."}
    if SYSTEM == "Windows":
        return {"ready": True, "detail": "Windows SystemNotification sound", "fix": "Windows sound support is built in."}
    if SYSTEM == "Linux":
        ready = bool(shutil.which("canberra-gtk-play")) or (
            bool(shutil.which("paplay"))
            and Path("/usr/share/sounds/freedesktop/stereo/message.oga").exists()
        )
        return {
            "ready": ready,
            "detail": "desktop message sound",
            "fix": "Install libcanberra-gtk3-module or PulseAudio utilities with freedesktop sounds.",
        }
    return {"ready": False, "detail": f"Unsupported platform: {SYSTEM}", "fix": "Use macOS, Windows, or Linux."}


def doctor(send_test: bool = True) -> dict:
    """Check local popup, sound, and icon readiness; optionally send a test alert."""
    checks = {
        "icon": {"ready": ICON_PATH.is_file(), "path": str(ICON_PATH)},
        "notification": _check_notification_backend(),
        "sound": _check_sound_backend(),
    }
    result = {
        "platform": SYSTEM,
        "checks": checks,
        "ready": all(check["ready"] for check in checks.values()),
    }
    if SYSTEM == "Darwin":
        focus = bool(_terminal_notifier())
        state = macos_focus()
        result["optional"] = {
            "focus_mode": {
                "ready": state != "on",
                "state": state or "unknown",
                "fix": {
                    "on": "A Focus is on, so macOS hides popups. Turn it off in Control Center, or allow pintumcp in the Focus settings.",
                    None: "Can't read Focus state without Full Disk Access. If popups don't appear, check Control Center for an active Focus.",
                }.get(state, ""),
            },
            "click_to_focus": {
                "ready": focus,
                "fix": "" if focus else "brew install terminal-notifier, then allow its notifications in System Settings.",
            }
        }
    if send_test:
        result["test_delivery"] = send_notification(
            "pintumcp doctor", "Local notification test", sound="default", volume=35
        )
    return result


_tn_ready: bool | None = None


def _terminal_notifier() -> str | None:
    """terminal-notifier path, only if macOS has authorised it to post notifications."""
    global _tn_ready
    tool = shutil.which("terminal-notifier")
    if not tool:
        return None
    if _tn_ready is None:
        try:
            out = subprocess.run([tool, "-diagnose"], capture_output=True, text=True, timeout=10).stdout
            _tn_ready = bool(re.search(r"authorization\s+authorized", out))
        except (OSError, subprocess.SubprocessError):
            _tn_ready = False
    return tool if _tn_ready else None


def _macos_notify(title: str, message: str, icon: Path = ICON_PATH) -> bool:
    """Show a macOS notification. Click-to-focus needs terminal-notifier (optional).

    Order: terminal-notifier (modern API, clicking focuses the app running the agent),
    then JXA NSUserNotification (deprecated by Apple, still works), then plain
    `display notification` (no custom icon) so an alert is never silently lost.
    """
    tool = _terminal_notifier()
    if tool:
        command = [tool, "-title", title, "-message", message, "-contentImage", str(icon)]
        app = os.environ.get("__CFBundleIdentifier")  # app that launched this agent
        if app:
            command += ["-activate", app]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, timeout=10)
            return True
        except (OSError, subprocess.SubprocessError) as error:
            print(f"[pintumcp] terminal-notifier error: {error}", file=sys.stderr)

    script = f"""
ObjC.import("Foundation");
ObjC.import("AppKit");
const notification = $.NSUserNotification.alloc.init;
notification.title = $({json.dumps(title)});
notification.informativeText = $({json.dumps(message)});
notification.contentImage = $.NSImage.alloc.initWithContentsOfFile($({json.dumps(str(icon))}));
$.NSUserNotificationCenter.defaultUserNotificationCenter.deliverNotification(notification);
"""
    plain = f"display notification {json.dumps(message, ensure_ascii=False)} with title {json.dumps(title, ensure_ascii=False)}"
    for command in (["osascript", "-l", "JavaScript", "-e", script], ["osascript", "-e", plain]):
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            return True
        except (OSError, subprocess.CalledProcessError) as error:
            print(f"[pintumcp] macOS notification error: {error}", file=sys.stderr)
    return False


def macos_focus() -> str | None:
    """'on' / 'off' if macOS lets us read the Focus (Do Not Disturb) state, else None."""
    path = Path.home() / "Library/DoNotDisturb/DB/Assertions.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8")).get("data", [])
    except (OSError, ValueError, AttributeError):
        return None  # needs Full Disk Access on recent macOS; not an error
    return "on" if any(d.get("storeAssertionRecords") for d in data if isinstance(d, dict)) else "off"


def frontmost_app() -> str | None:
    """Bundle id of the focused macOS app (no permission prompt); None elsewhere/unknown."""
    if SYSTEM != "Darwin":
        return None
    script = 'ObjC.import("AppKit"); ObjC.unwrap($.NSWorkspace.sharedWorkspace.frontmostApplication.bundleIdentifier)'
    try:
        out = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script], capture_output=True, text=True, timeout=5
        ).stdout.strip()
        return out or None
    except (OSError, subprocess.SubprocessError):
        return None


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


def _windows_notify(title: str, message: str, icon: Path = ICON_PATH) -> bool:
    """Show a Windows toast; winotify is installed by the CLI on Windows."""
    try:
        from winotify import Notification

        notification_args = {"app_id": "pintumcp", "title": title, "msg": message}
        if icon.exists():
            notification_args["icon"] = str(icon)
        Notification(**notification_args).show()
        return True
    except (ImportError, OSError, RuntimeError) as error:
        print(
            "[pintumcp] Windows notifications require winotify; "
            f"run `pintumcp install` to repair the installation ({error}).",
            file=sys.stderr,
        )
        return False


def _linux_notify(title: str, message: str, icon: Path = ICON_PATH) -> bool:
    """Show a freedesktop notification when a desktop notification daemon exists."""
    if not shutil.which("notify-send"):
        print(
            "[pintumcp] Linux notifications require notify-send (libnotify-bin).",
            file=sys.stderr,
        )
        return False
    try:
        subprocess.run(
            ["notify-send", "--urgency=normal", f"--icon={icon}", title, message],
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
    icon: Path | None = None,
) -> dict:
    """Send a platform-native popup and, by default, a gentle sound."""
    result = {"notification": False, "sound": False, "platform": SYSTEM}
    icon = icon or ICON_PATH
    if SYSTEM == "Darwin":
        result["notification"] = _macos_notify(title, message, icon)
    elif SYSTEM == "Windows":
        result["notification"] = _windows_notify(title, message, icon)
    elif SYSTEM == "Linux":
        result["notification"] = _linux_notify(title, message, icon)
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
    icon: Path | None = None,
    silent: bool = False,
) -> dict:
    sound_map = {"low": "default", "normal": "default", "critical": "attention"}
    return send_notification(
        title,
        message,
        sound=sound or sound_map.get(priority, "default"),
        volume=volume,
        play_snd=not silent,
        icon=icon,
    )
