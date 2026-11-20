"""Unresolved flags by review severity, safely escaped in HTML."""
import html
import json
from pathlib import Path
from .triage import classify, summarize, SEVERITY_ORDER

def collect(store):
    problems=[];total=0
    for s in store.sources():
        if s['state']!='active' or s['last_parsed_hash']!=s['sha256']: continue
        for p in store.pages(s['source_id']):
            total+=1
            flags=json.loads(p['flags'])
            if flags:
                problems.append({'source_id':s['source_id'],'source':s['relative_path'],'page':p['page_no'],
                                 'flags':flags,'severity':classify(flags)})
    problems.sort(key=lambda x: (SEVERITY_ORDER[x['severity']],x['source'],x['page']))
    return total, problems

def write_report(store,destination:Path)->dict:
    total,problems=collect(store)
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    severity_counts=summarize(problems)
    report={'total_pages':total,'flagged_pages':len(problems),'by_severity':severity_counts,
            'unresolved':problems,'ready_for_unqualified_use':False,
            'note':'No flags is not proof of visual, mathematical, or RTL fidelity.'}
    (destination/'QUALITY_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    rows=''.join('<tr><td>'+html.escape(x['severity'])+'</td><td>'+html.escape(x['source'])+'</td><td>'+str(x['page'])+'</td><td>'+html.escape(', '.join(x['flags']))+'</td></tr>' for x in problems)
    markup=(f'<!doctype html><html><head><meta charset="utf-8"><title>Extraction QA</title>'
            '<style>body{font:16px system-ui;max-width:1200px;margin:2rem auto}'
            'td,th{border:1px solid #ccc;padding:.5rem}table{border-collapse:collapse}</style>'
            f'</head><body><h1>Extraction QA</h1><p>Pages: {total}; flagged: {len(problems)}. '
            'Unflagged pages are not guaranteed accurate.</p>'
            f'<p>Review priority: {html.escape(json.dumps(severity_counts))}</p>'
            '<table><tr><th>Severity</th><th>Original source</th><th>Page</th><th>Flags</th></tr>'
            f'{rows}</table></body></html>')
    (destination/'QUALITY_REPORT.html').write_text(markup,encoding='utf-8')
    return {'total_pages':total,'flagged_pages':len(problems),'by_severity':severity_counts}
