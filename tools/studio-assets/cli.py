"""Selected artwork metadata/hydration using existing Studio storage adapters."""
import argparse,json,os,sys
from pathlib import Path
class RegistryView:
 def __init__(self,root):self.root=root.resolve()
 def read(self):
  with (self.root/'state.json').open('rb') as stream:raw=stream.read(16777217)
  if len(raw)>16777216:raise ValueError('Registry exceeds16MiB bound')
  return json.loads(raw)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,default=os.environ.get('PINPIN_STUDIO_SOURCE'));p.add_argument('--data-root',type=Path,default=os.environ.get('PINPIN_STUDIO_DATA'));p.add_argument('--restore',action='store_true');p.add_argument('--byte-budget',type=int,default=33554432);p.add_argument('--timeout',type=float,default=45);p.add_argument('asset_ids',nargs='+');a=p.parse_args()
 if not a.source_root or not a.data_root:p.error('Trusted source/data roots required via flags or PINPIN_STUDIO environment')
 sys.path.insert(0,str(a.source_root/'tools/studio'))
 from business.asset_storage import hydrate_selected
 from model import StudioError
 try:print(json.dumps(hydrate_selected(RegistryView(a.data_root),a.asset_ids,restore=a.restore,byte_budget=a.byte_budget,timeout_seconds=a.timeout)))
 except (StudioError,ValueError,OSError) as exc:print(json.dumps({'status':'pending' if a.restore else 'error','errorType':type(exc).__name__,'remoteBackupStatus':'unverified'}));raise SystemExit(2)
if __name__=='__main__':main()
