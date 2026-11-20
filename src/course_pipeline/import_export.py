"""Reconcile a prior ChatGPT Markdown export with unchanged original PDFs.

Useful when Docling already ran but a previous Markdown export omitted visual text.
No claims are made about images or right-to-left ordering.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from .core import Store, hash_file, Page
from .hybrid import reconcile
from .parsers import parse_pymupdf_diagnostic
from .quality import assess

HEADER = re.compile(r'^## Source: (.+?) \| page (\d+) \| id ([a-zA-Z0-9-]+)\s*$', re.MULTILINE)
NO_TEXT = '[NO EXTRACTED TEXT — inspect original slide]'


def read_prior_export(directory: Path) -> tuple[dict,dict]:
    root=Path(directory)
    manifest_path=root/'manifest.json'
    if not manifest_path.exists():
        raise FileNotFoundError(f'Missing previous export manifest: {manifest_path}')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    indexed={s['source_path']:s for s in manifest}
    if len(indexed)!=len(manifest):
        raise ValueError('Duplicate source paths in manifest')
    chunks={}
    bundles=sorted(root.glob('course_sources_*.md'))
    if not bundles:
        raise ValueError('Prior export lacks Markdown bundles')
    for bundle in bundles:
        data=bundle.read_text(encoding='utf-8').replace('\r\n','\n')
        matches=list(HEADER.finditer(data))
        for i,m in enumerate(matches):
            source=m.group(1);number=int(m.group(2))
            content=data[m.end():matches[i+1].start() if i+1<len(matches) else len(data)].strip()
            if content==NO_TEXT:
                content=''
            if (source,number) in chunks:
                raise ValueError(f'Duplicate source page: {source}:{number}; fragmented pages need an explicit merger')
            chunks[source,number]=content
    for source,entry in indexed.items():
        pages=[n for (src,n) in chunks if src==source]
        if sorted(pages)!=list(range(1,entry['pages']+1)):
            raise ValueError(f'Incomplete prior export for {source}: expected {entry["pages"]} contiguous pages')
    if set(s for s,_ in chunks)!=set(indexed):
        raise ValueError('Prior Markdown references sources not in manifest')
    return indexed,chunks


def import_and_reconcile(store: Store, source_root: Path, export_root: Path)->dict:
    """Import only matching source hashes. No writes until all inputs verified."""
    source_root=Path(source_root).resolve()
    index,contents=read_prior_export(export_root)
    scanned=store.scan(source_root)
    verified=[]
    for row in store.sources():
        if row['state']!='active':
            continue
        path=(source_root/row['relative_path']).resolve()
        if not path.is_relative_to(source_root):
            raise ValueError(f'Source escaped root: {path}')
        old=index.get(row['relative_path'])
        if old is None:
            raise ValueError(f'No source in prior export for {row["relative_path"]}')
        if row['sha256'] != old['source_sha256'] or hash_file(path)!=old['source_sha256']:
            raise ValueError(f'Source hash mismatch for {row["relative_path"]}')
        if path.suffix.lower()!='.pdf':
            raise ValueError(f'Reconciliation import currently supports PDFs only: {path}')
        verified.append((row,path,old))
    if len(verified)!=len(index):
        raise ValueError('Source set differs from old export')
    results=[]
    for row,path,old in verified:
        native=parse_pymupdf_diagnostic(path)
        old_pages=[Page(page_no=i,body=contents[(row['relative_path'],i)],
                        figure_notes=[],flags=[],backend='docling-prior-export')
                   for i in range(1,old['pages']+1)]
        pages=reconcile(old_pages,native)
        report=assess(pages,path)
        for issue in report['warnings']:
            number=issue['page']
            if isinstance(number,int) and 1<=number<=len(pages):
                pages[number-1].flags.append(issue['kind'])
        for p in pages:p.flags=sorted(set(p.flags))
        store.save_pages(row['source_id'],pages,'hybrid',row['sha256'])
        results.append({'source':path.name,'pages':len(pages),
                        'secondary_disagreements':sum('secondary_native_text_disagrees_review' in p.flags for p in pages)})
    return {'method':'previous_docling_export_plus_new_native_pdf_extraction',
            'source_scan':scanned,'processed':len(results),'sources':results}
