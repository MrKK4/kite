# Configuration reference

This file ships with the CLI and is extracted to `~/.kite/docs/user-guide/26-config-reference.md` on launch. It is the complete field list for `config.toml`, `managed_config.toml`, and `requirements.toml`. For conceptual guidance see [05-configuration.md](05-configuration.md).

## How to configure

Three files configure Kite, and they are written by different people.

| File | Who writes it | Where it lives | Use it to |
| --- | --- | --- | --- |
| `config.toml` | The developer | `~/.kite/config.toml`, and `.grok/config.toml` in a project | Set personal defaults. Anything here can be changed by the person using the machine. |
| `managed_config.toml` | You, with a deployment tool | `/etc/grok/managed_config.toml`, or `$KITE_HOME/managed_config.toml` | Ship a starting point to a fleet. A developer's own file overrides it. |
| `requirements.toml` | You, signed | `/etc/grok/requirements.toml`, macOS device management, or `$KITE_HOME/requirements.toml` | Set values a developer cannot change. Keys marked `pin` below hold against every other file, the environment, and the command line. |

Choose `managed_config.toml` for defaults you want people to be able to adjust, and `requirements.toml` for the ones you do not.

Kite also reads these layers, later rows winning except where a requirements pin or the Managed column says otherwise.

1. Compiled defaults.
2. `/etc/grok/managed_config.toml`, then `$KITE_HOME/managed_config.toml` (fleet defaults).
3. `$KITE_HOME/config.toml` (your settings; `/settings` writes here). Default `$KITE_HOME` is `~/.kite`.
4. Project `.grok/config.toml`: only `[mcp_servers]`, `[plugins]`, `[permission]`, and `[mcp] max_output_bytes`.
5. `GROK_CONFIG` (inline JSON) or `GROK_CONFIG_PATH` (JSON or TOML file). Allowlisted keys only.
6. `$KITE_HOME/requirements.toml`, then `/etc/grok/requirements.toml`, then macOS MDM `ai.x.grok`. Admin layer. Keys marked `pin` in the table cannot be overridden; keys marked `yes` are also valid in this file.
7. `GROK_*` environment variables.
8. CLI flags such as `--model`, `--sandbox`, `--yolo`.

Run `kite inspect` or `kite inspect --json` to see which files and values won.

## config.toml

User-level configuration lives in `$KITE_HOME/config.toml` (default `~/.kite/config.toml`; Windows `%USERPROFILE%\.kite\config.toml`). Project-scoped overrides live in `.grok/config.toml` and only contribute `[mcp_servers]`, `[plugins]`, `[permission]`, and `[mcp] max_output_bytes`.

**Requirements** marks whether the same key can be set in `requirements.toml`: `pin` cannot be overridden (including env and CLI where the resolver honors the pin); `yes` is accepted in that file; `—` is not read from `requirements.toml`. **Managed** marks whether a fleet `managed_config.toml` value stands (`fleet`) or the user's file wins (`user`).

### `agent`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `agent.definition` | `string (path)` | `yes` | `user` | Path to an agent definition markdown file with YAML frontmatter. |
| `agent.name` | `string` | `yes` | `user` | Built-in or discovered agent definition name. Also GROK_AGENT and `--agent-profile`. |
| `agent.system_prompt_label` | `string` | `yes` | `user` | Global system-prompt identity; per-model override wins. |

### `auth`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `auth` | `table` | `yes` | `user` | Alias of `[grok_com_config]`; each `grok_com_config.*` key below also works as `auth.*`. External auth-provider settings for a custom endpoint. |
| `auth.auth_provider_command` | `string` | `yes` | `user` | External auth binary; stdout is the token. With `endpoints.models_base_url` or `models_list_url` set, that endpoint's list decides which models are offered. Also GROK_AUTH_PROVIDER_COMMAND; also valid as `grok_com_config.auth_provider_command`. |
| `auth.auth_provider_label` | `string` | `yes` | `user` | Login button label for an external auth provider. Also GROK_AUTH_PROVIDER_LABEL; also valid as `grok_com_config.auth_provider_label`. |
| `auth.auth_token_ttl` | `number` | `yes` | `user` | Token TTL in seconds for providers that return a bare token. Also GROK_AUTH_TOKEN_TTL; also valid as `grok_com_config.auth_token_ttl`. |
| `auth.token_header` | `string` | `yes` | `user` | Header name that carries the CLI auth token; default `xai-grok-cli`; also valid as `grok_com_config.token_header`. |

### `auth_provider`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `auth_provider.<name>` | `table` | `yes` | `user` | Named credential helper used by `[model.<id>] auth_provider`. |

### `auto_mode`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `auto_mode.enabled` | `boolean` | `yes` | `user` | Enable Auto permission mode. |

### `cli`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `cli.grove` | `boolean` or `grove` / `grove-fuse` / `grove-nfs` / `nfs` / `all` / `copy` / `true` / `false` / `1` / `0` / `on` / `off` | `yes` | `user` | Convenience that turns **both** `kite clone` and session / `-w` Grove on when the specific knobs are unset. Also `GROK_GROVE`. `false` / `copy` / `off` means enable-all is off (fall through); it does not force both surfaces off. `[cli] grove_worktree` and `GROK_WORKTREE_TYPE` still win for worktrees; `GROK_CLONE` still wins for clone. |
| `cli.grove_worktree` | `boolean` or `grove` / `grove-fuse` / `grove-nfs` / `nfs` / `copy` / `true` / `false` / `1` / `0` / `on` / `off` | `yes` | `user` | Session / `-w` Grove vs copy. Default copy. Distinct from creation-mode `cli.worktree_type`. Also `GROK_WORKTREE_TYPE`. Layer order: request → env → local → enable-all (`GROK_GROVE` / `[cli] grove`). Does not enable `kite clone`. |
| `cli.nfs_worktree` | same as `cli.grove_worktree` | `yes` | `user` | Read alias of `cli.grove_worktree`. |
| `cli.session_picker_grouped` | `boolean` | `yes` | `user` | Group sessions by repo in the picker and CLI listings. |
| `cli.session_registry` | `boolean` | `yes` | `user` | Participate in the cross-process session registry. |
| `cli.show_tips` | `boolean` | `pin` | `user` | Startup tips. |
| `cli.use_leader` | `boolean` | `pin` | `user` | Use the leader process for config reload and MCP watches. |
| `cli.worktree_type` | `string` | `yes` | `user` | Creation-mode when set to `linked`, `standalone`, or `git`. The spellings `grove`, `grove-fuse`, `grove-nfs`, `nfs`, and `copy` also feed the session / `-w` Grove gate (same as `cli.grove_worktree`); they are not creation-mode values. |

