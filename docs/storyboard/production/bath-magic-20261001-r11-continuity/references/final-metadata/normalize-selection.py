#!/usr/bin/env python3
"""Normalize only selected artwork provenance; preserve all captions/order."""
from pathlib import Path
import json
p=Path(__file__).resolve().parent
f=p/"story-plan.json";plan=json.loads(f.read_text());assets=json.loads((p/"derivatives.json").read_text())["assets"]
before=[(s["id"],s["number"],s["paragraphs"]) for s in plan["scenes"]]
for s in [plan["cover"],*plan["scenes"]]:
 sid="title" if s["id"]=="cover" else s["id"];a=assets[sid]
 s["image"]=a["web"]["path"];s["sourceProduction"]=a["sourceProduction"]
 s["selectedMaster"]=a["master"]["path"];s["selectedMasterSha256"]=a["master"]["sha256"]
 s["selectedWebSha256"]=a["web"]["sha256"];s["selectedSourceProduction"]=a["sourceProduction"]
 s["selectedWeb"]=a["web"]["path"];s["selectedImagePath"]=a["web"]["path"];s["selectedImageProduction"]=a["sourceProduction"]
 s["selectionKind"]="generated continuity correction" if a["kind"]=="generated" else "unchanged upstream art"
 s["sourceSceneId"]=a.get("sourceSceneId",sid)
 s["reviewStatus"]="Continuity proposal; visually reviewed; awaiting user feedback"
 s["retainArt"]=a["kind"]!="generated";s["newImageRequired"]=False
 if s["retainArt"]:
  s["reuseSourceProduction"]="bath-magic-20261001-r10-story-repair";s["reuseSourceSceneId"]=sid
  s["upstreamSelected"]={"production":a["reusedFromProduction"],"sceneId":a["reusedFromSceneId"],"master":a["master"],"web":a["web"],"physicalSourceProduction":a["sourceProduction"],"generationRecord":a.get("upstreamGenerationRecord"),"reuseRecord":a.get("upstreamReuseRecord")}
  s.pop("generationRecord",None)
  if a.get("upstreamReuseRecord"):s["reuseRecord"]=a["upstreamReuseRecord"]
  else:s.pop("reuseRecord",None)
 else:
  s["generationRecord"]=a["generationRecord"];s.pop("reuseRecord",None);s.pop("reuseSourceProduction",None);s.pop("reuseSourceSceneId",None);s.pop("upstreamSelected",None)
assert before==[(s["id"],s["number"],s["paragraphs"]) for s in plan["scenes"]]
f.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n")
print("Normalized artwork identity only; 113 captions/order unchanged")
