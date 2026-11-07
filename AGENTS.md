# Repository Guidelines

## Project Structure & Module Organization

Kite is a Rust CLI/TUI coding agent for local and self-hosted models, derived from SpaceXAI's Grok Build (workspace crates use the `kite-*` prefix). Most application crates live under `crates/codegen/`: `kite-pager-bin` builds the `kite` executable, `kite-pager` implements the TUI, `kite-shell` owns the agent runtime, and `kite-tools` implements tools. Shared libraries live in `crates/common/`, build helpers in `crates/build/`, and protocol support in `prod/mc/`.

Each crate keeps Rust code in `src/` and integration tests in `tests/` where present. Pager assets and user documentation live in `crates/codegen/kite-pager/assets/` and `docs/user-guide/`. `third_party/` contains vendored sources; preserve their license notices.

## Build, Test, and Development Commands

Use the Rust 1.94.0 toolchain pinned in `rust-toolchain.toml`. Install DotSlash (`cargo install dotslash`) for `bin/protoc`; alternatively configure `protoc` through `PATH` or `PROTOC`. macOS and Linux are supported build hosts; Windows builds are best-effort.

- `cargo run -p kite-pager-bin`: build and launch the TUI.
- `cargo build -p kite-pager-bin --release --bin kite`: produce `target/release/kite`. See `KITE.md` for the Modal build and for regenerating the embedded system prompt after editing templates.
- `cargo check -p <crate>`: validate a specific crate quickly.
- `cargo test -p kite-config`: run a crate's tests; substitute the affected package.
- `cargo clippy -p <crate>`: check repository lint rules.
- `cargo fmt --all -- --check`: check formatting; use `cargo fmt --all` to apply it.

Prefer targeted checks over slow full-workspace builds.

## Coding Style & Naming Conventions

Use Rust 2024 conventions: four-space indentation, `snake_case` functions/modules, `PascalCase` types, and `SCREAMING_SNAKE_CASE` constants. Follow `rustfmt.toml` and `clippy.toml`. Use `dunce::canonicalize` for synchronous path canonicalization and `kite_dirs` for home-directory resolution, following existing helpers.

The root `Cargo.toml` is generated; treat it as read-only and edit per-crate manifests.

## Testing Guidelines

Use Rust unit tests and crate-local integration tests; asynchronous tests use `#[tokio::test]`, and existing rendering tests use Insta snapshots. Follow nearby `tests` modules, `*_tests.rs` files, and descriptive snake-case test names. Add regression coverage for behavior changes and review snapshot differences. No numeric coverage threshold is documented.

## Commit & Pull Request Guidelines

Kite's history starts fresh (no upstream `Synced from monorepo` commits). Write short imperative subjects and explain intent and validation in the body. Consult `CONTRIBUTING.md` for the contribution policy.

## Kite Rules

- **Portable changes only:** behavior changes are compiled-in defaults plus documentation in `KITE.md`, never machine-local configuration. A fresh clone and build must behave the same on any machine.
- **No xAI/grok.com services:** no feature may depend on xAI-hosted servers. Remove hosted clients rather than gating them; use local or open replacements (the `/login <url>` local endpoint, Exa/Parallel/`web_fetch` MCP, local session search, bundled skills).
- **Local model first:** the target is a single-slot llama.cpp server. Avoid hidden side requests and anything that rewrites already-sent history, since both break prompt-cache reuse and cause long stalls.
- **System prompt:** templates in `crates/codegen/kite-agent/templates/` ship as an obfuscated copy; after editing one, run `python crates/codegen/kite-agent/scripts/encrypt_templates.py` (templates must stay LF).
- **Builds and tests:** see `KITE.md` (`scripts/modal_build.py`: `--mode test`, `--mode lock` after dependency edits, `--target windows|linux`).
- **Clean up:** delete temporary scripts, probes and logs you create; leave nothing behind.

## Security Reports

Follow `SECURITY.md`; upstream Grok Build security programs do not cover Kite. Do not disclose vulnerabilities in public issues.
