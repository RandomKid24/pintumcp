<p align="center">
  <img src="https://img.shields.io/badge/MCP-Server-blue?style=for-the-badge&logo=modelcontextprotocol&logoColor=white" alt="MCP Server">
  <img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-green?style=for-the-badge" alt="Cross Platform">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/npm/v/pintumcp?style=for-the-badge&logo=npm&logoColor=white" alt="npm">
  <img src="https://img.shields.io/github/license/RandomKid24/pintumcp?style=for-the-badge" alt="License">
</p>

<h1 align="center">pintumcp</h1>

<p align="center">
  <strong>Never miss an AI agent alert again.</strong><br>
  Desktop notifications with sound for every AI coding tool you use.
</p>

<p align="center">
  <code>npm install -g pintumcp</code> → done. Every agent in every tool can now ping you.
</p>

---

## Why?

You kick off a long-running task in Claude. You switch to another tab. Five minutes later, the agent is done — but you don't know. You miss the output. You miss the question. You waste time.

**pintumcp fixes this.** When an agent finishes, asks a question, or hits an error, you get a desktop notification **with sound**. Cross-platform. Zero config. Works everywhere.

## Install

```bash
npx pintumcp
```

One command. That's it. This will:

```
 Scanning your machine for AI coding tools...

  ✓ MiMoCode          → ~/.config/mimocode/mimocode.jsonc
  ✓ OpenCode          → ~/.config/opencode/opencode.json
  ✓ Claude Desktop    → ~/Library/Application Support/Claude/...
  ✓ Claude Code       → ~/.claude/settings.json
  ✓ Codex             → ~/.codex/config.toml
  ✓ Antigravity       → ~/Library/Application Support/Antigravity/...

  ✓ pintumcp installed! 6 tool(s) configured.
  Restart your AI coding tools to activate alerts.
```

- Creates a Python virtual environment
- Installs the MCP SDK
- Auto-detects **every AI coding tool** on your machine
- Writes the MCP server config into each one
- Sends a test notification so you know it works

**No API keys. No accounts. No cloud. Everything runs locally.**

## Supported Tools

| Tool | Status | Config |
|------|--------|--------|
| **MiMoCode** | Auto-detected | `~/.config/mimocode/mimocode.jsonc` |
| **OpenCode** | Auto-detected | `~/.config/opencode/opencode.json` |
| **Claude Desktop** | Auto-detected | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Claude Code** | Auto-detected | `~/.claude/settings.json` |
| **Codex** (OpenAI) | Auto-detected | `~/.codex/config.toml` |
| **Antigravity** | Auto-detected | `~/Library/Application Support/Antigravity/User/settings.json` |
| **VS Code** | Auto-detected | `~/Library/Application Support/Code/User/settings.json` |

> Don't see your tool? Run `npx pintumcp detect` to check, or add it manually.

## How It Works

Once configured, the MCP server starts **automatically** when you open any supported tool. The tool reads its config, sees `pintumcp`, and spawns the server in the background. You don't start it manually — it's always there, waiting to alert you.

When an agent calls a tool like `agent_done` or `agent_question`, pintumcp:

1. Shows a **native desktop notification** (macOS Notification Center / Windows Toast / Linux notify-send)
2. Plays a **distinct sound** so you hear it even if you're not looking at the screen

## MCP Tools

Six tools for every agent situation:

| Tool | When to use | Sound |
|------|------------|-------|
| `alert_notify` | Full control — title, message, priority, sound | Configurable |
| `notify` | Quick alert — just title + message | Default chime |
| `ping` | Sound only — get attention without a popup | Configurable |
| `agent_done` | Work finished successfully | Success chime |
| `agent_question` | Agent needs your input | Attention ping |
| `agent_error` | Something went wrong | Error tone |

Every notification **always plays sound**. You will hear it.

### Usage Examples

In any AI agent conversation, the agent can call:

