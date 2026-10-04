"""Host supervision behind Mission Control CLI; never modifies app implementation."""
import argparse,datetime,fcntl,json,math,os,pathlib,shutil,subprocess,sys,time,uuid

def atomic(p,d):
 q=p.with_suffix('.tmp')
 with q.open('w') as f:f.write(json.dumps(d,indent=2)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(q,p)
def invoke(args):
 r=subprocess.run(args,capture_output=True,text=True,timeout=30)
 if r.returncode:raise RuntimeError('CLI failed: '+str(r.returncode))
 return json.loads(r.stdout)
def decision(status,now,c,action,state):
 if now>=c['deadlineEpoch']:return 'deadline'
 if status.get('activeTurnId') or status.get('status') not in ('idle','completed'):return 'active-or-not-ready'
 if status.get('threadId')!=c.get('approvedThread'):return 'config-thread-refused'
 if not action:return 'read-only-no-queued-action'
 if not isinstance(action.get('id'),str) or not action['id'] or not action.get('text'):return 'invalid-action'
 if action.get('id') in state.get('claims',{}):return 'duplicate-claimed'
 if action.get('coordinatorApproved') is not True or action.get('threadId')!=status.get('threadId'):return 'unapproved-or-wrong-thread'
 if action.get('expectedCursor')!=status.get('cursor'):return 'stale-progress-token'
 if action.get('publication') or (action.get('fullProduction') and action.get('explicitProductionApproval') is not True):return 'scope-approval-required'
 cost=action.get('reserveUSD')
 amounts=(cost,state.get('reservedUSD'),state.get('spentUSD'))
 if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in amounts):return 'budget-refused'
 if sum(amounts)>25:return 'budget-refused'
 return 'eligible'
