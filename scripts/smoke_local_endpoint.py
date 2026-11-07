"""Exercise a built Kite against a mock server; never calls a real model API.

Usage: py -3 scripts/smoke_local_endpoint.py dist/kite.exe
"""

import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class CheckedServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        error = sys.exc_info()[1]
        if isinstance(error, (BrokenPipeError, ConnectionResetError)):
            return  # The agent may cancel an optional background request at exit.
        self.errors.append(repr(error))
        super().handle_error(request, client_address)


class ModelServer(BaseHTTPRequestHandler):
    requests = []
    marker = "kite-tool-roundtrip-ok"

    def log_message(self, *_):
        pass

    def do_GET(self):
        assert self.headers.get("Authorization") is None
        # Transport prewarming may probe the origin before inference.
        if self.path == "/":
            body = b'{"status":"ok"}'
        else:
            assert self.path == "/v1/models", self.path
            body = json.dumps({"data": [{"id": "qwen-smoke", "object": "model"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.requests.append(body)
        assert self.path == "/v1/chat/completions", self.path
        assert body["model"] == "qwen-smoke", body.get("model")
        assert "reasoning_effort" not in body
        assert "store" not in body
        assert "max_completion_tokens" not in body
        assert all(m["role"] != "developer" for m in body["messages"])
        names = [t["function"]["name"] for t in body.get("tools", [])]
        assert "task" not in names and "send_subagent_message" not in names
        read = next((t["function"] for t in body.get("tools", [])
                     if t["function"]["name"].lower() in ("read_file", "read")), None)
        tool_output = next((m for m in body["messages"] if m["role"] == "tool"), None)
        if tool_output:
            assert self.marker in str(tool_output), tool_output
            delta = {"content": "Kite local smoke passed."}
            finish = "stop"
        elif read is None:
            # Session titles and other side calls need no tool round trip.
            delta = {"content": "Kite smoke test"}
            finish = "stop"
        else:
            # Side calls may use a smaller explicit token budget.
            if body.get("max_tokens") is not None:
                assert 0 < body["max_tokens"] <= 32_768
            props = read["parameters"]["properties"]
            path_key = next(k for k in ("target_file", "file_path", "path") if k in props)
            delta = {"tool_calls": [{"index": 0, "id": "read-smoke", "type": "function", "function": {
                "name": read["name"], "arguments": json.dumps({path_key: "marker.txt"}),
            }}]}
            finish = "tool_calls"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Connection", "close")
        self.end_headers()
        for change, stop in ((delta, None), ({}, finish)):
            event = {"id": "smoke", "object": "chat.completion.chunk", "created": 0, "model": "qwen-smoke",
                     "choices": [{"index": 0, "delta": change, "finish_reason": stop}]}
            self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()
        self.close_connection = True


class Agent:
    def __init__(self, binary, workspace, home):
        env = os.environ.copy()
        env["KITE_HOME"] = str(home)
        self.stderr = (home / "smoke-stderr.log").open("wb")
        self.process = subprocess.Popen(
            [str(binary), "agent", "--no-leader", "--always-approve", "stdio"],
            cwd=workspace, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.stderr, text=True, encoding="utf-8", bufsize=1,
        )
        self.messages = queue.Queue()
        self.next_id = 0
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.process.stdout:
            try:
                self.messages.put(json.loads(line))
            except json.JSONDecodeError:
                continue

    def call(self, method, params, expect_error=False):
        self.next_id += 1
        request_id = self.next_id
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}) + "\n")
        self.process.stdin.flush()
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(f"Kite exited {self.process.returncode}; see {self.stderr.name}")
            try:
                message = self.messages.get(timeout=1)
            except queue.Empty:
                continue
            if message.get("id") == request_id and "method" not in message:
                assert ("error" in message) == expect_error, message
                return message.get("result", message.get("error"))
            if "id" in message and "method" in message:
                raise AssertionError(f"unexpected reverse request: {message['method']}")
        raise TimeoutError(f"{method} timed out; see {self.stderr.name}")

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.stderr.close()


def main(binary):
    binary = Path(binary).resolve()
    assert binary.is_file(), binary
    with tempfile.TemporaryDirectory(prefix="kite-smoke-") as directory:
        root = Path(directory)
        workspace, home = root / "workspace", root / "home"
        workspace.mkdir()
        home.mkdir()
        (workspace / "marker.txt").write_text(ModelServer.marker)
        isolation = "[memory]\nenabled = false\n[cli]\nuse_leader = false\n"
        for vendor in ("claude", "cursor", "codex"):
            isolation += f"[compat.{vendor}]\n" + "".join(
                f"{surface} = false\n" for surface in ("skills", "rules", "agents", "mcps", "hooks", "sessions")
            )
        (home / "config.toml").write_text(isolation)
        server = CheckedServer(("127.0.0.1", 0), ModelServer)
        server.errors = []
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{server.server_port}/v1"
        try:
            for restarted in (False, True):
                agent = Agent(binary, workspace, home)
                try:
                    initialized = agent.call("initialize", {"protocolVersion": 1, "clientCapabilities": {}})
                    assert not initialized.get("authMethods"), initialized.get("authMethods")
                    if not restarted:
                        result = agent.call("authenticate", {"methodId": "local_endpoint:" + url})
                        assert "local_models" in result["_meta"], result
                        saved = (home / "config.toml").read_bytes()
                        config = tomllib.loads(saved.decode())
                        entry = config["model"]["local:qwen-smoke"]
                        assert entry["auto_compact_at_tokens"] == 220_000
                        assert entry["context_window"] == 262_144
                        agent.call("authenticate", {"methodId": "local_endpoint:file:///invalid"}, expect_error=True)
                        assert (home / "config.toml").read_bytes() == saved
                    session = agent.call("session/new", {"cwd": str(workspace), "mcpServers": []})
                    result = agent.call("session/prompt", {"sessionId": session["sessionId"], "prompt": [
                        {"type": "text", "text": "Read marker.txt using read_file, then report its content."},
                    ]})
                    assert result["stopReason"] == "end_turn", result
                    print("PASS:", "restart with saved endpoint" if restarted else "discover, save, reject invalid URL, tool round trip")
                finally:
                    agent.close()
            assert len(ModelServer.requests) >= 4
            assert not server.errors, server.errors
        finally:
            server.shutdown()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dist/kite.exe")