### `compat`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `compat.claude.agents` | `boolean` | `yes` | `user` | Scan CLAUDE.md. Also GROK_CLAUDE_AGENTS_ENABLED. |
| `compat.claude.hooks` | `boolean` | `yes` | `user` | Scan Claude hooks. Also GROK_CLAUDE_HOOKS_ENABLED. |
| `compat.claude.mcps` | `boolean` | `yes` | `user` | Scan Claude MCP config. Also GROK_CLAUDE_MCPS_ENABLED. |
| `compat.claude.rules` | `boolean` | `yes` | `user` | Scan Claude rules. Also GROK_CLAUDE_RULES_ENABLED. |
| `compat.claude.skills` | `boolean` | `yes` | `user` | Scan Claude skills. Also GROK_CLAUDE_SKILLS_ENABLED. |
| `compat.codex.hooks` | `boolean` | `yes` | `user` | Scan Codex hooks when present. |
| `compat.codex.skills` | `boolean` | `yes` | `user` | Scan Codex skills directories when present. |
| `compat.cursor.agents` | `boolean` | `yes` | `user` | Scan agent definitions from Cursor compat sources. Also GROK_CURSOR_AGENTS_ENABLED. |
| `compat.cursor.hooks` | `boolean` | `yes` | `user` | Scan Cursor hooks. Also GROK_CURSOR_HOOKS_ENABLED. |
| `compat.cursor.mcps` | `boolean` | `yes` | `user` | Scan Cursor mcp.json. Also GROK_CURSOR_MCPS_ENABLED. |
| `compat.cursor.rules` | `boolean` | `yes` | `user` | Scan `.cursor/rules/`. Also GROK_CURSOR_RULES_ENABLED. |
| `compat.cursor.skills` | `boolean` | `yes` | `user` | Scan Cursor skills directories. Also GROK_CURSOR_SKILLS_ENABLED. |

### `dashboard`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `dashboard.enabled` | `boolean` | `yes` | `user` | Show the agent dashboard. |
| `dashboard.grouping` | `state / directory` | `yes` | `user` | How dashboard rows group. |

### `default_auto_mode`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `default_auto_mode` | `boolean` | `yes` | `user` | Start sessions in auto permission mode when no per-session override is set. |

### `diagnostics`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `diagnostics.crash_handler` | `boolean` | `yes` | `user` | Write a panic report under `$KITE_HOME/crash/`. Also GROK_CRASH_HANDLER. |

### `disable_web_search`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `disable_web_search` | `boolean` | `yes` | `user` | Drop the web_search tool for this process. Also `--disable-web-search`. |

### `disabled_mcp_servers`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `disabled_mcp_servers` | `string[]` | `yes` | `user` | MCP server names to skip without deleting their `[mcp_servers]` blocks. |

### `disabled_mcp_tools`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `disabled_mcp_tools` | `map<string, string[]>` | `yes` | `user` | Per-server MCP tool deny lists keyed by server name. |

### `doom_loop_recovery`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `doom_loop_recovery.enabled` | `boolean` | `yes` | `user` | Resample confident tool-call loops; set false to disable. |

### `endpoints`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `endpoints.cli_chat_proxy_base_url` | `string` | `pin` | `user` | Session-service API base URL. |
| `endpoints.models_base_url` | `string` | `pin` | `user` | Custom inference base URL. With `auth_provider_command` set, `{models_base_url}/models` decides which models are offered. Also GROK_MODELS_BASE_URL. |
| `endpoints.models_list_url` | `string` | `pin` | `user` | Override model-list URL. With `auth_provider_command` set, this list decides which models are offered. Also GROK_MODELS_LIST_URL. Alias `models_endpoint`. |

