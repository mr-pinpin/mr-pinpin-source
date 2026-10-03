#!/usr/bin/env python3
"""Shared client for Studio's existing persisted conversation (stdlib only)."""
import argparse
from datetime import datetime, timezone
from timings import measure
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ACTIVE = {"connecting", "running", "interrupting"}


class ClientError(Exception):
    def __init__(self, code, message, exit_code=1, **details):
        super().__init__(message)
        self.payload = {"error": {"code": code, "message": message}, **details}
        self.exit_code = exit_code


class Client:
    def __init__(self, url, timeout=15):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ClientError("invalid_url", "Use an HTTP(S) Studio base URL without credentials, query or fragment.", 2)
        self.url = url.rstrip("/")
        self.timeout = timeout

    def request(self, path, body=None, timeout=None):
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        request = urllib.request.Request(self.url + path, data=data, headers={"Content-Type": "application/json", "Accept": "application/json"})
        # Never retry a POST: a lost response does not mean the message was rejected.
        try:
            with urllib.request.urlopen(request, timeout=timeout or self.timeout) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                result = json.loads(exc.read())
            except (ValueError, UnicodeError):
                result = {}
            error = result.get("error", {}) if isinstance(result, dict) else {}
            message = error.get("message", str(exc)) if isinstance(error, dict) else str(error)
            raise ClientError("conversation_busy" if exc.code == 409 else "http_error", message, 3 if exc.code == 409 else 1, httpStatus=exc.code) from exc
        except (OSError, urllib.error.URLError, ValueError) as exc:
            raise ClientError("transport_error", str(exc), outcomeUnknown=body is not None,
                              advice="Read the conversation before retrying; this client never resends automatically." if body is not None else "Check the Studio URL and connection.") from exc
        if not isinstance(result, dict) or not isinstance(result.get("conversation"), dict):
            raise ClientError("invalid_response", "Studio returned an invalid conversation snapshot.", outcomeUnknown=body is not None)
        return result

    def get(self, after=0, timeout=None):
        return self.request("/api/conversation?after=" + str(after), timeout=timeout)


def summary(snapshot):
    conversation = snapshot["conversation"]
    return {key: conversation.get(key) for key in ("id", "threadId", "status", "activeTurnId", "error")} | {
        "cursor": snapshot.get("cursor", 0), "messageCount": len(conversation.get("messages", []))}


def label(value):
    if not value or len(value) > 80 or not re.fullmatch(r"[\w .@-]+", value):
        raise argparse.ArgumentTypeError("Use 1–80 letters, numbers, spaces, dot, @, hyphen or underscore.")
    return value


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("Must be a finite positive number.")
    return number


def nonnegative(value):
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("Must be nonnegative.")
    return number


def wait(client, timeout, interval, message_id=None, snapshot=None):
    deadline = time.monotonic() + timeout
    snapshot = snapshot or client.get(timeout=min(client.timeout, timeout))
    while True:
        conversation = snapshot["conversation"]
        messages = conversation.get("messages", [])
        result = summary(snapshot)
        target = next((item for item in messages if item.get("id") == message_id), None) if message_id else None
        if message_id and not target:
            raise ClientError("message_not_found", "Message ID is absent from this conversation.", 2, messageId=message_id)
        turn_id = target.get("turnId") if target else None
        replies = [item for item in messages if item.get("role") == "assistant" and turn_id and item.get("turnId") == turn_id]
        terminal = conversation.get("status") not in ACTIVE
        if target:
            position = messages.index(target)
            later_users = any(item.get("role") == "user" for item in messages[position + 1:])
            final = any(item.get("phase") == "final_answer" and item.get("status") == "completed" for item in replies)
            if later_users:
                if final:
                    return result | {"messageId": message_id, "turnId": turn_id, "outcome": "completed", "messages": replies}
                raise ClientError("superseded", "A later user message exists; inspect this turn's history before deciding its outcome.", 1, messageId=message_id, turnId=turn_id, messages=replies)
            terminal = terminal and conversation.get("activeTurnId") != turn_id if turn_id else terminal
        if terminal:
            outcome = conversation.get("status", "idle")
            result.update(outcome=outcome, messageId=message_id, turnId=turn_id, messages=replies if target else messages[-1:])
            if outcome in ("error", "interrupted"):
                raise ClientError("turn_" + outcome, "Studio turn " + outcome + ".", 1, receipt=result)
            return result
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ClientError("wait_timeout", "Wait timed out; the Studio turn continues. Use wait or read, do not resend.", 4, receipt=result | {"messageId": message_id, "turnId": turn_id})
        time.sleep(min(interval, remaining))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            continue
        snapshot = client.get(snapshot.get("cursor", 0), timeout=min(client.timeout, remaining))


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--url", default=os.environ.get("PINPIN_STUDIO_URL", "http://127.0.0.1:18826"))
    common.add_argument("--json", action="store_true", help="Print one JSON result (including runtime errors).")
    common.add_argument("--request-timeout", type=positive, default=15, help="Seconds per HTTP request.")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("status", parents=[common])
    read = commands.add_parser("read", parents=[common])
    read.add_argument("--limit", type=nonnegative, default=20, help="Newest messages; 0 means all.")
    read.add_argument("--after", type=nonnegative, default=None, help="Opt in to events after this cursor; does not filter messages.")
    send = commands.add_parser("send", parents=[common])
    send.add_argument("--actor", type=label, required=True, help="Visible provenance label, not authentication.")
    send.add_argument("--on-behalf-of", type=label)
    content = send.add_mutually_exclusive_group(required=True)
    content.add_argument("--text")
    content.add_argument("--message-file", help="UTF-8 file, or - for stdin.")
    send.add_argument("--chapter")
    send.add_argument("--scene", action="append", default=[])
    send.add_argument("--entity")
    send.add_argument("--asset", action="append", default=[])
    send.add_argument("--revision", type=nonnegative)
    send.add_argument("--wait", action="store_true")
    for command in (send, commands.add_parser("wait", parents=[common])):
        command.add_argument("--timeout", type=positive, default=300, help="Total wait seconds.")
        command.add_argument("--poll", type=positive, default=1, help="Polling seconds, minimum 0.25.")
    measurement = commands.add_parser("measure", parents=[common])
    measurement.add_argument("--message-id", required=True)
    measurement.add_argument("--capture-file", help="Persist compact timestamp events for resumable measurement.")
    measurement.add_argument("--once", action="store_true", help="Report current measurements without waiting.")
    measurement.add_argument("--timeout", type=positive, default=300)
    measurement.add_argument("--poll", type=positive, default=1)
    commands.choices["wait"].add_argument("--message-id", help="Wait for a saved send receipt; otherwise observe current turn.")
    return root