def tick(c,root):
 statepath=root/'checkpoint.json';state=json.loads(statepath.read_text()) if statepath.exists() else {'claims':{},'spentUSD':0,'reservedUSD':0}
 status=invoke([c['python'],c['client'],'status','--url',c['url'],'--json','--request-timeout','15'])
 actionpath=root/'queued-action.json';action=json.loads(actionpath.read_text()) if actionpath.exists() else None
 now=time.time();reason=decision(status,now,c,action,state);entry={'observedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'correlationId':uuid.uuid4().hex,'monitors':'APP Studio conversation; does not revive ROOT','status':status.get('status'),'activeTurnId':status.get('activeTurnId'),'cursor':status.get('cursor'),'threadId':status.get('threadId'),'decision':reason,'mode':c['mode']}
 if reason=='eligible' and c['mode']=='coordinator-queue':
  # Recheck immediately before durable claim and send. Unknown delivery is never retried.
  again=invoke([c['python'],c['client'],'status','--url',c['url'],'--json'])
  if decision(again,time.time(),c,action,state)!='eligible':entry['decision']='recheck-refused'
  else:
   state['reservedUSD']+=action['reserveUSD'];state['claims'][action['id']]={'status':'claimed-before-send','reservedUSD':action['reserveUSD'],'correlationId':entry['correlationId']};atomic(statepath,state)
   message=root/('action-'+entry['correlationId']+'.txt');message.write_text(action['text'])
   try:
    result=invoke([c['python'],c['client'],'send','--url',c['url'],'--json','--actor','sprint-watchdog','--on-behalf-of','coordinator','--message-file',str(message)])
    claim=state['claims'][action['id']]
    for key in ('messageId','turnId','acceptedAt'):claim[key]=result.get(key)
    if result.get('accepted') is not True:raise RuntimeError('Send not positively accepted')
    claim['status']='submitted';entry['decision']='submitted'
   except Exception:state['claims'][action['id']]['status']='uncertain-no-retry';entry['decision']='uncertain-no-retry'
   finally:message.unlink(missing_ok=True)
 state['latest']=entry;atomic(statepath,state)
 (root/'observation-error.json').unlink(missing_ok=True)
 with (root/'ticks.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
 print(json.dumps(entry),flush=True);return reason!='deadline'
def observation_error(root,c,error):
 statepath=root/'checkpoint.json'
 try:state=json.loads(statepath.read_text())
 except FileNotFoundError:state={'claims':{},'spentUSD':0,'reservedUSD':0}
 except Exception:state=None
 entry={'observedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'correlationId':uuid.uuid4().hex,'monitors':'APP Studio conversation; does not revive ROOT','mode':c['mode'],'decision':'observation-error','errorType':type(error).__name__,'dispatches':0}
 if state is not None:state['latest']=entry;atomic(statepath,state)
 atomic(root/'observation-error.json',entry)
 with (root/'ticks.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
 print(json.dumps(entry),flush=True)

def tests():
 c={'deadlineEpoch':100,'approvedThread':'t'};s={'claims':{},'spentUSD':0,'reservedUSD':0};a={'id':'one','text':'bounded approved step','coordinatorApproved':True,'threadId':'t','reserveUSD':0,'expectedCursor':7};idle={'status':'completed','threadId':'t','cursor':7}
 assert decision(idle,100,c,a,s)=='deadline'
 assert decision(dict(idle,activeTurnId='busy'),1,c,a,s)=='active-or-not-ready'
 assert decision({'status':'connecting'},1,c,a,s)=='active-or-not-ready'
 s['claims']['one']={};assert decision(idle,1,c,a,s)=='duplicate-claimed';s['claims']={}
 assert decision(idle,1,c,None,s)=='read-only-no-queued-action'
 assert decision(idle,1,c,dict(a,reserveUSD=26),s)=='budget-refused'
 assert decision(idle,1,c,dict(a,fullProduction=True),s)=='scope-approval-required'
 assert decision(idle,1,c,dict(a,publication=True),s)=='scope-approval-required'
 assert decision(idle,1,c,dict(a,expectedCursor=6),s)=='stale-progress-token'
 assert decision(idle,1,c,a,s)=='eligible'
 print(json.dumps({'passed':10,'dryRun':True,'dispatches':0}))
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['start','stop','status','tick','run','test','arm','disarm']);p.add_argument('--config',required=True);p.add_argument('--action-file');a=p.parse_args();cfg=pathlib.Path(a.config).resolve();c=json.loads(cfg.read_text());root=cfg.parent
 if not os.path.ismount(c.get('requiredMount','/Volumes/TB4')):raise RuntimeError('Required external mount absent')
 tmux=c.get('tmuxBinary') or shutil.which('tmux')
 if not tmux:raise RuntimeError('tmux runtime unavailable')
 if a.command=='test':tests();return
 if a.command=='disarm':
  c['mode']='read-only';atomic(cfg,c);print(json.dumps({'disarmed':True,'claimsPreserved':True,'requiresSchedulerReload':True,'dispatchOwnership':'returned-to-coordinator'}));return
 if a.command=='arm':
  if not a.action_file:raise ValueError('--action-file required')
  action=json.loads(pathlib.Path(a.action_file).read_text());statepath=root/'checkpoint.json';state=json.loads(statepath.read_text()) if statepath.exists() else {'claims':{},'spentUSD':0,'reservedUSD':0}
  status=invoke([c['python'],c['client'],'status','--url',c['url'],'--json']);reason=decision(status,time.time(),c,action,state)
  if reason!='eligible':raise ValueError('Arm refused: '+reason)
  atomic(root/'queued-action.json',action);c['mode']='coordinator-queue';atomic(cfg,c);print(json.dumps({'armedActionId':action['id'],'dispatches':0,'requiresSchedulerReload':True}));return
 if a.command=='start':
  # tmux is an implementation detail of this CLI lifecycle surface.
  cmd=[c['cli'],'watchdog','run','--config',str(cfg)];import shlex
  subprocess.run([tmux,'new-session','-d','-s',c['session'],shlex.join(cmd)],check=True);print(json.dumps({'started':True,'mode':c['mode'],'session':c['session']}));return
 if a.command=='stop':
  subprocess.run([tmux,'kill-session','-t',c['session']],check=True);print(json.dumps({'stopped':True}));return
 if a.command=='status':
  try:d=json.loads((root/'checkpoint.json').read_text()) if (root/'checkpoint.json').exists() else {}
  except Exception:d={'checkpointUnreadable':True}
  if (root/'observation-error.json').exists():d['latest']=json.loads((root/'observation-error.json').read_text())
  r=subprocess.run([tmux,'has-session','-t',c['session']],capture_output=True);d['schedulerSessionExists']=r.returncode==0;d['configuredMode']=c['mode'];d['dispatchOwnership']='coordinator' if c['mode']=='read-only' else 'exclusive-coordinator-queue';d['deadlineUTC']=c.get('deadlineUTC');d['monitors']='APP only; does not revive ROOT'
  latest=d.get('latest',{});stamp=latest.get('observedUTC');d['heartbeatAgeSeconds']=time.time()-datetime.datetime.fromisoformat(stamp).timestamp() if stamp else None;d['observationFailed']=latest.get('decision')=='observation-error';print(json.dumps(d));return
 with (root/'watchdog.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  while True:
   try:more=tick(c,root)
   except Exception as e:
    observation_error(root,c,e);more=time.time()<c['deadlineEpoch']
   if a.command=='tick' or not more:break
   time.sleep(min(c['intervalSeconds'],max(0,c['deadlineEpoch']-time.time())))
if __name__=='__main__':main()
