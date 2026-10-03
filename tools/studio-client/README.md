# Shared Studio conversation client

Humans, Claude and Codex can use the same saved Studio conversation from their
existing terminal. The browser sees the same messages and responses. This client
does not launch an agent, open another thread, or run a server.

The chat client requires Python 3.9+ and uses only the standard library. Run from the source checkout on the Mini:

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

## Measure a turn without sending it again

    python3 tools/studio-client/chat.py measure --message-id SAVED_MESSAGE_ID --capture-file /path/turn-timing.json --timeout 900 --json
    python3 tools/studio-client/chat.py measure --message-id SAVED_MESSAGE_ID --capture-file /path/turn-timing.json --once --json

Start capture promptly: Studio retains only the last 1000 events. A capture file
stores compact timestamps and message identifiers, not prompts or transcript text.
Resume with the same URL, message ID and file. Do not run two writers against one
capture file. --once reports immediately; timeout returns the saved measurement
and can be resumed. These commands only GET the existing conversation.

Measures API acceptance timestamp, first visible running/tool/text event, first
assistant text, final-message delivery and completion. These are server observations,
not browser paint timestamps. Future send receipts also include actual
httpAcceptSeconds and requestStartedAt; HTTP latency cannot be reconstructed for
older sends. Client observation time is reported separately.

Image-generation activity is measured only when matching events are exposed.
Sequential pairs have timestamped spans; overlapping events without call IDs have
no fabricated per-image duration. With complete coverage and balanced events,
activeWallSeconds reports the union of concurrent image-tool intervals.
otherElapsedSeconds is total time minus that union: it includes reasoning,
other tools, registration and delivery, so it is not pure orchestration overhead.
Missing events and incomplete intervals remain partial/null rather than estimates.
Measurement success is distinct from turn success; inspect outcome.

## Register a native image in one command

This helper requires Studio's Python environment (Pillow), unlike the stdlib chat
client. It uses a verified frozen Store implementation, not a new service:

    /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-venv/bin/python -B tools/studio-client/register-image.py --runtime-dir /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime --native-path /absolute/native-image.png --prompt-file /absolute/exact-prompt.txt --reference REGISTERED_ASSET_ID --output-name character-solo.png

Repeat --reference for each actual input image (maximum12). The caller must supply
the exact generation prompt and real references; --tool defaults to the caller's
assertion image_gen.imagegen. The helper does not infer provenance from pixels.

--runtime-dir reads current-deployment.json for the frozen kernel and data path.
--data-dir can override the data destination explicitly. Alternatively use
--kernel-root /path/to/frozen-release with --data-dir /path/to/existing-data.
No immutable release or runtime manifest is modified.

Before copying, the helper validates the frozen bundle, registered references,
prompt and native image. It copies exact bytes into data/generated using a hash
prefix, verifies the copy, and calls Store.import_asset with prompt, hashes,
native source path, tool and reference provenance. It never resizes, approves,
selects, publishes, or edits the project. Identical bytes with matching unreviewed
provenance reuse the candidate; conflicting provenance/review status or output
bytes fail without overwriting them.

The JSON receipt contains assetId, sha256, candidate review status, copy path,
actual registration timing and a ready WorkflowCard with actions:[].
Place workflowCard JSON inside an assistant ui fence to display the finished
candidate. This is presentation, not an extra approval checkpoint.
Generation timing belongs to the turn measurement, not this registration receipt.

Run all tests (including real frozen Store fixtures) with the Studio environment:

    /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-venv/bin/python -B -m unittest discover -s tools/studio-client/tests -v

## Prepare once; register and record the package together

The coordinator prepares an exact command manifest once (and refreshes it whenever
the helper changes):

    /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-venv/bin/python -B tools/studio-client/register-image.py --runtime-dir /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime --setup-toolchain

This writes data/workflows/toolchain.json atomically with schemaVersion:1,
toolName:studio-register-image, helperSha256, parameter/input/output contracts and
argvPrefix containing the absolute Studio interpreter, helper and runtime paths.
The interpreter path preserves its virtual-environment identity. There are no
credentials or shell strings. Studio can hydrate this validated metadata before
generation; use the argv array without repeated path discovery.

Add --entity papa --stage solo (or --stage interactions) to the normal registration
command to also persist its actual receipt/provenance in
data/reports/character-packages/papa.json. Both options must be supplied together.
The entity must already exist in Studio; identifiers must be safe filenames.

The schema is {schemaVersion:1, entityId, updatedAt, stages:{STAGE:{candidates:[]}}}.
Each candidate records the registration receipt, WorkflowCard and exact asset
provenance. Writes use the Store lock and atomic JSON replacement. Prior stages,
candidates and extra metadata are preserved; repeating the same asset/stage does
not duplicate it. An incompatible existing dossier is preserved and rejected
before image copying. No project, approval or selected-reference changes occur.

Setup changes only tooling metadata; it does not generate or register artwork.
Registration without --entity/--stage keeps the original single-candidate behavior.
