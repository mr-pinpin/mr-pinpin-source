# Firebase recovery deployment — 2026-10-10

The Air's custom `codex` client now reaches the persistent VPS workspace through
Tailscale first, Firebase second, followed by its retained public/REALITY routes.
The Firebase route is independent of Tailscale and uses ordinary outbound
WebSocket connections on both machines. No Firebase Auth login is configured;
private pairing encryption and the existing SSH authentication protect access.

Source and operating instructions: [tools/recovery/README.md](../tools/recovery/README.md)
and [RUNBOOK.md](../tools/recovery/RUNBOOK.md). Source pushes perform verification;
this deployment does not select or alter an official book release.

## Recorded deployed state

- VPS helper: `pinpin-firebase-recovery.service`, active under systemd.
- Air forwarder: `io.mr-pinpin.firebase-recovery`, active under launchd at login.
- Air loopback SSH forward: port 22222; trusted host identity retained.
- Published custom client snapshot: `b1c9d57e734c55ebd5c207fd6ca855afa7d2ece74f085824e72a96c48bcfd62d`.
- VPS CLI: upgraded from `0.161.0` to `0.162.1` during this deployment.
- Existing `codex` wrapper routes through `pinpin-reconnect`; forced selection
  accepts `--connection=firebase`, `--connection firebase` and
  `--connection:firebase`. Tailscale and automatic selection are supported.
- `codex upgrade` updates both the published custom client and the VPS CLI.
  Repeating it successfully reported both already current.

## Evidence

Six transport tests and five command/manifest tests passed. Live tests verified
real Air→Firebase→VPS SSH access with the existing key and strict host checking;
the Codex entrypoint was present. An intentionally unavailable first route
caused the existing reconnect wrapper to select Firebase successfully.

Both forced Firebase and forced Tailscale checks reported `codex-cli 0.162.1`.
A held Firebase SSH connection survived SIGHUP transport reload while a new
connection used the updated listener. The loaded-version marker matched the
selected client version. Pairing configs and route settings were retained.

An isolated database test also verified encrypted ping and 48 KB binary round
trips. Warm ping round trips were about 433 ms from the VPS. These are measured
recovery-channel results, not a local-network latency claim.

Full reboot startup has not been exercised. Active TCP sessions cannot migrate
between routes; reconnecting reattaches to the persistent VPS workspace. Public
database rules remain unchanged, so deletion/disruption and quota consumption
remain possible despite authenticated encryption.
