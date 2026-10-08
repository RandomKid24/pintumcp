// Run with: node --test tests/configure.test.js
const test = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { removeMcp } = require("../npm/lib/configure");

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "pintumcp-"));

test("removeMcp deletes only pintumcp from a JSON config", () => {
  const file = path.join(tmp(), "settings.json");
  fs.writeFileSync(file, JSON.stringify({ theme: "dark", mcpServers: { pintumcp: {}, other: { command: "x" } } }));
  assert.strictEqual(removeMcp({ configPath: file, format: "json", mcpKey: "mcpServers" }), true);
  assert.deepStrictEqual(JSON.parse(fs.readFileSync(file, "utf-8")), { theme: "dark", mcpServers: { other: { command: "x" } } });
  assert.strictEqual(removeMcp({ configPath: file, format: "json", mcpKey: "mcpServers" }), false);
});

test("removeMcp deletes only the pintumcp table from Codex TOML", () => {
  const file = path.join(tmp(), "config.toml");
  fs.writeFileSync(file, 'model = "x"\n\n[mcp_servers.pintumcp]\ncommand = "p"\n\n[tui]\ntheme = "dark"\n');
  assert.strictEqual(removeMcp({ configPath: file, format: "toml", mcpKey: "mcp_servers" }), true);
  const out = fs.readFileSync(file, "utf-8");
  assert.ok(!out.includes("pintumcp") && out.includes("[tui]") && out.includes('model = "x"'));
});

test("removeMcp leaves an unreadable config untouched", () => {
  const file = path.join(tmp(), "settings.json");
  fs.writeFileSync(file, "{not json");
  assert.strictEqual(removeMcp({ configPath: file, format: "json", mcpKey: "mcpServers" }), false);
  assert.strictEqual(fs.readFileSync(file, "utf-8"), "{not json");
});

const { addHooks, removeHooks } = require("../npm/lib/hooks");

test("addHooks is idempotent, keeps other hooks, and removeHooks restores the rest", () => {
  const file = path.join(tmp(), "settings.json");
  const mine = "/x/pintumcp/npm/python/hook.py";
  const other = { hooks: [{ type: "command", command: "echo mine" }] };
  fs.writeFileSync(file, JSON.stringify({ theme: "dark", hooks: { Stop: [other] } }));

  addHooks(file, "/x/python", mine);
  addHooks(file, "/x/python", mine); // twice: no duplicates
  let data = JSON.parse(fs.readFileSync(file, "utf-8"));
  assert.strictEqual(data.hooks.Stop.length, 2);
  assert.deepStrictEqual(Object.keys(data.hooks).sort(), ["Notification", "Stop", "UserPromptSubmit"]);
  assert.ok(fs.existsSync(file + ".pintumcp.bak"));

  assert.strictEqual(removeHooks(file), true);
  data = JSON.parse(fs.readFileSync(file, "utf-8"));
  assert.deepStrictEqual(data, { theme: "dark", hooks: { Stop: [other] } });
  assert.strictEqual(removeHooks(file), false);
});
