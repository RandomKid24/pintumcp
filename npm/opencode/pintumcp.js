// Pintu for OpenCode — keeps the status board live (working / needs approval / done / gone) and sends alerts.
//
// Ships as one file that speaks both plugin APIs:
//   • OpenCode v2 loads the `default` export and calls `setup(ctx)`.
//   • OpenCode v1 (>= 1.18.29) loads the `server` hook on the same default export.
//
// The installer writes `pintumcp.runtime.json` next to this file with the Python
// and server.py paths. If that file is missing (e.g. the plugin was copied by
// hand) we fall back to the OpenCode MCP config, accepting both the v1
// (`mcp.<name>`) and v2 (`mcp.servers.<name>`) shapes.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

function locate() {
  try {
    const here = path.dirname(fileURLToPath(import.meta.url));
    const runtime = JSON.parse(fs.readFileSync(path.join(here, "pintumcp.runtime.json"), "utf-8"));
    if (runtime.python && runtime.server) return runtime;
  } catch {}
  try {
    const cfg = JSON.parse(fs.readFileSync(path.join(os.homedir(), ".config", "opencode", "opencode.json"), "utf-8"));
    const mcp = cfg.mcp ?? {};
    const entry = mcp.pintumcp ?? mcp.servers?.pintumcp;
    if (entry?.command) return { python: entry.command[0], server: entry.command[1] };
  } catch {}
  return null;
}

// Runs inside the Pintu Python runtime: update the board row and, for alerts, deliver a popup.
const BRIDGE = `
import sys, status
state, message, project, agent, pid, alert = sys.argv[1:7]
if state == "gone":
    status.remove(project, agent)
else:
    status.update(state, message, project, agent, pid=int(pid))
    if alert == "1":
        import events
        events.deliver(state, message, project, agent)
`;

// A few words for what a tool call is doing.
function toolLine(name, input) {
  input = input ?? {};
  const file = path.basename(String(input.filePath ?? input.path ?? ""));
  switch (name) {
    case "edit": case "write": case "patch": return file ? `Editing ${file}` : "Editing files";
    case "read": return file ? `Reading ${file}` : "Reading files";
    case "shell": case "bash": return `Running: ${String(input.command ?? "").replace(/\s+/g, " ").slice(0, 48)}`;
    case "grep": case "glob": case "list": return `Searching: ${String(input.pattern ?? "").slice(0, 48)}`;
    case "webfetch": case "websearch": return "Browsing the web";
    default: return name ? String(name).replace(/[_-]/g, " ") : "Working on your request";
  }
}

function launch(cmd, args, cwd) {
  try {
    if (typeof Bun !== "undefined" && typeof Bun.spawn === "function") {
      // detached + unref so a final alert still lands if OpenCode exits right after
      Bun.spawn([cmd, ...args], { cwd, detached: true, stdin: "ignore", stdout: "ignore", stderr: "ignore" }).unref?.();
      return;
    }
  } catch {}
  try {
    spawn(cmd, args, { cwd, detached: true, stdio: "ignore" }).unref();
  } catch {}
}

// One reporter per OpenCode process/directory: remembers the last row so Python
// only spawns on a real change (alerts always fire).
function makeReporter(directory) {
  const runtime = locate();
  const last = new Map();
  return (session, state, message, alert) => {
    if (!runtime) return;
    const key = String(session ?? "main");
    if (!alert && last.get(key) === state + message) return;
    last.set(key, state + message);
    const agent = "OpenCode " + key.slice(-4);
    launch(runtime.python,
      ["-c", BRIDGE, state, message, path.basename(directory || ""), agent, String(process.pid), alert ? "1" : "0"],
      path.dirname(runtime.server));
  };
}

// ── OpenCode v2 (Promise plugin API) ────────────────────────────────────────
const v2 = {
  id: "pintumcp",
  async setup(ctx) {
    const report = makeReporter(ctx?.location?.directory);
    const controller = new AbortController();
    const toolNames = new Map(); // tool-call id -> tool name (v2 splits name and input)

    const handle = (event) => {
      const data = event?.data ?? {};
      const session = data.sessionID ?? data.form?.sessionID ?? data.info?.id ?? data.info?.sessionID ?? "main";
      switch (event.type) {
        case "session.execution.succeeded":
        case "session.idle":
          return report(session, "done", "Finished responding", true);
        case "session.execution.failed":
          return report(session, "error", data.error?.message ?? "Something went wrong", true);
        case "permission.asked":
          return report(session, "approval", "Needs your approval", true);
        case "permission.replied":
          return report(session, "working", "Working on your request", false);
        case "form.created":
          return report(session, "question", "Needs your input", true);
        case "form.replied":
        case "form.cancelled":
          return report(session, "working", "Working on your request", false);
        case "session.deleted":
          return report(session, "gone", "", false);
        case "session.execution.started":
          return report(session, "working", "Working on your request", false);
        case "session.status":
          if (data.status?.type === "busy") report(session, "working", "Working on your request", false);
          return;
        case "session.tool.input.started":
          toolNames.set(data.id, data.name); // remember the name; `called` carries the input
          return;
        case "session.tool.called":
          return report(session, "working", toolLine(toolNames.get(data.id) ?? data.name, data.input), false);
        default:
          return;
      }
    };

    (async () => {
      try {
        for await (const event of ctx.event.subscribe({ signal: controller.signal })) handle(event);
      } catch {}
    })();

    return () => controller.abort();
  },
};

// ── OpenCode v1 (legacy `event` hook) ───────────────────────────────────────
async function server(input) {
  const report = makeReporter(input?.directory);
  const EVENTS = {
    "session.idle": ["done", "Finished responding", true],
    "permission.asked": ["approval", "Needs your approval", true],
    "permission.updated": ["approval", "Needs your approval", true],
    "permission.replied": ["working", "Working on your request", false],
    "session.deleted": ["gone", "", false],
  };
  return {
    event: async ({ event }) => {
      const properties = event?.properties ?? {};
      const session = properties.sessionID ?? properties.info?.id ?? properties.info?.sessionID ?? "main";
      const hit = EVENTS[event.type];
      if (hit) return report(session, hit[0], hit[1], hit[2]);
      if (event.type === "session.status" && properties.status?.type !== "busy") return;
      if (event.type === "session.status" || event.type === "message.part.updated") {
        const part = properties.part;
        report(session, "working", part?.type === "tool" ? toolLine(part.tool, part.state?.input) : "Working on your request", false);
      }
    },
  };
}

export default { ...v2, server };
