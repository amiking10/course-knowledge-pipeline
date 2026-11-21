"""Evidence-first structured course index.

Only explicit term matches are extracted. Co-occurrence means shared page,
not prerequisite, equivalence, or conceptual dependency.
"""
from __future__ import annotations
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

from .core import Store
from .topic_index import discover_course_terms

def _segments(body: str):
    """Keep primary and fallback evidence separate when tagged hybrid text is present."""
    marker='[SECONDARY PYMUPDF EXTRACTION'
    if marker in body:
        first,rest=body.split(marker,1)
        return [('docling',first.replace('[DOCLING EXTRACTION — UNVERIFIED]','').strip()),
                ('secondary_native_pdf',rest.split(']',1)[-1].strip())]
    return [('extracted_text',body)]

def _matched_aliases(text: str,aliases:list[str])->list[str]:
    lower=text.casefold()
    return [alias for alias in aliases
            if re.search(r'(?<!\w)'+re.escape(alias.casefold())+r'(?!\w)',lower)]

def _snippet(text: str,alias: str,context: int=100)->str:
    match=re.search(re.escape(alias),text,re.IGNORECASE)
    if not match:return text[:context*2]
    return text[max(0,match.start()-context):min(len(text),match.end()+context)].replace('\n',' ')

def _page_provenance(row,source,flags,segment):
    return {'source_id':source['source_id'],'source_path':source['relative_path'],
            'source_sha256':source['sha256'],'page':row['page_no'],
            'extractor':segment,'review_status':'machine_extracted_unverified',
            'flags':flags}

def build_knowledge(store: Store,destination:Path,
                    terms:dict[str,list[str]]|None=None)->dict:
    terms=discover_course_terms(store) if terms is None else terms
    # Empty course content must not produce unrelated course headings.
    nodes={key:{'name':key,'aliases':sorted(set(aliases)),
                'references':[]} for key,aliases in terms.items()}
    page_topics=defaultdict(set)
    pages_seen=0
    for source in store.sources():
        if source['state']!='active' or source['last_parsed_hash']!=source['sha256']:
            continue
        for page in store.pages(source['source_id']):
            pages_seen+=1
            flags=json.loads(page['flags'])
            for extractor,text in _segments(page['body']):
                if not text:continue
                for topic,aliases in terms.items():
                    matches=_matched_aliases(text,aliases)
                    if not matches:continue
                    page_topics[(source['source_id'],page['page_no'])].add(topic)
                    for match in matches:
                        evidence=_snippet(text,match)
                        provenance=_page_provenance(page,source,flags,extractor)
                        digest=sha256((source['sha256']+str(page['page_no'])+
                                       extractor+match+evidence).encode('utf-8')).hexdigest()
                        nodes[topic]['references'].append({
                            'evidence_id':digest,'matched_alias':match,
                            'excerpt':evidence,**provenance})
    for node in nodes.values():
        node['references'].sort(key=lambda r:(r['source_path'],r['page'],r['extractor'],r['matched_alias']))
    # Shared-page links do not claim prerequisite or causality.
    edge_pages=defaultdict(list)
    for (sid,page),topics in page_topics.items():
        names=sorted(topics)
        for i,left in enumerate(names):
            for right in names[i+1:]:
                edge_pages[(left,right)].append({'source_id':sid,'page':page})
    edges=[{'from':a,'to':b,'relation':'co_mentioned_on_same_page_only',
            'evidence_pages':references}
           for (a,b),references in sorted(edge_pages.items())]
    data={'schema_version':'1.0','status':'automatic_evidence_not_human_verified',
          'source_pages_scanned':pages_seen,'topics':list(nodes.values()),'edges':edges,
          'note':'Co-occurrence is not a semantic, explanatory or prerequisite relationship.'}
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    (destination/'COURSE_KNOWLEDGE.json').write_text(
        json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    md=['# Evidence-linked course knowledge (automatic, not reviewed)','',
        'All occurrences cite source file, original page and source SHA-256. Diagram fidelity not implied.','']
    for node in data['topics']:
        md.extend([f"## {node['name']}",''])
        if not node['references']:md.append('- No explicit occurrence found')
        for r in node['references'][:50]:
            md.append(f"- **{r['source_path']}**, page {r['page']} [{r['extractor']}; unverified] — {r['excerpt']}")
        if len(node['references'])>50:
            md.append(f"- ... and {len(node['references'])-50} additional references (see JSON)")
        md.append('')
    (destination/'COURSE_KNOWLEDGE.md').write_text('\n'.join(md),encoding='utf-8')
    return {'topics':len(nodes),'evidence_occurrences':sum(len(n['references']) for n in nodes.values()),
            'co_mention_edges':len(edges),'source_pages_scanned':pages_seen,
            'status':data['status']}
