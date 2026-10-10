"""Update the VPS CLI and verified custom Air client via the selected SSH route."""
import base64
import fcntl
import time
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

FILES = {'channel.mjs','cli.mjs','forward.mjs','helper.mjs','protocol.mjs','tunnel.mjs',
         'package.json','package-lock.json','codex-client.py','client_upgrade.py'}


def verify(bundle):
    if not isinstance(bundle, dict) or set(bundle) != {'version','files'} or set(bundle['files']) != FILES:
        raise ValueError('Invalid client release manifest')
    canonical = json.dumps(bundle['files'],sort_keys=True,separators=(',',':')).encode()
    version = hashlib.sha256(canonical).hexdigest()
    if bundle['version'] != version:
        raise ValueError('Client release checksum mismatch')
    return version, {name:base64.b64decode(value,validate=True) for name,value in bundle['files'].items()}


def route_command(connection, remote, home):
    quoted = shlex.join(remote)
    if connection == 'auto':
        return [str(home/'bin/pinpin-reconnect'),'--',quoted]
    return ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o',
            'ConnectTimeout='+('20' if connection == 'firebase' else '5'),
            '-o','ServerAliveInterval=20','-o','ServerAliveCountMax=3',
            'hostinger-vps-firebase' if connection == 'firebase' else 'hostinger-vps',quoted]


def run(connection, home=None):
    home = Path(home or Path.home())
    runtime = home/'.local/share/pinpin-connect/firebase'
    with (runtime/'upgrade.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('A custom client upgrade is already running')
        return _run_locked(connection,home)


def _run_locked(connection, home):
    # Complete remote work before changing the transport carrying the upgrade.
    subprocess.run(route_command(connection,['/usr/local/bin/pinpin-codex-upgrade'],home),check=True)
    raw = subprocess.check_output(route_command(connection,['/usr/local/bin/pinpin-codex-upgrade','--client-bundle'],home),timeout=120)
    if len(raw) > 2_000_000:
        raise ValueError('Client release is too large')
    version, files = verify(json.loads(raw))
    runtime = home/'.local/share/pinpin-connect/firebase'
    versions = runtime/'versions'
    versions.mkdir(parents=True,exist_ok=True,mode=0o700)
    target = versions/version
    if not target.exists():
        stage = Path(tempfile.mkdtemp(prefix='.upgrade-',dir=versions))
        try:
            for name, content in files.items():
                (stage/name).write_bytes(content)
            environment = dict(os.environ)
            environment['PATH'] = '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'
            subprocess.run(['/opt/homebrew/bin/npm','ci','--ignore-scripts','--prefix',str(stage)],env=environment,check=True,timeout=300)
            stage.rename(target)
        finally:
            if stage.exists():shutil.rmtree(stage)
    wrapper = home/'bin/codex'
    backup = home/'.config/pinpin-connect/backups'
    backup.mkdir(parents=True,exist_ok=True,mode=0o700)
    if wrapper.exists():
        previous = hashlib.sha256(wrapper.read_bytes()).hexdigest()
        backup_file = backup/('codex-'+previous)
        if not backup_file.exists():shutil.copy2(wrapper,backup_file)
    current = runtime/'current'
    old_target = os.readlink(current) if current.is_symlink() else None
    link = runtime/'current.next'
    if link.exists() or link.is_symlink():link.unlink()
    link.symlink_to(target)
    os.replace(link,current)
    temporary_wrapper = wrapper.with_name('.codex.next')
    temporary_wrapper.write_bytes(files['codex-client.py'])
    temporary_wrapper.chmod(0o755)
    os.replace(temporary_wrapper,wrapper)
    if old_target != str(target):
        result = subprocess.run(['/bin/launchctl','kill','SIGHUP',f'gui/{os.getuid()}/io.mr-pinpin.firebase-recovery'],capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError('Client installed, but transport reload failed; check launchd service')
        deadline = time.monotonic()+15
        while time.monotonic() < deadline:
            marker = runtime/'loaded-version'
            if marker.exists() and marker.read_text().strip() == version:break
            time.sleep(0.1)
        else:raise RuntimeError('Client installed, but new transport version has not reported ready')
    print('Custom client ready: '+version[:12])
    print('Pairing keys and route settings preserved. Existing sessions stay running.')
    return 0
