import importlib.util
import shlex
import unittest
from pathlib import Path
from unittest.mock import patch


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(file))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


client = module('client', 'codex-client.py')
upgrade = module('upgrade', 'codex-upgrade.py')
installer = module('installer', 'client_upgrade.py')


class Commands(unittest.TestCase):
    def test_forced_connection_forms_and_no_fallback(self):
        for args in [['--connection=firebase'], ['--connection:firebase'], ['--connection', 'firebase']]:
            command = client.command(args)
            self.assertEqual(command[-2], 'hostinger-vps-firebase')
            self.assertNotIn('pinpin-reconnect', ' '.join(command))
        self.assertEqual(client.command(['--connection=tailscale'])[-2], 'hostinger-vps')

    def test_automatic_route_and_quoting(self):
        malicious = 'uuid; echo should-not-execute'
        command = client.command(['--resume', malicious], home='/private/user')
        self.assertEqual(command[:2], ['/private/user/bin/pinpin-reconnect', '--'])
        self.assertEqual(shlex.split(command[-1]), ['/usr/local/bin/codex-menu', '--resume', malicious])

    def test_check_and_upgrade_bypass_session_menu(self):
        check = client.command(['--connection=firebase', '--check'])
        self.assertNotIn('-t', check)
        self.assertEqual(shlex.split(check[-1]), ['/usr/local/bin/codex', '--version'])
        command = client.command(['upgrade', '--connection=firebase'])
        self.assertEqual(command[-1], '/usr/local/bin/pinpin-codex-upgrade')
        self.assertNotIn('-t', command)

    def test_release_integrity_and_path_rejection(self):
        import base64, hashlib, json
        files = {name:base64.b64encode(b'fixture').decode() for name in installer.FILES}
        version = hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self.assertEqual(installer.verify({'version':version,'files':files})[0],version)
        corrupted = dict(files, **{'cli.mjs':base64.b64encode(b'altered').decode()})
        with self.assertRaises(ValueError):installer.verify({'version':version,'files':corrupted})
        bad_path = dict(files, **{'../config.json':'AAAA'})
        with self.assertRaises(ValueError):installer.verify({'version':version,'files':bad_path})

    def test_invalid_flags_fail_before_connecting(self):
        for args in [['--connection=bad'], ['--connection'], ['--connection=firebase','--connection=auto'],
                     ['upgrade','--new'], ['upgrade','--check'], ['--check','--new']]:
            with self.assertRaises(ValueError):
                client.command(args)


if __name__ == '__main__':
    unittest.main()
