# Repository Guidelines

## Project Structure & Module Organization

Kite is a Rust CLI/TUI coding agent for local and self-hosted models, derived from SpaceXAI's Grok Build (crate names keep the inherited `xai-grok-*` prefix). Most application crates live under `crates/codegen/`: `xai-grok-pager-bin` builds the `kite` executable, `xai-grok-pager` implements the TUI, `xai-grok-shell` owns the agent runtime, and `xai-grok-tools` implements tools. Shared libraries live in `crates/common/`, build helpers in `crates/build/`, and protocol support in `prod/mc/`.

Each crate keeps Rust code in `src/` and integration tests in `tests/` where present. Pager assets and user documentation live in `crates/codegen/xai-grok-pager/assets/` and `docs/user-guide/`. `third_party/` contains vendored sources; preserve their license notices.

## Build, Test, and Development Commands

Use the Rust 1.94.0 toolchain pinned in `rust-toolchain.toml`. Install DotSlash (`cargo install dotslash`) for `bin/protoc`; alternatively configure `protoc` through `PATH` or `PROTOC`. macOS and Linux are supported build hosts; Windows builds are best-effort.

- `cargo run -p xai-grok-pager-bin`: build and launch the TUI.
- `cargo build -p xai-grok-pager-bin --release --bin kite`: produce `target/release/kite`. See `KITE.md` for the Modal build and for regenerating the embedded system prompt after editing templates.
- `cargo check -p <crate>`: validate a specific crate quickly.
- `cargo test -p xai-grok-config`: run a crate's tests; substitute the affected package.
- `cargo clippy -p <crate>`: check repository lint rules.
- `cargo fmt --all -- --check`: check formatting; use `cargo fmt --all` to apply it.

Prefer targeted checks over slow full-workspace builds.

## Coding Style & Naming Conventions

Use Rust 2024 conventions: four-space indentation, `snake_case` functions/modules, `PascalCase` types, and `SCREAMING_SNAKE_CASE` constants. Follow `rustfmt.toml` and `clippy.toml`. Use `dunce::canonicalize` for synchronous path canonicalization and `xai_dirs` for home-directory resolution, following existing helpers.

The root `Cargo.toml` is generated; treat it as read-only and edit per-crate manifests.

## Testing Guidelines

Use Rust unit tests and crate-local integration tests; asynchronous tests use `#[tokio::test]`, and existing rendering tests use Insta snapshots. Follow nearby `tests` modules, `*_tests.rs` files, and descriptive snake-case test names. Add regression coverage for behavior changes and review snapshot differences. No numeric coverage threshold is documented.

## Commit & Pull Request Guidelines

Recent history uses `Synced from monorepo`; it establishes no feature-commit naming convention. Keep local change descriptions concise and explain intent and validation. Consult `CONTRIBUTING.md` for the contribution policy.

## Security Reports

Follow `SECURITY.md`; upstream Grok Build security programs do not cover Kite. Do not disclose vulnerabilities in public issues.
