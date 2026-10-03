"""Mini host supervision for the generic replica-store CLI, never Studio."""
import argparse, hashlib, json, os, plistlib, subprocess, time
from pathlib import Path


def volume_ready(mount, uuid):
    if not os.path.ismount(mount):
        return False
    try:
        result = subprocess.run(['/usr/sbin/diskutil', 'info', '-plist', mount],
                                capture_output=True, timeout=8, check=True)
        info = plistlib.loads(result.stdout)
        return (info.get('MountPoint') == mount and info.get('VolumeUUID') == uuid
                and info.get('Internal') is False)
    except (OSError, subprocess.SubprocessError, ValueError):
        return False


def plain_path(path):
    for entry in (path, *path.parents):
        if entry.is_symlink():
            raise ValueError('Symlink deployment path')


def record(path, message):
    plain_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size >= 262144:
        older = path.with_suffix('.log.2')
        prior = path.with_suffix('.log.1')
        if prior.exists():
            os.replace(prior, older)
        os.replace(path, prior)
    with path.open('a') as stream:
        stream.write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + message[:1024] + '\n')


def heartbeat(host, stage):
    """Explicitly authorized bounded home metadata; no payload/error bodies."""
    path = Path(host['healthPath'])
    plain_path(path)
    if path.parent != Path.home() / '.config/replica-store':
        raise ValueError('Health path must use existing host config directory')
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps({'stage': stage, 'pid': os.getpid(),
                                    'observedUTC': time.time()}) + '\n')
    os.replace(temporary, path)


def run_once(host):
    heartbeat(host, 'checking-volume')
    mount = host['mountPoint']
    if not volume_ready(mount, host['volumeUUID']):
        heartbeat(host, 'volume-unavailable')
        return 'volume-unavailable'
    config_path = Path(host['configPath'])
    log = Path(host['logPath'])
    for path in (config_path, log):
        if not path.is_relative_to(Path(mount)):
            raise ValueError('Deployment paths must remain on TB4')
        plain_path(path)
    heartbeat(host, 'reading-worker-config')
    config = json.loads(config_path.read_text())
    data = config_path.parents[1]
    relative = Path(config['libraryPath'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Invalid configured library path')
    library = Path(host.get('librarySource', str(data / relative)))
    if not library.is_absolute() or not library.is_relative_to(Path(mount)):
        raise ValueError('Library source must remain on TB4')
    plain_path(library)
    files = config.get('libraryFiles', {})
    if set(files) != {'__init__.py', 'core.py', 'hf.py', 'cli.py', '__main__.py'}:
        raise ValueError('Final library receipt required')
    heartbeat(host, 'checking-library-files')
    for name, expected in files.items():
        path = library / 'replica_store' / name
        plain_path(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Library differs from final reviewed receipt')
    root = Path(config['root'])
    plain_path(root)
    if not root.is_absolute() or not root.is_relative_to(Path(mount)):
        raise ValueError('Outbox root must remain on TB4')
    cache_root = Path(host['cacheRoot'])
    plain_path(cache_root)
    if not cache_root.is_absolute() or not cache_root.is_relative_to(Path(mount)):
        raise ValueError('Transfer caches must remain on TB4')
    env = dict(os.environ, PYTHONPATH=str(library), PYTHONDONTWRITEBYTECODE='1',
               HF_HUB_DISABLE_PROGRESS_BARS='1',
               HF_XET_CACHE=str(cache_root / 'xet'),
               HF_HUB_CACHE=str(cache_root / 'hub'),
               HF_XET_CHUNK_CACHE_SIZE_BYTES='67108864',
               HF_XET_SHARD_CACHE_SIZE_LIMIT='67108864')
    if not volume_ready(mount, host['volumeUUID']):
        return 'volume-unavailable'
    started = time.monotonic()
    heartbeat(host, 'invoking-worker')
    result = subprocess.run([host['pythonPath'], '-B', '-m', 'replica_store',
                             '--config', str(config_path), 'worker', '--once'],
                            env=env, cwd=mount, capture_output=True,
                            timeout=host['workerTimeoutSeconds'])
    # Logs contain status/timing only; owned jobs and receipts hold details.
    message = 'worker exit=%d seconds=%.3f outputBytes=%d' % (
        result.returncode, time.monotonic() - started, len(result.stdout) + len(result.stderr))
    if volume_ready(mount, host['volumeUUID']):
        record(log, message)
    stage = 'worker-completed' if result.returncode == 0 else 'worker-failed'
    heartbeat(host, stage)
    return stage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host-config', required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    host = json.loads(Path(args.host_config).read_text())
    heartbeat(host, 'supervisor-started')
    interval = host['intervalSeconds']
    if type(interval) is not int or not 5 <= interval <= 3600:
        raise ValueError('Invalid interval')
    if not 30 <= host['workerTimeoutSeconds'] <= 600:
        raise ValueError('Invalid worker timeout')
    if args.check:
        print(json.dumps({'volumeReady': volume_ready(host['mountPoint'], host['volumeUUID']),
                          'workerStarted': False}))
        return
    while True:
        try:
            run_once(host)
        except Exception as exc:
            heartbeat(host, 'error-' + type(exc).__name__)
            if volume_ready(host['mountPoint'], host['volumeUUID']):
                record(Path(host['logPath']), 'supervisor errorType=' + type(exc).__name__)
        time.sleep(interval)


if __name__ == '__main__':
    main()
