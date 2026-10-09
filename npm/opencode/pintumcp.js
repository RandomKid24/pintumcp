// Pintu alerts for OpenCode: notify when a session goes idle (agent replied) or needs permission.
import fs from "node:fs"
import os from "node:os"
import path from "node:path"

const cfg = path.join(os.homedir(), ".config/opencode/opencode.json")
const [python, server] = JSON.parse(fs.readFileSync(cfg, "utf-8")).mcp.pintumcp.command

const EVENTS = {
  "session.idle": ["done", "Finished responding"],
  "permission.asked": ["approval", "Needs your approval"],
  "permission.updated": ["approval", "Needs your approval"],
}

export const Pintumcp = async ({ directory }) => ({
  event: async ({ event }) => {
    const hit = EVENTS[event.type]
    if (!hit) return
    const code = "import events,sys;events.deliver_event(sys.argv[1],sys.argv[2],80,sys.argv[3],'OpenCode')"
    Bun.spawn([python, "-c", code, hit[0], hit[1], path.basename(directory)], { cwd: path.dirname(server) })
  },
})
