"""Diagnostic contact sheets only; native illustrations remain untouched."""
import argparse,json,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--start',type=int,required=True);p.add_argument('--end',type=int,required=True);p.add_argument('--out',required=True);a=p.parse_args()
pack=Path(__file__).resolve().parent;root=pack.parents[3];out=Path(a.out).resolve();assert not out.is_relative_to(root),'Review outputs must stay outside checkout';out.mkdir(parents=True,exist_ok=True)
script=json.loads((pack/'script/story-script.json').read_text());records=json.loads((pack/'generation-records.json').read_text());selected=json.loads((pack/'working-selection.json').read_text())['selected'];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
scenes=[s for s in script['scenes'] if a.start<=s['number']<=a.end]
for offset in range(0,len(scenes),12):
 board=Image.new('RGB',(1536,4*430),'#f8f4e9');draw=ImageDraw.Draw(board)
 for i,s in enumerate(scenes[offset:offset+12]):
  n=s['number'];id=selected.get(f'{n:03}');matches=[r for r in records if r['id'].startswith(f'r6-{n:03}-')]
  if id:source=pack/'native'/f'{id}.png'
  elif matches:source=root/matches[-1]['nativePath'];id=matches[-1]['id']
  elif s.get('reusedEnvironmentNative'):source=pack/s['reusedEnvironmentNative'];id='environment POV'
  elif s.get('reusedApprovedImage'):source=root/'docs/storyboard'/s['reusedApprovedImage'];id='approved existing image'
  else:source=None;id='MISSING'
  x=(i%3)*512;y=(i//3)*430
  if source and source.exists():
   with Image.open(source) as image:
    image=image.convert('RGB');image.thumbnail((506,338));board.paste(image,(x+3,y+3))
  draw.text((x+5,y+342),f'{n:03} / {s["location"]} / {id}',font=font,fill='black')
  caption=' '.join(s['narration']['en']);draw.multiline_text((x+5,y+363),'\n'.join(textwrap.wrap(caption,65)[:3]),font=font,fill='black',spacing=3)
 name=f'board-{scenes[offset]["number"]:03}-{scenes[min(offset+11,len(scenes)-1)]["number"]:03}.jpg';board.save(out/name,quality=92);print(out/name)