### `features`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `features.active_agent_messages` | `boolean` | `pin` | `user` | Enable or disable `active_agent_messages`. Default false. Also `GROK_ACTIVE_AGENT_MESSAGES`. |
| `features.ask_user_question` | `boolean` | `pin` | `user` | Enable or disable `ask_user_question`. Default true. Also `GROK_ASK_USER_QUESTION`. |
| `features.auto_wake` | `boolean` | `pin` | `user` | Enable or disable `auto_wake`. Default true. Also `GROK_AUTO_WAKE`. |
| `features.cancel_rewind` | `boolean` | `pin` | `user` | Enable or disable `cancel_rewind`. Default true. Also `GROK_CANCEL_REWIND`. |
| `features.codebase_indexing` | `boolean / string[]` | `pin` | `user` | Codebase graph indexing; true indexes git repos, or pass include/exclude globs. |
| `features.compaction_detail` | `none / minimal / balanced / verbose` | `yes` | `user` | Verbatim detail level for `segments` compaction. Also GROK_COMPACTION_DETAIL. |
| `features.compaction_mode` | `summary / transcript / segments` | `yes` | `user` | Compaction strategy. Also GROK_COMPACTION_MODE. |
| `features.compaction_tool_choice` | `string` | `yes` | `user` | Tool-choice hint used during compaction. |
| `features.compaction_verbatim_input` | `boolean` | `pin` | `user` | Enable or disable `compaction_verbatim_input`. Default true. Also `GROK_COMPACTION_VERBATIM_INPUT`. |
| `features.dock` | `boolean` | `pin` | `user` | Enable or disable `dock`. Default false. Also `GROK_DOCK`. |
| `features.file_acceleration` | `boolean` | `pin` | `user` | Hand local sessions' file systems to a file accelerator when the build installs one. Default false. Also `GROK_FILE_ACCELERATION`. |
| `features.lsp_tools` | `boolean` | `pin` | `user` | Enable or disable `lsp_tools`. Default false. Also `GROK_LSP_TOOLS`. |
| `features.mcp_auto_restart` | `boolean` | `yes` | `user` | Auto-restart stdio MCP servers after transport failure. Also GROK_MCP_AUTO_RESTART. |
| `features.mcp_liveness_watchers` | `boolean` | `yes` | `user` | Poll MCP transports and push server_status updates. Emergency kill switch when false. |
| `features.mcp_push_server_status` | `boolean` | `yes` | `user` | Pager subscribes to MCP server_status push. Process env GROK_MCP_PUSH_SERVER_STATUS wins at launch. |
| `features.mcp_recursive_config_watch` | `boolean` | `yes` | `user` | Watch `<cwd>/` and `<cwd>/.grok/` for project MCP config edits. Name is a misnomer; watches are non-recursive. |
| `features.non_git_warning` | `boolean` | `yes` | `user` | Show a blocking warning when Kite starts outside a Git repository. |
| `features.remember_mode` | `boolean` | `—` | `—` | Remember the last permission mode across sessions. Read from user `config.toml` only. |
| `features.session_recap` | `boolean` | `pin` | `user` | Enable or disable `session_recap`. Default false in Kite. Also `GROK_SESSION_RECAP`. |
| `features.session_search` | `boolean` | `pin` | `user` | Enable or disable `session_search`. Default true. Also `GROK_SESSION_SEARCH`. |
| `features.subagent_worktree_snapshot` | `boolean` | `pin` | `user` | Enable or disable `subagent_worktree_snapshot`. Default false. Also `GROK_SUBAGENT_WORKTREE_SNAPSHOT`. |
| `features.support_permission` | `boolean` | `yes` | `user` | Allow the agent to ask permission for tool executions. |
| `features.terminal_theme` | `boolean` | `pin` | `user` | Reveal the terminal-native `terminal` color theme during its rollout. Default false. Also `GROK_TERMINAL_THEME`. |
| `features.title_refresh` | `boolean` | `pin` | `user` | Early-session auto-title refresh. Pin this in requirements to beat GROK_TITLE_REFRESH. |
| `features.turn_summary` | `boolean` | `pin` | `user` | Enable or disable `turn_summary` (per-turn summaries and title refresh). Default false in Kite. Also `GROK_TURN_SUMMARY`. |
| `features.two_pass_compaction` | `boolean` | `pin` | `user` | Enable or disable `two_pass_compaction`. Default false in Kite. Also `GROK_TWO_PASS_COMPACTION`. |
| `features.web_fetch` | `boolean` | `pin` | `user` | Enable or disable `web_fetch`. Default true in Kite. Also `GROK_WEB_FETCH`. |
| `features.write_file` | `boolean` | `pin` | `user` | Enable or disable `write_file`. Default true. Also `GROK_WRITE_FILE`. |

### `file_acceleration`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `file_acceleration.routes` | `string` | `yes` | `user` | Route override passed unparsed to the installed file accelerator; empty is unset. Also `GROK_FILE_ACCELERATION_ROUTES`. |

### `goal`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `goal.enabled` | `boolean` | `yes` | `user` | Enable `/goal`. |

### `grok_com_config`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `grok_com_config` | `table` | `yes` | `user` | External auth-provider settings (the config key keeps its upstream name). `[auth]` is an alias. |
| `grok_com_config.auth_provider_command` | `string` | `yes` | `user` | External auth binary; stdout is the token. With `endpoints.models_base_url` or `models_list_url` set, that endpoint's list decides which models are offered. Also GROK_AUTH_PROVIDER_COMMAND. |
| `grok_com_config.auth_provider_label` | `string` | `yes` | `user` | Login button label for an external auth provider. Also GROK_AUTH_PROVIDER_LABEL. |
| `grok_com_config.auth_token_ttl` | `number` | `yes` | `user` | Token TTL in seconds for providers that return a bare token. Also GROK_AUTH_TOKEN_TTL. |
| `grok_com_config.token_header` | `string` | `yes` | `user` | Header name that carries the CLI auth token; default `xai-grok-cli`. |

### `harness`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `harness.disable_workspace_teleport` | `boolean` | `pin` | `user` | Kill switch for per-turn workspace snapshots. |

### `hints`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `hints.fork_worktree_mode` | `ask / always / never` | `yes` | `user` | Whether `/fork` offers a worktree. |
| `hints.new_session_worktree_mode` | `ask / always / never` | `yes` | `user` | Whether `/new` offers a worktree. |

### `hooks`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `hooks.<event>` | `array of tables` | `yes` | `user` | Matcher groups for a lifecycle event such as PreToolUse or Stop. See Hooks. |
| `hooks.<event>[].hooks[].command` | `string` | `yes` | `user` | Command to run for this hook. `$VAR` is not expanded at load. |
| `hooks.<event>[].hooks[].type` | `command` | `yes` | `user` | Hook handler type. Command hooks are supported. |
| `hooks.<event>[].matcher` | `string` | `yes` | `user` | Tool-name matcher for this hook group. |

### `long_reasoning_reminder`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `long_reasoning_reminder.enabled` | `boolean` | `yes` | `user` | Inject a mid-turn reminder to reason briefly after a model call with long hidden reasoning. Default false. Also `GROK_LONG_REASONING_REMINDER` (a bool word, or a JSON object in this table's shape). |
| `long_reasoning_reminder.tokens` | `integer` | `yes` | `user` | Reasoning tokens in one model call that count as long. Default 1000, clamped to 100–200000. Also `tokens` in the `GROK_LONG_REASONING_REMINDER` JSON object. |
| `long_reasoning_reminder.delay` | `integer` | `yes` | `user` | Model calls to wait after the long call before the reminder. Default 1, clamped to 0–10. Also `delay` in the `GROK_LONG_REASONING_REMINDER` JSON object. |

