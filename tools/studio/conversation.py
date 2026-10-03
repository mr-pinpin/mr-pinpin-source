"""Durable local conversation with one persistent Codex app-server thread."""
import copy
import hashlib
import json
import threading
from pathlib import Path
from model import StudioError, now, new_id
from store import atomic_json
from conversation_context import POLICY_VERSION, selected_context, instructions
from conversation_transport import AppServer, AgentUnavailable

ACTIVE = {"connecting", "running", "interrupting"}


class Conversation:
    def __init__(self, store, transport_factory=AppServer, workspace_source=None):
        self.store = store
        self.workspace_source = Path(workspace_source).resolve() if workspace_source else None
        self.path = store.root / "conversation.json"
        self.lock = threading.RLock()
        self.transport_factory = transport_factory
        self.transport = None
        self.cancelled = False
        self.last_agent_error = None
        self.closed = False
        self.state = json.loads(self.path.read_text()) if self.path.exists() else {
            "id": "studio", "threadId": None, "activeTurnId": None, "status": "idle",
            "messages": [], "error": None, "model": None, "usage": None, "plan": [],
            "events": [], "cursor": 0}
        if self.state["status"] in ACTIVE:
            self._finish("interrupted", {"code": "server_restarted",
                "message": "Studio restarted during this turn. Send a message to resume the conversation."})

    def _save(self):
        atomic_json(self.path, self.state)

    def _event(self, event_type, **fields):
        self.state["cursor"] += 1
        self.state["events"].append({"seq": self.state["cursor"], "type": event_type,
                                     "createdAt": now(), **fields})
        # Transcript persists in full; incremental events are a bounded replay window.
        self.state["events"] = self.state["events"][-1000:]
        self._save()

    def snapshot(self, after=0):
        with self.lock:
            state = copy.deepcopy(self.state)
        events = state.pop("events")
        cursor = state.pop("cursor")
        state.pop("instructionPolicy", None)
        return {"conversation": state, "events": [e for e in events if e["seq"] > after],
                "cursor": cursor}

    def send(self, body):
        text, scope, inputs = selected_context(self.store, body)
        with self.lock:
            if self.closed:
                raise StudioError("Studio is shutting down", "unavailable", 503)
            if self.state["status"] in ACTIVE:
                raise StudioError("A response is already running. Stop it or wait.", "conversation_busy", 409)
            self.cancelled = False
            self.last_agent_error = None
            message = {"id": new_id("message"), "role": "user", "text": text,
                       "status": "sent", "createdAt": now(), "turnId": None, "context": scope}
            self.state["messages"].append(message)
            self.state.update(status="connecting", error=None, plan=[], activeTurnId=None)
            self._event("message", messageId=message["id"])
            threading.Thread(target=self._start, args=(inputs, message["id"], bool(scope.get("reviewSnapshot"))), daemon=True).start()
            return self.snapshot()

    def _start(self, inputs, message_id, review=False):
        phase = "connect"
        try:
            if self.transport is None or self.transport.process.poll() is not None:
                self.transport = self.transport_factory(self.notify, self.store.root)
            policy = instructions(self.store, self.workspace_source, review)
            params = {"cwd": str(self.store.root), "approvalPolicy": "never",
                      "sandbox": "read-only" if review else "workspace-write",
                      "developerInstructions": policy}
            with self.lock:
                thread_id = self.state["threadId"]
            if thread_id:
                params["threadId"] = thread_id
            # Resume can rejoin an already loaded thread without replacing its history.
            # A durable developer policy item below updates model-visible scope explicitly.
            response = self.transport.request("thread/resume" if thread_id else "thread/start", params)
            with self.lock:
                self.state["threadId"] = response["thread"]["id"]
                self.state["model"] = response.get("model")
                self._event("status", status="connecting")
            with self.lock:
                if self.cancelled or self.closed:
                    self._finish("interrupted")
                    return
                thread_id = self.state["threadId"]
            phase = "policy"
            policy_hash = hashlib.sha256(policy.encode()).hexdigest()
            with self.lock:
                applied = self.state.get("instructionPolicy") or {}
                needs_policy = applied.get("threadId") != thread_id or applied.get("sha256") != policy_hash
            if needs_policy:
                self.transport.request("thread/inject_items", {
                    "threadId": thread_id,
                    "items": [{"type": "message", "role": "developer",
                               "content": [{"type": "input_text", "text": policy}]}]})
                # Persist only after upstream confirms the trusted item was appended.
                with self.lock:
                    self.state["instructionPolicy"] = {"threadId": thread_id, "sha256": policy_hash,
                        "version": POLICY_VERSION, "scope": "review" if review else "live", "updatedAt": now()}
                    self._save()
            with self.lock:
                if self.cancelled or self.closed:
                    self._finish("interrupted")
                    return
            phase = "turn"
            writable = [str(self.store.root)]
            if self.workspace_source:
                writable.append(str(self.workspace_source))
            sandbox = {"type": "readOnly", "networkAccess": False} if review else {
                "type": "workspaceWrite", "writableRoots": writable,
                "networkAccess": False, "excludeSlashTmp": True, "excludeTmpdirEnvVar": True}
            response = self.transport.request("turn/start", {
                "threadId": thread_id, "input": inputs, "cwd": str(self.store.root),
                "approvalPolicy": "never", "sandboxPolicy": sandbox})
            with self.lock:
                turn_id = response["turn"]["id"]
                for message in self.state["messages"]:
                    if message["id"] == message_id:
                        message["turnId"] = turn_id
                if self.state["status"] in ACTIVE:
                    self.state["activeTurnId"] = turn_id
                    self.state["status"] = "interrupting" if self.cancelled else "running"
                    self._event("status", status=self.state["status"])
                cancel = self.cancelled
            if cancel:
                self.transport.request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})
        except Exception:
            with self.lock:
                error = {"code": "policy_update_failed",
                         "message": "Studio could not refresh this conversation's permissions. No turn was started; try again."} if phase == "policy" else {
                         "code": "agent_unavailable",
                         "message": "Local Codex is unavailable. Check the Mac mini Codex login/model, then send again."}
                failed_transport = self.transport
                self.transport = None
                self._finish("error", error)
            if failed_transport:
                failed_transport.close()

    def _assistant(self, identifier, turn_id):
        for message in self.state["messages"]:
            if message["id"] == identifier:
                return message
        message = {"id": identifier, "role": "assistant", "text": "", "status": "streaming",
                   "createdAt": now(), "turnId": turn_id}
        self.state["messages"].append(message)
        return message

    def _finish(self, status, error=None):
        self.state.update(status=status, error=error, activeTurnId=None)
        for message in self.state["messages"]:
            if message["status"] == "streaming":
                message["status"] = status
        self._event("status", status=status)

    def notify(self, method, params):
        with self.lock:
            if self.closed:
                return
            thread_id = params.get("threadId")
            if thread_id and self.state["threadId"] and thread_id != self.state["threadId"]:
                return
            turn_id = params.get("turnId")
            if method == "item/agentMessage/delta":
                message = self._assistant(params["itemId"], turn_id)
                message["text"] += params.get("delta", "")
                self._event("delta", messageId=message["id"], delta=params.get("delta", ""))
            elif method == "item/completed":
                item = params.get("item", {})
                if item.get("type") == "agentMessage":
                    message = self._assistant(item["id"], turn_id)
                    message.update(text=item.get("text", message["text"]), status="completed",
                                   phase=item.get("phase"))
                    self._event("message", messageId=message["id"])
                elif item.get("type") == "plan":
                    self.state["planText"] = item.get("text", "")
                    self._event("plan")
                elif item.get("type") not in ("reasoning", "userMessage"):
                    # Never expose commands, tool output, credentials, or hidden reasoning.
                    self._event("activity", kind=item.get("type"), status=item.get("status", "completed"))
            elif method == "item/started":
                item = params.get("item", {})
                if item.get("type") not in ("reasoning", "userMessage", "agentMessage"):
                    self._event("activity", kind=item.get("type"), status="running")
            elif method == "turn/started":
                self.state["activeTurnId"] = params["turn"]["id"]
                self.state["status"] = "interrupting" if self.cancelled else "running"
                self._event("status", status=self.state["status"])
            elif method == "turn/completed":
                turn = params.get("turn", {})
                status = turn.get("status", "completed")
                status = status if status in ("completed", "interrupted") else "error"
                error = {"code": "turn_failed", "message":
                         "Codex could not finish this turn. Check local login/model availability or try again."} if status == "error" else None
                self._finish(status, self.last_agent_error or error)
            elif method == "thread/tokenUsage/updated":
                self.state["usage"] = params.get("tokenUsage")
                self._event("usage")
            elif method == "turn/plan/updated":
                self.state["plan"] = params.get("plan", [])
                self._event("plan")
            elif method == "studio/approvalRequired":
                self._event("activity", kind="approval", status="blocked")
            elif method == "studio/disconnected" and self.state["status"] in ACTIVE:
                self._finish("error", {"code": "agent_disconnected",
                                      "message": "Local Codex disconnected. Send again to reconnect."})
            elif method == "error":
                description = str(params.get("error", {}).get("message", "")).lower()
                if any(word in description for word in ("unauthorized", "authentication", "401", "sign in", "login")):
                    self.last_agent_error = {"code": "login_required", "message":
                        "The Mac mini Codex login needs to be renewed. Sign in to Codex on the mini, then send again."}
                self._event("activity", kind="agent", status="retrying" if params.get("willRetry") else "error")

    def interrupt(self):
        with self.lock:
            if self.state["status"] not in ACTIVE:
                return self.snapshot()
            self.cancelled = True
            self.state["status"] = "interrupting"
            turn_id = self.state["activeTurnId"]
            thread_id = self.state["threadId"]
            self._event("status", status="interrupting")
        if turn_id and self.transport:
            try:
                self.transport.request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})
            except AgentUnavailable:
                with self.lock:
                    self._finish("interrupted")
        return self.snapshot()

    def close(self):
        with self.lock:
            self.closed = True
            if self.state["status"] in ACTIVE:
                self._finish("interrupted", {"code": "server_stopped", "message": "Studio stopped during the turn."})
        if self.transport:
            self.transport.close()
