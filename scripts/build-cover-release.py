#!/usr/bin/env python3
"""Build the verified public baseline with only approved chapter-cover/catalog changes."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
for n in ['baseline','baseline-manifest','build-root','dest','proof']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads(a.baseline_manifest.read_text());expected={x['path']:x for x in old['files']}
assert not a.build_root.exists() and not a.dest.exists()
assert {p.relative_to(a.baseline).as_posix()for p in a.baseline.rglob('*')if p.is_file()}==set(expected)
for rel,e in expected.items():
 f=a.baseline/rel;assert not f.is_symlink() and f.stat().st_size==e['bytes'] and sha(f)==e['sha256'],rel
overlay=['storyboard/standalone-stories.js', 'storyboard/title-covers.js', 'storyboard/index.html', 'storyboard/atlas.html', 'storyboard/atlas-webgpu.html']+['storyboard/stories/bath-magic.json','storyboard/covers.json','storyboard/library-pdfs.json']+['storyboard/images/published/bath-magic/title-'+l+'-v2.webp' for l in ['en','ru','es']]
shutil.copytree(a.baseline,a.build_root/'docs')
for rel in overlay:
 src=root/'docs'/rel;assert src.is_file() and not src.is_symlink()
 dst=a.build_root/'docs'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
(a.build_root/'assets').mkdir()
shutil.copy2(root/'assets/manifest.json',a.build_root/'assets/manifest.json')
res=subprocess.run(['/opt/homebrew/bin/node',str(root/'tools/assets/build-pages.cjs'),'--root',str(a.build_root),'--dest',str(a.dest)],check=True,capture_output=True,text=True)
final={p.relative_to(a.dest).as_posix():sha(p)for p in a.dest.rglob('*')if p.is_file()}
assert not set(expected)-set(final)
changed=sorted(p for p in expected if final[p]!=expected[p]['sha256']);added=sorted(set(final)-set(expected))
assert set(changed+added)==set(overlay),(changed,added)
assert all(final[p]==e['sha256']for p,e in expected.items()if p not in overlay)
proof={'baselineManifestSha256':sha(a.baseline_manifest),'baselineSourceCommit':old['source_commit'],'changedPublishedFiles':changed,'addedFiles':added,'removedFiles':[],'allOtherPublishedFilesByteIdentical':True,'all138NarrativeImagesUnchanged':True,'miniatureUnchanged':True,'overlay':overlay,'build':json.loads(res.stdout)}
a.proof.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
