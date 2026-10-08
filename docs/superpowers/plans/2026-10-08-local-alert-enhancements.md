# Local Alert Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local readiness diagnostics, project/agent labels, and three-second completion bundling without introducing a backend service.

**Architecture:** Lifecycle delivery is centralized in a small local dispatcher that formats titles and keeps one in-memory, lock-protected completion buffer per label. The existing notifier remains the sole cross-platform delivery boundary. `doctor` inspects only local files, commands, and Python modules, and can run the existing delivery path for a labelled test alert.

**Tech Stack:** Python 3.10+, MCP Python SDK, `threading.Timer`, `unittest`, existing platform utilities (`osascript`, `winotify`, `notify-send`, `canberra-gtk-play`/`paplay`).

**Spec:** `docs/superpowers/specs/2026-10-08-local-alert-enhancements-design.md`

## Global Constraints

- Keep all behavior local-only: no cloud service, account, database, external API, or separately managed process.
- Preserve current tool calls when callers omit new optional fields.
- Bundle only completion events, for exactly three seconds per running MCP process.
- Never bundle question, approval, or error events.
- Deliver a real local popup and gentle sound when `doctor(send_test=True)` is invoked.
- Keep standalone and npm-packaged Python copies functionally identical.

## Review Focus

- Blank or newline-containing labels must not create malformed native notification titles.
- A completion from project A must never be included in project B's bundle.
- A question, approval, or error during a pending completion window must still deliver immediately.
- A notification backend missing at runtime must be reported by `doctor`, not claimed as ready.
- A bundle timer firing after its process state changes must not send duplicate notifications.

---

### Task 1: Label Formatting and Lifecycle Tool Parameters

**Files:**
- Create: `tests/test_events.py`
- Create: `events.py`
- Create: `npm/python/events.py`
- Modify: `server.py:1-95`
- Modify: `npm/python/server.py:1-75`

**Interfaces:**
- Produces: `format_event_title(event: str, project: str | None, agent: str | None) -> str`
- Produces: `deliver_event(event: str, message: str, volume: int, project: str | None = None, agent: str | None = None) -> dict`
- Consumes: `notifier.agent_event(event, message, volume)` from the existing notifier.
- Produces: optional `project` and `agent` arguments for all four lifecycle MCP tools.

- [ ] **Step 1: Write failing title-format tests**

```python
def test_format_event_title_includes_project_and_agent():
    assert format_event_title("approval", "API", "Agent 2") == "API · Agent 2: Approval Needed"

def test_format_event_title_uses_legacy_title_without_labels():
    assert format_event_title("error", None, None) == "Agent: Error"

def test_format_event_title_normalizes_blank_and_multiline_labels():
    assert format_event_title("done", " API\n", " ") == "API: Task Complete"
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `python3 -m unittest tests/test_events.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'events'`.

- [ ] **Step 3: Implement the local event formatter and immediate delivery helper**

```python
EVENT_SUFFIXES = {
    "done": "Task Complete",
    "question": "Input Needed",
    "approval": "Approval Needed",
    "error": "Error",
}

def format_event_title(event, project=None, agent=None):
    labels = [clean_label(value) for value in (project, agent)]
    labels = [value for value in labels if value]
    prefix = " · ".join(labels) or "Agent"
    return f"{prefix}: {EVENT_SUFFIXES[event]}"
```

`deliver_event` must call `notifier.agent_event` when no labels are supplied and otherwise call `notifier.alert` with the same event priority/sound and the formatted title. Copy the completed module to `npm/python/events.py`.

- [ ] **Step 4: Add optional label parameters to lifecycle MCP tools**

```python
@mcp.tool()
def agent_approval(
    message: str = "Agent needs your approval before continuing.",
    project: str | None = None,
    agent: str | None = None,
) -> dict:
    return deliver_event("approval", message, get("volume", 80), project, agent)
