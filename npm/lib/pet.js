// Animated terminal pet: renders npm/lib/pet.json with half-block characters.
const pet = require("./pet.json");

function render(name) {
  const rows = pet.frames[name];
  const pal = { ...pet.palette, ...(pet.tints || {})[name] };
  const fg = (c) => `\x1b[38;2;${pal[c].join(";")}m`;
  const bg = (c) => `\x1b[48;2;${pal[c].join(";")}m`;
  const lines = [];
  for (let y = 0; y < rows.length; y += 2) {
    let line = "  ";
    for (let x = 0; x < rows[y].length; x++) {
      const top = rows[y][x], bot = rows[y + 1][x];
      if (top === "." && bot === ".") line += " ";
      else if (bot === ".") line += `${fg(top)}▀\x1b[0m`;
      else if (top === ".") line += `${fg(bot)}▄\x1b[0m`;
      else line += `${fg(top)}${bg(bot)}▀\x1b[0m`;
    }
    lines.push(line);
  }
  return lines;
}

const sleep = (ms) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);

// Waves in place for a moment, then leaves the idle pose on screen.
// Skipped when output is not a terminal (pipes, CI) so logs stay clean.
function playPet() {
  if (!process.stdout.isTTY || process.env.NO_COLOR) return;
  const height = render("idle").length;
  console.log("\n".repeat(height));
  for (const name of [...pet.sequence, "idle"]) {
    process.stdout.write(`\x1b[${height}A` + render(name).join("\n") + "\n");
    sleep(pet.delay_ms);
  }
}

// Static pose (done / question / approval / error) after a result, e.g. doctor.
function showPose(name) {
  if (!process.stdout.isTTY || process.env.NO_COLOR) return;
  console.log(render(name).join("\n"));
}

module.exports = { playPet, showPose, render };
