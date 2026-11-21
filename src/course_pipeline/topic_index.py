"""Conservative source-linked topic navigation. No invented semantic relations."""
from __future__ import annotations
import json
import re
from pathlib import Path
from .core import Store

from collections import Counter

# Explicit OS vocabulary is retained only for callers requesting it.
COURSE_TERMS = {
 'Processes / תהליכים': ['process','תהליך','תהליכים','fork','exec','pcb'],
 'Interrupts / פסיקות': ['interrupt','פסיקה','פסיקות','idt','exception'],
 'Signals / איתותים': ['signal','signals','איתות','איתותים','sigaction'],
 'Scheduling / זימון': ['scheduler','scheduling','זימון','fcfs','sjf','srtf','round robin'],
 'Kernel and system calls': ['kernel','גרעין','system call','קריאת מערכת'],
 'Process state and context switching': ['context switch','החלפת הקשר','ready','waiting','running'],
}

STOPWORDS = set('the and for with from this that have has into about also using used are was not but can how when where what which your you its our their these those then than all one two page lecture slides course source original extraction unverified secondary check text pdf docling pymupdf figure figures detected inspect document review required markdown native structure format backend'.split()) | set('של על את עם זה היא הוא הם הן גם אבל אשר כמו מתוך בין זאת אלה היה היו יש אין לא אם כי כל עוד שם כאן יותר כדי לפי או מה מי כך רק'.split())

def discover_course_terms(store: Store, *, limit: int = 35) -> dict[str, list[str]]:
    """Find repeated source-backed terms and 2-3 word phrases, not inferred topics.

    Page frequency gives each lecture page one vote. The result remains a
    lexical navigation aid, never a semantic classification or syllabus.
    """
    counts = Counter()
    pages_seen = 0
    for source in store.sources():
        if source['state'] != 'active' or source['last_parsed_hash'] != source['sha256']:
            continue
        for page in store.pages(source['source_id']):
            pages_seen += 1
            found = set()
            # Avoid combining words across PDF headings, lines, or extraction labels.
            for line in page['body'].splitlines():
                if line.lstrip().startswith('[') and ']' in line:
                    continue
                tokens = re.findall(r'[^\W\d_]{2,}', line.casefold(), re.UNICODE)
                for token in tokens:
                    if len(token) >= 3 and len(token) <= 35 and token not in STOPWORDS:
                        found.add(token)
                for size in (2, 3):
                    for i in range(len(tokens)-size+1):
                        phrase_tokens=tokens[i:i+size]
                        if any(x in STOPWORDS or len(x)>35 for x in phrase_tokens):
                            continue
                        phrase=' '.join(phrase_tokens)
                        if len(phrase)<=70:
                            found.add(phrase)
            counts.update(found)
    if not pages_seen:
        return {}
    minimum_pages = 2 if pages_seen >= 4 else 1
    phrases = sorted((x for x,n in counts.items() if ' ' in x and n>=minimum_pages),
                     key=lambda x:(-counts[x],-len(x.split()),x))
    words = sorted((x for x,n in counts.items() if ' ' not in x and n>=minimum_pages),
                   key=lambda x:(-counts[x],x))
    # Reserve slots for short acronyms and standalone terms as well as phrases.
    phrase_limit = min(limit*2//3,len(phrases))
    selected=phrases[:phrase_limit]+words[:limit-phrase_limit]
    if len(selected)<limit:
        selected += phrases[phrase_limit:phrase_limit+limit-len(selected)]
    return {term:[term] for term in selected}


def make_index(store: Store, dest: Path, terms: dict[str,list[str]]|None=None) -> dict:
    terms=discover_course_terms(store) if terms is None else terms
    entries={key:[] for key in terms}
    for source in store.sources():
        if source['state']!='active' or source['last_parsed_hash']!=source['sha256']:continue
        for p in store.pages(source['source_id']):
            body=p['body'].casefold()
            for topic, aliases in terms.items():
                matched=[a for a in aliases if re.search(r'(?<!\w)'+re.escape(a.casefold())+r'(?!\w)',body)]
                if matched:
                    entries[topic].append({'source':source['relative_path'],'page':p['page_no'],
                                           'source_id':source['source_id'],'matched':matched})
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
    (dest/'COURSE_INDEX.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Course topic navigation (evidence-matched, not AI verified)', '',
           'This index lists explicit term occurrences; it does not assert conceptual completeness.', '']
    for topic,hits in entries.items():
        lines.extend([f'## {topic}', ''])
        lines.extend(f"- {h['source']} — page {h['page']} (matched: {', '.join(h['matched'])})" for h in hits)
        if not hits:lines.append('- No exact term matches found')
        lines.append('')
    (dest/'COURSE_INDEX.md').write_text('\n'.join(lines),encoding='utf-8')
    return {'topics':len(entries),'references':sum(map(len,entries.values()))}
