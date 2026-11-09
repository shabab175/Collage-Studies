from pathlib import Path
from urllib.parse import quote
import json,re,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader
for label,file in [('Study','DejaVuSans.ttf'),('Study-Bold','DejaVuSans-Bold.ttf'),('Study-Italic','DejaVuSans-Oblique.ttf'),('Study-BoldItalic','DejaVuSans-BoldOblique.ttf')]:
 pdfmetrics.registerFont(TTFont(label,'/usr/share/fonts/truetype/dejavu/'+file))
pdfmetrics.registerFontFamily('Study',normal='Study',bold='Study-Bold',italic='Study-Italic',boldItalic='Study-BoldItalic')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyStudy',fontName='Study',fontSize=10.2,leading=15.2,spaceAfter=7,textColor=colors.HexColor('#243248')))
styles.add(ParagraphStyle(name='TitleStudy',fontName='Study-Bold',fontSize=21,leading=27,spaceAfter=12,textColor=colors.HexColor('#123650')))
styles.add(ParagraphStyle(name='H2Study',fontName='Study-Bold',fontSize=13.2,leading=18,spaceBefore=14,spaceAfter=8,keepWithNext=True,textColor=colors.HexColor('#156478')))
styles.add(ParagraphStyle(name='H3Study',fontName='Study-Bold',fontSize=10.8,leading=15.5,spaceBefore=9,spaceAfter=5,keepWithNext=True,textColor=colors.HexColor('#123650')))
styles.add(ParagraphStyle(name='SmallStudy',parent=styles['BodyStudy'],fontSize=8.5,leading=12,textColor=colors.HexColor('#526477')))
styles.add(ParagraphStyle(name='BulletStudy',parent=styles['BodyStudy'],leftIndent=11,firstLineIndent=-9))
styles.add(ParagraphStyle(name='CellStudy',parent=styles['BodyStudy'],fontSize=8.5,leading=12,spaceAfter=2))
def inline(s):
 s=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',s)
 s=html.escape(s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
 s=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<i>\1</i>',s)
 return s

def parse(md):
 flow=[];para=[];lines=md.splitlines();i=0
 def flush():
  if para: flow.append(Paragraph(inline(' '.join(para)),styles['BodyStudy']));para.clear()
 while i<len(lines):
  line=lines[i].strip()
  if not line:flush();i+=1;continue
  if line.startswith('|'):
   flush();rows=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    row=[x.strip() for x in lines[i].strip().strip('|').split('|')]
    if not all(re.fullmatch(r'[: -]+',x) for x in row):rows.append(row)
    i+=1
   cols=max(map(len,rows));data=[]
   for ri,row in enumerate(rows):
    data.append([Paragraph(('<b>'+inline(c)+'</b>') if ri==0 else inline(c),styles['CellStudy']) for c in row]+['']*(cols-len(row)))
   table=Table(data,colWidths=[(A4[0]-102)/cols]*cols,repeatRows=1,hAlign='LEFT')
   table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f0f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cad7df')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
   flow.extend([table,Spacer(1,8)]);continue
  if line.startswith('### '):flush();flow.append(Paragraph(inline(line[4:]),styles['H3Study']))
  elif line.startswith('## '):flush();flow.append(Paragraph(inline(line[3:]),styles['H2Study']))
  elif re.match(r'^(- |\d+\. )',line):
   flush();line=re.sub(r'^- ','• ',line);flow.append(Paragraph(inline(line),styles['BulletStudy']))
  else:para.append(line)
  i+=1
 flush();return flow

# Rebuild from editable Markdown files next to this script. Requires reportlab and pypdf.
root=Path(__file__).resolve().parent
results=[]
for source in sorted((root/'expanded sources').glob('Block*.md')):
 text=source.read_text()
 title=text.splitlines()[0][2:].replace(' — Expanded Exam Notes','')
 body=text.split('<!-- CONTENT -->',1)[1]
 target=root/source.with_suffix('.pdf').name
 story=[Paragraph('MA ENGLISH • SEMESTER 1',styles['SmallStudy']),Paragraph(inline(title),styles['TitleStudy']),Paragraph('MILTON TO THE PRE-ROMANTICS • M21EG03DC',styles['SmallStudy']),Paragraph('Expanded exam notes | Simple teaching + developed argument',styles['BodyStudy']),Paragraph('Based on the supplied SGOU self-learning material. Use the assigned primary texts for exact quotations and full scene or passage analysis.',styles['SmallStudy']),Spacer(1,9)]+parse(body)
 short=' • '.join(source.stem.split(' - ')[:2])
 def decorate(canvas,doc,short=short):
  canvas.saveState();w,h=A4
  canvas.setStrokeColor(colors.HexColor('#cad7df'));canvas.line(51,h-39,w-51,h-39);canvas.line(51,42,w-51,42)
  canvas.setFont('Study',7.5);canvas.setFillColor(colors.HexColor('#526477'))
  canvas.drawString(51,h-30,'Milton to the Pre-Romantics | Expanded exam notes')
  canvas.drawString(51,29,short);canvas.drawRightString(w-51,29,f'Page {doc.page}');canvas.restoreState()
 doc=SimpleDocTemplate(str(target),pagesize=A4,rightMargin=51,leftMargin=51,topMargin=53,bottomMargin=57,title=title+' - Expanded Exam Notes',author='Study Notes',allowSplitting=True)
 doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
 reader=PdfReader(target)
 extracted='\n'.join(page.extract_text() or '' for page in reader.pages)
 for marker in ['Developed exam discussion','Textbook assignment checklist','Common mistake to avoid']:
  assert marker in extracted,(target,marker)
 assert all((page.extract_text() or '').strip() for page in reader.pages),target
 results.append({'name':target.name,'pages':len(reader.pages),'words':len(body.split())})
 print(f'{len(reader.pages)} pages | {len(body.split())} words | {target.name}')
(root/'build-summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
