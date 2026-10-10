# Independent Firebase SSH fallback

The existing Air reconnect command reaches the persistent Codex workspace on the
VPS. This transport adds Firebase as an independent route to that same SSH
server. Tailscale remains first; Firebase is the next alternative. Existing
public/REALITY recovery routes are retained.

The VPS helper connects only to its local SSH server. The Air forwarder listens
only on loopback and carries SSH bytes through Firebase Realtime Database SDK
WebSocket events. The SSH client keeps its existing login keys and verifies the
same VPS host key. No Firebase login is required by the current database; a
private pairing key authenticates and encrypts the relay messages. Firebase
Auth remains optional for databases that require it.

A failed SSH session must reconnect; this cannot migrate an established TCP
session between routes. The existing persistent remote workspace can then be
reattached. Firebase needs ordinary internet access at both ends.

## Operation

Runtime is installed under the existing `pinpin-connect/firebase` directory on
each machine, outside this checkout. Pairing secrets and replay claims stay in
private configuration directories, never Git or Firebase. The helper is
supervised independently of the Codex session. The Air's normal `codex` wrapper
continues to use `pinpin-reconnect`.

A manual check on the Air selects Firebase explicitly:

```sh
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes hostinger-vps-firebase hostname
```

The VPS helper runs as `pinpin-firebase-recovery.service`; the Air forwarder
runs as the login agent `io.mr-pinpin.firebase-recovery`. Both restart on failure.
Service recipes are retained in `services/`; substitute the actual home directory for `__HOME__` in the launchd template.
The installed forward uses `127.0.0.1:22222`; its SSH alias uses
`HostKeyAlias 100.109.138.51`, matching the existing trusted VPS key. The existing
route policy inserts `primary hostinger-vps-firebase` immediately after
`primary hostinger-vps`, retaining the other routes.

The installation, rollback and troubleshooting steps are in [RUNBOOK.md](RUNBOOK.md).
The dated deployed state is recorded in [the runtime report](../../workflows/firebase-recovery.md).

## Source and setup

Node 22+; install dependencies with `npm ci --prefix tools/recovery`.
`node tools/recovery/setup.mjs /private/config-directory` creates two private
configurations with one random pairing key. It refuses to overwrite files and
does not print the key. Provision `controller.json` privately to the client.
Run:

```sh
node tools/recovery/cli.mjs helper /private/config-directory/helper.json
node tools/recovery/cli.mjs forward /private/controller.json
node tools/recovery/cli.mjs request /private/controller.json ping
```

The forwarder defaults to Firebase-only, suitable for the fallback SSH alias.
Optionally set `primaryHost`, `primaryPort` and `connectTimeoutMs` to have this
forwarder try a direct TCP connection first. A working primary route does not
initialize or depend on Firebase.

The helper configuration has `sshPort` (22 by default), `stateDir` for durable
control-request claims, and optional fixed local `actions`. The remote peer
cannot change SSH destination, command arguments, environment or working
directory. At most four SSH tunnels run concurrently. Output for fixed repair
actions is not returned; use SSH for interactive repair.

## Transport behavior

AES-256-GCM binds pair, direction, sequence/ID and expiry. Control requests are
claimed durably before execution and never automatically retried. A timeout
means the outcome may be unknown. Do not delete claim files while the same
pairing key is active. Keep machine clocks synchronized.

Binary packets use 12 KB chunks, ordered delivery, acknowledgements and stream
backpressure. A missing acknowledgement times out after 20 seconds, closing the
affected tunnel rather than replaying stale bytes. Delivered packets and ACKs
are removed. A crashed peer can leave encrypted, expired records; administrative
expiry cleanup can remove those. This channel is for recovery SSH traffic,
not production media transfers.

Database access rules have not been changed. Encryption protects message
contents and rejects forged messages, while existing public access can still
permit deletion/disruption of the relay or consumption of database quota.

## Validation

`npm test --prefix tools/recovery` tests ciphertext tampering, direction binding,
expiry, durable replay rejection, request timeouts, binary tunneling with the
primary unavailable, and the primary continuing to work with Firebase offline.

A live isolated test against the supplied database used two real WebSocket
clients and anonymous database access. It verified encrypted ping and 48 KB
binary round trips with the primary deliberately unavailable. Warm ping round
trips were about 433 ms from this VPS; this is a measured recovery route, not a
claim of local-network latency. Temporary test messages were cleaned up.

References: [SDK events](https://firebase.google.com/docs/database/web/read-and-write),
[WebSocket transport](https://firebase.google.com/docs/reference/js/database#forcewebsockets),
[connection behavior](https://firebase.google.com/docs/database/web/offline-capabilities).

The live Air→Firebase→VPS SSH check returned `srv2044532` and confirmed the
Codex menu entrypoint exists, using the existing SSH key and strict host-key
verification. The reconnect wrapper was also tested with an intentionally
unavailable first route followed by Firebase. Automatic startup after a full
reboot has not been exercised; launchd starts the client at user login.

## Codex connection and upgrade commands

On the Air:

```sh
codex                                 # automatic fallback
codex --connection=firebase           # Firebase only
codex --connection=tailscale          # Tailscale only
codex --connection=firebase --check   # verify access and report CLI version
codex upgrade                        # upgrade custom client and VPS CLI
codex --connection=firebase upgrade   # upgrade both through Firebase
```

`--connection firebase` and `--connection:firebase` are accepted too. A forced
connection does not silently select another route. Existing `--list`, `--new`
and `--resume UUID` menu options remain available.

Upgrade completes the VPS work before changing the local client. It resolves
the latest stable Codex CLI from the official npm registry, installs that exact
version, and verifies it. This follows [OpenAI's CLI update instructions](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex).
Running Codex processes retain their current version; new processes use the
updated installation.

The custom client downloads the latest published source snapshot from the VPS
through authenticated SSH, verifies its SHA-256 manifest and exact filenames,
installs locked dependencies into a version directory, and atomically changes
its `current` pointer and launcher. It preserves pairing secrets, route policy
and SSH keys. A SIGHUP reload switches the forwarder's listener to the updated
transport while retaining established SSH sockets. Previous versions and
launcher backups remain available. Upgrades are locked to prevent concurrent
installers.

Source recipes live in `commands/`. Publish an updated, credential-free custom
client snapshot on the VPS with:

```sh
python3 -B tools/recovery/commands/publish_client.py /root/.local/share/pinpin-connect/client-release.json
```

`codex upgrade` consumes that published snapshot; it does not change the
repository's branches or working files. The VPS upgrade endpoint is installed
from `commands/codex-upgrade.py` as `/usr/local/bin/pinpin-codex-upgrade`.
Test the command parser and manifest checks with:

```sh
python3 -B -m unittest discover -s tools/recovery/commands -p 'test_*.py'
```

The existing source CI runs `npm run verify`, which now includes
`npm run test:recovery` alongside asset checks and the production build check.
No workflow-file edit is required.
