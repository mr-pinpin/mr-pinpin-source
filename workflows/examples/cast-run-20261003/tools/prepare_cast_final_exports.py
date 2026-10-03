"""Prepare final source-checkpoint docs once; no image binaries or approval metadata."""
import json,hashlib
from pathlib import Path
from cast_ops import DATA as D,Store,atomic_json
guide=D/'workflows/character-creation.md'
text=guide.read_text()
marker='## Complete-cast checkpoint'
if marker not in text:
 text+='\n'+marker+'\n\nWhen the reconciled queue has no missing stages, the existing `tools/cast_ops.py checkpoint <batch> <entity> ...` also writes `reports/cast-complete-inventory.md` and `.json`: all final IDs/native links, sourced age/life stage, curated dossiers/bibliography, standard receipts including retained attempts, exact prompts/reference roles and available timing reports. Unknown legacy or delivery/billing measurements stay unknown. Production and agent QA do not grant human approval or publication. The active finish CLI is tested twice on the end-of-dossier fixture, preserving one complete metrics marker block and curated prose; see tools/test_cast_closeout.py and reports/cast-closeout-proof.json.\n'
if len(text.encode())>22000:raise ValueError('Guide exceeds context cap')
guide.write_text(text)
doc=D/'exports/workflows-README.md';text=doc.read_text()
heading='## Complete-cast draft inventory'
if heading not in text:
 text+='\n'+heading+'\n\nThe final checkpoint exports a [readable final-stage inventory](/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-conversation-data/reports/cast-complete-inventory.md) and [full receipt/source inventory](/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-conversation-data/reports/cast-complete-inventory.json). Registered native artwork stays outside Git. Source/proposal distinctions, age evidence and unknown historical measurements remain explicit. These inventories document drafts and agent QA, not personal Miguel approval, reference selection or publication.\n\nNative image inputs are capped at five using saved toolchain policy: current verified solo/identity first, needed counterpart identities, then layout/style/context. Omitted bibliography remains recorded. Fresh context supplies the policy and persistent stage/reference bindings; it never relies on prior chat memory. Notetaker remains unavailable; Markdown is the truthful fallback.\n'
doc.write_text(text)
store=Store(D);state=store.read();project=state['project'];binding=project['book']['characterReferenceDefaults']['characters']['tarin']
note=' The final human study retains a generated carved walking staff as a proposed prop, absent from inspected original portraits; it is not asserted as manuscript canon.'
if note not in binding['designBasis']:binding['designBasis']+=note
store.save_project(project,expected_revision=state['revision'])
ep=D/'workflows/characters/tarin/evidence.json';e=json.loads(ep.read_text());e['referenceBindings']=binding;atomic_json(ep,e)
runpath=D/'workflows/cast-run.json';run=json.loads(runpath.read_text());next(r for r in run['characters'] if r['id']=='tarin')['referenceBindings']=binding;atomic_json(runpath,run)
# Coordinator checkpoints exact authored tests/docs, never images or mutable kernel.
source=D/'tools/test_cast_closeout.py';(D/'exports/test_cast_closeout.py').write_bytes(source.read_bytes())
paths=[guide,doc,source,D/'exports/test_cast_closeout.py',D/'exports/test_business_routes.py',D/'tools/cast_ops.py',D/'tools/verify-cast-active.py',D/'workflows/toolchain.json']
atomic_json(D/'exports/final-cast-source-receipt.json',{'files':[{'path':str(p.relative_to(D)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths],'imageBinariesIncluded':False,'approvalInvented':False})
print(json.dumps({'preparedFiles':len(paths),'guideBytes':guide.stat().st_size,'readback':'Consolidated existing checkpoint operation after final images'}))
