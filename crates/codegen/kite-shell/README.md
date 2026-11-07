# Kite

Kite is a terminal coding agent for local and self-hosted models. Use it
interactively as a TUI, from scripts in headless mode, or from editors and other
apps through the Agent Client Protocol (ACP).

The full user guide is installed alongside this file in
`~/.kite/docs/user-guide/` (or `$KITE_HOME/docs/user-guide/` when `KITE_HOME`
is set). Inside Kite, `/docs` opens it, and you can ask Kite questions about it.

## Quick start

```bash
# Connect an OpenAI-compatible model server, then open Kite
kite login http://localhost:8080/v1

# Interactive TUI
kite

# Headless (scripts and automation)
kite -p "Explain this codebase"

# Agent mode (IDE/app integration over ACP)
kite agent stdio
```

Inside Kite, `/login <base-url>` connects or reconnects a model server and
`/model` switches between the models it reports.

## Where things live

| Path | Contents |
| --- | --- |
| `~/.kite/config.toml` | User configuration |
| `~/.kite/sessions/` | Saved sessions |
| `~/.kite/skills/<name>/SKILL.md` | User skills |
| `~/.kite/docs/user-guide/` | User guide |
| `.grok/` in a project | Project configuration, skills, agents, hooks, and plugins |
| `AGENTS.md` in a project | Project rules added to the system prompt |

Environment variables that configure Kite still use the `GROK_` prefix, except
`KITE_HOME`.

## Useful commands

```bash
kite --help              # all options and subcommands
kite doctor              # check terminal, clipboard, color, and input support
kite inspect             # show the configuration Kite discovers here
kite sessions search --all "<keywords>"   # search past sessions
kite export <session-id> # export one session as Markdown
kite mcp list            # list configured MCP servers
kite plugin list         # list installed plugins
```

## Clipboard passthrough (`kite wrap`)

`kite wrap` runs any command inside a local pseudo-terminal that forwards its
OSC 52 clipboard sequences to your local clipboard. Use it for remote shells and
containers when your terminal does not handle OSC 52 itself (for example Apple
Terminal):

```bash
kite wrap ssh user@host
kite wrap docker exec -it my-container bash
kite wrap kubectl exec -it my-pod -- bash
```

This runs entirely locally.
