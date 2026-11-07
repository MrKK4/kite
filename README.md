# Kite

A fun project, by me, for me. 🪁

I run a **Qwen 3.6 35B** model on a private Kaggle notebook (llama.cpp) and use
it as my own "local" model. The notebook exposes the server through a
**cloudflared tunnel**, and Kite is the harness I point at that tunnel. The two
together work really well for me and handle all kinds of topics, from coding to
research to browsing.

Kite started as a fork of xAI's Grok Build. I've personalized it for my needs:
little UI tweaks, different skills, a Chrome/Camoufox browser setup, memory, and
I removed all of the Grok/xAI telemetry, feedback and hosted services, so it's
now fully local (well, I think so 😄). The only network calls are the ones you
make: your model server and the tools you use.

You can use it yourself too. Connecting it to a cloudflared tunnel (or any
OpenAI-compatible server) is pretty straightforward; see
[Usage and connecting](#usage-and-connecting) below.

> ⚠️ **Friendly heads-up:** a lot of Kite was built with the help of AI, so bugs
> are expected. Use it at your own risk, and feel free to open an issue if
> something breaks!

[What's different](#whats-different-from-grok-build) ·
[Usage and connecting](#usage-and-connecting) ·
[Building from source](#building-from-source) ·
[Documentation](#documentation) ·
[Repository layout](#repository-layout) ·
[Development](#development) ·
[Contributing](#contributing) ·
[License and provenance](#license-and-provenance)

---

## What's different from Grok Build

The highlights (full list in [CHANGELOG.md](CHANGELOG.md)):

- 🔌 **Bring your own model:** `kite login <url>` for any OpenAI-compatible
  server or cloudflared tunnel. No account needed.
- ⚡ **Fast on a single local server:** no hidden side requests, and history is
  never rewritten, so llama.cpp's prompt cache keeps replies quick even deep
  into long chats. Starting context is cut roughly in half (~20k → ~11k tokens).
- 🧠 **Memory:** a built-in knowledge-graph memory that loads into every
  session, plus search across past chats ("do you remember...").
- 🌐 **Web and browser:** keyless Exa/Parallel search, `web_fetch`, a real
  Chrome browser (Patchright), and opt-in Camoufox for bot-protected sites.
- 🖥️ **UI fixes:** typing and flicker fixed on Windows, right-click paste,
  Esc cancels, clickable file paths, tighter layout.
- 🧩 **Skills and plugins:** bundled skill-creator, Claude Code plugins, hooks
  via Git Bash on Windows.
- 🔒 **Nothing goes to xAI:** telemetry, feedback, account, billing, remote
  settings, updater, voice and media tools are removed.

## Usage and connecting

1. **Get Kite:** download `kite-windows-x64.exe` from
   [Releases](https://github.com/MrKK4/kite/releases) (or build it, see below).
2. **Install helpers:** [Node.js](https://nodejs.org) (memory and browser tools)
   and Google Chrome (browser tool).
3. **Start a model server.** Anything OpenAI-compatible works: llama.cpp,
   LM Studio, vLLM, Ollama's `/v1`... My setup is llama.cpp on a Kaggle notebook
   with `cloudflared tunnel --url http://localhost:8080`, which prints a URL like
   `https://something-random.trycloudflare.com`.
4. **Connect and go:**

   ```sh
   kite login https://something-random.trycloudflare.com/v1   # connect, then open Kite
   kite                                                       # next time, just run it
   kite -p "Explain this codebase"                            # headless, one-shot
   ```

   Inside Kite, `/login <url>` reconnects. Quick tunnels get a new URL every
   restart, so just run `/login` again with the new one.

Kite finds the model automatically from `<url>/models`. Defaults (context size,
MCP servers, memory, browser, skills) are all explained in [KITE.md](KITE.md).

## Building from source

Requirements:

- **Rust** — the toolchain is pinned by [`rust-toolchain.toml`](rust-toolchain.toml);
  `rustup` installs it automatically on first build.
- **[DotSlash](https://dotslash-cli.com)** — required so hermetic tools under
  [`bin/`](bin/) (notably [`bin/protoc`](bin/protoc)) can download and run.
  Install it and ensure `dotslash` is on your `PATH` **before** building:

  ```sh
  cargo install dotslash
  # or: prebuilt packages — https://dotslash-cli.com/docs/installation/
  /usr/bin/env dotslash --help   # sanity check
  ```

- **protoc** — proto codegen resolves [`bin/protoc`](bin/protoc) via DotSlash,
  or falls back to a `protoc` on `PATH` / `$PROTOC`.
- macOS and Linux are supported build hosts; Windows builds are best-effort.

```sh
cargo run -p kite-pager-bin                         # build + launch the TUI
cargo build -p kite-pager-bin --release --bin kite  # release binary: target/release/kite
cargo check -p kite-pager-bin                       # fast validation
```

[KITE.md](KITE.md) also describes the remote Modal build used for Windows and
Linux release binaries. After editing a system prompt template under
`crates/codegen/kite-agent/templates/`, run
`python crates/codegen/kite-agent/scripts/encrypt_templates.py` before a
local build.

## Documentation

The user guide ships with the pager crate and is copied to
`~/.kite/docs/user-guide/` at startup:
[`crates/codegen/kite-pager/docs/user-guide/`](crates/codegen/kite-pager/docs/user-guide/)
— getting started, keyboard shortcuts, slash commands, configuration, theming,
MCP servers, skills, plugins, hooks, headless mode, sandboxing, and more.

## Repository layout

| Path | Contents |
|------|----------|
| `crates/codegen/kite-pager-bin` | Composition-root package; builds the `kite` binary |
| `crates/codegen/kite-pager` | The TUI: scrollback, prompt, modals, rendering |
| `crates/codegen/kite-shell` | Agent runtime + leader/stdio/headless entry points |
| `crates/codegen/kite-tools` | Tool implementations (terminal, file edit, search, ...) |
| `crates/codegen/kite-workspace` | Host filesystem, VCS, execution, checkpoints |
| `crates/codegen/...` | The rest of the CLI crate closure (config, MCP, markdown, sandbox, ...) |
| `crates/common/`, `crates/build/`, `prod/mc/` | Small shared leaf crates pulled in by the closure |
| `third_party/` | Vendored upstream source (Mermaid diagram stack) — see below |

Workspace crates and Rust modules use the `kite-*` / `kite_*` prefixes; see
[the crate rename map](docs/crate-renames.md). User-facing `GROK_` environment
variables and project `.grok/` directories retain their names for compatibility.

> [!IMPORTANT]
> The root `Cargo.toml` (workspace members, dependency versions, lints,
> profiles) is **generated** — treat it as read-only. Prefer editing per-crate
> `Cargo.toml` files.

## Development

```sh
cargo check -p <crate>        # always target specific crates; full-workspace builds are slow
cargo test -p kite-config # per-crate tests
cargo clippy -p <crate>       # lint config: clippy.toml at the repo root
cargo fmt --all               # rustfmt.toml at the repo root
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License and provenance

Kite is derived from SpaceXAI's Grok Build source, published under the
**Apache License, Version 2.0**. The inherited copyright notice and license are
in [`LICENSE`](LICENSE); Kite's modifications are distributed under the same
license. [`SOURCE_REV`](SOURCE_REV) records the upstream monorepo commit the
inherited source was synced from. Kite is not affiliated with or supported by
SpaceXAI.

Third-party and vendored code remains under its original licenses. See:

- [`THIRD-PARTY-NOTICES`](THIRD-PARTY-NOTICES) — crates.io / git dependencies,
  bundled UI themes, and **in-tree source ports** (including openai/codex and
  sst/opencode tool implementations)
- [`crates/codegen/kite-tools/THIRD_PARTY_NOTICES.md`](crates/codegen/kite-tools/THIRD_PARTY_NOTICES.md)
  — crate-local notice for the codex and opencode ports (license texts +
  Apache §4(b) change notice)
- [`third_party/NOTICE`](third_party/NOTICE) — vendored Mermaid-stack index
