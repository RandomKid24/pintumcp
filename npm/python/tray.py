"""macOS menu-bar app: a dashboard of every agent and its status, with Pintu's face.

Run: python tray.py   (or `npx pintumcp tray`)
Click Pintu in the menu bar to open the panel. It only reads the files the MCP server
writes (see status.py); nothing is sent anywhere.
"""

import json
import subprocess
import time
from pathlib import Path

import status

HERE = Path(__file__).parent
ICONS = HERE / "assets" / "menubar"
SIZE = (18, 16)  # points; the PNGs are exactly 2x
NEEDS_YOU = ("approval", "error", "question")
WIDTH = 520


def frames_for(name: str) -> list:
    return sorted(str(p) for p in ICONS.glob(f"{name}_*.png"))


# With nothing urgent Pintu keeps busy: wave, sweater, coffee, music, nap (one activity every ~6s).
IDLE_ACTIVITIES = ("empty", "sweater", "coffee", "music", "sleep")
TICKS_PER_ACTIVITY = 15  # at 0.4s a frame


def frame_for(state: str, n: int) -> str:
    """Menu-bar image path for animation tick n."""
    name = state
    if state in ("empty", "idle"):
        name = IDLE_ACTIVITIES[(n // TICKS_PER_ACTIVITY) % len(IDLE_ACTIVITIES)]
    frames = frames_for(name) or frames_for("empty")
    return frames[n % len(frames)]


def bar_state(items: list) -> tuple:
    """Icon state and badge text for the menu bar: the most urgent agent, and how many need you."""
    if not items:
        return "empty", ""
    waiting = sum(1 for i in items if i["state"] in NEEDS_YOU)
    return items[0]["state"], str(waiting) if waiting else ""


def agent_key(item: dict) -> str:
    return item["project"] + "|" + item["agent"]


def payload(items: list = None, now: float = None) -> dict:
    """What the panel page renders: agents (most urgent first) and the Today card."""
    items = status.snapshot() if items is None else items
    now = time.time() if now is None else now
    agents = [{"key": agent_key(i), "name": status.describe(i)["name"], "state": i["state"],
               "message": i["message"], "in_state": i["in_state"], "age": i["age"], "stale": i["stale"]}
              for i in items]
    return {"now": now, "agents": agents, "today": status.today_stats(now)}


def main() -> None:
    import objc
    from Cocoa import (NSApplication, NSApplicationActivationPolicyAccessory, NSBackingStoreBuffered, NSColor,
                       NSEvent, NSImage, NSMakeRect, NSObject, NSPanel, NSScreen, NSStatusBar, NSStatusWindowLevel,
                       NSTimer, NSVariableStatusItemLength)
    from Foundation import NSURL
    from WebKit import WKUserContentController, WKWebView, WKWebViewConfiguration

    class Panel(NSPanel):
        def canBecomeKeyWindow(self):  # borderless windows refuse key status by default
            return True

    class App(NSObject, protocols=[objc.protocolNamed("WKScriptMessageHandler")]):
        def applicationDidFinishLaunching_(self, _note):
            self.items = []
            self.height = 600
            self.last_icon = None
            self.shown_at = 0.0
            bar = NSStatusBar.systemStatusBar()
            self.item = bar.statusItemWithLength_(NSVariableStatusItemLength)
            self.item.button().setTarget_(self)
            self.item.button().setAction_("toggle:")

            config = WKWebViewConfiguration.alloc().init()
            controller = WKUserContentController.alloc().init()
            controller.addScriptMessageHandler_name_(self, "pintu")
            config.setUserContentController_(controller)
            self.web = WKWebView.alloc().initWithFrame_configuration_(NSMakeRect(0, 0, WIDTH, self.height), config)
            self.web.setValue_forKey_(False, "drawsBackground")  # let the panel's rounded corners show
            page = HERE / "panel.html"
            self.web.loadFileURL_allowingReadAccessToURL_(NSURL.fileURLWithPath_(str(page)),
                                                          NSURL.fileURLWithPath_(str(HERE)))

            self.win = Panel.alloc().initWithContentRect_styleMask_backing_defer_(
                NSMakeRect(0, 0, WIDTH, self.height), 0, NSBackingStoreBuffered, False)
            self.win.setOpaque_(False)
            self.win.setBackgroundColor_(NSColor.clearColor())
            self.win.setHasShadow_(True)
            self.win.setLevel_(NSStatusWindowLevel)
            self.win.setContentView_(self.web)
            self.win.setReleasedWhenClosed_(False)
            # click anywhere outside the panel to dismiss it
            NSEvent.addGlobalMonitorForEventsMatchingMask_handler_((1 << 1) | (1 << 3), lambda e: time.time() - self.shown_at > 0.4 and self.hide())  # the status-item click itself also reaches this monitor

            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(1.0, self, "tick:", None, True)
            self.frame = 0
            self.state = "empty"
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.4, self, "animate:", None, True)
            self.tick_(None)

        def animate_(self, _timer):
            self.frame += 1
            image = NSImage.alloc().initWithContentsOfFile_(frame_for(self.state, self.frame))
            image.setSize_(SIZE)
            self.item.button().setImage_(image)

        # ---- panel
        def toggle_(self, _sender):
            self.hide() if self.win.isVisible() else self.show()

        @objc.python_method
        def show(self):
            frame = self.item.button().window().frame()
            screen = NSScreen.mainScreen().frame()
            x = min(max(frame.origin.x + frame.size.width / 2 - WIDTH / 2, 8), screen.size.width - WIDTH - 8)
            self.win.setFrame_display_(NSMakeRect(x, frame.origin.y - self.height - 6, WIDTH, self.height), True)
            self.shown_at = time.time()
            self.push()
            self.win.makeKeyAndOrderFront_(None)

        @objc.python_method
        def hide(self):
            self.win.orderOut_(None)

        @objc.python_method
        def resize(self, height):
            self.height = max(200, min(int(height), 820))
            if self.win.isVisible():
                top = self.win.frame().origin.y + self.win.frame().size.height
                self.win.setFrame_display_(NSMakeRect(self.win.frame().origin.x, top - self.height, WIDTH, self.height), True)
                self.win.invalidateShadow()

        # ---- data
        @objc.python_method
        def push(self):
            self.web.evaluateJavaScript_completionHandler_(
                "window.render && window.render(" + json.dumps(payload(self.items)) + ")", None)

        def tick_(self, _timer):
            self.items = status.snapshot()
            state, badge = bar_state(self.items)
            if (state, badge) != self.last_icon:
                self.last_icon = (state, badge)
                self.state = state
                self.item.button().setTitle_(" " + badge if badge else "")
                self.animate_(None)
            if self.win.isVisible():
                self.push()

        # ---- messages from the page
        def userContentController_didReceiveScriptMessage_(self, _controller, message):
            body = message.body()
            kind = body.get("type")
            if kind == "size":
                self.resize(body.get("height", self.height))
            elif kind == "focus":
                for item in self.items:
                    if agent_key(item) == body.get("key") and item.get("app"):
                        subprocess.run(["open", "-b", item["app"]], check=False)
                        self.hide()
            elif kind == "clear":
                status.clear_finished()
                self.tick_(None)
            elif kind == "doctor":
                import events
                events.deliver_event("done", "Test alert from the menu bar", 40, "pintumcp", "menu bar")
            elif kind == "quit":
                NSApplication.sharedApplication().terminate_(None)

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)  # no Dock icon
    delegate = App.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
