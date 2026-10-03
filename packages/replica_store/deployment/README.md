# Generic host workers on Mini

The deployed uploader and optional HF poller run the generic library CLI through `worker-host.py` in two windows of the existing authorized Mini tmux runtime. They never restart Studio. The independent poller uses the production namespace and a separate bounded2GiB root; uploader polling may remain off.

The wrapper verifies the mounted external volume and configured VolumeUUID before worker/log writes, pins library source hashes, uses TB4 HF_XET_CACHE/HF_HUB_CACHE while retaining standard auth lookup, and rotates three256KiB status-only logs. Interval15s, worker timeout180s, Xet chunk/shard cache limits64MiB each. Explicit tiny atomic home heartbeats report stage/PID/time only. Fill `host-config.example.json` with reviewed absolute paths. All storage, transfer caches and logs remain on the external disk.

Use the existing authorized Mini terminal/tmux runtime to start both windows:

```sh
tmux new-session -d -s replica-store-host -n uploader '/opt/homebrew/bin/python3 -B ~/bin/replica-store-worker-host.py --host-config ~/.config/replica-store/host-config.json'
tmux new-window -d -t replica-store-host -n poller '/opt/homebrew/bin/python3 -B ~/bin/replica-store-worker-host.py --host-config ~/.config/replica-store/poller-host-config.json'
```

Inspect the uploader/poller heartbeat files in ~/.config/replica-store, library status/receipts, and bounded TB4 logs. Stop only these jobs with `tmux kill-session -t replica-store-host`. Queued owned bytes, receipts and remote objects remain intact. Restart the same two commands in an authorized runtime; do not call backups manually.

## Login/reboot limitation

Direct Python LaunchAgents blocked opening TB4 config despite a valid mount guard. A fresh launchd-created dedicated tmux server also blocked on its public fixture read. Therefore connecting to the already authorized tmux server proves current-login operation and SSH-disconnect persistence, not login/reboot recovery. The two attempted LaunchAgent labels are disabled to avoid later duplicates; no TCC database, SSH keys, sandbox policy or protection was changed. Automatic login restart requires an authorized OS execution/volume-consent path; no reboot-capable deployment is claimed here. Library outbox durability and live automatic HF polling are verified independently of this limitation.
