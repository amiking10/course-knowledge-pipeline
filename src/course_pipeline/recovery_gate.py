"""Explicit regression gate for previously observed source-page omissions."""
from __future__ import annotations
import json
from pathlib import Path
from .core import Store


def validate_recovery(store: Store, target_file: Path) -> dict:
    entries=json.loads(Path(target_file).read_text(encoding='utf-8'))
    seen=set();cases=[]
    for entry in entries:
        source=entry['source']
        for page_no in entry['pages']:
            target=(source,int(page_no))
            if target in seen:raise ValueError(f'Duplicate target: {target}')
            seen.add(target)
            rows=store.conn.execute('''SELECT p.body, p.flags FROM pages p
              JOIN sources s ON s.source_id=p.source_id
              WHERE s.relative_path=? AND p.page_no=?
              AND s.state='active' AND s.last_parsed_hash=s.sha256''',target).fetchall()
            recovered=bool(rows and 'SECONDARY PYMUPDF EXTRACTION' in rows[0]['body'])
            cases.append({'source':source,'page':page_no,'secondary_text_present':recovered})
    successes=sum(c['secondary_text_present'] for c in cases)
    return {'targets':len(cases),'secondary_text_present':successes,
            'passed':bool(cases) and successes==len(cases),'cases':cases,
            'note':'Checks presence of fallback native text, NOT mathematical/visual correctness'}