```

Apply the same signature pattern to `agent_done`, `agent_question`, and `agent_error` in both server copies.

- [ ] **Step 5: Run the focused tests and verify they pass**

Run: `python3 -m unittest tests/test_events.py -v`

Expected: PASS with all three title-format tests green.

- [ ] **Step 6: Commit the labelled lifecycle tools**

```bash
git add events.py npm/python/events.py server.py npm/python/server.py tests/test_events.py
git commit -m "feat: add labels to agent lifecycle alerts"
```

### Task 2: Three-Second Completion Bundler

**Files:**
- Modify: `events.py`
- Modify: `npm/python/events.py`
- Modify: `tests/test_events.py`

**Interfaces:**
- Consumes: `deliver_event(event, message, volume, project, agent)` from Task 1.
- Produces: `queue_completion(message: str, volume: int, project: str | None, agent: str | None) -> dict`.
- Produces: `flush_completion(key: tuple[str | None, str | None]) -> None` for timer callbacks.

- [ ] **Step 1: Write failing bundling tests using a controllable timer factory**

```python
def test_one_completion_is_delivered_after_three_seconds():
    dispatcher.queue_completion("Built API", 35, "API", "Agent 1")
    timer_factory.created[0].fire()
    deliver.assert_called_once_with("done", "Built API", 35, "API", "Agent 1")

def test_multiple_completions_share_one_summary_per_label():
    dispatcher.queue_completion("Built API", 35, "API", "Agent 1")
    dispatcher.queue_completion("Wrote tests", 35, "API", "Agent 1")
    timer_factory.created[0].fire()
    deliver.assert_called_once_with("done", "2 agents completed: Built API; Wrote tests", 35, "API", "Agent 1")

def test_question_is_immediate_while_a_completion_is_buffered():
    dispatcher.queue_completion("Built API", 35, "API", "Agent 1")
    dispatcher.deliver_event("question", "Which database?", 35, "API", "Agent 1")
    deliver.assert_called_once_with("question", "Which database?", 35, "API", "Agent 1")
```

- [ ] **Step 2: Run the focused bundling tests and verify they fail**

Run: `python3 -m unittest tests/test_events.py -v`

Expected: FAIL because `queue_completion` is not defined.

- [ ] **Step 3: Implement a lock-protected three-second bundle dispatcher**

```python
class CompletionDispatcher:
    def __init__(self, deliver=deliver_event, timer_factory=Timer):
        self._deliver = deliver
        self._timer_factory = timer_factory
        self._lock = Lock()
        self._pending = {}

    def queue_completion(self, message, volume, project=None, agent=None):
        key = (clean_label(project), clean_label(agent))
        with self._lock:
            bucket = self._pending.setdefault(key, {"messages": [], "volume": volume})
            bucket["messages"].append(message)
            if len(bucket["messages"]) == 1:
                timer = self._timer_factory(3, self.flush_completion, args=(key,))
                timer.daemon = True
                bucket["timer"] = timer
                timer.start()
        return {"queued": True, "delay_seconds": 3}
```

`flush_completion` must atomically remove the bucket before delivering it, preventing a duplicate timer callback. One message passes through unchanged; multiple messages become a bounded, semicolon-separated summary.

- [ ] **Step 4: Route `agent_done` through the completion dispatcher**

```python
def agent_done(message=..., project=None, agent=None):
    return completion_dispatcher.queue_completion(
        message, get("volume", 80), project, agent
    )
```

Questions, approvals, and errors continue using immediate `deliver_event` calls.

- [ ] **Step 5: Run focused tests and verify they pass**

Run: `python3 -m unittest tests/test_events.py -v`

Expected: PASS; completion tests show a three-second timer and immediate-event test remains green.

- [ ] **Step 6: Commit completion bundling**

```bash
git add events.py npm/python/events.py server.py npm/python/server.py tests/test_events.py
git commit -m "feat: bundle completion alerts locally"
```

### Task 3: Local Doctor, Asset Packaging, and README

**Files:**
- Modify: `notifier.py`
- Modify: `npm/python/notifier.py`
- Modify: `server.py`
- Modify: `npm/python/server.py`
- Create: `assets/pintumcp-icon.png`
- Create: `npm/python/assets/pintumcp-icon.png`
- Modify: `tests/test_notifier.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `notifier.doctor(send_test: bool = True) -> dict`.
- Consumes: `send_notification`, `ICON_PATH`, `SYSTEM`, and local `shutil.which` checks.
- Produces: MCP tool `doctor(send_test: bool = True) -> dict`.

