#!/usr/bin/env node

const { detect } = require("../lib/detect");
const { configureMcp, removeMcp } = require("../lib/configure");
const { playPet, showPose } = require("../lib/pet");
const { addHooks, removeHooks, listHooks } = require("../lib/hooks");
const os = require("os");
const path = require("path");
const fs = require("fs");
const { execSync, spawn } = require("child_process");

// Everything runs from a stable folder, never from the package folder: `npx` keeps packages in a cache that
// npm cleans up, and the tray, the login item and every tool's MCP entry would then point at deleted files.
const APP_DIR = path.join(os.homedir(), ".pintumcp", "app");
const PYTHON_DIR = path.join(APP_DIR, "python");
const SERVER_PY = path.join(PYTHON_DIR, "server.py");
const VENV_DIR = path.join(APP_DIR, ".venv");

// Copy this package's Python sources into APP_DIR (every run, so an update is picked up).
function syncApp() {
  try {
    fs.mkdirSync(APP_DIR, { recursive: true });
    fs.cpSync(path.join(__dirname, "..", "python"), PYTHON_DIR, { recursive: true, force: true, filter: (p) => !p.includes("__pycache__") });
  } catch (e) {
    console.error(`  Could not copy Pintu into ${APP_DIR}: ${e.message}`);
  }
}

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
    const dependencies = ['"mcp>=2.0.0,<3"'];
    if (process.platform === "win32") {
      dependencies.push('"psutil>=5.9"');   // finds Claude Code's process in-process, no helper windows
    }
    if (process.platform === "darwin") {
      dependencies.push('"pyobjc-framework-WebKit>=10"');
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

const LAUNCH_AGENT = path.join(os.homedir(), "Library", "LaunchAgents", "com.pintumcp.tray.plist");

// Start Pintu in the menu bar now and again at every login.
function startTrayAtLogin() {
  cmdTray();
  if (process.platform === "win32") {            // a .vbs in Startup runs the tray with no console window
    const startup = path.join(process.env.APPDATA || "", "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "pintumcp-tray.vbs");
    fs.writeFileSync(startup, `CreateObject("Wscript.Shell").Run """${getVenvPython()}"" ""${path.join(PYTHON_DIR, "tray_cross.py")}""", 0\r\n`);
    return console.log("  ✓ Pintu will start in the tray at login");
  }
  if (process.platform === "linux") {
    const dir = path.join(os.homedir(), ".config", "autostart");
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, "pintumcp.desktop"),
      `[Desktop Entry]\nType=Application\nName=Pintu\nExec="${getVenvPython()}" "${path.join(PYTHON_DIR, "tray_cross.py")}"\nX-GNOME-Autostart-enabled=true\n`);
    // an app-menu entry too, so Pintu can always be opened even where the shell hides tray icons
    const apps = path.join(os.homedir(), ".local", "share", "applications");
    fs.mkdirSync(apps, { recursive: true });
    fs.writeFileSync(path.join(apps, "pintumcp.desktop"),
      `[Desktop Entry]\nType=Application\nName=Pintu\nComment=Agent status board\nExec="${getVenvPython()}" "${path.join(PYTHON_DIR, "tray_cross.py")}" --open\nIcon=${path.join(PYTHON_DIR, "assets", "pintumcp-icon.png")}\nCategories=Utility;\nTerminal=false\n`);
    return console.log("  ✓ Pintu will start in the tray at login");
  }
  const args = [getVenvPython(), path.join(PYTHON_DIR, "tray.py")].map((a) => `<string>${a}</string>`).join("");
  fs.mkdirSync(path.dirname(LAUNCH_AGENT), { recursive: true });
  fs.writeFileSync(LAUNCH_AGENT, `<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict><key>Label</key><string>com.pintumcp.tray</string>
<key>ProgramArguments</key><array>${args}</array><key>RunAtLoad</key><true/></dict></plist>
`);
  console.log("  ✓ Pintu will start in the menu bar at login");
}

