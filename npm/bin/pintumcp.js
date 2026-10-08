#!/usr/bin/env node

const { detect } = require("../lib/detect");
const { configureMcp, removeMcp } = require("../lib/configure");
const { playPet } = require("../lib/pet");
const path = require("path");
const fs = require("fs");
const { execSync, spawn } = require("child_process");

const PYTHON_DIR = path.join(__dirname, "..", "python");
const SERVER_PY = path.join(PYTHON_DIR, "server.py");
const VENV_DIR = path.join(__dirname, "..", ".venv");

function getVenvPython() {
  const p = process.platform;
  if (p === "win32") {
    return path.join(VENV_DIR, "Scripts", "python.exe");
  }
  return path.join(VENV_DIR, "bin", "python");
}

function getSystemPython() {
  // Try python3 first, then python
  try {
    execSync("python3 --version", { stdio: "ignore" });
    return "python3";
  } catch {}
  try {
    execSync("python --version", { stdio: "ignore" });
    return "python";
  } catch {}
  return null;
}

function setupVenv() {
  if (fs.existsSync(getVenvPython())) {
    console.log("  Virtual environment already exists.");
    return true;
  }

  const py = getSystemPython();
  if (!py) {
    console.error("  Error: Python 3 not found. Install Python first.");
    return false;
  }

  console.log(`  Creating virtual environment with ${py}...`);
  try {
    execSync(`${py} -m venv "${VENV_DIR}"`, { stdio: "inherit" });
    const dependencies = ['"mcp>=2.0.0"'];
    if (process.platform === "win32") {
      dependencies.push('"winotify>=1.1.0"');
    }
    console.log("  Installing notification dependencies...");
    execSync(`"${getVenvPython()}" -m pip install ${dependencies.join(" ")} --quiet`, {
      stdio: "inherit",
    });
    return true;
  } catch (e) {
    console.error(`  Error setting up venv: ${e.message}`);
    return false;
  }
}

function testNotification() {
  console.log("\nTesting notification...");
  try {
    execSync(`"${getVenvPython()}" -c "from notifier import alert; r = alert('pintumcp', 'Install complete! All agents will now alert you.', priority='normal'); print(r)"`, {
      cwd: PYTHON_DIR,
      stdio: "inherit",
    });
  } catch {
    console.log("  (notification test skipped — install dependencies manually)");
  }
}

function printBanner() {
  playPet();
  console.log(`
╔══════════════════════════════════════════╗
║         pintumcp — Agent Alerts          ║
║   Desktop notifications with sound for   ║
║      AI coding agents, everywhere        ║
╚══════════════════════════════════════════╝
`);
}

// ─── Commands ───────────────────────────────────────────

function cmdInstall() {
  printBanner();
  console.log("Setting up Python environment...\n");

  if (!setupVenv()) {
    process.exit(1);
  }

  const pythonPath = getVenvPython();
  const serverPath = SERVER_PY;

  console.log(`\nPython: ${pythonPath}`);
  console.log(`Server: ${serverPath}`);

  console.log("\nDetecting AI coding tools...\n");
  const tools = detect();

  if (tools.length === 0) {
    console.log("  No AI coding tools found. pintumcp is installed but not configured.");
    console.log("  Run `pintumcp config` later to set up integrations.\n");
  } else {
    for (const tool of tools) {
      configureMcp(tool, pythonPath, serverPath);
    }
  }

  testNotification();

  console.log("\n✓ pintumcp installed successfully!");
  console.log(`  Detected ${tools.length} tool(s): ${tools.map(t => t.name).join(", ") || "none"}`);
  console.log("\n  Restart your AI coding tools to activate alerts.\n");
}

function cmdDetect() {
  printBanner();
  console.log("Scanning for AI coding tools...\n");

  const tools = detect();
  if (tools.length === 0) {
    console.log("  No AI coding tools detected.\n");
    return;
  }

  for (const tool of tools) {
    const exists = fs.existsSync(tool.configPath);
    console.log(`  ${exists ? "✓" : "✗"} ${tool.name}`);
    console.log(`    Config: ${tool.configPath}`);
    console.log(`    Format: ${tool.format}`);
    console.log();
  }
}

