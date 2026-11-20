"""Prioritized review queue. Notes are never auto-verified."""
import json
from pathlib import Path
from .quality_report import collect

def build_queue(store,directory:Path,source_root:Path,*,render:bool=False,limit:int|None=None)->dict:
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    from .visuals import render_review
    _,problems=collect(store)
    records=[]
    for entry in problems[:limit]:
        pdf=Path(source_root)/entry['source']
        record={**entry,'reviewed':False,'image':None}
        if render and pdf.suffix.lower()=='.pdf':
            folder=directory/(pdf.stem+'_'+str(entry['page']))
            render_review(pdf,[entry['page']],folder)
            record['image']=str(folder.relative_to(directory)/(f"page-{entry['page']:04d}.png"))
        records.append(record)
    (directory/'review_queue.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'items':len(records),'queue':str(directory/'review_queue.json')}
