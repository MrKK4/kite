# Changelog

What Kite changes compared to the upstream Grok Build source it was forked from
(upstream commit `2bdd1d6a`, see `SOURCE_REV`). Details and settings live in
[KITE.md](KITE.md).




## v0.1.7 — lean browsers, context-aware compaction, paste and title fixes

- Browser lean mode (both servers): actions no longer return page snapshots;
  `browser_snapshot` saves to a file in `~/Downloads/Kite` that the model
  searches, and links are pulled with `browser_evaluate`. About 85% less
  context on a search-then-download task. `KITE_BROWSER_LEAN=0` turns it off.
- Right-click now pastes clipboard text, or a clipboard image like Alt+V (before,
  it pasted nothing: Ctrl+V text paste is done by the terminal, not Kite).
- The terminal window/tab title said "grok"; it now says "kite".
- Docs: user guide now says local models compact at 230,000 tokens (the code
  already did; four pages still said 220,000).
- Local models now use the context size the server reports at `/login`
  (llama.cpp `/props`, vLLM `max_model_len`, or the training context; 262,144 if
  unknown) and compact at 88% of it, so a 131k server compacts at ~115k. The
  login message no longer shows a hard-coded 220,000.

## v0.1.6 — browser guide and tool-definition fixes

- Browser: hide Chromium's "unsupported command-line flag" warning bar caused by
  Patchright's stealth flag (`--test-type`).
- Browser guide `docs/browsers.md` (usage, file locations, patches, updating),
  installed to `~/.kite/docs/browsers.md`; the model is told to read it instead
  of assuming stock Playwright defaults.
- Tool-definition audit (`TOOL_AUDIT.md`) fixes: xAI-hosted web/X search is
  never offered; the memory prompt says to call memory tools through
  `use_tool`; accurate browser text in tool descriptions and the MCP docs;
  corrected scheduler hint and skills path.

## v0.1.5 — isolated self-installing browsers

- Browser: Kite's own isolated ungoogled-chromium + uBlock Origin Lite (full
  strength) via Patchright, downloaded automatically on first use (Windows x64);
  separate profile under `~/.kite`.
- Camoufox installs itself into `~/.kite/camoufox-venv` on first use, with one
  automatic retry for the first launch.

## v0.1.4 — release source provenance

- Build releases only from a clean Kite checkout, so the displayed commit
  identifies Kite source instead of the upstream-history development checkout.
- Reject wrong-origin and uncommitted release builds before compilation.

## v0.1.3 — resume fix

- Fix: "Resume session" with no saved sessions opened and instantly closed the
  picker; it now opens the same picker as `/resume`.

## v0.1.2 — installers and build version

- Report the Kite release version and source commit in `kite --version`,
  including Modal builds that upload source without Git metadata.
- Add Windows PowerShell and Git Bash one-line installers, with release SHA-256
  verification, user PATH setup, version pinning and custom install directories.
- Preserve the previous binary if a download fails checksum verification.

## v0.1.1 — workspace crate rename

- Rename all 100 `xai-*` workspace crates to `kite-*`, including Rust imports,
  crate directories, snapshots, build scripts and documentation.
- Preserve environment variables, project settings, protocol methods and HTTP
  headers for compatibility. See [the crate rename map](docs/crate-renames.md).
- Install ripgrep in the Modal test image so search tests can run.

## v0.1.0 — first release

### Local model connection
- `kite login <url>` and `/login <url>` connect any OpenAI-compatible server
  (llama.cpp, LM Studio, vLLM, a cloudflared tunnel...). Models are discovered
  from `<url>/models`; logging in again with a new tunnel URL replaces the old
  models.
- The welcome screen asks for an endpoint instead of looping when no model is
  connected.
- Local models default to a 262,144-token window with compaction at 230,000.

### Speed on a single-slot local server
- Hidden side requests are off by default: per-turn summaries, title refresh,
  session recap, prompt suggestions, LLM session titles and built-in memory
  extraction. They queued ahead of real replies and caused 90–120 s stalls.
- Old tool results are no longer trimmed per request, and the speculative
  two-pass compaction is off. Both rewrote already-sent history and destroyed
  llama.cpp's prompt cache (multi-minute re-reads in long chats).
- Requests send `chat_template_kwargs.preserve_thinking`, so Qwen-style
  templates keep earlier reasoning and history renders identically.
- Starting context cut from ~20k to ~11k tokens: only Kite's own skills folder
  is scanned by default, and the `workflow` and `send_feedback` tools and the
  workflow catalog are gone. Scheduler tools are opt-in.

### Tools and MCP servers (built in, no setup)
- **memory**: long-term memory as a knowledge graph in `~/.kite/memory.json`;
  saved facts load into every new session.
- **exa** and **parallel**: keyless web search. `web_fetch` can read any public
  site (documentation sites pre-approved).
- **playwright**: real Chrome through Patchright (patched driver that hides
  common automation signals); opens maximized and follows window resizes.
  Screenshots come back to the model as images.
- **camoufox** (opt-in): fingerprint-resistant Firefox launched through
  Camoufox's official launcher, for sites that block automation.
- `use_tool` uses a flat schema, because llama.cpp's grammar conversion
  rejected the original one and forced empty arguments.
- **Past chats**: the model can search earlier conversations
  (`kite sessions search --all`, `kite export <id>`) when you ask
  "do you remember...".
- **skill-creator**: Anthropic's skill (Apache-2.0) is bundled; new skills go to
  `~/.kite/skills/<name>/SKILL.md`.

### UI and terminal
- Fixed typing (cursor jumping to the start), flicker on every keystroke on
  Windows, and the slash menu vanishing.
- Right-click pastes.
- Esc cancels a running turn (Ctrl+C still works).
- File paths in replies are clickable (Ctrl+click), including absolute paths
  with spaces; the model is told to always write full paths.
- Tighter layout: smaller margins and padding so answers get most of the
  screen.
- Kite name, logo text and themes throughout.

### Plugins and hooks
- Claude Code plugins load, and can be disabled per plugin for Kite. On Windows,
  hooks run under Git Bash (fixes `/dev/null` and "not a valid Win32
  application" hook errors).

### Removed: everything hosted by xAI
- Telemetry and analytics (Mixpanel, Sentry, remote trace export), feedback
  commands and the feedback tool, the training/retention consent setting.
- Account login, billing, subscriptions and upsells, remote settings and
  campaigns, announcements, the auto-updater, voice, and the `image_gen`,
  `image_edit` and `video_gen` tools.
- Every default xAI endpoint now points to an unresolvable address, so nothing
  can reach xAI.

### Portability
- Every change is a built-in default documented in `KITE.md`; a fresh clone
  behaves the same on any machine. Settings live in `~/.kite` (`KITE_HOME`).
