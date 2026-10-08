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
}

_config: dict | None = None


def _config_path() -> Path:
    return Path(__file__).parent / "config.json"


def load_config() -> dict:
    """Load config from config.json, falling back to defaults."""
    global _config
    if _config is not None:
        return _config

    cfg = dict(DEFAULTS)
    path = _config_path()

    if path.exists():
        try:
            with open(path) as f:
                user_cfg = json.load(f)
            cfg.update(user_cfg)
        except (json.JSONDecodeError, OSError):
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