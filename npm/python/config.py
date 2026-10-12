"""Configuration loader for pintumcp Agent Alerts MCP."""

import json
import os
from pathlib import Path

DEFAULTS = {
    "default_title": "Agent Alert",
    "default_sound": "default",
    "sound_enabled": True,
    "notification_enabled": True,
    "volume": 80,
    "always_sound_with_notification": True,
    # {"start": "22:00", "end": "08:00"}: popups still show, sound is off (errors keep theirs)
    "quiet_hours": None,
    # Skip "task complete" alerts while the app running the agent is already focused (macOS)
    "mute_when_focused": False,
    # Settings screen in the panel
    "toast_enabled": True,     # animated Pintu popup (macOS) instead of the system notification
    "stuck_alerts": True,      # one "maybe stuck?" alert per quiet agent
    "mute_minutes": 60,        # what the Mute button mutes for
    "theme": "dark",           # dark | light | pastel | hacker
    "break_reminder": True,    # nudge after a long work session
    "break_minutes": 50,
    "drink_reminder": True,    # nudge to drink some water while you work
    "drink_minutes": 45,
    "wear": None,              # accessories Pintu wears (None = the daily ones, unlocked by level)
    # Look of the panel
    "layout": "vertical",      # vertical | horizontal
    "sections": {"hero": True, "xp": True, "friends": False, "stats": True, "agents": True, "today": True, "actions": True},
    "agent_rows": 3,           # rows shown before the list scrolls (0 = all)
    "hide_done": False,        # leave finished agents out of the list
    "chart_range": "hours",    # hours | days
    "animations": True,
}

WEARABLE = ("coffee", "sweater", "music", "scarf", "glasses", "hat", "umbrella", "crown", "party", "cape")

# Panel-editable keys; they live in ~/.pintumcp/settings.json so package updates never wipe them
USER_KEYS = ("volume", "sound_enabled", "notification_enabled", "toast_enabled", "stuck_alerts",
             "quiet_hours", "mute_when_focused", "mute_minutes", "theme",
             "break_reminder", "break_minutes", "drink_reminder", "drink_minutes", "wear", "layout", "sections", "agent_rows", "hide_done", "chart_range", "animations")

_config: dict | None = None
_stamp = None  # (mtime of config.json, mtime of settings.json) the cache was built from


def _user_path() -> Path:
    import status
    return status.root() / "settings.json"


def _mtimes():
    out = []
    for p in (_config_path(), _user_path()):
        try:
            out.append(p.stat().st_mtime_ns)
        except OSError:
            out.append(0)
    return tuple(out)


def save_user(values: dict) -> dict:
    """Merge panel-edited settings into settings.json (only known keys, basic type checks)."""
    path = _user_path()
    try:
        current = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        current = {}
    for key, value in values.items():
        if key not in USER_KEYS:
            continue
        if key == "volume":
            value = max(0, min(int(value), 100))
        elif key == "mute_minutes":
            value = max(5, min(int(value), 24 * 60))
        elif key in ("break_minutes", "drink_minutes"):
            value = max(10, min(int(value), 240))
        elif key == "wear":
            value = [w for w in value if w in WEARABLE] if isinstance(value, list) else None
        elif key == "layout":
            value = value if value in ("vertical", "horizontal") else "vertical"
        elif key == "chart_range":
            value = value if value in ("hours", "days") else "hours"
        elif key == "agent_rows":
            value = max(0, min(int(value), 20))
        elif key == "sections":
            names = DEFAULTS["sections"]
            value = {k: bool(value.get(k, names[k])) for k in names} if isinstance(value, dict) else dict(names)
        elif key == "theme":
            value = value if value in ("dark", "light", "pastel", "hacker") else "dark"
        elif key == "quiet_hours":
            value = value if isinstance(value, dict) and {"start", "end"} <= set(value) else None
        else:
            value = bool(value)
        current[key] = value
    path.write_text(json.dumps(current), encoding="utf-8")
    return current


def user_settings() -> dict:
    return {k: get(k) for k in USER_KEYS}


def _config_path() -> Path:
    return Path(__file__).parent / "config.json"


def load_config() -> dict:
    """Load config from config.json, falling back to defaults."""
    global _config, _stamp
    if _config is not None and _stamp == _mtimes():  # cheap stat; edits from the panel apply to every process
        return _config
    _stamp = _mtimes()

    cfg = dict(DEFAULTS)
    path = _config_path()

    if path.exists():
        try:
            with open(path) as f:
                user_cfg = json.load(f)
            cfg.update(user_cfg)
        except (json.JSONDecodeError, OSError):
            pass

    try:
        user = json.loads(_user_path().read_text(encoding="utf-8"))
        cfg.update({k: v for k, v in user.items() if k in USER_KEYS})
    except (OSError, ValueError):
        pass

    # Env var overrides
    env_map = {
        "PINTUMCP_TITLE": "default_title",
        "PINTUMCP_SOUND": "default_sound",
        "PINTUMCP_VOLUME": "volume",
        "PINTUMCP_MUTE_WHEN_FOCUSED": "mute_when_focused",
    }
    for env_key, cfg_key in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            if cfg_key == "volume":
                cfg[cfg_key] = int(val)
            elif cfg_key == "mute_when_focused":
                cfg[cfg_key] = val.lower() in ("1", "true", "yes", "on")
            else:
                cfg[cfg_key] = val

    _config = cfg
    return _config


def get(key: str, default=None):
    """Get a single config value."""
    return load_config().get(key, default)