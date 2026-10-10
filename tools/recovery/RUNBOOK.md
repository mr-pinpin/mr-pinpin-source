# Firebase recovery operations

This is the Air-to-VPS connection used by the existing `codex` launcher. The
Mini is not involved. Keep the existing VPS SSH server, trusted host keys,
Codex login, `codex-menu`, and persistent session data.

## Installed paths

| Machine | Path | Purpose |
| --- | --- | --- |
| VPS | `/root/.local/share/pinpin-connect/firebase/` | Helper runtime and locked npm dependencies |
| VPS | `/root/.local/share/pinpin-access/firebase/helper.json` | Private pairing key and claim directory configuration |
| VPS | `/root/.local/share/pinpin-access/firebase/claims/` | Durable executed-request IDs |
| VPS | `/root/.local/share/pinpin-connect/client-release.json` | Latest published client source snapshot; no credentials |
| VPS | `/usr/local/bin/pinpin-codex-upgrade` | CLI upgrade and snapshot-download endpoint |
| VPS | `/etc/systemd/system/pinpin-firebase-recovery.service` | Helper supervisor |
| Air | `~/.local/share/pinpin-connect/firebase/versions/<sha>/` | Verified client runtime versions |
| Air | `~/.local/share/pinpin-connect/firebase/current` | Selected client version |
| Air | `~/.config/pinpin-connect/firebase.json` | Private pairing configuration |
| Air | `~/.config/pinpin-connect/recovery-routes.conf` | Existing recovery route policy |
| Air | `~/.config/pinpin-connect/backups/` | Original launchers, route policy and SSH configuration |
| Air | `~/Library/LaunchAgents/io.mr-pinpin.firebase-recovery.plist` | Forwarder supervisor at user login |
| Air | `~/bin/codex`, `~/bin/pinpin-reconnect` | Connection selection and automatic fallback |

All private configs must remain outside Git with mode 0600, inside private
directories. Do not print or copy their contents into reports. The Firebase URL
is in `channel.mjs`; possession of that URL is not recovery authorization. The
pairing key authenticates encrypted relay messages, and SSH separately verifies
both client login and the VPS host key.

## Installing on the existing machines

1. Copy the helper's source modules and `package*.json` into its external runtime
   directory. Run `npm ci --ignore-scripts` there. Use Node 22 or newer.
2. Run `node tools/recovery/setup.mjs /root/.local/share/pinpin-access/firebase`
   on the VPS **only for a new pairing**. It refuses to overwrite existing files.
   Provision the controller configuration privately to the Air as
   `~/.config/pinpin-connect/firebase.json`. The same pairing key must remain on
   both ends. Keep the existing pair during ordinary upgrades.
3. Install `commands/codex-upgrade.py` as executable
   `/usr/local/bin/pinpin-codex-upgrade`. Publish the custom client snapshot from
   the source checkout using the command in [README.md](README.md).
4. Install `services/pinpin-firebase-recovery.service` in the systemd directory,
   then run `systemctl daemon-reload` and
   `systemctl enable --now pinpin-firebase-recovery.service`.
5. Bootstrap a verified snapshot into the Air's external `versions/<sha>`
   directory and install its locked dependencies. Verify the JSON snapshot with
   `commands/client_upgrade.py`'s `verify()` before writing its files. Create the
   `current` symlink to that directory. Back up `~/bin/codex`, then install
   `commands/codex-client.py` there, executable.
6. Substitute the actual home directory in the launchd template. Install it in
   `~/Library/LaunchAgents/`, then bootstrap it with
   `launchctl bootstrap gui/$(id -u) PLIST_PATH`. Allow a previous bootout to
   finish before bootstrapping the same service label again. Its environment
   must contain `PINPIN_CLIENT_CURRENT`, pointing to the stable `current` path.
7. Add the supplied Firebase SSH alias to the existing SSH configuration. Keep
   strict host-key checking and the existing trusted host identity. Do not
   replace the whole SSH config or accept an unexpected key.
8. Test `codex --connection=firebase --check`. Back up the existing route policy
   and reconnect script before adding Firebase immediately after Tailscale.
   Source recipes are in `commands/pinpin-reconnect.sh` and
   `commands/recovery-routes.example.conf`; preserve other configured routes.

This workflow depends on the pre-existing SSH/Codex installation; it is not a
new-machine account/credential installer. Bootstrap and service replacement
must be performed when there are no active Firebase SSH sessions. Routine
`codex upgrade` uses SIGHUP and retains active sockets.

## Checking and troubleshooting

On the Air, run `codex --connection=firebase --check`. Expected output is
`Connection: firebase` followed by `codex-cli VERSION`, and exit status zero.
The command tests real VPS access through the selected route; it does not
silently fall back to Tailscale. Plain `codex` uses automatic route fallback.

The VPS helper can be inspected with:

```sh
systemctl is-active pinpin-firebase-recovery.service
journalctl -u pinpin-firebase-recovery.service -n 20 --no-pager
```

On the Air, inspect `launchctl print gui/$(id -u)/io.mr-pinpin.firebase-recovery`
and `~/.config/pinpin-connect/firebase.log`. Check whether loopback port 22222
is listening before investigating SSH itself. Retain the SSH host-key check if
connection errors occur. `loaded-version` in the client runtime records the
version selected by the most recently started listener.

Use `codex upgrade` to update the published custom client and the latest stable
VPS CLI. Explicit Firebase selection works for upgrade too. Pairing configs,
route policy, login keys and active Codex processes are retained. A failed
upgrade leaves its error visible; inspect it before retrying. Publication of a
custom snapshot is a separate operator step, not a repository `git pull`.

## Rollback and stopping

Restore the launcher from `~/.config/pinpin-connect/backups/` if necessary. For a
transport rollback, select the previous retained version by atomically replacing
`current`, restore its `codex-client.py` as `~/bin/codex`, and send SIGHUP with
`launchctl kill SIGHUP gui/$(id -u)/io.mr-pinpin.firebase-recovery`. Preserve the
pairing key and claim files. Never clear replay claims while keeping the same
key. CLI package rollback is a separate npm version selection; it does not
require deleting sessions or changing the project's Git history.

To stop the fallback, remove only its route from the policy, boot out the Air
agent, and stop/disable the VPS helper service. Retain Tailscale and the other
existing routes. Stopping or forcibly restarting a transport closes its active
SSH connections; persistent VPS Codex sessions remain available for reattachment.

The live database rules were not changed. Public database access can still
allow disruption or quota consumption; encryption rejects forged recovery
commands but cannot prevent deletion of relay messages.
