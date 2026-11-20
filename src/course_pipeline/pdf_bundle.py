"""Loss-minimizing PDF consolidation for ChatGPT Project file-count limits.

This keeps original visual pages intact (including plots and circuit diagrams) and
builds a page-range map. It does not improve model retrieval or fix OCR.
"""
from __future__ import annotations
import json
from pathlib import Path
from .core import Store


def export_pdf_bundle(store: Store, source_dir: Path, output_pdf: Path) -> dict:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError('PyMuPDF is required for visual PDF bundling') from exc
    source_dir=Path(source_dir).resolve()
    output_pdf=Path(output_pdf)
    output_pdf.parent.mkdir(parents=True,exist_ok=True)
    toc=[];manifest=[];skipped=[];page_count=0
    bundle=fitz.open()
    try:
        for row in store.sources():
            if row['state']!='active': continue
            if row['ext']!='.pdf':
                skipped.append({'source':row['relative_path'],'reason':'not a PDF'})
                continue
            path=(source_dir/row['relative_path']).resolve()
            if not path.is_relative_to(source_dir):
                raise ValueError('Source escaped source root')
            if not path.is_file():
                raise FileNotFoundError(path)
            # Stop if the registry fingerprint is stale. Do not assemble unknown bytes.
            from .core import hash_file
            if hash_file(path)!=row['sha256']:
                raise ValueError(f'Source changed after scan: {path}')
            with fitz.open(path) as original:
                if not original.page_count:
                    raise ValueError(f'PDF has no pages: {path}')
                start=page_count+1
                bundle.insert_pdf(original)
                page_count+=original.page_count
                toc.append([1,row['relative_path'],start])
                manifest.append({'source':row['relative_path'],'source_id':row['source_id'],
                    'source_sha256':row['sha256'],'original_pages':original.page_count,
                    'merged_start_page':start,'merged_end_page':page_count})
        if page_count==0:
            raise ValueError('No PDF pages to export')
        bundle.set_toc(toc)
        bundle.set_metadata({'title':'Course source visual archive',
                             'subject':'Original course PDF pages grouped with bookmarks'})
        temp=output_pdf.with_suffix('.partial.pdf')
        bundle.save(temp,garbage=3,deflate=True)
        temp.replace(output_pdf)
    finally:
        bundle.close()
    with fitz.open(output_pdf) as check:
        if check.page_count!=page_count or len(check.get_toc())!=len(toc):
            raise RuntimeError('PDF archive validation failed')
    report={'total_pages':page_count,'sources':manifest,'skipped':skipped,
            'pdf':output_pdf.name}
    output_pdf.with_suffix('.manifest.json').write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
