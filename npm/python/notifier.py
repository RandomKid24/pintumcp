"""Cross-platform desktop notification and sound for agent alerts."""

import platform
import subprocess
import shutil
import sys
from pathlib import Path

SYSTEM = platform.system()

SOUNDS = {
    "default": {
        "Darwin": "/System/Library/Sounds/Glass.aiff",
        "Windows": None,
        "Linux": None,
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
    entry = SOUNDS.get(sound_name, SOUNDS["default"])
    if isinstance(entry, dict):
        return entry.get(SYSTEM)
    return entry


def play_sound(sound_name: str = "default", volume: int = 80) -> bool:
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
            subprocess.Popen(
                ["osascript", "-e", "beep"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        elif SYSTEM == "Windows":
            import winsound
            freq, duration = 800, 300
            if sound_name == "error":
                freq, duration = 400, 500
            elif sound_name == "attention":
                freq, duration = 1000, 200
            elif sound_name == "success":
                freq, duration = 1200, 200
            winsound.Beep(freq, duration)
            return True
        elif SYSTEM == "Linux":
            if shutil.which("paplay"):
                path = _get_sound_path(sound_name)
                if path and Path(path).exists():
                    subprocess.Popen(
                        ["paplay", path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True
            if shutil.which("beep"):
                subprocess.Popen(["beep"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
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
    result = {"notification": False, "sound": False, "platform": SYSTEM}
    try:
        if SYSTEM == "Darwin":
            # Escape quotes for AppleScript
            safe_title = title.replace('"', '\\"')
            safe_msg = message.replace('"', '\\"')
            # Use terminal-notifier for proper toast popup if available
            if shutil.which("terminal-notifier"):
                subprocess.Popen(
                    ["terminal-notifier",
                     "-title", title,
                     "-message", message,
                     "-appIcon", "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/AlertNoteIcon.icns",
                     "-sound", "Glass"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                result["notification"] = True
            else:
                # osascript display notification — shows in Notification Center
                script = f'display notification "{safe_msg}" with title "{safe_title}" sound name "Glass"'
                subprocess.run(
                    ["osascript", "-e", script],
                    check=True, capture_output=True,
                )
                result["notification"] = True
        elif SYSTEM == "Windows":
            try:
                from winotify import Notification, audio
                toast = Notification(
                    app_id="Agent Alerts", title=title, msg=message,
                )
                toast.set_audio(audio.Default, loop=False)
                toast.show()
                result["notification"] = True
            except ImportError:
                subprocess.run(
                    ["powershell", "-Command",
                     f'Add-Type -AssemblyName System.Windows.Forms;'
                     f'[System.Windows.Forms.MessageBox]::Show(\'{message}\', \'{title}\')'],
                    capture_output=True,
                )
                result["notification"] = True
        elif SYSTEM == "Linux":
            if shutil.which("notify-send"):
                subprocess.run(
                    ["notify-send", title, message],
                    check=True, capture_output=True,
                )
                result["notification"] = True
            else:
                print(f"[pintumcp] {title}: {message}")
                result["notification"] = True
    except Exception as e:
        print(f"[pintumcp] Notification error: {e}", file=sys.stderr)
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
    sound_map = {"low": "default", "normal": "default", "critical": "error"}
    resolved_sound = sound or sound_map.get(priority, "default")
    return send_notification(title, message, sound=resolved_sound, volume=volume)