### `marketplace`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `marketplace.sources` | `array of tables` | `yes` | `user` | `[[marketplace.sources]]` plugin marketplace repos. |
| `marketplace.require_sha` | `boolean` | `yes` | `user` | Tighten-only: remote plugin installs and updates must pin a full commit sha. Also `GROK_MARKETPLACE_REQUIRE_SHA`. Neither this key nor the env var can turn the gate back off. |

### `mcp`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `mcp.max_output_bytes` | `number` | `yes` | `user` | Cap MCP tool output size in bytes. Project files may set this. |

### `mcp_servers`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `mcp_servers.<name>.args` | `string[]` | `yes` | `user` | `[mcp_servers.<name>]` `args` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.bearer_token_env_var` | `string` | `yes` | `user` | `[mcp_servers.<name>]` `bearer_token_env_var` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.bearer_token_file` | `string` | `yes` | `user` | `[mcp_servers.<name>]` `bearer_token_file` on an HTTP MCP server: absolute or `~/` path to a bearer token, re-read on every request. |
| `mcp_servers.<name>.command` | `string` | `yes` | `user` | `[mcp_servers.<name>]` `command` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.cwd` | `string` | `yes` | `user` | `[mcp_servers.<name>]` `cwd` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.enabled` | `boolean` | `yes` | `user` | `[mcp_servers.<name>]` `enabled` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.env` | `table` | `yes` | `user` | `[mcp_servers.<name>]` `env` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.expose_image_base64` | `boolean` | `yes` | `user` | `[mcp_servers.<name>]` `expose_image_base64` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.headers` | `table` | `yes` | `user` | `[mcp_servers.<name>]` `headers` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.oauth` | `table` | `yes` | `user` | `[mcp_servers.<name>]` `oauth` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.oauth_client_id` | `string` | `yes` | `user` | `[mcp_servers.<name>]` `oauth_client_id` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.oauth_client_secret_env_var` | `string` | `yes` | `user` | `[mcp_servers.<name>]` `oauth_client_secret_env_var` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.oauth_scopes` | `string[]` | `yes` | `user` | `[mcp_servers.<name>]` `oauth_scopes` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.setup` | `table` | `yes` | `user` | `[mcp_servers.<name>]` `setup` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.startup_timeout_sec` | `number` | `yes` | `user` | `[mcp_servers.<name>]` `startup_timeout_sec` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.tool_timeout_sec` | `number` | `yes` | `user` | `[mcp_servers.<name>]` `tool_timeout_sec` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.tool_timeouts` | `table` | `yes` | `user` | `[mcp_servers.<name>]` `tool_timeouts` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.type` | `string` | `yes` | `user` | `[mcp_servers.<name>]` `type` on a stdio or HTTP MCP server. |
| `mcp_servers.<name>.url` | `string` | `yes` | `user` | `[mcp_servers.<name>]` `url` on a stdio or HTTP MCP server. |

### `memory`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `memory.enabled` | `boolean` | `pin` | `user` | Legacy memory switch. Also `GROK_MEMORY`; superseded when the v2 gate is enabled. |
| `memory_v2.enabled` | `boolean` | `pin` | `user` | Primary memory-v2 switch. When true, v2 takes precedence over legacy `memory.enabled`. When false or absent, legacy enablement is resolved normally. Default: `false`. |
| `memory_v2.rollout` | `"off"`, `"record_only"`, `"shadow"`, `"active"` | — | `user` | Advanced staged-rollout control for new v2 sessions. Default: `"active"` after enabling v2. Most users should leave this unset. |
| `memory_v2.capture_status_enabled` | `boolean` | — | `user` | Shows memory-v2 capture lifecycle messages in the UI for debugging. Successful captures are expandable and include generated content plus links to committed observation files. Debug logs are always recorded. Default: `false`. |
| `memory_v2.capture_enabled` | `boolean` | — | `user` | Enables memory-v2 extraction and observation capture. Default: `true`. |
| `memory_v2.automatic_dream_enabled` | `boolean` | — | `user` | Enables event-driven memory-v2 Dream. Default: `true`. |
| `memory_v2.manual_dream_enabled` | `boolean` | — | `user` | Enables explicitly requested memory-v2 Dream. Default: `true`. |
| `memory_v2.batch_dream_enabled` | `boolean` | — | `user` | Runs active memory-v2 Dream as batch Dream, which folds notes into topics in batches with the full topic catalog. Default: `false`. |
| `memory_v2.batch_dream_max_run_secs` | `number` | — | `user` | Caps one batch Dream run in seconds, default `1800`, clamped to `60`–`3600`; unfinished notes stay in the inbox. |
| `memory_v2.batch_dream_max_calls_per_batch` | `number` | — | `user` | Caps model calls per batch Dream batch, default `6`, clamped to `2`–`16`. |
| `memory_v2.batch_dream_max_batch_note_bytes` | `number` | — | `user` | Caps note bytes in one batch Dream batch, default `98304`, clamped to `16384`–`262144`. |
| `memory_v2.compact_index_enabled` | `boolean` | — | `user` | Injects a titles-only memory index into the system prompt (no topic descriptions, no pending observations) so more topics fit the 8 KiB budget; titled entries are ordered by how often the agent has read each topic, and the on-disk `MEMORY.md` is rendered the same way. Default: `false`. |
| `memory_v2.file_writes_enabled` | `boolean` | — | `user` | Enables all memory-v2 file mutation; `false` fails closed before scaffold creation. Default: `true`. |
| `memory_v2.archived_retention_days` | `number` | — | `user` | Retains archived memory-v2 observation files for this many days. Default: `30`. |
| `memory_v2.job_retention_days` | `number` | — | `user` | Retains terminal memory-v2 capture-job metadata for this many days. Default: `14`. |

