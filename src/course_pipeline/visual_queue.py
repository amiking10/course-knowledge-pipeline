"""Opt-in visual-review queue. No AI assertion is marked reviewed automatically."""
from __future__ import annotations
import json
from pathlib import Path
from .core import Store


def build_queue(store: Store, directory: Path, source_root: Path,
                *, render: bool=False, limit: int|None=None) -> dict:
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    records=[]
    from .visuals import render_review
    for source in store.sources():
        if source['state']!='active' or source['last_parsed_hash']!=source['sha256']:
            continue
        pdf=Path(source_root)/source['relative_path']
        for page in store.pages(source['source_id']):
            flags=json.loads(page['flags'])
            if not flags:continue
            identifier=f"{source['source_id']}_{page['page_no']:04d}"
            record={'source_id':source['source_id'],'source':source['relative_path'],
                    'page':page['page_no'],'flags':flags,'reviewed':False,'image':None}
            if render and pdf.suffix.lower()=='.pdf':
                render_review(pdf,[page['page_no']],directory/identifier)
                record['image']=f"{identifier}/page-{page['page_no']:04d}.png"
            records.append(record)
            if limit is not None and len(records)>=limit:break
        if limit is not None and len(records)>=limit:break
    (directory/'review_queue.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'items':len(records),'queue':str(directory/'review_queue.json')}
