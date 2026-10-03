"""Read-only lifecycle measurements from Studio's existing timestamped events."""
from datetime import datetime, timezone
import json
from pathlib import Path
import time

FIELDS = ("seq", "type", "createdAt", "messageId", "kind", "status")


def timestamp(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return None


def elapsed(start, end):
    a, b = timestamp(start), timestamp(end)
    return round(b - a, 6) if a is not None and b is not None and b >= a else None


def ingest(capture, snapshot, observed_at):
    conversation = snapshot["conversation"]
    capture["conversation"] = {key: conversation.get(key) for key in ("threadId", "status", "activeTurnId")}
    capture["messages"] = [{key: item.get(key) for key in ("id", "role", "turnId", "createdAt", "status", "phase")}
                           for item in conversation.get("messages", [])]
    events = snapshot.get("events", [])
    previous = capture.get("cursor", 0)
    if previous and events and events[0].get("seq", 0) > previous + 1:
        capture["eventGap"] = True
    captured = capture.setdefault("events", [])
    delta_ids = {item.get("messageId") for item in captured if item["type"] == "delta"}
    seen = {item["seq"] for item in captured}
    for event in events:
        seq = event.get("seq")
        if seq in seen:
            continue
        if event.get("type") == "delta":
            if event.get("messageId") in delta_ids:
                continue
            delta_ids.add(event.get("messageId"))
        if event.get("type") not in ("delta", "message", "activity", "status"):
            continue
        captured.append({key: event[key] for key in FIELDS if key in event})
    capture["cursor"] = snapshot.get("cursor", previous)
    capture["observedAt"] = observed_at
    if len(captured) > 10000:
        capture["eventGap"] = True
        capture["events"] = captured[-10000:]


def metrics(capture):
    messages = capture.get("messages", [])
    target = next((m for m in messages if m["id"] == capture["messageId"] and m["role"] == "user"), None)
    if not target:
        raise ValueError("Saved user message ID not found in this conversation.")
    started = target.get("createdAt")
    turn = target.get("turnId")
    following = next((m for m in messages[messages.index(target) + 1:] if m["role"] == "user"), None)
    start, end = timestamp(started), timestamp(following.get("createdAt")) if following else None
    events = sorted((event for event in capture.get("events", []) if timestamp(event.get("createdAt")) is not None
                     and start is not None and timestamp(event["createdAt"]) >= start
                     and (end is None or timestamp(event["createdAt"]) < end)), key=lambda e:e["seq"])
    replies = [m for m in messages if turn and m["role"] == "assistant" and m.get("turnId") == turn]
    reply_ids = {m["id"] for m in replies}
    finals = {m["id"] for m in replies if m.get("phase") == "final_answer" and m.get("status") == "completed"}
    first_progress = next((e["createdAt"] for e in events if e["type"] == "activity" or
                           e["type"] == "delta" and e.get("messageId") in reply_ids or
                           e["type"] == "status" and e.get("status") == "running"), None)
    first_text = next((e["createdAt"] for e in events if e["type"] == "delta" and e.get("messageId") in reply_ids), None)
    if first_text is None and replies:
        first_text = min((m["createdAt"] for m in replies if m.get("createdAt")), default=None)
    final_event = next((e for e in reversed(events) if e["type"] == "message" and e.get("messageId") in finals), None)
    complete = next((e for e in events if e["type"] == "status" and e.get("status") in ("completed", "error", "interrupted")), None)
    coverage = any(e["type"] == "message" and e.get("messageId") == target["id"] for e in events) and not capture.get("eventGap")
    spans, pending = [], []
    active_periods, busy_start, active_count, balanced = [], None, 0, True
    ambiguous = False
    image_events = [e for e in events if e["type"] == "activity" and e.get("kind") == "imageGeneration"]
    for event in image_events:
        if event.get("status") == "running":
            if active_count == 0:
                busy_start = event["createdAt"]
            active_count += 1
            pending.append(event)
            if len(pending) > 1:
                ambiguous = True
        elif event.get("status") in ("completed", "failed", "interrupted", "error"):
            if active_count <= 0:
                balanced = False
            else:
                active_count -= 1
                if active_count == 0:
                    active_periods.append({"startedAt": busy_start, "endedAt": event["createdAt"], "seconds": elapsed(busy_start, event["createdAt"])})
            if len(pending) == 1 and not ambiguous:
                beginning = pending.pop()
                spans.append({"startedAt": beginning["createdAt"], "endedAt": event["createdAt"],
                              "seconds": elapsed(beginning["createdAt"], event["createdAt"]),
                              "status": event["status"], "startEvent": beginning["seq"], "endEvent": event["seq"]})
            elif pending:
                pending.pop(0)
            else:
                ambiguous = True
    image_seconds = round(sum(s["seconds"] for s in spans), 6) if image_events and not ambiguous and not pending and coverage else None
    active_wall = round(sum(p["seconds"] for p in active_periods), 6) if image_events and coverage and balanced and active_count == 0 else None
    total = elapsed(started, complete["createdAt"]) if complete else None
    outcome = complete.get("status") if complete else None
    return {"messageId": target["id"], "turnId": turn, "threadId": capture["conversation"].get("threadId"),
            "acceptedAt": started, "observedAt": capture.get("observedAt"), "cursor": capture.get("cursor"),
            "eventCoverage": "complete" if coverage else "partial",
            "firstVisibleProgressAt": first_progress, "firstVisibleProgressSeconds": elapsed(started, first_progress),
            "firstAssistantTextAt": first_text, "firstAssistantTextSeconds": elapsed(started, first_text),
            "finalMessageIds": sorted(finals), "finalDeliveredAt": final_event.get("createdAt") if final_event else None,
            "finalDeliveredSeconds": elapsed(started, final_event["createdAt"]) if final_event else None,
            "completedAt": complete.get("createdAt") if complete else None, "totalSeconds": total, "outcome": outcome,
            "imageGeneration": {"spans": spans, "totalSeconds": image_seconds, "activeWallSeconds": active_wall, "activePeriods": active_periods, "ambiguous": ambiguous,
                                "inFlight": len(pending), "exposedEvents": len(image_events)},
            "otherElapsedSeconds": round(total - active_wall, 6) if total is not None and active_wall is not None else None,
            "notes": ["Times are server/API observations, not browser paint or model-internal timing.",
                      "Other elapsed includes reasoning, tools, registration and delivery; it is not pure orchestration overhead.",
                      "Image events have no call IDs; overlapping/unmatched events cannot be assigned per-call durations. Active wall time unions balanced concurrent event intervals.",
                      "Original HTTP acceptance latency is available only in a measured send receipt."]}


def measure(client, args, error_type):
    path = Path(args.capture_file) if args.capture_file else None
    try:
        capture = json.loads(path.read_text()) if path and path.exists() else {"messageId": args.message_id, "url": client.url, "events": []}
    except (OSError, ValueError) as exc:
        raise error_type("capture_error", str(exc), 2) from exc
    if capture.get("messageId") != args.message_id or capture.get("url") != client.url:
        raise error_type("capture_mismatch", "Capture belongs to another URL/message; choose its original ID or a new capture file.", 2)
    deadline = time.monotonic() + args.timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise error_type("wait_timeout", "Measurement stopped; resume with the same message ID and capture file.", 4, measurement=metrics(capture))
        snapshot = client.get(capture.get("cursor", 0), timeout=min(client.timeout, remaining))
        ingest(capture, snapshot, datetime.now(timezone.utc).isoformat())
        try:
            result = metrics(capture)
        except ValueError as exc:
            raise error_type("message_not_found", str(exc), 2) from exc
        if path:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_name(path.name + ".tmp")
                temporary.write_text(json.dumps(capture, ensure_ascii=False, indent=2))
                temporary.replace(path)
            except OSError as exc:
                raise error_type("capture_error", str(exc), 1, measurement=result) from exc
        if result["outcome"] or args.once:
            return result
        # If history is incomplete but the target is no longer active, don't wait forever.
        users = [m for m in capture["messages"] if m["role"] == "user"]
        if users[-1]["id"] != args.message_id or capture["conversation"]["status"] not in ("connecting", "running", "interrupting"):
            result["measurementIncomplete"] = True
            return result
        time.sleep(min(max(.25, args.poll), max(0, deadline - time.monotonic())))
