"""macOS menu-bar app: a dashboard of every agent and its status, with Pintu's face.

Run: python tray.py   (or `npx pintumcp tray`)
Click Pintu in the menu bar to open the panel. It only reads the files the MCP server
writes (see status.py); nothing is sent anywhere.
"""

import json
import random
import subprocess
import time
from pathlib import Path

import status

HERE = Path(__file__).parent
ICONS = HERE / "assets" / "menubar"
SIZE = (18, 16)  # points; the PNGs are exactly 2x
NEEDS_YOU = ("approval", "error", "question")
WIDTH = 380


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


# Short lines Pintu mutters next to his icon (kept tiny: menu-bar space is precious).
QUIPS = {
    "working": ["on it", "typing...", "brb, coding", "beep boop", "cooking", "no peeking", "in the zone", "hold my coffee", "compiling vibes", "big brain time"],
    "approval": ["psst!", "ahem...", "need a yes", "your call", "pls approve", "pretty please?"],
    "question": ["quick q!", "thoughts?", "help me out", "hello??", "got a sec?"],
    "error": ["oh no", "it's fine", "ow.", "whoopsie", "not my fault", "send snacks"],
    "done": ["ta-da!", "nailed it", "done & dusted", "too easy", "gg", "boom"],
    "empty": ["zzz", "vibing", "so quiet", "wake me", "any work?", "snack time?", "la la la", "*knits*"],
    "idle": ["zzz", "chillin", "all good", "still here", "waiting...", "*yawn*"],
}
QUIP_SECONDS = 5


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
            self.hiding = False
            self.images, self.shown, self.title, self.badge = {}, None, None, ""
            self.quip, self.quip_until, self.quip_next = "", 0.0, 0.0
            bar = NSStatusBar.systemStatusBar()
            self.item = bar.statusItemWithLength_(NSVariableStatusItemLength)
            self.item.button().setTarget_(self)
            self.item.button().setAction_("toggle:")
            self.item.button().sendActionOn_(1 << 1)  # fire on mouse-down

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
            self.win.setHidesOnDeactivate_(False)  # NSPanel hides when its (accessory) app is inactive, which is always
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

        @objc.python_method
        def image(self, path):
            if path not in self.images:  # load each frame once, not every 0.4s
                img = NSImage.alloc().initWithContentsOfFile_(path)
                img.setSize_(SIZE)
                self.images[path] = img
            return self.images[path]

        @objc.python_method
        def set_title(self):
            now = time.time()
            if now >= self.quip_next:
                self.quip, self.quip_until = random.choice(QUIPS.get(self.state, QUIPS["idle"])), now + QUIP_SECONDS
                self.quip_next = now + random.uniform(20, 35)
            quip = self.quip if now < self.quip_until else ""
            title = " ".join(x for x in (self.badge, quip) if x)
            if title != self.title:
                self.title = title
                self.item.button().setTitle_(" " + title if title else "")

        def animate_(self, _timer):
            self.frame += 1
            path = frame_for(self.state, self.frame)
            if path != self.shown:
                self.shown = path
                self.item.button().setImage_(self.image(path))
            self.set_title()

        # ---- panel
        def toggle_(self, _sender):
            self.hide() if self.win.isVisible() else self.show()

        @objc.python_method
        def show(self):
            frame = self.item.button().window().frame()
            screen = NSScreen.mainScreen().frame()
            x = min(max(frame.origin.x + frame.size.width / 2 - WIDTH / 2, 8), screen.size.width - WIDTH - 8)
            self.win.setFrame_display_(NSMakeRect(x, frame.origin.y - self.height - 6, WIDTH, self.height), True)
            self.hiding = False
            self.shown_at = time.time()
            self.web.evaluateJavaScript_completionHandler_("window.opening && window.opening()", None)
            self.push()
            self.win.makeKeyAndOrderFront_(None)

        @objc.python_method
        def hide(self):
            if not self.win.isVisible() or self.hiding:
                return
            self.hiding = True
            self.web.evaluateJavaScript_completionHandler_("window.closing && window.closing()", None)
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.16, self, "finish:", None, False)

        def finish_(self, _timer):
            if self.hiding:
                self.hiding = False
                self.win.orderOut_(None)
                self.web.evaluateJavaScript_completionHandler_("window.setActive && window.setActive(false)", None)

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
                changed = state != self.state
                self.last_icon = (state, badge)
                self.state, self.badge = state, badge
                if changed:
                    self.quip_next = 0.0  # say something about the new mood right away
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
