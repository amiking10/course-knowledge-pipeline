"""Unresolved flags by review severity, safely escaped in HTML."""
import html
import json
from collections import Counter
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
    flag_counts=dict(sorted(Counter(flag for page in problems for flag in page['flags']).items()))
    action_required=[p for p in problems if p['severity'] in ('critical','major')]
    advisory=[p for p in problems if p['severity'] in ('minor','informational')]
    summary={'action_required_pages':len(action_required),'advisory_pages':len(advisory),
             'highest_priority':[{k:v for k,v in p.items() if k in ('source','page','severity','flags')}
                                 for p in action_required[:20]]}
    report={'summary':summary,'total_pages':total,'flagged_pages':len(problems),'by_severity':severity_counts,'by_flag':flag_counts,
            'unresolved':problems,'ready_for_unqualified_use':False,
            'note':'No flags is not proof of visual, mathematical, or RTL fidelity.'}
    (destination/'QUALITY_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    def rows_for(pages):
        return ''.join('<tr><td>'+html.escape(x['severity'])+'</td><td>'+
                       html.escape(x['source'])+'</td><td>'+str(x['page'])+'</td><td>'+
                       html.escape(', '.join(x['flags']))+'</td></tr>' for x in pages)
    headings='<tr><th>Priority</th><th>Document</th><th>Page</th><th>Reasons</th></tr>'
    markup=('<!doctype html><html><head><meta charset="utf-8"><title>UNI-VERSE Quality Review</title>'
            '<style>body{font:16px system-ui;max-width:1200px;margin:2rem auto;padding:0 1rem}'
            'table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ccc;padding:.55rem;text-align:left}'
            'details{margin:1rem 0}pre{white-space:pre-wrap}</style></head><body>'
            '<h1>Course extraction review</h1>'
            f'<p><strong>{total}</strong> pages scanned; <strong>{len(action_required)}</strong> '
            f'need priority review; <strong>{len(advisory)}</strong> have advisory-only flags.</p>'
            '<p>Priority flags are diagnostic, not confirmed extraction errors. '
            'Even unflagged pages can contain errors.</p>'
            '<h2>Review first — possible content loss</h2>'
            '<table>'+headings+rows_for(action_required)+'</table>'
            '<details><summary>Show advisory-only pages</summary><table>'+
            headings+rows_for(advisory)+'</table></details>'
            '<details><summary>All warning categories</summary><pre>'+
            html.escape(json.dumps(flag_counts,ensure_ascii=False,indent=2))+'</pre></details>'
            '</body></html>')
    (destination/'QUALITY_REPORT.html').write_text(markup,encoding='utf-8')
    return {'total_pages':total,'flagged_pages':len(problems),'by_severity':severity_counts,'by_flag':flag_counts,'summary':summary}
