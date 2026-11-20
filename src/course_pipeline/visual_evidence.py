"""Generate a locally inspectable evidence pack without making verification claims."""
from __future__ import annotations
from pathlib import Path
import json
import html
import re
from .core import Store
from .quality_report import collect

NUMBER_RE = re.compile(r'(?<!\w)\d+(?:[.,]\d+)*(?!\w)')


def build_visual_evidence(store: Store, source_dir: Path, destination: Path,
                          *, severity: str='critical', limit: int=30,
                          scale: float=1.6) -> dict:
    if severity not in {'critical','major','minor','informational','all'}:
        raise ValueError('Invalid severity')
    if not 1<=limit<=500: raise ValueError('Limit must be 1..500')
    if not .5<=scale<=3.0: raise ValueError('Scale must be 0.5..3.0')
    import pymupdf
    source_dir=Path(source_dir).resolve();destination=Path(destination).resolve()
    if not source_dir.is_dir(): raise NotADirectoryError(source_dir)
    destination.mkdir(parents=True,exist_ok=True)
    _,all_problems=collect(store)
    chosen=[e for e in all_problems if severity=='all' or e['severity']==severity][:limit]
    index=[]
    docs={}
    try:
        for entry in chosen:
            source=(source_dir/entry['source']).resolve()
            if not source.is_relative_to(source_dir) or not source.is_file():
                raise FileNotFoundError(f'Source missing/outside root: {entry["source"]}')
            if source.suffix.lower()!='.pdf':
                continue
            if source not in docs: docs[source]=pymupdf.open(source)
            doc=docs[source]
            n=int(entry['page'])
            if not 1<=n<=len(doc): raise ValueError('Review page outside PDF')
            img_name=f"{entry['source_id']}_{n:04d}.png"
            page=doc[n-1]
            page.get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=False).save(destination/img_name)
            raw=page.get_text(sort=False)
            row=store.conn.execute('SELECT body FROM pages WHERE source_id=? AND page_no=?',
                                   (entry['source_id'],n)).fetchone()
            if row is None: raise ValueError('Review page missing from database')
            body=row['body']
            # Extract only the Docling segment: never treat secondary fallback as Docling.
            primary=body.split('[SECONDARY PYMUPDF EXTRACTION',1)[0]
            primary=primary.replace('[DOCLING EXTRACTION — UNVERIFIED]','').strip()
            native_numbers=set(NUMBER_RE.findall(raw))
            primary_numbers=set(NUMBER_RE.findall(primary))
            record={**entry,'image':img_name,'status':'unreviewed',
                    'native_text_chars':len(raw),'primary_chars':len(primary),
                    'numbers_in_native_not_primary':sorted(native_numbers-primary_numbers),
                    'note':'Native PDF text is a diagnostic, not visual ground truth.'}
            base=Path(img_name).stem
            (destination/f'{base}_native.txt').write_text(raw,encoding='utf-8')
            (destination/f'{base}_extracted.txt').write_text(body,encoding='utf-8')
            (destination/f'{base}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
            index.append(record)
    finally:
        for doc in docs.values():doc.close()
    (destination/'review_queue.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
    fragments=[]
    for record in index:
        fragments.append('<section><h2>'+html.escape(record['source'])+' — page '+str(record['page'])+'</h2>'
             '<p><strong>Unreviewed.</strong> Candidate numbers found in PDF native text but not the primary extraction: '
             +html.escape(', '.join(record['numbers_in_native_not_primary']))+'</p>'
             +'<img loading="lazy" src="'+html.escape(record['image'],quote=True)+'" alt="original PDF page">'
             +'</section>')
    web_page=('<!doctype html><html><head><meta charset="utf-8"><title>Review original PDF pages</title>'
              '<style>body{font:16px system-ui;max-width:1150px;margin:2rem auto}'
              'section{padding:1.5rem;border:1px solid #ccc;margin:1.5rem 0;border-radius:10px}'
              'img{max-width:100%}</style></head><body><h1>Visual evidence review</h1>'
              '<p>Every item is unreviewed. Compare extracted text, numbers, tables and figure labels with the image.</p>'
              +''.join(fragments)+'</body></html>')
    (destination/'INDEX.html').write_text(web_page,encoding='utf-8')
    return {'items':len(index),'severity':severity,'directory':str(destination),
            'reviewed':0,'status':'review_required'}