### `model`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `model.<id>` | `table` | `yes` | `user` | Per-model override or BYOK definition. Prefer `env_key` over inline `api_key`. |
| `model.<id>.agent_type` | `string` | `yes` | `user` | Agent definition type associated with this model. |
| `model.<id>.api_backend` | `chat_completions / responses / messages` | `yes` | `user` | Wire protocol for this model. |
| `model.<id>.api_base_url` | `string` | `yes` | `user` | Alternate API base URL. |
| `model.<id>.api_key` | `string` | `yes` | `user` | Inline API key. Prefer `env_key`. Not a secret to put in a shared repo. |
| `model.<id>.auth_provider` | `string` | `yes` | `user` | Name of a `[auth_provider.<name>]` helper that mints this model's bearer token. |
| `model.<id>.auto_compact_at_tokens` | `integer` | `yes` | `user` | Absolute token count that triggers auto-compaction for this model; takes precedence over percentages. Models saved by `kite login` default to 220000. |
| `model.<id>.auto_compact_threshold_percent` | `integer` | `yes` | `user` | Per-model auto-compact threshold (0-100). |
| `model.<id>.base_url` | `string` | `yes` | `user` | Provider endpoint base URL. |
| `model.<id>.compaction_at_tokens` | `number / table` | `yes` | `user` | Token threshold that triggers compaction for this model. |
| `model.<id>.compactions_remaining` | `string / table` | `yes` | `user` | How compaction leftover context is sent. Alias `send_compactions_remaining`. |
| `model.<id>.context_window` | `number` | `yes` | `user` | Context window tokens; drives auto-compact timing. |
| `model.<id>.description` | `string` | `yes` | `user` | Optional description shown in the picker. |
| `model.<id>.env_http_headers` | `map<string,string>` | `yes` | `user` | HTTP headers populated from environment variables when set. |
| `model.<id>.env_key` | `string / string[]` | `yes` | `user` | Environment variable name(s) holding the provider API key. |
| `model.<id>.extra_headers` | `map<string,string>` | `yes` | `user` | Per-request headers for this model. |
| `model.<id>.hidden` | `boolean` | `yes` | `user` | Hide this model from the picker. Still usable via `-m`. |
| `model.<id>.inference_idle_timeout_secs` | `number` | `yes` | `user` | Idle timeout for streaming inference on this model. |
| `model.<id>.max_completion_tokens` | `number` | `yes` | `user` | Per-model max completion tokens. |
| `model.<id>.max_request_bytes` | `number` | `yes` | `user` | Provider request-body cap that inline images are evicted to stay under. Unset inherits the `[model_providers.<id>]` value, then the `api_backend` default: 30 MB for `messages`, 50 MiB otherwise. |
| `model.<id>.max_retries` | `number` | `yes` | `user` | Inference retries for this model. |
| `model.<id>.model` | `string` | `yes` | `user` | Model id sent to the API. |
| `model.<id>.model_family` | `string` | `yes` | `user` | Family id used for compaction and capability grouping. |
| `model.<id>.model_provider` | `string` | `yes` | `user` | Named `[model_providers.<name>]` provider id for this model. |
| `model.<id>.mtls_cert_dir` | `string` | `yes` | `user` | Directory containing the model endpoint's mTLS identity as `client.crt` and `client.key`, or `tls.crt` and `tls.key`; configuration is rejected unless the same model has one HTTPS `base_url` and no `api_base_url`, and requests do not follow redirects. |
| `model.<id>.name` | `string` | `yes` | `user` | Label shown in the model picker. |
| `model.<id>.notice` | `table` (`severity` = `info / warning / critical`, `text`, `label`) | `yes` | `user` | Message shown above the prompt while this model is selected, cleared for this model by a blank `text`. |
| `model.<id>.query_params` | `map<string,string>` | `yes` | `user` | Extra query parameters on this model's requests. |
| `model.<id>.rate_limit_retry_threshold` | `number` | `yes` | `user` | Total-attempt ceiling for rate-limited requests, capped by the resolved `max_retries`; when configured, it disables the separate subagent 429 wait loop. |
| `model.<id>.reasoning_effort` | `string` | `yes` | `user` | Deprecated per-model effort; prefer `reasoning_efforts`. |
| `model.<id>.reasoning_efforts` | `array of tables` | `yes` | `user` | Allowed reasoning-effort values for this model. When omitted, the menu comes from the endpoint's `/v1/models` row (`reasoning_efforts`, or `capabilities.reasoning_effort` when that is absent). |
| `model.<id>.reasoning_summary` | `none / auto / concise / detailed` | `yes` | `user` | Responses API `reasoning.summary` for this model; default `concise`. `none` omits the field for endpoints that reject it (e.g. AWS Bedrock Mantle). |
| `model.<id>.show_model_fingerprint` | `boolean` | `yes` | `user` | Show the provider model fingerprint in the UI when present. |
| `model.<id>.stream_tool_calls` | `boolean` | `yes` | `user` | Per-model tool-call streaming request shape. |
| `model.<id>.subagent_rate_limit_max_attempts` | `number` | `yes` | `user` | Maximum subagent 429 wait-loop attempts when `rate_limit_retry_threshold` is unset; default 8, maximum 32, and `0` disables the wait loop. |
| `model.<id>.supported_in_api` | `boolean` | `yes` | `user` | Whether this catalog entry is offered as a public API model. |
| `model.<id>.supports_reasoning_effort` | `boolean` | `yes` | `user` | Deprecated; prefer `reasoning_efforts`. An explicit `false` keeps the model out of any menu it would otherwise inherit from the endpoint or from a same-model catalog entry. |
| `model.<id>.system_prompt_label` | `string` | `yes` | `user` | Per-model system-prompt identity label. |
| `model.<id>.temperature` | `number` | `yes` | `user` | Per-model sampling temperature. |
| `model.<id>.top_p` | `number` | `yes` | `user` | Per-model top_p. |
| `model.<id>.use_concise` | `boolean` | `yes` | `user` | Use the concise tool-description pack for this model. |

### `model_providers`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `model_providers.<name>` | `table` | `yes` | `user` | Named custom model provider definition. |

