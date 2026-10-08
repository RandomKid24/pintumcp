"""Tests for local lifecycle alert formatting and completion bundling."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import events  # noqa: E402


class FakeTimer:
    def __init__(self, delay, callback, args=()):
        self.delay = delay
        self.callback = callback
        self.args = args
        self.daemon = False
        self.started = False

    def start(self):
        self.started = True

    def cancel(self):
        self.callback = lambda *a: None

    def fire(self):
        self.callback(*self.args)


class TimerFactory:
    def __init__(self):
        self.created = []

    def __call__(self, delay, callback, args=()):
        timer = FakeTimer(delay, callback, args)
        self.created.append(timer)
        return timer


class EventTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.spool = Path(tmp.name)
        events._recent.clear()

    def make(self, deliver, timers):
        return events.CompletionDispatcher(deliver=deliver, timer_factory=timers, spool=self.spool)

    def test_format_event_title_includes_project_and_agent(self):
        self.assertEqual(
            events.format_event_title("approval", "API", "Agent 2"),
            "API · Agent 2: Approval Needed",
        )

    def test_format_event_title_preserves_legacy_title_without_labels(self):
        self.assertEqual(events.format_event_title("error", None, None), "Agent: Error")

    def test_format_event_title_normalizes_blank_and_multiline_labels(self):
        self.assertEqual(events.format_event_title("done", " API\n", " "), "API: Task Complete")

    def test_approval_delivery_uses_an_actionable_title_and_soft_attention_sound(self):
        deliver = MagicMock(return_value={"notification": True, "sound": True})
        with patch.object(events, "alert", deliver):
            result = events.deliver_event("approval", "Approve the production deploy?", 35)

        self.assertEqual(result, {"notification": True, "sound": True})
        deliver.assert_called_once_with(
            title="Agent: Approval Needed",
            message="Approve the production deploy?",
            priority="normal",
            sound="attention",
            volume=35,
            icon=events.event_icon("approval"),
            silent=False,
        )

    def test_one_completion_delivers_after_a_three_second_delay(self):
        deliver, timers = MagicMock(), TimerFactory()
        dispatcher = self.make(deliver, timers)

        queued = dispatcher.queue_completion("Built API", 35, "API", "Agent 1")
        deliver.assert_not_called()
        timers.created[0].fire()

        self.assertEqual(queued, {"queued": True, "delay_seconds": 3})
        self.assertEqual(timers.created[0].delay, 3)
        deliver.assert_called_once_with("done", "Built API", 35, "API", "Agent 1")

    def test_same_project_completions_combine_and_agents_are_named(self):
        deliver, timers = MagicMock(), TimerFactory()
        dispatcher = self.make(deliver, timers)

        dispatcher.queue_completion("Built API", 35, "API", "Agent 1")
        dispatcher.queue_completion("Wrote tests", 50, "API", "Agent 2")
        timers.created[0].fire()

        deliver.assert_called_once_with(
            "done", "2 tasks completed: Agent 1: Built API; Agent 2: Wrote tests", 50, "API", None
        )

    def test_same_agent_completions_keep_the_agent_label(self):
        deliver, timers = MagicMock(), TimerFactory()
        dispatcher = self.make(deliver, timers)

        dispatcher.queue_completion("a", 35, "API", "Agent 1")
        dispatcher.queue_completion("b", 35, "API", "Agent 1")
        timers.created[0].fire()

        deliver.assert_called_once_with("done", "2 tasks completed: a; b", 35, "API", "Agent 1")

    def test_different_projects_are_not_combined(self):
        deliver, timers = MagicMock(), TimerFactory()
        dispatcher = self.make(deliver, timers)

        dispatcher.queue_completion("Built API", 35, "API", "Agent 1")
        dispatcher.queue_completion("Built web", 35, "Web", "Agent 1")
        for timer in timers.created:
            timer.fire()

        self.assertEqual(deliver.call_count, 2)

    def test_servers_in_separate_processes_share_one_bundle(self):
        """Two dispatchers on one spool stand in for two MCP server processes."""
        deliver, timers_a, timers_b = MagicMock(), TimerFactory(), TimerFactory()
        a, b = self.make(deliver, timers_a), self.make(deliver, timers_b)

        a.queue_completion("from A", 35)
        b.queue_completion("from B", 35)
        timers_a.created[0].fire()
        timers_b.created[0].fire()

        deliver.assert_called_once_with("done", "2 tasks completed: from A; from B", 35, None, None)

    def test_long_bundles_say_how_many_were_left_out(self):
        deliver, timers = MagicMock(), TimerFactory()
        dispatcher = self.make(deliver, timers)

        for n in range(7):
            dispatcher.queue_completion(f"t{n}", 35)
        timers.created[0].fire()

        self.assertEqual(
            deliver.call_args.args[1], "7 tasks completed: t0; t1; t2; t3; t4; +2 more"
        )

    def test_flush_all_sends_pending_completions_immediately(self):
        deliver, timers = MagicMock(), TimerFactory()
        dispatcher = self.make(deliver, timers)

        dispatcher.queue_completion("last words", 35)
        dispatcher.flush_all()

        deliver.assert_called_once_with("done", "last words", 35, None, None)

    def test_delivery_failure_is_reported_not_swallowed(self):
        deliver, timers = MagicMock(return_value={"notification": False}), TimerFactory()
        dispatcher = self.make(deliver, timers)

        dispatcher.queue_completion("x", 35)
        with patch.object(events.sys, "stderr") as stderr:
            timers.created[0].fire()

        self.assertIn("run doctor", "".join(c.args[0] for c in stderr.write.call_args_list))

    def test_identical_immediate_alerts_are_dropped_for_a_few_seconds(self):
        deliver = MagicMock(return_value={"notification": True})
        with patch.object(events, "alert", deliver):
            events.deliver_event("error", "Build failed", 35)
            second = events.deliver_event("error", "Build failed", 35)
            events.deliver_event("error", "Different failure", 35)

        self.assertTrue(second["duplicate"])
        self.assertEqual(deliver.call_count, 2)

    def test_every_event_has_its_own_mascot_icon(self):
        for event in events.EVENT_DETAILS:
            face = events.ICON_FOR.get(event, event)
            self.assertEqual(events.event_icon(face).name, f"{face}.png")

    def test_working_is_a_silent_heads_up_with_the_thinking_face(self):
        deliver = MagicMock(return_value={"notification": True})
        with patch.object(events, "alert", deliver), patch.object(events, "in_quiet_hours", return_value=False):
            events.deliver_event("working", "Refactoring auth", 35, "API", "Agent 1")

        kwargs = deliver.call_args.kwargs
        self.assertEqual(kwargs["title"], "API · Agent 1: Started")
        self.assertTrue(kwargs["silent"])
        self.assertEqual(kwargs["icon"].name, "thinking.png")

    def test_quiet_hours_show_the_sleepy_face_but_errors_stay_themselves(self):
        deliver = MagicMock(return_value={"notification": True})
        with patch.object(events, "alert", deliver), patch.object(events, "in_quiet_hours", return_value=True):
            events.deliver_event("done", "ok", 35)
            events.deliver_event("error", "boom", 35)

        self.assertEqual(deliver.call_args_list[0].kwargs["icon"].name, "sleepy.png")
        self.assertEqual(deliver.call_args_list[1].kwargs["icon"].name, "error.png")

    def test_a_bundle_of_three_or_more_gets_the_party_face(self):
        deliver, timers = MagicMock(), TimerFactory()
        dispatcher = self.make(deliver, timers)
        for n in range(3):
            dispatcher.queue_completion(f"t{n}", 35)
        timers.created[0].fire()
        self.assertEqual(deliver.call_args.kwargs, {"mood": "party"})

        deliver2, timers2 = MagicMock(), TimerFactory()
        pair = self.make(deliver2, timers2)
        pair.queue_completion("a", 35, "Web")
        pair.queue_completion("b", 35, "Web")
        timers2.created[0].fire()
        self.assertEqual(deliver2.call_args.kwargs, {})

    def test_quiet_hours_wrap_past_midnight(self):
        from datetime import datetime

        window = {"start": "22:00", "end": "08:00"}
        with patch.object(events, "get", side_effect=lambda k, d=None: window if k == "quiet_hours" else d):
            self.assertTrue(events.in_quiet_hours(datetime(2026, 1, 1, 23, 30)))
            self.assertTrue(events.in_quiet_hours(datetime(2026, 1, 1, 7, 59)))
            self.assertFalse(events.in_quiet_hours(datetime(2026, 1, 1, 8, 0)))
            self.assertFalse(events.in_quiet_hours(datetime(2026, 1, 1, 13, 0)))

    def test_quiet_hours_silence_sound_but_never_errors(self):
        deliver = MagicMock(return_value={"notification": True})
        with patch.object(events, "alert", deliver), patch.object(events, "in_quiet_hours", return_value=True):
            events.deliver_event("question", "q", 35)
            events.deliver_event("error", "boom", 35)

        self.assertTrue(deliver.call_args_list[0].kwargs["silent"])
        self.assertFalse(deliver.call_args_list[1].kwargs["silent"])

    def test_completion_is_muted_only_when_the_agent_app_is_focused(self):
        deliver = MagicMock(return_value={"notification": True})
        cfg = lambda k, d=None: True if k == "mute_when_focused" else d
        env = {"__CFBundleIdentifier": "com.apple.Terminal"}
        with patch.object(events, "alert", deliver), patch.object(events, "get", side_effect=cfg), \
                patch.dict(events.os.environ, env):
            with patch.object(events.notifier, "frontmost_app", return_value="com.apple.Terminal"):
                muted = events.deliver_event("done", "a", 35)
            with patch.object(events.notifier, "frontmost_app", return_value="org.mozilla.firefox"):
                events.deliver_event("done", "b", 35)
            with patch.object(events.notifier, "frontmost_app", return_value="com.apple.Terminal"):
                events.deliver_event("error", "c", 35)  # errors are never muted

        self.assertEqual(muted["muted"], "focused")
        self.assertEqual(deliver.call_count, 2)


if __name__ == "__main__":
    unittest.main()
