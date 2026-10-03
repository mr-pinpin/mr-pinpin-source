"""Register a captured call with existing helper; preserve exact spec and timings."""
import json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
DATA=Path(__file__).resolve().parents[1]
def main():
    spec_path,call_path=sys.argv[1:]
    spec=json.loads(Path(spec_path).read_text());call=json.loads(Path(call_path).read_text())
    if not spec.get('attemptId') or spec.get('status') != 'prepared':
        raise ValueError('Use cast_ops.py prepare before native generation; register its prepared spec')
    from cast_ops import BusinessRuntime,Store,RUNTIME
    runtime=BusinessRuntime(None,RUNTIME,watch=False,read_only=True)
    try:
        runtime.invoke('route',Store(DATA),'POST','/api/characters/registration-preflight',{},dict(
            attemptId=spec['attemptId'],nativeBytes=Path(call['nativePath']).stat().st_size))
    finally:runtime.close()
    if len(spec['references'])>5:raise ValueError('Prepare and cap native references before registration/generation')
    cfg=json.loads((DATA/'workflows/toolchain.json').read_text())
    args=['--native-path',call['nativePath'],'--prompt-file',spec['promptFile'],'--output-name',spec['outputName'],'--entity',spec['entityId'],'--stage',spec['stage']]
    for ref in spec['references']:args+=['--reference',ref['assetId']]
    receipt=json.loads(subprocess.check_output(cfg['argvPrefix']+args,text=True))
    record_path=DATA/'reports/character-packages'/f'{spec["entityId"]}-generation.json'
    record=json.loads(record_path.read_text()) if record_path.exists() else {'entityId':spec['entityId'],'calls':[],'monetaryCost':None,'deliveryBounds':None,'firstReplyBounds':None}
    record['calls'].append(dict(call,specPath=str(Path(spec_path).resolve()),prompt=spec['prompt'],references=spec['references'],omittedReferences=spec.get('omittedReferences',[]),receipt=receipt,recordedAt=datetime.now(timezone.utc).isoformat()))
    package_path=DATA/receipt['dossierPath']
    package=json.loads(package_path.read_text())
    for candidate in package['stages'][spec['stage']]['candidates']:
        if candidate['assetId']==receipt['assetId']:
            candidate['preparation']={'referenceRoles':spec['references'],'omittedReferences':spec.get('omittedReferences',[]),'nativeInputLimit':5}
    package_path.write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n')
    record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    runtime=BusinessRuntime(None,RUNTIME,watch=False,read_only=True)
    try:
        runtime.invoke('route',Store(DATA),'POST','/api/characters/outcome',{},dict(
            attemptId=spec['attemptId'],status='registered',assetId=receipt['assetId'],
            generationBeforeUTC=call.get('generationBeforeUTC'),generationAfterUTC=call.get('generationAfterUTC'),
            retryOfAttempt=spec.get('retryOfAttempt'),repair=call.get('repair',False)))
    finally:runtime.close()
    subprocess.check_call([sys.executable,'-B',str(DATA/'tools/cast_ops.py'),'reconcile'],stdout=subprocess.DEVNULL)
    print(json.dumps({'assetId':receipt['assetId'],'sha256':receipt['sha256'],'generatedPath':receipt['generatedPath'],'workflowCard':receipt['workflowCard']}))
if __name__=='__main__':main()
