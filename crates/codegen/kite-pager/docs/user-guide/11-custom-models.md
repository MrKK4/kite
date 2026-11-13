# Custom Models

Kite runs against models you supply: a local or tunneled OpenAI-compatible server (the usual setup), or any other provider you configure by hand (bring your own key). This guide explains how to connect a model server, select models, configure endpoints, and integrate third-party providers.

---

## Connecting a Model Server

Kite has no built-in hosted models and no account sign-in. The normal flow is to point it at an OpenAI-compatible server such as llama.cpp, vLLM, or Ollama.

From a terminal (connects, then opens Kite):

```bash
kite login https://your-tunnel.trycloudflare.com/v1
```

Or inside a running session:

```
/login https://your-tunnel.trycloudflare.com/v1
/login http://localhost:8080/v1
```

The argument is the API **base URL** (http or https), not an inference path: a URL ending in `/chat/completions` or `/models`, or one that carries credentials, a query string, or a fragment, is rejected. A URL with no path gets `/v1`.

What happens:

1. Kite requests `<base-url>/models` without any account credentials.
2. Every non-empty model ID in the response becomes a model named `local:<id>` (for example `local:qwen3-coder`), and the first one becomes the default.
3. The discovered models are saved in `~/.kite/config.toml`, **replacing** any `local:*` models saved from a previous URL. Discovery must succeed before any settings change.

Use `/model` (or `Ctrl+M`) to switch between discovered models. Repeat the login whenever your server or tunnel URL changes.

### Defaults for discovered models

Each `local:*` entry is written with settings suited to a single local server:

| Setting | Value |
|---------|-------|
| `api_backend` | `chat_completions` (OpenAI Chat Completions, `max_tokens`, system messages) |
| `context_window` | 262,144 tokens |
| `auto_compact_at_tokens` | 88% of the server-reported context (compaction starts here) |
| `max_completion_tokens` | 32,768 |
| `api_key` | `none` (placeholder; the server is expected to accept unauthenticated requests) |
| Reasoning effort | not sent; the server owns its chat template and thinking configuration |

Streamed `reasoning_content` is shown as reasoning. To fit a different model size, edit `context_window` and `auto_compact_at_tokens` in that model's entry in `~/.kite/config.toml` (re-running `/login` regenerates the entries and discards such edits). See `KITE.md` at the repository root for more on the local profile.

---

## Selecting a Model

List all available models:

```bash
kite models
```

### CLI Flag

```bash
kite -p "Hello" -m local:qwen3-coder
```

### Slash Command

In the TUI, switch models during a session:

```
/model local:qwen3-coder
```

Or use the alias:

```
/m local:qwen3-coder
```

### Model Picker (Ctrl+M)

Press `Ctrl+M` from the scrollback pane to open the model picker. It lists all available models (discovered and hand-configured) and lets you switch with a single keystroke. With the prompt focused, `Ctrl+M` toggles multiline input instead -- use `/model` to switch without leaving the prompt.

### Fleet allowlist (`requirements.toml`)

Managed hosts can pin the **selectable** set — not only the default — in signed `requirements.toml`. That list **replaces** any user `allowed_models` (it is not a union), so `/model`, `Ctrl+M`, and `-m` cannot offer models outside it.

```toml
[models]
default = "qwen3-coder"
allowed_models = ["qwen3-coder", "qwen3-*"]
```

A fleet pin matches the **model id** (not a user-chosen catalog key), so a local `[model.<name>]` entry cannot widen the set. User-config `allowed_models` still matches catalog key or model id. Omit the key to leave user config standing. An empty array is unrestricted. A present-but-unreadable pin fail-closes (nothing selectable). A default or `-m` value outside the pinned set is rejected once the model catalog is resolved — contact your administrator; the list is not user-editable. `/login` also refuses a discovered default that the allowlist excludes.

### Config Default

Set a persistent default in `~/.kite/config.toml` (`/login` sets this to the first discovered model):