```
# Task complete
agent_done("Built and tested the auth module. All 47 tests pass.")

# Need input
agent_question("Should I use PostgreSQL or MongoDB for this service?")

# Something broke
agent_error("Build failed: missing dependency 'lodash' in package.json")
```

You'll see a notification and hear the sound immediately — even if you're in a different app.

## Commands

```bash
npx pintumcp              # Install + configure everything
npx pintumcp install      # Same as above
npx pintumcp detect       # Scan for AI tools (read-only, no changes)
npx pintumcp test         # Send a test notification + sound
npx pintumcp run          # Start MCP server manually (stdio mode)
npx pintumcp help         # Show help
```

## Sounds

Five built-in sounds, each mapped to a different situation:

| Sound | Vibe | macOS | Windows | Linux |
|-------|------|-------|---------|-------|
| `default` | Neutral chime | Glass.aiff | 800Hz beep | System beep |
| `success` | Victory fanfare | Hero.aiff | 1200Hz beep | System beep |
| `attention` | Quick ping | Ping.aiff | 1000Hz beep | System beep |
| `error` | Alert tone | Sosumi.aiff | 400Hz beep | System beep |
| `complete` | Done signal | Blow.aiff | 800Hz beep | System beep |

## Configuration

Edit `config.json` in the install directory (`<npm-global>/pintumcp/python/config.json`):

```json
{
  "default_title": "Agent Alert",
  "default_sound": "default",
  "volume": 80,
  "always_sound_with_notification": true
}
```

### Environment Variables

Override any setting without editing files:

```bash
export PINTUMCP_TITLE="My Custom Title"
export PINTUMCP_SOUND="attention"
export PINTUMCP_VOLUME=100
```

| Variable | What it does | Default |
|----------|-------------|---------|
| `PINTUMCP_TITLE` | Default notification title | `Agent Alert` |
| `PINTUMCP_SOUND` | Default sound name | `default` |
| `PINTUMCP_VOLUME` | Volume (0-100) | `80` |

## Cross-Platform

| | macOS | Windows | Linux |
|-|-------|---------|-------|
| **Notification** | `osascript` Notification Center | `winotify` native toast | `notify-send` |
| **Sound** | `afplay` with system .aif | `winsound.Beep` | `paplay` / beep |
| **Deps** | None (built-in) | `winotify` (auto-installed) | `libnotify-bin` |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No sound on macOS | System Preferences > Sound > Enable "Play sound on startup" and system sounds |
| No notification on Linux | `sudo apt install libnotify-bin` |
| No notification on Windows | `pip install winotify` in the venv |
| Python not found | Install Python 3.10+ and ensure `python3` is in PATH |
| Tool not detected | Run `npx pintumcp detect` to check, or configure manually |
| Config not taking effect | Restart the AI tool — MCP servers load at startup |

## Manual Setup

If you prefer not to use npm:

```bash
git clone https://github.com/RandomKid24/pintumcp.git
cd pintumcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Then add this to your tool's MCP config:

```json
{
  "mcpServers": {
    "pintumcp": {
      "command": "/path/to/pintumcp/.venv/bin/python",
      "args": ["/path/to/pintumcp/server.py"]
    }
  }
}
```

## Architecture

```
pintumcp/
├── npm/                    # npm package (what you install)
│   ├── bin/pintumcp.js     # CLI entry point
│   ├── lib/
│   │   ├── detect.js       # AI tool auto-detection
│   │   └── configure.js    # Config writer for each tool
│   ├── python/
│   │   ├── server.py       # MCP server (Python)
│   │   ├── notifier.py     # Cross-platform notifications + sound
│   │   ├── config.py       # Configuration loader
│   │   └── config.json     # Default settings
│   ├── install.js          # npm postinstall hook
│   └── package.json
├── server.py               # Standalone MCP server
├── notifier.py             # Notification engine
├── config.py               # Config loader
├── config.json             # Default settings
├── requirements.txt        # Python dependencies
└── README.md
```

## License

MIT

---

<p align="center">
  <strong>pintumcp</strong> — because your AI agents should be able to tap you on the shoulder.
</p>