"""Loss-minimizing ChatGPT Project export, never claiming native index transfer."""
from pathlib import Path
import json
from .core import Store


def export_project(store: Store, destination: Path, max_chars: int=150000) -> dict:
    if max_chars<1000: raise ValueError('max_chars must be >=1000')
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    # Old bundles are cleaned after all current bundles are written successfully.
    manifest=[]; files=[]; package=[]; count=0
    def flush():
        nonlocal package,count
        if not package:return
        name=f'course_sources_{len(files)+1:03d}.md'
        (destination/name).write_text('\n\n'.join(package),encoding='utf-8')
        files.append(name);package=[];count=0
    for s in store.sources():
        if s['state']!='active' or s['last_parsed_hash'] != s['sha256']: continue
        pages=store.pages(s['source_id'])
        if not pages: continue
        manifest.append({'source_id':s['source_id'],'source_path':s['relative_path'],
                         'source_sha256':s['sha256'],'pages':len(pages),'backend':s['last_backend']})
        for p in pages:
            header=f"## Source: {s['relative_path']} | page {p['page_no']} | id {s['source_id']}\n"
            text=p['body'].strip() or '[NO EXTRACTED TEXT — inspect original slide]'
            # Split page *text*, not the source header; preserve full provenance on every fragment.
            max_piece=max_chars-len(header)-100
            if max_piece<=0: raise ValueError('Source filename too long for bundle size')
            fragments=[text[i:i+max_piece] for i in range(0,len(text),max_piece)]
            for idx,fragment in enumerate(fragments,1):
                tag=f'[fragment {idx}/{len(fragments)}]\n' if len(fragments)>1 else ''
                entry=header+'\n'+tag+fragment
                if count+len(entry)>max_chars: flush()
                package.append(entry);count+=len(entry)
    flush()
    for old in destination.glob('course_sources_*.md'):
        if old.name not in files: old.unlink()
    (destination/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (destination/'INDEX.md').write_text('# Course source index\n\n'+'\n'.join(
        f"- **{m['source_path']}** — {m['pages']} pages, backend: {m['backend']}, sha256: {m['source_sha256']}" for m in manifest
    )+'\n\nNote: this is an inventory, not a validated semantic concept index. Original diagrams are not present.\n',encoding='utf-8')
    return {'sources':len(manifest),'bundles':len(files),'bundle_files':files}
