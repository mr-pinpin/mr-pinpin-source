#!/usr/bin/env python3
"""Register already-produced built-in image candidates honestly; no generation API calls."""
import sys,json,pathlib,hashlib,datetime
BASE=pathlib.Path("/Volumes/TB4/mac-mini-storage/shared")
sys.path.insert(0,str(BASE/"pinpin-r17-studio-source/tools/studio"))
from store import Store
from jobs import create_job,claim_job,complete_job
P=pathlib.Path(__file__).parent
store=Store(BASE/"pinpin-studio-data")
selection=json.loads((P/"selection.json").read_text())["selected"]
report=[]
for sid,r in sorted(selection.items()):
 out=P/"records"/(sid+"-studio-completed.json")
 if out.exists():report.append(json.loads(out.read_text()));continue
 bindings=[]
 for index,ref in enumerate(r["references"]):
  asset=store.import_asset(ref["path"],provenance={"source":"R23 actual image reference","generationRecord":r["record"]})
  assert asset["sha256"]==ref["sha256"]
  bindings.append({"assetId":asset["id"],"roles":["actual-tool-input-"+str(index+1)]})
 instruction="Register already-generated R23 candidate "+sid+". This job is created AFTER built-in generation to preserve actual tool provenance and permit review; claim-to-complete time is NOT generation duration. Native production record: "+r["record"]+". No livechapter scene target because R23 not installed; do not auto-publish.\n"+r["toolArguments"]["prompt"]
 job=create_job(store,{"kind":"illustration","instruction":instruction,"sceneIds":[],"referenceBindings":[{"assetId":x["assetId"],"role":x["roles"][0]} for x in bindings]})[0]
 claim_job(store,job["id"],"r12_papa_round")
 job=complete_job(store,job["id"],"r12_papa_round",image=r["master"],actual_prompt=r["toolArguments"]["prompt"],actual_references=bindings,tool_name="image_gen__imagegen",visual_pass=True)[0]
 a=job["artifacts"][-1]
 assert a["sha256"]==r["sha256"]
 expected=hashlib.sha256(r["toolArguments"]["prompt"].encode()).hexdigest()
 assert a["actualPromptSha256"]==expected
 small={"sceneId":sid,"jobId":job["id"],"artifactId":a["id"],"assetId":a["assetId"],"sha256":a["sha256"],"actualPromptSha256":a["actualPromptSha256"],"actualReferencesStatus":a["actualReferencesStatus"],"status":job["status"],"rootReview":"pass","userReview":"pending","registrationAfterGeneration":True}
 out.write_text(json.dumps(small,indent=2)+"\n");report.append(small)
 print(sid,job["id"],job["status"],flush=True)
(P/"studio-registration.json").write_text(json.dumps({"records":report,"registered":len(report),"note":"Actual native candidates, exact submitted prompt and references. No scene selection or publication."},indent=2)+"\n")

