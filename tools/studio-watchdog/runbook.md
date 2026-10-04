# Watchdog operations

Run from this directory:

```sh
./stavka-sprint watchdog status --config watchdog-config.json
./stavka-sprint watchdog test --config watchdog-config.json
python3 test_watchdog.py
./stavka-sprint watchdog stop --config watchdog-config.json
./stavka-sprint watchdog start --config watchdog-config.json
```

Read checkpoint.json and ticks.jsonl for APP progress, exact observation time and decisions. Status includes schedulerSessionExists; session existence alone is not progress proof. Check latest tick age (expected<=330s), activeTurnId, cursor, deadline and budget. If stale, coordinator inspects; never resend a claimed action. Lock prevents concurrent run/tick processes. No scheduler revival of ROOT is claimed.

Automatic queue mode requires explicit coordinator plan/ownership handoff. Stop CLI scheduler, review queued-action.json and checkpoint spent/reserved, set config mode to coordinator-queue, restart through CLI. Do not arm during simultaneous root dispatch. Approval before full production and $25 cumulative additional video/API cap remain mandatory. No story publication. Missing/invalid cost, unknown status, stale cursor, wrong thread, existing claim and deadline refuse. Claim precedes send; uncertain delivery holds reservation and never retries. Manual reconciliation is coordinator-only. Deadline does not cancel in-flight app work.

Mount must be real /Volumes/TB4; scheduler refuses to start absent mount. Runtime survives current-login disconnect; automatic reboot startup is not verified and no new launchd/TCC workaround is attempted. Stop only the watchdog through CLI; leave Studio/replica workers untouched.

CLI ownership handoff: `watchdog arm --config CONFIG --action-file FILE` validates current approved thread, cursor and budget before writing the single action and enabling coordinator-queue mode. Stop/restart through CLI to reload. Return ownership with `watchdog stop`, `watchdog disarm`, `watchdog start`; disarm preserves claims and receipts. Status reports configuredMode, dispatchOwnership, heartbeatAgeSeconds, observationFailed, latest APP status/cursor and exact accepted message identity. APP-only observation cannot revive ROOT or detect model-goal progress independently. Runtime/source files and metadata stay private unless sanitized in the narrow handoff.
