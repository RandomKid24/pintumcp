"""Cross-platform desktop notification and sound for agent alerts."""

import platform
import subprocess
import shutil
import sys
from pathlib import Path

SYSTEM = platform.system()

# Built-in system sounds per OS
SOUNDS = {
    "default": {
        "Darwin": "/System/Library/Sounds/Glass.aiff",
        "Windows": None,  # uses winsound.Beep
        "Linux": None,    # uses paplay beep
    },
    "success": {
        "Darwin": "/System/Library/Sounds/Hero.aiff",
        "Windows": None,
        "Linux": None,
    },
    "attention": {
        "Darwin": "/System/Library/Sounds/Ping.aiff",
        "Windows": None,
        "Linux": None,
    },
    "error": {
        "Darwin": "/System/Library/Sounds/Sosumi.aiff",
        "Windows": None,
        "Linux": None,
    },
    "complete": {
        "Darwin": "/System/Library/Sounds/Blow.aiff",
        "Windows": None,
        "Linux": None,
    },
}


def _get_sound_path(sound_name: str) -> str | None:
    """Resolve a sound name to a platform-specific file path."""
    entry = SOUNDS.get(sound_name, SOUNDS["default"])
    if isinstance(entry, dict):
        return entry.get(SYSTEM)
    return entry


def play_sound(sound_name: str = "default", volume: int = 80) -> bool:
    """Play a sound cross-platform. Returns True on success."""
    try:
        if SYSTEM == "Darwin":
            path = _get_sound_path(sound_name)
            if path and Path(path).exists():
                subprocess.Popen(
                    ["afplay", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            # fallback: use system beep
            subprocess.Popen(
                ["osascript", "-e", "beep"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True

        elif SYSTEM == "Windows":
            import winsound
            freq = 800
            duration = 300
            if sound_name == "error":
                freq, duration = 400, 500
            elif sound_name == "attention":
                freq, duration = 1000, 200
            elif sound_name == "success":
                freq, duration = 1200, 200
            winsound.Beep(freq, duration)
            return True

        elif SYSTEM == "Linux":
            # Try paplay first, then aplay, then speaker-test
            if shutil.which("paplay"):
                path = _get_sound_path(sound_name)
                if path and Path(path).exists():
                    subprocess.Popen(
                        ["paplay", path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True
            # fallback: beep via console
            if shutil.which("beep"):
                subprocess.Popen(["beep"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            # ultimate fallback: print bell character
            sys.stdout.write("\a")
            sys.stdout.flush()
            return True

    except Exception as e:
        print(f"[pintumcp] Sound error: {e}", file=sys.stderr)
        return False

    return False


def send_notification(
    title: str,
    message: str,
    sound: str = "default",
    volume: int = 80,
    play_snd: bool = True,
) -> dict:
    """Send a desktop notification with optional sound.

    Returns dict with 'notification' and 'sound' success status.
    """
    result = {"notification": False, "sound": False, "platform": SYSTEM}

    # --- Desktop Notification ---
    try:
        if SYSTEM == "Darwin":
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True,
            )
            result["notification"] = True

        elif SYSTEM == "Windows":
            try:
                from winotify import Notification, audio
                toast = Notification(
                    app_id="Agent Alerts",
                    title=title,
                    msg=message,
                )
                toast.set_audio(audio.Default, loop=False)
                toast.show()
                result["notification"] = True
            except ImportError:
                # fallback: PowerShell notification
                ps_cmd = (
                    f'[Windows.UI.Notifications.ToastNotificationManager, '
                    f'Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;'
                    f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms;'
                    f'[System.Windows.Forms.MessageBox]::Show(\'{message}\', \'{title}\')"'
                )
                subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                )
                result["notification"] = True

        elif SYSTEM == "Linux":
            if shutil.which("notify-send"):
                subprocess.run(
                    ["notify-send", title, message],
                    check=True,
                    capture_output=True,
                )
                result["notification"] = True
            else:
                print(f"[pintumcp] {title}: {message}")
                result["notification"] = True  # printed at least

    except Exception as e:
        print(f"[pintumcp] Notification error: {e}", file=sys.stderr)

    # --- Sound (always plays with notification by default) ---
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
    """Send a desktop notification with sound. Sound is always played."""
    sound_map = {
        "low": "default",
        "normal": "default",
        "critical": "error",
    }
    resolved_sound = sound or sound_map.get(priority, "default")
    return send_notification(title, message, sound=resolved_sound, volume=volume)