const fs = require("fs");
const path = require("path");
const os = require("os");

const HOME = os.homedir();

function platformPaths() {
  const p = os.platform();
  if (p === "darwin") {
    return {
      appData: path.join(HOME, "Library", "Application Support"),
      config: path.join(HOME, ".config"),
    };
  }
  if (p === "win32") {
    return {
      appData: process.env.APPDATA || path.join(HOME, "AppData", "Roaming"),
      config: path.join(HOME, "AppData", "Local"),
    };
  }
  return {
    appData: path.join(HOME, ".config"),
    config: path.join(HOME, ".config"),
  };
}

function detect() {
  const { appData, config } = platformPaths();
  const tools = [];

  // 1. MiMoCode
  const mimocodeCfg = path.join(config, "mimocode", "mimocode.jsonc");
  if (fs.existsSync(mimocodeCfg)) {
    tools.push({
      name: "MiMoCode",
      configPath: mimocodeCfg,
      format: "jsonc",
      mcpKey: "mcp",
      mimocodeFormat: true,
    });
  }

  // 2. OpenCode
  const opencodeCfg = path.join(config, "opencode", "opencode.json");
  if (fs.existsSync(opencodeCfg)) {
    tools.push({
      name: "OpenCode",
      configPath: opencodeCfg,
      format: "json",
      mcpKey: "mcp",
      mimocodeFormat: true,
    });
  }

  // 3. Claude Desktop
  const claudeDesktopCfg = path.join(appData, "Claude", "claude_desktop_config.json");
  if (fs.existsSync(claudeDesktopCfg)) {
    tools.push({
      name: "Claude Desktop",
      configPath: claudeDesktopCfg,
      format: "json",
      mcpKey: "mcpServers",
      claudeFormat: true,
    });
  }

  // 4. Claude Code (terminal)
  const claudeCodeCfg = path.join(HOME, ".claude", "settings.json");
  const claudeCodeCfgAlt = path.join(HOME, ".claude.json");
  if (fs.existsSync(claudeCodeCfg)) {
    tools.push({
      name: "Claude Code",
      configPath: claudeCodeCfg,
      format: "json",
      mcpKey: "mcpServers",
      claudeFormat: true,
    });
  } else if (fs.existsSync(claudeCodeCfgAlt)) {
    tools.push({
      name: "Claude Code",
      configPath: claudeCodeCfgAlt,
      format: "json",
      mcpKey: "mcpServers",
      claudeFormat: true,
    });
  }

  // 5. Codex (OpenAI)
  const codexCfg = path.join(HOME, ".codex", "config.toml");
  if (fs.existsSync(codexCfg)) {
    tools.push({
      name: "Codex",
      configPath: codexCfg,
      format: "toml",
      mcpKey: "mcp_servers",
    });
  }

  // 6. Antigravity (VS Code fork)
  const antigravitySettings = path.join(appData, "Antigravity", "User", "settings.json");
  if (fs.existsSync(antigravitySettings)) {
    tools.push({
      name: "Antigravity",
      configPath: antigravitySettings,
      format: "json",
      mcpKey: "mcp",
    });
  }

  // 7. VS Code (general)
  const vscodeSettings = path.join(appData, "Code", "User", "settings.json");
  if (fs.existsSync(vscodeSettings) && !tools.find(t => t.name === "Antigravity")) {
    tools.push({
      name: "VS Code",
      configPath: vscodeSettings,
      format: "json",
      mcpKey: "mcp",
    });
  }

  return tools;
}

module.exports = { detect, platformPaths };