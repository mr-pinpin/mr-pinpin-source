#!/usr/bin/env python3
"""Bounded cold-index worker with native diagnostics and transactional publication.

Example: python3 -B tools/studio-locations/index_job.py --root SOURCE
 --catalog EXPORTED/catalog.json --index DATA/cache/location-index.json
 --diagnostics HOME/tmp/location-index-diagnostics --timeout-seconds 180
Queries never invoke this explicit background entrypoint.
"""
import argparse
import faulthandler
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid
from paths import LocationError,atomic_json,external_path


def supervise(args):
    # Diagnostics should use native small-code storage when remote FS is suspect.
    root=Path(args.root).absolute()
    index=external_path(root,args.index)
    diagnostics=external_path(root,args.diagnostics)
    diagnostics.mkdir(parents=True,exist_ok=True)
    identifier=uuid.uuid4().hex[:12]
    result_path=diagnostics/(identifier+'-result.json')
    progress_path=diagnostics/(identifier+'-progress.json')
    trace_path=diagnostics/(identifier+'-trace.txt')
    candidate=index.with_name('.'+index.name+'.candidate-'+identifier)
    index.parent.mkdir(parents=True,exist_ok=True)
    argv=[sys.executable,'-B',str(Path(__file__).resolve()),'--worker','--root',str(root),
          '--index',str(index),'--candidate',str(candidate),'--diagnostics',str(progress_path)]
    if args.catalog:argv+=['--catalog',str(args.catalog)]
    if args.studio_data:argv+=['--studio-data',str(args.studio_data)]
    began=time.monotonic()
    # Parent never reads source packs. A killed worker cannot replace the live index.
    with trace_path.open('wb') as trace:
        process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=trace,start_new_session=True)
        timed_out=False
        try:
            stdout,_=process.communicate(timeout=args.timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out=True
            process.kill()
            try:stdout,_=process.communicate(timeout=5)
            except subprocess.TimeoutExpired:stdout=b''
    success=not timed_out and process.returncode==0
    result={'schemaVersion':1,'jobId':identifier,'status':'timeout' if timed_out else 'failed',
            'timeoutSeconds':args.timeout_seconds,'elapsedSeconds':time.monotonic()-began,
            'indexPath':str(index),'oldIndexPreserved':True,'published':False,
            'progressPath':str(progress_path),'tracePath':str(trace_path),
            'candidatePath':str(candidate),'networkInvoked':False}
    if success:
        try:
            proof=json.loads(stdout)
            if proof.get('status')!='candidate-ready':raise LocationError('Incomplete worker result')
            failures=[e for e in proof['indexResult'].get('errors',[]) if not e['error'].startswith('Catalog identity conflict')]
            if failures:raise LocationError('Incomplete metadata scan; candidate retained and previous index preserved')
            # Candidate is already atomically complete; one same-directory rename publishes it.
            os.replace(candidate,index)
            result.update(status='complete',published=True,oldIndexPreserved=False,indexResult=proof['indexResult'])
        except (OSError,ValueError,KeyError) as exc:
            result['error']={'code':'index_publish_failed','message':str(exc)[:200]}
    elif not timed_out:
        result['error']={'code':'index_worker_failed','message':'See bounded phase/trace diagnostics'}
    if timed_out:
        result['error']={'code':'index_timeout','message':'Cold index timed out; last valid cache remains queryable'}
    atomic_json(result_path,result)
    result['resultPath']=str(result_path)
    print(json.dumps(result,separators=(',',':')))
    return 0 if result['published'] else 3


def worker(args):
    from indexer import build
    state={'phase':'starting','path':None,'startedMonotonic':time.monotonic()}
    stop=threading.Event()
    def update(**values):state.update(values)
    def emit():
        while not stop.is_set():
            value=dict(state,elapsedSeconds=time.monotonic()-state['startedMonotonic'])
            atomic_json(Path(args.diagnostics),value)
            stop.wait(1)
    thread=threading.Thread(target=emit,daemon=True);thread.start()
    faulthandler.enable()
    faulthandler.dump_traceback_later(10,repeat=True)
    try:
        value=build(Path(args.root),Path(args.candidate),args.studio_data,args.catalog,
                    previous_path=Path(args.index),progress=update)
        print(json.dumps({'status':'candidate-ready','indexResult':value},separators=(',',':')))
        return 0
    finally:
        faulthandler.cancel_dump_traceback_later();stop.set();thread.join(timeout=2)
        atomic_json(Path(args.diagnostics),dict(state,elapsedSeconds=time.monotonic()-state['startedMonotonic']))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True);p.add_argument('--index',required=True)
    p.add_argument('--catalog');p.add_argument('--studio-data');p.add_argument('--diagnostics',required=True)
    p.add_argument('--timeout-seconds',type=float,default=180)
    p.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    p.add_argument('--candidate',help=argparse.SUPPRESS)
    args=p.parse_args()
    if not 0<args.timeout_seconds<=900:p.error('Timeout must be greater than zero and at most 900s')
    try:return worker(args) if args.worker else supervise(args)
    except (OSError,ValueError) as exc:
        print(json.dumps({'error':{'code':'index_job_rejected','message':str(exc)[:200]},'published':False}))
        return 2


if __name__=='__main__':sys.exit(main())
