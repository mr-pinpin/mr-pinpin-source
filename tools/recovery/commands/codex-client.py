#!/usr/bin/python3
"""Air launcher for persistent VPS Codex, with explicit transport selection."""
import os
import importlib.util
import shlex
import sys
from pathlib import Path

HELP = """Usage: codex [--connection=auto|tailscale|firebase] [menu options]
       codex [--connection=firebase] --check
       codex [--connection=firebase] upgrade

Plain codex uses automatic fallback. Explicit connections use only that route.
--connection firebase and --connection:firebase are also accepted.
--check verifies the selected route and reports the VPS Codex CLI version.
upgrade updates our custom client and the latest stable VPS Codex CLI; running sessions keep
using their current process until restarted. Menu options include --list,
--new and --resume UUID.
"""
ROUTES = {'tailscale': 'hostinger-vps', 'firebase': 'hostinger-vps-firebase'}


def parse(argv):
    connection = 'auto'
    seen = False
    check = False
    remaining = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == '--':
            remaining.extend(argv[i + 1:])
            break
        if arg == '--connection' or arg.startswith('--connection=') or arg.startswith('--connection:'):
            if seen:
                raise ValueError('Specify --connection only once')
            seen = True
            if arg == '--connection':
                i += 1
                if i == len(argv):
                    raise ValueError('--connection requires auto, tailscale or firebase')
                connection = argv[i]
            else:
                connection = arg.split('=', 1)[1] if '=' in arg else arg.split(':', 1)[1]
            if connection not in ('auto', *ROUTES):
                raise ValueError('Unknown connection; choose auto, tailscale or firebase')
        elif arg == '--check':
            check = True
        else:
            remaining.append(arg)
        i += 1
    upgrade = bool(remaining and remaining[0] == 'upgrade')
    if upgrade and (len(remaining) != 1 or check):
        raise ValueError('Usage: codex [--connection=firebase] upgrade')
    if check and remaining:
        raise ValueError('--check cannot be combined with menu arguments')
    return connection, check, upgrade, remaining


def command(argv, home=None):
    connection, check, upgrade, remaining = parse(argv)
    if upgrade:
        remote = ['/usr/local/bin/pinpin-codex-upgrade']
    elif check:
        remote = ['/usr/local/bin/codex', '--version']
    else:
        remote = ['/usr/local/bin/codex-menu', *remaining]
    # OpenSSH joins command arguments for a remote shell; quote exactly once.
    remote_command = shlex.join(remote)
    if connection == 'auto':
        reconnect = str(Path(home or Path.home()) / 'bin/pinpin-reconnect')
        return [reconnect, '--', remote_command]
    options = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
               '-o', 'ConnectTimeout=' + ('20' if connection == 'firebase' else '5'),
               '-o', 'ServerAliveInterval=20', '-o', 'ServerAliveCountMax=3']
    if not check and not upgrade:
        options.append('-t')
    return [*options, ROUTES[connection], remote_command]


def main():
    if sys.argv[1:] in (['--help'], ['-h']):
        print(HELP)
        return 0
    try:
        parsed = parse(sys.argv[1:])
        connection = parsed[0]
        if parsed[2]:
            path = Path.home() / '.local/share/pinpin-connect/firebase/current/client_upgrade.py'
            spec = importlib.util.spec_from_file_location('pinpin_client_upgrade', path)
            upgrade_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(upgrade_module)
            return upgrade_module.run(connection)
        argv = command(sys.argv[1:])
        print('Connection: ' + connection, file=sys.stderr)
        os.execv(argv[0], argv) if argv[0].startswith('/') else os.execvp(argv[0], argv)
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