function cmdTest() {
  printBanner();
  const pythonPath = getVenvPython();
  if (!fs.existsSync(pythonPath)) {
    console.error("  Error: Run `pintumcp install` first.");
    process.exit(1);
  }

  console.log("Sending test notification + sound...\n");
  try {
    execSync(`"${pythonPath}" -c "from notifier import alert; print(alert('pintumcp Test', 'Agent alerts are working!', priority='normal'))"`, {
      cwd: PYTHON_DIR,
      stdio: "inherit",
    });
  } catch (e) {
    console.error(`  Error: ${e.message}`);
  }
}

function cmdUninstall() {
  printBanner();
  console.log("Removing pintumcp from AI tools...\n");
  for (const tool of detect()) {
    try {
      console.log(`  ${removeMcp(tool) ? "✓ removed from" : "- not configured in"} ${tool.name}`);
    } catch (e) {
      console.log(`  ✗ ${tool.name}: ${e.message}`);
    }
  }
  fs.rmSync(VENV_DIR, { recursive: true, force: true });
  console.log("\n  Removed the Python environment. Restart your AI tools to finish.\n");
}

function cmdDoctor() {
  printBanner();
  // notifier.py is stdlib-only, so the system Python works even before `install`.
  const py = fs.existsSync(getVenvPython()) ? getVenvPython() : getSystemPython();
  if (!py) {
    console.error("  Error: Python 3 not found. Install Python first.");
    process.exit(1);
  }
  try {
    execSync(`"${py}" -c "import json; from notifier import doctor; print(json.dumps(doctor(), indent=2))"`, {
      cwd: PYTHON_DIR,
      stdio: "inherit",
    });
  } catch {
    process.exit(1);
  }
}

function cmdRun() {
  const pythonPath = getVenvPython();
  if (!fs.existsSync(pythonPath)) {
    console.error("Error: Run `pintumcp install` first.");
    process.exit(1);
  }

  const child = spawn(pythonPath, [SERVER_PY], {
    stdio: "inherit",
    cwd: PYTHON_DIR,
  });

  child.on("error", (err) => {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  });

  process.on("SIGINT", () => child.kill("SIGINT"));
  process.on("SIGTERM", () => child.kill("SIGTERM"));
}

function cmdHelp() {
  console.log(`
pintumcp — Agent Alerts MCP Server

Usage:
  npx pintumcp              Install and configure all AI tools
  npx pintumcp install      Install Python env + configure tools
  npx pintumcp detect       Scan for installed AI coding tools
  npx pintumcp test         Send a test notification
  npx pintumcp doctor       Check popup, sound and icon; send a test alert
  npx pintumcp uninstall    Remove pintumcp from every AI tool's config
  npx pintumcp run          Start MCP server (stdio mode)
  npx pintumcp help         Show this help

Supported AI Tools:
  • MiMoCode       ~/.config/mimocode/mimocode.jsonc
  • OpenCode       ~/.config/opencode/opencode.json
  • Claude Desktop ~/Library/Application Support/Claude/claude_desktop_config.json
  • Claude Code    ~/.claude/settings.json
  • Codex          ~/.codex/config.toml
  • Antigravity    ~/Library/Application Support/Antigravity/User/settings.json
  • VS Code        ~/Library/Application Support/Code/User/settings.json
`);
}

// ─── Main ───────────────────────────────────────────────

const cmd = (process.argv[2] || "install").toLowerCase();

switch (cmd) {
  case "install":
    cmdInstall();
    break;
  case "detect":
    cmdDetect();
    break;
  case "test":
    cmdTest();
    break;
  case "uninstall":
    cmdUninstall();
    break;
  case "doctor":
    cmdDoctor();
    break;
  case "run":
    cmdRun();
    break;
  case "help":
  case "--help":
  case "-h":
    cmdHelp();
    break;
  default:
    console.error(`Unknown command: ${cmd}`);
    cmdHelp();
    process.exit(1);
}
