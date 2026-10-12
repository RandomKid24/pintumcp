// Add/remove pintumcp's Claude Code hooks (they feed the menu-bar status board).
const fs = require("fs");

const EVENTS = ["SessionStart", "UserPromptSubmit", "Notification", "PostToolUse", "Stop", "StopFailure", "SessionEnd"];
const isOurs = (h) => typeof h.command === "string" && h.command.includes("pintumcp") && h.command.includes("hook.py");

function load(settingsPath) {
  if (!fs.existsSync(settingsPath)) return {};
  const raw = fs.readFileSync(settingsPath, "utf-8");
  try {
    return JSON.parse(raw);
  } catch (e) {
    // Refuse to touch a file we can't parse rather than clobber someone's settings.
    throw new Error(`${settingsPath} is not valid JSON (${e.message}); leaving it untouched.`);
  }
}

// Write via temp file + rename so a reader never sees a half-written settings file.
function save(settingsPath, data) {
  if (fs.existsSync(settingsPath)) fs.copyFileSync(settingsPath, settingsPath + ".pintumcp.bak");
  const tmp = `${settingsPath}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2) + "\n", "utf-8");
  fs.renameSync(tmp, settingsPath);
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

function sleep(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

// Serialize read-modify-write so two installs can't interleave and corrupt the file.
function withLock(target, fn) {
  const lockPath = target + ".pintumcp.lock";
  const deadline = Date.now() + 5000;
  let fd;
  for (;;) {
    try {
      fd = fs.openSync(lockPath, "wx");
      break;
    } catch (e) {
      if (e.code !== "EEXIST") throw e;
      try {
        if (Date.now() - fs.statSync(lockPath).mtimeMs > 30000) fs.unlinkSync(lockPath); // stale lock
      } catch {}
      if (Date.now() > deadline) throw new Error(`timed out waiting for ${lockPath}`);
      sleep(50);
    }
  }
  try {
    return fn();
  } finally {
    try { fs.closeSync(fd); } catch {}
    try { fs.unlinkSync(lockPath); } catch {}
  }
}

function addHooks(settingsPath, python, hookPath) {
  return withLock(settingsPath, () => {
    const data = load(settingsPath);
    strip(data);
    data.hooks = data.hooks || {};
    for (const event of EVENTS) {
      data.hooks[event] = data.hooks[event] || [];
      data.hooks[event].push({ hooks: [{ type: "command", command: `"${python}" "${hookPath}" ${event}` }] });
    }
    save(settingsPath, data);
  });
}

function removeHooks(settingsPath) {
  if (!fs.existsSync(settingsPath)) return false;
  return withLock(settingsPath, () => {
    const data = load(settingsPath);
    const before = JSON.stringify(data);
    strip(data);
    if (JSON.stringify(data) === before) return false;
    save(settingsPath, data);
    return true;
  });
}

// pintumcp's hooks currently in the file, for `pintumcp hooks status`.
function listHooks(settingsPath) {
  const data = load(settingsPath);
  const found = [];
  for (const [event, groups] of Object.entries(data.hooks || {})) {
    for (const group of groups) {
      for (const h of group.hooks || []) {
        if (isOurs(h)) found.push({ event, command: h.command });
      }
    }
  }
  return found;
}

module.exports = { addHooks, removeHooks, listHooks, EVENTS };
