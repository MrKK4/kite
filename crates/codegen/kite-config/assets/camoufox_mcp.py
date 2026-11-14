# Kite's Camoufox MCP server (written by Kite to ~/.kite/camoufox-mcp.py; edits are overwritten).
# Starts Camoufox through its official launcher, so its generated fingerprint configuration is
# applied, then runs Playwright MCP connected to that browser over Playwright's remote protocol.
# Self-installing and isolated: on first run it creates ~/.kite/camoufox-venv, installs the latest
# Camoufox there and downloads its browser. KITE_CAMOUFOX_UPDATE=1 reinstalls. Needs Python 3 and
# Node.js (npx).
import json
import os
import shutil
import queue
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

# Playwright MCP must speak the same Playwright minor version as the Python camoufox server,
# so the venv pins Playwright to match this MCP release (Playwright 1.62).
MCP_PACKAGE = os.environ.get("KITE_CAMOUFOX_MCP_PACKAGE", "@playwright/mcp@0.0.78")
PLAYWRIGHT_PIN = os.environ.get("KITE_CAMOUFOX_PLAYWRIGHT", "playwright==1.62.*")
VENV = Path(os.environ.get("KITE_HOME") or Path.home() / ".kite") / "camoufox-venv"
VENV_PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def fail(message):
    print(f"camoufox-mcp: {message}", file=sys.stderr)
    sys.exit(1)


def kill_tree(proc):
    # The launcher runs Node and the browser as children; end the whole tree.
    if os.name == "nt":
        subprocess.call(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    proc.terminate()
    try:
        proc.wait(10)
    except subprocess.TimeoutExpired:
        proc.kill()


def run_quiet(args):
    # stdout is the MCP channel: send installer output to stderr.
    subprocess.check_call(args, stdin=subprocess.DEVNULL, stdout=sys.stderr, stderr=sys.stderr)


def ensure_venv():
    """Re-run this script inside Kite's own Camoufox venv, creating it on first use."""
    if Path(sys.prefix).resolve() == VENV.resolve():
        return
    update = os.environ.get("KITE_CAMOUFOX_UPDATE") == "1"
    if update or not VENV_PY.exists():
        print("camoufox-mcp: installing Camoufox into ~/.kite/camoufox-venv (first run takes a few minutes)", file=sys.stderr)
        try:
            if not VENV_PY.exists():
                run_quiet([sys.executable, "-m", "venv", str(VENV)])
            run_quiet([str(VENV_PY), "-m", "pip", "install", "-U", "--quiet", "camoufox[geoip]", PLAYWRIGHT_PIN])
            run_quiet([str(VENV_PY), "-m", "camoufox", "fetch"])
        except (OSError, subprocess.CalledProcessError) as error:
            fail(f"Camoufox setup failed: {error}")
    sys.exit(subprocess.call([str(VENV_PY), os.path.abspath(__file__)]))


def main():
    ensure_venv()
    try:
        import camoufox  # noqa: F401
    except ImportError:
        fail("Camoufox is missing from ~/.kite/camoufox-venv. Retry with KITE_CAMOUFOX_UPDATE=1.")
    npx = shutil.which("npx")
    if not npx:
        fail("npx not found. Install Node.js.")

    headless = os.environ.get("KITE_CAMOUFOX_HEADLESS", "") == "1"
    def start_server():
        # The launcher prints the browser's websocket endpoint on stdout (stdout is the MCP channel, so pipe it).
        proc = subprocess.Popen(
            [sys.executable, "-u", "-c",
             f"from camoufox.server import launch_server; launch_server(headless={headless})"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=sys.stderr, text=True,
        )
        endpoints = queue.Queue()

        def read_stdout():
            for line in proc.stdout:
                found = re.search(r"wss?://\S+", line)
                if found:
                    endpoints.put(found.group(0))
            endpoints.put(None)

        threading.Thread(target=read_stdout, daemon=True).start()
        try:
            return proc, endpoints.get(timeout=180)
        except queue.Empty:
            return proc, None

    # The very first launch downloads Camoufox's fingerprint model and can exit early; retry once.
    server, endpoint = start_server()
    if not endpoint:
        kill_tree(server)
        print("camoufox-mcp: first launch failed, retrying", file=sys.stderr)
        server, endpoint = start_server()
    try:
        if not endpoint:
            fail("Camoufox failed to start (see errors above). Retry with KITE_CAMOUFOX_UPDATE=1.")
        config = {
            "browser": {
                "browserName": "firefox",
                "remoteEndpoint": endpoint,
                "contextOptions": {"viewport": None},
            }
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        try:
            args = [npx, "-y", MCP_PACKAGE, "--config", config_path]
            # Lean mode like Kite's Chromium server: no snapshot after actions; browser_snapshot
            # saves to a file. KITE_BROWSER_LEAN=0 restores inline snapshots.
            if os.environ.get("KITE_BROWSER_LEAN") != "0":
                out = os.environ.get("KITE_BROWSER_OUTPUT") or str(Path.home() / "Downloads" / "Kite")
                os.makedirs(out, exist_ok=True)
                args += ["--snapshot-mode", "none", "--output-mode", "file", "--output-dir", out]
            sys.exit(subprocess.call(args))
        finally:
            os.unlink(config_path)
    finally:
        kill_tree(server)


if __name__ == "__main__":
    main()