### `models`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `models.agent_type` | `string` | `yes` | `user` | Fallback agent_type for models without a per-model override. |
| `models.allowed_models` | `string[]` | `pin` | `user` | Glob allowlist for the model picker, default, and `-m`, ignored outside `requirements.toml` when `auth_provider_command` and a custom models endpoint are set. Empty means no restriction. |
| `models.default` | `string` | `pin` | `user` | Model used for new sessions. Also `GROK_DEFAULT_MODEL`, `--model`, `-m`. |
| `models.default_reasoning_effort` | `string` | `yes` | `user` | Default reasoning effort for the default model when the model supports it. |
| `models.disabled_models` | `string[]` | `yes` | `user` | Remove these model IDs from the catalog. Wins over `hidden_models`. |
| `models.extra_headers` | `map<string,string>` | `yes` | `user` | Request headers applied to every model; per-model keys win. |
| `models.hidden_models` | `string[]` | `yes` | `user` | Hide these model IDs from the picker; `-m` can still select them. |
| `models.image_description` | `string` | `yes` | `user` | Vision model used to transcribe user-supplied images. |
| `models.inference_idle_timeout_secs` | `number` | `yes` | `user` | Global idle timeout for streaming inference when a model leaves it unset. |
| `models.max_completion_tokens` | `number` | `yes` | `user` | Global max completion tokens default when a model leaves it unset. |
| `models.max_retries` | `number` | `yes` | `user` | Global inference retry default when a model leaves it unset. |
| `models.prompt_suggestion` | `string` | `yes` | `user` | Model pin for next-prompt ghost text. Unset uses the session model. |
| `models.rate_limit_retry_threshold` | `number` | `yes` | `user` | Global total-attempt ceiling for rate-limited requests when a model leaves it unset, capped by the resolved `max_retries`; when configured, it disables the separate subagent 429 wait loop. |
| `models.session_summary` | `string` | `yes` | `user` | Model used for session titles and summaries. |
| `models.stream_tool_calls` | `boolean` | `yes` | `user` | Global tool-call streaming request shape; some BYOK endpoints need false. |
| `models.subagent_rate_limit_max_attempts` | `number` | `yes` | `user` | Global default for subagent 429 wait-loop attempts when `rate_limit_retry_threshold` is unset; default 8, maximum 32, and `0` disables the wait loop. |
| `models.temperature` | `number` | `yes` | `user` | Global sampling temperature default when a model leaves it unset. |
| `models.top_p` | `number` | `yes` | `user` | Global top_p default when a model leaves it unset. |

### `path_not_found_hints`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `path_not_found_hints` | `boolean` | `yes` | `user` | Enrich path-not-found errors with CWD reminders and similar-name suggestions. |

### `paths`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `paths.extra_rule_dirs` | `string[]` | `yes` | `user` | More rule directories (absolute or `~/…`; each contains `*.md`), loaded after the home rules. |
| `paths.extra_skill_dirs` | `string[]` | `yes` | `user` | Records `/import-claude` skill directories that skill injection ignores in favor of `[skills] paths`. |

### `permission`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `permission.allow` | `string[]` | `yes` | `user` | Compact allow rules such as `Bash(git *)`. Deny beats ask beats allow. Project files may set this. |
| `permission.ask` | `string[]` | `yes` | `user` | Compact ask rules. Project files may set this. |
| `permission.deny` | `string[]` | `yes` | `user` | Compact deny rules. Project files may set this. |
| `permission.rules` | `array of tables` | `yes` | `user` | Verbose action/tool/pattern object rules. Project files may set this. |

### `plugins`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `plugins.disabled` | `string[]` | `yes` | `user` | Plugin IDs to discover but not load. Project files may set this. |
| `plugins.enabled` | `string[]` | `yes` | `user` | Plugin IDs to enable; needed for project plugins that default off. |
| `plugins.paths` | `string[]` | `yes` | `user` | Additional plugin directories. Project files may set this when the folder is trusted. |

### `sandbox`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `sandbox.auto_allow_bash` | `boolean` | `pin` | `user` | Skip bash permission prompts when a sandbox profile is active. Also GROK_SANDBOX_AUTO_ALLOW_BASH. |
| `sandbox.profile` | `off / workspace / read-only / strict / string` | `pin` | `user` | Filesystem sandbox profile. Also `--sandbox` and GROK_SANDBOX. |

### `session`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `session.auto_compact_threshold_percent` | `integer` | `yes` | `user` | Auto-compact when context usage reaches this percent (0–100). |
| `session.load_envrc` | `boolean` | `yes` | `user` | Inject `.envrc` variables into bash. |

### `shell_environment_policy`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `shell_environment_policy.exclude` | `string[]` | `yes` | `user` | Env names to drop from bash. Overlay-allowlisted. |
| `shell_environment_policy.ignore_default_excludes` | `boolean` | `yes` | `user` | Skip the built-in env denylist. Overlay-allowlisted. |
| `shell_environment_policy.include_only` | `string[]` | `yes` | `user` | If set, bash inherits only these env names. Overlay-allowlisted. |
| `shell_environment_policy.inherit` | `string` | `yes` | `user` | Which parent env names bash inherits. Overlay-allowlisted; cannot inject values. |
| `shell_environment_policy.set` | `map<string,string>` | `yes` | `user` | Inject env values into bash. Not overlay-allowlisted. |

### `skills`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `skills.disabled` | `string[]` | `yes` | `user` | Skill names to discover but not activate. |
| `skills.paths` | `string[]` | `yes` | `user` | Additional skill directories. |

### `storage`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `storage.cleanup_ttl_days` | `integer` | `yes` | `user` | Days a session may stay idle before its folder is deleted; media and terminal logs older than this are pruned from live sessions; unset or `0` disables cleanup. |

### `subagents`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `subagents.enabled` | `boolean` | `pin` | `user` | Subagent / task tool master switch; off by default in Kite. Also GROK_SUBAGENTS or `--no-subagents`. |
| `subagents.limit_behavior` | `queue / fail` | `yes` | `user` | What to do when the concurrent subagent cap is hit. |
| `subagents.max_concurrent` | `integer` | `yes` | `user` | Max concurrent subagents. |
| `subagents.max_depth` | `integer` | `yes` | `user` | Max nested subagent depth (clamped ≥1). |
| `subagents.models.<name>` | `string` | `yes` | `user` | Per-subagent model id override. |
| `subagents.toggle.<name>` | `boolean` | `yes` | `user` | Enable or disable an individual subagent type. Omitted agents default on. |

