#!/usr/bin/env python3
from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;old=p.parent/"pinpin-bath-magic-20261001-r10-story-repair"
plan=json.loads((p/"story-plan.json").read_text());before=json.loads((old/"story-plan.json").read_text())
assert len(plan["scenes"])==113
assert [(s["id"],s["number"]) for s in plan["scenes"]]==[(s["id"],s["number"]) for s in before["scenes"]]
a=json.loads((p/"media.json").read_text())["images"];b=json.loads((old/"media.json").read_text())["images"]
expected={"scene-81","scene-82","scene-123","scene-75","scene-55","scene-55a","scene-55c","scene-63"}
changed={sid for sid in a if a[sid]["sha256"]!=b[sid]["sha256"]}
assert changed==expected,(changed,expected)
assert len(a)==len(b)==114
for sid in a:
 f=p.parent/("pinpin-"+a[sid]["sourceProduction"])/a[sid]["path"]
 assert hashlib.sha256(f.read_bytes()).hexdigest()==a[sid]["sha256"],sid
assert a["scene-55b"]["sha256"]==b["scene-55b"]["sha256"]
assert a["scene-45"]["sha256"]==b["scene-45"]["sha256"]
result={"passed":True,"scenes":113,"allPointersChecked":114,"changedStableIds":sorted(changed),"allOther106SlotsByteIdentical":True,"chronologyUnchanged":True,"scene55bCurrent59Unchanged":True,"scene45Unchanged":True,"r10PlanSHA256":hashlib.sha256((old/"story-plan.json").read_bytes()).hexdigest()}
(p/"reader/selection-qa.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result))
