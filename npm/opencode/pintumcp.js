// Pintu for OpenCode: keeps the status board live (working / needs approval / done / gone) and sends alerts.
import fs from "node:fs"
import os from "node:os"
import path from "node:path"

const cfg = path.join(os.homedir(), ".config/opencode/opencode.json")
const [python, server] = JSON.parse(fs.readFileSync(cfg, "utf-8")).mcp.pintumcp.command

// event -> [state, message, alert?]. The board row belongs to this OpenCode process, so it vanishes when OpenCode exits.
const EVENTS = {
  "session.idle": ["done", "Finished responding", true],
  "permission.asked": ["approval", "Needs your approval", true],
  "permission.updated": ["approval", "Needs your approval", true],
  "permission.replied": ["working", "Working on your request", false],
  "session.deleted": ["gone", "", false],
}
const BUSY = new Set(["session.status", "message.part.updated"])  // the agent is doing something
const toolLine = (part) => {                                          // what a tool call is doing, in a few words
  const input = part?.state?.input ?? {}, name = part?.tool ?? ""
  const file = path.basename(String(input.filePath ?? input.path ?? ""))
  if (["edit", "write", "patch"].includes(name)) return file ? `Editing ${file}` : "Editing files"
  if (name === "read") return file ? `Reading ${file}` : "Reading files"
  if (name === "bash") return `Running: ${String(input.command ?? "").replace(/\s+/g, " ").slice(0, 48)}`
  if (["grep", "glob", "list"].includes(name)) return `Searching: ${String(input.pattern ?? "").slice(0, 48)}`
  if (name === "webfetch") return "Browsing the web"
  return name ? name.replace(/_/g, " ") : "Working on your request"
}
const CODE = `
import sys, status
state, message, project, agent, pid, alert = sys.argv[1:7]
if state == "gone":
    status.remove(project, agent)
else:
    status.update(state, message, project, agent, pid=int(pid))
    if alert == "1":
        import events
        events.deliver_event(state, message, 80, project, agent)
`

export const Pintumcp = async ({ directory }) => {
  const last = new Map()  // session -> last state we reported, so we only spawn Python on a change
  const report = (session, state, message, alert) => {
    if (last.get(session) === state + message && !alert) return
    last.set(session, state + message)
    const agent = "OpenCode " + String(session).slice(-4)
    Bun.spawn([python, "-c", CODE, state, message, path.basename(directory), agent, String(process.pid), alert ? "1" : "0"],
      { cwd: path.dirname(server) })
  }
  return {
    event: async ({ event }) => {
      const session = event.properties?.sessionID ?? event.properties?.info?.id ?? event.properties?.info?.sessionID ?? "main"
      const hit = EVENTS[event.type]
      if (hit) return report(session, hit[0], hit[1], hit[2])
      if (BUSY.has(event.type) && (event.type !== "session.status" || event.properties?.status?.type === "busy"))
        report(session, "working", event.properties?.part?.type === "tool" ? toolLine(event.properties.part) : "Working on your request", false)
    },
  }
}
