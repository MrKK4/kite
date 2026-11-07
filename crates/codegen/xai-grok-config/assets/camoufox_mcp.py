# Kite's Camoufox MCP server (written by Kite to ~/.kite/camoufox-mcp.py; edits are overwritten).
# Starts Camoufox through its official launcher, so its generated fingerprint configuration is
# applied, then runs Playwright MCP connected to that browser over Playwright's remote protocol.
# Needs: pip install -U camoufox[geoip] && python -m camoufox fetch, plus Node.js (npx).
import json
import os
import shutil
import queue
import re
import subprocess
import sys
import tempfile
import threading

# Playwright MCP must speak the same Playwright minor version as the Python camoufox server.
MCP_PACKAGE = os.environ.get("KITE_CAMOUFOX_MCP_PACKAGE", "@playwright/mcp@0.0.78")


def fail(message):
    print(f"camoufox-mcp: {message}", file=sys.stderr)
    sys.exit(1)


def main():
    try:
        import camoufox  # noqa: F401
    except ImportError:
        fail("Python package 'camoufox' is missing. Run: pip install -U camoufox[geoip] && python -m camoufox fetch")
    npx = shutil.which("npx")
    if not npx:
        fail("npx not found. Install Node.js.")

    headless = os.environ.get("KITE_CAMOUFOX_HEADLESS", "") == "1"
    # The launcher prints the browser's websocket endpoint on stdout (stdout is the MCP channel, so pipe it).
    server = subprocess.Popen(
        [sys.executable, "-u", "-c",
         f"from camoufox.server import launch_server; launch_server(headless={headless})"],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=sys.stderr, text=True,
    )
    try:
        endpoints = queue.Queue()

        def read_stdout():
            for line in server.stdout:
                found = re.search(r"wss?://\S+", line)
                if found:
                    endpoints.put(found.group(0))
            endpoints.put(None)

        threading.Thread(target=read_stdout, daemon=True).start()
        try:
            endpoint = endpoints.get(timeout=180)
        except queue.Empty:
            endpoint = None
        if not endpoint:
            fail("Camoufox failed to start (see errors above). Try: python -m camoufox fetch")
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
            sys.exit(subprocess.call([npx, "-y", MCP_PACKAGE, "--config", config_path]))
        finally:
            os.unlink(config_path)
    finally:
        # The launcher runs Node and the browser as children; end the whole tree.
        if os.name == "nt":
            subprocess.call(["taskkill", "/T", "/F", "/PID", str(server.pid)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        server.terminate()
        try:
            server.wait(10)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
