# Connection infrastructure moved

The single maintained Codex/Firebase/Tailscale connection implementation lives
in [mr-pinpin/infrastructure](https://github.com/mr-pinpin/infrastructure/tree/main/tools/firebase-ssh-relay).

Use that repository for the relay, Mac/VPS launchers, connection flags, upgrades,
service recipes, tests and operating documentation. This repository contains no
executable recovery implementation. Earlier source remains in Git history.

The [consolidation record](https://github.com/mr-pinpin/infrastructure/blob/main/docs/firebase-relay-consolidation.md)
compares the temporary proof and persistent deployment and records retained
features. The [runbook](https://github.com/mr-pinpin/infrastructure/blob/main/tools/firebase-ssh-relay/RUNBOOK.md)
covers the unified installation, checks and rollback.
