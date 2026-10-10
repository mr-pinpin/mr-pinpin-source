#!/usr/bin/python3
"""Upgrade the VPS's npm-managed CLI without replacing active session processes."""
import fcntl
import json
import re
import subprocess
import sys
from pathlib import Path

REGISTRY = 'https://registry.npmjs.org'
CODEX = '/usr/local/bin/codex'
NPM = '/usr/bin/npm'


def main():
    if sys.argv[1:] == ['--client-bundle']:
        print((Path.home() / '.local/share/pinpin-connect/client-release.json').read_text(), end='')
        return 0
    if len(sys.argv) != 1:
        print('Usage: pinpin-codex-upgrade', file=sys.stderr)
        return 2
    lock_dir = Path.home() / '.local/share/pinpin-connect'
    lock_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (lock_dir / 'codex-upgrade.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('A Codex upgrade is already running', file=sys.stderr)
            return 1
        before = subprocess.check_output([CODEX, '--version'], text=True).strip()
        raw = subprocess.check_output([NPM, 'view', '@openai/codex@latest', 'version', '--json',
                                       '--registry', REGISTRY], text=True, timeout=60)
        version = json.loads(raw)
        if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
            raise ValueError('Registry did not return a stable release version')
        print('Installed: ' + before, flush=True)
        print('Latest stable: ' + version, flush=True)
        if before == 'codex-cli ' + version:
            print('Already using the latest installed CLI; no change needed')
            return 0
        subprocess.run([NPM, 'install', '--global', '--prefix', '/usr/local', '--registry', REGISTRY,
                        '@openai/codex@' + version], check=True, timeout=300)
        after = subprocess.check_output([CODEX, '--version'], text=True).strip()
        if after != 'codex-cli ' + version:
            raise ValueError('Installed CLI version did not match the requested release')
        print('Ready: ' + after, flush=True)
        print('New sessions use this version. Existing sessions stay running until restarted.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (subprocess.SubprocessError, OSError, ValueError):
        print('Upgrade failed; inspect the installer output before retrying', file=sys.stderr)
        sys.exit(1)