### `tools`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `tools.respect_gitignore` | `boolean` | `pin` | `user` | When true, search and read tools skip gitignored files. Also GROK_RESPECT_GITIGNORE. |

### `toolset`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `toolset.ask_user_question.timeout_secs` | `number` | `yes` | `user` | Timeout for the ask_user_question tool. |
| `toolset.bash.auto_background_on_timeout` | `boolean` | `yes` | `user` | Background the command when the foreground timeout fires. |
| `toolset.bash.login_shell_capture` | `boolean` | `yes` | `user` | Capture the user's login shell environment for bash. Overlay-allowlisted. |
| `toolset.bash.max_timeout_secs` | `number` | `yes` | `user` | Cap on model-requested foreground timeouts. |
| `toolset.bash.output_byte_limit` | `number` | `yes` | `user` | Max captured bash output in bytes. |
| `toolset.bash.timeout_secs` | `number` | `yes` | `user` | Foreground bash command timeout in seconds. |
| `toolset.file_toolset` | `standard / hashline` | `yes` | `user` | File edit tool scheme. |
| `toolset.web_fetch.allowed_domains` | `string[]` | `yes` | `user` | Domain allowlist override for web_fetch. |
| `toolset.web_fetch.proxy_endpoint` | `string` | `yes` | `user` | Egress proxy URL for web_fetch. Also GROK_WEB_FETCH_PROXY. |

### `ui`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `ui.approval_mode` | `string` | `yes` | `user` | Deprecated; use `ui.permission_mode`. |
| `ui.auto_dark_theme` | `string` | `yes` | `user` | Theme when `theme = auto` and the OS is dark. |
| `ui.auto_light_theme` | `string` | `yes` | `user` | Theme when `theme = auto` and the OS is light. |
| `ui.cancel_subagents_on_turn_cancel` | `ask / always_stop / always_continue` | `yes` | `user` | What to do with running subagents when cancelling a parent turn. |
| `ui.collapsed_edit_blocks` | `boolean` | `yes` | `user` | Show edits as one-line +N/-M summaries. Also GROK_COLLAPSED_EDIT_BLOCKS. |
| `ui.combine_queued_prompts` | `boolean` | `yes` | `user` | Merge consecutive plain follow-ups into one turn. |
| `ui.compact_mode` | `boolean` | `yes` | `user` | Denser message padding. Also `/compact-mode`. |
| `ui.confirm_before_rewind` | `boolean` | `yes` | `user` | Ask before rewinding conversation history. |
| `ui.dashboard_preview` | `boolean` | `yes` | `user` | The dashboard preview and reply panel appear by default (Appearance in `/settings`). |
| `ui.contextual_hints.image_input` | `boolean` | `yes` | `user` | Clipboard image paste tip when the model accepts images. |
| `ui.contextual_hints.plan_mode` | `boolean` | `yes` | `user` | Suggest plan mode (Shift+Tab) for planning-style prompts. |
| `ui.contextual_hints.send_now` | `boolean` | `yes` | `user` | After queuing a mid-turn follow-up, Enter on an empty prompt sends now. |
| `ui.contextual_hints.small_screen` | `boolean` | `yes` | `user` | Suggest `/compact-mode` on short terminals. |
| `ui.contextual_hints.ssh_wrap` | `boolean` | `yes` | `user` | Recommend `kite wrap` when SSH lacks a clipboard sink. |
| `ui.contextual_hints.undo` | `boolean` | `yes` | `user` | Ctrl+Z restores a wiped prompt draft tip. |
| `ui.contextual_hints.word_select` | `boolean` | `yes` | `user` | After double-click with fold/nav selection, point at Word select in settings. |
| `ui.cursor_blink` | `boolean` | `yes` | `user` | Force blinking (true) or steady (false) block cursor. Unset inherits the terminal. |
| `ui.default_selected_permission` | `string` | `yes` | `user` | Preselected approval row on the first prompt of a session. Also GROK_DEFAULT_SELECTED_PERMISSION. |
| `ui.display_refresh.auto_cadence_enabled` | `boolean` | `yes` | `user` | Match stream/scroll cadence to display refresh rate. Also GROK_DISPLAY_REFRESH_AUTO_CADENCE. |
| `ui.follow_up_behavior` | `queue / steer` | `yes` | `user` | Mid-turn follow-up routing. |
| `ui.fork_secondary_model` | `string` | `yes` | `user` | Model for the secondary agent when forking. Defaults to the main default model. |
| `ui.group_tool_verbs` | `boolean` | `yes` | `user` | Fold consecutive read/search/list tool rows. Also GROK_GROUP_TOOL_VERBS. |
| `ui.hunk_tracker_mode` | `agent_only / all_dirty / off` | `yes` | `user` | File-change hunk tracking. Also GROK_HUNK_TRACKER and `--hunk-tracker-mode`. |
| `ui.invert_scroll` | `boolean` | `yes` | `user` | Reverse vertical scroll direction. Also GROK_INVERT_SCROLL. |
| `ui.keep_text_selection` | `flash / hold / word_select` | `yes` | `user` | In-app selection: brief flash, hold, or double-click word select. |
| `ui.max_thoughts_width` | `number` | `yes` | `user` | Column width for the thoughts panel (40–500). |
| `ui.mouse_reporting_toggle` | `boolean` | `yes` | `user` | Ctrl+R in scrollback toggles terminal mouse capture. Also GROK_MOUSE_REPORTING_TOGGLE. |
| `ui.page_flip_on_send` | `boolean` | `yes` | `user` | Snap the sent prompt to the top of the viewport. |
| `ui.permission_mode` | `default / ask / auto / always-approve` | `yes` | `user` | Default tool-permission behavior. Enterprise locks use requirements.toml. |
| `ui.prompt_suggestions` | `boolean` | `yes` | `user` | Next-prompt ghost text after each turn. Off by default in Kite. Also GROK_PROMPT_SUGGESTIONS. |
| `prompt_suggestions.max_output_tokens` | `number` | `yes` | `user` | Visible-output tokens for the suggestion call; clamped to 16–256, default 64, with a separate reserve for reasoning. |
| `prompt_suggestions.temperature` | `number` | `yes` | `user` | Sampling temperature for the suggestion call (default 0.2). |
| `prompt_suggestions.reasoning_effort` | `none / minimal / low / medium / high` | `yes` | `user` | Reasoning effort for the suggestion call; default and `none` disable reasoning, while other values use a supported model effort. |
| `ui.remember_tool_approvals` | `boolean` | `yes` | `user` | Show per-tool Always allow options. Also GROK_REMEMBER_TOOL_APPROVALS. |
| `ui.render_mermaid` | `auto / on / off` | `yes` | `user` | How mermaid fences render: clickable open row or raw source. |
| `ui.screen_mode` | `fullscreen / minimal` | `yes` | `user` | Default render mode for plain `kite`. Restart required. |
| `ui.scroll_lines` | `integer` | `yes` | `user` | Lines per scroll tick (1–10). Also GROK_SCROLL_LINES. |
| `ui.scroll_mode` | `auto / wheel / trackpad` | `yes` | `user` | Scroll input classification. Also GROK_SCROLL_MODE. |
| `ui.scroll_speed` | `integer` | `yes` | `user` | Mouse/trackpad scroll speed multiplier (1–100). Also GROK_SCROLL_SPEED. |
| `ui.show_thinking_blocks` | `boolean` | `yes` | `user` | Show thinking/reasoning blocks while streaming. Also GROK_SHOW_THINKING_BLOCKS. |
| `ui.show_timeline` | `boolean` | `yes` | `user` | Per-turn tick rail instead of the scrollbar. |
| `ui.show_timestamps` | `boolean` | `yes` | `user` | Clock time next to messages. Also `/timestamps`. |
| `ui.simple_mode` | `boolean` | `yes` | `user` | Readline prompt editing when true; experimental vim prompt keys when false. |
| `ui.status_line.command` | `string` | `yes` | `user` | Script for a `command` status line. A requirements layer still merges it. |
| `ui.status_line.type` | `disabled / command` | `yes` | `user` | Optional status-line row above the shortcuts bar. Off by default. See the status-line user guide. |
| `ui.theme` | `string` | `yes` | `user` | Color theme name, or `auto`/`system` to follow the OS. Also `/theme` and GROK_THEME. |
| `ui.ui_theme` | `string` | `yes` | `user` | Legacy alias for `ui.theme`. |
| `ui.vim_mode` | `boolean` | `yes` | `user` | Vim keys in the scrollback, not the prompt. Also `/vim-mode`. |
| `ui.yolo` | `boolean` | `pin` | `user` | Always-approve tool calls. Requirements can pin false and block `--yolo`. |