def run(args):
    client = Client(args.url, args.request_timeout)
    if args.command == "measure":
        return measure(client, args, ClientError)
    if args.command == "status":
        return summary(client.get())
    if args.command == "read":
        snapshot = client.get(args.after or 0)
        messages = snapshot["conversation"].get("messages", [])
        result = summary(snapshot) | {"messages": messages[-args.limit:] if args.limit else messages}
        if args.after is not None:
            result["events"] = snapshot.get("events", [])
        return result
    if args.command == "wait":
        return wait(client, args.timeout, max(.25, args.poll), args.message_id)
    try:
        text = args.text if args.text is not None else (sys.stdin.read() if args.message_file == "-" else Path(args.message_file).read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise ClientError("message_file_error", str(exc), 2) from exc
    attribution = "[Actor: " + args.actor + ("; on behalf of: " + args.on_behalf_of if args.on_behalf_of else "") + "]"
    prefix = "[fleet-msg from codex-wap1]\n" if args.actor == "codex-wap1" else ""
    text = (prefix + attribution + "\n\n" + text).strip() if text and text.strip() else ""
    if not text or len(text) > 32000 or len(args.scene) > 24 or len(args.asset) > 12:
        raise ClientError("invalid_message", "Require nonempty text, <=32000 characters including attribution, <=24 scenes and <=12 assets.", 2)
    body = {"text": text, "sceneIds": args.scene, "assetIds": args.asset}
    for key, value in (("chapterId", args.chapter), ("entityId", args.entity), ("projectRevision", args.revision)):
        if value is not None:
            body[key] = value
    request_started_at = datetime.now(timezone.utc).isoformat()
    request_started = time.monotonic()
    snapshot = client.request("/api/conversation/messages", body)
    accept_seconds = time.monotonic() - request_started
    users = [item for item in snapshot["conversation"].get("messages", []) if item.get("role") == "user"]
    if not users or (users[-1].get("text") or "").strip() != text:
        raise ClientError("receipt_missing", "Send returned no matching saved message; inspect history before retrying.", outcomeUnknown=True)
    message = users[-1]
    receipt = summary(snapshot) | {"messageId": message["id"], "turnId": message.get("turnId"), "actor": args.actor, "onBehalfOf": args.on_behalf_of, "accepted": True, "acceptedAt": message.get("createdAt"), "requestStartedAt": request_started_at, "httpAcceptSeconds": round(accept_seconds, 6)}
    if args.wait:
        try:
            return receipt | {"completion": wait(client, args.timeout, max(.25, args.poll), message["id"], snapshot)}
        except ClientError as exc:
            exc.payload["sendReceipt"] = receipt
            raise
    return receipt


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result, code = run(args), 0
    except ClientError as exc:
        result, code = exc.payload, exc.exit_code
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif args.command == "measure" and "error" not in result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif "error" in result and result["error"]:
        print(result["error"]["code"] + ": " + result["error"]["message"], file=sys.stderr)
        if result.get("sendReceipt") or result.get("receipt"):
            print(json.dumps(result.get("sendReceipt", result.get("receipt")), ensure_ascii=False), file=sys.stderr)
    else:
        print(f"{result.get('status', '')} · thread {result.get('threadId') or 'not started'} · {result.get('messageCount', 0)} messages")
        if result.get("messageId"):
            print("Saved message: " + result["messageId"])
        for message in result.get("messages", []):
            print("\n" + message.get("role", "?") + " [" + str(message.get("id", "?")) + "]\n" + message.get("text", ""))
        if result.get("completion"):
            print(json.dumps(result["completion"], ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
