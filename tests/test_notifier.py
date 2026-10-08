"""Regression tests for the platform notification backends."""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import notifier  # noqa: E402


class NotifierTests(unittest.TestCase):
    def test_macos_submits_a_native_notification(self):
        """Replacing the JXA Notification Center call must fail this test."""
        run = MagicMock()
        with patch.object(notifier, "SYSTEM", "Darwin"), patch.object(
            notifier.subprocess, "run", run
        ):
            sent = notifier.send_notification("Build complete", "All checks passed", play_snd=False)

        self.assertTrue(sent["notification"])
        command = run.call_args.args[0]
        self.assertEqual(command[:4], ["osascript", "-l", "JavaScript", "-e"])
        self.assertIn("NSUserNotificationCenter", command[4])
        self.assertIn('"Build complete"', command[4])

    def test_windows_uses_the_quiet_system_notification_sound(self):
        """Replacing the system notification sound with a raw beep must fail this test."""
        winsound = SimpleNamespace(
            SND_ALIAS=1,
            SND_ASYNC=2,
            PlaySound=MagicMock(),
        )
        with patch.object(notifier, "SYSTEM", "Windows"), patch.dict(
            sys.modules, {"winsound": winsound}
        ):
            played = notifier.play_sound()

        self.assertTrue(played)
        winsound.PlaySound.assert_called_once_with("SystemNotification", 3)

    def test_linux_uses_the_desktop_message_sound_without_a_terminal_bell(self):
        """Falling back to a terminal bell instead of the desktop message sound must fail."""
        popen = MagicMock()
        with patch.object(notifier, "SYSTEM", "Linux"), patch.object(
            notifier.shutil, "which", side_effect=lambda name: "/usr/bin/canberra-gtk-play"
            if name == "canberra-gtk-play"
            else None,
        ), patch.object(notifier.subprocess, "Popen", popen):
            played = notifier.play_sound()

        self.assertTrue(played)
        self.assertEqual(popen.call_args.args[0], ["canberra-gtk-play", "-i", "message"])

    def test_linux_without_a_notification_daemon_reports_failure(self):
        """Claiming a popup was shown when no notifier exists must fail this test."""
        with patch.object(notifier, "SYSTEM", "Linux"), patch.object(
            notifier.shutil, "which", return_value=None
        ):
            sent = notifier.send_notification("Build complete", "All checks passed", play_snd=False)

        self.assertFalse(sent["notification"])
