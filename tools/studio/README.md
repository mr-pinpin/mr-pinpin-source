# Story Studio

The primary workspace pairs a persistent Codex conversation with the current
chapter: Board, Read, References, Spaces, and Insights. Select a panel or
reference to include it in your next message, attach images, edit a draft plan,
or export real PNG contact sheets. Plan approval records the exact preproduction
version; image approval and publication remain separate. The previous full
editor remains available at `/legacy.html`.

Read [CONVERSATION.md](CONVERSATION.md) for the conversation, preproduction,
media, and evidence contracts. [API.md](API.md) documents project and asset
operations. Conversation uses the local Codex login and reports connection or
execution failures without inventing an answer.

## Conversation preview

The isolated preview uses external data at
`/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-conversation-data`.
Mini URL: `http://127.0.0.1:18826/`; Air forward:
`http://127.0.0.1:18825/`. It preserves the existing service and its data.
Check the running session and forward before starting either again.

From the checkout on the Mini, after configuring the Python environment below:

```sh
~/bin/tmux new-session -d -s pinpin-studio-conversation 'cd /Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source && exec /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-venv/bin/python tools/studio/server.py --data-dir /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-conversation-data --media-root /Volumes/TB4/mac-mini-storage/shared --port 18826 >> /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-conversation-data/server.log 2>&1'
curl --fail http://127.0.0.1:18826/api/state
```

If the Air forward is absent:

```sh
ssh -N -L 18825:127.0.0.1:18826 mini
```

Keep the existing project when restarting; do not reseed it. The preview may
contain a newer draft chapter than the existing service; neither selects an
official published release.

## Existing service and environment

The instructions below describe the original Mini service on **18806**, its
Air forward on **18805**, and its existing external data directory. These are
retained independently of the conversation preview.

The local Studio stores projects, native assets, reference bindings, review history and agent jobs outside Git. It never publishes a chapter automatically.

Run on the Mac mini. System Python needs Pillow; create a dedicated environment on the SSD once:

```sh
python3 -m venv /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-venv
/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-venv/bin/pip install -r tools/studio/requirements.txt
```

From a checkout, launch persistently (replace `/PATH/TO/CHECKOUT` with its absolute path):

```sh
~/bin/tmux new-session -d -s pinpin-studio 'cd /PATH/TO/CHECKOUT && exec /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-venv/bin/python tools/studio/server.py --data-dir /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-data --media-root /Volumes/TB4/mac-mini-storage/shared --port 18806 >> /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-data/server.log 2>&1'
curl --fail http://127.0.0.1:18806/api/state
```

For foreground diagnostics instead:

```sh
python tools/studio/server.py --data-dir /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-data --media-root /Volumes/TB4/mac-mini-storage/shared --port 18806
```

Use a persistent tmux session for normal operation. The current session is `pinpin-studio`; its log is in the external data directory. The Air preview uses the existing SSH forward at `http://127.0.0.1:18805/`. Restarting preserves the project. Do not replace or reseed an existing project merely to restart the server.

If the Air forward is absent, run `ssh -N -L 18805:127.0.0.1:18806 mini` on the Air, then open that preview URL. Check existing sessions/forwards before launching duplicates. The currently running service may use an existing production Python environment; future independent installs can use the dedicated environment above.

Read [API.md](API.md) for the wire contract. Generation jobs wait for an active agent with the appropriate tool; the server does not pretend to render images itself.

An agent starts with `cli.py --data-dir DATA inbox`, then claims a job with `claim JOB --agent NAME`. Complete an image using `complete JOB --agent NAME --image NATIVE --scene-id SCENE --prompt-file ACTUAL_PROMPT --references-file ACTUAL_REFERENCES --tool TOOL`. Use `--used-job-prompt` or `--used-job-references` only when those inputs were actually submitted unchanged. Missing actual-input provenance is recorded as unknown. Text planning jobs accept `--text-file`. Completion creates a review candidate, not an approved scene. Reply to durable feedback with `reply JOB_OR_BOARD --agent NAME --feedback-id ID --text TEXT`.

Project-only snapshots are preserved in `history/` with hashes. `GET /api/history` lists revisions; `GET /api/history/N` retrieves one. The CLI supports `history` and `export-project --output FILE --revision N`. Restore deliberately by saving the recovered project with the current expected revision; do not overwrite runtime state files.

Run isolated backend tests with `python -m unittest discover -s tools/studio/tests -v`. Test data must be separate from the live external data directory.

For the immutable conversation shell, hot-loaded workspace, release freezing, restoration and stable-core migrations, read [STABLE-RUNTIME.md](STABLE-RUNTIME.md). The evolving workspace is the only UI source directory made writable to the live agent; it does not require restarting the stable service.
