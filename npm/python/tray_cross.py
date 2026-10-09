"""Windows/Linux tray: Pintu's animated icon in the system tray, with the same dashboard in an app window.

Run: python tray_cross.py   (or `npx pintumcp tray`)
Left-click the icon (or pick "Open Pintu") to open the panel. Everything stays on this machine:
a tiny server on 127.0.0.1 serves panel.html and the status files the MCP server writes.
"""

import json
import os
import random
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pystray
from PIL import Image

import status
import tray  # constants and payload() only; its macOS code lives inside main()

HERE = Path(__file__).parent
SERVER_PORT = 0  # chosen at start
POPUP = None  # Windows: the borderless popup (winpopup.Popup)
TOKEN = f"{random.getrandbits(64):x}"  # other local pages can't poke the server without it
ACTIONS = {"clear": lambda: status.clear_finished(),
           "mute": lambda: status.set_mute(0 if status.muted_until() else 3600), "doctor": lambda: __import__("events").deliver_event(
    "done", "Test alert from the tray", 40, "pintumcp", "tray")}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, body: bytes, kind: str, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/state":
            return self._send(json.dumps(tray.payload()).encode(), "application/json")
        rel = "panel.html" if url.path in ("/", "") else url.path.lstrip("/")
        target = (HERE / rel).resolve()
        if HERE not in target.parents or not target.is_file() or target.suffix not in (".html", ".png", ".gif", ".js"):
            return self._send(b"not found", "text/plain", 404)
        kind = {".html": "text/html", ".png": "image/png", ".gif": "image/gif", ".js": "text/javascript"}[target.suffix]
        self._send(target.read_bytes(), kind)

    def do_POST(self):
        url = urlparse(self.path)
        name = url.path.lstrip("/").removeprefix("act/")
        if TOKEN not in url.query:
            return self._send(b"forbidden", "text/plain", 403)
        if name == "quit":
            self._send(b"ok", "text/plain")
            return os._exit(0)
        if name == "size" and POPUP:
            POPUP.resize(int(parse_qs(url.query).get("h", ["720"])[0]))
        if name in ACTIONS:
            ACTIONS[name]()
        self._send(b"ok", "text/plain")


def browser_app_command(url: str):
    """Chrome/Edge in app mode (a bare window, no tabs), if one is installed."""
    names = ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser", "microsoft-edge")
    candidates = [shutil.which(n) for n in names]
    if sys.platform == "win32":
        for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
            if base:
                candidates += [os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"),
                               os.path.join(base, "Google", "Chrome", "Application", "chrome.exe")]
    exe = next((c for c in candidates if c and os.path.exists(c)), None)
    return [exe, f"--app={url}", "--window-size=400,720"] if exe else None


def open_panel():
    url = f"http://127.0.0.1:{SERVER_PORT}/?live&t={TOKEN}"
    command = browser_app_command(url)
    if POPUP:
        return POPUP.toggle()
    if command:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        webbrowser.open(url)


def icon_image(path: str) -> Image.Image:
    return Image.open(path).convert("RGBA").resize((72, 64), Image.NEAREST)


def main():
    global SERVER_PORT
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    SERVER_PORT = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    if sys.platform == "win32":
        global POPUP
        import winpopup
        url = f"http://127.0.0.1:{SERVER_PORT}/?live&t={TOKEN}"
        command = browser_app_command(url)
        if command:
            command += [f"--user-data-dir={status.root() / 'edge-profile'}", "--no-first-run", "--no-default-browser-check"]
            POPUP = winpopup.Popup(url, command)

    menu = pystray.Menu(
        pystray.MenuItem("Open Pintu", lambda: open_panel(), default=True),
        pystray.MenuItem("Mute for 1 hour", lambda: ACTIONS["mute"]()),
        pystray.MenuItem("Clear finished", lambda: status.clear_finished()),
        pystray.MenuItem("Send test alert", lambda: ACTIONS["doctor"]()),
        pystray.MenuItem("Quit", lambda icon: (icon.stop(), os._exit(0))),
    )
    icon = pystray.Icon("pintumcp", icon_image(tray.frame_for("empty", 0)), "Pintu", menu)

    def animate():
        frame, state, quip_until, quip_next, quip, last, stuck_seen = 0, "empty", 0.0, 0.0, "", None, set()
        while True:
            time.sleep(0.4)
            frame += 1
            try:
                items = status.snapshot()
                tray.stuck_alerts(items, stuck_seen)
                new_state, badge = tray.bar_state(items)
                if status.muted_until() and new_state in ("empty", "idle", "done"):
                    new_state = "muted"
                if new_state != state:
                    state, quip_next = new_state, 0.0
                now = time.time()
                if now >= quip_next:
                    quip, quip_until = random.choice(tray.QUIPS.get(state, tray.QUIPS["idle"])), now + tray.QUIP_SECONDS
                    quip_next = now + random.uniform(20, 35)
                path = tray.frame_for(state, frame)
                if path != last:
                    last = path
                    icon.icon = icon_image(path)
                waiting = f"{badge} need you" if badge else ""
                icon.title = "Pintu" + "".join(f" - {x}" for x in (waiting, quip if now < quip_until else "") if x)
            except Exception:
                pass  # a bad status file must not kill the tray

    threading.Thread(target=animate, daemon=True).start()
    icon.run()


if __name__ == "__main__":
    main()
