"""Tests for the shipped code in npm/python (the root-level copies are stale): Esc detection, Windows and Linux alerts."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys
from types import SimpleNamespace
PY = Path(__file__).resolve().parents[1] / "npm/python"


def load(name):
    spec = importlib.util.spec_from_file_location(name + "_npm", PY / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sys.path.insert(0, str(PY))  # notifier imports config/status lazily
status, notifier = load("status"), load("notifier")


class InterruptTests(unittest.TestCase):
    def test_esc_turns_a_working_row_into_stopped(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"PINTUMCP_HOME": tmp}):
            transcript = Path(tmp) / "t.jsonl"
            transcript.write_text('{"type":"assistant"}\n')
            status.update("working", "Editing a.py", "API", "A", now=1000, transcript=str(transcript))
            os.utime(transcript, (1000, 1000))
            self.assertEqual(status.snapshot(now=1010)[0]["state"], "working")  # still running: nothing new written
            transcript.write_text('{"type":"assistant"}\n{"message":{"content":[{"text":"[Request interrupted by user]"}]}}\n')
            os.utime(transcript, (1005, 1005))
            row = status.snapshot(now=1010)[0]
            self.assertEqual((row["state"], row["message"]), ("idle", "Stopped by you"))
            self.assertEqual(status.snapshot(now=1011)[0]["state"], "idle")  # and it stays that way

    def test_today_card_survives_an_event_dated_in_the_future(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"PINTUMCP_HOME": tmp}):
            status.update("done", "ok", "API", "A", now=5000)  # clock skew: newer than "now"
            self.assertEqual(len(status.today_stats(now=100)["trend"]), 12)

    def test_hook_never_opens_a_console_on_windows(self):
        hook = load("hook")
        out = SimpleNamespace(stdout="ParentProcessId=1\nCommandLine=x\n")
        with mock.patch.object(hook, "NO_WINDOW", 0x08000000), mock.patch.object(hook.subprocess, "run", return_value=out) as run:
            hook._windows_proc(5)
        self.assertTrue(all(c.kwargs.get("creationflags") == 0x08000000 for c in run.call_args_list))

    def test_windows_toast_runs_a_hidden_powershell(self):
        with mock.patch.object(notifier.subprocess, "run", return_value=SimpleNamespace(returncode=0, stderr="")) as run:
            self.assertTrue(notifier._windows_notify("Done", "it's <ok>"))
        args, kwargs = run.call_args
        self.assertEqual(args[0][0], "powershell.exe")
        self.assertEqual(kwargs["creationflags"], 0x08000000)  # CREATE_NO_WINDOW: no console flashes

    def test_linux_hands_the_alert_to_the_tray_for_the_animated_popup(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"PINTUMCP_HOME": tmp}):
            import time
            (Path(tmp) / "tray.alive").write_text(str(time.time()))
            with mock.patch.object(notifier, "SYSTEM", "Linux"), mock.patch.object(notifier, "_linux_notify") as plain:
                self.assertTrue(notifier.send_notification("Done", "x", play_snd=False)["notification"])
            self.assertFalse(plain.called)
            self.assertEqual(len(list((Path(tmp) / "toasts").glob("*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
