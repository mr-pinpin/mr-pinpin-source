#!/usr/bin/env python3
"""Lay out existing approved draft illustrations; no synthesis or retouching."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

parser = argparse.ArgumentParser()
parser.add_argument('--pack', type=Path, default=Path(__file__).resolve().parent)
parser.add_argument('--version',type=int,default=1)
args = parser.parse_args()
root = args.pack.resolve()
plan = json.loads((root / 'story-plan.json').read_text())
media = json.loads((root / 'media.json').read_text())
missing = [scene['id'] for scene in plan['scenes'] if scene['id'] not in media['images']]
if missing:
    raise SystemExit(f'All scenes must exist before making final contact sheets: {missing}')
font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
recipes=[]
def sheet(scenes, columns, width, slug):
    gutter = 18
    cell_width = (width - (columns + 1) * gutter) // columns
    cell_height = round(cell_width * 2 / 3)
    label_height = 44 if columns < 3 else 26
    rows = (len(scenes) + columns - 1) // columns
    canvas = Image.new('RGB', (width, gutter + rows*(cell_height+label_height+gutter)), '#fcf7eb')
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(font_path, 27 if columns < 3 else 18)
    for index, scene in enumerate(scenes):
        x = gutter + index % columns * (cell_width + gutter)
        y = gutter + index // columns * (cell_height + label_height + gutter)
        with Image.open(root / media['images'][scene['id']]['path']) as original:
            tile = ImageOps.contain(original.convert('RGB'), (cell_width, cell_height), Image.Resampling.LANCZOS)
            canvas.paste(tile, (x + (cell_width - tile.width)//2, y + (cell_height - tile.height)//2))
        draw.text((x, y+cell_height+4), f"{scene['number']:02}", font=font, fill='#443424')
    master = root / 'masters' / f'{slug}-v{args.version}.png'
    canvas.save(master)
    subprocess.run([sys.executable, str(root/'accept-asset.py'), '--pack', str(root), '--master', str(master), '--slug', slug], check=True)
    recipes.append({'id':slug,'master':master.relative_to(root).as_posix(),
                    'masterSha256':hashlib.sha256(master.read_bytes()).hexdigest(),
                    'columns':columns,'width':canvas.width,'height':canvas.height,'gutter':gutter,
                    'inputs':[{'scene':scene['id'],**media['images'][scene['id']]} for scene in scenes]})
sheet(plan['scenes'], 6, 2400, 'storyboard-00')
for start in range(0,len(plan['scenes']),6):
    sheet(plan['scenes'][start:start+6], 2, 1800, f'storyboard-{start//6+1:02}')
(root/'contact-sheets.json').write_text(json.dumps({'version':1,'operation':'layout-only','recipe':'contact-sheets.py',
    'recipeSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sheets':recipes},indent=2)+'\n')
subprocess.run([sys.executable,str(root/'refresh-media.py'),'--pack',str(root)],check=True)
print(json.dumps({'scenes':len(plan['scenes']), 'sheets':7,'operation':'deterministic layout of existing images','artEdited':False}))