// OpenCode v2 discovers plugin files under the global plugins directory, so a
// copy there is enough. A small runtime file beside it carries the Python paths
// so the plugin never has to parse the MCP config.
const OPENCODE_PLUGINS = path.join(os.homedir(), ".config", "opencode", "plugins");

function installOpencodePlugin(pythonPath, serverPath) {
  if (!fs.existsSync(path.dirname(OPENCODE_PLUGINS))) return; // OpenCode isn't installed
  fs.mkdirSync(OPENCODE_PLUGINS, { recursive: true });
  fs.copyFileSync(path.join(__dirname, "..", "opencode", "pintumcp.js"), path.join(OPENCODE_PLUGINS, "pintumcp.js"));
  fs.writeFileSync(path.join(OPENCODE_PLUGINS, "pintumcp.runtime.json"),
    JSON.stringify({ python: pythonPath, server: serverPath }, null, 2) + "\n");
  console.log("  ✓ OpenCode alerts plugin installed");
}

function removeOpencodePlugin() {
  for (const file of ["pintumcp.js", "pintumcp.runtime.json"]) {
    fs.rmSync(path.join(OPENCODE_PLUGINS, file), { force: true });
  }
}

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

  // Alerts for OpenCode (plugin) and Claude Code (hooks) so replies notify without prompting the agent.
  try {
    installOpencodePlugin(pythonPath, serverPath);
    const claude = path.join(os.homedir(), ".claude", "settings.json");
    if (fs.existsSync(path.dirname(claude))) {
      if (fs.existsSync(pythonPath)) {
        addHooks(claude, pythonPath, path.join(PYTHON_DIR, "hook.py"));
        console.log("  ✓ Claude Code hooks installed");
      } else {
        console.log("  ✗ Claude Code hooks skipped: Python environment not found");
      }
    }
  } catch (e) { console.log(`  ✗ alerts setup: ${e.message}`); }

  try { startTrayAtLogin(); } catch (e) { console.log(`  ✗ menu-bar app: ${e.message}`); }

  testNotification();

  showPose("party");
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
    showPose("wink");
  } catch (e) {
    showPose("error");
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
  try { removeHooks(path.join(os.homedir(), ".claude", "settings.json")); } catch {}
  try { removeOpencodePlugin(); } catch {}
  try { execSync("pkill -f python/tray", { stdio: "ignore" }); } catch {}
  fs.rmSync(LAUNCH_AGENT, { force: true });
  try { fs.rmSync(path.join(os.homedir(), ".config", "autostart", "pintumcp.desktop"), { force: true }); } catch {}
  try { fs.rmSync(path.join(os.homedir(), ".local", "share", "applications", "pintumcp.desktop"), { force: true }); } catch {}
  try { fs.rmSync(path.join(process.env.APPDATA || "", "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "pintumcp-tray.vbs"), { force: true }); } catch {}
  fs.rmSync(APP_DIR, { recursive: true, force: true });   // the copied sources and the Python environment
  showPose("sad");
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
    const out = execSync(`"${py}" -c "import json; from notifier import doctor; print(json.dumps(doctor(), indent=2))"`, {
      cwd: PYTHON_DIR,
      encoding: "utf-8",
    });
    console.log(out);
    const ready = JSON.parse(out).ready;
    showPose(ready ? "done" : "error");
    console.log(ready ? "  All good — alerts will reach you.\n" : "  Something needs fixing — see the \"fix\" lines above.\n");
  } catch (e) {
    showPose("error");
    process.exit(1);
  }
}

// Ubuntu/GNOME shows tray icons only through AppIndicator, which pystray reaches via PyGObject ("gi").
// The venv can't see the system's gi unless system site-packages are on, so turn that on and re-check.
// Ubuntu's package ships ubuntu-appindicators@ubuntu.com; appindicatorsupport@... is the extensions.gnome.org build. Try both.
function enableTrayExtension() {
  for (const id of ["appindicatorsupport@rgcjonas.gmail.com", "ubuntu-appindicators@ubuntu.com"]) {
    try { execSync(`gnome-extensions enable ${id}`, { stdio: "ignore" }); } catch {}
  }
}

function ensureLinuxTray(py) {
  enableTrayExtension();   // installed but switched off is the usual reason GNOME shows no icon (needs a log out/in once)
  const probe = () => { try { execSync(`"${py}" -c "import gi"`, { stdio: "ignore" }); return true; } catch { return false; } };
  if (probe()) return;
  const cfg = path.join(VENV_DIR, "pyvenv.cfg");
  try { fs.writeFileSync(cfg, fs.readFileSync(cfg, "utf-8").replace("include-system-site-packages = false", "include-system-site-packages = true")); } catch {}
  if (probe()) return;
  // Ask for the missing system packages through the desktop's own password prompt (pkexec), then enable the tray extension.
  const pkgs = "python3-gi gir1.2-ayatanaappindicator3-0.1 gnome-shell-extension-appindicator";
  try {
    console.log("Installing the Ubuntu tray libraries (a password prompt will appear)...");
    execSync(`pkexec apt-get install -y ${pkgs}`, { stdio: "inherit" });
  } catch {}
  enableTrayExtension();
  if (probe()) return;
  console.log(`
  Pintu still can't reach the Ubuntu tray. Install the libraries once, then log out and in:

    sudo apt install ${pkgs}
`);
}

function cmdTray(sub) {
  const mac = process.platform === "darwin", script = mac ? "tray.py" : "tray_cross.py";
  if (sub === "stop-quiet") {
    try { if (process.platform !== "win32") execSync(`pkill -f python/${script}`, { stdio: "ignore" }); } catch {}
    return;
  }
  if (sub === "stop") {
    try {
      if (process.platform === "win32") execSync(`wmic process where "commandline like '%tray_cross.py%'" call terminate`, { stdio: "ignore" });
      else execSync(`pkill -f python/${script}`);
      console.log("Pintu left the tray.");
    } catch { console.log("The tray app was not running."); }
    return;
  }
  const py = getVenvPython();
  if (!fs.existsSync(py)) {
    console.error("Run `pintumcp install` first.");
    process.exit(1);
  }
  const [probe, pkg] = mac ? ["import WebKit", "pyobjc-framework-WebKit>=10"] : ["import pystray, PIL, psutil", "pystray pillow psutil"];
  try {
    execSync(`"${py}" -c "${probe}"`, { stdio: "ignore" });
  } catch {
    console.log(`Installing the tray dependency (${pkg})...`);
    execSync(`"${py}" -m pip install ${mac ? `"${pkg}"` : pkg} --quiet`, { stdio: "inherit" });
  }
  if (process.platform === "linux") ensureLinuxTray(py);
  if (process.platform === "win32") {            // a frameless native window for the panel; without it we fall back to an Edge window
    try { execSync(`"${py}" -c "import webview"`, { stdio: "ignore" }); }
    catch { try { execSync(`"${py}" -m pip install pywebview --quiet`, { stdio: "inherit" }); } catch { console.log("  (pywebview unavailable, using an Edge window for the panel)"); } }
  }
  cmdTray("stop-quiet");
  const child = spawn(py, [path.join(PYTHON_DIR, script)], { detached: true, stdio: "ignore", cwd: PYTHON_DIR, windowsHide: true });
  child.unref();
  console.log(mac ? "Pintu is in your menu bar. Stop him with `pintumcp tray stop`."
                  : "Pintu is in your system tray (Linux: needs a tray/AppIndicator). Stop him with `pintumcp tray stop`.");
}

// Pintu in the terminal, for anyone who'd rather not use the menu-bar app.
// `pintumcp board` watches the same status files the tray reads; `--once` prints one frame.
function cmdBoard(args) {
  const py = getVenvPython();
  if (!fs.existsSync(py)) {
    console.error("  Error: Run `pintumcp install` first.");
    process.exit(1);
  }
  const child = spawn(py, [path.join(PYTHON_DIR, "board.py"), ...(args || [])], {
    stdio: "inherit",
    cwd: PYTHON_DIR,
  });
  child.on("error", (err) => {
    console.error(`  Error: ${err.message}`);
    process.exit(1);
  });
  process.on("SIGINT", () => child.kill("SIGINT"));
  process.on("SIGTERM", () => child.kill("SIGTERM"));
  child.on("exit", (code) => process.exit(code ?? 0));
}

function cmdHooks(sub) {
  const settings = path.join(os.homedir(), ".claude", "settings.json");
  const python = getVenvPython();
  const hookPath = path.join(PYTHON_DIR, "hook.py");
  if (sub === "install") {
    if (!fs.existsSync(python)) {
      console.error(`  ✗ Python environment not found (${python}); run \`pintumcp install\` first.`);
      process.exit(1);
    }
    addHooks(settings, python, hookPath);
    console.log(`Added Claude Code hooks to ${settings} (backup: settings.json.pintumcp.bak).`);
    console.log("Claude Code sessions now report starting / working / needs-you / done / failed to the menu-bar app.");
  } else if (sub === "remove") {
    let removed;
    try {
      removed = removeHooks(settings);
    } catch (e) {
      console.error(`  ✗ ${e.message}`);
      process.exit(1);
    }
    console.log(removed ? "Removed pintumcp's Claude Code hooks." : "No pintumcp hooks were installed.");
  } else if (sub === "status") {
    let hooks;
    try {
      hooks = listHooks(settings);
    } catch (e) {
      console.error(`  ✗ ${e.message}`);
      process.exit(1);
    }
    if (hooks.length === 0) {
      console.log("No pintumcp hooks installed.");
      return;
    }
    console.log(`pintumcp hooks in ${settings}:`);
    for (const { event, command } of hooks) {
      const stale = command !== `"${python}" "${hookPath}" ${event}`;
      console.log(`  ${stale ? "⚠" : "✓"} ${event.padEnd(16)} ${command}${stale ? "  (paths changed; re-run 'pintumcp hooks install')" : ""}`);
    }
  } else {
    console.error("Usage: pintumcp hooks install|remove|status");
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
  npx pintumcp tray         Show every agent's status in the macOS menu bar (tray stop to quit)
  npx pintumcp board        Watch every agent's status live in your terminal (--once for one frame)
  npx pintumcp hooks install  Let Claude Code report its status automatically (hooks remove to undo; hooks status to check)
  npx pintumcp uninstall    Remove pintumcp from every AI tool's config
  npx pintumcp run          Start MCP server (stdio mode)
  npx pintumcp help         Show this help

Supported AI Tools:
  • MiMoCode       ~/.config/mimocode/mimocode.jsonc
  • OpenCode       ~/.config/opencode/opencode.json
  • Claude Desktop ~/Library/Application Support/Claude/claude_desktop_config.json
  • Claude Code    ~/.claude/settings.json
  • Codex          ~/.codex/config.toml
  • Kiro (app+CLI) ~/.kiro/settings/mcp.json
  • Antigravity    ~/Library/Application Support/Antigravity/User/settings.json
  • VS Code        ~/Library/Application Support/Code/User/settings.json
`);
}

// ─── Main ───────────────────────────────────────────────

const cmd = (process.argv[2] || "install").toLowerCase();
if (!["help", "--help", "-h", "uninstall"].includes(cmd)) syncApp();

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
  case "tray":
    cmdTray(process.argv[3]);
    break;
  case "board":
    cmdBoard(process.argv.slice(3));
    break;
  case "hooks":
    cmdHooks(process.argv[3]);
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
