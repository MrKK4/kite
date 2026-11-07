"""Audit the built Kite's request pruning with synthetic usage, without a real LLM.

Runs in a disposable KITE_HOME and workspace. Captures sizes only, not payloads.
Usage: python scripts/audit_context_pruning.py dist/kite.exe
"""

import json
import argparse
from pathlib import Path
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler

from smoke_local_endpoint import Agent, CheckedServer


class Probe(BaseHTTPRequestHandler):
    captures = []

    def log_message(self, *_):
        pass

    def do_GET(self):
        body = json.dumps({"data": [{"id": "qwen-smoke"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        body = json.loads(raw)
        assert self.path == "/v1/chat/completions"
        tools = body.get("tools", [])
        old_results = [m for m in body["messages"] if m["role"] == "tool"]
        result_size = len(str(old_results[0]["content"])) if old_results else 0
        capture = {
            "request": len(self.captures) + 1,
            "bytes": len(raw),
            "messages": len(body["messages"]),
            "old_tool_result_chars": result_size,
            "chat_template_kwargs": body.get("chat_template_kwargs"),
        }
        read = next((t["function"] for t in tools if t["function"]["name"].lower() in ("read_file", "read")), None)
        if read is not None:
            self.captures.append(capture)
        if not old_results and read is not None:
            props = read["parameters"]["properties"]
            key = next(k for k in ("target_file", "file_path", "path") if k in props)
            delta = {"tool_calls": [{"index": 0, "id": "probe-read", "type": "function", "function": {
                "name": read["name"], "arguments": json.dumps({key: "marker.txt"}),
            }}]}
            finish = "tool_calls"
        else:
            delta, finish = {"content": "ok"}, "stop"
        # Deliberately synthetic: exercise the >131072-token gate without
        # creating a real 150k-token prompt or paying for model inference.
        prompt_tokens = 150_000 if not old_results or result_size > 4000 else 50_000
        capture["synthetic_prompt_tokens"] = prompt_tokens
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Connection", "close")
        self.end_headers()
        for change, stop in ((delta, None), ({}, finish)):
            event = {"id": "audit", "object": "chat.completion.chunk", "created": 0, "model": "qwen-smoke",
                     "choices": [{"index": 0, "delta": change, "finish_reason": stop}]}
            if stop:
                event["usage"] = {"prompt_tokens": prompt_tokens, "completion_tokens": 1,
                                  "total_tokens": prompt_tokens + 1}
            self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()
        self.close_connection = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", nargs="?", default="dist/kite.exe")
    parser.add_argument("--disable-pruning", action="store_true")
    args = parser.parse_args()
    binary = Path(args.binary).resolve()
    with tempfile.TemporaryDirectory(prefix="kite-pruning-audit-") as directory:
        root = Path(directory)
        workspace, home = root / "workspace", root / "home"
        workspace.mkdir()
        home.mkdir()
        (workspace / "marker.txt").write_text("AUDIT_MARKER " * 900)
        enabled = "false" if args.disable_pruning else "true"
        config = f"[memory]\nenabled = false\n[cli]\nuse_leader = false\n[compaction.pruning]\nenabled = {enabled}\n"
        for vendor in ("claude", "cursor", "codex"):
            config += f"[compat.{vendor}]\n" + "".join(
                f"{surface} = false\n" for surface in ("skills", "rules", "agents", "mcps", "hooks", "sessions")
            )
        (home / "config.toml").write_text(config)
        server = CheckedServer(("127.0.0.1", 0), Probe)
        server.errors = []
        threading.Thread(target=server.serve_forever, daemon=True).start()
        agent = Agent(binary, workspace, home)
        try:
            agent.call("initialize", {"protocolVersion": 1, "clientCapabilities": {}})
            agent.call("authenticate", {"methodId": f"local_endpoint:http://127.0.0.1:{server.server_port}/v1"})
            session = agent.call("session/new", {"cwd": str(workspace), "mcpServers": []})
            for turn in range(7):
                reply = agent.call("session/prompt", {"sessionId": session["sessionId"], "prompt": [
                    {"type": "text", "text": "Read marker.txt." if turn == 0 else f"Say ok. Turn {turn}."},
                ]})
                assert reply["stopReason"] == "end_turn", reply
            assert not server.errors, server.errors
            results = [r["old_tool_result_chars"] for r in Probe.captures if r["old_tool_result_chars"]]
            restored = any(a <= 4000 < b for a, b in zip(results, results[1:]))
            print(json.dumps({"synthetic_usage": True, "binary": str(binary),
                              "pruning_enabled": not args.disable_pruning,
                              "old_result_restored_after_pruning": restored, "requests": Probe.captures}, indent=2))
            if args.disable_pruning:
                assert not restored and len(set(results)) == 1, "Disabled pruning must preserve the old tool result"
            else:
                assert restored, "Expected request-copy pruning to restore an old result on a later request"
        finally:
            agent.close()
            server.shutdown()


if __name__ == "__main__":
    main()
