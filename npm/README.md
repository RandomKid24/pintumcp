<p align="center">
  <img src="https://img.shields.io/badge/MCP-Server-blue?style=for-the-badge&logo=modelcontextprotocol&logoColor=white" alt="MCP Server">
  <img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-green?style=for-the-badge" alt="Cross Platform">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/github/stars/RandomKid24/pintumcp?style=for-the-badge&logo=github&logoColor=white" alt="Stars">
  <img src="https://img.shields.io/github/license/RandomKid24/pintumcp?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/npm/v/pintumcp?style=for-the-badge&logo=npm" alt="npm version">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/pintumcp-pet.gif" width="180" alt="pintumcp mascot waving">
</p>

<h1 align="center">pintumcp</h1>

<p align="center">
  <strong>Never miss an AI agent alert again.</strong><br>
  Desktop notifications with sound for every AI coding tool you use.
</p>

<p align="center">
  One command. Every tool. Zero config. Runs locally.
</p>

---

## The Problem

You kick off a long task in Claude. You switch tabs. Five minutes later the agent is done — but you don't know. You miss the output. You miss the question. You waste time scrolling back.

## The Fix

```bash
npx pintumcp
```

(or straight from GitHub: `npx github:RandomKid24/pintumcp`)

That's it. One command. This will:

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

---

## What You'll See

Each alert type has its own mascot pose, and labelled titles tell parallel agents apart.

<p align="center">
  <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/alert-preview.png" width="560" alt="Illustration of pintumcp notifications for task complete, approval needed and error">
</p>
<p align="center"><sub>Illustration of the popups (macOS style). Windows and Linux use their native toast and notify-send.</sub></p>

On macOS, install [terminal-notifier](https://github.com/julienXX/terminal-notifier) (`brew install terminal-notifier`) and clicking a popup brings you back to the app running the agent. It is optional; `doctor` tells you whether it is active.

---

## How It Works

Once configured, the MCP server starts **automatically** when you open any supported tool. The tool reads its config, sees `pintumcp`, and spawns the server in the background. You don't start it manually — it's always there.

When an agent calls a tool like `agent_done` or `agent_question`:

1. A **native desktop notification** appears (macOS Notification Center / Windows Toast / Linux notify-send)
2. A **distinct sound** plays — so you hear it even if you're not looking at the screen

Every notification **always plays sound**. You will hear it.

---

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

> Don't see your tool? Run `npx github:RandomKid24/pintumcp detect` to check, or add it manually.

---

## MCP Tools

Seven local tools for every agent situation:

| Tool | When to use | Sound |
|------|------------|-------|
| `alert_notify` | Full control — title, message, priority, sound | Configurable |
| `notify` | Quick alert — just title + message | Default chime |
| `ping` | Sound only — get attention without a popup | Configurable |
| `doctor` | Verify local popup, sound, and icon readiness | Gentle test chime |
| `agent_done` | Work finished successfully | Success chime |
| `agent_question` | Agent needs your input | Attention ping |
| `agent_approval` | Agent needs your approval before continuing | Attention ping |
| `agent_error` | Something went wrong | Error tone |

### Usage Examples

In any AI agent conversation, the agent can call:

```
# Task complete — waits three seconds so matching completions can be combined
agent_done("Built and tested the auth module. All 47 tests pass.", project="API", agent="Agent 2")

# Need input
agent_question("Should I use PostgreSQL or MongoDB for this service?", project="API", agent="Agent 2")

# Approval needed before a consequential action
agent_approval("Approve deploying version 2.4.0 to production?")

# Something broke
agent_error("Build failed: missing dependency 'lodash' in package.json")

# Verify this machine can show the popup, play the sound, and load the icon
doctor()
```

Questions, approvals, and errors appear immediately (identical repeats within 5 seconds are dropped). Completion alerts wait three seconds: completions for the same project become one concise popup — even when they come from agents running in separate AI apps or sessions on your machine. Labels are optional, and existing calls remain valid. Pending completions are sent right away if the server exits.

The server also tells your AI tool *when* to call each alert (via MCP server instructions), so no prompt or `CLAUDE.md` setup is needed.

Everything runs locally inside the MCP process started by your AI tool. There is no account, cloud backend, database, or separate service to run.

---

## Commands

```bash
npx github:RandomKid24/pintumcp              # Install + configure everything
npx github:RandomKid24/pintumcp install      # Same as above
npx github:RandomKid24/pintumcp detect       # Scan for AI tools (read-only, no changes)
npx github:RandomKid24/pintumcp test         # Send a test notification + sound
npx github:RandomKid24/pintumcp doctor       # Check popup, sound and icon readiness
npx github:RandomKid24/pintumcp uninstall    # Remove pintumcp from every AI tool's config
npx github:RandomKid24/pintumcp run          # Start MCP server manually (stdio mode)
npx github:RandomKid24/pintumcp help         # Show help
```

---

## Sounds

Five built-in sounds, each mapped to a different situation:

| Sound | Vibe | macOS | Windows | Linux |
|-------|------|-------|---------|-------|
| `default` | Gentle chime | Glass.aiff | System notification | Desktop message |
| `success` | Gentle chime | Glass.aiff | System notification | Desktop message |
| `attention` | Soft ping | Ping.aiff | System notification | Desktop message |
| `error` | Gentle attention | Glass.aiff | System notification | Desktop message |
| `complete` | Gentle chime | Glass.aiff | System notification | Desktop message |

---

## Configuration

Edit `config.json` in the install directory:

```json
{
  "default_title": "Agent Alert",
  "default_sound": "default",
  "volume": 80,
  "always_sound_with_notification": true,
  "quiet_hours": { "start": "22:00", "end": "08:00" },
  "mute_when_focused": true
}
```

- `quiet_hours` — between these local times popups still appear but without sound (errors keep their sound). Omit it to disable.
- `mute_when_focused` — skip "task complete" alerts while the app running your agent is already the focused window (macOS). Questions, approvals and errors always alert. Off by default.

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
| `PINTUMCP_MUTE_WHEN_FOCUSED` | `1` to mute completions while the agent's app is focused | off |

---

## Cross-Platform

| | macOS | Windows | Linux |
|-|-------|---------|-------|
| **Notification** | `osascript` (JXA) Notification Center | `winotify` native toast | `notify-send` |
| **Sound** | `afplay` with system .aif | Windows system notification | `canberra-gtk-play` / `paplay` |
| **Deps** | None (built-in) | `winotify` (auto-installed) | `libnotify-bin`, optional `libcanberra-gtk3-module` |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No sound on macOS | System Settings > Sound > Enable system sounds |
| No notification on Linux | `sudo apt install libnotify-bin` |
| No notification on Windows | `pip install winotify` in the venv |
| Python not found | Install Python 3.10+ and ensure `python3` is in PATH |
| Tool not detected | Run `npx github:RandomKid24/pintumcp detect` to check |
| Config not taking effect | Restart the AI tool — MCP servers load at startup |
| Unsure whether alerts work | Run `npx github:RandomKid24/pintumcp doctor` (or call the MCP `doctor()` tool); it checks local dependencies and sends a test alert |

---

## Manual Setup

If you prefer not to use npx:

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

---

## Architecture

```
pintumcp/
├── npm/                    # CLI installer (what npx runs)
│   ├── bin/pintumcp.js     # Entry point
│   ├── lib/
│   │   ├── detect.js       # AI tool auto-detection
│   │   └── configure.js    # Config writer per tool
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

---

## License

MIT

---

<p align="center">
  <strong>pintumcp</strong> — because your AI agents should be able to tap you on the shoulder.
</p>
