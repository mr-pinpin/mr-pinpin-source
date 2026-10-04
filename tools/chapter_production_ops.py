"""Portable CLI over verified Studio business jobs; no generation or publication."""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

MAX_REQUEST = 1024 * 1024
SCHEMA = {
    'dispatch': {'required': ['kind', 'chapterId', 'sceneIds', 'instruction'],
                 'optional': ['referenceIds', 'referenceBindings', 'productionScope', 'retryOf', 'entityId'],
                 'productionScope': ['full-production', 'rough-preproduction'],
                 'referenceBindings': [{'assetId': '<registered ID>', 'role': '<actual role>'}]},
    'complete': {'required': ['jobId', 'agent', 'sceneId for multi-scene images', 'image or text-file',
                              'prompt-file', 'references-file', 'tool'],
                 'references-file': [{'assetId': '<registered ID>', 'roles': ['<actual role>']}],
                 'atomicity': 'Existing business complete_job performs one Store mutation per artifact.'},
    'safety': ['Dispatch uses existing version/reference authorization and local-byte guards.',
               'No authorization, approval, publication, generation or automatic retry is performed.',
               'Write exact prompt files BEFORE generation. Completion records actual supplied prompt/references.',
               'Inspect resume after uncertain completion; completion is not an exactly-once RPC.']}


