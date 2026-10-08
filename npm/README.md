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

## Meet Pintu

Pintu is the little pixel-art mascot of pintumcp: the one who taps you on the shoulder when your agent needs you.

**What he looks like.** A small teal creature built from chunky pixels. He has a wide, rounded body with a darker teal belt, big dark eyes with white glints, a tiny smile, stubby arms and two short feet. On top of his head sits a grey antenna stalk topped with an amber bell: his "ping". When something happens, sound-wave marks pop out beside the bell.

**His moods.** Pintu changes pose with the kind of alert, so you can tell what happened from the corner of your eye, before you even read the title:

| | Pose | When you see it | Title |
|---|---|---|---|
| <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/icons/done.png" width="88" alt="Pintu cheering"> | **Cheering.** Arms up, happy `^ ^` eyes, sparkles around him | The agent finished its work | `Task Complete` |
| <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/icons/question.png" width="88" alt="Pintu with a question mark"> | **Curious.** A `?` floats beside his head | The agent is stuck and needs your input | `Input Needed` |
| <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/icons/approval.png" width="88" alt="Pintu with a raised hand and an exclamation mark"> | **Hand up.** A raised hand and a `!` | The agent wants permission before a risky step | `Approval Needed` |
| <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/icons/error.png" width="88" alt="Pintu looking upset"> | **Upset.** Turns red, `x x` eyes, a small frown | Something failed | `Error` |

**All his faces.** Pintu has 18 faces. The four alert moods above go into your popups; the rest are for the terminal, docs and stickers.

<p align="center">
  <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/pintu-faces.png" width="720" alt="Pintu's faces: idle, wave, cheer, question, hand up, error, wink, surprised, sleepy, love, thinking, angry, dizzy, cool, sad and party">
</p>

| Face | Where he shows it |
|---|---|
| `idle`, `blink`, `waveA`, `waveB` | Waves hello while `install`, `test` and `doctor` run |
| `done` | `doctor` when everything is ready; the Task Complete popup |
| `party` | A bundle of **3 or more** completions in one popup; the end of `install`, with confetti |
| `thinking` | The silent "Started" popup from `agent_working` |
| `sleepy` | Any popup that arrives during your **quiet hours** (silent, so he is asleep too) |
| `wink` | After `test` sends its sample alert |
| `sad` | The end of `uninstall`: "bye for now" |
| `error` | `doctor` or `test` when something is wrong; the Error popup |
| `question`, `approval` | The Input Needed and Approval Needed popups |
| `wink`, `surprised`, `love`, `angry`, `dizzy`, `cool` | Free to use in your own docs, slides and stickers |

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

## Meet Pintu

Pintu is the little pixel-art mascot of pintumcp: the one who taps you on the shoulder when your agent needs you.

**What he looks like.** A small teal creature built from chunky pixels, drawn with a dark-teal outline so he stays crisp on any background. He has a wide, rounded body with a glossy highlight on his head, a darker belt, rosy cheeks, big dark eyes with white glints, a tiny smile, stubby arms and two short feet. On top of his head sits a grey antenna stalk topped with an amber bell: his "ping". When something happens, sound-wave marks pop out beside the bell.

**His moods.** Pintu changes pose with the kind of alert, so you can tell what happened from the corner of your eye, before you even read the title:

| | Pose | When you see it | Title |
|---|---|---|---|
| <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/icons/done.png" width="88" alt="Pintu cheering"> | **Cheering.** Arms up, happy `^ ^` eyes, sparkles around him | The agent finished its work | `Task Complete` |
| <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/icons/question.png" width="88" alt="Pintu with a question mark"> | **Curious.** A `?` floats beside his head | The agent is stuck and needs your input | `Input Needed` |
| <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/icons/approval.png" width="88" alt="Pintu with a raised hand and an exclamation mark"> | **Hand up.** A raised hand and a `!` | The agent wants permission before a risky step | `Approval Needed` |
| <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/icons/error.png" width="88" alt="Pintu looking upset"> | **Upset.** Turns red, `x x` eyes, a small frown | Something failed | `Error` |

He also waves hello when you run `install`, `test` or `doctor` in a terminal, and cheers (or turns red) when the check is done.

<p align="center">
  <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/pintumcp-pet.gif" width="160" alt="Pintu waving">
</p>

**Transparent versions.** Pintu on his own, with no background, for slides, docs and stickers. They live in [`assets/transparent`](assets/transparent) and are split into two folders:

