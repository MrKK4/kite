# Authentication

Kite has no account sign-in. It connects to a model server you run or choose: any OpenAI-compatible endpoint (for example a local llama.cpp server, or one exposed through a Cloudflare tunnel). Connecting is done with `kite login <base-url>` or `/login <base-url>`.

Kite does not include account sign-in, OIDC or OAuth single sign-on for a hosted service, `kite logout`, or device-code sign-in.

---

## Connect a model server

From a terminal (connects, then opens Kite):

```bash
kite login https://your-tunnel.trycloudflare.com/v1
```

Or inside Kite:

```text
/login https://your-tunnel.trycloudflare.com/v1
/login http://localhost:8080/v1
```

What happens:

1. Kite requests `<base-url>/models` without account credentials.
2. It selects the first nonempty model ID and saves the discovered models in `~/.kite/config.toml`, replacing models saved from a previous URL.
3. Use `/model` to select another discovered model.

Discovery must succeed before any settings change, so a wrong or unreachable URL leaves your configuration untouched. Repeat the login whenever the server URL changes (for example, when your Cloudflare tunnel URL changes).

The endpoint is expected to accept unauthenticated requests: the inference credential Kite sends for discovered models is the placeholder `none`.

### Request format

The local profile uses OpenAI Chat Completions with `max_tokens` and system messages, and sends no reasoning-effort parameter or `store` field. The server owns its chat template and thinking configuration; streamed `reasoning_content` is supported.

### Context size

Models discovered this way use the context size the server reports (llama.cpp `/props`, else `/models`; 262,144 if unknown) and compact at 88% of it. Edit `context_window` and `auto_compact_at_tokens` in the model's entry in `~/.kite/config.toml` for a different model size. See [Custom Models](11-custom-models.md).

---

## Servers that need an API key

If your endpoint requires a key, define the model by hand in `~/.kite/config.toml` and give it an `api_key` or `env_key`:

```toml
[model.my-model]
model = "my-model"
base_url = "https://llm.example.com/v1"
env_key = "MY_PROVIDER_API_KEY"   # or: api_key = "sk-..."
```

A per-model `api_key` or `env_key` is used whenever it is present. See [Custom Models](11-custom-models.md) for the full model configuration, including multiple providers.

---

## Credential storage

MCP OAuth tokens (for MCP servers that use OAuth) are stored in `~/.kite/mcp_credentials.json` with owner-only permissions (`0600` on Unix). Anyone with filesystem access to that path can use the credentials, so:

- Prefer full-disk encryption (FileVault, BitLocker, LUKS, or equivalent).
- Do not copy `mcp_credentials.json` or a `config.toml` that contains an `api_key` into shared directories, tickets, or chat.
- On multi-user hosts, keep `$HOME` / `$KITE_HOME` private to your account.

---

## Grove Git credentials

`kite login` does not create a Git credential. The Grove daemon builds its own credential cell from `auth_mode` in Grove config. Those credentials are managed with `grove status` and `grove reload-credentials` -- see [kite clone](27-kite-clone.md#authentication) for the failure classes and their next steps.

---

## Troubleshooting

### Debug logging

Set `RUST_LOG` to control the verbosity of the file log and headless stderr output. (The TUI's on-screen tracing pane uses a fixed filter and ignores `RUST_LOG`.) In the TUI, file logging defaults to `DEBUG`; in headless mode (`-p`), `RUST_LOG` defaults to `off` so only the answer is printed — set `RUST_LOG=error` (or broader) to see logs on stderr.

In the TUI, set `GROK_LOG_FILE` to an absolute path to write logs to that file:

```bash
GROK_LOG_FILE=/tmp/kite.log RUST_LOG=debug kite
tail -f /tmp/kite.log
```

`GROK_LOG_FILE` is treated as a literal file path. A relative value such as `1` writes a file named `1` in the current directory.

In headless mode, logs go to stderr. Redirect them to a file:

```bash
RUST_LOG=debug kite -p "hello" 2> /tmp/kite.log
```

### Common fixes

- **`/login` fails or finds no models** -- Check that `<base-url>/models` responds (for example `curl <base-url>/models`), that the URL includes the `/v1` path your server expects, and that a tunnel URL is still current.
- **Requests fail with 401** -- The server requires a key; configure the model with `api_key` or `env_key` as shown above.
- **Wrong model selected** -- Use `/model` to pick another discovered model.
