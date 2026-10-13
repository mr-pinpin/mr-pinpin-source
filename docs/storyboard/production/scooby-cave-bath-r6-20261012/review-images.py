"""Apply explicit visual-review decisions without racing generation recorders."""
import argparse,fcntl,hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
parser=argparse.ArgumentParser();parser.add_argument('decisions');args=parser.parse_args()
pack=Path(__file__).resolve().parent;root=pack.parents[3];decisions=json.loads(Path(args.decisions).read_text())
assert isinstance(decisions,list)
selection=pack/'working-selection.json';selected=json.loads(selection.read_text())
with (pack/'generation-records.json').open('r+') as handle:
 fcntl.flock(handle.fileno(),fcntl.LOCK_EX);records=json.load(handle);byid={r['id']:r for r in records}
 for d in decisions:
  r=byid[d['id']];native=root/r['nativePath'];assert hashlib.sha256(native.read_bytes()).hexdigest()==r['nativeSha256'];assert d['review'].strip()
  r['status']=d['status'];r['review']=d['review'];r['reviewedAt']=datetime.now(timezone.utc).isoformat();r['selectedForPublication']=False
  if d.get('select'):
   n=re.fullmatch(r'r6-(\d{3})-v\d+',d['id']);assert n,'Narrative selections require scene id';assert d['status']=='agent-reviewed-working';selected['selected'][n[1]]=d['id']
 handle.seek(0);handle.write(json.dumps(records,indent=2)+'\n');handle.truncate();handle.flush()
selection.write_text(json.dumps(selected,indent=2)+'\n');print(len(decisions),'explicit review decisions recorded')
