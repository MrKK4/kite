# Kite's browsers

Kite ships two browser MCP servers. Both set themselves up on first use and keep
everything under `~/.kite`, isolated from any global Playwright or Python
installs.

| Server | Browser | Default | Best for |
|---|---|---|---|
| `playwright` | ungoogled-chromium + uBlock Origin Lite, driven by **Patchright** | On | Everyday browsing, JavaScript sites, logins, screenshots |
| `camoufox` | **Camoufox** (fingerprint-resistant Firefox) | Off | Sites that block automation or show bot checks |

## Using them

Just ask Kite to use the browser ("open example.com and take a screenshot").
The model finds the tools through `search_tool` (`playwright__browser_*`,
`camoufox__browser_*`).

- **Turn Camoufox on/off:** `/mcp` → MCP Servers → select `camoufox` → space.
  Or in `~/.kite/config.toml`:

  ```toml
  [mcp_servers.camoufox]
  enabled = true
  ```

- **First start takes a while:** Chromium downloads about 150 MB; Camoufox
  installs into its own Python environment and downloads about 1.3 GB. Later
  starts are quick. The server shows `initializing` until setup finishes.
- **Requirements:** Node.js (both), Python 3 (Camoufox only). The automatic
  Chromium download is Windows x64; elsewhere `playwright` uses your installed
  Google Chrome.

## Where everything lives

| Path | What |
|---|---|
| `~/.kite/browser/chrome.exe` | ungoogled-chromium binary |
| `~/.kite/browser/mcp-config.json` | Generated launch config (rewritten every start) |
| `~/.kite/extensions/ublock-lite/` | uBlock Origin Lite (unpacked) |
| `~/.kite/browser-profile/` | Chromium profile: cookies, logins, uBlock settings |
| `~/.kite/playwright-mcp.json` | **Your** settings for the `playwright` server (safe to edit) |
| `~/.kite/kite-browser-mcp.mjs` | Chromium launcher (written by Kite on start; don't edit) |
| `~/.kite/camoufox-venv/` | Camoufox's Python environment (Camoufox package, Playwright 1.62) |
| `%LOCALAPPDATA%\camoufox\camoufox\Cache\` (Windows) | Camoufox browser binary, fingerprint data (managed by Camoufox) |
| `~/.kite/camoufox-mcp.py` | Camoufox launcher (written by Kite on start; don't edit) |

## What Kite patches, and how it stays patched

Kite never modifies the browser binaries, so updating them can't remove a
patch. Every patch is reapplied by the launcher each time the server starts:

- **Patchright** (`patchright-mcp`, pinned in the launcher) replaces Playwright's
  driver to hide automation signals, e.g. `navigator.webdriver` is `false`.
- **uBlock Origin Lite at full strength:** the launcher sets the default
  filtering mode to "complete" in the extension's `js/mode-manager.js` on every
  start, so a fresh download is patched automatically.
- **Launch flags** in the generated config: load only uBlock
  (`--load-extension`, `--disable-extensions-except`), keep extensions enabled,
  no background networking or sync, no first-run screens, no "unsupported flag"
  warning bar (`--test-type`), separate profile.
- **Camoufox** starts through its official launcher (`launch_server`), so its
  generated fingerprint (OS, screen, fonts, WebGL...) is applied on every
  launch.

## Updating the browsers

Both update in place and keep their patches and your profile.

**Chromium + uBlock Origin Lite** (downloads the latest releases of both):

```powershell
$env:KITE_BROWSER_UPDATE = "1"; kite     # start once like this, then use Kite normally
```

**Camoufox** (reinstalls the latest Camoufox and its browser):

```powershell
$env:KITE_CAMOUFOX_UPDATE = "1"; kite
```

Clear the variable afterwards (new terminal, or `Remove-Item Env:KITE_BROWSER_UPDATE`)
so later starts don't download again. Alternatively delete `~/.kite/browser/` or
`~/.kite/camoufox-venv/` and start Kite: it sets them up fresh.

Your logins and uBlock settings survive updates (they live in the profile). To
start clean, delete `~/.kite/browser-profile/`.

## Customizing

- **Use your own browser** for `playwright`: set
  `"executablePath"` under `browser.launchOptions` in `~/.kite/playwright-mcp.json`;
  Kite then skips its own Chromium. Other settings in that file (viewport,
  extra args, `userDataDir`) are merged into the generated config.
- **Headless Camoufox:** set `KITE_CAMOUFOX_HEADLESS=1`.
- **Other MCP package versions:** `KITE_BROWSER_MCP_PACKAGE`,
  `KITE_CAMOUFOX_MCP_PACKAGE` (Camoufox's MCP must match the Playwright minor
  version in its venv, pinned with `KITE_CAMOUFOX_PLAYWRIGHT`).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `camoufox` stuck on `initializing` the first time | Setup is downloading; wait a few minutes. |
| Camoufox fails after setup | Start with `KITE_CAMOUFOX_UPDATE=1`. |
| Browser opens but ads show | Wait a few seconds after first start (uBlock loads its rules), or update. |
| "Opening in existing browser session" | Another Kite window is using the profile; close it. |
| A page says "uBO Lite has prevented the following page from loading" | Expected for tracker domains; click Proceed if you need it. |
| Hand-made `[mcp_servers.camoufox]` or `playwright` command in `config.toml` | Remove it; your entry overrides Kite's built-in launcher. |