```toml
[models]
default = "local:qwen3-coder"
```

---

## Supported API Backends

Kite supports three API backends. Set `api_backend` in your `[model.*]` config to choose which protocol the model uses:

| Value | API | Default |
|-------|-----|---------|
| `"chat_completions"` | OpenAI Chat Completions (`/v1/chat/completions`) | Yes |
| `"responses"` | OpenAI Responses (`/v1/responses`) | |
| `"messages"` | Anthropic Messages (`/v1/messages`) | |

When you omit `api_backend`, Kite uses `chat_completions`.

To send provider-specific authentication or version headers -- for example, Anthropic's `x-api-key` -- use the `extra_headers` field described below. Kite sends those headers verbatim with every request to the endpoint.

---

## Configuring Custom Models

Besides the `local:*` entries `/login` writes, you can add model endpoints by hand in `~/.kite/config.toml` under `[model.<name>]` sections:

```toml
[model.my-model]
model = "model-id"                        # Model identifier sent to the API
base_url = "https://api.example.com/v1"   # OpenAI-compatible endpoint
name = "Display Name"                     # Shown in the model picker
description = "Model description"          # Optional description
api_key = "sk-..."                        # API key for this provider (optional)
env_key = "MY_PROVIDER_API_KEY"           # Env var holding the API key (optional; string or array)
api_backend = "chat_completions"          # "chat_completions", "responses", or "messages"
reasoning_summary = "concise"             # Responses API only: "none", "auto", "concise", or "detailed"
temperature = 0.7                         # Sampling temperature
top_p = 0.95                              # Nucleus sampling parameter
max_completion_tokens = 8192              # Maximum tokens per response
context_window = 128000                   # Total context window in tokens
auto_compact_at_tokens = 110000           # Compact at this many tokens (optional)
extra_headers = { "x-api-key" = "sk-..." } # Extra request headers, sent verbatim (optional)
query_params = { api-version = "2026-07-22" } # Query params appended to every request URL (optional)
env_http_headers = { "X-Tenant" = "TENANT_TOKEN" }    # Headers from env vars, resolved at client build (optional)
```

### Credential Resolution

Kite resolves the API key in this order:

1. The `api_key` field in the model config (the `local:*` entries use the placeholder `none`)
2. The environment variable(s) named by `env_key` — a single string or an array of names. The first set, non-empty value wins (for example `env_key = ["ANTHROPIC_AUTH_TOKEN", "LC_ANTHROPIC_AUTH_TOKEN"]` for SSH `LC_*` forwarding)
3. The `XAI_API_KEY` environment variable as a global fallback (the name is inherited from upstream; Kite also accepts `GROK_CODE_XAI_API_KEY`)

### Context Window

The `context_window` value tells Kite when to trigger auto-compaction. When you define a new model and omit `context_window`, Kite defaults to 200,000 tokens, so set it explicitly to match your provider. `auto_compact_at_tokens` sets an absolute compaction point for that model.

### Request Size Limit

`max_request_bytes` is the largest request body your endpoint accepts. Kite evicts older inline images from the conversation to stay under it, so a session with many screenshots keeps working instead of being rejected. When you omit it, Kite picks the default for the `api_backend`: 30 MB for `messages`, and 50 MiB for `chat_completions` and `responses`. Set it only when your host enforces a different cap.

The cap is a property of the endpoint, so it also works on a shared `[model_providers.<id>]` block, where every model pointing at that provider inherits it; a `max_request_bytes` on the model itself overrides the provider's value.

```toml
[model_providers.messages-gateway]
base_url = "https://gateway.example/v1"
api_backend = "messages"
max_request_bytes = 25000000   # every model on this provider inherits it

[model.claude-sonnet]
model = "claude-sonnet"
model_provider = "messages-gateway"   # inherits 25 MB

[model.claude-opus]
model = "claude-opus"
model_provider = "messages-gateway"
max_request_bytes = 20000000   # per-model override
```

