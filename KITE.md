# Kite

Kite is this repository's personal, local-model fork. The executable is
`kite.exe` on Windows and `kite` on Linux. It keeps settings and sessions in
`~/.kite/`; set `KITE_HOME` to use another directory. It does not read your
installed Grok account or share its default application directory.

Kite's user guide is copied to `~/.kite/docs/user-guide/` at startup (`/docs`
inside Kite). Workspace crates use the `kite-*` prefix (see [the rename map](docs/crate-renames.md)).
Some inherited names remain for compatibility: project-level
folders are `.grok/` (for example `.grok/skills/`), environment variables use
the `GROK_` prefix (except `KITE_HOME`), and the built-in themes are stored as
`groknight` / `grokday` (shown as Kite Dark / Kite Light; `kite-dark` and
`kite-light` are accepted too).

Everything below is a built-in default compiled into Kite, not local
configuration, so a fresh clone and build behaves the same on any machine. The
only per-machine step is connecting a model.

## Connect a model

From a terminal (connects, then opens Kite):

```powershell
kite login https://your-tunnel.trycloudflare.com/v1
```

Or inside Kite:

```text
/login https://your-tunnel.trycloudflare.com/v1
/login http://localhost:8080/v1
```

Kite requests `<base-url>/models` without account credentials, selects the first
nonempty model ID, and saves the discovered models in `~/.kite/config.toml`,
replacing models saved from a previous URL. Use `/model` to select another
discovered model. Repeat the login whenever your Cloudflare tunnel URL changes.
Discovery must succeed before settings change.

The local profile uses OpenAI Chat Completions, `max_tokens`, system messages,
and no reasoning-effort parameter or `store` field. The server owns its chat
template and thinking configuration; streamed `reasoning_content` is supported.
The endpoint is expected to accept unauthenticated requests (the inference
credential is the placeholder `none`, matching the supplied llama.cpp setup).

Models discovered this way default to a 262,144-token context window and compact
at **230,000 tokens**. Edit `context_window` and `auto_compact_at_tokens` in the
model's config entry for a different model size.

## Tools and MCP servers

Default MCP servers (turn any off with `/mcp`, or
`[mcp_servers.<name>] enabled = false` in `~/.kite/config.toml`):

