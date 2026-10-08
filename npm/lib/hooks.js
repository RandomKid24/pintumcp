// Add/remove pintumcp's Claude Code hooks (they feed the menu-bar status board).
const fs = require("fs");

const EVENTS = ["UserPromptSubmit", "Notification", "Stop"];
const isOurs = (h) => typeof h.command === "string" && h.command.includes("pintumcp") && h.command.includes("hook.py");

function load(settingsPath) {
  return fs.existsSync(settingsPath) ? JSON.parse(fs.readFileSync(settingsPath, "utf-8")) : {};
}

function save(settingsPath, data) {
  if (fs.existsSync(settingsPath)) fs.copyFileSync(settingsPath, settingsPath + ".pintumcp.bak");
  fs.writeFileSync(settingsPath, JSON.stringify(data, null, 2) + "\n", "utf-8");
}

// Drop our entries (and any group left empty); everything else is untouched.
function strip(data) {
  for (const event of Object.keys(data.hooks || {})) {
    data.hooks[event] = data.hooks[event]
      .map((g) => ({ ...g, hooks: (g.hooks || []).filter((h) => !isOurs(h)) }))
      .filter((g) => g.hooks.length > 0);
    if (data.hooks[event].length === 0) delete data.hooks[event];
  }
  if (data.hooks && Object.keys(data.hooks).length === 0) delete data.hooks;
}

function addHooks(settingsPath, python, hookPath) {
  const data = load(settingsPath);
  strip(data);
  data.hooks = data.hooks || {};
  for (const event of EVENTS) {
    data.hooks[event] = data.hooks[event] || [];
    data.hooks[event].push({ hooks: [{ type: "command", command: `"${python}" "${hookPath}" ${event}` }] });
  }
  save(settingsPath, data);
}

function removeHooks(settingsPath) {
  if (!fs.existsSync(settingsPath)) return false;
  const data = load(settingsPath);
  const before = JSON.stringify(data);
  strip(data);
  if (JSON.stringify(data) === before) return false;
  save(settingsPath, data);
  return true;
}

module.exports = { addHooks, removeHooks, EVENTS };
