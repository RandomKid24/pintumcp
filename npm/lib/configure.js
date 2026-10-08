const fs = require("fs");
const path = require("path");

const MCP_NAME = "pintumcp";

function buildMcpEntry(pythonPath, serverPath) {
  return {
    command: pythonPath,
    args: [serverPath],
  };
}

// MiMoCode uses: { "type": "local", "command": ["python", "server.py"] }
function buildMimocodeEntry(pythonPath, serverPath) {
  return {
    type: "local",
    command: [pythonPath, serverPath],
  };
}

function readJsonc(filePath) {
  let raw = fs.readFileSync(filePath, "utf-8");
  raw = raw.replace(/^\s*\/\/.*$/gm, "");
  raw = raw.replace(/,(\s*[}\]])/g, "$1");
  return JSON.parse(raw);
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + "\n", "utf-8");
}

function writeJsonc(filePath, data) {
  let raw = "";
  if (fs.existsSync(filePath)) {
    raw = fs.readFileSync(filePath, "utf-8");
  }
  let existing = {};
  try {
    existing = readJsonc(filePath);
  } catch {}
  const merged = { ...existing, ...data };
  fs.writeFileSync(filePath, JSON.stringify(merged, null, 2) + "\n", "utf-8");
}

function configureJsonMcpServers(tool, pythonPath, serverPath) {
  let data = {};

  if (fs.existsSync(tool.configPath)) {
    try {
      data = tool.format === "jsonc" ? readJsonc(tool.configPath) : JSON.parse(fs.readFileSync(tool.configPath, "utf-8"));
    } catch {
      data = {};
    }
  }

  if (!data[tool.mcpKey]) {
    data[tool.mcpKey] = {};
  }

  // Build entry based on tool type
  if (tool.mimocodeFormat) {
    data[tool.mcpKey][MCP_NAME] = buildMimocodeEntry(pythonPath, serverPath);
    // Remove stale mcpServers key if present
    delete data["mcpServers"];
  } else if (tool.claudeFormat) {
    // Claude Desktop uses mcpServers with command + args
    data[tool.mcpKey][MCP_NAME] = buildMcpEntry(pythonPath, serverPath);
  } else {
    data[tool.mcpKey][MCP_NAME] = buildMcpEntry(pythonPath, serverPath);
  }

  if (tool.format === "jsonc") {
    writeJsonc(tool.configPath, data);
  } else {
    writeJson(tool.configPath, data);
  }
}

function configureCodexToml(tool, pythonPath, serverPath) {
  let raw = "";
  if (fs.existsSync(tool.configPath)) {
    raw = fs.readFileSync(tool.configPath, "utf-8");
  }

  // Check if pintumcp section already exists
  const sectionRegex = new RegExp(`\\[mcp_servers\\.${MCP_NAME}\\]`, "m");
  if (sectionRegex.test(raw)) {
    // Remove old section
    const lines = raw.split("\n");
    let start = -1;
    let end = lines.length;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].match(sectionRegex)) {
        start = i;
      } else if (start >= 0 && lines[i].match(/^\[/)) {
        end = i;
        break;
      }
    }
    if (start >= 0) {
      lines.splice(start, end - start);
    }
    raw = lines.join("\n");
  }

  // Append new section
  const section = `\n[mcp_servers.${MCP_NAME}]\ncommand = "${pythonPath}"\nargs = ["${serverPath}"]\n`;
  raw = raw.trimEnd() + "\n" + section;
  fs.writeFileSync(tool.configPath, raw, "utf-8");
}

function configureMcp(tool, pythonPath, serverPath) {
  console.log(`  Configuring ${tool.name}...`);

  if (tool.format === "toml") {
    configureCodexToml(tool, pythonPath, serverPath);
  } else {
    configureJsonMcpServers(tool, pythonPath, serverPath);
  }

  console.log(`  ✓ ${tool.name} configured`);
}

module.exports = { configureMcp, buildMcpEntry };