| Server | Purpose | Needs |
| --- | --- | --- |
| `memory` | Tool-driven long-term memory (`@modelcontextprotocol/server-memory`), stored in `~/.kite/memory.json` | Node/npx |
| `exa` | Keyless web search and page reading (`https://mcp.exa.ai/mcp`) | Network |
| `parallel` | Keyless web search (`https://search.parallel.ai/mcp`) | Network |
| `playwright` | Real browser for JavaScript sites, clicks, logins: `patchright-mcp@0.0.68` (Patchright's fork of `@playwright/mcp`, same tools, patched driver that hides common automation signals) driving installed Google Chrome. Opens maximized and follows window resizes via `~/.kite/playwright-mcp.json`, created on first use and safe to edit | Node/npx, Google Chrome |
| `camoufox` | **Off by default.** Fingerprint-resistant Firefox for sites that block automation. Kite writes `~/.kite/camoufox-mcp.py`, which starts Camoufox through its official launcher (`launch_server`, so its fingerprint config is applied) and runs `@playwright/mcp@0.0.78` connected to it. Enable with `[mcp_servers.camoufox] enabled = true` | Python + `pip install -U camoufox[geoip]` + `python -m camoufox fetch`, Node/npx |

MCP tools are reached through `search_tool` and `use_tool`; `search_tool`'s
description names these servers so the model knows to use them. `use_tool`'s
argument schema is a flat object because llama.cpp's grammar conversion turns
`oneOf`/`not` schemas into a grammar that only allows `{}`.

Browser notes:
- No Chrome? Set `"channel": "chromium"` in `~/.kite/playwright-mcp.json` and run
  `npx patchright install chromium`.
- Camoufox sessions are not persistent (Playwright cannot serve a persistent
  profile over its remote protocol), so logins do not survive a restart. Set
  `KITE_CAMOUFOX_HEADLESS=1` for headless. The Playwright MCP version must match
  the Python Playwright minor version used by Camoufox (1.62 → `0.0.78`);
  override with `KITE_CAMOUFOX_MCP_PACKAGE`.
- Pointing `@playwright/mcp` at `camoufox.exe` with `--executable-path` skips the
  launcher, so Camoufox's fingerprint config is not applied. Remove such a
  hand-made `[mcp_servers.camoufox]` entry to use the built-in one.
- Each MCP result is capped at 20 KB (full output saved to a file the model can
  search), and snapshots after actions contain only what changed.

`web_fetch` is on and can fetch any public site; documentation sites are
pre-approved, other hosts go through the normal permission prompt. Private and
local addresses stay blocked. xAI-hosted `web_search` is off; it needs an xAI
account.

## Memory

Memory is tool-driven for writes: the model saves facts with the `memory` MCP
server when asked ("remember this") or when clearly useful. For reads, each new
session loads a compact summary of `~/.kite/memory.json` (up to 8,000 characters)
into the system prompt, so saved facts such as your name are known without the
model having to search. Facts saved mid-conversation appear from the next session. The built-in memory system (`~/.kite/memory-v2/`, its prompt block,
per-turn extraction, and background consolidation) is off by default; opt in with
`[memory_v2] enabled = true`.

Past chats are searchable too. The system prompt tells the model to run
`kite sessions search --all "<keywords>"` (full-text index of every saved
session, `~/.kite/sessions/session_search.sqlite`) and `kite export <id>` (one
chat as Markdown) when you ask about an earlier conversation. You can run the
same commands yourself.

## Local-model performance

A single-slot llama.cpp server runs one request at a time, so hidden side calls
delay the next reply. Kite disables them by default: per-turn summaries and title
refresh (`[features] turn_summary`), session recap (`[features] session_recap`),
prompt suggestions, LLM session titles for `local:*` models, and built-in memory
extraction. Subagents are off by default.

The server reuses its prompt cache only while the start of the prompt stays
identical, so Kite keeps sent history stable:
- Request-time trimming of old tool results is off (`[compaction.pruning]
  enabled`); it rewrote earlier messages and caused multi-minute re-reads.
  Compaction at 230k tokens handles size instead.
- Two-pass compaction (a speculative early summary call) is off
  (`[features] two_pass_compaction`).
- Requests send `chat_template_kwargs: {"preserve_thinking": true}` so Qwen-style
  templates keep earlier reasoning instead of re-rendering history.

## Screen layout

Kite uses tighter spacing than upstream so answers get most of the screen: no
blank rows at the top and bottom or around the header and footer, 1-column side
margins and block padding, and no padding rows inside the pinned prompt box.
Restore any of it in your appearance config under `scrollback.layout`
(`outer_vpad`, `outer_hpad_left/right`, `block_pad_left/right`) and
`scrollback.blocks.prompt.vpad`.

## Skills and tools (context size)

Kite ships Anthropic's **skill-creator** (Apache-2.0, from `anthropics/skills`)
and installs it to `~/.kite/bundled/skill-creator/` on startup (kept in sync with
the build; a skill of the same name in `~/.kite/skills/` overrides it). Its eval
scripts call the Claude Code CLI and are optional. Anthropic's docx/pdf/xlsx/pptx
skills are source-available, not open source, so they are not bundled; copy them
into `~/.kite/skills/` yourself if your use is permitted by their license.

Skills load only from `~/.kite/skills/<name>/SKILL.md` by default. Other tools'
skill folders (`~/.claude`, `~/.cursor`, `~/.agents`, Claude Code plugin skills)
are off because listing them cost ~8k tokens per request. Turn them back on with:

```toml
[compat.claude]
skills = true          # ~/.claude skills, Claude plugin skills, ~/.agents

[skills]
paths = ["~/.agents"]  # or add any folder explicitly
```

The `workflow` and `send_feedback` tools are not offered. The scheduler tools
(`scheduler_create/list/delete`, used by `/loop`) are off unless enabled:

```toml
[kite]
scheduler = true
```

## Plugins and hooks

Kite loads plugins enabled in your Claude Code `~/.claude/settings.json`, so those
follow whatever is installed on each machine (their skills stay off as above). Disable a plugin for Kite only with
`[plugins] disabled = ["name@marketplace"]`. On Windows, hooks run under Git Bash
when it is installed (as in Claude Code); `GROK_SHELL` overrides this.

## Private local operation

Account login, product telemetry, trace uploads, error reporting, hosted model
catalog/settings sync, remote control, voice, and Grok auto-updates are disabled
by the build's distribution policy. Config or environment flags cannot re-enable
those capabilities. Local session transcripts and debug logs remain available.
Ordinary model requests and explicitly used network tools still use the network.

Some of that is removed from the code outright rather than switched off: Mixpanel
analytics, the remote product-event sink, and Sentry error reporting are gone;
OTLP span and external telemetry exporters are never configured; the
`/feedback` and `/privacy` commands, the `send_feedback` tool, the hosted
feedback client, the feedback trace-upload offer, and the "Coding data,
retention, and training" setting and banner are removed.

## New machine checklist

1. Install with `irm https://raw.githubusercontent.com/MrKK4/kite/main/scripts/install.ps1 | iex`
   in Windows PowerShell (or use the Git Bash command in [README.md](README.md#install-on-windows)).
   The installer verifies release checksums and adds `~/.kite/bin` to your user PATH.
   Re-run it to update after closing Kite. Building or copying `kite.exe` also works.
2. Install Node.js 24+ (for the `memory` and `playwright` servers).
3. Windows: install Git for Windows so plugin hooks get Git Bash.
4. Run `kite login <your model URL>`.

Memory (`~/.kite/memory.json`) and sessions stay on the machine that made them;
copy `~/.kite/memory.json` to carry memories over.

## Build on Modal

With an authenticated Modal CLI:

```powershell
modal run scripts/modal_build.py --mode test
modal run scripts/modal_build.py --target windows
```

The build uses **16 CPU cores, 64 GiB RAM, and no GPU**. Rust compilation runs
on Modal; the local computer only uploads source and downloads the result to
`dist/kite.exe`. Registry downloads and the Windows toolchain are cached in
`kite-build-cache`; compiler outputs use fast container-local disk.
Use `--target linux` to produce `dist/kite` instead. Local builds remain possible
with `cargo build -p kite-pager-bin --release --bin kite`.

The system prompt is compiled from an obfuscated copy of
`crates/codegen/kite-agent/templates/*.md`. The Modal build regenerates it;
for a local build after editing a template, first run
`python crates/codegen/kite-agent/scripts/encrypt_templates.py`.
