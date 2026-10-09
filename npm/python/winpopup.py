"""Windows: show the dashboard as a small borderless popup above the tray, like the macOS dropdown.

No extra dependency: Edge/Chrome opens the page in app mode, then Win32 (ctypes) strips the title bar,
moves the window to the bottom-right corner, hides it from the taskbar, and hides it again when it loses focus.
"""

import ctypes
import os
import subprocess
import threading
import time
from ctypes import wintypes as wt

import status

user32, dwm = ctypes.windll.user32, ctypes.windll.dwmapi
TITLE = "Pintu panel"  # the page's <title>, so we can find our window among Edge's
GWL_STYLE, GWL_EXSTYLE = -16, -20
STRIP = 0x00C00000 | 0x00040000 | 0x00020000 | 0x00010000 | 0x00080000  # caption, thick frame, min/max boxes, sysmenu
WS_EX_TOOLWINDOW, WS_EX_APPWINDOW = 0x80, 0x40000
HWND_TOPMOST, SWP_FRAMECHANGED, SWP_NOACTIVATE = -1, 0x20, 0x10
SW_HIDE, SW_SHOW = 0, 5
WIDTH, MARGIN, IDLE_CLOSE = 400, 12, 600  # css px; px from the screen edge; seconds hidden before Edge is closed
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass


def _scale() -> float:
    try:
        return user32.GetDpiForSystem() / 96
    except Exception:
        return 1.0


class Popup:
    def __init__(self, url: str, browser_command):
        self.url, self.command = url, browser_command
        self.hwnd, self.proc, self.height = 0, None, 720
        self.shown_at = self.hidden_at = 0.0
        self.lock = threading.Lock()
        threading.Thread(target=self._watch, daemon=True).start()

    # ---- finding and styling the window
    def _find(self) -> int:
        found = []
        callback = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)(lambda h, _: found.append(h) or True)
        user32.EnumWindows(callback, 0)
        for h in found:
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(h, buf, 256)
            if buf.value.startswith(TITLE):
                return h
        return 0

    def _style(self, h: int) -> None:
        user32.ShowWindow(h, SW_HIDE)
        style = user32.GetWindowLongW(h, GWL_STYLE) & ~STRIP
        user32.SetWindowLongW(h, GWL_STYLE, style)
        ex = (user32.GetWindowLongW(h, GWL_EXSTYLE) | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW  # no taskbar button
        user32.SetWindowLongW(h, GWL_EXSTYLE, ex)
        try:  # Windows 11: rounded corners
            dwm.DwmSetWindowAttribute(h, 33, ctypes.byref(ctypes.c_int(2)), 4)
        except Exception:
            pass

    def _place(self) -> None:
        rect = wt.RECT()
        user32.SystemParametersInfoW(0x30, 0, ctypes.byref(rect), 0)  # work area (excludes the taskbar)
        k = _scale()
        w, h = int(WIDTH * k), min(int(self.height * k), rect.bottom - rect.top - 2 * MARGIN)
        user32.SetWindowPos(self.hwnd, HWND_TOPMOST, rect.right - w - MARGIN, rect.bottom - h - MARGIN, w, h,
                            SWP_FRAMECHANGED | SWP_NOACTIVATE)

    # ---- show / hide
    def _visible(self) -> bool:
        return bool(self.hwnd and user32.IsWindow(self.hwnd) and user32.IsWindowVisible(self.hwnd))

    def toggle(self) -> None:
        with self.lock:
            if self._visible():
                return self._hide()
            if time.time() - self.hidden_at < 0.5:  # the tray click itself just made it lose focus
                return
            self._show()

    def _show(self) -> None:
        if not (self.hwnd and user32.IsWindow(self.hwnd)):
            self.proc = subprocess.Popen(self.command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(80):  # wait up to 8s for Edge to create the window
                time.sleep(0.1)
                self.hwnd = self._find()
                if self.hwnd:
                    break
            if not self.hwnd:
                return
            self._style(self.hwnd)
        self._place()
        user32.ShowWindow(self.hwnd, SW_SHOW)
        user32.SetForegroundWindow(self.hwnd)
        self.shown_at = time.time()

    def _hide(self) -> None:
        user32.ShowWindow(self.hwnd, SW_HIDE)
        self.hidden_at = time.time()

    def resize(self, height: int) -> None:
        self.height = max(240, min(int(height), 900))
        if self._visible():
            self._place()

    def _watch(self) -> None:
        """Hide when the window loses focus; close Edge after a long idle spell to free its memory."""
        while True:
            time.sleep(0.15)
            try:
                if self._visible():
                    if time.time() - self.shown_at > 0.6 and user32.GetForegroundWindow() != self.hwnd:
                        with self.lock:
                            if self._visible():
                                self._hide()
                elif self.hwnd and time.time() - self.hidden_at > IDLE_CLOSE and self.proc:
                    user32.PostMessageW(self.hwnd, 0x0010, 0, 0)  # WM_CLOSE
                    self.hwnd, self.proc = 0, None
            except Exception:
                pass
