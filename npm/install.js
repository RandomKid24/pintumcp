#!/usr/bin/env node

/**
 * npm postinstall script.
 * Runs `pintumcp install` automatically after npm install -g pintumcp.
 */

const { execSync } = require("child_process");
const path = require("path");

const cliPath = path.join(__dirname, "bin", "pintumcp.js");

try {
  execSync(`node "${cliPath}" install`, { stdio: "inherit" });
} catch {
  // Postinstall failures shouldn't block npm install
  console.log("\n[pintumcp] Auto-setup had issues. Run `npx pintumcp install` manually.\n");
}