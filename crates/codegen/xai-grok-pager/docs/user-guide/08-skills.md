# Skills

Skills are reusable prompt packages that extend Kite with task-specific instructions. They let you capture a repeatable procedure once, instead of re-explaining it each session. Startup discovery skips project skills and commands in untrusted folders.

---

## What Are Skills?

A skill is a directory that contains a `SKILL.md` file. Its markdown body tells Kite how to handle a specific type of task: step-by-step instructions, conventions, and tool-usage patterns.

Use a skill for a repeatable procedure that's too specific for AGENTS.md but too long to retype. Kite activates a skill only when it applies to your current task.

---

## Skill Locations

By default Kite loads your personal skills only from `~/.kite/skills/<name>/SKILL.md`, plus project skills from `.grok/skills/` in the current directory and repository, and any extra directories listed in `[skills] paths`. Other tools' skill folders (`~/.claude`, `~/.cursor`, `~/.agents`, and Claude Code plugin skills) are **off by default** because listing them added roughly 8k tokens to every request.

Kite discovers skills from these directories, in priority order:

| Location | Scope | Priority | Default |
|----------|-------|----------|---------|
| `./.grok/skills/`, `./.grok/commands/` | Local (CWD) | Highest | On |
| `<repo_root>/.grok/skills/`, `…/commands/` | Repo | Medium | On |
| `~/.kite/skills/`, `~/.kite/commands/` | User | Lowest | On |
| `[skills] paths` entries | Config | Lowest | On (when listed) |
| `./.claude/skills/`, `./.claude/commands/` | Local / Repo | High | Off; on with `[compat.claude] skills = true` |
| `~/.claude/skills/`, `~/.claude/commands/`, Claude Code plugin skills | User | Lowest | Off; on with `[compat.claude] skills = true` |
| `./.cursor/skills/` | Local / Repo | High | Off; on with `[compat.cursor] skills = true` |
| `~/.cursor/skills/` | User | Lowest | Off; on with `[compat.cursor] skills = true` |
| `.agents/skills/` (project and `~/.agents`) | Local / Repo / User | Same tier as `.grok/` | Off; on when Claude or Cursor skills are enabled |

To turn the other tools' folders back on, or add one folder explicitly:

```toml
[compat.claude]
skills = true          # ~/.claude skills, Claude plugin skills, ~/.agents

[skills]
paths = ["~/.agents"]  # or add any folder explicitly
```

Kite deduplicates skills by name -- a higher-priority location overrides a lower one. Kite walks every directory between your working directory and the repo root.

Flat `*.md` files under a `commands/` directory become user-invocable slash commands (filename stem = command name), matching Claude Code's legacy custom-command layout.

Skill and command discovery does **not** use `.gitignore`. Paths under enabled skill roots (`.grok/`, and `.agents/`, `.claude/`, `.cursor/` when enabled) always load when present on disk — teams often ignore `.claude/**` as local-only config while still expecting `/frontend`-style project commands to work. To hide a skill, use `[skills] ignore` in config (not repo ignore rules).

