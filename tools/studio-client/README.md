# Shared Studio conversation client

Humans, Claude and Codex can use the same saved Studio conversation from their
existing terminal. The browser sees the same messages and responses. This client
does not launch an agent, open another thread, or run a server.

Python 3.9+; standard library only. Run from the source checkout on the Mini:

    python3 tools/studio-client/chat.py status --json
    python3 tools/studio-client/chat.py read --limit 3
    python3 tools/studio-client/chat.py send --actor codex-wap1 --on-behalf-of Miguel --message-file /path/feedback.txt --json
    python3 tools/studio-client/chat.py wait --message-id USER_MESSAGE_ID --timeout 300 --json

The default URL is http://127.0.0.1:18826. Set PINPIN_STUDIO_URL or add
--url to any subcommand; use the existing forwarded port when running elsewhere.
No credentials are embedded in this client. Actor names are **provenance labels,
not authentication**. A proxy should use --on-behalf-of only when actually
delegated by that person.

Every send requires --actor and either --text or --message-file (UTF-8; "-" means
stdin). The stored message visibly begins with:

    [fleet-msg from codex-wap1]
    [Actor: codex-wap1; on behalf of: Miguel]

The message follows after a blank line; final outer whitespace is normalized to
match Studio’s saved text. Actor codex-wap1 also receives its required fleet
message prefix. This uses the current API rather
than inventing an unsupported actor field. It adds no approval or publication
authority. Context options --chapter, repeatable --scene, --entity, repeatable
--asset and --revision map directly to Studio's existing selection fields.
Do not rely on whatever another person's browser currently has selected.

send returns accepted, messageId, threadId, turnId (initially null), cursor and
status. Accepted means saved for processing, not completed. Add --wait to wait
for that receipt, or call wait later with its messageId. An unqualified wait
observes the currently active turn. A completed commentary message does not
finish a wait while the turn remains active. If another user starts a later turn,
the client only claims prior completion when its final response is recorded;
otherwise it asks you to inspect history.

read returns the newest 20 messages by default; --limit 0 explicitly requests all.
Events are omitted unless you explicitly pass --after CURSOR. That cursor filters
events only, not the accumulated messages. status emits counts and identifiers,
never the transcript. --json emits one JSON result; parse the exit status too.
Argument syntax errors use argparse's normal stderr help.

Timeouts and concurrent users:

- --request-timeout defaults to 15 seconds per HTTP request.
- wait/--wait --timeout defaults to 300 seconds total; --poll defaults to 1 second
  and is clamped to at least 0.25 seconds. A timeout does not stop Studio.
- Exit 0: success; 1: HTTP/transport/turn failure; 2: invalid input or missing
  message; 3: busy (409); 4: wait timeout.
- POST is never retried automatically. If a response is lost, outcomeUnknown is
  true: read the conversation before deciding whether to resend.
- A busy response never queues or silently duplicates the prompt. Read/wait,
  review the intervening response, then decide what to send.
- send --wait errors retain sendReceipt so you can resume waiting without
  resending. This is particularly useful from a Mission Control lane.

Use Mission Control's normal CLI to operate fleet lanes and hand off bounded work.
An existing Herdr terminal can run these commands directly; the Studio client
itself has no Herdr dependency and does not bypass Mission Control fleet routing.

Interface precedent: the existing
[Mission Control repository](https://github.com/the-gazeteer/mission-control)
and installed Stavka CLI use attributed sends, JSON receipts and bounded waits.
This is a fresh stdlib implementation of those interface patterns; no third-party
implementation code was copied.

Tests use only an isolated local HTTP fixture:

    python3 -m unittest discover -s tools/studio-client/tests -v

Creative workflow definitions and examples: [workflows](../../workflows/README.md).