def read_file(path, limit):
    with Path(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    if not raw or len(raw) > limit:
        raise ValueError('Input must contain1 to' + str(limit) + ' bytes')
    return raw.decode('utf-8')


def load(data, runtime_dir, read_only):
    deployment = json.loads((runtime_dir / 'current-deployment.json').read_text())
    release = deployment['stableRelease']
    if not re.fullmatch('[a-f0-9]{64}', release):
        raise ValueError('Invalid stable release identity')
    kernel = runtime_dir / 'stable-releases' / release
    sys.path.insert(0, str(kernel))
    from immutable_bundle import verify_bundle
    if verify_bundle(kernel).get('kind') != 'stable-runtime':
        raise ValueError('Expected verified immutable stable runtime')
    from store import Store
    from business_runtime import BusinessRuntime
    if read_only:
        store = Store.__new__(Store)
        store.root, store.path = data, data / 'state.json'
        store.media_roots = [Path(p) for p in json.loads((data / 'settings.json').read_text()).get('mediaRoots', [])]
        store.read = lambda: json.loads(store.path.read_text())
    else:
        store = Store(data)
    return store, BusinessRuntime(None, runtime_dir, watch=False, read_only=True)


def job_summary(job):
    artifacts = [{k: a.get(k) for k in ('id', 'sceneId', 'type', 'assetId', 'sha256', 'reviewStatus',
                 'actualPromptStatus', 'actualPromptSha256', 'actualPromptPath', 'actualReferencesStatus')}
                 for a in job.get('artifacts', [])]
    completed = {a['sceneId'] for a in artifacts if a['type'] == 'image'}
    return {**{k: job.get(k) for k in ('id', 'status', 'kind', 'chapterId', 'sceneIds', 'claimedBy',
             'draftBinding', 'productionScope', 'retryOf', 'promptPath', 'promptSha256')},
            'artifacts': artifacts, 'remainingSceneIds': [s for s in job.get('sceneIds', []) if s not in completed],
            'referenceBindings': [{k: r.get(k) for k in ('assetId', 'sha256', 'roles', 'role', 'path', 'reviewStatus')}
                                  for r in job.get('referenceBindings', [])]}


def execute(args, store, runtime):
    if args.command in ('context', 'resume'):
        state = store.read()
        jobs = [j for j in state['jobs'] if (getattr(args, 'chapter', None) is None or j.get('chapterId') == args.chapter)
                and (getattr(args, 'job', None) is None or j['id'] == args.job)]
        if args.command == 'resume' and not jobs:
            raise ValueError('Unknown job')
        # Bounded job metadata, no full prompts, conversation or snapshots.
        result = {'revision': state['revision'], 'jobs': [job_summary(j) for j in jobs[-16:]],
                  'totalMatchingJobs': len(jobs), 'schema': SCHEMA, 'mutated': False}
        if args.command == 'context':
            response = runtime.invoke('route', store, 'GET', '/api/chapter-drafts', {'chapterId': [args.chapter], 'page': ['0']}, None)
            result['draft'] = response[1]
        return result
    if args.command == 'prepare':
        state = store.read()
        job = next((j for j in state['jobs'] if j['id'] == args.job), None)
        if not job or job.get('status') != 'claimed' or job.get('claimedBy') != args.agent:
            raise ValueError('Preparation requires job claimed by this agent')
        if args.scene not in job.get('sceneIds', []) or not re.fullmatch('[A-Za-z0-9_-]{1,100}', args.scene):
            raise ValueError('Scene must be a safe job target')
        prompt = read_file(args.prompt_file, 100000)
        references = json.loads(read_file(args.references_file, MAX_REQUEST))
        if not isinstance(references, list) or len(references) > 32:
            raise ValueError('Expected bounded reference bindings')
        verified = []
        total_bytes = 0
        for binding in references:
            if not isinstance(binding, dict) or not isinstance(binding.get('roles'), list) or not binding['roles']:
                raise ValueError('Each actual reference needs assetId and roles')
            asset = next((a for a in state['assets'] if a['id'] == binding.get('assetId')), None)
            if not asset or any(not isinstance(role, str) or not role.strip() for role in binding['roles']):
                raise ValueError('Unknown reference or invalid roles')
            total_bytes += asset['bytes']
            if total_bytes > 256 * 1024 * 1024:
                raise ValueError('Prepared references exceed256MiB budget')
            path = store.asset_path(asset['id'], state)
            raw = path.read_bytes()
            if len(raw) != asset['bytes'] or hashlib.sha256(raw).hexdigest() != asset['sha256']:
                raise ValueError('Actual reference bytes require verified local restoration')
            verified.append({'assetId': asset['id'], 'roles': binding['roles'], 'sha256': asset['sha256']})
        raw = prompt.encode('utf-8'); sha = hashlib.sha256(raw).hexdigest()
        directory = store.root / 'jobs' / job['id'] / 'prepared'
        if not directory.resolve().is_relative_to(store.root.resolve()):
            raise ValueError('Preparation output escapes data root')
        prompt_path = directory / (args.scene + '-' + sha + '.txt')
        references_path = directory / (args.scene + '-' + sha + '-references.json')
        from store import atomic_bytes, atomic_json
        directory.mkdir(parents=True, exist_ok=True)
        if prompt_path.exists() and prompt_path.read_bytes() != raw:
            raise ValueError('Existing prepared prompt differs')
        if references_path.exists() and json.loads(references_path.read_text()) != verified:
            raise ValueError('Existing prepared references differ; use a distinct exact prompt')
        atomic_bytes(prompt_path, raw); atomic_json(references_path, verified)
        return {'jobId': job['id'], 'sceneId': args.scene, 'promptFile': str(prompt_path),
                'promptSHA256': sha, 'referencesFile': str(references_path),
                'generationStarted': False, 'stateMutated': False}
    if args.command == 'dispatch':
        body = json.loads(read_file(args.request_file, MAX_REQUEST))
        if not isinstance(body, dict) or not all(k in body for k in SCHEMA['dispatch']['required']):
            raise ValueError('Dispatch requires kind/chapterId/sceneIds/instruction')
        if not isinstance(body['sceneIds'], list) or not body['sceneIds']:
            raise ValueError('Explicit nonempty sceneIds required for resumable scene production')
        response = runtime.invoke('route', store, 'POST', '/api/jobs', {}, body)
        return {'job': job_summary(response[1]['job']), 'revision': response[1]['revision']}
    if args.command == 'claim':
        job, state = runtime.invoke('claim_job', store, args.job, args.agent)
    elif args.command == 'fail':
        job, state = runtime.invoke('fail_job', store, args.job, args.agent, args.reason)
    else:
        prompt = read_file(args.prompt_file, 100000)
        references = json.loads(read_file(args.references_file, MAX_REQUEST))
        if not isinstance(references, list) or len(references) > 32 or any(
                not isinstance(r, dict) or not isinstance(r.get('assetId'), str) or
                not isinstance(r.get('roles'), list) or not r['roles'] or
                any(not isinstance(role, str) or not role.strip() for role in r['roles']) for r in references):
            raise ValueError('Actual references must be at most32 assetId/roles bindings')
        text = read_file(args.text_file, 5 * 1024 * 1024) if args.text_file else None
        # Actual existing guards own allowed-source validation, ownership and atomic completion.
        job, state = runtime.invoke('complete_job', store, args.job, args.agent,
                                  image=args.image, text=text, scene_id=args.scene,
                                  actual_prompt=prompt, actual_references=references,
                                  tool_name=args.tool, visual_pass=args.visual_pass)
    return {'job': job_summary(job), 'revision': state['revision']}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir', type=Path, default=os.environ.get('PINPIN_STUDIO_DATA'))
    p.add_argument('--runtime-dir', type=Path, default=os.environ.get('PINPIN_STUDIO_RUNTIME'))
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('schema')
    c = sub.add_parser('context'); c.add_argument('chapter')
    c = sub.add_parser('resume'); c.add_argument('job')
    c = sub.add_parser('dispatch'); c.add_argument('request_file')
    for name in ('claim', 'fail', 'prepare', 'complete'):
        c = sub.add_parser(name); c.add_argument('job'); c.add_argument('--agent', required=True)
        if name == 'fail':
            c.add_argument('--reason', required=True)
        if name == 'prepare':
            c.add_argument('--scene', required=True); c.add_argument('--prompt-file', required=True)
            c.add_argument('--references-file', required=True)
        if name == 'complete':
            media = c.add_mutually_exclusive_group(required=True)
            media.add_argument('--image'); media.add_argument('--text-file')
            c.add_argument('--scene'); c.add_argument('--prompt-file', required=True)
            c.add_argument('--references-file', required=True); c.add_argument('--tool', required=True)
            c.add_argument('--visual-pass', action='store_true', help='Actual agent QA, never user approval')
    return p


def main():
    p = parser(); args = p.parse_args()
    if args.command == 'schema':
        print(json.dumps(SCHEMA)); return
    if not args.data_dir or not args.runtime_dir:
        p.error('Trusted local roots required via PINPIN_STUDIO_DATA/RUNTIME or explicit flags')
    try:
        store, runtime = load(args.data_dir.resolve(), args.runtime_dir.resolve(), args.command in ('context', 'resume'))
        print(json.dumps(execute(args, store, runtime), ensure_ascii=False))
    except Exception as exc:
        # No raw prompts, paths or credentials from exception details.
        print(json.dumps({'status': 'error', 'errorType': type(exc).__name__,
                          'advice': 'Inspect context/resume and recorded receipts before retry; guards remain intact.'}))
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
