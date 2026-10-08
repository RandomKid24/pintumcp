"""Tests for local lifecycle alert formatting and completion bundling."""

import sys
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
        )

    def test_one_completion_delivers_after_a_three_second_delay(self):
        deliver = MagicMock()
        timers = TimerFactory()
        dispatcher = events.CompletionDispatcher(deliver=deliver, timer_factory=timers)

        queued = dispatcher.queue_completion("Built API", 35, "API", "Agent 1")
        timers.created[0].fire()

        self.assertEqual(queued, {"queued": True, "delay_seconds": 3})
        self.assertEqual(timers.created[0].delay, 3)
        deliver.assert_called_once_with("done", "Built API", 35, "API", "Agent 1")

    def test_matching_completions_are_combined_into_one_summary(self):
        deliver = MagicMock()
        timers = TimerFactory()
        dispatcher = events.CompletionDispatcher(deliver=deliver, timer_factory=timers)

        dispatcher.queue_completion("Built API", 35, "API", "Agent 1")
        dispatcher.queue_completion("Wrote tests", 35, "API", "Agent 1")
        timers.created[0].fire()

        deliver.assert_called_once_with(
            "done", "2 agents completed: Built API; Wrote tests", 35, "API", "Agent 1"
        )

    def test_completions_with_different_labels_are_not_combined(self):
        deliver = MagicMock()
        timers = TimerFactory()
        dispatcher = events.CompletionDispatcher(deliver=deliver, timer_factory=timers)

        dispatcher.queue_completion("Built API", 35, "API", "Agent 1")
        dispatcher.queue_completion("Built web", 35, "Web", "Agent 1")
        timers.created[0].fire()
        timers.created[1].fire()

        self.assertEqual(deliver.call_count, 2)