- [`icons/`](assets/transparent/icons): the four mood icons (`done`, `question`, `approval`, `error`) at 512px, same size and scale as the app icons, plus `thinking`, `sleepy` and `party`, and every other face as `pintu-<face>.png`.
- [`previews/`](assets/transparent/previews): animated GIFs of Pintu (`pintu-pet.gif` plus a bouncing GIF for each face), `pintu-faces.png` (the face sheet without labels) and `alert-preview.png`, the popup cards without a backdrop.

All of them are generated from one sprite builder: edit `scripts/build_pet.py`, then run `python3 scripts/build_pet.py && python3 scripts/make_assets.py`, and every icon, GIF and terminal animation updates together.

---

## What You'll See

A real popup on macOS (the pet appears on the right; the left icon is the notifier app's own):

<p align="center">
  <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/popup-real.png" width="560" alt="A real pintumcp notification: API · Agent 2: Task Complete">
</p>

Each alert type has its own mascot pose, and labelled titles tell parallel agents apart (rendered illustration):

<p align="center">
  <img src="https://raw.githubusercontent.com/RandomKid24/pintumcp/main/assets/alert-preview.png" width="560" alt="Illustration of pintumcp notifications for task complete, approval needed and error">
</p>
<p align="center"><sub>Windows and Linux use their native toast and notify-send. See <a href="#meet-pintu">Meet Pintu</a> for all of his moods and the transparent versions.</sub></p>

On macOS, install [terminal-notifier](https://github.com/julienXX/terminal-notifier) (`brew install terminal-notifier`) and clicking a popup brings you back to the app running the agent. It is optional; `doctor` tells you whether it is active.

---

## Agent Status Board (macOS menu bar)

A tiny app that puts Pintu in your menu bar and shows **every agent and what it is doing**, each with its own face:

| Agent | Status | Pintu |
|---|---|---|
| API · Agent 1 | Working, 4m | thinking |
| API · Agent 2 | Needs approval | hand up `!` |
| Web · Agent 1 | Needs your input | `?` |
| Docs · Agent 1 | Done | cheering |
| Web · Agent 2 | Error | red |

The menu-bar icon shows the most urgent agent, with a number for how many need you. Click a row to jump back to that agent's app.

```bash
npx pintumcp tray            # Pintu appears in the menu bar
npx pintumcp tray stop       # and leaves again
npx pintumcp hooks install   # optional: Claude Code reports its status by itself
```

**Where the status comes from**

- The MCP tools you already have: `agent_working`, `agent_question`, `agent_approval`, `agent_error`, `agent_done`, plus `agent_status` for silent progress notes. Pass `project` and `agent` so rows have good names; without them each AI session gets its own "Session 1234" row.
- Claude Code hooks (optional, `hooks install`): Claude Code reports "working", "needs permission / input" and "done" automatically, so it shows up even if the AI never calls a tool. `hooks remove` undoes it, and your settings file is backed up first.

Limits: an agent only shows up if it reports, and an agent that goes quiet while "working" for 10 minutes is flagged as maybe stuck. Everything stays on your machine, in small files under `~/.pintumcp/agents`. The menu-bar app is macOS-only for now; Windows and Linux builds are planned.

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

Nine local tools for every agent situation:

| Tool | When to use | Sound |
|------|------------|-------|
| `alert_notify` | Full control — title, message, priority, sound | Configurable |
| `notify` | Quick alert — just title + message | Default chime |
| `ping` | Sound only — get attention without a popup | Configurable |
| `doctor` | Verify local popup, sound, and icon readiness | Gentle test chime |
| `agent_working` | A long task just started (silent heads-up, thinking face) | None |
| `agent_status` | Silent progress note for the menu-bar status board | None |
| `agent_done` | Work finished successfully | Success chime |
| `agent_question` | Agent needs your input | Attention ping |
| `agent_approval` | Agent needs your approval before continuing | Attention ping |
| `agent_error` | Something went wrong | Error tone |

### Usage Examples

In any AI agent conversation, the agent can call:

```
# Starting something that will take minutes? A silent heads-up
agent_working("Refactoring the auth module", project="API", agent="Agent 2")

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
| Popups never appear | `doctor` reports whether a macOS Focus is on (it can only read this with Full Disk Access; otherwise it says "unknown" — check Control Center) |
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
