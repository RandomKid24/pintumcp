// Pintu as pixel art on a 22x20 grid. Shared by the dashboard panel and the alert popup.
const S = 6;
const PC = {body: "#48d6be", shade: "#28a096", eye: "#101634", white: "#fff", yel: "#ffb830", stem: "#96aac8", red: "#ff7878", redShade: "#d25a5a",
            sweater: "#ff6b50", cream: "#ffe296", steam: "#bec8dc", gray: "#5a6272", dark: "#3a4150", glow: "#9ad8ff"};

function drawPet(pctx, mode, now, pet) {
  const frame = Math.floor(now / 350);
  const err = mode === "error", c = (x, y, col, w = 1, h = 1) => { pctx.fillStyle = col; pctx.fillRect(x * S, y * S, w * S, h * S); };
  let dx = 0, dy = 0;
  if (now < pet.jumpUntil) dy = -Math.round(Math.sin((1 - (pet.jumpUntil - now) / 600) * Math.PI) * 3);
  else if (["approval", "question"].includes(mode)) dy = frame % 3 === 0 ? -2 : 0;
  if (err) dx = frame % 2 ? 1 : -1;
  const spin = now < pet.spinUntil;
  pctx.clearRect(0, 0, 132, 120);
  if (spin && frame % 2) { pctx.save(); pctx.translate(132, 0); pctx.scale(-1, 1); }

  // shadow
  pctx.fillStyle = "rgba(255,255,255,.07)"; pctx.fillRect((6 + (dy < -1 ? 1 : 0)) * S, 17 * S, (10 - (dy < -1 ? 2 : 0)) * S, S);
  const bc = err ? PC.red : PC.body, sh = err ? PC.redShade : PC.shade;
  const X = (x) => x + dx, Y = (y) => y + dy;
  const px = (x, y, col, w = 1, h = 1) => c(X(x), Y(y), col, w, h);
  const breathe = Math.floor(now / 700) % 2;                                   // chest rises
  // antenna
  px(10, 3, PC.yel, 2); px(9, 4, PC.yel, 4); px(10, 5, PC.stem, 2);
  if (mode === "working" && frame % 2) px(10, 3, PC.cream, 2);
  // body
  px(5, 6, bc, 12); px(4, 7, bc, 14, 4); px(3, 11, bc, 16, 2); px(4, 13, bc, 14); px(5, 14, sh, 12);
  px(6, 15, bc, 3, 2); px(13, 15, bc, 3, 2);
  if (breathe) px(4, 6, bc);
  // sleeves / arms
  if (mode === "done") { px(2, 9, bc, 1, 2); px(19, 9, bc, 1, 2); px(2, 8, bc); px(19, 8, bc); }
  if (mode === "wave") { px(19, 9, bc, 1, 3); px(20, frame % 2 ? 8 : 9, bc); }
  // sweater
  if (mode === "sweater") {
    px(3, 11, PC.sweater, 16, 2); px(4, 13, PC.sweater, 14);
    for (let x = 3; x < 19; x += 2) px(x, 12, PC.cream);
  }
  // eyes
  const L = 7 + pet.look, R = 13 + pet.look;
  const blinking = now < pet.blinkAt + 140 && now >= pet.blinkAt;
  const eyesFor = (x, left) => {
    if (mode === "nap" || blinking) return [[x, 10], [x + 1, 10]];
    if (err) return left ? [[x, 9], [x + 1, 10], [x + 1, 9]] : [[x + 1, 9], [x, 10], [x, 9]];
    if (pet.hover || mode === "done" || mode === "music" || mode === "party") return [[x, 10], [x + 1, 9], [x + 2, 10]];  // ^ ^
    const e = [[x, 9], [x, 10], [x + 1, 10]]; px(x + 1, 9, PC.white);
    if (["approval", "question"].includes(mode)) e.push([x, 11]);
    if (mode === "working") { return [[x, 10], [x + 1, 10], [x, 9]]; }          // looking down at the keys
    return e;
  };
  [...eyesFor(L, true), ...eyesFor(R, false)].forEach(([x, y]) => px(x, y, PC.eye));
  if (mode === "music") { for (const y of [8, 9, 10]) { px(3, y, PC.eye); px(18, y, PC.eye); } px(4, 6, PC.eye); px(17, 6, PC.eye); px(3, 7, PC.eye); px(18, 7, PC.eye); }
  // mouth
  const talk = now < pet.overrideUntil ? frame % 2 : 0;
  if (err) { px(10, 12, PC.eye, 2); px(9, 13, PC.eye); px(12, 13, PC.eye); }
  else if (["approval", "question"].includes(mode) || talk) { px(10, 12, PC.eye, 2, 2); }
  else if (mode === "nap" || mode === "working") px(10, 13, PC.eye, 2);
  else { px(9, 12, PC.eye); px(12, 12, PC.eye); px(10, 13, PC.eye, 2); }
  // props and effects
  if (mode === "coffee") {
    px(19, 11, PC.white, 2, 3); px(21, 12, PC.white);
    px(frame % 2 ? 20 : 19, 9, PC.steam); px(frame % 2 ? 19 : 20, 10, PC.steam);
  }
  if (mode === "music") { const n = frame % 2; px(17 - n, 3 - n, PC.yel); px(18 - n, 2 - n, PC.yel); px(18 - n, 1 - n, PC.yel); px(16 + n, 5, PC.cream); }
  if (mode === "nap") { const z = frame % 4; px(16, 5, PC.cream); if (z > 0) { px(17, 4, PC.cream, 2); px(18, 3, PC.cream); } if (z > 1) { px(18, 1, PC.cream, 3); px(19, 2, PC.cream); px(18, 3, PC.cream, 3); } }
  if (mode === "working") {
    c(4, 17, PC.gray, 14); c(3, 18, PC.dark, 16);
    for (let i = 0; i < 3; i++) c(5 + ((frame * 3 + i * 5) % 12), 17, PC.cream);
    for (let i = 0; i < 3; i++) if ((frame + i) % 4 !== 3) c(14 + i * 2, 3 + (i % 2), PC.cream);
  }
  if (["approval", "question"].includes(mode)) {
    const col = mode === "approval" ? "#ff8a3d" : PC.yel;
    if (mode === "approval") { px(19, 2, col, 1, 4); px(19, 7, col); }
    else { px(18, 2, col, 3); px(20, 3, col); px(19, 4, col); px(19, 5, col); px(19, 7, col); }
  }
  if (err && frame % 2) px(15, 7, PC.glow);
  if (mode === "done") for (const [x, y] of [[1, 5], [20, 5], [0, 9], [21, 10], [3, 2], [18, 1]]) if ((frame + x) % 3) c(x, y, (frame + y) % 2 ? PC.yel : PC.cream);
  if (mode === "hat") { px(7, 2, PC.dark, 8, 3); px(7, 4, PC.sweater, 8); px(6, 5, PC.dark, 10); }
  if (mode === "glasses") {
    for (const x of [L - 1, R - 1]) { px(x, 8, PC.eye, 4); px(x, 11, PC.eye, 4); px(x, 9, PC.eye, 1, 2); px(x + 3, 9, PC.eye, 1, 2); px(x + 1, 9, PC.glow); }
    px(L + 3, 9, PC.eye, R - L - 4);
  }
  if (mode === "umbrella") {
    px(7, 0, PC.sweater, 8); px(5, 1, PC.sweater, 12); px(4, 2, PC.sweater, 14);
    for (const x of [6, 10, 14]) { px(x, 1, PC.cream); px(x - 1, 2, PC.cream); }
    px(10, 3, PC.stem, 2, 3);
    for (const [x, y] of [[1, 3], [20, 4], [2, 9], [19, 8], [0, 13], [21, 12]]) c(x, ((y + frame * 2) % 15) + 2, PC.glow);
  }
  if (mode === "party") {
    px(10, 0, PC.cream, 2); px(10, 1, PC.sweater, 2); px(9, 2, PC.cream, 4); px(8, 3, PC.sweater, 6);
    for (const [x, y] of [[2, 4], [19, 3], [1, 9], [20, 8], [3, 14], [18, 15]]) if ((frame + x) % 3) c(x, y, [PC.yel, PC.sweater, PC.glow][(x + frame) % 3]);
  }
  if (spin && frame % 2) pctx.restore();
}

let active = true;                                                                        // the page idles while the panel is hidden
window.setActive = (on) => { active = on; };