### `version_overrides`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `version_overrides` | `array of tables` | `yes` | `user` | Per-CLI-version config patches applied before merge. See `[[version_overrides]]`. |

### `workflows`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `workflows.enabled` | `boolean` | `yes` | `user` | Enable workflows. |

### `worktree`

| Key | Type / Values | Requirements | Managed | Details |
| --- | --- | --- | --- | --- |
| `worktree.auto_gc` | `table` | `yes` | `user` | Automatic worktree garbage collection policy. |

## managed_config.toml

`managed_config.toml` accepts every key in the tables above. It sets fleet defaults, so a developer's own `config.toml` overrides it. Use it for values you want people to be able to adjust, and `requirements.toml` for values they cannot.

Kite reads `/etc/grok/managed_config.toml` first, then `$KITE_HOME/managed_config.toml`. Values in the second replace values in the first.

The **Managed** column on the tables above is the per-key answer: `fleet` means the fleet value stands, `user` means the user's file wins, `—` means this file is ignored.

## requirements.toml

`requirements.toml` is an admin-enforced file. Locations: `$KITE_HOME/requirements.toml` then `/etc/grok/requirements.toml`, then macOS MDM `ai.x.grok`. The **Requirements** column on the `config.toml` tables lists every `config.toml` key this file accepts (`pin` or `yes`). Omitted keys stay unconstrained.

These keys exist only in `requirements.toml`:

| Key | Type / Values | Default | Details |
| --- | --- | --- | --- |
| `fail_closed` | `boolean` | `false` | Refuse to start when signed requirements or version_overrides cannot be applied; default false. |
| `ui.disable_bypass_permissions_mode` | `boolean` | — | Lock always-approve off. The lock is enforced only from a requirements layer; true in user or managed files is ignored. |

Policy pins such as `allow_managed_hooks_only` (see [Hooks](10-hooks.md#allow-only-managed-hooks)) and the MCP and marketplace lists (see [Plugins](09-plugins.md#restrict-which-mcp-servers-can-run)) are accepted in `requirements.toml` and `managed_config.toml` alike and only ever tighten.

`[[hooks.<Event>]]` tables are accepted in every config file. Hooks from `requirements.toml` and the root-owned `/etc/grok` files are enforced; see [Hooks](10-hooks.md#enforced-hooks).

## What happens when a setting is refused

| Situation | What Kite does |
| --- | --- |
| A developer sets a key you pinned | The pinned value applies. `kite inspect` lists the requirements file that contributed. |
| A developer sets a key you shipped in `managed_config.toml` | Their value applies. Pin the key instead if it must hold. |
| `requirements.toml` is missing or its signature does not verify | The pins do not apply, and Kite starts without them. Set `fail_closed = true` to refuse to start instead. |
| A pinned key names a value this version does not recognise | The key is ignored and the rest of the file still applies. |

## Check what is in effect

Run `kite inspect` on the developer's machine. It lists every config file that contributed, including requirements and managed layers, so a policy that is not applying is visible in one command.
