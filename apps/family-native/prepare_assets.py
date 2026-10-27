#!/usr/bin/env python3
"""Verify existing artwork and export lossless RGBA bytes outside the checkout.

Requires Pillow in the build environment. No resizing, repainting or source writes.
Creative inputs retain their existing permissions; this conversion grants no rights.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    spec = json.loads((here / 'inputs.json').read_text())
    # Verify every original before writing any derivative.
    sources = []
    for item in spec['assets']:
        path = args.asset_root / item['source']
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise SystemExit(f'Input checksum mismatch: {item["source"]}')
        image = Image.open(path)
        image.load()
        if list(image.size) != item['size']:
            raise SystemExit(f'Input dimensions mismatch: {item["source"]}')
        sources.append((item, image))
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for item, image in sources:
        raw = image.convert('RGBA').tobytes()
        (args.output / item['output']).write_bytes(raw)
        records.append(dict(item, derivativeSha256=hashlib.sha256(raw).hexdigest(), derivativeBytes=len(raw)))
    (args.output / 'provenance.json').write_text(json.dumps({'conversion':'Pillow RGBA conversion only; no resizing', 'inputs':records},indent=2)+'\n')
    print(f'Verified and exported {len(records)} existing images')


if __name__ == '__main__':
    main()
