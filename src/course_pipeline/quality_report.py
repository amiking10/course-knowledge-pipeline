"""Auditable report of unresolved page flags with safe HTML escaping."""
import html
import json
from pathlib import Path
from .core import Store


def write_report(store: Store, destination: Path)->dict:
    problems=[];total=0
    for s in store.sources():
        if s['state']!='active' or s['last_parsed_hash']!=s['sha256']:continue
        for p in store.pages(s['source_id']):
            total+=1;flags=json.loads(p['flags'])
            if flags:problems.append({'source':s['relative_path'],'page':p['page_no'],'flags':flags})
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    report={'total_pages':total,'flagged_pages':len(problems),'unresolved':problems,
            'ready_for_unqualified_use':not problems and total>0}
    (destination/'QUALITY_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    rows=''.join('<tr><td>'+html.escape(x['source'])+'</td><td>'+str(x['page'])+'</td><td>'+html.escape(', '.join(x['flags']))+'</td></tr>' for x in problems)
    markup=f'''<!doctype html><html><head><meta charset="utf-8"><title>Extraction QA</title>
<style>body{{font:16px system-ui;max-width:1200px;margin:2rem auto}}td,th{{border:1px solid #ccc;padding:.5rem}}table{{border-collapse:collapse}}</style></head><body>
<h1>Extraction QA — review required</h1><p>Processed pages: {total}; flagged pages: {len(problems)}.
Flags are diagnostic and do not establish that other pages are accurate.</p>
<table><tr><th>Original source</th><th>Page</th><th>Unresolved flags</th></tr>{rows}</table></body></html>'''
    (destination/'QUALITY_REPORT.html').write_text(markup,encoding='utf-8')
    return {'total_pages':total,'flagged_pages':len(problems)}
