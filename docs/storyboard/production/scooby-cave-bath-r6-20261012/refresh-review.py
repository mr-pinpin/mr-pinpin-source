"""Refresh working-only review and scoped restoration data from catalogued art."""
import json,html
from pathlib import Path
pack=Path(__file__).resolve().parent;root=pack.parents[3];records=json.loads((pack/'generation-records.json').read_text());manifest=json.loads((root/'assets/manifest.json').read_text());prefix=str(pack.relative_to(root))+'/'
scope={'version':1,'bucket':manifest['bucket'],'assets':[e for e in manifest['assets'] if e['path'].startswith(prefix+'native/')]}
(pack/'environment/asset-scope.json').write_text(json.dumps(scope,indent=2)+'\n')
page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Unpublished R6 working review</title><style>body{background:#20241e;color:#eee;font:16px system-ui;margin:24px}a{color:#aee0a9}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}article{background:#30382d;padding:12px;border-radius:8px}img{width:100%;height:auto}p{line-height:1.5}</style><h1>Unpublished Scooby R6 — working review</h1><p>Agent-reviewed art candidates, not the published chapter. <a href="top-down-map.html">Map</a> · <a href="../script/english-reading.md">Full English script</a></p><div class="grid">'
for r in records:
 if r['status'].startswith(('agent-reviewed','reviewed-environment')):
  i=html.escape(r['id']);page+=f'<article><h2>{i}</h2><a href="../native/{i}.png" target="_blank" rel="noopener"><img src="../native/{i}.png" loading="lazy" alt="{i} working candidate"></a><p>{html.escape(r["status"])}</p><p>{html.escape(r["review"])}</p></article>'
page+='</div></html>\n';(pack/'environment/review.html').write_text(page)
print('Working review:',len(records),'recorded outputs;',len(scope['assets']),'catalogued native files in restoration scope')
