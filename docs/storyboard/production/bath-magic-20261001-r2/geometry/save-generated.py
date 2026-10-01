"""Preserve a completed built-in tool output. Never calls an image API."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess
import sys

production = Path(__file__).resolve().parents[1]
pack = Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r2')
stem, source = sys.argv[1], Path(sys.argv[2])
target = pack / 'masters' / (stem + '.png')
if target.exists():
    raise SystemExit('Refusing to overwrite existing master ' + str(target))
shutil.copy2(source, target)
for directory in ['prompts', 'records']:
    (pack / directory).mkdir(exist_ok=True)
shutil.copy2(production / 'prompts' / (stem + '.txt'), pack / 'prompts' / (stem + '.txt'))
record = json.loads((production / 'records' / (stem + '-request.json')).read_text())
record.update(tool='image_gen__imagegen', generatedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              sourceOutputPath=str(source), savedOriginalPath=str(target),
              imageSha256=hashlib.sha256(target.read_bytes()).hexdigest(),
              promptSha256=hashlib.sha256(record['prompt'].encode()).hexdigest(),
              reviewStatus='generated draft; not user approved')
record_path = production / 'records' / (stem + '.json')
record_path.write_text(json.dumps(record, indent=2) + '\n')
shutil.copy2(record_path, pack / 'records' / record_path.name)
slug = '-'.join(stem.split('-')[:2])
subprocess.run(['ssh', 'mini', str(pack / '.venv/bin/python'), str(pack / 'accept-asset.py'),
                '--master', str(target), '--slug', slug,
                '--prompt', str(pack / 'prompts' / (stem + '.txt')), '--generation-record', str(pack / 'records' / (stem + '.json'))], check=True)
print(json.dumps({'saved': str(target), 'slug': slug}))
