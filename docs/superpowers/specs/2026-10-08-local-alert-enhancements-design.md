# Local Alert Enhancements Design

## Goal

Make pintumcp more useful while retaining its plug-and-play, local-only model.
The additions must require no cloud service, account, database, external API, or
separately managed background process.

## Scope

Add three features:

1. A `doctor` MCP tool that checks local notification readiness and sends a
   clearly-labelled local test alert.
2. Optional project and agent labels on lifecycle alerts.
3. A three-second in-memory completion bundler.

## Architecture

The existing Python MCP process remains the only running component. New helper
code lives alongside the notifier and server code in both the standalone and
packaged Python directories.

```text
Agent MCP call
  -> lifecycle tool
  -> label formatter
  -> immediate delivery (question / approval / error)
     or 3-second local completion buffer (done)
  -> existing platform notifier
```

The completion buffer is process-local. It is intentionally discarded when the
MCP process exits, so no persistent state or backend is introduced.

## MCP Tools

### `doctor`

`doctor(send_test: bool = True)` returns structured local readiness checks:

- the current platform;
- whether the notification backend is available;
- whether a gentle sound backend is available;
- whether the bundled icon exists;
- when `send_test` is true, the observed popup and sound submission result.

The tool does not contact any network service. It reports an actionable local
fix when a Linux utility or Windows Python package is missing.

### Lifecycle labels

`agent_done`, `agent_question`, `agent_approval`, and `agent_error` gain
optional `project` and `agent` parameters. Existing calls remain valid.

Examples:

- `project="API", agent="Agent 2"` + approval -> `API · Agent 2: Approval Needed`
- no labels + error -> `Agent: Error`

Blank labels are ignored. Labels are limited to a short, single-line value to
keep native notifications readable.

## Completion Bundling

`agent_done` buffers events for three seconds. The buffer key is the formatted
project/agent label, preventing unrelated work from being combined.

- One completion: notify after three seconds with the original message.
- Multiple completions: send one summary containing the count and compact
  messages.
- Question, approval, and error: always immediate and never bundled.

The buffer uses a lock and daemon timer to prevent races and avoid holding the
MCP process open. Each MCP process only bundles events it receives itself.

## Error Handling

Local readiness checks and delivery errors are returned in the tool result;
they do not crash the MCP server. If a bundle timer encounters delivery failure,
the result is logged to stderr because the originating tool call has already
returned.

## Testing

Tests will cover:

- label formatting and backwards-compatible titles;
- doctor checks and test-delivery results through mocked platform boundaries;
- a single buffered completion;
- multiple completions merged after three seconds;
- immediate delivery for questions, approvals, and errors;
- current cross-platform notification and gentle-sound behavior.

## Non-goals

- Cloud synchronization, accounts, analytics, webhooks, or databases.
- Persistent notification history.
- Popup buttons or replies, whose support varies by operating system.
- Cross-process bundling.
