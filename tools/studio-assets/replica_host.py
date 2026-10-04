"""Portable host CLI around the existing pinned replica_store worker; no Studio writes."""
import argparse,json,hashlib,os,subprocess,sys,time,signal
from pathlib import Path

def checked(candidate):
 data=candidate/'data';path=data/'workflows/replica-store.json';cfg=json.loads(path.read_text());library=data/cfg['libraryPath']
 assert Path(cfg['root']).resolve().is_relative_to(data.resolve())
 assert set(cfg['libraryFiles'])=={'__init__.py','core.py','cli.py','hf.py','__main__.py'}
 for name,digest in cfg['libraryFiles'].items():assert hashlib.sha256((library/'replica_store'/name).read_bytes()).hexdigest()==digest
 return path,library,cfg

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--receipt',type=Path);p.add_argument('command',choices=['status','start','stop','run']);a=p.parse_args();config,library,cfg=checked(a.candidate);owned=a.candidate/'runtime/replica-host-ownership.json'
 if a.command=='status':
  metadata=json.loads(owned.read_text()) if owned.exists() else None
  print(json.dumps({'root':cfg['root'],'config':str(config),'owner':metadata,'pollReplica':cfg['pollReplica'],'networkInvoked':False}));return
 if a.command=='run':
  logs=a.candidate/'runtime/replica-host-logs';logs.mkdir(exist_ok=True);log=logs/'worker.log'
  while True:
   config,library,cfg=checked(a.candidate)
   env=dict(os.environ,PYTHONPATH=str(library),PYTHONDONTWRITEBYTECODE='1',HF_HUB_DISABLE_PROGRESS_BARS='1',HF_XET_CHUNK_CACHE_SIZE_BYTES='0',HF_XET_SHARD_CACHE_SIZE_LIMIT='67108864')
   began=time.monotonic();proc=subprocess.Popen([str(a.candidate/'data/tools/studio-python'),'-m','replica_store','--config',str(config),'worker','--once'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   try:
    out,err=proc.communicate(timeout=60);result={'exitCode':proc.returncode,'outputBytes':len(out)+len(err)}
   except subprocess.TimeoutExpired:
    proc.terminate()
    try:proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:proc.kill();proc.communicate()
    result={'status':'pending','reason':'host-timeout'}
   result.update(epoch=time.time(),elapsedMs=round((time.monotonic()-began)*1000,3))
   if log.exists() and log.stat().st_size>=262144:
    prior=log.with_suffix('.log.1');older=log.with_suffix('.log.2')
    if prior.exists():os.replace(prior,older)
    os.replace(log,prior)
   with log.open('a') as stream:stream.write(json.dumps(result)+'\n')
   time.sleep(15)
 if a.command=='start':
  if not a.receipt:p.error('Verified outbox migration receipt required before worker handoff')
  r=json.loads(a.receipt.read_text());assert r['quiescent'] and r['verifiedApplied'] and r['root']==cfg['root']
  for pid in r['oldActorPids']:
   try:os.kill(pid,0)
   except ProcessLookupError:pass
   else:raise RuntimeError('Old queue actor remains')
  if owned.exists():raise RuntimeError('Owner receipt exists; verify/stop through CLI first')
  logs=a.candidate/'runtime/replica-host-logs';logs.mkdir(exist_ok=True);log=logs/'worker.log'
  if log.exists() and log.stat().st_size>262144:raise RuntimeError('Rotate bounded owned log before restart')
  env=dict(os.environ,PYTHONPATH=str(library),PYTHONDONTWRITEBYTECODE='1',HF_HUB_DISABLE_PROGRESS_BARS='1',HF_XET_CHUNK_CACHE_SIZE_BYTES='0',HF_XET_SHARD_CACHE_SIZE_LIMIT='67108864')
  cmd=[str(a.candidate/'data/tools/studio-python'),str(Path(__file__).resolve()),'--candidate',str(a.candidate),'run']
  with log.open('ab') as stream:proc=subprocess.Popen(cmd,env=env,stdout=stream,stderr=stream,start_new_session=True)
  meta={'pid':proc.pid,'pgid':proc.pid,'command':cmd,'config':str(config),'root':cfg['root'],'migrationReceipt':str(a.receipt),'startedEpoch':time.time(),'log':str(log)};owned.write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta));return
 meta=json.loads(owned.read_text());pid=meta['pid'];cmd=subprocess.run(['/bin/ps','-p',str(pid),'-o','command='],capture_output=True,text=True,check=False).stdout
 if cmd:
  if str(Path(__file__).resolve()) not in cmd or str(a.candidate) not in cmd or 'run' not in cmd:raise RuntimeError('PID ownership mismatch')
  os.killpg(pid,signal.SIGTERM)
 owned.rename(owned.with_suffix('.stopped.json'));print(json.dumps({'stoppedOwnedPid':pid}))
if __name__=='__main__':main()
