"""macOS menu-bar app: every agent and its status, with Pintu's face.

Run: python tray.py   (or `npx pintumcp tray`)
It only reads the files the MCP server writes (see status.py); nothing is sent anywhere.
"""

import subprocess
from pathlib import Path

import status

ICONS = Path(__file__).parent / "assets" / "menubar"
SIZE = (18, 16)  # points; the PNGs are exactly 2x
NEEDS_YOU = ("approval", "error", "question")


def icon_for(state: str) -> str:
    path = ICONS / f"{state}.png"
    return str(path if path.exists() else ICONS / "empty.png")


def bar_state(items: list[dict]) -> tuple[str, str]:
    """Icon state and badge text for the menu bar: the most urgent agent, and how many need you."""
    if not items:
        return "empty", ""
    waiting = sum(1 for i in items if i["state"] in NEEDS_YOU)
    return items[0]["state"], str(waiting) if waiting else ""


def main() -> None:
    import rumps

    app = rumps.App("pintumcp", icon=icon_for("empty"), template=False, quit_button=None)
    shown = {"signature": None}

    def focus(app_id):
        def callback(_):
            if app_id:
                subprocess.run(["open", "-b", app_id], check=False)
        return callback

    def clear(_):
        status.clear_finished()

    def refresh(_):
        items = status.snapshot()
        rows = [(status.describe(i), i.get("app")) for i in items]
        signature = tuple((r["name"], r["status"], r["message"], r["state"]) for r, _ in rows)
        if signature == shown["signature"]:
            return  # rebuilding every second would close an open menu
        shown["signature"] = signature
        state, badge = bar_state(items)
        app.icon, app.title = icon_for(state), badge
        menu = [rumps.MenuItem(f"pintumcp: {len(rows)} agent{'s' if len(rows) != 1 else ''}"
                               if rows else "pintumcp: no agents yet"), None]
        for row, app_id in rows:
            menu.append(rumps.MenuItem(f"{row['name']}: {row['status']}", callback=focus(app_id),
                                       icon=icon_for(row["state"]), dimensions=SIZE))
            if row["message"]:
                menu.append(rumps.MenuItem(f"      {row['message']}"))
        menu += [None, rumps.MenuItem("Clear finished", callback=clear),
                 rumps.MenuItem("Quit", callback=rumps.quit_application)]
        app.menu.clear()
        app.menu = menu

    rumps.Timer(refresh, 1).start()
    app.run()


if __name__ == "__main__":
    main()
