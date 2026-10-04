# Studio watchdog

Reusable, bounded host supervision for the existing Studio conversation. The coordinator owns the active mission goal, acceptance decisions and full-production approval. This watcher monitors APP via the supported Studio client CLI; it does not revive ROOT. [Observed proof](observed-proof.json) records a natural five-minute interval and one exclusively delegated submission. [CLI adapter integration](cli-integration.md) explains the Mission Control boundary and provenance; [runbook](runbook.md) describes lifecycle and ownership handoff.

The default example is read-only. Configure the existing CLI binary, Studio client, approved thread and deadline before use. No live configuration, private queue, prompt/history, copied CLI dependency tree or binary is included here. Mount and current-login runtime requirements remain explicit. Reboot startup is not verified.

Portable tests from repository root (synthetic fixtures, no network/dispatch):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/studio-watchdog/test_watchdog.py
```

Production CLI integration adds the narrow `watchdog.go` adapter to the canonical Mission Control CLI, registers its command and installs sibling `watchdog.py`. Do not run standalone adapter Go source as a separate server. The existing Studio client provides status and send; no direct Herdr or private fleet stores are used. Automatic mode requires exclusive coordinator ownership and a single approved progress-bound action. Exact acceptance, claim-before-send, nonfinite-money rejection and durable observation failures are covered by regression tests. Deadline stops new submissions without cancelling active app work. Paid work remains blocked unless explicitly authorized and reserved within the cumulative $25 cap; no publication is permitted.
