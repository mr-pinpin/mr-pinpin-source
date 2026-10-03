"""Minimal private stdio transport for the installed Codex app-server."""
import json
import os
import queue
import shutil
import subprocess
import threading


class AgentUnavailable(RuntimeError):
    pass


class AppServer:
    def __init__(self, notify, cwd):
        self.notify = notify
        self.pending = {}
        self.lock = threading.Lock()
        self.counter = 0
        self.closed = False
        env = os.environ.copy()
        env["PATH"] = "/opt/homebrew/bin:" + env.get("PATH", "")
        binary = os.environ.get("PINPIN_CODEX_BIN") or shutil.which("codex", path=env["PATH"])
        if not binary:
            raise AgentUnavailable("Local Codex is not installed.")
        # Authentication stays inside Codex. Never read or forward credentials.
        self.process = subprocess.Popen(
            [binary, "app-server", "--stdio"], cwd=str(cwd), env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", bufsize=1)
        threading.Thread(target=self._read, daemon=True).start()
        try:
            self.request("initialize", {"clientInfo": {
                "name": "pinpin_studio", "title": "PinPin Studio", "version": "1.0"}})
            self._write({"method": "initialized", "params": {}})
        except Exception:
            self.close()
            raise

    def _write(self, payload):
        with self.lock:
            if self.closed or self.process.poll() is not None:
                raise AgentUnavailable("Local Codex connection closed. Send again to reconnect.")
            self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self.process.stdin.flush()

    def request(self, method, params, timeout=45):
        with self.lock:
            self.counter += 1
            identifier = self.counter
            result = queue.Queue(maxsize=1)
            self.pending[identifier] = result
        try:
            self._write({"id": identifier, "method": method, "params": params})
            try:
                response = result.get(timeout=timeout)
            except queue.Empty:
                raise AgentUnavailable("Local Codex did not respond in time. Try again.")
            if "error" in response:
                # Do not expose upstream errors, which can contain credentials or paths.
                raise AgentUnavailable("Local Codex could not complete " + method +
                                       ". Check its local login and model availability.")
            return response.get("result", {})
        finally:
            with self.lock:
                self.pending.pop(identifier, None)

    def _read(self):
        try:
            for line in self.process.stdout:
                try:
                    item = json.loads(line)
                except ValueError:
                    continue
                if "method" not in item and "id" in item:
                    with self.lock:
                        target = self.pending.get(item["id"])
                    if target:
                        target.put_nowait(item)
                elif "method" in item and "id" in item:
                    # Never auto-approve escalations, MCP requests, or interactive prompts.
                    self._write({"id": item["id"], "error": {
                        "code": -32601, "message": "Interactive approval unavailable in Studio"}})
                    self.notify("studio/approvalRequired", {})
                elif "method" in item:
                    self.notify(item["method"], item.get("params", {}))
        except (OSError, ValueError, BrokenPipeError):
            pass
        finally:
            with self.lock:
                for target in self.pending.values():
                    try:
                        target.put_nowait({"error": {"message": "disconnected"}})
                    except queue.Full:
                        pass
            if not self.closed:
                self.notify("studio/disconnected", {})

    def close(self):
        self.closed = True
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        for stream in (self.process.stdin, self.process.stdout):
            stream.close()
