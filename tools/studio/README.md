# Story Studio

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
