// Kite's browser MCP server (written by Kite to ~/.kite/kite-browser-mcp.mjs; edits are overwritten).
// Runs Patchright's Playwright MCP on Kite's own isolated browser: ungoogled-chromium plus
// uBlock Origin Lite at full strength, both under ~/.kite and never shared with global
// Playwright installs. On first use (Windows x64) it downloads the latest releases of both.
// KITE_BROWSER_UPDATE=1 re-downloads the latest. Elsewhere, or if setup fails, it falls back
// to ~/.kite/playwright-mcp.json as written (installed Google Chrome).
import { spawn, execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const MCP_PACKAGE = process.env.KITE_BROWSER_MCP_PACKAGE || "patchright-mcp@0.0.68";
const home = process.env.KITE_HOME || path.join(os.homedir(), ".kite");
const browserDir = path.join(home, "browser");
const extDir = path.join(home, "extensions", "ublock-lite");
const profileDir = path.join(home, "browser-profile");
const userConfigPath = path.join(home, "playwright-mcp.json");
const generatedConfigPath = path.join(browserDir, "mcp-config.json");
const chromeExe = path.join(browserDir, "chrome.exe");
const log = (msg) => process.stderr.write(`kite-browser: ${msg}\n`);

async function latestAsset(repo, pattern) {
  const res = await fetch(`https://api.github.com/repos/${repo}/releases/latest`, {
    headers: { "User-Agent": "kite-browser", Accept: "application/vnd.github+json" },
  });
  if (!res.ok) throw new Error(`${repo}: GitHub API ${res.status}`);
  const release = await res.json();
  const asset = release.assets.find((a) => pattern.test(a.name));
  if (!asset) throw new Error(`${repo}: no asset matching ${pattern}`);
  return { tag: release.tag_name, url: asset.browser_download_url, name: asset.name };
}

async function downloadAndExtract(asset, dest) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "kite-browser-"));
  try {
    const zip = path.join(tmp, asset.name);
    const res = await fetch(asset.url, { headers: { "User-Agent": "kite-browser" } });
    if (!res.ok) throw new Error(`download ${asset.name}: ${res.status}`);
    fs.writeFileSync(zip, Buffer.from(await res.arrayBuffer()));
    const out = path.join(tmp, "out");
    fs.mkdirSync(out);
    // Windows 10+ ships bsdtar, which extracts zip files. Call it by full path: a Git Bash
    // GNU tar earlier on PATH cannot read zips or `C:` paths.
    const tar = path.join(process.env.SystemRoot || "C:\\Windows", "System32", "tar.exe");
    execFileSync(fs.existsSync(tar) ? tar : "tar", ["-xf", zip, "-C", out]);
    // Zips may wrap everything in a single top-level folder.
    let root = out;
    const entries = fs.readdirSync(out);
    if (entries.length === 1 && fs.statSync(path.join(out, entries[0])).isDirectory()) {
      root = path.join(out, entries[0]);
    }
    fs.rmSync(dest, { recursive: true, force: true });
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.cpSync(root, dest, { recursive: true });
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

function fullStrength() {
  const file = path.join(extDir, "js", "mode-manager.js");
  const src = fs.readFileSync(file, "utf8");
  const patched = src
    .replace(/optimal:\s*\[\s*'all-urls'\s*\],/, "optimal: [],")
    .replace(/complete:\s*\[\s*\],/, "complete: [ 'all-urls' ],");
  if (patched === src && !/complete:\s*\[\s*'all-urls'\s*\]/.test(src)) {
    log("could not set uBlock Origin Lite to full strength; using its default mode");
  }
  fs.writeFileSync(file, patched);
}

async function ensureBrowser() {
  const update = process.env.KITE_BROWSER_UPDATE === "1";
  if (update || !fs.existsSync(chromeExe)) {
    const asset = await latestAsset("ungoogled-software/ungoogled-chromium-windows", /_windows_x64\.zip$/);
    log(`downloading ungoogled-chromium ${asset.tag} (first run can take a few minutes)`);
    await downloadAndExtract(asset, browserDir);
  }
  if (update || !fs.existsSync(path.join(extDir, "manifest.json"))) {
    const asset = await latestAsset("uBlockOrigin/uBOL-home", /\.chromium\.zip$/);
    log(`downloading uBlock Origin Lite ${asset.tag}`);
    await downloadAndExtract(asset, extDir);
  }
  fullStrength();
}

function readUserConfig() {
  try {
    return JSON.parse(fs.readFileSync(userConfigPath, "utf8"));
  } catch {
    return {};
  }
}

async function main() {
  let configPath = userConfigPath;
  const user = readUserConfig();
  const userLaunch = user.browser?.launchOptions ?? {};
  // Respect a user-chosen browser; otherwise use Kite's own.
  if (!userLaunch.executablePath && process.platform === "win32" && process.arch === "x64") {
    try {
      await ensureBrowser();
      const ext = extDir.replaceAll("\\", "/");
      const args = (userLaunch.args ?? []).filter(
        (a) => !a.startsWith("--load-extension=") && !a.startsWith("--disable-extensions-except="),
      );
      const { channel, ...launch } = userLaunch;
      const config = {
        ...user,
        browser: {
          ...user.browser,
          userDataDir: user.browser?.userDataDir ?? profileDir,
          launchOptions: {
            ...launch,
            executablePath: chromeExe,
            ignoreDefaultArgs: ["--disable-extensions"],
            args: [
              ...args,
              `--load-extension=${ext}`,
              `--disable-extensions-except=${ext}`,
              "--disable-background-networking",
              "--disable-sync",
              "--no-default-browser-check",
              "--no-first-run",
            ],
          },
        },
      };
      fs.writeFileSync(generatedConfigPath, JSON.stringify(config, null, 2));
      configPath = generatedConfigPath;
    } catch (err) {
      log(`browser setup failed (${err.message}); using installed Google Chrome`);
    }
  }
  const npx = process.platform === "win32" ? "npx.cmd" : "npx";
  // With a shell (needed for npx.cmd), quote the path so spaces survive.
  const shell = process.platform === "win32";
  const args = ["-y", MCP_PACKAGE];
  if (fs.existsSync(configPath)) args.push("--config", shell ? `"${configPath}"` : configPath);
  const child = spawn(npx, args, {
    stdio: "inherit",
    shell,
  });
  child.on("exit", (code) => process.exit(code ?? 1));
  for (const sig of ["SIGINT", "SIGTERM"]) process.on(sig, () => child.kill(sig));
}

main();
