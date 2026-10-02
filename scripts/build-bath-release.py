#!/usr/bin/env python3
"""Build only the verified published baseline plus the approved bath overlay."""
from pathlib import Path
import argparse,json,hashlib,shutil,subprocess
a=argparse.ArgumentParser();a.add_argument('--baseline',type=Path,required=True);a.add_argument('--baseline-manifest',type=Path,required=True);a.add_argument('--build-root',type=Path,required=True);a.add_argument('--dest',type=Path,required=True);a.add_argument('--proof',type=Path,required=True);args=a.parse_args()
root=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads(args.baseline_manifest.read_text())
assert not args.build_root.exists() and not args.dest.exists()
expected={x['path']:x for x in old['files']}
assert {p.relative_to(args.baseline).as_posix()for p in args.baseline.rglob('*')if p.is_file()}==set(expected)
for rel,item in expected.items():
 p=args.baseline/rel;assert not p.is_symlink() and p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],rel
shutil.copytree(args.baseline,args.build_root/'docs')
overlay=['storyboard/standalone-stories.js','storyboard/stories/bath-magic.json','storyboard/covers.json','storyboard/title-covers.js','storyboard/reader.js','storyboard/reader-navigation.css','storyboard/index.html','storyboard/atlas-webgpu.html','storyboard/atlas.html','storyboard/library.html','storyboard/atlas-stories.js','storyboard/atlas-preview.js','storyboard/atlas.css','storyboard/atlas-webgpu.js','storyboard/library-pdfs.json']
manifest=json.loads((root/'assets/manifest.json').read_text())
overlay += [x['path'][5:]for x in manifest['assets']if x['role']=='production' and x['path'].startswith('docs/storyboard/images/published/bath-magic/')]
identities=[]
for rel in overlay:
 source=root/'docs'/rel;target=args.build_root/'docs'/rel
 assert source.is_file() and not source.is_symlink(),rel
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 identities.append({'path':rel,'sha256':sha(source),'bytes':source.stat().st_size})
(args.build_root/'assets').mkdir();shutil.copy2(root/'assets/manifest.json',args.build_root/'assets/manifest.json')
result=subprocess.run(['/opt/homebrew/bin/node',str(root/'tools/assets/build-pages.cjs'),'--root',str(args.build_root),'--dest',str(args.dest)],check=True,capture_output=True,text=True);print(result.stdout)
final={p.relative_to(args.dest).as_posix():sha(p)for p in args.dest.rglob('*')if p.is_file()}
assert not set(expected)-set(final),'Published files removed'
changed=[p for p in expected if expected[p]['sha256']!=final[p]]
added=sorted(set(final)-set(expected))
assert set(changed+added)<=set(overlay)
proof={'baselineManifestSha256':sha(args.baseline_manifest),'baselineSourceCommit':old['source_commit'],'sourceOverlay':identities,'allUnchangedPublishedFilesByteIdentical':True,'publishedFilesRemoved':[],'changedPublishedFiles':sorted(changed),'addedFiles':added,'build':json.loads(result.stdout)}
args.proof.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'changed':len(changed),'added':len(added),'removed':0,'bytes':proof['build']['bytes']}))
