# Monitoring Usage

Kite tracks token and context usage locally, per session. Nothing is sent anywhere: Kite does not include product telemetry, trace upload, or an OpenTelemetry exporter.

---

## Context window

- **`/context`** shows the context window split into System prompt, Messages, Reasoning/overhead, and Free. Rows for Tool definitions, Skills, and MCP servers are already counted in those totals.
- **`/session-info`** (aliases `/status`, `/info`) shows the model, turn count, and context usage for the current session.
- **`/context-window <size>`** overrides the context window size for the current model (for example `/context-window 256000`). See [Slash Commands](04-slash-commands.md).

Models discovered with `kite login` / `/login` default to a 262,144-token context window and compact at 220,000 tokens. To change that for a model, edit `context_window` and `auto_compact_at_tokens` in the model's entry in `~/.kite/config.toml`. See [Custom Models](11-custom-models.md) and [Session Management](17-sessions.md) for compaction.

---

## Status line

The optional status line can show the model, context-window usage, cost, directory, and git worktree live at the bottom of the screen. Opt in with `[ui.status_line]` in `~/.kite/config.toml`. See [Status Line](25-status-line.md).

---

## Per-session token totals

`kite usage` prints the persisted token usage for a saved session as JSON:

```bash
# Session totals plus every recorded turn
kite usage <session-id>

# One turn
kite usage <session-id> 3
```

See [Session Management](17-sessions.md#the-kite-usage-subcommand) for the output format. Headless runs (`kite -p --output-format json` / `streaming-json`) also report usage in their result; see [Headless Mode](14-headless-mode.md).

Cost figures depend on the model's configured pricing; a local model server usually has none, so token counts are the meaningful number.

---

## Local logs

For debugging, Kite writes local logs. In the TUI, set `GROK_LOG_FILE` to an absolute path to write the log to that file, and use `RUST_LOG` to control verbosity:

```bash
GROK_LOG_FILE=/tmp/kite.log RUST_LOG=debug kite
```

In headless mode, logs go to stderr. See [Terminal Support and Troubleshooting](21-terminal-support.md).
