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
TOAST_W, TOAST_H, TOAST_SECONDS = 360, 92, 5.5


def frames_for(name: str) -> list:
    return sorted(str(p) for p in ICONS.glob(f"{name}_*.png"))


# With nothing urgent Pintu keeps busy: wave, sweater, coffee, music, nap (one activity every ~6s).
IDLE_ACTIVITIES = ("empty", "sweater", "coffee", "music", "sleep", "hat", "glasses", "umbrella", "party")
TICKS_PER_ACTIVITY = 15  # at 0.4s a frame


def frame_for(state: str, n: int) -> str:
    """Menu-bar image path for animation tick n."""
    name = "sleep" if state == "muted" else state
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
    "muted": ["shh", "muted", "zzz", "dnd", "quiet mode"],
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
               "message": i["message"], "in_state": i["in_state"], "age": i["age"], "stale": i["stale"], "took": i.get("took")}
              for i in items]
    return {"now": now, "agents": agents, "today": status.today_stats(now), "muted_until": status.muted_until()}


def stuck_alerts(items: list, seen: set) -> None:
    """One heads-up per agent that went quiet while "working"; forgotten again once it moves on."""
    stale = {agent_key(i): i for i in items if i.get("stale")}
    seen &= set(stale)
    for key, item in stale.items():
        if key not in seen:
            seen.add(key)
            try:
                import events
                name = status.describe(item)["name"]
                events.deliver_event("stuck", f"{name} has been quiet for {int(item['age'] // 60)} min. Maybe stuck?",
                                     80, item.get("project") or None, item.get("agent") or None)
            except Exception:
                pass  # an alert failing must never stop the tray


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
            self.stuck_seen, self.toast_until, self.toast_app = set(), 0.0, None
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

            # the animated alert popup: a small transparent window at the top-right of the screen
            tconfig = WKWebViewConfiguration.alloc().init()
            tcontroller = WKUserContentController.alloc().init()
            tcontroller.addScriptMessageHandler_name_(self, "pintu")
            tconfig.setUserContentController_(tcontroller)
            self.toast_web = WKWebView.alloc().initWithFrame_configuration_(NSMakeRect(0, 0, TOAST_W, TOAST_H), tconfig)
            self.toast_web.setValue_forKey_(False, "drawsBackground")
            self.toast_web.loadFileURL_allowingReadAccessToURL_(NSURL.fileURLWithPath_(str(HERE / "toast.html")),
                                                                NSURL.fileURLWithPath_(str(HERE)))
            self.toast_win = Panel.alloc().initWithContentRect_styleMask_backing_defer_(
                NSMakeRect(0, 0, TOAST_W, TOAST_H), 0, NSBackingStoreBuffered, False)
            self.toast_win.setOpaque_(False)
            self.toast_win.setBackgroundColor_(NSColor.clearColor())
            self.toast_win.setHasShadow_(False)
            self.toast_win.setHidesOnDeactivate_(False)
            self.toast_win.setLevel_(NSStatusWindowLevel)
            self.toast_win.setCollectionBehavior_(1 | 256)  # every Space, over full-screen apps
            self.toast_win.setContentView_(self.toast_web)
            self.toast_win.setReleasedWhenClosed_(False)

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

        # ---- alert popup
        @objc.python_method
        def show_toast(self, toast):
            screen = NSScreen.mainScreen().visibleFrame()
            x = screen.origin.x + screen.size.width - TOAST_W - 6
            y = screen.origin.y + screen.size.height - TOAST_H - 4
            self.toast_win.setFrameOrigin_((x, y))
            self.toast_web.evaluateJavaScript_completionHandler_("window.toast(" + json.dumps(toast) + ")", None)
            self.toast_win.orderFrontRegardless()
            self.toast_until, self.toast_app = time.time() + TOAST_SECONDS, toast.get("app")

        @objc.python_method
        def hide_toast(self):
            self.toast_until = 0.0
            self.toast_web.evaluateJavaScript_completionHandler_("window.toastOut && window.toastOut()", None)
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.25, self, "finishToast:", None, False)

        def finishToast_(self, _timer):
            if time.time() > self.toast_until:
                self.toast_win.orderOut_(None)

        def tick_(self, _timer):
            self.items = status.snapshot()
            try:
                status.tray_heartbeat()
                toasts = status.take_toasts()
                if toasts:
                    self.show_toast(toasts[-1])
                elif self.toast_until and time.time() > self.toast_until:
                    self.hide_toast()
            except OSError:
                pass
            stuck_alerts(self.items, self.stuck_seen)
            state, badge = bar_state(self.items)
            if status.muted_until() and state in ("empty", "idle", "done"):
                state = "muted"
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
            elif kind == "mute":
                status.set_mute(0 if status.muted_until() else 3600)
                self.tick_(None)
            elif kind == "toastclick":
                if body.get("app"):
                    subprocess.run(["open", "-b", body["app"]], check=False)
                self.hide_toast()
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