You can also set the `GROK_CURSOR_SKILLS_ENABLED` or `GROK_CLAUDE_SKILLS_ENABLED` environment variable instead of the config cell. See [Configuration](05-configuration.md#harness-compatibility) for details. Kite always filters out known vendor-shipped default skills (such as Cursor's `shell`, `canvas`, and `statusline`), regardless of these settings.

### Additional Skill Directories

Add directories, exclude paths, or disable individual skills via `[skills]` in `~/.kite/config.toml`:

```toml
[skills]
paths = ["~/my-team-skills"]          # Additional directories to scan
ignore = ["~/my-team-skills/wip"]     # Paths to exclude (hidden entirely)
disabled = ["wip-skill"]              # Skill names to keep listed but inactive
```

Each entry in `paths` is a `SKILL.md` file or a directory that Kite walks recursively. `ignore` hides a skill completely; `disabled` keeps it in the list but excludes it from the system prompt and from invocation. `paths` and `ignore` take filesystem paths and support `~` expansion; `disabled` takes skill names.

`[paths] extra_skill_dirs` is written by `/import-claude`. It does not inject skills. Put extra directories in `[skills] paths`.

---

## Creating a Skill

### Directory Structure

Each skill lives in its own directory with a `SKILL.md` file:

```
~/.kite/skills/
  commit/
    SKILL.md
  review-pr/
    SKILL.md
  deploy/
    SKILL.md
```

### SKILL.md Format

A skill file has YAML frontmatter followed by markdown instructions:

```markdown
---
name: commit
description: Create well-formatted git commits following conventional commit standards. Use when the user wants to commit changes or asks for /commit.
---

# Git Commit Skill

Review staged changes and create a commit with a clear, conventional message.

## Steps

1. Run `git diff --staged` to see changes
2. Summarize what changed and why
3. Create commit message following conventional commits format
4. Run `git commit -m "..."` with the message
```

### Core Frontmatter Fields

| Field | Description |
|-------|-------------|
| `name` | Skill identifier. Use lowercase letters, digits, and hyphens, up to 64 characters. Kite normalizes spaces and underscores to hyphens. If you omit `name`, Kite uses the skill's directory name. |
| `description` | What the skill does and when to use it. Kite reads this to decide whether to invoke the skill. If you omit it, Kite uses the first paragraph of the body. |

Write a specific `description`. It determines when Kite invokes the skill automatically. Name the trigger phrases and use cases.

### Optional Frontmatter Fields

Multi-word frontmatter keys use kebab-case (single-word keys like `model` are written as-is).

| Field | Description |
|-------|-------------|
| `when-to-use` | Trigger phrases for automatic invocation, kept separate from `description`. |
| `allowed-tools` | Tools the skill uses, as a YAML list or a comma- or space-separated string. |
| `argument-hint` | Hint text shown in the slash-command autocomplete (for example, `commit message`). |
| `user-invocable` | Whether you can run the skill as a slash command. Defaults to `true`; set `false` to hide it from slash commands. (To stop the model from invoking a skill, set `disable-model-invocation` instead.) |
| `disable-model-invocation` | When `true`, only your slash command runs the skill -- the model cannot invoke it automatically. Defaults to `false`. |
| `model` | Model override for running the skill. |
| `effort` | Reasoning-effort override. |
| `license` | License identifier (for example, `Apache-2.0`). |
| `compatibility` | Environment requirements (for example, `Requires git, docker, jq`). |
| `metadata` | Arbitrary string key-value pairs. Kite promotes `metadata.author` and `metadata.short-description` for display. |

---

## Creating Skills with /create-skill

The `/create-skill` command walks you through building a new skill interactively. Kite asks what you want, drafts the files, and writes them to disk.

### How It Works

When you run `/create-skill`, Kite:

1. **Gathers requirements.** Kite asks for the skill name, the scope to save it under, and a description of the workflow you want to capture. Use a name with lowercase letters, digits, and hyphens (2–64 characters, starting and ending with a letter or digit).

2. **Drafts the description.** Kite writes a `description` that states what the skill does, the phrases that trigger it, and the slash command name. You approve or edit the draft before continuing.

3. **Creates the skill directory.** Kite creates the `<scope>/.grok/skills/<name>/` directory, plus `scripts/` or `references/` subdirectories when the skill needs them.

4. **Writes SKILL.md.** Kite writes the frontmatter (`name` and `description`) and a markdown body of instructions, along with any supporting files.

5. **Verifies and confirms.** Kite reads the file back, confirms it wrote correctly, and tells you how to run the skill.

### Choosing a Scope

Kite asks where to save the skill:

- **Project** (`<repo_root>/.grok/skills/<name>/`) -- available only in this repository and shareable with teammates through version control. Kite recommends this scope inside a git repository.
- **User** (`~/.kite/skills/<name>/`) -- available across all your projects.

To distribute a skill to a whole team or organization, package it in a plugin and publish it through a marketplace. See [Create your own marketplace](09-plugins.md#create-your-own-marketplace) and [Distribute across an organization](09-plugins.md#distribute-across-an-organization).

The new skill appears in the slash menu within a few seconds, because Kite reloads skills when files change on disk.

---

## Using Skills

### Run a Skill by Name

Each skill is a slash command named after the skill. Run one by typing its name:

```
/commit              # Runs the "commit" skill
/review-pr           # Runs the "review-pr" skill
```

Running a skill loads its instructions into the conversation and directs the model to follow them. To pass arguments, type them after the name:

```
/commit fix the build
```

To browse your skills, type `/` to open the slash-command menu. Kite lists every built-in command and skill and filters them as you type. To list skills from the command line instead, run `kite inspect` (see [Viewing Skill Details](#viewing-skill-details)).

### Qualified Names

When a skill's name collides with another skill or a built-in command, Kite keeps **both** invocable. The built-in keeps the bare name (`/login`, `/compact`, …). The skill is advertised under a qualified name prefixed by its scope -- `local:`, `repo:`, `user:`, or the plugin name:

```
/local:commit        # The "commit" skill from ./.grok/skills/
/user:commit         # The "commit" skill from ~/.kite/skills/
/acme:login          # A plugin skill named "login" (built-in /login is unchanged)
```

Typing `/login` in the slash menu shows both rows, with a right-aligned **built-in** or **skill · plugin-name** badge so you can tell them apart. Rename the skill (or its directory) if you want the bare `/name` for the skill instead.

`kite inspect` tags colliding skills with `[collides with /login → /acme:login]`.

### Automatic Invocation

Kite can invoke a skill on its own when it recognizes a relevant task. Kite matches your prompt against the skill's `description` and `when-to-use` fields, so write both to describe the triggering situation.

For example, if a skill's description says "Use when the user wants to commit changes," then saying "commit my changes" can trigger that skill automatically. To require an explicit slash command and prevent automatic invocation, set `disable-model-invocation: true` in the frontmatter.

---

## Viewing Skill Details

Run `kite inspect` to see every skill Kite discovers, along with the rest of your configuration:

```bash
kite inspect          # Human-readable summary
kite inspect --json   # Machine-readable report
```

In the human-readable output, the Skills section lists each skill's name and its source -- `project`, `user`, `bundled`, `config` (a `[skills].paths` entry), or `plugin: <name>`. Kite tags any skill disabled via `[skills].disabled` or from a disabled vendor surface with `[disabled]`.

The report honors your `[skills]` config the same way a live session does: skills from `paths` are listed, skills under an `ignore` prefix are hidden, and skills named in `disabled` stay listed but tagged `[disabled]`.

The `--json` report includes the full detail for each skill: its `name`, `description`, `source` (with the path to the SKILL.md file), and `userInvocable` flag. Skills whose bare slash name is contested — by a built-in command or by another skill — also include `collidesWith` (the contested name) and `invocableAs` (the qualified command to type).

---

## Bundled and Plugin Skills

Kite distributes platform skills separately from your personal skills. Bundled skills are cached under `~/.kite/bundled/skills/`; Kite never writes them into `~/.kite/skills/`. A same-named local, repo, or user skill overrides the bundled copy. `kite inspect` labels each definition by its actual source. (A plugin skill of the same name does not override a native skill; it stays available under its qualified `plugin:name` form.)

Skills can also come from plugins. When you install a plugin that includes skills, they appear alongside your user and project skills. `kite inspect` labels each plugin-provided skill with its source as `plugin: <name>`.

See the [Plugins guide](09-plugins.md) for more on installing plugins that provide skills.

---

## Best Practices

1. **Write specific descriptions.** The description drives automatic invocation. "Create git commits" is too vague; "Create well-formatted git commits following conventional commit standards. Use when the user wants to commit changes or asks for /commit." works better.

2. **Include concrete steps.** Skills work best when they give Kite a clear, ordered procedure to follow.

3. **Reference tools by name.** When a skill relies on specific tools (such as `run_terminal_cmd` or `search_replace`), name them so the model knows what to use.

4. **Keep skills focused.** Write one skill per workflow. A "deploy" skill and a "rollback" skill work better than a single "deploy-and-rollback" skill.

5. **Version-control project skills.** Commit `.grok/skills/` to your repository so the whole team benefits. User skills in `~/.kite/skills/` stay personal and unshared.

6. **Test by running it.** Invoke `/name` and confirm the skill works before you rely on automatic invocation.

7. **Keep the body under the file-read cap.** Kite inlines at most the first 25,000 tokens of a skill body (the same cap as `read_file`). Put long reference material in sibling files and tell Kite to read them with a line offset and limit.
