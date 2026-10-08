"""Real-OS smoke test (CI only): sends actual notifications, nothing mocked.

Run: python tests/smoke.py
Fails if a platform backend cannot deliver one of the four alert types.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import events  # noqa: E402
import notifier  # noqa: E402

report = notifier.doctor(send_test=False)
print(report)
failed = []
for event in events.EVENT_DETAILS:
    result = events.deliver_event(event, f"smoke test: {event}", 0, "CI", "smoke")
    print(event, result)
    if not result.get("notification"):
        failed.append(event)
if not report["checks"]["notification"]["ready"]:
    failed.append("doctor: notification backend not ready")
sys.exit(f"FAILED: {failed}" if failed else 0)
