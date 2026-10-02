#!/usr/bin/env python3
"""Export one registered chapter plus three coloring pages; preserve existing editions."""
import argparse, hashlib, io, json, re, unicodedata
from pathlib import Path
from PIL import Image
import fitz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from xml.sax.saxutils import escape
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);p.add_argument('--story',default='bath-magic');a=p.parse_args()
root=Path(a.root);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
sb=root/'docs/storyboard';model=json.loads((sb/'stories'/f'{a.story}.json').read_text())
assert len(model['scenes'])==139
prefix=sb/'images/published'/a.story
pack=out.parent
cache=out/'jpeg-cache';cache.mkdir(exist_ok=True)
pdfmetrics.registerFont(TTFont('BookGeorgia','/System/Library/Fonts/Supplemental/Georgia.ttf'))
pdfmetrics.registerFont(TTFont('BookGeorgiaBold','/System/Library/Fonts/Supplemental/Georgia Bold.ttf'))
style=ParagraphStyle('story',fontName='BookGeorgia',fontSize=17,leading=17*1.36,textColor='#282519',spaceAfter=2.4*mm)
titleStyle=ParagraphStyle('title',fontName='BookGeorgiaBold',fontSize=31,leading=39,alignment=1,textColor='#523316')
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
report={'schemaVersion':1,'storyId':a.story,'storyPageCount':139,'coloringPageCount':3,'pageCount':142,
 'renderer':'ReportLab','verification':'PyMuPDF text/page/image checks','font':'Embedded Georgia/Georgia Bold with Cyrillic',
 'layout':{'story':'A4 landscape','cover':'A4 portrait','coloring':'A4 portrait','marginMm':12,'prosePt':17,'leading':23.12},
 'encoding':{'storyArt':'JPEG quality92 native dimensions; originals unchanged','cover':'approved art intact within typeset portrait page','coloring':'native PNG embedded'},
 'artwork':[],'covers':[],'pdfs':[]}
artCache={}
def art(src):
 if src not in artCache:
  f=sb/src;assert f.is_file(),f
  im=Image.open(f).convert('RGB');dest=cache/(sha(f)+'.jpg')
  if not dest.exists():im.save(dest,'JPEG',quality=92,subsampling=0)
  assert Image.open(dest).size==im.size
  report['artwork'].append({'source':src,'sourceSha256':sha(f),'sourceBytes':f.stat().st_size,'jpeg':str(dest),'dimensions':list(im.size)})
  artCache[src]=(dest,im.size)
 return artCache[src]
def fitted(c,src,rect):
 im=Image.open(src);iw,ih=im.size;x,y,w,h=rect;s=min(w/iw,h/ih);c.drawImage(str(src),x+(w-iw*s)/2,y+(h-ih*s)/2,iw*s,ih*s,mask='auto')
def cover(c,lang):
 w,h=A4;c.setPageSize(A4);c.setFillColorRGB(0.99,0.967,0.92);c.rect(0,0,w,h,fill=1,stroke=0)
 title=Paragraph(escape(model['title'][lang]),titleStyle);tw,th=title.wrap(w-28*mm,80*mm)
 assert th<80*mm;title.drawOn(c,14*mm,h-29*mm-th)
 # Intact landscape approved artwork: contain, no crop or AI edits.
 fitted(c,prefix/'approved-title-art.webp',(12*mm,70*mm,w-24*mm,135*mm))
 c.setStrokeColorRGB(.69,.48,.20);c.setLineWidth(.7);c.line(62*mm,55*mm,w-62*mm,55*mm)
 c.setFont('BookGeorgia',14);c.setFillColorRGB(.32,.20,.10);c.drawCentredString(w/2,41*mm,{'en':'Mr. PinPin','ru':'Мистер Пин-Пин','es':'El señor PinPin'}[lang])
 c.showPage()
for lang in ['en','ru','es']:
 cov=out/f'title-{lang}.pdf';cc=canvas.Canvas(str(cov),pagesize=A4,pageCompression=1);cover(cc,lang);cc.save()
 d=fitz.open(cov);pix=d[0].get_pixmap(matrix=fitz.Matrix(1024/A4[0],1536/A4[1]),alpha=False)
 # Page-card raster, not alteration of illustration: approved artwork remains intact within layout.
 png=pack/'web'/f'title-{lang}.png';pix.save(png)
 im=Image.open(png).convert('RGB');assert im.size==(1024,1536),im.size
 web=prefix/f'title-{lang}.webp';im.save(web,'WEBP',quality=94,method=6)
 report['covers'].append({'lang':lang,'path':str(web.relative_to(root)),'sha256':sha(web),'approvedArtSha256':sha(prefix/'approved-title-art.webp'),'derivation':'Localized vector typography and intact approved landscape artwork composed on portrait page; no artwork repaint/crop'})
 file=out/f'{a.story}-{lang}.pdf';c=canvas.Canvas(str(file),pagesize=A4,pageCompression=1)
 c.setTitle(model['title'][lang]);c.setAuthor('Mr. PinPin');cover(c,lang)
 for scene in model['scenes'][1:]:
  w,h=landscape(A4);c.setPageSize((w,h));margin=12*mm;aw=w-2*margin
  paras=[Paragraph(escape(t),style) for t in scene['paragraphs'][lang]]
  heights=[x.wrap(aw,h)[1] for x in paras];textHeight=sum(heights)+max(0,len(paras)-1)*2.4*mm
  artBottom=margin+textHeight+(5*mm if paras else 0);artH=h-margin-artBottom
  assert artH>105*mm,(scene['id'],artH)
  source=scene.get('images',{}).get(lang) or scene['image'];img,_=art(source);fitted(c,img,(margin,artBottom,aw,artH))
  y=margin+textHeight
  for para,ph in zip(paras,heights):y-=ph;para.drawOn(c,margin,y);y-=2.4*mm
  c.showPage()
 for id in ['coloring-title','coloring-ride','coloring-build']:
  c.setPageSize(A4);w,h=A4;fitted(c,pack/'masters'/f'{id}-v1.png',(12*mm,12*mm,w-24*mm,h-24*mm));c.showPage()
 c.save()
 d=fitz.open(file);assert len(d)==142
 norm=lambda s:re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s)).strip()
 for n,s in enumerate(model['scenes'][1:],1):
  text=norm(d[n].get_text())
  for para in s['paragraphs'][lang]:assert norm(para) in text,(lang,s['id'],'missing selectable text')
  assert len(d[n].get_images())>=1
 for n in range(139,142):assert len(d[n].get_images())==1
 assert norm(model['title'][lang]) in norm(d[0].get_text())
 longest=max(range(1,139),key=lambda n:sum(map(len,model['scenes'][n]['paragraphs'][lang])))
 for n in [0,1,longest,138,139,140,141]:
  d[n].get_pixmap(matrix=fitz.Matrix(1,1)).save(pack/'screenshots'/f'{lang}-page-{n+1:03}.png')
 entry={'id':a.story,'lang':lang,'filename':file.name,'file':str(file),'bytes':file.stat().st_size,'sha256':sha(file),'pageCount':142,'storyPageCount':139,'coloringPageCount':3,'allParagraphsSelectable':True,'layoutChecked':True}
 report['pdfs'].append(entry);print('PASS',file.name,'142 pages',entry['bytes'],flush=True)
report['pass']=True;(out/'export-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
