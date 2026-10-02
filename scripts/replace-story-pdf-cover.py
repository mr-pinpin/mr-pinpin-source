#!/usr/bin/env python3
"""Replace only a registered chapter's illustrated PDF cover; verify every interior page."""
import argparse, hashlib, io, json
from pathlib import Path
import fitz
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
p=argparse.ArgumentParser()
p.add_argument('--root',required=True,type=Path)
p.add_argument('--base-pdfs',required=True,type=Path)
p.add_argument('--out',required=True,type=Path)
p.add_argument('--story',default='bath-magic')
p.add_argument('--languages',nargs='+',choices=['en','ru','es'],default=['en','ru','es'])
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
sb=a.root/'docs/storyboard';story=json.loads((sb/'stories'/f'{a.story}.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pdfmetrics.registerFont(TTFont('CoverGeorgia','/System/Library/Fonts/Supplemental/Georgia.ttf'))
proof={'schemaVersion':1,'storyId':a.story,'method':'New illustrated cover, original pages2–142 copied without rerendering or text changes','pdfs':[]}
for lang in a.languages:
 old=a.base_pdfs/f'{a.story}-{lang}.pdf';cover=sb/story['cover'][lang]
 base=fitz.open(old);assert len(base)==142
 im=Image.open(cover).convert('RGB');w=A4[0];h=w*im.height/im.width
 buf=io.BytesIO();cc=canvas.Canvas(buf,pagesize=(w,h),pageCompression=1)
 cc.drawImage(ImageReader(im),0,0,w,h)
 t=cc.beginText(12,h-20);t.setFont('CoverGeorgia',8);t.setTextRenderMode(3);t.textLine(story['title'][lang]);cc.drawText(t)
 cc.showPage();cc.save()
 first=fitz.open(stream=buf.getvalue(),filetype='pdf')
 result=fitz.open();result.insert_pdf(first);result.insert_pdf(base,from_page=1,to_page=len(base)-1)
 result.set_metadata(base.metadata)
 dest=a.out/old.name;assert not dest.exists(),dest
 result.save(dest,garbage=0,deflate=False);result.close()
 test=fitz.open(dest);assert len(test)==142
 pages=[]
 for n in range(1,len(base)):
  assert tuple(base[n].rect)==tuple(test[n].rect)
  assert base[n].get_text()==test[n].get_text(),(lang,n,'text changed')
  before=base[n].get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
  after=test[n].get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
  bh=hashlib.sha256(before.samples).hexdigest();ah=hashlib.sha256(after.samples).hexdigest()
  assert bh==ah,(lang,n,'render changed')
  pages.append({'page':n+1,'renderSha256At72dpi':bh,'textIdentical':True,'dimensionsIdentical':True})
 assert story['title'][lang] in test[0].get_text()
 test[0].get_pixmap(matrix=fitz.Matrix(1,1),alpha=False).save(a.out/f'cover-{lang}.png')
 row={'lang':lang,'filename':dest.name,'file':str(dest),'bytes':dest.stat().st_size,'sha256':sha(dest),'pageCount':142,'storyPageCount':139,'coloringPageCount':3,'basePdf':str(old),'baseSha256':sha(old),'cover':str(cover),'coverSha256':sha(cover),'coverAspectRatio':im.width/im.height,'interiorPagesIdentical':True,'checkedPages':pages}
 proof['pdfs'].append(row)
 print('PASS',lang,'141 interior pages pixel/text identical',row['sha256'],flush=True)
proof['pass']=True;(a.out/'export-manifest.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
