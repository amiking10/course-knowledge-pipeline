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

STOPWORDS = set('the and for with from this that have has into about also using used are was not but can how when where what which your you its our their these those then than all one two page lecture slides course source original extraction unverified secondary check text pdf'.split()) | set('של על את עם זה היא הוא הם הן גם אבל אשר כמו מתוך בין זאת אלה היה היו יש אין לא אם כי כל עוד שם כאן יותר כדי לפי או מה מי כך רק'.split())

def discover_course_terms(store: Store, *, limit: int = 35) -> dict[str, list[str]]:
    """Select keywords only from currently parsed pages of this course."""
    counts = Counter()
    page_count = 0
    for source in store.sources():
        if source['state'] != 'active' or source['last_parsed_hash'] != source['sha256']:
            continue
        for page in store.pages(source['source_id']):
            page_count += 1
            tokens = set(re.findall(r'[^\W\d_]{3,}', page['body'].casefold(), re.UNICODE))
            for term in tokens:
                if term not in STOPWORDS and len(term) <= 35:
                    counts[term] += 1
    threshold = 2 if page_count >= 4 else 1
    ranked = sorted((t for t, n in counts.items() if n >= threshold), key=lambda t: (-counts[t], t))
    return {t: [t] for t in ranked[:limit]}


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
