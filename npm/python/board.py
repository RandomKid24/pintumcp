"""Pintu in the terminal: the same status board the menu-bar app shows, live in your shell.

Run: pintumcp board        (or: python board.py)
     pintumcp board --once  print one frame and exit (handy for scripts/tmux)

Reads the same ~/.pintumcp/agents files the tray reads; writes nothing.
"""

from __future__ import annotations

import sys
import time

import status

CLEAR = "\x1b[2J\x1b[H"
RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"

COLOR = {
    "approval": "\x1b[95m",
    "error": "\x1b[91m",
    "question": "\x1b[96m",
    "working": "\x1b[93m",
    "done": "\x1b[92m",
    "idle": "\x1b[90m",
}
FACE = {
    "approval": "(!)",
    "error": "(x)",
    "question": "(?)",
    "working": "(~)",
    "done": "(ok)",
    "idle": "(z)",
}


def render(items: list[dict], color: bool = True) -> str:
    if not color:
        global RESET, BOLD, DIM, COLOR
        RESET = BOLD = DIM = ""
        COLOR = {}
    lines = [f"{BOLD}Pintu{RESET}  {DIM}{len(items)} agent(s){RESET}", ""]
    if not items:
        lines.append(f"{DIM}  Nothing running yet — start an agent and it shows up here.{RESET}")
    for item in items:
        row = status.describe(item)
        tint = COLOR.get(row["state"], "")
        lines.append(f"  {tint}{FACE.get(row['state'], '(?)')} {row['status']}{RESET}  {BOLD}{row['name']}{RESET}")
        if row["message"]:
            lines.append(f"      {DIM}{row['message']}{RESET}")
    lines.append("")
    lines.append(f"{DIM}  Ctrl+C to quit{RESET}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    once = "--once" in argv
    color = sys.stdout.isatty() and "--no-color" not in argv
    try:
        while True:
            frame = render(status.snapshot(), color)
            sys.stdout.write((("\n" if once else CLEAR) + frame + "\n"))
            sys.stdout.flush()
            if once:
                return 0
            time.sleep(1)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
