"""Portable active-bundle chapter CLI. No cast_ops dependency or network calls."""
import argparse
import json
import os
import sys
import time
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', default=os.environ.get('PINPIN_STUDIO_DATA', str(Path(__file__).resolve().parents[1])))
    parser.add_argument('--runtime-dir', default=os.environ.get('PINPIN_STUDIO_RUNTIME', str(Path(__file__).resolve().parents[1].parent / 'pinpin-studio-runtime')))
    sub = parser.add_subparsers(dest='command', required=True)
    save = sub.add_parser('save'); save.add_argument('spec')
    patch = sub.add_parser('patch'); patch.add_argument('chapterId'); patch.add_argument('--panel', required=True)
    patch.add_argument('--fields', required=True, help='JSON object of selected panel fields')
    patch.add_argument('--version', type=int); patch.add_argument('--sha256'); patch.add_argument('--expected-revision', type=int)
    patch.add_argument('--request', default=''); patch.add_argument('--reason', default='Selected panel revision')
    context = sub.add_parser('context'); context.add_argument('chapterId'); context.add_argument('--page', type=int, default=0)
    authorize = sub.add_parser('authorize', help='Record explicit version-bound full-production go; do not dispatch')
    authorize.add_argument('chapterId')
    authorize.add_argument('--version', required=True, type=int)
    authorize.add_argument('--sha256', required=True)
    authorize.add_argument('--reference-hash', required=True)
    authorize.add_argument('--expected-revision', required=True, type=int)
    authorize.add_argument('--instruction', required=True, help='Exact explicit user full-production instruction')
    args = parser.parse_args()
    data, runtime_dir = Path(args.data_dir), Path(args.runtime_dir)
    deployment = json.loads((runtime_dir / 'current-deployment.json').read_text())
    sys.path.insert(0, str(runtime_dir / 'stable-releases' / deployment['stableRelease']))
    from store import Store, atomic_json
    from business_runtime import BusinessRuntime
    from model import StudioError
    store = Store(data)
    runtime = BusinessRuntime(None, runtime_dir, watch=False, read_only=True)
    started = time.monotonic(); state = store.read()
    if args.command == 'context':
        _, result = runtime.invoke('route', store, 'GET', '/api/chapter-drafts', {'chapterId': [args.chapterId], 'page': [str(args.page)]}, None)
        print(json.dumps(result, ensure_ascii=False)); return
    if args.command == 'save':
        body = json.loads(Path(args.spec).read_text()); route = '/api/chapter-drafts'
        body.setdefault('expectedRevision', state['revision'])
    elif args.command == 'authorize':
        body = {'chapterId': args.chapterId, 'version': args.version, 'sha256': args.sha256,
                'referenceHash': args.reference_hash, 'expectedRevision': args.expected_revision,
                'explicitFullProductionGo': True, 'userInstruction': args.instruction}
        route = '/api/chapter-drafts/authorize-production'
    else:
        chapter = next((c for c in state['project']['chapters'] if c['id'] == args.chapterId), None)
        if not chapter or not chapter.get('studioDraft'):
            raise StudioError('Chapter has no persistent draft')
        draft = chapter['studioDraft']; version = next(v for v in draft['versions'] if v['version'] == draft['currentVersion'])
        body = {'chapterId': args.chapterId, 'baseVersion': args.version if args.version is not None else version['version'],
                'baseSHA256': args.sha256 or version['sha256'],
                'expectedRevision': args.expected_revision if args.expected_revision is not None else state['revision'],
                'patches': [{'panelId': args.panel, 'fields': json.loads(args.fields)}],
                'request': args.request, 'reason': args.reason}
        route = '/api/chapter-drafts/patch'
    _, result = runtime.invoke('route', store, 'POST', route, {}, body)
    result['timing']['cliPreparationToSaveSeconds'] = time.monotonic() - started
    folder = data / 'reports/chapter-drafts' / body['chapterId']; folder.mkdir(parents=True, exist_ok=True)
    atomic_json(folder / (('authorization-' + result['receipt']['receiptSHA256'] + '.json') if args.command == 'authorize' else ('v' + str(result['version']) + '.json')), {'request': body, 'result': result})
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
