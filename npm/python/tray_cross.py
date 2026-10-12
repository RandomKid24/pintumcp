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

try:
    import pystray
    from PIL import Image
except Exception:  # no usable tray (headless or missing libraries): the panel still opens in a window
    pystray = None

import status
import tray  # constants and payload() only; its macOS code lives inside main()

HERE = Path(__file__).parent
SERVER_PORT = 0  # chosen at start
POPUP = None  # Windows: the borderless popup (winpopup.Popup)
TOKEN = f"{random.getrandbits(64):x}"  # other local pages can't poke the server without it
ACTIONS = {"clear": lambda: status.clear_finished(),
           "break": lambda: status.end_break() if status.progress()["break_until"] else status.start_break(5),
           "update": lambda: tray.run_update(),
           "remove_stale": lambda: [status.remove(i["project"], i["agent"]) for i in status.snapshot() if i.get("stale")],
           "mute": lambda: status.set_mute(0 if status.muted_until() else __import__("config").get("mute_minutes", 60) * 60), "doctor": lambda: __import__("events").deliver_event(
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
        if name == "settings":
            import config
            config.save_user(json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}"))
        if name == "remove":
            key = parse_qs(url.query).get("key", [""])[0]
            for item in status.snapshot():
                if tray.agent_key(item) == key:
                    status.remove(item["project"], item["agent"])
        if name == "size" and POPUP:
            q = parse_qs(url.query)
            POPUP.resize(int(q.get("h", ["720"])[0]), int(q.get("w", ["0"])[0]))
        if name in ACTIONS:
            ACTIONS[name]()
        self._send(b"ok", "text/plain")


TOAST_SECONDS = 6


def screen_width() -> int:
    try:
        out = subprocess.run(["xrandr", "--current"], capture_output=True, text=True, timeout=2).stdout
        return int(next(l for l in out.splitlines() if "*" in l).split()[0].split("x")[0])
    except Exception:
        return 1920


def show_toast(toast: dict) -> None:
    """Linux: Pintu's animated popup in a small Chromium app window; a plain notify-send if there is none."""
    from urllib.parse import quote
    url = f"http://127.0.0.1:{SERVER_PORT}/toast.html?t={quote(json.dumps(toast))}"
    command = browser_app_command(url)
    if command:
        # own profile = own process, so we can close exactly this window; x is the top-right corner (ignored on pure Wayland)
        command = command[:2] + ["--window-size=380,100", f"--window-position={max(0, screen_width() - 400)},40",
                                 f"--user-data-dir={status.root() / 'toast-profile'}", "--no-first-run", "--no-default-browser-check"]
        proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        threading.Timer(TOAST_SECONDS, proc.terminate).start()
        return
    import notifier
    face = notifier.ICON_DIR / "faces" / f"{toast.get('face')}.png"
    notifier._linux_notify(toast.get("title", ""), toast.get("message", ""), face if face.exists() else notifier.ICON_PATH)


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


def icon_image(path: str):
    return Image.open(path).convert("RGBA").resize((72, 64), Image.NEAREST)


INSTANCE = status.root() / "tray_cross.json"  # who is running: {"pid", "port", "token"}


def running_instance():
    try:
        info = json.loads(INSTANCE.read_text())
        return info if info["pid"] != os.getpid() and status.pid_alive(info["pid"]) else None
    except (OSError, ValueError, KeyError):
        return None


def main():
    global SERVER_PORT, TOKEN
    other = running_instance()
    if other:  # one Pintu per user: a second launch (e.g. the app-menu entry) just opens the panel of the first
        if "--open" in sys.argv:
            url = f"http://127.0.0.1:{other['port']}/?live&t={other['token']}"
            command = browser_app_command(url)
            subprocess.Popen(command) if command else webbrowser.open(url)
        return
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    SERVER_PORT = server.server_address[1]
    INSTANCE.write_text(json.dumps({"pid": os.getpid(), "port": SERVER_PORT, "token": TOKEN}))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    window = None
    if sys.platform == "win32":
        global POPUP
        import winpopup
        url = f"http://127.0.0.1:{SERVER_PORT}/?live&t={TOKEN}"
        try:  # preferred: a frameless native window, so it never looks like a browser
            import webview
            window = webview.create_window("Pintu panel", url, width=400, height=720, x=-4000, y=-4000, frameless=True,
                                           on_top=True, easy_drag=False, resizable=False, background_color="#000000")
            POPUP = winpopup.WebviewPopup(url)
        except Exception:
            window = None
            command = browser_app_command(url)  # fallback: Edge/Chrome in app mode, restyled with Win32
            if command:
                command += [f"--user-data-dir={status.root() / 'edge-profile'}", "--no-first-run", "--no-default-browser-check"]
                POPUP = winpopup.Popup(url, command)

    if pystray is None:
        print("pintumcp: no system tray available; opening the panel window instead", file=sys.stderr)
        open_panel()
        threading.Event().wait()  # keep serving
        return
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
                tray.housekeeping()
                if sys.platform.startswith("linux"):
                    for toast in status.take_toasts()[-1:]:  # only the newest, never a pile of windows
                        show_toast(toast)
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
    if sys.platform.startswith("linux") and ("--open" in sys.argv or type(icon).__module__.endswith("_xorg")):
        # --open: launched from the app menu. The xorg backend means GNOME has no tray for us: show the panel so Pintu is still reachable.
        threading.Timer(1.5, open_panel).start()
    if window is not None:  # pywebview needs the main thread; the tray icon runs beside it
        import webview
        icon.run_detached()
        webview.start(POPUP.adopt)
        os._exit(0)
    icon.run()


if __name__ == "__main__":
    main()
