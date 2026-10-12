// Run with: node --test tests/opencode_plugin.test.js
const test = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { pathToFileURL } = require("url");

const PLUGIN = path.join(__dirname, "..", "npm", "opencode", "pintumcp.js");

test("OpenCode plugin exports one default that speaks both the v1 and v2 APIs", async () => {
  // The plugin is ESM, but the package is CommonJS, so load it through a .mjs copy.
  const tmp = path.join(os.tmpdir(), `pintumcp-plugin-${process.pid}.mjs`);
  fs.copyFileSync(PLUGIN, tmp);
  try {
    const mod = await import(pathToFileURL(tmp).href);
    assert.strictEqual(mod.default.id, "pintumcp", "v2 needs a stable plugin id");
    assert.strictEqual(typeof mod.default.setup, "function", "v2 calls setup(ctx)");
    assert.strictEqual(typeof mod.default.server, "function", "v1 calls the server hook");
  } finally {
    fs.rmSync(tmp, { force: true });
  }
});
