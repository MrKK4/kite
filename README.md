# Kite

**Kite** is a terminal coding agent for local and self-hosted models. It runs
as a full-screen TUI that understands your codebase, edits files, executes
shell commands, and manages long-running tasks — interactively, headlessly for
scripting, or embedded in editors via the Agent Client Protocol (ACP).

Kite connects to an OpenAI-compatible model server you choose; no hosted
account is needed. See [KITE.md](KITE.md) for connecting a model, default tools
and MCP servers, memory, local-model performance settings, and building.

[Building from source](#building-from-source) ·
[Documentation](#documentation) ·
[Repository layout](#repository-layout) ·
[Development](#development) ·
[Contributing](#contributing) ·
[License and provenance](#license-and-provenance)

---

## Quick start

```sh
kite login http://localhost:8080/v1   # connect a model server, then open Kite
kite                                  # interactive TUI
kite -p "Explain this codebase"       # headless
kite --version
```

Inside Kite, `/login <base-url>` connects or reconnects a model server.

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
cargo run -p xai-grok-pager-bin                         # build + launch the TUI
cargo build -p xai-grok-pager-bin --release --bin kite  # release binary: target/release/kite
cargo check -p xai-grok-pager-bin                       # fast validation
```

[KITE.md](KITE.md) also describes the remote Modal build used for Windows and
Linux release binaries. After editing a system prompt template under
`crates/codegen/xai-grok-agent/templates/`, run
`python crates/codegen/xai-grok-agent/scripts/encrypt_templates.py` before a
local build.

## Documentation

The user guide ships with the pager crate and is copied to
`~/.kite/docs/user-guide/` at startup:
[`crates/codegen/xai-grok-pager/docs/user-guide/`](crates/codegen/xai-grok-pager/docs/user-guide/)
— getting started, keyboard shortcuts, slash commands, configuration, theming,
MCP servers, skills, plugins, hooks, headless mode, sandboxing, and more.

## Repository layout

| Path | Contents |
|------|----------|
| `crates/codegen/xai-grok-pager-bin` | Composition-root package; builds the `kite` binary |
| `crates/codegen/xai-grok-pager` | The TUI: scrollback, prompt, modals, rendering |
| `crates/codegen/xai-grok-shell` | Agent runtime + leader/stdio/headless entry points |
| `crates/codegen/xai-grok-tools` | Tool implementations (terminal, file edit, search, ...) |
| `crates/codegen/xai-grok-workspace` | Host filesystem, VCS, execution, checkpoints |
| `crates/codegen/...` | The rest of the CLI crate closure (config, MCP, markdown, sandbox, ...) |
| `crates/common/`, `crates/build/`, `prod/mc/` | Small shared leaf crates pulled in by the closure |
| `third_party/` | Vendored upstream source (Mermaid diagram stack) — see below |

Crate, module, and environment-variable names still carry the inherited
`xai-grok` / `GROK_` prefixes; renaming them is planned separately.

> [!IMPORTANT]
> The root `Cargo.toml` (workspace members, dependency versions, lints,
> profiles) is **generated** — treat it as read-only. Prefer editing per-crate
> `Cargo.toml` files.

## Development

```sh
cargo check -p <crate>        # always target specific crates; full-workspace builds are slow
cargo test -p xai-grok-config # per-crate tests
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
- [`crates/codegen/xai-grok-tools/THIRD_PARTY_NOTICES.md`](crates/codegen/xai-grok-tools/THIRD_PARTY_NOTICES.md)
  — crate-local notice for the codex and opencode ports (license texts +
  Apache §4(b) change notice)
- [`third_party/NOTICE`](third_party/NOTICE) — vendored Mermaid-stack index
