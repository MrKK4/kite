# Coming from Claude, Cursor, or Codex?

Your rules, MCP servers, and hooks come with you. Kite reads the same
project conventions other agents use, and can import the rest.

## Picked up automatically

- **Rules & instructions** — `AGENTS.md` (the Codex/OpenCode convention),
  `CLAUDE.md` (including nested ones), and `*.md` rules under
  `.claude/rules/` and `.cursor/rules/`.
- **Skills** — not by default. Kite loads skills from
  `~/.kite/skills/<name>/SKILL.md` (and project `.grok/skills/`). Skill
  folders from other tools (`~/.claude`, `~/.cursor`, `~/.agents`, Claude
  Code plugin skills) are off to keep requests small; turn them back on with
  `[compat.claude] skills = true` / `[compat.cursor] skills = true`, or list
  folders in `[skills] paths`.
- **MCP servers** — from `~/.claude.json`, `.cursor/mcp.json`, and project
  `.mcp.json`.
- **Hooks** — from `.claude/settings.json`, including matcher aliases like
  `Bash`, so most hooks run unchanged.

## One-step import

**`/import-claude`** scans your `~/.claude` settings — permissions, env
vars, MCP servers, hooks — and shows a checkbox preview; confirming
writes the items you selected into your Kite `config.toml`. Re-run it anytime.

## Pick up where you left off

The **`/resume-claude`**, **`/resume-codex`**, and **`/resume-cursor`**
skills continue a recent session from those tools right here.

## Check what was discovered

Run **`kite inspect`** in a repo to see every rules file, skill, and MCP
server Kite picked up, tagged with where it came from. Each compat source
can be toggled in `[compat.claude]` / `[compat.cursor]` config sections.

And a few things you might have missed elsewhere: `/btw` asks a side
question without interrupting the current task, and `/rewind` rewinds the
conversation to an earlier turn (file changes stay as they are).

*Go deeper: `/docs Project Rules (AGENTS.md)`, `/docs Skills`, or `/docs MCP Servers`*