### Global Default Headers

To apply the same headers to *every* model in the catalog -- discovered, fetched from a `/v1/models` endpoint, or custom -- set them once under the global `[models]` section instead of repeating them per model:

```toml
[models]
extra_headers = { "X-Request-Tags" = "team=example,env=prod" }
```

These act as a base for each model's inference requests. A per-model `[model.<id>].extra_headers` entry overrides the global default **per key** (matched case-insensitively): a key set on the model wins, while any global-only keys are still inherited by that model. Like the per-model field, they ride on that model's inference calls only, which makes them handy for attribution tags (for example, cost tracking) without re-declaring them whenever a new model appears.

### Global Default Values

A few common per-model settings can also be set once under `[models]` as a default for *every* model. A per-model `[model.<id>]` value always wins; the global only fills in where a model (or the server's model list) left the field unset:

```toml
[models]
temperature                 = 0.7
top_p                       = 0.95
max_completion_tokens       = 8192
max_retries                 = 8
rate_limit_retry_threshold  = 4
inference_idle_timeout_secs = 600
subagent_rate_limit_max_attempts = 8
stream_tool_calls           = true
```

This is a small, fixed set of environment-wide knobs. Settings that identify a specific model (`model`, `base_url`, `api_key`, `context_window`, ...) cannot be defaulted this way, and a few settings with their own dedicated configuration -- auto-compaction (`[session]`), the system-prompt label (`[agent]`), and reasoning effort (`[models].default_reasoning_effort`) -- keep their existing homes.

`rate_limit_retry_threshold` and `subagent_rate_limit_max_attempts` select different 429 retry paths for subagents. Configuring `rate_limit_retry_threshold` makes the sampler own those retries and disables the separate subagent wait loop, including its 150-second cumulative wait budget. `subagent_rate_limit_max_attempts` applies only when the sampler threshold is unset.

> **Note on `stream_tool_calls`:** this one affects request *shape*, not just sampling. A few endpoints (some BYOK providers) expect it left unset; if a global `stream_tool_calls = true` causes problems for such a model, opt that model out with `stream_tool_calls = false` in its `[model.<id>]` block. The `local:*` entries already set it to `false`.

### Request Query Parameters

Some gateways route or version on the query string. `query_params` appends percent-encoded query parameters to every request Kite makes for a model. For example, a gateway that selects an API version this way:

```toml
[model.my-gateway]
model = "my-model"
base_url = "https://gateway.example/v1"
api_backend = "responses"
env_key = "GATEWAY_API_KEY"
query_params = { api-version = "2026-07-22" }
```

A key that also appears in the `base_url` query string is overridden (last value wins) rather than duplicated. Query parameters are saved in the session, so do not put secrets in them: use `env_http_headers` for a secret.

### Environment-Variable Headers

`env_http_headers` maps a request header to the name of an environment variable that supplies its value, so a per-request secret never has to be written into `config.toml`:

```toml
[model.gateway]
model = "my-model"
base_url = "https://gateway.example/v1"
env_http_headers = { "X-Tenant-Token" = "GATEWAY_TENANT_TOKEN" }
```

Kite reads each variable when it builds the client for a session and places the value in the request headers only, never on disk. A header is skipped when its variable is unset or blank, and a resolved value overrides an `extra_headers` entry of the same name. Use `extra_headers` for a static value and `env_http_headers` for one that comes from the environment.

Both fields also work on a shared `[model_providers.<id>]` block. A model that points at a provider with `model_provider = "<id>"` inherits the provider's `query_params` and `env_http_headers` when it sets none of its own, matching how `extra_headers` is inherited.

### Model Notice

`notice` puts a message above the prompt for as long as the model is selected. The banner cannot be dismissed. It goes away when you switch to a model without a notice.

```toml
[model.legacy]
model = "legacy-model"
base_url = "https://gateway.example/v1"
notice = { severity = "warning", text = "This model is deprecated on Oct 15. Switch to my-model.", label = "deprecated" }
```

`severity` sets the banner color and is `info`, `warning`, or `critical`. It defaults to `info`. `text` is required, and long text wraps. `label` is an optional short tag shown before the text. A custom models endpoint can send the same object as `notice` or `_meta.notice` on a model entry. To remove a notice a model carries, set `notice = { text = "" }`.

---

## Overriding Existing Models

You can override specific fields of a model that is already in the catalog (for example one fetched from a custom models endpoint) without redefining everything. Only specify the fields you want to change:

```toml
# Override only the API key for a model from the endpoint's model list
[model.my-model]
api_key = "my-api-key"

# Override temperature and the context window
[model.my-model]
temperature = 0.5
context_window = 65536
```

Kite starts with the existing configuration (including its `base_url`), then applies only the fields you specify. Unspecified fields are inherited.

### Priority Order

1. Your config (`[model.*]`, including the `local:*` entries `/login` writes) -- highest priority
2. Models fetched from a custom `/v1/models` endpoint
3. Hardcoded defaults -- lowest priority

---

## Provider Examples

### llama.cpp / vLLM (OpenAI-Compatible Server)

The simplest route is `/login <base-url>`, which discovers the server's models for you. To define one by hand instead:

```toml
[model.local-qwen]
model = "qwen3-coder"
base_url = "http://localhost:8080/v1"
name = "Qwen3 Coder (local)"
api_key = "none"
context_window = 262144
auto_compact_at_tokens = 220000
```

### Ollama (Local Models)

Run models locally with Ollama:

```toml
[model.ollama-codellama]
model = "codellama"
base_url = "http://localhost:11434/v1"
name = "CodeLlama (Ollama)"
```

Make sure Ollama is running (`ollama serve`) and the model is pulled (`ollama pull codellama`). `/login http://localhost:11434/v1` also works.

### Anthropic (Claude)

Use Claude models directly via the Anthropic Messages API:

```toml
[model.claude-opus]
model = "claude-opus-4-6"
base_url = "https://api.anthropic.com/v1"
name = "Claude Opus 4.6"
api_backend = "messages"
context_window = 200000
extra_headers = { "x-api-key" = "sk-ant-...", "anthropic-version" = "2023-06-01" }
```

The `messages` backend uses the Anthropic Messages protocol. Anthropic authenticates with an `x-api-key` header rather than `Authorization: Bearer`, so pass your key through `extra_headers`, which Kite sends verbatim.

### OpenAI (Chat Completions)

```toml
[model.gpt-4o]
model = "gpt-4o"
base_url = "https://api.openai.com/v1"
name = "GPT-4o"
env_key = "OPENAI_API_KEY"
```

`api_backend` defaults to `"chat_completions"`, so you don't need to set it explicitly for OpenAI.

### OpenAI (Responses API)

If your provider supports the newer Responses API:

```toml
[model.gpt-4o-responses]
model = "gpt-4o"
base_url = "https://api.openai.com/v1"
name = "GPT-4o (Responses)"
api_backend = "responses"
env_key = "OPENAI_API_KEY"
```

On the Responses API, Kite asks for a `concise` reasoning summary by default; that is what the reasoning text shown in the UI comes from. `reasoning_summary` changes the request: `detailed` or `auto` for a fuller summary, or `none` to omit the field for gateways that reject it.

### AWS Bedrock (Mantle)

Bedrock's OpenAI-compatible gateway rejects `reasoning.summary`, so set `reasoning_summary = "none"`. It authenticates with a Bedrock API key as a bearer token; the example below mints a short-lived one through a named auth provider:

```toml
[auth_provider.bedrock]
command = "aws-bedrock-token"   # prints a Bedrock API key on stdout (e.g. via aws-bedrock-token-generator)
token_ttl_secs = 3600

[model."bedrock-my-model"]
model = "my-bedrock-model-id"
base_url = "https://bedrock-mantle.us-west-2.api.aws/openai/v1"
name = "My Model (Bedrock)"
api_backend = "responses"
reasoning_summary = "none"
auth_provider = "bedrock"
context_window = 500000
```

### Together AI

```toml
[model.together-mixtral]
model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
base_url = "https://api.together.xyz/v1"
name = "Mixtral 8x7B"
env_key = "TOGETHER_API_KEY"
```

---

## Custom Models Endpoint

Besides `/login`, you can point Kite at an OpenAI-compatible `/v1/models` endpoint through environment variables or config. Use this when your models sit behind a corporate gateway or a self-hosted inference service that requires a bearer key.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROK_MODELS_BASE_URL` | Yes | Base URL for inference. Kite fetches the model list from `{base_url}/models`. |
| `XAI_API_KEY` | Yes | API key sent as `Authorization: Bearer` (name inherited from upstream). Kite also accepts `GROK_CODE_XAI_API_KEY`. |
| `GROK_MODELS_LIST_URL` | No | Override the model-list URL when it differs from `{base_url}/models`. |

### Setup

```bash
export GROK_MODELS_BASE_URL="https://api.acme.com/v1"
export XAI_API_KEY="sk-..."
kite
```

### Config File Alternative

```toml
[endpoints]
models_base_url = "https://api.acme.com/v1"

# Override only the API key for a specific model
[model.my-model]
api_key = "my-api-key"
```

When you use `[endpoints]` with partial model overrides, Kite inherits the `base_url` from the endpoints config. You do not need to specify it in each `[model.*]` section. `XAI_API_KEY` is still required. A per-model `api_key` or `env_key` authenticates inference requests for that model. The startup model-list fetch always uses `XAI_API_KEY`.

### Auth Behavior

When you set `models_base_url`, Kite authenticates the model-list request with `XAI_API_KEY` only (`Authorization: Bearer`). With an external auth provider (`auth_provider_command`) and no `XAI_API_KEY`, it sends the provider's token instead. Otherwise, if `XAI_API_KEY` is unset, the fetch fails with an error asking you to set it. Inference requests to the custom host authenticate separately. An `api_key` or `env_key` on each model makes those requests use an API key too.

For an unauthenticated server, use `/login <base-url>` instead; it needs no key.

---

## Web Search

The hosted `web_search` tool is off in Kite (it needs an xAI account), and `/login` disables it explicitly. For web access use `web_fetch` or the default `exa` and `parallel` MCP servers (see `KITE.md`).

---

## Using Custom Models

```bash
# List available models (including custom)
kite models

# Use in the TUI via slash command
/model my-model

# Use in headless mode
kite -p "Hello" -m my-model

# Set as default in config.toml:
[models]
default = "my-model"
```

---

## Shared Deployment Example

A complete config for a team deployment that routes through a company proxy with an external auth provider:

```toml
[auth]
auth_provider_command = "/usr/local/bin/my-company-auth-provider"
auth_provider_label = "Acme Corp"
auth_token_ttl = 3600

[models]
default = "company-model"

[model.company-model]
model = "qwen3-coder"
base_url = "https://llm-proxy.acme.com/"
name = "Qwen3 Coder (Proxy)"
context_window = 128000
```

---

## Troubleshooting

### Model Not Found

```bash
# List available models
kite models

# Check config.toml for typos in [model.*] sections
```

If the `local:*` models are missing or stale, run `/login <base-url>` again.

### Connection Errors

Verify the endpoint is reachable and returns a model list:

```bash
curl -s http://localhost:8080/v1/models
```

Add `-H "Authorization: Bearer $YOUR_KEY"` for a provider that requires a key. A `/login` failure ("Local model connection failed: ...") leaves your settings unchanged.

### Debug Logging

```bash
RUST_LOG=debug GROK_LOG_FILE=/tmp/kite.log kite
tail -f /tmp/kite.log
```

Look for log entries containing `model` or `sampling` to trace model selection and API calls.
