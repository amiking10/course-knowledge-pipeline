"""Docling production parser plus clearly labelled diagnostic PyMuPDF backend."""
from __future__ import annotations
import re
from functools import lru_cache
from pathlib import Path
from .core import Page


@lru_cache(maxsize=1)
def _docling_converter():
    """Reuse a single Docling converter across pages in the same process."""
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise RuntimeError('Docling unavailable: install course-knowledge-pipeline[parse]') from exc
    return DocumentConverter()


def parse_docling(path: Path) -> list[Page]:
    result = _docling_converter().convert(str(path))
    doc = result.document
    # Per-page provenance avoids splitting whole-document Markdown by guessed headings.
    grouped: dict[int,list[str]] = {}
    flags_by_page: dict[int,set[str]] = {}
    figures_by_page: dict[int,list[str]] = {}
    seen = set()
    for element, level in doc.iterate_items():
        prov = getattr(element,'prov',None) or []
        if not prov:continue
        page_nos = sorted({int(p.page_no) for p in prov})
        typ = type(element).__name__.lower()
        label = str(getattr(element,'label','')).lower()
        is_table = typ == 'tableitem' or 'table' in label
        is_picture = typ == 'pictureitem' or 'picture' in label or 'figure' in label
        body = ''
        if is_table:
            try:
                body = element.export_to_markdown(doc=doc).strip()
            except Exception:
                for no in page_nos:flags_by_page.setdefault(no,set()).add('table_structure_review_required')
                body = '[TABLE DETECTED — cannot serialize; inspect original page]'
            if not body:
                for no in page_nos:flags_by_page.setdefault(no,set()).add('table_structure_review_required')
                body = '[TABLE DETECTED — empty serialization; inspect original page]'
        elif is_picture:
            body = '[FIGURE DETECTED — inspect original page]'
            for no in page_nos:
                flags_by_page.setdefault(no,set()).add('figure_content_review_required')
                figures_by_page.setdefault(no,[]).append('Picture or figure detected in original PDF')
        else:
            text = getattr(element,'text',None)
            if text:body=str(text).strip()
        if not body: continue
        if len(page_nos)>1:
            for no in page_nos:flags_by_page.setdefault(no,set()).add('multi_page_item_review_required')
        for no in page_nos:
            key=(no,id(element))
            if key not in seen:
                grouped.setdefault(no,[]).append(body)
                seen.add(key)
    expected=len(doc.pages) if hasattr(doc,'pages') else max(grouped,default=0)
    if expected==0:raise ValueError('Docling returned no numbered pages')
    return [Page(i,'\n\n'.join(grouped.get(i,[])),figures_by_page.get(i,[]),
                 sorted(flags_by_page.get(i,set())),'docling')
            for i in range(1,expected+1)]

def parse_pymupdf_diagnostic(path: Path) -> list[Page]:
    if path.suffix.lower()!='.pdf': raise ValueError('PyMuPDF diagnostic backend supports PDFs only')
    import fitz
    pages=[]
    with fitz.open(path) as doc:
        for i,p in enumerate(doc,1):
            # No OCR or image understanding; mark visually complex pages in QA.
            pages.append(Page(i,p.get_text(sort=True),[],[], 'pymupdf-diagnostic'))
    return pages


def parse(path: Path, backend: str) -> list[Page]:
    if backend=='docling': return parse_docling(path)
    if backend=='hybrid':
        from .hybrid import parse_hybrid
        return parse_hybrid(path)
    if backend=='pymupdf-diagnostic': return parse_pymupdf_diagnostic(path)
    raise ValueError(f'Unknown backend: {backend}')