- [ ] **Step 1: Write failing local-doctor tests**

```python
def test_doctor_reports_local_backends_and_runs_a_labelled_test():
    with patch.object(notifier, "SYSTEM", "Linux"), patch.object(
        notifier.shutil, "which", return_value="/usr/bin/notify-send"
    ), patch.object(notifier, "send_notification", return_value={
        "notification": True, "sound": True, "platform": "Linux"
    }) as send:
        result = notifier.doctor(send_test=True)

    assert result["ready"] is True
    assert result["test_delivery"]["notification"] is True
    send.assert_called_once_with("pintumcp doctor", "Local notification test", sound="default", volume=35)
```

- [ ] **Step 2: Run doctor tests and verify they fail**

Run: `python3 -m unittest tests/test_notifier.py -v`

Expected: FAIL with `AttributeError: module 'notifier' has no attribute 'doctor'`.

- [ ] **Step 3: Implement the local readiness report**

```python
def doctor(send_test=True):
    checks = {
        "icon": {"ready": ICON_PATH.is_file(), "path": str(ICON_PATH)},
        "notification": notification_backend_check(),
        "sound": sound_backend_check(),
    }
    result = {"platform": SYSTEM, "checks": checks, "ready": all(check["ready"] for check in checks.values())}
    if send_test:
        result["test_delivery"] = send_notification(
            "pintumcp doctor", "Local notification test", sound="default", volume=35
        )
    return result
```

Use only local executable/module/file checks. Include a `fix` string for a missing Windows `winotify` or Linux `notify-send` backend. Keep macOS dependent only on built-in `osascript` and the icon file.

- [ ] **Step 4: Expose the doctor tool and update documentation**

```python
@mcp.tool()
def doctor(send_test: bool = True) -> dict:
    """Check local popup, sound, and icon readiness; optionally send a test alert."""
    return notification_doctor(send_test)
```

Document the seven lifecycle/general tools, optional `project`/`agent` labels, the three-second completion delay, and `doctor` in the README. Explain that all behavior is local and no backend is required.

- [ ] **Step 5: Run the full verification suite**

Run: `python3 -m unittest discover -s tests -v && python3 -m py_compile notifier.py server.py events.py npm/python/notifier.py npm/python/server.py npm/python/events.py && diff -u notifier.py npm/python/notifier.py && diff -u events.py npm/python/events.py && node --check npm/bin/pintumcp.js && git diff --check`

Expected: PASS, matching notifier/event copies, valid Python and JavaScript, and no whitespace errors.

- [ ] **Step 6: Commit doctor, icon, and documentation**

```bash
git add README.md notifier.py npm/python/notifier.py server.py npm/python/server.py assets npm/python/assets tests/test_notifier.py
git commit -m "feat: add local alert diagnostics"
```

### Task 4: Final Readiness and Push

**Files:**
- Modify: `README.md` only if verification exposes inaccurate setup instructions.

**Interfaces:**
- Consumes: all completed tasks.
- Produces: a verified `main` branch ready to push.

- [ ] **Step 1: Verify clean status and inspect staged history**

Run: `git status --short && git log --oneline -5`

Expected: no unintended files; only planned commits are present.

- [ ] **Step 2: Run the complete verification command**

Run: `python3 -m unittest discover -s tests -v && python3 -m py_compile notifier.py server.py events.py npm/python/notifier.py npm/python/server.py npm/python/events.py && node --check npm/bin/pintumcp.js && git diff --check`

Expected: PASS with all tests green.

- [ ] **Step 3: Push main**

Run: `git push origin main`

Expected: remote `main` advances to include the completed feature commits.
